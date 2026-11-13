"""이슈 원장 — 조회·등록·주간 업데이트·지식 매핑 (F2 · F3 · F4).

화면(`views/ledger.py`)은 여기만 부른다. DB 를 직접 열지 않는다.

**ID 는 사람이 읽을 수 있게** (`CLAUDE.md` §6-8). 유형이 바뀌어도 ID 를 새로 발급하지 않는다 —
접두어는 **최초 등록 유형**이고 `block_type` 만 바뀐다.

**매핑은 기준정보 ID 로 한다** (§6-5). 매핑 못 한 표기는 `raw_text` 로 남고,
사람이 고르면 `target_id` 를 채우면서 `alias` 에 더한다 — 다음부터는 자동으로 걸린다.
"""
from __future__ import annotations

import datetime
import hashlib
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config.paths import DATA_DIR, photo_path

from modules import milestone
from modules import models as m
from modules.db import session
from modules.sn_util import ensure_sn

# 최초 등록 유형 → ID 접두어 (`docs/03` §1)
PREFIX = {"issue": "ISS", "problem": "PRB", "share": "SHR", "dashboard": "DSH"}

BLOCK_TYPES = tuple(PREFIX)
STATUSES = ("신규", "진행", "종결요청", "종결")

# 원장에서 사람이 **고를 수 있는** 상태. 「종결」이 빠져 있다.
# **종결은 부서가 하지 않는다** (`CLAUDE.md` §6-7) — 부서는 「종결 요청」(조치 내용 필수)까지고,
# 승인은 부서 현안 공유회의 진행 화면(S7)이나 기획 주관자가 홈(F19)에서 한다.
# `STATUSES` 는 DB 에 들어갈 수 있는 값 전부라 「종결」을 그대로 둔다 — 거르기에도 쓴다.
ASSIGNABLE_STATUSES = ("신규", "진행", "종결요청")

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
    occurred_on: datetime.date | None = None,
) -> str:
    """이슈를 하나 등록하고 ID 를 돌려준다 (F2).

    `hull_text`·`equipment_text` 는 현장 표기 그대로 받는다. 기준정보에 걸리면 `target_id` 를
    채우고, 안 걸리면 `raw_text` 만 남긴다 — 「미등록」으로 보인다 (F3).

    `occurred_on` 은 **일이 난 날**이다. 적은 날이 아니라서 따로 받는다 — 그 날의 호선 단계를
    잡는 데 쓴다 (`stage_at`). 모르면 비워 둔다.
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
                occurred_on=occurred_on,
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


def resolves(kind: str, raw: str) -> str | None:
    """현장 표기가 기준정보에 걸리는가. 걸리면 그 ID, 아니면 `None`.

    `_resolve` 를 세션 밖에서 쓰라고 연 창구다 — 기록함이 메모에서 호선을 읽을 때 쓴다.
    """
    with session() as s:
        return _resolve(s, kind, raw)


def known_marks(kind: str) -> list[str]:
    """별칭 사전에 적힌 **현장 표기**들. 긴 것부터 준다.

    `DG2`·`C/P #3` 처럼 사람이 쓰는 말이다. 메모에서 장비를 읽을 때 이 말들을 찾는다.
    긴 것부터인 이유는 `씰` 이 `메카니컬씰` 을 가로채지 않게 하기 위해서다.
    """
    with session() as s:
        rows = s.execute(select(m.Alias.text).where(m.Alias.target_kind == kind)).scalars().all()
    return sorted({r for r in rows if r}, key=len, reverse=True)


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

    칸: ID · 유형 · 부서 · 호선 · 장비 · 제목 · 금주 진행 · 매핑 n/5 · **단계** · 경보 · 초안 · 상태

    「단계」는 **사건 당시 호선 단계**다 (`requirements.md` §2-C). 지금과 다르면 둘 다 적는다.
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
            label, left, _ = _alert_of(s, b)
            out.append({
                "ID": b.id,
                "유형": b.block_type,
                "부서": dept.name if dept else "",
                "호선": pick.get("hull", ""),
                "장비": pick.get("installed_equipment", ""),
                "제목": b.title,
                "금주 진행": note or "",
                "매핑": f"{n}/{total}",
                "단계": _stage_label(s, b),
                "경보": f"{label} D{left:+d}" if label else (f"D{left:+d}" if left is not None else ""),
                "초안": {"none": "", "wip": "작성 중", "ok": "완료"}.get(b.draft_state or "none", ""),
                "상태": b.status,
            })
    return out


# ── 사건 당시 단계 ─────────────────────────────────────────────────────────
def _hull_of(s: Session, block_id: str) -> str | None:
    """그 블록이 걸린 호선 ID. 「미등록」(raw_text 만 있는 것)은 호선이 아니다."""
    return s.execute(
        select(m.BlockTag.target_id).where(
            m.BlockTag.block_id == block_id,
            m.BlockTag.kind == "hull",
            m.BlockTag.target_id.is_not(None),
            m.BlockTag.dismissed.is_not(True),
        )
    ).scalars().first()


def stage_at(block_id: str) -> tuple[str, str]:
    """**(사건 당시 단계, 지금 단계).** 호선이나 발생일이 없으면 그 자리는 빈 값이다.

    단계는 날짜에 따라 달라지는 값이다 (`SPEC.md` §3-3). 같은 호선이라도 어제는 시운전기간,
    오늘은 안벽기간일 수 있다 — 그래서 **일이 난 날**로 한 번, **오늘**로 한 번 잡는다.
    저장하지 않는다. 일정이 바뀌면 다음에 볼 때 따라간다.
    """
    with session() as s:
        b = s.get(m.Block, block_id)
        hull = _hull_of(s, block_id)
        if not hull:
            return "", ""
        then = milestone.stage(hull, on=b.occurred_on)[0] if b.occurred_on else ""
        return then, milestone.stage(hull)[0]


def set_occurred(block_id: str, day: datetime.date | None) -> None:
    """발생일을 고친다. 비우면 「그때 단계」가 사라진다 — 모르는 날을 지어내지 않는다.

    사람이 고른 날에는 **메모 구간이 근거가 아니다.** 메모에서 읽어 둔 근거를 지운다 (§6-3) —
    받치지 못하는 근거를 남겨 두면 나중에 그 구간이 값을 증명하는 것처럼 보인다.
    """
    with session() as s:
        blk = s.get(m.Block, block_id)
        if blk.occurred_on != day:
            s.execute(
                m.SourceSpan.__table__.delete().where(
                    m.SourceSpan.block_id == block_id,
                    m.SourceSpan.field == "occurred_on",
                )
            )
        blk.occurred_on = day
        s.commit()


def occurred_of(block_id: str) -> datetime.date | None:
    with session() as s:
        return s.get(m.Block, block_id).occurred_on


def _stage_label(s: Session, b: m.Block) -> str:
    """원장 한 줄에 넣을 단계 글. 그때와 지금이 다르면 둘 다 적는다."""
    hull = _hull_of(s, b.id)
    if not hull:
        return ""
    now = milestone.stage(hull)[0]
    then = milestone.stage(hull, on=b.occurred_on)[0] if b.occurred_on else ""
    if then and then != now:
        return f"그때 {then} · 지금 {now}"
    # 홀로 선 값은 무엇의 값인지 모른다 — 「매핑 3/5」 처럼 이름을 앞에 쓴다
    return f"단계 {now}" if now else ""


def counts() -> dict[str, int]:
    """상태별 건수. 홈(F19)과 원장 머리줄에서 쓴다."""
    with session() as s:
        rows = s.execute(select(m.Block.status, func.count()).group_by(m.Block.status)).all()
        return {k: n for k, n in rows}


# ── F21 일정 경보 ─────────────────────────────────────────────────────────
DEFAULT_ALERT_DAYS = 14  # app_setting `alert_days:<이벤트>` 의 처음 값 (docs/03)
DUE_EVENTS = ("", "STTO", "GASTO", "ACTO", "DL", "DATE")


def hull_of(s: Session, block_id: str) -> str | None:
    """그 이슈가 걸린 호선. 일정 경보의 기준이다."""
    return s.execute(
        select(m.BlockTag.target_id).where(
            m.BlockTag.block_id == block_id,
            m.BlockTag.kind == "hull",
            m.BlockTag.target_id.is_not(None),
            m.BlockTag.dismissed.is_not(True),
        )
    ).scalars().first()


def set_due(block_id: str, due_event: str, due_date: datetime.date | None, alert_days: int) -> None:
    """「~전 해결」 목표와 경보 일수를 정한다 (F21).

    **이벤트 날짜는 저장하지 않는다.** 볼 때마다 `milestone` 에서 잡는다 (`SPEC.md` §10-2) —
    일정이 당겨지면 경보가 저절로 다시 켜진다.
    """
    with session() as s:
        b = s.get(m.Block, block_id)
        b.due_event = due_event or None
        b.due_date = due_date if due_event == "DATE" else None
        b.alert_days = alert_days
        s.commit()


def _alert_of(s: Session, b: m.Block) -> tuple[str, int | None, datetime.date | None]:
    if not b.due_event:
        return "", None, None
    target = b.due_date if b.due_event == "DATE" else None
    if target is None:
        hull = hull_of(s, b.id)
        if hull:
            target = milestone.due(b.due_event, hull)
    label, left = milestone.alert(target, b.alert_days or DEFAULT_ALERT_DAYS)
    return label, left, target


def due_of(block_id: str) -> dict[str, object]:
    """그 이슈의 목표·경보 한 벌 (화면용)."""
    with session() as s:
        b = s.get(m.Block, block_id)
        label, left, target = _alert_of(s, b)
        return {
            "due_event": b.due_event or "",
            "due_date": b.due_date,
            "alert_days": b.alert_days or DEFAULT_ALERT_DAYS,
            "target": target,
            "label": label,
            "left": left,
            "hull": hull_of(s, b.id) or "",
        }


# ── F5 1차 초안 ───────────────────────────────────────────────────────────
DRAFT_FIELDS = ("body", "cause_text", "action_text", "decision_needed")


def draft(block_id: str) -> dict[str, object]:
    with session() as s:
        b = s.get(m.Block, block_id)
        return {f: getattr(b, f) or "" for f in DRAFT_FIELDS} | {
            "draft_state": b.draft_state or "none",
            "title": b.title,
            "important": bool(b.important),
        }


def save_draft(block_id: str, values: dict[str, str], done: bool) -> None:
    """「상세 한 장」의 칸을 저장한다 (F5).

    칸을 고치면 `wip`, 「초안 완료」를 누르면 `ok` 다 (`docs/03`).
    """
    with session() as s:
        b = s.get(m.Block, block_id)
        for f in DRAFT_FIELDS:
            setattr(b, f, (values.get(f) or "").strip() or None)
        b.draft_state = "ok" if done else "wip"
        s.commit()


PHOTO_ROLES = ("main", "before", "after")


def attach_photo(block_id: str, name: str, data: bytes, role: str, caption: str = "") -> str:
    """사진을 붙인다 (F5).

    **원본은 그대로 저장하고 다시 건드리지 않는다** (`CLAUDE.md` §6-1).
    파일 이름은 내용 해시라, 같은 사진을 두 번 올려도 한 자리에만 쓰인다.
    마킹은 여기 굽지 않는다 — `annotation` 에 좌표 JSON 으로 따로 둔다.
    """
    sha = hashlib.sha256(data).hexdigest()
    suffix = Path(name).suffix.lower() or ".bin"
    path = photo_path(sha, suffix)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    rel = path.relative_to(DATA_DIR).as_posix()  # 데이터 폴더 기준 — docs/03 그대로
    with session() as s:
        row = s.execute(select(m.Photo).where(m.Photo.sha256 == sha)).scalars().first()
        if row is None:
            row = m.Photo(id=_rid(), file_path=rel, sha256=sha, uploaded_by=None,
                          taken_at=datetime.datetime.now())
            s.add(row)
            s.flush()
        if s.get(m.PhotoLink, (row.id, block_id, role)) is None:
            s.add(m.PhotoLink(photo_id=row.id, block_id=block_id, role=role,
                              caption=(caption or "").strip()[:80] or None))
        s.commit()
        return row.id


def photos(block_id: str) -> list[dict[str, str]]:
    with session() as s:
        rows = s.execute(
            select(m.PhotoLink, m.Photo)
            .join(m.Photo, m.Photo.id == m.PhotoLink.photo_id)
            .where(m.PhotoLink.block_id == block_id)
        ).all()
        return [
            {"role": link.role, "caption": link.caption or "",
             "path": str(DATA_DIR / photo.file_path), "sha": photo.sha256[:12]}
            for link, photo in rows
        ]


# ── F23 일괄 정리 ─────────────────────────────────────────────────────────
def bulk_update(
    block_ids: list[str],
    department_id: str | None = None,
    status: str | None = None,
    important: bool | None = None,
) -> int:
    """여러 건의 담당 부서·상태·중요를 한꺼번에 바꾼다 (F23).

    **이관해도 ID 는 그대로다** (`CLAUDE.md` §6-8) — `owner_department_id` 만 바뀐다.
    상태를 바꾸면 주차별 진행에 한 줄이 남는다.
    """
    now = datetime.datetime.now()
    changed = 0
    with session() as s:
        week = ensure_week(s)
        for bid in block_ids:
            b = s.get(m.Block, bid)
            if b is None:
                continue
            touched = []
            if department_id is not None and b.owner_department_id != department_id:
                b.owner_department_id = department_id
                touched.append("담당 부서")
            if status is not None and b.status != status:
                b.status = status
                touched.append("상태")
            if important is not None and bool(b.important) != important:
                b.important = important
                touched.append("중요")
            if not touched:
                continue
            s.add(
                m.BlockHistory(
                    id=_rid(), block_id=bid, week_id=week.id,
                    department_id=b.owner_department_id, status=b.status,
                    note="일괄 정리 — " + "·".join(touched), created_at=now,
                )
            )
            changed += 1
        s.commit()
    return changed
