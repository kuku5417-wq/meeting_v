"""이슈 원장 — 조회·등록·주간 업데이트·지식 매핑 (F2 · F3 · F4).

화면(`views/ledger.py`)은 여기만 부른다. DB 를 직접 열지 않는다.

**ID 는 사람이 읽을 수 있게** (`CLAUDE.md` §6-8). 유형이 바뀌어도 ID 를 새로 발급하지 않는다 —
접두어는 **최초 등록 유형**이고 `block_type` 만 바뀐다.

**매핑은 기준정보 ID 로 한다** (§6-5). 매핑 못 한 표기는 `raw_text` 로 남고,
사람이 고르면 `target_id` 를 채우면서 `alias` 에 더한다 — 다음부터는 자동으로 걸린다.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules import models as m
from modules.db import session
from modules.sn_util import ensure_sn

# 최초 등록 유형 → ID 접두어 (`docs/03` §1)
PREFIX = {"issue": "ISS", "problem": "PRB", "share": "SHR", "dashboard": "DSH"}

BLOCK_TYPES = tuple(PREFIX)
STATUSES = ("신규", "진행", "종결요청", "종결")

# 매핑 n/5 를 세는 갈래 (F3 — 호선·장비·부위·증상·원인)
MAPPING_KINDS = ("hull", "installed_equipment", "component", "symptom", "cause")


def week_id(day: datetime.date | None = None) -> str:
    """ISO 주차 ID. 예: `2026-W46`."""
    day = day or datetime.date.today()
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def ensure_week(s: Session, day: datetime.date | None = None) -> m.Week:
    """그 주차 행이 없으면 만든다. 월요일~일요일."""
    day = day or datetime.date.today()
    wid = week_id(day)
    row = s.get(m.Week, wid)
    if row is None:
        monday = day - datetime.timedelta(days=day.weekday())
        row = m.Week(id=wid, start_date=monday, end_date=monday + datetime.timedelta(days=6))
        s.add(row)
        s.flush()
    return row


def next_block_id(s: Session, block_type: str, year: int | None = None) -> str:
    """`ISS-2026-0142` 꼴. 같은 접두어·같은 해에서 이어 센다."""
    year = year or datetime.date.today().year
    head = f"{PREFIX[block_type]}-{year}-"
    used = s.execute(select(m.Block.id).where(m.Block.id.like(f"{head}%"))).scalars().all()
    nums = [int(x[len(head):]) for x in used if x[len(head):].isdigit()]
    return f"{head}{max(nums, default=0) + 1:04d}"


def _rid() -> str:
    return uuid.uuid4().hex[:16]


def create_block(
    title: str,
    block_type: str = "issue",
    owner_department_id: str | None = None,
    body: str | None = None,
    hull_text: str = "",
    equipment_text: str = "",
) -> str:
    """이슈를 하나 등록하고 ID 를 돌려준다 (F2).

    `hull_text`·`equipment_text` 는 현장 표기 그대로 받는다. 기준정보에 걸리면 `target_id` 를
    채우고, 안 걸리면 `raw_text` 만 남긴다 — 「미등록」으로 보인다 (F3).
    """
    now = datetime.datetime.now()
    with session() as s:
        week = ensure_week(s)
        bid = next_block_id(s, block_type)
        s.add(
            m.Block(
                id=bid,
                block_type=block_type,
                title=title.strip(),
                body=(body or "").strip() or None,
                status="신규",
                owner_department_id=owner_department_id,
                created_week_id=week.id,
                origin="manual",
                draft_state="none",
                important=False,
            )
        )
        s.flush()
        for kind, raw in (("hull", hull_text), ("installed_equipment", equipment_text)):
            if raw.strip():
                _add_tag(s, bid, kind, raw.strip())
        s.commit()
    return bid


def _resolve(s: Session, kind: str, raw: str) -> str | None:
    """현장 표기를 기준정보 ID 로. 못 걸면 `None` (미연결)."""
    if kind == "hull":
        sn = ensure_sn(raw)
        return sn if s.get(m.Hull, sn) is not None else None
    hit = s.execute(
        select(m.Alias.target_id).where(m.Alias.text == raw, m.Alias.target_kind == kind)
    ).scalars().first()
    if hit:
        return hit
    cls = {"installed_equipment": m.InstalledEquipment, "component": m.Component}.get(kind)
    if cls is not None and s.get(cls, raw) is not None:
        return raw
    return None


def _add_tag(s: Session, block_id: str, kind: str, raw: str) -> None:
    target = _resolve(s, kind, raw)
    s.add(
        m.BlockTag(
            id=_rid(),
            block_id=block_id,
            kind=kind,
            target_id=target,
            raw_text=raw,
            confirmed=bool(target),
            dismissed=False,
        )
    )


def add_tag(block_id: str, kind: str, raw: str) -> bool:
    """태그 하나를 더한다. 기준정보에 걸렸으면 `True` (F3)."""
    with session() as s:
        _add_tag(s, block_id, kind, raw)
        s.commit()
        return _resolve(s, kind, raw) is not None


def mapping_score(s: Session, block_id: str) -> tuple[int, int]:
    """매핑 n/5 — 갈래 다섯 중 몇 개가 기준정보에 걸렸나 (F2 그리드)."""
    rows = s.execute(
        select(m.BlockTag.kind).where(
            m.BlockTag.block_id == block_id,
            m.BlockTag.target_id.is_not(None),
            m.BlockTag.dismissed.is_not(True),
        )
    ).scalars().all()
    return len({k for k in rows if k in MAPPING_KINDS}), len(MAPPING_KINDS)


def add_history(block_id: str, note: str, status: str | None = None) -> None:
    """주차별 진행 한 줄 (F4). 상태를 함께 바꿀 수 있다."""
    now = datetime.datetime.now()
    with session() as s:
        week = ensure_week(s)
        blk = s.get(m.Block, block_id)
        s.add(
            m.BlockHistory(
                id=_rid(),
                block_id=block_id,
                week_id=week.id,
                department_id=blk.owner_department_id if blk else None,
                status=status or (blk.status if blk else None),
                note=note.strip(),
                created_at=now,
            )
        )
        if status and blk is not None:
            blk.status = status
        s.commit()


def history(block_id: str) -> list[dict[str, str]]:
    """그 이슈의 주차별 진행 — 최근 것이 위로."""
    with session() as s:
        rows = s.execute(
            select(m.BlockHistory)
            .where(m.BlockHistory.block_id == block_id)
            .order_by(m.BlockHistory.created_at.desc())
        ).scalars().all()
        return [
            {"주차": r.week_id, "상태": r.status or "", "한 줄": r.note or "",
             "적은 때": r.created_at.strftime("%Y-%m-%d %H:%M")}
            for r in rows
        ]


def tags(block_id: str) -> list[dict[str, str]]:
    """그 이슈의 태그. 미연결은 `연결`이 빈 칸이다."""
    with session() as s:
        rows = s.execute(
            select(m.BlockTag).where(m.BlockTag.block_id == block_id, m.BlockTag.dismissed.is_not(True))
        ).scalars().all()
        return [
            {"갈래": r.kind, "현장 표기": r.raw_text or "", "연결": r.target_id or "",
             "상태": "연결됨" if r.target_id else "미등록"}
            for r in rows
        ]


def ledger(status: str | None = None, department_id: str | None = None) -> list[dict[str, object]]:
    """원장 그리드 한 판 (F2).

    칸: ID · 유형 · 부서 · 호선 · 장비 · 제목 · 금주 진행 · 매핑 n/5 · 상태
    """
    this_week = week_id()
    out: list[dict[str, object]] = []
    with session() as s:
        q = select(m.Block)
        if status:
            q = q.where(m.Block.status == status)
        if department_id:
            q = q.where(m.Block.owner_department_id == department_id)
        for b in s.execute(q.order_by(m.Block.id.desc())).scalars().all():
            tag_rows = s.execute(
                select(m.BlockTag.kind, m.BlockTag.target_id, m.BlockTag.raw_text).where(
                    m.BlockTag.block_id == b.id, m.BlockTag.dismissed.is_not(True)
                )
            ).all()
            pick = {k: (t or r or "") for k, t, r in tag_rows}
            note = s.execute(
                select(m.BlockHistory.note)
                .where(m.BlockHistory.block_id == b.id, m.BlockHistory.week_id == this_week)
                .order_by(m.BlockHistory.created_at.desc())
            ).scalars().first()
            n, total = mapping_score(s, b.id)
            dept = s.get(m.Department, b.owner_department_id) if b.owner_department_id else None
            out.append({
                "ID": b.id,
                "유형": b.block_type,
                "부서": dept.name if dept else "",
                "호선": pick.get("hull", ""),
                "장비": pick.get("installed_equipment", ""),
                "제목": b.title,
                "금주 진행": note or "",
                "매핑": f"{n}/{total}",
                "상태": b.status,
            })
    return out


def counts() -> dict[str, int]:
    """상태별 건수. 홈(F19)과 원장 머리줄에서 쓴다."""
    with session() as s:
        rows = s.execute(select(m.Block.status, func.count()).group_by(m.Block.status)).all()
        return {k: n for k, n in rows}
