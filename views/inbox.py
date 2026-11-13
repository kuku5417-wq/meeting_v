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

            # 「발생일」 — **일이 난 날**이지 적은 날이 아니다. 그 날의 호선 단계를 잡는 데 쓴다.
            # 날짜 고르기는 캘린더 한 칸이다 (디자인_규칙 §3). 메모에서 읽었으면 미리 차 있고,
            # 못 읽었으면 **비워 둔다** — 근거 없는 값은 채우지 않는다 (CLAUDE.md §6-3).
            col1, col2 = st.columns([1, 2], vertical_alignment="center")
            day = col1.date_input(
                "발생일", value=c.get("occurred_on"), key=f"cdt_{memo_id}_{i}", format="YYYY-MM-DD",
                help="일이 난 날이다. 메모에 없으면 비워 둔다 — 적은 날로 대신하지 않는다",
            )
            read = (c.get("_date_text") or "").strip()
            if read:
                col2.caption(f"메모에서 읽음 — 「{read[:40]}」")

            if c.get("quote"):
                st.markdown(theme.evidence(f"근거: {c['quote']}"), unsafe_allow_html=True)

            # 이 화면의 주 버튼은 「기록하고 다음」 하나다 (규칙 2-5).
            # 후보마다 반복되는 이것은 보조 버튼이고, 아이콘은 원장의 「등록」과 같은 `add` 다
            # — `arrow_forward` 는 「다음 일로 넘어가기」에만 쓴다 (규칙 2-4 "같은 뜻에 같은 아이콘").
            done_key = f"done_{memo_id}_{i}"
            if st.session_state.get(done_key):
                st.caption(f"{st.session_state[done_key]} 로 등록했다 — 이슈 원장에서 볼 수 있다")
            elif st.button(
                "이슈로 등록", key=f"cr_{memo_id}_{i}", icon=":material/add:",
                disabled=not title.strip(), help="제목을 적으면 누를 수 있다",
            ):
                bid = extract.register(
                    memo_id,
                    {**c, "title": title, "block_type": btype, "hull": hull,
                     "equipment": equip, "body": body, "occurred_on": day,
                     # 아래 칸들은 사람이 고친 값이다. **기계가 낸 원값**을 함께 넘겨야
                     # (AI 값, 사람 값)이 둘 다 남는다 (CLAUDE.md §6-2).
                     "_ai": {f: c.get(f, "") for f in extract.AI_FIELDS}
                            | {"occurred_on": c.get("occurred_on")},
                     # 사람이 날짜를 고쳤으면 메모 구간은 더 이상 그 값의 근거가 아니다
                     "_date_span": c.get("_date_span") if day == c.get("occurred_on") else None,
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
        # 아래 「최근 메모」목록이 **먼저 고른 줄**을 기억하므로, 거기도 새 메모로 옮긴다.
        # 옮기지 않으면 목록이 옛 메모를 돌려주어 방금 적은 메모가 화면에서 밀린다.
        st.session_state["memo_list__sel"] = mid
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
            if st.button("AI 로 정리", icon=":material/auto_awesome:"):
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
            # 날짜만은 메모에서 찾아 미리 채운다 — 사람이 다시 치지 않게. 틀리면 고치면 된다.
            blank: dict = {"title": "", "hull": "", "equipment": "", "body": ""}
            found = extract.date_for(text, None)
            if found is not None:
                day, where = found
                blank |= {"occurred_on": day, "_date_span": where, "_date_text": text[where[0]:where[1]]}
            _candidate_rows(memo_id, [blank], by_ai=False, depts=depts)

    st.divider()
    st.markdown("**최근 메모**")
    # 목록은 카드 그룹이다 (디자인_규칙 §3). 고르면 그 메모로 바로 넘어간다 —
    # 표·고르기·버튼 셋으로 나누지 않는다.
    # 아직 아무 메모도 열지 않았으면 **저절로 열지 않는다** (`auto_select=False`).
    rows = extract.memos()
    pick = ui.card_list(
        rows, "id",
        title=lambda r: str(r["글"] or "(빈 메모)"),
        meta=lambda r: " · ".join(str(x) for x in (r["적은 때"], r["판"]) if x),
        key="memo_list",
        selected=memo_id,
        auto_select=False,
        empty="아직 저장한 메모가 없다",
    )
    if pick and pick != memo_id:
        st.session_state["last_memo"] = pick
        st.session_state.pop("cands", None)
        st.session_state.pop("dropped", None)
        st.rerun()
