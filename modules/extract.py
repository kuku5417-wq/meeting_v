"""메모 → 이슈 후보 (F1).

**원본은 바꾸지 않는다** (`CLAUDE.md` §6-1). 메모는 넣은 그대로 저장하고, 고칠 때는
새 행을 만들어 `revises_id` 로 앞 판을 가리킨다.

**근거 없는 AI 값은 표시하지 않는다** (§6-3). 이것을 말로만 두지 않고 코드로 막는다 —
AI 가 채운 칸은 메모 안의 **원문 구간**(`quote`)을 함께 내야 하고, 그 구간이 메모에서
실제로 찾아지지 않으면 **그 칸을 버린다**. `verify()` 가 그 일을 한다.

**AI 값과 사람 값을 둘 다 남긴다** (§6-2). 화면이 `_ai` 로 **기계가 낸 원값**을 함께 넘기고,
`register()` 가 `ai_field_log` 에 (AI 값, 사람 값)을 적는다 — 사람이 안 고친 칸은 사람 값을 비운다.
`_ai` 를 넘기지 않으면 고친 값이 AI 값 자리에 들어가므로, 화면은 **반드시** 원값을 함께 넘긴다.

사내 LLM 설정이 없으면 `extract()` 는 `LLMNotConfigured` 를 낸다 — 사외망에서는 정상이고,
화면은 **수동 입력**으로 떨어진다 (`views/inbox.py`).
"""
from __future__ import annotations

import datetime
import re
import uuid

from modules import issues
from modules import models as m
from modules.db import session
from modules.llm_client import DEFAULT_SYSTEM, LLMNotConfigured, ask_json  # noqa: F401

# AI 가 채울 수 있는 칸. 각각 근거 구간이 있어야 산다 (§6-3).
AI_FIELDS = ("title", "body", "hull", "equipment")

PROMPT = """아래는 조선소 커미셔닝 현장에서 적은 메모다. 이슈 후보로 나눠라.

규칙
- 메모에 적히지 않은 것은 **채우지 마라.** 빈 문자열로 둔다.
- 각 후보마다 `quote` 에 **메모에서 그대로 복사한 구간**을 넣어라. 바꿔 쓰지 마라.
  그 구간이 메모에 없으면 그 후보는 버려진다.
- 호선·장비는 메모에 적힌 **현장 표기 그대로** 둔다. 정규화하지 마라.
- 후보는 많아야 5개.

JSON 으로만 답한다:
{{"candidates": [{{"title": "...", "block_type": "issue|problem|share",
  "hull": "", "equipment": "", "body": "", "quote": "메모에서 그대로 복사한 구간"}}]}}

메모:
{memo}
"""


def _rid() -> str:
    return uuid.uuid4().hex[:16]


def locate(raw: str, quote: str) -> tuple[int, int] | None:
    """메모에서 근거 구간의 자리를 찾는다. 없으면 `None`.

    줄바꿈·연속 공백은 느슨하게 본다 — LLM 이 공백을 다르게 내는 일이 잦다.

    >>> locate("발전기 2번 배기온도 편차 40도", "배기온도 편차")
    (7, 14)
    >>> locate("발전기  2번   배기온도", "발전기 2번 배기온도")
    (0, 14)
    >>> locate("아무 말", "없는 구간") is None
    True
    """
    if not quote.strip():
        return None
    at = raw.find(quote)
    if at >= 0:
        return at, at + len(quote)
    # 공백을 느슨하게: 조각들이 순서대로 나오면 처음과 끝을 구간으로 본다
    parts = [p for p in quote.split() if p]
    if not parts:
        return None
    pos = raw.find(parts[0])
    if pos < 0:
        return None
    end = pos + len(parts[0])
    for p in parts[1:]:
        nxt = raw.find(p, end)
        if nxt < 0:
            return None
        end = nxt + len(p)
    return pos, end


# 메모에서 **사건이 난 날**을 찾는 모양 (`requirements.md` §2-C). 모두 (연도, 월, 일) 세 묶음이고
# 연도 자리는 비어 있을 수 있다. 못 찾으면 비워 두고 사람이 고른다 (§6-3).
#
# **덜 찾더라도 잘못 찾지 않는다.** 메모에는 날짜가 아닌 `m/d` 꼴이 흔하다 —
# "DG 2/3 번", "매핑 2/5", "편차 1/2". 그래서 연도가 없는 `11/12` 는 **줄머리에서만** 받는다
# (메모는 "11/12 SN2511 안벽" 처럼 날짜로 줄을 연다). 같은 이유로 `11.12` 꼴은 아예 받지 않는다 —
# `1.5` 같은 수치와 구별할 수 없다.
_DATE_PATTERNS = (
    re.compile(r"(?<!\d)(\d{4})[-./](\d{1,2})[-./](\d{1,2})(?!\d)"),      # 2026-11-12 (어디서나)
    re.compile(r"()(\d{1,2})\s*월\s*(\d{1,2})\s*일"),                      # 11월 12일 (어디서나)
    re.compile(r"^[ \t]*()(\d{1,2})/(\d{1,2})(?!\d)", re.M),              # 11/12 (줄머리에서만)
)

# 연도가 없는 날짜를 전해로 돌려볼 수 있는 한계. 이보다 오래된 것으로 읽히면 버린다.
_BACK_LIMIT_DAYS = 180


def find_date(text: str, base: datetime.date | None = None) -> tuple[datetime.date, tuple[int, int]] | None:
    """글에서 **처음 나오는 날짜**와 그 구간. 못 찾으면 `None`.

    **사건은 적기 전에 일어난다.** 그래서 `base`(메모를 적은 날)보다 뒤인 날짜는 발생일이 아니다 —
    연도가 없으면 전해로 한 번 돌려보고(1월에 적은 "12/28"), 그래도 반 년 넘게 거슬러 가면 버린다.
    연도가 적힌 날짜가 앞날이면 그냥 버린다 — "11/20 예정" 같은 **계획**을 발생일로 삼지 않는다.

    >>> find_date("11/12 SN2511 안벽 DG2 배기온도", datetime.date(2026, 11, 13))
    (datetime.date(2026, 11, 12), (0, 5))
    >>> find_date("2026-09-30 조타기 이상음", datetime.date(2026, 11, 13))
    (datetime.date(2026, 9, 30), (0, 10))
    >>> find_date("11월 12일에 났다", datetime.date(2026, 11, 13))
    (datetime.date(2026, 11, 12), (0, 7))
    >>> find_date("12/28 누유", datetime.date(2027, 1, 4))
    (datetime.date(2026, 12, 28), (0, 5))

    날짜가 아닌 것은 받지 않는다.

    >>> find_date("DG 2/3 번 발전기 점검", datetime.date(2026, 11, 13)) is None
    True
    >>> find_date("편차 40도, 1.5 bar", datetime.date(2026, 11, 13)) is None
    True
    >>> find_date("11/20 예정", datetime.date(2026, 11, 13)) is None
    True
    """
    base = base or datetime.date.today()
    best: tuple[datetime.date, tuple[int, int]] | None = None
    for pattern in _DATE_PATTERNS:
        for hit in pattern.finditer(text):
            year, month, day = hit.group(1), hit.group(2), hit.group(3)
            found = _date_or_none(int(year) if year else base.year, int(month), int(day))
            if found is None:
                continue
            if found > base:
                if year:
                    continue  # 연도까지 적힌 앞날 — 계획이지 발생일이 아니다
                found = _date_or_none(base.year - 1, int(month), int(day))
                if found is None or (base - found).days > _BACK_LIMIT_DAYS:
                    continue
            start = hit.start(2) if not year else hit.start()
            if best is None or start < best[1][0]:
                best = (found, (start, hit.end()))
    return best


def _date_or_none(year: int, month: int, day: int) -> datetime.date | None:
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    try:
        return datetime.date(year, month, day)
    except ValueError:  # 2월 30일 같은 것
        return None


def date_for(raw: str, span: tuple[int, int] | None, base: datetime.date | None = None):
    """그 후보의 발생일. **제 근거 구간 안**을 먼저 보고, 없으면 메모 전체를 본다.

    돌려주는 것: `(날짜, 메모 안에서의 구간)` 또는 `None`.
    구간은 메모 기준 자리라 그대로 `source_span` 에 남길 수 있다.
    """
    if span is not None:
        inside = find_date(raw[span[0]:span[1]], base)
        if inside is not None:
            found, (a, b) = inside
            return found, (span[0] + a, span[0] + b)
    return find_date(raw, base)


def verify(
    raw: str, candidates: list[dict], base: datetime.date | None = None
) -> tuple[list[dict], list[str]]:
    """근거가 없는 후보를 버린다 (§6-3). 살아남은 후보에는 **발생일**을 붙여 준다.

    돌려주는 것: (살아남은 후보, 버린 이유 목록). 버린 것을 조용히 숨기지 않는다.
    발생일은 그 후보의 근거 구간 안을 먼저 보고, 없으면 메모 전체를 본다 — 못 찾으면 붙이지 않는다.
    """
    kept: list[dict] = []
    dropped: list[str] = []
    for i, c in enumerate(candidates, 1):
        title = (c.get("title") or "").strip()
        if not title:
            dropped.append(f"{i}번: 제목이 없다")
            continue
        span = locate(raw, (c.get("quote") or "").strip())
        if span is None:
            dropped.append(f"{i}번 「{title[:20]}」: 근거 구간을 메모에서 찾지 못했다")
            continue
        row = {**c, "title": title, "_span": span}
        found = date_for(raw, span, base)
        if found is not None:
            day, where = found
            row |= {"occurred_on": day, "_date_span": where, "_date_text": raw[where[0]:where[1]]}
        kept.append(row)
    return kept, dropped


def extract(raw: str) -> tuple[list[dict], list[str]]:
    """메모에서 이슈 후보를 뽑는다. 사내 LLM 설정이 없으면 `LLMNotConfigured`."""
    answer = ask_json(PROMPT.format(memo=raw))
    if not answer:
        return [], ["LLM 이 JSON 을 내지 않았다"]
    return verify(raw, list(answer.get("candidates") or []))


def save_memo(raw_text: str, author_id: str | None = None, revises_id: str | None = None) -> str:
    """메모를 **그대로** 저장한다. 고칠 때는 새 행을 만들고 앞 판을 가리킨다 (§6-1)."""
    mid = _rid()
    with session() as s:
        s.add(
            m.Memo(
                id=mid,
                raw_text=raw_text,
                author_id=author_id,
                created_at=datetime.datetime.now(),
                revises_id=revises_id,
            )
        )
        s.commit()
    return mid


def memos(limit: int = 20) -> list[dict[str, object]]:
    """최근 메모. 고쳐진 판(뒤에 새 판이 있는 것)은 표시해 준다."""
    with session() as s:
        rows = s.execute(
            m.Memo.__table__.select().order_by(m.Memo.created_at.desc()).limit(limit)
        ).mappings().all()
        revised = {r["revises_id"] for r in rows if r["revises_id"]}
        return [
            {
                "id": r["id"],
                "적은 때": r["created_at"].strftime("%Y-%m-%d %H:%M"),
                "글": (r["raw_text"] or "")[:80],
                "판": "옛 판" if r["id"] in revised else ("고친 판" if r["revises_id"] else ""),
            }
            for r in rows
        ]


def memo_text(memo_id: str) -> str:
    with session() as s:
        row = s.get(m.Memo, memo_id)
        return row.raw_text if row else ""


def register(memo_id: str, candidate: dict, by_ai: bool) -> str:
    """후보 하나를 이슈로 등록한다.

    AI 가 낸 것이면 근거 구간을 `source_span` 에, AI 값을 `ai_field_log` 에 남긴다 (§6-2·§6-3).
    사람이 직접 적은 것이면 근거 구간이 없어도 된다 — 사람이 근거다.
    """
    bid = issues.create_block(
        title=candidate.get("title", ""),
        block_type=candidate.get("block_type") or "issue",
        owner_department_id=candidate.get("department_id") or None,
        body=candidate.get("body") or "",
        hull_text=candidate.get("hull") or "",
        equipment_text=candidate.get("equipment") or "",
        occurred_on=candidate.get("occurred_on") or None,
    )
    now = datetime.datetime.now()
    span = candidate.get("_span")
    date_span = candidate.get("_date_span")
    # 화면이 넘겨 준 **기계가 낸 원값**. 사람이 고쳤으면 `candidate[field]` 와 다르다 (§6-2).
    ai_values: dict = candidate.get("_ai") or {}
    with session() as s:
        blk = s.get(m.Block, bid)
        blk.origin = "memo"
        # 발생일은 메모에서 읽은 값이라 **어디서 읽었는지**를 남긴다 (§6-3).
        # 사람이 고른 날이면 구간이 없다 — 사람이 근거다.
        if date_span and blk.occurred_on:
            s.add(
                m.SourceSpan(
                    id=_rid(), block_id=bid, field="occurred_on", memo_id=memo_id,
                    start=date_span[0], end=date_span[1],
                    quote=candidate.get("_date_text") or "",
                )
            )
        if by_ai and span:
            quote = (candidate.get("quote") or "").strip()
            for field in AI_FIELDS:
                if not (candidate.get(field) or "").strip():
                    continue
                s.add(
                    m.SourceSpan(
                        id=_rid(), block_id=bid, field=field, memo_id=memo_id,
                        start=span[0], end=span[1], quote=quote,
                    )
                )
                # (AI 값, 사람 값)을 **둘 다** 남긴다 (§6-2). 사람이 안 고쳤으면 사람 값은 비운다.
                ai_value = str(ai_values.get(field, candidate[field]) or "")
                human = str(candidate[field] or "")
                s.add(
                    m.AiFieldLog(
                        id=_rid(), block_id=bid, field=field,
                        ai_value=ai_value, human_value=human if human != ai_value else None,
                        model="사내 LLM", created_at=now,
                    )
                )
        # 발생일도 기계가 낸 값이라 같은 기록을 남긴다. 사람이 날짜를 고치면 그 값이 사람 값이다.
        ai_day = ai_values.get("occurred_on")
        if ai_day:
            human_day = blk.occurred_on
            s.add(
                m.AiFieldLog(
                    id=_rid(), block_id=bid, field="occurred_on",
                    ai_value=str(ai_day),
                    human_value=str(human_day) if human_day != ai_day else None,
                    model="메모 날짜 읽기", created_at=now,
                )
            )
        s.commit()
    return bid


def evidence(block_id: str) -> list[dict[str, str]]:
    """그 이슈가 어느 메모의 어느 구간에서 나왔는지."""
    with session() as s:
        rows = s.execute(
            m.SourceSpan.__table__.select().where(m.SourceSpan.block_id == block_id)
        ).mappings().all()
        return [
            {"칸": r["field"], "메모": r["memo_id"][:8], "구간": f"{r['start']}–{r['end']}",
             "원문": r["quote"] or ""}
            for r in rows
        ]
