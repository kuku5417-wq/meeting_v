"""호선 기준정보 CSV 점검 — 적재(seed_masters) 전에 돌린다.

SPEC.md §7 의 7개 규칙을 확인한다. 끊긴 연결을 DB 에 만들지 않는 것이 목적.
사용법:  python3 _check.py            (이 폴더에서)
         python3 _check.py <폴더>     (다른 폴더의 CSV 를 볼 때)
종료 코드 0 = 통과, 1 = 오류 있음.
"""
from __future__ import annotations

import collections
import csv
import datetime
import re
import sys
from pathlib import Path

STAGES = ("설계", "건조", "시운전 1단계", "시운전 2단계", "인도")


def read(base: Path, name: str) -> list[dict[str, str]]:
    with (base / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def check(base: Path, today: datetime.date) -> list[str]:
    ship_type = {r["id"] for r in read(base, "ship_type")}
    model = {r["id"]: r for r in read(base, "ship_model")}
    owner = {r["id"] for r in read(base, "owner")}
    series = {r["id"] for r in read(base, "sister_group")}
    hulls = read(base, "hull")
    err: list[str] = []

    for h in hulls:
        hid = h["id"]
        # 1) 호선번호 형식
        if not re.fullmatch(r"SN\d{4}", hid):
            err.append(f"[1] {hid} 호선번호가 SN+4자리가 아님")
        # 참조 해소
        if h["ship_type_id"] not in ship_type:
            err.append(f"[FK] {hid} 선종 {h['ship_type_id']} 없음")
        if h["model_id"] and h["model_id"] not in model:
            err.append(f"[FK] {hid} 모델 {h['model_id']} 없음")
        if h["owner_id"] not in owner:
            err.append(f"[FK] {hid} 선주 {h['owner_id']} 없음")
        if h["sister_group_id"] and h["sister_group_id"] not in series:
            err.append(f"[FK] {hid} 시리즈 {h['sister_group_id']} 없음")
        # 2) 호선의 선종 = 그 모델의 선종
        m = model.get(h["model_id"])
        if m and m["ship_type_id"] != h["ship_type_id"]:
            err.append(f"[2] {hid} 선종({h['ship_type_id']}) ≠ 모델의 선종({m['ship_type_id']})")
        # 3) 순번만 있고 묶음이 없음
        if h["series_no"] and not h["sister_group_id"]:
            err.append(f"[3] {hid} series_no 가 있으나 sister_group_id 가 비었음")
        # 6) 단계 어휘
        if h["stage"] not in STAGES:
            err.append(f"[6] {hid} 단계 '{h['stage']}' 는 어휘 5개 밖")
        # 7) 단계 ↔ 인도일
        d = datetime.date.fromisoformat(h["delivery_date"])
        if h["stage"] == "인도" and d > today:
            err.append(f"[7] {hid} 인도 상태인데 인도일({d})이 미래")
        if h["stage"] != "인도" and d <= today:
            err.append(f"[7] {hid} 미인도 상태인데 인도일({d})이 과거")

    # 4) 묶음별 순번 1부터 연속 / 5) 묶음 안은 같은 모델·선주
    group: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for h in hulls:
        if h["sister_group_id"]:
            group[h["sister_group_id"]].append(h)
    for gid, rows in sorted(group.items()):
        nums = sorted(int(h["series_no"]) for h in rows if h["series_no"])
        if nums != list(range(1, len(rows) + 1)):
            err.append(f"[4] {gid} 순번이 1부터 연속이 아님: {nums}")
        if len({h["model_id"] for h in rows}) > 1:
            err.append(f"[5] {gid} 묶음 안에 모델이 섞임")
        if len({h["owner_id"] for h in rows}) > 1:
            err.append(f"[5] {gid} 묶음 안에 선주가 섞임")

    print(f"호선 {len(hulls)}건 (시리즈 {len(group)}묶음 "
          f"{sum(len(v) for v in group.values())}척 + 단독선 "
          f"{len(hulls) - sum(len(v) for v in group.values())}척)")
    print("단계 분포:", dict(collections.Counter(h["stage"] for h in hulls)))
    return err


if __name__ == "__main__":
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    problems = check(base, datetime.date.today())
    if problems:
        print(f"\n오류 {len(problems)}건")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("\n규칙 7개 전부 통과")
