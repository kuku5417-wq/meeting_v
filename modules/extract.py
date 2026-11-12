"""메모 → 이슈 후보 (F1).

**원본은 바꾸지 않는다** (`CLAUDE.md` §6-1). 메모는 넣은 그대로 저장하고, 고칠 때는
새 행을 만들어 `revises_id` 로 앞 판을 가리킨다.

**근거 없는 AI 값은 표시하지 않는다** (§6-3). 이것을 말로만 두지 않고 코드로 막는다 —
AI 가 채운 칸은 메모 안의 **원문 구간**(`quote`)을 함께 내야 하고, 그 구간이 메모에서
실제로 찾아지지 않으면 **그 칸을 버린다**. `verify()` 가 그 일을 한다.

**AI 값과 사람 값을 둘 다 남긴다** (§6-2). 사람이 고치면 `ai_field_log` 에 (AI 값, 사람 값)이 남는다.

사내 LLM 설정이 없으면 `extract()` 는 `LLMNotConfigured` 를 낸다 — 사외망에서는 정상이고,
화면은 **수동 입력**으로 떨어진다 (`views/inbox.py`).
"""
from __future__ import annotations

import datetime
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


def verify(raw: str, candidates: list[dict]) -> tuple[list[dict], list[str]]:
    """근거가 없는 후보를 버린다 (§6-3).

    돌려주는 것: (살아남은 후보, 버린 이유 목록). 버린 것을 조용히 숨기지 않는다.
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
        kept.append({**c, "title": title, "_span": span})
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
    )
    now = datetime.datetime.now()
    span = candidate.get("_span")
    with session() as s:
        blk = s.get(m.Block, bid)
        blk.origin = "memo"
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
                s.add(
                    m.AiFieldLog(
                        id=_rid(), block_id=bid, field=field,
                        ai_value=candidate[field], human_value=None,
                        model="사내 LLM", created_at=now,
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
