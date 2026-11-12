"""기록함 (S6) — 메모를 붙여넣고 이슈 후보로 정리한다 (F1).

**원본은 바꾸지 않는다.** 메모는 넣은 그대로 저장되고, 고치면 새 판이 된다.
**근거 없는 AI 값은 표시하지 않는다** — 근거 구간을 메모에서 찾지 못한 후보는
등록 목록에 올라오지 않고, 왜 버렸는지 화면에 적는다.

사내 LLM 설정이 없으면(사외망에서는 정상) AI 정리 대신 **직접 적기**로 간다.
창구는 `modules/llm_client.py` 에 있으므로 사내망에서 설정만 채우면 그대로 돈다.
"""
from __future__ import annotations

import streamlit as st

from modules import extract, issues
from modules.llm_client import LLMNotConfigured, is_configured
from views import theme, ui


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

            # 이 화면의 주 버튼은 「저장」 하나다 (규칙 2-5). 후보마다 반복되는 이것은 보조 버튼.
            done_key = f"done_{memo_id}_{i}"
            if st.session_state.get(done_key):
                st.caption(f"{st.session_state[done_key]} 로 등록했다 — 이슈 원장에서 볼 수 있다")
            elif st.button(
                "이슈로 등록", key=f"cr_{memo_id}_{i}", icon=":material/arrow_forward:",
                disabled=not title.strip(), help="제목을 적으면 누를 수 있다",
            ):
                bid = extract.register(
                    memo_id,
                    {**c, "title": title, "block_type": btype, "hull": hull,
                     "equipment": equip, "body": body,
                     "department_id": None if dept == "(없음)" else dept},
                    by_ai=by_ai,
                )
                # 한 번 더 눌러 같은 후보가 두 번 들어가지 않게 자리를 바꾼다
                st.session_state[done_key] = bid
                st.toast(f"{bid} 등록", icon=":material/check:")
                st.rerun()


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
    # 「다음 일로 넘어가기」 토큰 (디자인_규칙 §3) — 적으면 다음 칸(후보 확인)으로 간다.
    # 이 화면의 유일한 주 버튼이다.
    if col1.button("기록하고 다음", type="primary", icon=":material/arrow_forward:",
                   disabled=not raw.strip(), help="메모를 붙여넣으면 누를 수 있다"):
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
    # 목록은 카드 그룹이다 (디자인_규칙 §3). 고르면 그 메모로 바로 넘어간다 —
    # 표·고르기·버튼 셋으로 나누지 않는다.
    rows = extract.memos()
    pick = ui.card_list(
        rows, "id",
        title=lambda r: r["글"] or "(빈 메모)",
        meta=lambda r: " · ".join(x for x in (r["적은 때"], r["판"]) if x),
        key="memo_list",
        selected=memo_id,
        empty="아직 저장한 메모가 없다",
    )
    if pick and pick != memo_id:
        st.session_state["last_memo"] = pick
        st.session_state.pop("cands", None)
        st.session_state.pop("dropped", None)
        st.rerun()
