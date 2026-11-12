"""설정 — 기준정보 15종 CRUD·재시드 (S4 / **F18**).

표를 `st.data_editor` 로 고친다. `st_aggrid` 는 사외망에서 설치가 막힐 수 있어
쓰지 않는다 — `code-gen.md` §4⑦ 의 강등 경로다. Enterprise 기능(rowGroup·pivot)은
애초에 범위 밖이고, 여기서 필요한 것은 인라인 편집·행 추가·행 삭제뿐이다.

**값의 정본은 CSV 다** (`SPEC.md` §9-A). 여기서 고치면 **DB 만 바뀌고
`data/samples/masters/*.csv` 는 그대로다.** 재시드하면 편집한 내용이 CSV 값으로 덮인다.
실데이터 전환은 CSV 교체로 한다 — 화면 편집은 그 전까지의 임시 수단이다.

칸 이름·표 이름은 바꿀 수 없다. 사내망에서 헤더 값만 매칭하기 때문이다.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import select

from modules import seed
from modules.db import session

TABLES: dict[str, type] = dict(seed.SEED_ORDER)  # 순서 = FK 순서

# 사람이 고치면 안 되는 칸. `hull.stage` 는 호선 이벤트 일정에서 **계산되는 값**이라
# 손으로 적으면 일정과 어긋난다 (`SPEC.md` §3-3·§10-2).
READ_ONLY: dict[str, list[str]] = {"hull": ["stage"]}


def _pk(cls: type) -> tuple[str, ...]:
    return tuple(c.name for c in cls.__table__.primary_key.columns)


def _cols(cls: type) -> list[str]:
    return [c.name for c in cls.__table__.columns]


def _read(cls: type) -> pd.DataFrame:
    """표 하나를 전부 읽어 **문자열** DataFrame 으로. CSV 와 같은 모양으로 다룬다."""
    cols = _cols(cls)
    with session() as s:
        rows = s.execute(select(cls)).scalars().all()
        data = [{c: ("" if getattr(r, c) is None else str(getattr(r, c))) for c in cols} for r in rows]
    return pd.DataFrame(data, columns=cols, dtype="string").fillna("")


def _key(row: dict[str, Any], pk: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(c, "") or "").strip() for c in pk)


def _restore(name: str, cls: type, rows: list[dict[str, Any]]) -> None:
    """지운 줄을 되돌린다 (디자인_규칙 §3 "삭제·취소: 바로 실행 + 되돌리기")."""
    with session() as s:
        for row in rows:
            s.add(cls(**seed.to_values(name, cls, row)))
        s.commit()


def _save(
    name: str, cls: type, before: pd.DataFrame, after: pd.DataFrame
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """편집 결과를 DB 에 반영한다. 기본키로 더하기·고치기·지우기를 가른다.

    돌려주는 것: 건수와 **지운 줄들**. 지운 줄은 되돌리기에 쓰므로 그대로 넘긴다.
    """
    pk = _pk(cls)
    cols = _cols(cls)
    before_rows = {_key(r, pk): r for r in before.to_dict("records")}
    after_rows: dict[tuple[str, ...], dict[str, Any]] = {}
    for r in after.to_dict("records"):
        clean = {c: ("" if pd.isna(r.get(c)) else str(r.get(c, "")).strip()) for c in cols}
        key = _key(clean, pk)
        if all(k == "" for k in key):
            continue  # 기본키가 비어 있는 줄은 아직 쓰는 중이다
        after_rows[key] = clean

    added = changed = 0
    gone: list[dict[str, Any]] = []
    with session() as s:
        for key in before_rows.keys() - after_rows.keys():
            obj = s.get(cls, key if len(key) > 1 else key[0])
            if obj is not None:
                s.delete(obj)
                gone.append(before_rows[key])
        for key, row in after_rows.items():
            values = seed.to_values(name, cls, row)
            if key in before_rows:
                if before_rows[key] == row:
                    continue
                obj = s.get(cls, key if len(key) > 1 else key[0])
                for c, v in values.items():
                    setattr(obj, c, v)
                changed += 1
            else:
                s.add(cls(**values))
                added += 1
        s.commit()
    return {"added": added, "changed": changed, "removed": len(gone)}, gone


def render() -> None:
    st.header("설정 — 기준정보")
    st.caption(
        "값의 정본은 `data/samples/masters/*.csv` 다. 여기서 고치면 **DB 만** 바뀌고 CSV 는 그대로이며, "
        "재시드하면 편집한 내용이 CSV 값으로 덮인다."
    )

    counts = seed.counts()
    # 15종은 칩으로 늘어놓기에 많다. 여기 선택은 **거르기가 아니라 자리 옮기기**라
    # 디자인_규칙 §3 의 "걸러 보기: 칩 + 찾기 칸" 토큰을 쓰지 않는다.
    name = st.selectbox(
        "표",
        list(TABLES),
        format_func=lambda n: f"{n}  ({counts.get(n, 0)}행)",
        key="settings_table",
    )
    cls = TABLES[name]

    st.caption("기본키: " + " + ".join(f"`{c}`" for c in _pk(cls)))

    locked = READ_ONLY.get(name, [])
    if locked:
        st.caption(
            "잠긴 칸: " + " · ".join(f"`{c}`" for c in locked)
            + " — 호선 이벤트 일정에서 계산되는 값이라 손으로 고치지 않는다 (`SPEC.md` §3-3)."
        )

    # 되돌리기를 하면 표 위젯이 기억하는 「지운 줄」을 비워야 한다 — 그대로 두면 되살린 줄을
    # 다음 그림에서 또 지운다. 위젯 key 에 판 번호를 붙여 새 위젯으로 만든다.
    ver = int(st.session_state.get(f"ver_{name}", 0))
    before = _read(cls)
    after = st.data_editor(
        before,
        num_rows="dynamic",
        use_container_width=True,
        disabled=locked,
        key=f"editor_{name}_{ver}",
    )

    # 자동 저장 — 저장 버튼을 두지 않는다 (디자인_규칙 §3 "저장").
    # 고치면 Streamlit 이 다시 돌고, 그때 바뀐 줄만 쓴다. 같으면 아무것도 쓰지 않는다.
    done, gone = _save(name, cls, before, after)
    if any(done.values()):
        st.toast(
            f"{name}: 추가 {done['added']} · 수정 {done['changed']} · 삭제 {done['removed']}",
            icon=":material/check:",
        )
    if gone:
        st.session_state[f"undo_{name}"] = gone
    elif any(done.values()):
        st.session_state.pop(f"undo_{name}", None)  # 다음 편집으로 넘어갔으면 되돌리기를 접는다

    # 삭제는 확인을 묻지 않고 바로 하고 되돌리기를 준다 (디자인_규칙 §3 "삭제·취소", 2-6).
    undo = st.session_state.get(f"undo_{name}")
    if undo:
        col1, col2 = st.columns([4, 1], vertical_alignment="center")
        col1.warning(f"{name} 에서 {len(undo)}행을 지웠다.", icon=":material/delete:")
        if col2.button("되돌리기", key=f"undo_{name}_btn", icon=":material/undo:"):
            _restore(name, cls, undo)
            st.session_state.pop(f"undo_{name}", None)
            st.session_state[f"ver_{name}"] = ver + 1
            st.toast(f"{len(undo)}행 되돌렸다", icon=":material/check:")
            st.rerun()

    st.divider()
    st.subheader("재시드")
    st.caption(
        f"CSV 15종을 FK 순서로 다시 적재한다. **지금 DB 에 있는 {sum(counts.values())}행이 지워지고** "
        "CSV 값으로 바뀐다. 화면에서 고친 내용은 사라진다."
    )
    ok = st.checkbox("편집한 내용이 사라져도 괜찮다", key="reseed_ok")
    if st.button("CSV 로 재시드", disabled=not ok, key="reseed",
                 help="위 칸을 켜야 누를 수 있다 — 지금 DB 의 값이 지워진다"):
        loaded = seed.seed_masters(force=True)
        # CSV 값으로 전부 덮었으니 아까 지운 줄의 되돌리기는 뜻이 없다
        for n in TABLES:
            st.session_state.pop(f"undo_{n}", None)
            st.session_state[f"ver_{n}"] = int(st.session_state.get(f"ver_{n}", 0)) + 1
        st.toast(f"재시드 완료 — {sum(loaded.values())}행 / {len(loaded)}표", icon=":material/check:")
        st.rerun()
