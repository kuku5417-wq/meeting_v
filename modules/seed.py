"""기준정보 CSV → DB 적재.

**순서가 곧 FK 순서다** (`code-gen.md` §4②). `SEED_ORDER` 를 바꾸면 적재가 깨진다.
`system`·`symptom_code`·`cause_code` 는 `parent_id` 자기참조라 부모 행이 파일 안에서
먼저 나와야 한다 — `diagnostics/check_data.py` 가 그 순서를 미리 검사한다.

**1회 가드는 `st.session_state` 로 판정하지 않는다** (`code-gen.md` §4④).
탭을 새로 열면 세션이 새로 생겨 다시 적재한다. **DB 안에 행이 있는지**로 판정한다.

CSV 는 `utf-8-sig` 로 읽는다 — 엑셀이 BOM 을 붙여서, 안 하면 첫 칸 이름이 깨진다.
빈 날짜·빈 정수는 `None` 으로 바꿔 꽂는다 — `""` 를 그대로 `Date`·`Integer` 칸에 넣으면 터진다.
"""
from __future__ import annotations

import csv
import datetime
from pathlib import Path

from sqlalchemy import Date, Integer, func, select
from sqlalchemy.orm import Session

from config.paths import MASTERS_DIR
from modules import models as m
from modules.db import session
from modules.sn_util import ensure_sn

# 적재 순서 = FK 순서. diagnostics/check_data.py 의 SEED_ORDER 와 같아야 한다.
SEED_ORDER: list[tuple[str, type]] = [
    ("department", m.Department),
    ("ship_type", m.ShipType),
    ("ship_model", m.ShipModel),
    ("owner", m.Owner),
    ("sister_group", m.SisterGroup),
    ("hull", m.Hull),
    ("system", m.System),
    ("maker", m.Maker),
    ("equipment_model", m.EquipmentModel),
    ("installed_equipment", m.InstalledEquipment),
    ("component", m.Component),
    ("test_item", m.TestItem),
    ("symptom_code", m.SymptomCode),
    ("cause_code", m.CauseCode),
    ("alias", m.Alias),
]

# 호선번호가 들어가는 칸 — ensure_sn 을 거쳐야 별칭 사전(F3)이 어긋나지 않는다.
HULL_REF: set[tuple[str, str]] = {
    ("hull", "id"),
    ("installed_equipment", "hull_id"),
    ("alias", "scope_hull_id"),
}

# 적재 여부를 판정하는 표. 호선이 없으면 아무것도 적재되지 않은 것으로 본다.
SENTINEL = m.Hull


def _rows(name: str, base: Path) -> list[dict[str, str]]:
    with (base / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def to_values(name: str, cls: type, row: dict[str, str]) -> dict[str, object]:
    """CSV 한 줄 → 모델 생성자 인수. 빈 값은 None, 정수·날짜는 형을 맞춘다.

    설정 화면(S4)의 저장도 같은 규칙을 거친다 — 변환이 두 군데로 갈리지 않게.
    """
    values: dict[str, object] = {}
    for col in cls.__table__.columns:
        raw = row.get(col.name, "")
        if (name, col.name) in HULL_REF:
            raw = ensure_sn(raw)
        if raw == "":
            values[col.name] = None
        elif isinstance(col.type, Integer):
            values[col.name] = int(raw)
        elif isinstance(col.type, Date):
            values[col.name] = datetime.date.fromisoformat(raw)
        else:
            values[col.name] = raw
    return values


def is_seeded(s: Session) -> bool:
    """DB 안에 호선이 있는가. 세션 상태가 아니라 이것으로 판정한다."""
    return s.execute(select(func.count()).select_from(SENTINEL.__table__)).scalar_one() > 0


def seed_masters(force: bool = False, base: Path | None = None) -> dict[str, int]:
    """기준정보 15표를 FK 순서로 적재한다.

    이미 적재돼 있으면 아무것도 하지 않고 빈 사전을 돌려준다.
    `force=True` 면 전부 지우고 다시 넣는다 (설정 화면의 재시드, S4).
    """
    base = base or MASTERS_DIR
    loaded: dict[str, int] = {}
    with session() as s:
        if is_seeded(s) and not force:
            return loaded
        if force:
            for name, cls in reversed(SEED_ORDER):  # FK 역순으로 지운다
                s.execute(cls.__table__.delete())
        for name, cls in SEED_ORDER:
            rows = _rows(name, base)
            s.add_all([cls(**to_values(name, cls, r)) for r in rows])
            s.flush()  # 다음 표의 FK 가 이 표를 볼 수 있게
            loaded[name] = len(rows)
        s.commit()
    return loaded


def counts() -> dict[str, int]:
    """표별 적재 행 수. 진단·설정 화면에서 쓴다."""
    out: dict[str, int] = {}
    with session() as s:
        for name, cls in SEED_ORDER:
            out[name] = s.execute(select(func.count()).select_from(cls.__table__)).scalar_one()
    return out


if __name__ == "__main__":
    import sys

    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    done = seed_masters(force="--force" in sys.argv)
    if done:
        print(f"적재 {sum(done.values())}행 / {len(done)}표")
        for name, n in done.items():
            print(f"  {name:<22} {n}")
    else:
        print("이미 적재돼 있어 건너뜀 (--force 로 다시 넣는다)")
        for name, n in counts().items():
            print(f"  {name:<22} {n}")
