"""화면 공통 컴포넌트 — 같은 일은 같은 방식으로 (`docs/디자인_규칙.md` §3).

화면마다 목록·거르기를 따로 만들면 모양이 갈린다. 여기 한 번만 만들고 화면은 부르기만 한다.

| 하는 일 | 정한 방식 | 여기서 |
|---|---|---|
| 목록 | 흰 카드 그룹 목록, 선택 행 왼쪽 파란 막대 | `card_list()` · 고르지 않는 카드 한 장은 `card()` |
| 걸러 보기 | 칩 + 찾기 칸 | `filter_pills()` · `search_box()` |
| 여러 건 처리 | 체크한 뒤 일괄 동작 | `check_list()` |

**사람이 적은 글은 모두 `html.escape` 를 거친다.** 제목·설명에 `<` 가 들어와도 카드가 깨지지
않아야 한다. 칩처럼 **우리가 만든 HTML** 만 `chips` 로 따로 받는다.

**주 버튼은 한 화면에 하나다** (규칙 2-5). 여기 컴포넌트는 주 버튼을 쓰지 않는다 —
화면이 제 주 동작에만 `type="primary"` 를 준다.
"""
from __future__ import annotations

import html
from collections.abc import Callable, Sequence
from typing import Any

import pandas as pd
import streamlit as st

CHECK = "고름"  # 일괄 처리 체크 칸 이름


def filter_pills(
    label: str,
    options: Sequence[str],
    key: str,
    counts: dict[str, int] | None = None,
    format_func: Callable[[str], str] | None = None,
) -> str | None:
    """거르기 칩. 아무것도 안 고르면 `None` = 전체.

    건수를 주면 칩 안에 함께 보인다 — 건수 지표를 따로 두지 않아도 된다.
    """

    def _fmt(o: str) -> str:
        text = format_func(o) if format_func else o
        return f"{text} {counts[o]}" if counts and o in counts else text

    return st.pills(label, list(options), format_func=_fmt, key=key, default=None)


def search_box(key: str, placeholder: str = "제목·호선·장비로 찾기") -> str:
    return st.text_input("찾기", key=key, placeholder=placeholder, label_visibility="collapsed").strip()


def card(title: str, meta: str, chips: str = "", on: bool = False) -> None:
    """고르지 않는 카드 한 장. 이력·태그처럼 목록이지만 선택이 없는 곳에 쓴다.

    `title`·`meta` 는 사람이 적은 글이라 이스케이프하고, `chips` 만 HTML 로 그대로 넣는다.
    """
    head = html.escape(title)
    if chips:
        head = f"{head} {chips}"
    st.markdown(
        f'<div class="sd-card{" sd-on" if on else ""}">'
        f'<div class="sd-t">{head}</div>'
        f'<div class="sd-m">{html.escape(meta)}</div></div>',
        unsafe_allow_html=True,
    )


def card_list(
    rows: list[dict[str, Any]],
    id_key: str,
    title: Callable[[dict], str],
    meta: Callable[[dict], str],
    key: str,
    selected: str | None = None,
    empty: str = "보여 줄 것이 없다",
    limit: int = 50,
    chips: Callable[[dict], str] | None = None,
    auto_select: bool = True,
) -> str | None:
    """흰 카드 목록. 고른 카드는 왼쪽에 파란 막대가 선다.

    돌려주는 것: 고른 행의 `id_key` 값.
    `title`·`meta` 는 행을 **글**로 바꾸는 함수다 — 여기서 이스케이프한다.
    칩처럼 우리가 만든 HTML 은 `chips` 로 따로 준다.
    `auto_select=False` 면 아직 아무것도 열지 않은 상태를 그대로 둔다 (`None` 을 돌려준다).
    고른 줄은 `st.session_state[f"{key}__sel"]` 에 있다 — 화면이 밖에서 바꿀 수 있다.
    """
    if not rows:
        st.caption(empty)
        return None

    ids = {str(r[id_key]) for r in rows}
    picked = st.session_state.get(f"{key}__sel") or selected
    if picked not in ids:
        picked = str(rows[0][id_key]) if auto_select else None

    for row in rows[:limit]:
        rid = str(row[id_key])
        left, right = st.columns([9, 2], vertical_alignment="center")
        with left:
            card(title(row), meta(row), chips(row) if chips else "", on=rid == picked)
        # 아이콘만 단독으로 두지 않는다 (디자인_규칙 2-4) — 글자를 함께 쓴다
        if right.button("열기", key=f"{key}__{rid}", icon=":material/chevron_right:"):
            st.session_state[f"{key}__sel"] = rid
            st.rerun()

    if len(rows) > limit:
        st.caption(f"{len(rows)}건 가운데 {limit}건만 보인다. 위에서 걸러 보십시오.")
    return picked


def check_list(
    rows: list[dict[str, Any]],
    columns: Sequence[str],
    key: str,
    id_key: str = "ID",
) -> list[str]:
    """체크한 뒤 일괄 동작 — 체크 칸이 붙은 표. 돌려주는 것은 체크된 `id_key` 목록."""
    if not rows:
        st.caption("고를 것이 없다")
        return []
    frame = pd.DataFrame([{CHECK: False, **{c: r.get(c, "") for c in columns}} for r in rows])
    edited = st.data_editor(
        frame,
        key=key,
        hide_index=True,
        use_container_width=True,
        disabled=list(columns),  # 체크 칸만 고칠 수 있다 — 값은 여기서 바꾸지 않는다
        column_config={CHECK: st.column_config.CheckboxColumn(CHECK, width="small")},
    )
    return [str(r[id_key]) for _, r in edited.iterrows() if r[CHECK]]
