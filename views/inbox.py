"""기록함 (S6) — 메모를 붙여넣고 이슈 후보로 정리한다 (F1).

**원본은 바꾸지 않는다.** 메모는 넣은 그대로 저장되고, 고치면 새 판이 된다.
**근거 없는 AI 값은 표시하지 않는다** — 근거 구간을 메모에서 찾지 못한 후보는
등록 목록에 올라오지 않고, 왜 버렸는지 화면에 적는다.

사내 LLM 설정이 없으면(사외망에서는 정상) AI 정리 대신 **직접 적기**로 간다.
창구는 `modules/llm_client.py` 에 있으므로 사내망에서 설정만 채우면 그대로 돈다.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from modules import extract, issues
from modules.llm_client import LLMNotConfigured, is_configured
from views import theme


def _departments() -> dict[str, str]:
    from sqlalchemy import select

    from modules import models as m
    from modules.db import session

    with session() as s:
        rows = s.execute(select(m.Department).order_by(m.Department.order_no)).scalars().all()
        return {r.id: r.name for r in rows}


def _candidate_rows(memo_id: str, cands: list[dict], by_ai: bool, depts: dict[str, str]) -> None:
    st.markdown(f"**이슈 후보 {len(cands)}건** — 확인하고 등록한다")
    for i, c in enumerate(cands):
        with st.container(border=True):
            col1, col2 = st.columns([3, 2])
            title = col1.text_input("제목", value=c.get("title", ""), key=f"ct_{memo_id}_{i}")
            dept = col2.selectbox(
                "담당 부서", ["(없음)", *depts],
                format_func=lambda d: depts.get(d, d), key=f"cd_{memo_id}_{i}",
            )
            col1, col2, col3 = st.columns(3)
            btype = col1.selectbox("유형", issues.BLOCK_TYPES, key=f"cb_{memo_id}_{i}")
            hull = col2.text_input("호선", value=c.get("hull", ""), key=f"ch_{memo_id}_{i}")
            equip = col3.text_input("장비", value=c.get("equipment", ""), key=f"ce_{memo_id}_{i}")
            body = st.text_area("현상", value=c.get("body", ""), key=f"cy_{memo_id}_{i}")

            if c.get("quote"):
                st.markdown(theme.evidence(f"근거: {c['quote']}"), unsafe_allow_html=True)

            if st.button("이슈로 등록", key=f"cr_{memo_id}_{i}", type="primary"):
                bid = extract.register(
                    memo_id,
                    {**c, "title": title, "block_type": btype, "hull": hull,
                     "equipment": equip, "body": body,
                     "department_id": None if dept == "(없음)" else dept},
                    by_ai=by_ai,
                )
                st.success(f"{bid} 등록 — 이슈 원장에서 볼 수 있다")


def render() -> None:
    st.header("기록함")
    st.caption(
        "메모·회의록을 붙여넣으면 이슈 후보로 정리한다. **원본은 그대로 저장되고 바뀌지 않는다.**"
    )

    depts = _departments()

    raw = st.text_area(
        "메모 붙여넣기",
        height=160,
        key="memo_raw",
        placeholder="11/12 SN2511 안벽\nDG2 배기온도 편차 40도 발생. 열전대 접촉 불량으로 추정.",
    )

    col1, col2 = st.columns([1, 3])
    if col1.button("저장", type="primary", disabled=not raw.strip(),
                   help="메모를 붙여넣으면 누를 수 있다"):
        mid = extract.save_memo(raw)
        st.session_state["last_memo"] = mid
        st.success(f"메모 저장 — {mid[:8]}")

    if not is_configured():
        col2.info("사내 LLM 설정이 없어 **직접 적기**로 간다. 사외망에서는 정상이다.", icon=":material/edit_note:")

    memo_id = st.session_state.get("last_memo")
    if memo_id:
        st.divider()
        text = extract.memo_text(memo_id)
        st.markdown(f"**메모 {memo_id[:8]}**")
        st.code(text, language=None)

        if is_configured():
            if st.button("AI 로 정리"):
                try:
                    with st.spinner("사내 LLM 이 메모를 정리하는 중"):
                        kept, dropped = extract.extract(text)
                except LLMNotConfigured as e:
                    st.error(str(e))
                    kept, dropped = [], []
                st.session_state["cands"] = kept
                st.session_state["dropped"] = dropped

            dropped = st.session_state.get("dropped") or []
            if dropped:
                st.warning(
                    "**근거를 찾지 못해 버린 후보** — 메모에 없는 말은 싣지 않는다.\n\n"
                    + "\n".join(f"- {d}" for d in dropped),
                    icon=":material/block:",
                )
            cands = st.session_state.get("cands") or []
            if cands:
                _candidate_rows(memo_id, cands, by_ai=True, depts=depts)
        else:
            st.markdown("**직접 적기**")
            st.caption("메모에서 읽은 대로 적는다. 사람이 적은 값이므로 근거 구간을 따로 두지 않는다.")
            _candidate_rows(memo_id, [{"title": "", "hull": "", "equipment": "", "body": ""}],
                            by_ai=False, depts=depts)

    st.divider()
    st.markdown("**최근 메모**")
    rows = extract.memos()
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        pick = st.selectbox(
            "열어 볼 메모", [r["id"] for r in rows],
            format_func=lambda i: f"{i[:8]} — {next(r['글'] for r in rows if r['id'] == i)[:40]}",
            key="memo_pick",
        )
        if st.button("이 메모로 작업"):
            st.session_state["last_memo"] = pick
            st.session_state.pop("cands", None)
            st.session_state.pop("dropped", None)
            st.rerun()
    else:
        st.caption("아직 저장한 메모가 없다")
