"""기준정보 15표 — SQLAlchemy 선언.

**칸 이름의 정본은 `data/samples/masters/*.csv` 의 헤더다** (`SPEC.md` §9-A).
헤더에 있는 칸이 하나라도 빠지면 시드가 `TypeError` 로 죽는다.
표 이름·칸 이름·칸 순서를 바꾸지 않는다 — 사내망 전환 때 헤더 값만 매칭한다.

**여기에 없는 것**
- 운영 표(이슈·회의자료·슬라이드)는 S5·S7 에서 만든다 (`ROADMAP.md` 변경 기록)
- 사내 미러 표 `milestone` 은 기준정보가 아니다. S2 또는 S4 에서 넣는다
  (`requirements.md` §1-4). `hull.stage` 는 그 표에서 **계산되는** 파생 값이다

아래 클래스 순서는 **시드 FK 순서**와 같다 (`code-gen.md` §4②).
`system`·`symptom_code`·`cause_code` 는 `parent_id` 자기참조라 부모 행을 먼저 넣어야 한다.
"""
from __future__ import annotations

import datetime

from sqlalchemy import Date, ForeignKey, Integer, String
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
    equipment_model_id: Mapped[str] = mapped_column(ForeignKey("equipment_model.id"))
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
