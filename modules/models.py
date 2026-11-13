"""기준정보 15표 — SQLAlchemy 선언.

**칸 이름의 정본은 `data/samples/masters/*.csv` 의 헤더다** (`SPEC.md` §9-A).
헤더에 있는 칸이 하나라도 빠지면 시드가 `TypeError` 로 죽는다.
표 이름·칸 이름·칸 순서를 바꾸지 않는다 — 사내망 전환 때 헤더 값만 매칭한다.

**여기에 없는 것**
- 지식 표(`case_card`·`block_link`)는 S9 에서 만든다
- 사내 미러 표 `milestone` 은 기준정보가 아니다. S2 또는 S4 에서 넣는다
  (`requirements.md` §1-4). `hull.stage` 는 그 표에서 **계산되는** 파생 값이다

아래 **운영 표**(S5 이슈 원장 · S7 회의자료)는 `requirements.md` §1-2-2 를 따른다.
표 이름·칸 이름은 원본 `docs/03_데이터모델.md` 그대로다.

아래 클래스 순서는 **시드 FK 순서**와 같다 (`code-gen.md` §4②).
`system`·`symptom_code`·`cause_code` 는 `parent_id` 자기참조라 부모 행을 먼저 넣어야 한다.
"""
from __future__ import annotations

import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ── 1. department ─────────────────────────────────────────────────────────
class Department(Base):
    __tablename__ = "department"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    order_no: Mapped[int | None] = mapped_column(Integer)


# ── 2. ship_type ──────────────────────────────────────────────────────────
class ShipType(Base):
    __tablename__ = "ship_type"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))


# ── 3. ship_model ─────────────────────────────────────────────────────────
class ShipModel(Base):
    """모델타입. 원본 `app/models/masters.py` 에 없던 표다 (`SPEC.md` §4)."""

    __tablename__ = "ship_model"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ship_type_id: Mapped[str] = mapped_column(ForeignKey("ship_type.id"))
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    # 적재량을 숫자와 단위로 쪼갠다 — "180K 이상만" 조회가 문자열 비교가 되지 않게
    capacity: Mapped[int | None] = mapped_column(Integer)
    capacity_unit: Mapped[str | None] = mapped_column(String(16))


# ── 4. owner ──────────────────────────────────────────────────────────────
class Owner(Base):
    __tablename__ = "owner"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))


# ── 5. sister_group ───────────────────────────────────────────────────────
class SisterGroup(Base):
    __tablename__ = "sister_group"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))


# ── 6. hull ───────────────────────────────────────────────────────────────
class Hull(Base):
    """호선. **12칸이다** (`code-gen.md` §4①).

    `ship_type_id` 를 `model_id` 와 함께 남기는 이유는 `SPEC.md` §3-2 에 있다 —
    모델이 비어 있는 호선도 선종으로 묶을 수 있어야 한다. 둘이 어긋나면 §7-2 가 잡는다.
    """

    __tablename__ = "hull"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # SN2511
    ship_type_id: Mapped[str] = mapped_column(ForeignKey("ship_type.id"))
    model_id: Mapped[str | None] = mapped_column(ForeignKey("ship_model.id"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("owner.id"))
    sister_group_id: Mapped[str | None] = mapped_column(ForeignKey("sister_group.id"))
    series_no: Mapped[int | None] = mapped_column(Integer)  # 단독선은 빈 칸
    # 안벽기간·시운전기간·앵카링기간·Layup·인도선 (`SPEC.md` §3-3).
    # 사람이 고르지 않는다 — milestone 일정에서 계산한다 (§10-2).
    stage: Mapped[str] = mapped_column(String(16))
    delivery_date: Mapped[datetime.date | None] = mapped_column(Date)
    # 아래 넷은 pjtlist 동기화로 들어온다 (`SPEC.md` §3-2)
    title: Mapped[str | None] = mapped_column(String(128))
    dock: Mapped[str | None] = mapped_column(String(32))
    ship_class: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(32))


# ── 7. system ─────────────────────────────────────────────────────────────
class System(Base):
    __tablename__ = "system"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("system.id"))


# ── 8. maker ──────────────────────────────────────────────────────────────
class Maker(Base):
    __tablename__ = "maker"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))


# ── 9. equipment_model ────────────────────────────────────────────────────
class EquipmentModel(Base):
    __tablename__ = "equipment_model"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    maker_id: Mapped[str] = mapped_column(ForeignKey("maker.id"))
    name: Mapped[str] = mapped_column(String(64))
    model_no: Mapped[str | None] = mapped_column(String(64))


# ── 10. installed_equipment ───────────────────────────────────────────────
class InstalledEquipment(Base):
    """탑재 장비. 이슈는 **장비 모델이 아니라 여기에** 붙는다 (`CLAUDE.md` §6-6)."""

    __tablename__ = "installed_equipment"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # EQ-SN2511-GE-02
    hull_id: Mapped[str] = mapped_column(ForeignKey("hull.id"))
    equipment_model_id: Mapped[str] = mapped_column(ForeignKey("equipment_model.id"))
    system_id: Mapped[str] = mapped_column(ForeignKey("system.id"))
    name: Mapped[str] = mapped_column(String(64))
    unit_no: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[str | None] = mapped_column(String(64))


# ── 11. component ─────────────────────────────────────────────────────────
class Component(Base):
    __tablename__ = "component"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    # 공란 허용 — `requirements.md` §1-1 #11. 어느 장비 모델에도 매이지 않는 부위가 있다.
    equipment_model_id: Mapped[str | None] = mapped_column(ForeignKey("equipment_model.id"))
    name: Mapped[str] = mapped_column(String(64))


# ── 12. test_item ─────────────────────────────────────────────────────────
class TestItem(Base):
    __tablename__ = "test_item"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    system_id: Mapped[str | None] = mapped_column(ForeignKey("system.id"))


# ── 13. symptom_code ──────────────────────────────────────────────────────
class SymptomCode(Base):
    __tablename__ = "symptom_code"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("symptom_code.id"))


# ── 14. cause_code ────────────────────────────────────────────────────────
class CauseCode(Base):
    __tablename__ = "cause_code"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("cause_code.id"))


# ── 15. alias ─────────────────────────────────────────────────────────────
class Alias(Base):
    """별칭 사전. 현장 표기를 기준정보 ID로 바꾼다 (F3).

    **`id` 칸이 없다** — CSV 헤더가 5칸뿐이다 (`SPEC.md` §3-1 주). 그래서 PK 를
    `(text, target_kind, target_id)` 복합으로 둔다. 같은 표기("DG2")가 호선마다
    다른 장비를 가리킬 수 있어야 하므로 `text` 하나만으로는 부족하다.

    `target_id` 는 `installed_equipment`·`component`·`symptom_code` 중 어디든
    가리키므로 FK 를 걸지 않는다 — 어느 표인지는 `target_kind` 가 말한다.
    """

    __tablename__ = "alias"

    text: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scope_hull_id: Mapped[str | None] = mapped_column(ForeignKey("hull.id"))
    source: Mapped[str | None] = mapped_column(String(32))


# ══════════════════════════════════════════════════════════════════════════
# 운영 표 — S5 이슈 원장 (`requirements.md` §1-2-2)
# ══════════════════════════════════════════════════════════════════════════


class Person(Base):
    """사람. 역할 전환은 **표시용 분기**다 — 로그인·인증을 만들지 않는다 (`CLAUDE.md` §9)."""

    __tablename__ = "person"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    department_id: Mapped[str | None] = mapped_column(ForeignKey("department.id"))


class Week(Base):
    __tablename__ = "week"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)  # ISO 주차 2026-W42
    start_date: Mapped[datetime.date] = mapped_column(Date)
    end_date: Mapped[datetime.date] = mapped_column(Date)


class Section(Base):
    """주차 × 부서 1행.

    **「확정」 개념은 M12 에서 없앴다** — `status` 는 옛 기록으로만 남고 아무것도 잠그지 않는다.
    """

    __tablename__ = "section"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("week.id"))
    department_id: Mapped[str] = mapped_column(ForeignKey("department.id"))
    status: Mapped[str | None] = mapped_column(String(16))
    confirmed_by: Mapped[str | None] = mapped_column(String(32))
    confirmed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)


class Memo(Base):
    """원본 메모. **수정 금지** (`CLAUDE.md` §6-1).

    원문을 고칠 때는 새 행을 만들고 `revises_id` 로 앞 판을 가리킨다. 옛 판은 남는다.
    """

    __tablename__ = "memo"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("section.id"))
    author_id: Mapped[str | None] = mapped_column(ForeignKey("person.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    revises_id: Mapped[str | None] = mapped_column(ForeignKey("memo.id"))


class Block(Base):
    """이슈·문제점·공유정보·대시보드 블록 — **이슈 원장의 중심**.

    이관해도 `id` 는 그대로고 `owner_department_id` 만 바뀐다 (`CLAUDE.md` §6-8).
    `due_event` 의 날짜는 저장하지 않는다 — 볼 때마다 `milestone` 에서 잡는다 (`SPEC.md` §10-2).
    """

    __tablename__ = "block"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # ISS-2026-0142
    block_type: Mapped[str] = mapped_column(String(16))  # share / problem / issue / dashboard
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)  # 「현상」
    status: Mapped[str] = mapped_column(String(16))  # 신규 / 진행 / 종결요청 / 종결
    owner_department_id: Mapped[str | None] = mapped_column(ForeignKey("department.id"))
    created_week_id: Mapped[str | None] = mapped_column(ForeignKey("week.id"))
    valid_until: Mapped[datetime.date | None] = mapped_column(Date)
    # **사건이 난 날.** 적은 날이 아니라 일이 난 날이다 — 그 날의 호선 단계를 잡는 데 쓴다
    # (`milestone.stage(hull, on=occurred_on)`). 메모에 날짜가 적혀 있으면 자동으로 찬다.
    # 2026-11-13 에 칸을 더하기로 결정 (`requirements.md` §2-C, `CLAUDE.md` §2 "칸 추가는 먼저 묻는다").
    occurred_on: Mapped[datetime.date | None] = mapped_column(Date)
    origin: Mapped[str | None] = mapped_column(String(16))  # memo / meeting / manual
    created_by: Mapped[str | None] = mapped_column(ForeignKey("person.id"))
    # 1차 초안 「상세 한 장」 (F5)
    draft_state: Mapped[str | None] = mapped_column(String(8))  # none / wip / ok
    cause_text: Mapped[str | None] = mapped_column(Text)
    action_text: Mapped[str | None] = mapped_column(Text)
    decision_needed: Mapped[str | None] = mapped_column(Text)
    important: Mapped[bool | None] = mapped_column(Boolean)
    # 일정 경보 (F21) — 날짜는 milestone 에서 잡는다
    # 어휘는 `modules/issues.py` 의 `DUE_EVENTS` 하나다 — "" / STTO / GASTO / ACTO / DL / DATE.
    # `milestone` 의 이벤트 이름을 그대로 쓴다 (`requirements.md` §1-2-2).
    due_event: Mapped[str | None] = mapped_column(String(16))
    due_date: Mapped[datetime.date | None] = mapped_column(Date)
    alert_days: Mapped[int | None] = mapped_column(Integer)
    alert_off_reason: Mapped[str | None] = mapped_column(Text)
    alert_off_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    alert_off_date: Mapped[datetime.date | None] = mapped_column(Date)


class SectionBlock(Base):
    __tablename__ = "section_block"

    section_id: Mapped[str] = mapped_column(ForeignKey("section.id"), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"), primary_key=True)
    order_no: Mapped[int | None] = mapped_column(Integer)
    carried_over: Mapped[bool | None] = mapped_column(Boolean)


class BlockHistory(Base):
    """주차별 진행 한 줄 (F4)."""

    __tablename__ = "block_history"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"))
    week_id: Mapped[str] = mapped_column(ForeignKey("week.id"))
    department_id: Mapped[str | None] = mapped_column(ForeignKey("department.id"))
    status: Mapped[str | None] = mapped_column(String(16))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)


class SourceSpan(Base):
    """근거 구간. 근거 없는 AI 값은 표시하지 않는다 (`CLAUDE.md` §6-3)."""

    __tablename__ = "source_span"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"))
    field: Mapped[str] = mapped_column(String(32))
    memo_id: Mapped[str] = mapped_column(ForeignKey("memo.id"))
    start: Mapped[int | None] = mapped_column(Integer)
    end: Mapped[int | None] = mapped_column(Integer)
    quote: Mapped[str | None] = mapped_column(Text)


class AiFieldLog(Base):
    """AI 값과 사람 값을 둘 다 남긴다 (`CLAUDE.md` §6-2)."""

    __tablename__ = "ai_field_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"))
    field: Mapped[str] = mapped_column(String(32))
    ai_value: Mapped[str | None] = mapped_column(Text)
    human_value: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)


class Closure(Base):
    """종결 요청·승인 (F13). 조치 내용이 필수다 (`CLAUDE.md` §6-7)."""

    __tablename__ = "closure"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"))
    action_text: Mapped[str] = mapped_column(Text)
    requested_by: Mapped[str | None] = mapped_column(ForeignKey("person.id"))
    requested_week_id: Mapped[str | None] = mapped_column(ForeignKey("week.id"))
    # 저장되는 값은 **「승인」·「보류」 둘뿐**이다 (`meetings.DECISIONS`).
    # 「대기」는 저장 값이 아니라 **결정이 아직 없을 때(`None`) 화면에 보이는 말**이고,
    # `meetings.closure_pending()` 의 「결정」 칸이 그 말을 넣는다 (칩 색은 `views/theme.py`).
    decision: Mapped[str | None] = mapped_column(String(8))  # 승인 / 보류
    decided_week_id: Mapped[str | None] = mapped_column(ForeignKey("week.id"))
    decided_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)


class BlockTag(Base):
    """블록 ↔ 기준정보 연결 (F3).

    `target_id` 가 비고 `raw_text` 만 있으면 **미연결**이다. 사람이 고르면 채우고 `alias` 에 더한다.
    `target_id` 는 여러 표를 가리키므로 FK 를 걸지 않는다 — 어느 표인지는 `kind` 가 말한다.
    """

    __tablename__ = "block_tag"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"))
    kind: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64))
    raw_text: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float | None] = mapped_column(Float)
    confirmed: Mapped[bool | None] = mapped_column(Boolean)
    confirmed_by: Mapped[str | None] = mapped_column(ForeignKey("person.id"))
    dismissed: Mapped[bool | None] = mapped_column(Boolean)


class BlockTable(Base):
    """이슈에 붙인 표. 최대 20행 × 8열."""

    __tablename__ = "block_table"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"))
    title: Mapped[str | None] = mapped_column(String(128))
    rows_json: Mapped[str | None] = mapped_column(Text)
    order_no: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)


class Photo(Base):
    """사진 **원본은 바꾸지 않는다** (`CLAUDE.md` §6-1). 자리는 `config.paths.photo_path`."""

    __tablename__ = "photo"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    file_path: Mapped[str] = mapped_column(String(256))
    sha256: Mapped[str] = mapped_column(String(64))
    width: Mapped[int | None] = mapped_column(Integer)  # EXIF 회전 적용 크기
    height: Mapped[int | None] = mapped_column(Integer)
    taken_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey("person.id"))


class PhotoLink(Base):
    __tablename__ = "photo_link"

    photo_id: Mapped[str] = mapped_column(ForeignKey("photo.id"), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(8), primary_key=True)  # main / before / after
    order_no: Mapped[int | None] = mapped_column(Integer)
    caption: Mapped[str | None] = mapped_column(String(80))
    note: Mapped[str | None] = mapped_column(String(500))


class Annotation(Base):
    """마킹. **사진 위에 굽지 않고 좌표 JSON 으로 따로 둔다** (`CLAUDE.md` §6-1).

    좌표는 EXIF 회전 적용 원본 픽셀 기준이다. `drawable_canvas` 가 없어 좌표를 손으로
    넣는 강등 경로에서도 여기 들어오는 모양은 같다 (`code-gen.md` §4⑦).
    """

    __tablename__ = "annotation"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    photo_id: Mapped[str] = mapped_column(ForeignKey("photo.id"))
    block_id: Mapped[str | None] = mapped_column(ForeignKey("block.id"))
    shapes_json: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)


class Marker(Base):
    """번호 마커 → 부위 태그 → 사진 검색."""

    __tablename__ = "marker"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    annotation_id: Mapped[str] = mapped_column(ForeignKey("annotation.id"))
    no: Mapped[int | None] = mapped_column(Integer)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(String(64))
    component_id: Mapped[str | None] = mapped_column(ForeignKey("component.id"))


# ══════════════════════════════════════════════════════════════════════════
# 운영 표 — S7 회의자료 (`requirements.md` §1-2-2 「회의」)
#
# **표현은 `report_item`, 사실은 `block` 이다.** 회의자료에서 현상·원인·조치·결정 필요를
# 고치면 `block` 을 고치는 것이고, 회의용 한 줄·형태·순서·머리표는 `report_item` 에만 있다.
# 이 경계가 F8(사실 되먹임)의 전제다.
#
# **`deck_slide`·`slide_object` 는 선언하지 않는다** (2026-11-13 결정 D,
# `requirements.md` §1-2-3). 회의자료의 한 장은 `report_item` 하나다.
# ══════════════════════════════════════════════════════════════════════════


class Meeting(Base):
    """회의 한 건. 부서 자료는 「제출」, 나머지는 「발행」이다.

    정기 회의(부서 자료 8건 + 공유회 + 팀장 정보회의)는 주차마다 저절로 생긴다 —
    `modules/meetings.py` 의 `ensure_regular()`.
    """

    __tablename__ = "meeting"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # MTG-2026-W46-dept-D2
    week_id: Mapped[str] = mapped_column(ForeignKey("week.id"))
    # `held_on` 이 회의 날짜고, `held_at` 은 진행을 시작한 시각이다 (진행 화면이 적는다)
    held_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    chair_id: Mapped[str | None] = mapped_column(ForeignKey("person.id"))
    kind: Mapped[str] = mapped_column(String(8))  # dept / share / exec / hull / review
    title: Mapped[str] = mapped_column(String(200))
    owner_dept_id: Mapped[str | None] = mapped_column(ForeignKey("department.id"))
    held_on: Mapped[datetime.date | None] = mapped_column(Date)
    # 어휘는 **원본 `docs/03` 것을 그대로 쓴다** — 사내망 실데이터와 값을 맞추기 위해서다
    # (2026-11-13 결정). 1차에서 코드가 넣는 값은 「구성 중」·「제출」 둘이고, 「수정됨」·
    # 「발행」은 S8(발행·PPTX) 몫, 「종료」는 회의가 끝난 뒤라 어휘에만 둔다.
    status: Mapped[str] = mapped_column(String(8))  # 구성 중 / 제출 / 수정됨 / 발행 / 종료
    # 저장 값은 **영문 코드**다 (원본 `docs/03`). 화면에 보이는 말 「이어받기」·「빈 자료」는
    # `modules/meetings.py` 의 `START_MODE_LABELS` 한 군데에서만 갈린다.
    start_mode: Mapped[str | None] = mapped_column(String(16))  # carry / blank
    version: Mapped[int] = mapped_column(Integer)  # 0 = 아직 판이 없다
    hull_id: Mapped[str | None] = mapped_column(ForeignKey("hull.id"))  # 호선별 회의
    # 원본 `docs/03` 의 칸 — **공유회 부서 순서**(부서 ID 목록 JSON)다. 장 순서가 아니다
    # (장 순서의 정본은 `report_item.order_no` 하나다). **1차에서는 쓰지 않는다** —
    # 1차 공유회는 제출판을 취합한 순서대로 본다.
    order_json: Mapped[str | None] = mapped_column(Text)


class MeetingVersion(Base):
    """판 고정. **회의에서 본 그대로 남는다** — 뒤에 사실이 바뀌어도 이 글은 안 바뀐다."""

    __tablename__ = "meeting_version"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meeting.id"))
    version: Mapped[int] = mapped_column(Integer)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    snapshot_json: Mapped[str | None] = mapped_column(Text)


class ReportItem(Base):
    """**회의자료의 한 장.**

    `kind` 는 `single`(이슈 한 건) · `summary`(여러 이슈를 한 장으로, F7) ·
    `metric`(지표 요약) · `table`(기간 표). **`table` 은 2차다** —
    기간 표(`metric_table`)가 1차에 없다 (`requirements.md` §1-2-3).

    **`src` 는 「참조한 제출판 장의 `id`」다** (2026-11-13 결정). F10 취합에서 공유회가
    부서 **최신 제출판**의 장을 실을 때 글을 베끼지 않고 그 판에 적힌 장 `id` 를 가리킨다 —
    표현(한 줄·형태·머리표)은 판 그대로 굳고, 사실(현상·원인·조치)만 `block` 에서 지금
    값을 읽는다. 읽는 곳은 `modules/meetings.py` 의 `_src_ref()` 하나다.

    원본 `docs/03` 은 같은 칸을 **출처 구분**으로 적어 두었다 — 공유회가 직접 가진 장이
    「종결 요청 자동 채택」인지 「원장 채움」인지. **그 기능은 2차다.** 2차에 오면 출처
    구분을 둘 자리를 새로 정해야 한다 — 한 칸에 두 뜻(참조한 장 `id` · 출처 이름)을
    섞어 담지 않는다.
    """

    __tablename__ = "report_item"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meeting.id"))
    kind: Mapped[str] = mapped_column(String(8))  # single / summary / metric / table
    block_id: Mapped[str | None] = mapped_column(ForeignKey("block.id"))
    line: Mapped[str | None] = mapped_column(Text)  # 회의용 한 줄
    tag_on: Mapped[bool | None] = mapped_column(Boolean)  # 머리표를 보이나
    form: Mapped[str | None] = mapped_column(String(8))  # detail / card / photo / line
    order_no: Mapped[int | None] = mapped_column(Integer)
    # **FK 를 걸지 않는다.** 가리키는 것은 살아 있는 행이 아니라 **제출판에 굳은 장의
    # `ID`** 다 — 부서가 그 장을 빼면 `report_item` 행은 지워지지만 판에서는 빠지지
    # 않고, 공유회는 그 판의 글을 계속 보인다 (`meetings._src_ref`). FK 를 걸면 그
    # 빼기가 막힌다 (FOREIGN KEY constraint failed). 선례는 `table_id` 와
    # `Alias.target_id` 다 — 칸 이름은 그대로 두고 이을 곳만 코드가 안다.
    src: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    dept_id: Mapped[str | None] = mapped_column(ForeignKey("department.id"))
    # 원본 `docs/03` 의 「기간 표」 칸이다 — 가리키는 것은 **기간 표(`metric_table`)** 고,
    # 이슈에 붙인 표(`block_table`)가 아니다. 그 표는 **2차**라 1차에 없으므로
    # (`requirements.md` §1-2-3) 칸 이름만 그대로 두고 FK 는 걸지 않는다.
    # 2차에 `metric_table` 이 오면 그때 FK 를 건다.
    table_id: Mapped[str | None] = mapped_column(String(32))


class ReportItemBlock(Base):
    """요약 장이 잇는 이슈들 (F7). **요약해도 이슈는 그대로 남는다.**"""

    __tablename__ = "report_item_block"

    item_id: Mapped[str] = mapped_column(ForeignKey("report_item.id"), primary_key=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("block.id"), primary_key=True)
    order_no: Mapped[int | None] = mapped_column(Integer)


class MeetingComment(Base):
    """회의 진행 기록 (F12).

    `kind="decision"` 이면 **그 이슈의 `decision_needed` 를 비운다** — 정해진 것을
    「결정 필요」로 남겨 두면 다음 주에 같은 안건이 또 올라온다.
    """

    __tablename__ = "meeting_comment"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meeting.id"))
    block_id: Mapped[str | None] = mapped_column(ForeignKey("block.id"))
    text: Mapped[str] = mapped_column(Text)
    author_id: Mapped[str | None] = mapped_column(ForeignKey("person.id"))
    kind: Mapped[str] = mapped_column(String(8))  # comment / decision
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)


class Directive(Base):
    """지시사항 (F20) — 내용·담당 부서·기한(주차).

    **낸 주차부터** 그 부서 회의자료 **맨 위**에 나오고, **한 줄 보고로 완료**된다
    (2026-11-13 결정 — 그 주 안에 공유회가 열리면 그 주 자료에 바로 올라와야 한다).
    """

    __tablename__ = "directive"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meeting.id"))
    block_id: Mapped[str | None] = mapped_column(ForeignKey("block.id"))
    dept_id: Mapped[str] = mapped_column(ForeignKey("department.id"))
    text: Mapped[str] = mapped_column(Text)
    due_week_id: Mapped[str | None] = mapped_column(ForeignKey("week.id"))
    # 어휘는 **원본 `docs/03` 것을 그대로 쓴다** — 사내망 실데이터와 값을 맞추기 위해서다
    # (2026-11-13 결정). `requirements.md` §1-2-2·결정 I 도 「열림 + 이번 주 완료」로 적는다
    status: Mapped[str] = mapped_column(String(8))  # 열림 / 완료
    done_note: Mapped[str | None] = mapped_column(Text)
    done_week_id: Mapped[str | None] = mapped_column(ForeignKey("week.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
