"""회의자료 — 구성·요약·사실 되먹임·제출·취합·진행·종결·지시사항
(F6 · F7 · F8 · F9 · F10 · F12 · F13 · F20, `requirements.md` §1-3-2).

화면(`views/meeting.py`)은 여기만 부른다. DB 를 직접 열지 않는다.

**회의자료의 한 장은 `report_item` 하나다** (2026-11-13 결정 D, `requirements.md` §2-D).
`deck_slide`·`slide_object` 는 없다 — 1차 회의자료는 **틀(`form`)을 고르고 값을 고치는** 화면이고,
자유 배치는 S8 의 `.pptx` 내보내기로 넘긴다.

**표현은 `report_item`, 사실은 `block`.**

| 어느 표에 있나 | 무엇 |
|---|---|
| `report_item` | 회의용 한 줄(`line`) · 형태(`form`) · 순서(`order_no`) · 머리표(`tag_on`) · 참조(`src`) |
| `block` | 현상 · 원인 · 조치 · 결정 필요 · 상태 — **이슈 원장과 같은 한 벌** |

그래서 `save_fact()` 는 `block` 을 고치고 `set_line()`·`set_form()` 은 `report_item` 을 고친다.

**사실 되먹임(F8)은 1차다** (2026-11-13 결정). 회의자료에서 사실을 고치면 그 이슈가
바로 바뀌고 원장·부서 자료도 같은 값을 본다 — `block` 이 한 벌이라 베껴 둘 곳이 없다.
고친 자리는 `ai_field_log` 에 (AI 값, 사람 값)으로 남는다 (`CLAUDE.md` §6-2).

**업무 규칙은 여기서 막는다.** 화면이 버튼을 가려 주는 것에 기대지 않는다 —
종결은 공유회의 「종결요청」 이슈만(§6-7), 취합도 공유회만, 제출은 부서 자료만,
빈 글은 기록하지 않는다.
막을 때는 `NotAllowed` 에 **왜 막혔는지**를 적는다.

**「종결」은 부서가 하지 않는다** (`CLAUDE.md` §6-7). 부서는 「종결요청」까지고, 승인은
공유회 진행 화면의 `decide_closure()` 다. 사례 카드로 올리는 일은 S9 다.
"""
from __future__ import annotations

import datetime
import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules import issues
from modules import models as m
from modules.db import session

# 회의 갈래 — `meeting.kind`. 시안 v2e-studio 의 `?kind=` 가 이 값이다
KIND_LABELS = {
    "dept": "부서 자료",
    "share": "부서 현안 공유회",
    "exec": "팀장 정보회의",
    "hull": "호선별 회의",
    "review": "문제점·장비 리뷰",
}
KINDS = tuple(KIND_LABELS)
# 주차마다 저절로 생기는 회의 — 시안 "정기 회의는 매주 자동으로 생겨 「만들기」가 필요 없습니다"
REGULAR_KINDS = ("share", "exec")
# 사람이 「만들기」로 더하는 수시 회의
ADHOC_KINDS = ("hull", "review")

# 어휘(`meeting.status`·`report_item.kind`·`closure.decision`·`directive.status`)는
# `modules/models.py` 의 칸 옆에 적혀 있다 — 같은 내용을 두 군데 적지 않는다 (`CLAUDE.md` §2).
# **저장되는 값은 원본 `docs/03` 어휘다** — 사내망 실데이터와 값을 맞추기 위해서다
# (2026-11-13 결정). 부서 자료는 「제출」, 나머지는 「발행」이고 **「발행」은 S8 몫**이다.
# 1차에서 코드가 넣는 `meeting.status` 는 「구성 중」과 「제출」 둘이다.

# `meeting.start_mode` 는 **저장 값이 영문 코드**고 (원본 `docs/03`: carry/blank)
# **화면에 보이는 말은 「이어받기」·「빈 자료」**다. 라벨과 저장 값이 갈리는 곳은 여기
# 하나다 — 화면은 `meeting()` 의 「시작 이름」을 읽고 코드를 직접 번역하지 않는다
START_MODE_LABELS = {"blank": "빈 자료", "carry": "이어받기"}

# 장의 형태 (F6 형태 전환). 시안 README "형태(상세·카드·사진·한 줄)"
FORM_LABELS = {"detail": "상세", "card": "카드", "photo": "사진", "line": "한 줄"}
FORMS = tuple(FORM_LABELS)

# 장의 종류. **`table`(기간 표)은 2차다** — `metric_table` 이 1차에 없다 (§1-2-3).
# 어휘에는 두고 화면에서 만들지 않는다.
ITEM_KIND_LABELS = {"single": "이슈 한 건", "summary": "요약", "metric": "지표", "table": "기간 표"}

# **사실**이다. `report_item` 이 아니라 `block` 에 있다.
# 어휘를 두 군데 두지 않는다 — 원장 「상세 한 장」(F5)의 칸 한 벌 그대로다 (`CLAUDE.md` §2)
FACT_FIELDS = issues.DRAFT_FIELDS
FACT_LABELS = {
    "body": "현상",
    "cause_text": "원인",
    "action_text": "조치",
    "decision_needed": "결정 필요",
}

# 참조로 실은 장(F10)이 가리킨 판에서 그 장을 못 찾았을 때. 참조의 정본은 판이라
# (`_src_ref`) 그 자리를 빈 값으로 되돌려 보통 장처럼 보이게 두지 않고 이 말로 내보인다
MISSING_SRC = "부서 자료에서 빠진 장"

COMMENT_KINDS = ("comment", "decision")
COMMENT_LABELS = {"comment": "코멘트", "decision": "결정"}

# 아직 끝나지 않은 이슈 — 후보 목록에 오르고 다음 주로 이어받는다.
# 원장에서 사람이 고를 수 있는 상태와 같은 한 벌이다 — 「종결」이 빠져 있다 (`CLAUDE.md` §6-7)
OPEN_STATUSES = issues.ASSIGNABLE_STATUSES

# 종결 결정 — `closure.decision`. 「대기」는 아직 결정이 없다는 표시라 여기서 넣지 않는다
DECISIONS = ("승인", "보류")


class NotAllowed(RuntimeError):
    """업무 규칙이 막은 일. **왜 막혔는지**를 글로 담는다.

    화면이 버튼을 가려 주는 것으로는 규칙이 서지 않는다 — 규칙은 이 모듈에 있다.
    """


def _rid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _monday(wid: str) -> datetime.date:
    """`2026-W46` → 그 주 월요일. 주차 ID 를 날짜로 바꾸는 곳은 여기 하나다."""
    return datetime.date.fromisocalendar(int(wid[:4]), int(wid.split("W")[1]), 1)


# ── 주차 ───────────────────────────────────────────────────────────────────
def shift_week(wid: str, weeks: int) -> str:
    """`2026-W46` 에서 몇 주 앞뒤. 해를 넘어가도 ISO 주차로 맞는다.

    >>> shift_week("2026-W46", 1)
    '2026-W47'
    >>> shift_week("2026-W01", -1)
    '2025-W52'
    """
    return issues.week_id(_monday(wid) + datetime.timedelta(weeks=weeks))


def week_options(back: int = 5) -> list[str]:
    """고를 수 있는 주차 — 이번 주부터 거슬러 몇 주 + DB 에 이미 있는 주차. 최신이 앞."""
    this = issues.week_id()
    out = {shift_week(this, -i) for i in range(back)}
    with session() as s:
        out |= set(s.execute(select(m.Week.id)).scalars().all())
    return sorted(out, reverse=True)


def departments() -> dict[str, str]:
    with session() as s:
        rows = s.execute(select(m.Department).order_by(m.Department.order_no)).scalars().all()
        return {r.id: r.name for r in rows}


def hulls() -> list[str]:
    """호선별 회의에서 고를 호선. 인도선도 목록에 남긴다 — 지난 회의를 볼 수 있어야 한다."""
    with session() as s:
        return list(s.execute(select(m.Hull.id).order_by(m.Hull.id)).scalars().all())


# ── 회의 ───────────────────────────────────────────────────────────────────
def _meeting_id(
    s: Session, wid: str, kind: str, dept_id: str | None, hull_id: str | None
) -> str:
    """`MTG-2026-W46-dept-D2` 꼴. **사람이 읽을 수 있게** (`CLAUDE.md` §6-8)."""
    tail = dept_id or hull_id
    base = f"MTG-{wid}-{kind}" + (f"-{tail}" if tail else "")
    mid, n = base, 1
    while s.get(m.Meeting, mid) is not None:
        n += 1
        mid = f"{base}-{n}"
    return mid


def _new_meeting(
    s: Session,
    wid: str,
    kind: str,
    title: str,
    dept_id: str | None = None,
    hull_id: str | None = None,
    start_mode: str = "blank",
    held_on: datetime.date | None = None,
) -> str:
    mid = _meeting_id(s, wid, kind, dept_id, hull_id)
    s.add(
        m.Meeting(
            id=mid,
            week_id=wid,
            kind=kind,
            title=title,
            owner_dept_id=dept_id,
            hull_id=hull_id,
            held_on=held_on,
            status="구성 중",
            start_mode=start_mode,
            version=0,
        )
    )
    s.flush()
    return mid


def ensure_regular(wid: str | None = None) -> int:
    """그 주차의 정기 회의를 없으면 만든다 — 부서 자료 8건 + 공유회 + 팀장 정보회의.

    돌려주는 것은 **새로 만든 건수**다. 이미 있으면 0 이고 아무것도 고치지 않는다.
    """
    wid = wid or issues.week_id()
    made = 0
    with session() as s:
        issues.ensure_week(s, _monday(wid))
        have = set(
            s.execute(select(m.Meeting.id).where(m.Meeting.week_id == wid)).scalars().all()
        )
        for kind in REGULAR_KINDS:
            if f"MTG-{wid}-{kind}" not in have:
                _new_meeting(s, wid, kind, KIND_LABELS[kind])
                made += 1
        for dept_id, name in departments().items():
            if f"MTG-{wid}-dept-{dept_id}" not in have:
                _new_meeting(s, wid, "dept", f"{name} 회의자료", dept_id=dept_id)
                made += 1
        s.commit()
    return made


def create_meeting(
    kind: str,
    title: str,
    wid: str | None = None,
    dept_id: str | None = None,
    hull_id: str | None = None,
    start_mode: str = "blank",
    held_on: datetime.date | None = None,
) -> str:
    """수시 회의를 하나 만든다 (호선별 회의·문제점 리뷰). 돌려주는 것은 회의 ID.

    `meeting.week_id` 는 `week` 를 가리키므로 **그 주차 행을 먼저 보장한다** — SQLite 는
    FK 를 강제하지 않아 지금은 조용하지만, 사내망 DB 에서는 여기서 깨진다.
    """
    wid = wid or issues.week_id()
    with session() as s:
        issues.ensure_week(s, _monday(wid))
        mid = _new_meeting(
            s, wid, kind, title.strip() or KIND_LABELS[kind], dept_id, hull_id, start_mode, held_on
        )
        s.commit()
    return mid


def set_held_on(meeting_id: str, day: datetime.date | None) -> None:
    """회의 날짜. 비워 두면 주차만 보인다 — 모르는 날을 지어내지 않는다."""
    with session() as s:
        s.get(m.Meeting, meeting_id).held_on = day
        s.commit()


def meeting(meeting_id: str) -> dict[str, object]:
    """회의 한 건의 머리 정보."""
    with session() as s:
        mt = s.get(m.Meeting, meeting_id)
        dept = s.get(m.Department, mt.owner_dept_id) if mt.owner_dept_id else None
        n = s.execute(
            select(func.count()).select_from(m.ReportItem).where(m.ReportItem.meeting_id == mt.id)
        ).scalar_one()
        return {
            "ID": mt.id,
            "주차": mt.week_id,
            "갈래": mt.kind,
            "갈래 이름": KIND_LABELS.get(mt.kind, mt.kind),
            "제목": mt.title,
            "부서": dept.name if dept else "",
            "부서 ID": mt.owner_dept_id or "",
            "호선": mt.hull_id or "",
            "날짜": mt.held_on,
            "상태": mt.status,
            "판": mt.version or 0,
            "장": n,
            # 저장 값(코드)과 화면에 보이는 말을 함께 준다 — 「갈래」·「형태」와 같은 방식이다
            "시작": mt.start_mode or "",
            "시작 이름": START_MODE_LABELS.get(mt.start_mode or "", ""),
            "시작한 때": mt.held_at,
        }


def meetings(wid: str | None = None, kind: str | None = None) -> list[dict[str, object]]:
    """회의 목록 한 판. 주차를 주지 않으면 전부."""
    with session() as s:
        q = select(m.Meeting)
        if wid:
            q = q.where(m.Meeting.week_id == wid)
        if kind:
            q = q.where(m.Meeting.kind == kind)
        rows = s.execute(q.order_by(m.Meeting.week_id.desc(), m.Meeting.id)).scalars().all()
        ids = [r.id for r in rows]
    return [meeting(i) for i in ids]


# ── F6 장 구성 ─────────────────────────────────────────────────────────────
def _next_order(s: Session, meeting_id: str) -> int:
    last = s.execute(
        select(func.max(m.ReportItem.order_no)).where(m.ReportItem.meeting_id == meeting_id)
    ).scalar()
    return (last or 0) + 1


def _block_ids_on(s: Session, meeting_id: str) -> set[str]:
    """그 회의에 이미 실린 이슈 — **세 길을 다 센다.**

    1. 장 자신이 잇는 이슈 (`report_item.block_id`)
    2. 자기 요약 장이 잇는 이슈 (`report_item_block`, F7)
    3. **참조로 실은 장이 가리킨 판의 「이슈」** (F10) — 요약 참조 장이 여기 걸린다

    세 번째를 빼면 **요약 장으로만 실린 이슈가 이 회의에 없는 것처럼 보인다.** 참조
    장은 `report_item_block` 을 베끼지 않기 때문이다 (`collect`) — 참조의 정본은 판이라
    요약이 잇는 이슈도 판에서 읽는다 (`_shown`·`_src_ref`). 그러면 종결요청이
    `closure_pending()` 에 안 나오고 `decide_closure()` 가 「안건에 없다」고 막으며,
    같은 이슈가 후보(`candidates`)와 취합(`collect`)에 또 오른다.

    판에서 그 장을 못 찾은 「빠진 장」은 셀 이슈가 없다 — 판에 글이 없는 자리다.
    """
    rows = s.execute(
        select(m.ReportItem).where(m.ReportItem.meeting_id == meeting_id)
    ).scalars().all()
    out = {it.block_id for it in rows if it.block_id}
    if rows:
        out |= set(
            s.execute(
                select(m.ReportItemBlock.block_id).where(
                    m.ReportItemBlock.item_id.in_([it.id for it in rows])
                )
            ).scalars().all()
        )
    for it in rows:
        if it.src:
            snap = _src_ref(s, it)[2]
            out |= {b for b in str(snap.get("이슈") or "").split(", ") if b}
    return out


def add_items(meeting_id: str, block_ids: list[str], form: str = "detail") -> int:
    """고른 이슈를 장으로 만든다 (F6). 이미 실린 이슈는 건너뛴다. 돌려주는 것은 더한 수."""
    now = datetime.datetime.now()
    made = 0
    with session() as s:
        used = _block_ids_on(s, meeting_id)
        order = _next_order(s, meeting_id)
        dept_id = (s.get(m.Meeting, meeting_id)).owner_dept_id
        for bid in block_ids:
            if bid in used:
                continue
            blk = s.get(m.Block, bid)
            s.add(
                m.ReportItem(
                    id=_rid("RI"),
                    meeting_id=meeting_id,
                    kind="single",
                    block_id=bid,
                    form=form,
                    tag_on=True,
                    order_no=order,
                    created_at=now,
                    dept_id=dept_id or (blk.owner_department_id if blk else None),
                )
            )
            used.add(bid)
            order += 1
            made += 1
        s.commit()
    return made


def add_summary(meeting_id: str, block_ids: list[str], line: str = "") -> str:
    """여러 이슈를 한 장으로 (F7). **요약해도 이슈는 그대로다** — 원장에서 지우지 않는다.

    요약 장은 `block_id` 가 비어 있고, 잇는 이슈는 `report_item_block` 에 있다.
    """
    now = datetime.datetime.now()
    with session() as s:
        item_id = _rid("RI")
        s.add(
            m.ReportItem(
                id=item_id,
                meeting_id=meeting_id,
                kind="summary",
                block_id=None,
                line=line.strip() or None,
                form="card",
                tag_on=True,
                order_no=_next_order(s, meeting_id),
                created_at=now,
                dept_id=(s.get(m.Meeting, meeting_id)).owner_dept_id,
            )
        )
        s.flush()
        for i, bid in enumerate(block_ids, start=1):
            s.add(m.ReportItemBlock(item_id=item_id, block_id=bid, order_no=i))
        s.commit()
    return item_id


def _snapshot_of(s: Session, meeting_id: str, version: int | None = None) -> tuple[int, list]:
    """그 회의의 제출판에 굳은 글. 판을 주지 않으면 **최신 제출판**이다 (F10).

    돌려주는 것은 `(판 번호, 장 목록)`. 제출한 적이 없으면 `(0, [])` — 취합할 글이 없다.
    """
    q = select(m.MeetingVersion).where(m.MeetingVersion.meeting_id == meeting_id)
    if version is not None:
        q = q.where(m.MeetingVersion.version == version)
    row = s.execute(q.order_by(m.MeetingVersion.version.desc())).scalars().first()
    if row is None:
        return 0, []
    return row.version, json.loads(row.snapshot_json or "[]")


def _src_ref(s: Session, item: m.ReportItem) -> tuple[str, int, dict]:
    """참조로 실은 장이 가리키는 **판의 글** (F10) — `(부서 자료 ID, 판 번호, 그 장의 글)`.

    **참조의 정본은 「판」이고 살아 있는 `report_item` 행이 아니다** (2026-11-13 결정 H —
    「표현은 판 그대로 굳는다」). 그래서 `report_item` 을 찾아가지 않고 판에서 읽는다 —
    부서가 제출한 뒤 그 장을 빼면 행은 지워지지만 **이미 굳은 판에서는 빠지지 않는다.**
    빼기는 **다음 판**에 반영되는 일이고, 공유회는 참조한 판의 글을 계속 보인다.

    어느 부서 자료인지는 장 자신이 알고(`report_item.dept_id`) 주차는 회의가 안다
    (`meeting.week_id`) — 그 둘로 부서 자료를 찾아 **최신 판부터** 그 장을 뒤진다.

    **옛 판에 있으면 옛 판에서 읽는다** — 부서가 장을 빼고 다시 제출해도 공유회가 참조한
    판은 그대로라, 그 판의 글을 계속 보인다.

    어느 판에도 그 `ID` 가 없으면 `(부서 자료 ID, 0, {})` 다 — 부서 자료가 옮겨졌거나
    (주차·부서가 어긋남) 참조한 판 자체가 없는 자리다. 그 자리는 `_shown()` 이
    「부서 자료에서 빠진 장」으로 내보인다 — 빈 값으로 되돌아가 보통 장처럼 보이게
    두지 않는다. 화면에서도 **고치지 못한다** (`_own_item`) — 참조로 실은 장이다.
    """
    wid = s.execute(select(m.Meeting.week_id).where(m.Meeting.id == item.meeting_id)).scalar()
    mids = s.execute(
        select(m.Meeting.id)
        .where(
            m.Meeting.week_id == wid,
            m.Meeting.kind == "dept",
            m.Meeting.owner_dept_id == item.dept_id,
        )
        .order_by(m.Meeting.id)
    ).scalars().all()
    for mid in mids:
        rows = s.execute(
            select(m.MeetingVersion.version, m.MeetingVersion.snapshot_json)
            .where(m.MeetingVersion.meeting_id == mid)
            .order_by(m.MeetingVersion.version.desc())
        ).all()
        for ver, snap in rows:
            for row in json.loads(snap or "[]"):
                if row.get("ID") == item.src:
                    return mid, ver, row
    return (mids[0] if mids else ""), 0, {}


def _own_children(s: Session, item_id: str) -> list[str]:
    """그 요약 장이 잇는 이슈 (F7) — `report_item_block` 에 있는 자기 것."""
    return list(s.execute(
        select(m.ReportItemBlock.block_id)
        .where(m.ReportItemBlock.item_id == item_id)
        .order_by(m.ReportItemBlock.order_no)
    ).scalars().all())


def _titled(s: Session, block_ids: list[str]) -> list[tuple[str, str]]:
    """이슈 ID 에 제목을 붙인다 — 제목은 `block` 에 있어 늘 지금 값이다."""
    out = []
    for bid in block_ids:
        blk = s.get(m.Block, bid)
        out.append((bid, blk.title if blk else ""))
    return out


def _shown(s: Session, item: m.ReportItem) -> dict[str, object]:
    """장 하나의 **표현** 한 벌 — 한 줄·형태·머리표·참조·요약이 잇는 이슈.

    참조로 실은 장(F10 취합)은 **그 장이 실린 제출판의 글**을 읽는다 (2026-11-13 결정 H) —
    제출하지 않고 고친 글은 따라오지 않고, 다시 제출하면 **최신 제출판**의 글을 본다
    (`_src_ref`). 사실(현상·원인·조치)만 지금 값을 따른다 — `block` 에 있어 늘 한 벌이다.

    요약 장이 잇는 이슈도 참조면 **판에서** 읽는다 — 부서가 그 장을 빼면
    `report_item_block` 행이 함께 지워져, 행을 보고 세면 조용히 「요약 0건」이 된다.

    참조가 아닌 보통 장은 자기 값이고 「참조 판」은 `0`, 「빠진 장」은 거짓이다.
    참조인데 판 어디에도 그 장이 없으면 **「빠진 장」이 참이다** (`_src_ref`).
    """
    if not item.src:
        return {
            "한 줄": str(item.line or ""),
            "형태": str(item.form or "detail"),
            "머리표": bool(item.tag_on),
            "참조": "",
            "참조 판": 0,
            "빠진 장": False,
            "이슈들": _own_children(s, item.id) if item.kind == "summary" else [],
        }
    src_mid, ver, snap = _src_ref(s, item)
    bids = [b for b in str(snap.get("이슈") or "").split(", ") if b]
    return {
        "한 줄": str(snap.get("한 줄") or ""),
        "형태": str(snap.get("형태") or item.form or "detail"),
        "머리표": bool(snap["머리표"]) if "머리표" in snap else bool(item.tag_on),
        "참조": src_mid,
        "참조 판": ver,
        "빠진 장": not snap,
        "이슈들": bids if item.kind == "summary" else [],
    }


def _no_block_title(shown: dict[str, object], kid_n: int) -> str:
    """이슈 한 건이 아닌 장의 제목 — 요약 장과 **빠진 장**.

    빠진 장을 「요약 0건」처럼 보이게 두지 않는다 — 판에서 사라진 것이 제목에 드러난다.
    """
    if shown["빠진 장"]:
        return MISSING_SRC
    return str(shown["한 줄"]) or f"요약 {kid_n}건"


def items(meeting_id: str) -> list[dict[str, object]]:
    """장 목록 한 판 — 위에서 아래 순서 그대로."""
    out: list[dict[str, object]] = []
    with session() as s:
        rows = s.execute(
            select(m.ReportItem)
            .where(m.ReportItem.meeting_id == meeting_id)
            .order_by(m.ReportItem.order_no, m.ReportItem.created_at)
        ).scalars().all()
        for no, it in enumerate(rows, start=1):
            sh = _shown(s, it)
            blk = s.get(m.Block, it.block_id) if it.block_id else None
            kids = _titled(s, list(sh["이슈들"]))
            dept = s.get(m.Department, it.dept_id) if it.dept_id else None
            form = str(sh["형태"])
            out.append({
                "ID": it.id,
                "번호": no,
                "종류": it.kind,
                "종류 이름": ITEM_KIND_LABELS.get(it.kind, it.kind),
                "형태": form,
                "형태 이름": FORM_LABELS.get(form, form),
                "제목": blk.title if blk else _no_block_title(sh, len(kids)),
                "한 줄": sh["한 줄"],
                "이슈": it.block_id or ", ".join(b for b, _ in kids),
                "상태": blk.status if blk else "",
                "부서": dept.name if dept else "",
                "머리표": sh["머리표"],
                "참조": sh["참조"],
                "참조 판": sh["참조 판"],
                "빠진 장": sh["빠진 장"],
                "요약 건수": len(kids),
            })
    return out


def item_detail(item_id: str) -> dict[str, object]:
    """고른 장 한 벌 — **표현**(한 줄·형태·머리표)과 **사실**(현상·원인·조치·결정 필요).

    참조로 실은 장이면 표현은 **「참조 판」에 굳은 글**이고 고칠 수 없다 (F10).
    """
    with session() as s:
        it = s.get(m.ReportItem, item_id)
        sh = _shown(s, it)
        blk = s.get(m.Block, it.block_id) if it.block_id else None
        kids = _titled(s, list(sh["이슈들"]))
        return {
            "ID": it.id,
            "종류": it.kind,
            "형태": sh["형태"],
            "한 줄": sh["한 줄"],
            "머리표": sh["머리표"],
            "참조": sh["참조"],
            "참조 판": sh["참조 판"],
            "빠진 장": sh["빠진 장"],
            "block_id": it.block_id or "",
            "제목": blk.title if blk else _no_block_title(sh, len(kids)),
            "상태": blk.status if blk else "",
            "요약": kids,
            **({f: getattr(blk, f) or "" for f in FACT_FIELDS} if blk else
               {f: "" for f in FACT_FIELDS}),
        }


def _own_item(s: Session, item_id: str) -> m.ReportItem:
    """표현을 고칠 수 있는 장. **참조로 실은 장은 판에 굳어 고치지 못한다** (F10).

    고치게 두면 화면에는 판의 글이 보이고 고친 값은 어디에도 안 보인다 — 조용히 사라진다.
    """
    it = s.get(m.ReportItem, item_id)
    if it.src:
        src_mid, ver, snap = _src_ref(s, it)
        where = (
            f"{src_mid} 의 {ver}판에 굳은 글이다" if snap
            else f"{src_mid} 의 어느 판에도 없는 {MISSING_SRC}이다"
        )
        raise NotAllowed(
            f"참조로 실은 장은 표현을 고치지 않는다 — {where}. "
            "고칠 것이 있으면 부서 자료에서 고치고 다시 제출한다"
        )
    return it


def set_line(item_id: str, line: str) -> None:
    """회의용 한 줄 — **표현이다.** `block` 을 고치지 않는다."""
    with session() as s:
        _own_item(s, item_id).line = line.strip() or None
        s.commit()


def set_form(item_id: str, form: str) -> None:
    """형태 전환 (F6). 틀만 바뀌고 사실은 그대로다."""
    with session() as s:
        _own_item(s, item_id).form = form
        s.commit()


def set_tag_on(item_id: str, on: bool) -> None:
    with session() as s:
        _own_item(s, item_id).tag_on = on
        s.commit()


def _log_field(s: Session, block_id: str, field: str, new: str | None) -> None:
    """(AI 값, 사람 값)을 **둘 다** 남긴다 (`CLAUDE.md` §6-2).

    AI 가 채운 값은 추출(S6)이 `ai_field_log` 에 적어 두었다 — 그 값을 그대로 잇고 옆에
    사람이 적은 값을 둔다. AI 가 채운 적이 없는 칸이면 AI 값은 비어 있다.
    """
    ai = s.execute(
        select(m.AiFieldLog.ai_value)
        .where(m.AiFieldLog.block_id == block_id, m.AiFieldLog.field == field)
        .order_by(m.AiFieldLog.created_at.desc())
    ).scalars().first()
    s.add(
        m.AiFieldLog(
            id=_rid("AFL"),
            block_id=block_id,
            field=field,
            ai_value=ai,
            human_value=new,
            model=None,  # 사람이 고친 값이다 — 모델 이름이 없다
            created_at=datetime.datetime.now(),
        )
    )


def save_fact(block_id: str, values: dict[str, str]) -> None:
    """회의자료에서 고친 **사실**은 `block` 으로 들어간다 — 이슈 원장과 같은 한 벌이다 (F8).

    **사실 되먹임은 1차다** (2026-11-13 결정) — 여기서 고치면 그 이슈가 바로 바뀌고
    원장·부서 자료도 같은 값을 본다. 두 가지가 함께 따라온다.

    - 칸을 고치면 「상세 한 장」은 **「작성 중」(`wip`)으로 내려간다** (원본 `docs/03` 의
      `block.draft_state`) — 사실이 바뀌었는데 초안을 「완료」로 둘 수 없다.
    - 고친 칸마다 (AI 값, 사람 값)을 `ai_field_log` 에 남긴다 (`CLAUDE.md` §6-2).
    """
    with session() as s:
        blk = s.get(m.Block, block_id)
        changed = 0
        for f in FACT_FIELDS:
            if f not in values:
                continue
            new = (values.get(f) or "").strip() or None
            if new == getattr(blk, f):
                continue
            setattr(blk, f, new)
            _log_field(s, block_id, f, new)
            changed += 1
        if changed:
            blk.draft_state = "wip"
        s.commit()


def move_item(item_id: str, up: bool) -> bool:
    """「↑ 위로 · ↓ 아래로」 (F6, `requirements.md` §2-E). 끝에서는 `False` 를 돌려준다.

    끌어서 놓기는 쓰지 않는다 — Streamlit 기본 위젯에 없다 (`docs/디자인_규칙.md` §3).
    """
    with session() as s:
        it = s.get(m.ReportItem, item_id)
        rows = s.execute(
            select(m.ReportItem)
            .where(m.ReportItem.meeting_id == it.meeting_id)
            .order_by(m.ReportItem.order_no, m.ReportItem.created_at)
        ).scalars().all()
        at = [r.id for r in rows].index(item_id)
        to = at - 1 if up else at + 1
        if to < 0 or to >= len(rows):
            return False
        order = [r.id for r in rows]
        order[at], order[to] = order[to], order[at]
        for no, rid in enumerate(order, start=1):
            s.get(m.ReportItem, rid).order_no = no
        s.commit()
        return True


def remove_item(item_id: str) -> dict[str, object]:
    """장을 뺀다. **바로 빼고 되돌리기를 준다** (`docs/디자인_규칙.md` §3).

    돌려주는 것은 `restore_item()` 에 그대로 넣는 되돌리기 꾸러미다.
    이슈 자체는 지우지 않는다 — 장은 **표현**이고 이슈는 원장에 남는다.
    """
    with session() as s:
        it = s.get(m.ReportItem, item_id)
        snap = {c.name: getattr(it, c.name) for c in m.ReportItem.__table__.columns}
        kids = s.execute(
            select(m.ReportItemBlock.block_id, m.ReportItemBlock.order_no).where(
                m.ReportItemBlock.item_id == item_id
            )
        ).all()
        s.execute(
            m.ReportItemBlock.__table__.delete().where(m.ReportItemBlock.item_id == item_id)
        )
        s.delete(it)
        s.commit()
    return {"item": snap, "children": [(b, o) for b, o in kids]}


def restore_item(undo: dict[str, object]) -> str:
    """빼기 되돌리기. 같은 ID·같은 자리로 돌아온다."""
    with session() as s:
        s.add(m.ReportItem(**undo["item"]))
        s.flush()
        for bid, order in undo["children"]:
            s.add(m.ReportItemBlock(item_id=undo["item"]["id"], block_id=bid, order_no=order))
        s.commit()
    return str(undo["item"]["id"])


def candidates(meeting_id: str, department_id: str | None = None) -> list[dict[str, object]]:
    """후보 이슈 — 아직 이 회의에 실리지 않은 열린 이슈 (F6).

    원장 한 줄을 그대로 쓴다 (`issues.ledger`) — 회의자료에서도 호선·단계·경보가 함께 보인다.
    """
    with session() as s:
        used = _block_ids_on(s, meeting_id)
    return [
        r for r in issues.ledger(department_id=department_id)
        if r["ID"] not in used and r["상태"] in OPEN_STATUSES
    ]


def carry_over(meeting_id: str) -> int:
    """지난 주 같은 자료의 장을 **이어받는다** (`meeting.start_mode` = `carry`).

    진행 중인 이슈만 가져온다 — 종결된 것은 다시 올리지 않는다. 글을 베끼지 않고
    그 이슈로 장을 새로 만든다. 돌려주는 것은 더한 수.
    """
    with session() as s:
        mt = s.get(m.Meeting, meeting_id)
        last = s.execute(
            select(m.Meeting.id).where(
                m.Meeting.week_id == shift_week(mt.week_id, -1),
                m.Meeting.kind == mt.kind,
                m.Meeting.owner_dept_id == mt.owner_dept_id,
                m.Meeting.hull_id == mt.hull_id,
            )
        ).scalars().first()
        if last is None:
            return 0
        rows = s.execute(
            select(m.ReportItem.block_id, m.ReportItem.form)
            .where(m.ReportItem.meeting_id == last, m.ReportItem.block_id.is_not(None))
            .order_by(m.ReportItem.order_no)
        ).all()
        open_rows = [
            (b, f) for b, f in rows
            if (blk := s.get(m.Block, b)) is not None and blk.status in OPEN_STATUSES
        ]
    made = 0
    for bid, form in open_rows:
        made += add_items(meeting_id, [bid], form or "detail")
    if made:
        with session() as s:
            s.get(m.Meeting, meeting_id).start_mode = "carry"
            s.commit()
    return made


# ── F9 부서 제출 ───────────────────────────────────────────────────────────
def _snapshot(s: Session, meeting_id: str) -> list[dict[str, object]]:
    """판에 굳는 글. **회의에서 본 그대로** 남는다 — 뒤에 사실이 바뀌어도 이 글은 안 바뀐다.

    장의 `ID` 도 적는다 — 공유회가 이 판을 취합할 때 `report_item.src` 가 그 장을
    가리키고, 뒤에 **판에서** 그 `ID` 로 글을 찾는다 (F10, `_src_ref`).
    살아 있는 `report_item` 행을 찾지 않으므로 부서가 그 장을 빼도 공유회는 멀쩡하다.
    """
    out = []
    for row in items(meeting_id):
        snap = {
            k: row[k]
            for k in ("ID", "번호", "종류", "형태", "제목", "한 줄", "이슈", "상태", "머리표")
        }
        if row["이슈"] and row["종류"] == "single":
            blk = s.get(m.Block, str(row["이슈"]))
            if blk is not None:
                snap |= {FACT_LABELS[f]: getattr(blk, f) or "" for f in FACT_FIELDS}
        out.append(snap)
    return out


def submit(meeting_id: str) -> int:
    """부서 회의자료를 제출한다 (F9) — `status` 가 「제출」이 되고 **판이 하나 오른다.**

    1차는 **상태 표시만**이다. 마감 시각·경고·재제출 규칙은 2차다 (`requirements.md` §1-3).
    「제출」은 **부서 자료의 말이다** — 공유회·팀장 정보회의는 「발행」이고 그것은 S8 몫이라
    여기서 막는다. 「종결」은 이슈에 쓰는 말이라 여기 없다 (`CLAUDE.md` §6-7).
    """
    now = datetime.datetime.now()
    with session() as s:
        mt = s.get(m.Meeting, meeting_id)
        if mt.kind != "dept":
            raise NotAllowed(
                f"「제출」은 부서 자료의 말이다 — {KIND_LABELS.get(mt.kind, mt.kind)}는 "
                "「발행」이고, 판 고정은 S8(발행·PPTX)에서 한다"
            )
        mt.version = (mt.version or 0) + 1
        mt.status = "제출"
        s.add(
            m.MeetingVersion(
                id=_rid("MV"),
                meeting_id=meeting_id,
                version=mt.version,
                published_at=now,
                snapshot_json=json.dumps(_snapshot(s, meeting_id), ensure_ascii=False),
            )
        )
        s.commit()
        return mt.version


def versions(meeting_id: str) -> list[dict[str, object]]:
    with session() as s:
        rows = s.execute(
            select(m.MeetingVersion)
            .where(m.MeetingVersion.meeting_id == meeting_id)
            .order_by(m.MeetingVersion.version.desc())
        ).scalars().all()
        return [
            {"판": r.version, "때": r.published_at.strftime("%Y-%m-%d %H:%M"),
             "장": len(json.loads(r.snapshot_json or "[]"))}
            for r in rows
        ]


# ── F10 취합 ───────────────────────────────────────────────────────────────
def submitted(wid: str) -> list[dict[str, object]]:
    """그 주차에 제출된 부서 자료 — 취합할 거리. 실리는 것은 그 자료의 **최신 제출판**이다.

    **1차에서 이 목록을 쓰는 것은 부서 현안 공유회뿐이다** (2026-11-13 결정). 원본
    `docs/07` 은 팀장 정보회의 자료를 「**공유회 채택분** + 원장에서 추가」로 적었다 —
    팀장 정보회의가 부서 제출판을 바로 가져가는 길이 아니다. 「공유회에서 가져오기」는
    **2차**고, 1차의 팀장 정보회의는 후보 이슈에서 장을 직접 올린다.
    """
    return [r for r in meetings(wid, kind="dept") if r["상태"] == "제출" and r["장"]]


def collect(meeting_id: str, source_meeting_ids: list[str]) -> int:
    """부서 **최신 제출판**을 참조로 싣는다 (F10). **글을 복사하지 않는다.**

    취합이 가리키는 것은 살아 있는 부서 자료가 아니라 **판**이다 (2026-11-13 결정).

    - **표현**(한 줄·형태·머리표)은 **그 판의 글**이다 (`_shown`). 두 경우가 갈린다 —
      부서가 **제출하지 않고 고친 글은 따라오지 않고**(판에 안 들어간 수정이다),
      부서가 **다시 제출하면 새 판의 글을 본다**(참조는 「최신 제출판」이다, 결정 §2-H).
      그 사이에 공유회가 본 글은 그때의 최신 판 그대로다.
    - **사실**(현상·원인·조치·결정 필요)은 지금 값을 따른다 — `block` 에 있어 한 벌이다.
    - 제출 뒤에 부서가 **더한 장은 실리지 않는다** — 판에 없는 장이다.
    - 어느 판을 참조했는지는 `items()` 의 「참조 판」이다.

    이미 실은 장(`src`)과 이미 실은 이슈(`block_id`)는 건너뛴다 — `add_items` 와 같은
    규칙이다 (같은 일을 다르게 하지 않는다). 제출한 적이 없는 자료는 실을 글이 없다.
    돌려주는 것은 더한 수.

    **부서 현안 공유회(`share`)에서만** 한다 (2026-11-13 결정 L, `submitted`) — 팀장
    정보회의가 부서 제출판을 바로 가져가는 길은 1차에 없다. 화면이 「취합」을 공유회에만
    보이는 것으로는 규칙이 서지 않으므로 여기서 막는다.
    """
    now = datetime.datetime.now()
    made = 0
    with session() as s:
        mt = s.get(m.Meeting, meeting_id)
        if mt.kind != "share":
            raise NotAllowed(
                f"부서 제출판 취합은 {KIND_LABELS['share']}에서 한다 — "
                f"{KIND_LABELS.get(mt.kind, mt.kind)}({meeting_id})에서는 하지 않는다. "
                "팀장 정보회의 자료는 공유회 채택분에서 오는 것이고(원본 `docs/07`) "
                "그 길은 2차다 — 1차에서는 후보 이슈에서 장을 직접 올린다"
            )
        have = {
            src for src in s.execute(
                select(m.ReportItem.src).where(m.ReportItem.meeting_id == meeting_id)
            ).scalars().all() if src
        }
        used = _block_ids_on(s, meeting_id)
        order = _next_order(s, meeting_id)
        for src_mid in source_meeting_ids:
            src_mt = s.get(m.Meeting, src_mid)
            _, rows = _snapshot_of(s, src_mid)
            for row in rows:
                src_id = str(row["ID"])
                # 판의 「이슈」는 이슈 한 건이면 그 이슈, 요약 장이면 묶은 이슈들이다
                bids = [b for b in str(row["이슈"] or "").split(", ") if b]
                if src_id in have or used & set(bids):
                    continue
                s.add(
                    m.ReportItem(
                        id=_rid("RI"),
                        meeting_id=meeting_id,
                        kind=str(row["종류"]),
                        block_id=bids[0] if row["종류"] == "single" and bids else None,
                        # 표현은 판에서 읽는다 — 자기 값을 두지 않는다 (`_shown`)
                        order_no=order,
                        created_at=now,
                        src=src_id,
                        dept_id=src_mt.owner_dept_id,
                    )
                )
                # 요약 장이 잇는 이슈(`report_item_block`)는 베끼지 않는다 — 참조라
                # `_shown()` 이 **판의 「이슈」**에서 읽는다
                have.add(src_id)
                used |= set(bids)
                order += 1
                made += 1
        s.commit()
    return made


# ── F12 회의 진행 ──────────────────────────────────────────────────────────
def start_run(meeting_id: str) -> None:
    """진행을 시작한 시각을 적는다 (`meeting.held_at`). 이미 적혀 있으면 그대로 둔다."""
    with session() as s:
        mt = s.get(m.Meeting, meeting_id)
        if mt.held_at is None:
            mt.held_at = datetime.datetime.now()
            s.commit()


def add_comment(meeting_id: str, block_id: str | None, text: str, kind: str = "comment") -> None:
    """회의 진행 한 줄 (F12).

    **`kind="decision"` 이면 그 이슈의 `decision_needed` 를 비운다** — 정해진 것을
    「결정 필요」로 남겨 두면 다음 주에 같은 안건이 또 올라온다.
    결정 글 자체는 `meeting_comment` 에 남으므로 사라지는 것이 아니다. 비운 자리는
    (AI 값, 사람 값)으로 `ai_field_log` 에 남는다 (`CLAUDE.md` §6-2).

    **빈 글은 적지 않는다.** 빈 결정을 받으면 정해진 것은 어디에도 안 남고
    「결정 필요」 표시만 사라진다 — 글이 지워지는 것과 같다.
    """
    now = datetime.datetime.now()
    text = text.strip()
    if not text:
        raise NotAllowed("빈 글은 기록하지 않는다 — 적을 것이 없으면 아무것도 바뀌지 않는다")
    with session() as s:
        s.add(
            m.MeetingComment(
                id=_rid("MC"),
                meeting_id=meeting_id,
                block_id=block_id,
                text=text,
                kind=kind,
                created_at=now,
            )
        )
        if kind == "decision" and block_id:
            blk = s.get(m.Block, block_id)
            if blk.decision_needed is not None:
                _log_field(s, block_id, "decision_needed", None)
                blk.decision_needed = None
        s.commit()


def comments(meeting_id: str, block_id: str | None = None) -> list[dict[str, str]]:
    """그 회의의 기록 — 최근 것이 위로."""
    with session() as s:
        q = select(m.MeetingComment).where(m.MeetingComment.meeting_id == meeting_id)
        if block_id:
            q = q.where(m.MeetingComment.block_id == block_id)
        rows = s.execute(q.order_by(m.MeetingComment.created_at.desc())).scalars().all()
        return [
            {"갈래": COMMENT_LABELS.get(r.kind, r.kind), "kind": r.kind, "이슈": r.block_id or "",
             "글": r.text, "때": r.created_at.strftime("%Y-%m-%d %H:%M")}
            for r in rows
        ]


# ── F13 종결 승인·보류 ─────────────────────────────────────────────────────
def _closure_of(s: Session, block_id: str) -> m.Closure | None:
    """그 이슈의 종결 요청 행. **이슈마다 한 행**이고, 없으면 `None`.

    `one_or_none()` 이라 행이 둘이면 바로 드러난다 — 「어느 쪽이 정본인가」를 묻지 않게
    한다. 행을 만드는 곳은 `decide_closure()` 하나고, 거기서 먼저 이 함수로 찾는다.
    """
    return s.execute(
        select(m.Closure).where(m.Closure.block_id == block_id)
    ).scalars().one_or_none()


def closure_pending(meeting_id: str) -> list[dict[str, object]]:
    """이 회의에 실린 장 가운데 **「종결요청」인 이슈** (F13).

    「실린」은 `_block_ids_on` 의 세 길 전부다 — **요약 장으로만 실린 이슈도 여기 나오고
    승인할 수 있다** (사람 결정, 2026-11-13). 요약했다고 안건에서 빠지는 것이 아니다.

    조치 내용은 종결 요청 행(`closure.action_text`)에 있고, 없으면 이슈의 조치를 쓴다.
    **조치 내용이 없으면 승인할 수 없다** (`CLAUDE.md` §6-7).

    「결정」 칸의 「대기」는 **저장 값이 아니라 결정이 아직 없다는 표시**다 (`DECISIONS`).
    """
    out: list[dict[str, object]] = []
    with session() as s:
        for bid in sorted(_block_ids_on(s, meeting_id)):
            blk = s.get(m.Block, bid)
            if blk is None or blk.status != "종결요청":
                continue
            row = _closure_of(s, bid)
            out.append({
                "block_id": bid,
                "제목": blk.title,
                "조치": (row.action_text if row else None) or blk.action_text or "",
                "요청 주차": (row.requested_week_id if row else "") or "",
                "결정": (row.decision if row else "") or "대기",
            })
    return out


def decide_closure(meeting_id: str, block_id: str, decision: str) -> None:
    """종결요청을 **승인·보류**한다 (F13).

    - 승인 → `block.status` 가 「종결」이 되고 `closure` 에 승인이 남는다
    - 보류 → `closure` 에 보류만 남고 상태는 「종결요청」 그대로다 — 다음 주에 다시 올라온다

    **막는 것 다섯.** 화면이 버튼을 가려 주는 것으로는 규칙이 서지 않는다.

    1. 결정은 「승인」·「보류」뿐이다 — 아무 글이나 `closure.decision` 에 들어가면
       화면 칩이 뜻 없는 말을 내보인다
    2. **부서 현안 공유회(`share`)에서만** 한다 (`CLAUDE.md` §6-7) — 부서 자료 회의
       ID 로 승인이 되면 부서가 스스로 종결하는 길이 열린다
    3. **그 공유회 안건에 올라 있는 이슈만** 한다 — 종결은 공유회에서 **함께 본 뒤에**
       정하는 일이다 (`CLAUDE.md` §6-7). 안건에 없는 이슈가 승인되면 아무도 보지 않은
       종결이 남는다. 안건은 `closure_pending()` 이 내보이는 것과 같은 한 벌이다
    4. **「종결요청」인 이슈만** 승인·보류한다 — 신규·진행이 한 번에 「종결」이 되면
       상태 전이를 건너뛴다
    5. **조치 내용이 없으면 승인하지 않는다** — 「조치 내용 필수」(`CLAUDE.md` §6-7)

    기획 주관자가 홈(F19)에서 승인하는 길은 S10 이고, 사례 카드로 올리는 일은 **S9** 다.
    여기서는 상태와 기록까지다.
    """
    now = datetime.datetime.now()
    if decision not in DECISIONS:
        raise NotAllowed(
            f"종결 결정은 {' · '.join(DECISIONS)} 뿐이다 — 「{decision}」은 받지 않는다"
        )
    with session() as s:
        mt = s.get(m.Meeting, meeting_id)
        if mt.kind != "share":
            raise NotAllowed(
                f"종결 승인은 {KIND_LABELS['share']}에서 한다 — "
                f"{KIND_LABELS.get(mt.kind, mt.kind)}({meeting_id})에서는 하지 않는다"
            )
        if block_id not in _block_ids_on(s, meeting_id):
            raise NotAllowed(
                f"{meeting_id} 안건에 없는 이슈는 승인·보류하지 않는다 — {block_id} 는 "
                "이 공유회의 장에도, 그 장이 가리킨 제출판의 「이슈」에도 없다. "
                "부서 제출판을 취합하거나 후보에서 장으로 먼저 올린다"
            )
        blk = s.get(m.Block, block_id)
        if blk.status != "종결요청":
            raise NotAllowed(
                f"「종결요청」인 이슈만 승인·보류한다 — {block_id} 는 「{blk.status}」다. "
                "부서가 조치 내용과 함께 종결 요청을 먼저 낸다"
            )
        row = _closure_of(s, block_id)
        action = ((row.action_text if row else None) or blk.action_text or "").strip()
        if decision == "승인" and not action:
            raise NotAllowed(
                f"조치 내용이 없으면 종결을 승인하지 않는다 — {block_id} 의 조치를 먼저 적는다"
            )
        if row is None:
            row = m.Closure(
                id=_rid("CLO"),
                block_id=block_id,
                action_text=action,
                requested_week_id=blk.created_week_id,
            )
            s.add(row)
        row.decision = decision
        row.decided_week_id = mt.week_id
        row.decided_at = now
        if decision == "승인":
            blk.status = "종결"
        s.commit()
    if decision == "승인":
        # 상태가 바뀌면 주차별 진행에 한 줄 남는다 — 원장에서 왜 종결됐는지 보인다 (F4)
        issues.add_history(block_id, f"{meeting_id} 에서 종결 승인", None)


# ── F20 지시사항 ───────────────────────────────────────────────────────────
def add_directive(
    meeting_id: str, dept_id: str, text: str, due_week_id: str | None, block_id: str | None = None
) -> str:
    """지시 하나 — 내용·담당 부서·기한(주차).

    기한 주차도 `week` 를 가리키므로 **그 주차 행을 먼저 보장한다** — 아직 오지 않은 주차를
    기한으로 고를 수 있다. SQLite 는 FK 를 강제하지 않아 지금은 조용하지만 사내망에서 깨진다.
    """
    now = datetime.datetime.now()
    text = text.strip()
    if not text:
        raise NotAllowed("빈 지시는 남기지 않는다 — 무엇을 하라는 것인지 적어야 한다")
    with session() as s:
        if due_week_id:
            issues.ensure_week(s, _monday(due_week_id))
        did = _rid("DIR")
        s.add(
            m.Directive(
                id=did,
                meeting_id=meeting_id,
                block_id=block_id,
                dept_id=dept_id,
                text=text,
                due_week_id=due_week_id,
                status="열림",
                created_at=now,
            )
        )
        s.commit()
    return did


def _directive_row(s: Session, r: m.Directive) -> dict[str, object]:
    dept = s.get(m.Department, r.dept_id)
    return {
        "ID": r.id,
        "내용": r.text,
        "부서": dept.name if dept else r.dept_id,
        "부서 ID": r.dept_id,
        "기한": r.due_week_id or "",
        "상태": r.status,
        "낸 회의": r.meeting_id,
        "낸 주차": (s.get(m.Meeting, r.meeting_id)).week_id,
        "이슈": r.block_id or "",
        "보고": r.done_note or "",
        "끝낸 주차": r.done_week_id or "",
    }


def directives_of(meeting_id: str) -> list[dict[str, object]]:
    """이 회의에서 낸 지시."""
    with session() as s:
        rows = s.execute(
            select(m.Directive)
            .where(m.Directive.meeting_id == meeting_id)
            .order_by(m.Directive.created_at)
        ).scalars().all()
        return [_directive_row(s, r) for r in rows]


def directives_for(dept_id: str, wid: str) -> list[dict[str, object]]:
    """그 부서가 받은 지시 — 부서 회의자료 **맨 위**에 나온다 (F20).

    **낸 주차부터** 보인다 (2026-11-13 결정) — 그 주 안에 공유회가 열리면 그 주 자료에
    바로 올라와야 한다.

    보이는 것은 **아직 열린 지시(「열림」)와 그 주에 끝낸 지시**다. 끝낸 것이 그 자리에서
    곧바로 사라지면 한 줄 보고가 그 주 자료에 안 보여, 무엇을 보고했는지 회의에서 알 수 없다.
    """
    with session() as s:
        rows = s.execute(
            select(m.Directive)
            .where(m.Directive.dept_id == dept_id)
            .order_by(m.Directive.created_at)
        ).scalars().all()
        out = [_directive_row(s, r) for r in rows]
    return [
        r for r in out
        if str(r["낸 주차"]) <= wid
        and (r["상태"] == "열림" or str(r["끝낸 주차"]) == wid)
    ]


def finish_directive(directive_id: str, note: str, wid: str | None = None) -> None:
    """**한 줄 보고로 완료**한다 (F20).

    **보고가 비면 완료되지 않는다** — 무엇을 했는지 없이 완료만 남으면, 다음 주 회의에서
    그 지시가 어떻게 됐는지 아무도 모른다.
    """
    note = note.strip()
    if not note:
        raise NotAllowed("한 줄 보고가 없으면 지시를 완료하지 않는다 — 무엇을 했는지 적는다")
    wid = wid or issues.week_id()
    with session() as s:
        issues.ensure_week(s, _monday(wid))  # `done_week_id` 도 `week` 를 가리킨다
        r = s.get(m.Directive, directive_id)
        r.done_note = note
        r.done_week_id = wid
        r.status = "완료"
        s.commit()
