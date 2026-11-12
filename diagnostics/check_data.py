"""기준정보 CSV 점검 — 모델·시드를 쓰기 전에도 돌아간다.

`data/samples/masters/` 의 CSV 15종이 문서와 같은 모양인지 본다.
`_check.py` 는 호선 **값**의 규칙(SPEC.md §7)을 보고, 이쪽은 **표·칸·행 수**를 본다.

사용법:  python -X utf8 diagnostics/check_data.py
         python -X utf8 diagnostics/check_data.py <masters 폴더>
종료 코드 0 = 통과, 1 = 오류 있음.

표준 라이브러리만 쓴다. pandas·sqlalchemy가 없어도 돌아가야 한다 (S0 전에도 쓰는 판정 수단).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

# 시드 순서 = FK 순서. code-gen.md §4② 와 같아야 한다.
SEED_ORDER = [
    "department", "ship_type", "ship_model", "owner", "sister_group", "hull",
    "system", "maker", "equipment_model", "installed_equipment", "component",
    "test_item", "symptom_code", "cause_code", "alias",
]

# 칸 이름의 정본은 CSV 헤더다. 아래는 그것을 고정해 둔 것 —
# CSV가 바뀌면 requirements.md §1-1 과 modules/models.py 도 함께 고친다.
EXPECTED: dict[str, tuple[list[str], int]] = {
    "department":          (["id", "code", "name", "order_no"], 8),
    "ship_type":           (["id", "code", "name"], 5),
    "ship_model":          (["id", "ship_type_id", "code", "name", "capacity", "capacity_unit"], 7),
    "owner":               (["id", "code", "name"], 7),
    "sister_group":        (["id", "name"], 6),
    "hull":                (["id", "ship_type_id", "model_id", "owner_id", "sister_group_id",
                             "series_no", "stage", "delivery_date", "title", "dock",
                             "ship_class", "source"], 13),
    "system":              (["id", "code", "name", "parent_id"], 7),
    "maker":               (["id", "name"], 3),
    "equipment_model":     (["id", "maker_id", "name", "model_no"], 3),
    "installed_equipment": (["id", "hull_id", "equipment_model_id", "system_id", "name",
                             "unit_no", "position"], 7),
    "component":           (["id", "equipment_model_id", "name"], 6),
    "test_item":           (["id", "code", "name", "system_id"], 3),
    "symptom_code":        (["id", "code", "name", "parent_id"], 4),
    "cause_code":          (["id", "code", "name", "parent_id"], 6),
    "alias":               (["text", "target_kind", "target_id", "scope_hull_id", "source"], 14),
}

TOTAL_ROWS = 99  # 진행 호선 11척 + 인도선 2척 기준 (2026-11-12, SPEC §6)
SELF_PARENT = ("system", "symptom_code", "cause_code")  # parent_id 자기참조
# 빈 값이 허용되고, 적재 전에 None 으로 바꿔야 하는 칸 (code-gen.md §4⑥)
NULLABLE = {"hull": ["series_no", "delivery_date"]}


def default_base() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "samples" / "masters"


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
    return header, rows


def check(base: Path) -> list[str]:
    err: list[str] = []

    # 0) 시드 순서 목록이 기대 표 15종과 같은가
    if sorted(SEED_ORDER) != sorted(EXPECTED):
        err.append(f"[순서] SEED_ORDER({len(SEED_ORDER)}종)가 기대 표 {len(EXPECTED)}종과 다름")
    if len(SEED_ORDER) != len(set(SEED_ORDER)):
        err.append("[순서] SEED_ORDER 에 중복된 이름이 있음")

    total = 0
    for name in SEED_ORDER:
        want_header, want_rows = EXPECTED[name]
        path = base / f"{name}.csv"

        # 1) 파일이 있는가
        if not path.exists():
            err.append(f"[없음] {name}.csv 가 {base} 에 없음")
            continue

        header, rows = read(path)
        total += len(rows)

        # 2) 헤더가 문서와 같은가 (순서까지)
        if header != want_header:
            err.append(f"[헤더] {name}.csv\n      실제: {header}\n      기대: {want_header}")

        # 3) 행 수가 같은가
        if len(rows) != want_rows:
            err.append(f"[행수] {name}.csv {len(rows)}행 (기대 {want_rows}행)")

        # 4) id 중복
        key = "text" if name == "alias" else "id"
        if key in header:
            ids = [r[key] for r in rows]
            dup = {i for i in ids if ids.count(i) > 1}
            if dup:
                err.append(f"[중복] {name}.csv {key} 중복: {sorted(dup)}")

        # 5) 자기참조 부모가 자기 앞에 있는가 (시드가 FK 순서로 적재된다)
        if name in SELF_PARENT and "parent_id" in header:
            seen: set[str] = set()
            for r in rows:
                if r["parent_id"] and r["parent_id"] not in seen:
                    err.append(f"[부모] {name}.csv {r['id']} 의 parent_id {r['parent_id']} 가 자기보다 뒤에 있음")
                seen.add(r["id"])

    # 6) hull 은 12칸이고 model_id·series_no 가 있어야 한다 (code-gen.md §4①)
    hull_header = EXPECTED["hull"][0]
    if len(hull_header) != 12:
        err.append(f"[hull] 기대 칸이 12개가 아님: {len(hull_header)}개")
    for col in ("model_id", "series_no"):
        if col not in hull_header:
            err.append(f"[hull] {col} 가 없음 — 시드가 TypeError 로 죽는다")

    # 7) 합계
    if total != TOTAL_ROWS:
        err.append(f"[합계] 전체 {total}행 (기대 {TOTAL_ROWS}행)")

    print(f"기준정보 {len(EXPECTED)}표 / {total}행  (기대 {len(EXPECTED)}표 / {TOTAL_ROWS}행)")
    print("시드 순서:", " → ".join(SEED_ORDER))

    # 참고용 — 적재 전에 None 으로 바꿔야 하는 빈 칸 수
    for name, cols in NULLABLE.items():
        path = base / f"{name}.csv"
        if not path.exists():
            continue
        _, rows = read(path)
        counts = {c: sum(1 for r in rows if not r.get(c)) for c in cols}
        empties = {c: n for c, n in counts.items() if n}
        if empties:
            print(f"빈 칸(적재 전 None 으로): {name} {empties}")

    return err


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else default_base()
    if not base.is_dir():
        print(f"masters 폴더가 없음: {base}", file=sys.stderr)
        return 1
    problems = check(base)
    if problems:
        print(f"\n오류 {len(problems)}건")
        for p in problems:
            print(" -", p)
        return 1
    print("\n[OK] 표·칸·행 수가 문서와 같다")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
