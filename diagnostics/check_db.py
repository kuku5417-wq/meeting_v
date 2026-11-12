"""DB 점검 — 모델이 선언됐는지, 15표가 적재됐는지 본다.

S1(모델) 전에는 `modules.models` 가 없으므로 "아직 없음"을 한 줄로 알리고
**비정상 종료(1)** 한다. 그 상태를 통과로 세지 않기 위해서다 (ROADMAP P2 참고).

사용법:  python -X utf8 diagnostics/check_db.py
종료 코드 0 = 통과, 1 = 아직 없음 또는 오류.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_data import EXPECTED, SEED_ORDER, TOTAL_ROWS  # noqa: E402


def step_models() -> tuple[object | None, str]:
    try:
        import modules.models as m
    except ModuleNotFoundError as e:
        return None, f"modules.models 아직 없음 ({e.name}) — S1 에서 만든다"
    except Exception as e:  # 선언 자체가 깨진 경우
        return None, f"modules.models import 실패: {type(e).__name__}: {e}"
    return m, ""


def step_engine() -> tuple[object | None, str]:
    try:
        import modules.db as d
    except ModuleNotFoundError as e:
        return None, f"modules.db 아직 없음 ({e.name}) — S2 에서 만든다"
    except Exception as e:
        return None, f"modules.db import 실패: {type(e).__name__}: {e}"
    return d, ""


def main() -> int:
    err: list[str] = []

    m, msg = step_models()
    if m is None:
        print(f"[아직] {msg}")
        return 1

    tables = sorted(m.Base.metadata.tables)
    print(f"선언된 표 {len(tables)}개")

    missing = [t for t in SEED_ORDER if t not in tables]
    if missing:
        err.append(f"[표 없음] {missing}")
    extra = [t for t in tables if t not in EXPECTED]
    if extra:
        print(f"기준정보 밖의 표 {len(extra)}개(운영 표): {extra}")

    # 칸 이름이 CSV 헤더와 같은가 — 하나라도 없으면 시드가 TypeError 로 죽는다
    for name in SEED_ORDER:
        if name not in tables:
            continue
        want = set(EXPECTED[name][0])
        have = {c.name for c in m.Base.metadata.tables[name].columns}
        gap = want - have
        if gap:
            err.append(f"[칸 없음] {name}: CSV 헤더에 있으나 모델에 없음 {sorted(gap)}")

    d, msg = step_engine()
    if d is None:
        print(f"[아직] {msg}")
        if err:
            print(f"\n오류 {len(err)}건")
            for e in err:
                print(" -", e)
        return 1

    # 적재 행 수
    from sqlalchemy import func, select

    total = 0
    with d.session() as s:
        for name in SEED_ORDER:
            table = m.Base.metadata.tables.get(name)
            if table is None:
                continue
            n = s.execute(select(func.count()).select_from(table)).scalar_one()
            total += n
            want = EXPECTED[name][1]
            if n != want:
                err.append(f"[행수] {name} {n}행 (CSV {want}행)")
    print(f"적재 {total}행 (기대 {TOTAL_ROWS}행)")
    if total != TOTAL_ROWS:
        err.append(f"[합계] 적재 {total}행 ≠ 기대 {TOTAL_ROWS}행")

    if err:
        print(f"\n오류 {len(err)}건")
        for e in err:
            print(" -", e)
        return 1
    print("\n[OK] 15표 선언·적재가 CSV와 같다")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
