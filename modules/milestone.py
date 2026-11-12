"""호선 일정 — 단계 계산(§9-4)과 일정 경보(F21).

**전환 지점이다.** 사내망에서는 `data_manager` 의 `milestone.parquet`·`pjtlist.parquet` 을
그대로 읽고, 사외망에서는 같은 헤더의 샘플 CSV(`data/samples/mirror/`)를 읽는다.
바꿀 곳은 `_read()` 하나뿐이다 (`requirements.md` §1-4, `SPEC.md` §10).

규칙은 `SPEC.md` §10-2 그대로다.

| 단계 | 경계 |
|---|---|
| `시운전기간` | `STFROM`~`STTO`, `GASFROM`~`GASTO` |
| `앵카링기간` | `ACFROM`~`ACTO`, `COLDFROM`~`COLDTO` |
| `Layup` | `pjtlist.WORKFINISH` ~ `DL` |
| `안벽기간` | 나머지 |
| `인도선` | `DL` 이 지났다 |

날짜는 `PERF`(실적) → `PROS`(전망) → `PLAN`(계획) 순으로 처음 값이 있는 것을 쓴다.
구간이 겹치면 **시작일이 가장 늦은 것**이 이긴다.
"""
from __future__ import annotations

import csv
import datetime
from pathlib import Path

from config.paths import MIRROR_DIR
from modules.sn_util import ensure_sn

SERIES = ("PERF", "PROS", "PLAN")  # 실적 → 전망 → 계획

# 단계 → (시작 이벤트, 끝 이벤트) 쌍들. 앞에서부터 보고 하나라도 들면 그 단계다.
SPANS: dict[str, tuple[tuple[str, str], ...]] = {
    "시운전기간": (("STFROM", "STTO"), ("GASFROM", "GASTO")),
    "앵카링기간": (("ACFROM", "ACTO"), ("COLDFROM", "COLDTO")),
}
DELIVERED = "인도선"
DEFAULT = "안벽기간"
LAYUP = "Layup"


def _read(name: str) -> list[dict[str, str]]:
    """★ 사내망 전환 지점 — 여기만 parquet 읽기로 바꾼다."""
    path = Path(MIRROR_DIR) / f"{name}.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def _date(value: str) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def event_date(row: dict[str, str], evt: str) -> datetime.date | None:
    """한 이벤트의 날짜. 실적 → 전망 → 계획 순으로 처음 값이 있는 것."""
    for s in SERIES:
        d = _date(row.get(f"{s}{evt}", ""))
        if d is not None:
            return d
    return None


def events(hull_id: str) -> dict[str, datetime.date]:
    """그 호선의 이벤트 날짜 전부. 칸 이름에서 이벤트를 읽어 낸다 (`SELECT *` 이라 늘 수 있다)."""
    sn = ensure_sn(hull_id)
    for row in _read("milestone"):
        if ensure_sn(row.get("project", "")) != sn:
            continue
        names = {c[4:] for c in row if c[:4] in SERIES}
        return {e: d for e in sorted(names) if (d := event_date(row, e)) is not None}
    return {}


def work_finish(hull_id: str) -> datetime.date | None:
    """`pjtlist.WORKFINISH` — 공사 완료일. Layup 의 시작이다 (진수가 아니다)."""
    sn = ensure_sn(hull_id)
    for row in _read("pjtlist"):
        if ensure_sn(row.get("SHIPNUM", "")) == sn:
            return _date(row.get("WORKFINISH", ""))
    return None


def stage(hull_id: str, on: datetime.date | None = None) -> tuple[str, datetime.date | None]:
    """그 호선의 단계와 그 구간의 시작일. 일정이 없으면 `("", None)`."""
    on = on or datetime.date.today()
    evt = events(hull_id)
    if not evt:
        return "", None

    dl = evt.get("DL")
    if dl is not None and dl <= on:
        return DELIVERED, dl

    hits: list[tuple[datetime.date, str]] = []
    for name, pairs in SPANS.items():
        for a, b in pairs:
            start, end = evt.get(a), evt.get(b)
            if start and end and start <= on <= end:
                hits.append((start, name))
    wf = work_finish(hull_id)
    if wf and dl and wf <= on <= dl:
        hits.append((wf, LAYUP))

    if not hits:
        return DEFAULT, None
    # 겹치면 시작일이 가장 늦은 것이 이긴다 (§10-2 ③)
    start, name = max(hits, key=lambda x: x[0])
    return name, start


def due(event_or_date: str, hull_id: str, on: datetime.date | None = None) -> datetime.date | None:
    """이슈의 「~전 해결」 목표 날짜 (F21).

    `DATE` 면 호출하는 쪽이 `block.due_date` 를 쓴다. 그 밖에는 이벤트 이름이다.
    """
    if not event_or_date or event_or_date == "DATE":
        return None
    return events(hull_id).get(event_or_date)


def alert(target: datetime.date | None, alert_days: int, on: datetime.date | None = None) -> tuple[str, int | None]:
    """경보 상태와 D-n. 지나면 「기한 지남」은 해제와 관계없이 표시한다 (F21)."""
    if target is None:
        return "", None
    on = on or datetime.date.today()
    left = (target - on).days
    if left < 0:
        return "기한 지남", left
    if left <= alert_days:
        return "일정 임박", left
    return "", left
