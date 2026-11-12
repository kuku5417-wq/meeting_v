"""이슈 원장 (S5) — F2 그리드 · F3 지식 매핑 · F4 주간 업데이트.

`st_aggrid` 를 쓰지 않는다. 사외망에서 설치가 막힐 수 있어 `st.dataframe` 으로 간다
(`code-gen.md` §4⑦). Enterprise 기능(rowGroup·pivot)은 애초에 범위 밖이다.

**담당은 부서까지만이다.** 담당자가 아니어도 누구나 고칠 수 있고, 고친 사실은 이력에 남는다 (F2).
**역할 전환은 표시용 분기**라 여기서 권한을 막지 않는다 (`CLAUDE.md` §9).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from modules import issues
from modules import models as m
from modules.db import session
from sqlalchemy import select


def _departments() -> dict[str, str]:
    with session() as s:
        rows = s.execute(select(m.Department).order_by(m.Department.order_no)).scalars().all()
        return {r.id: r.name for r in rows}


def _new_issue_form(depts: dict[str, str]) -> None:
    with st.form("new_issue", clear_on_submit=True):
        st.markdown("**이슈 등록**")
        title = st.text_input("제목", placeholder="No.2 발전기 배기온도 편차")
        col1, col2, col3 = st.columns(3)
        block_type = col1.selectbox("유형", issues.BLOCK_TYPES, index=0)
        dept = col2.selectbox("담당 부서", ["(없음)", *depts], format_func=lambda d: depts.get(d, d))
        hull = col3.text_input("호선", placeholder="2511 · SN2511")
        equip = st.text_input("장비 (현장 표기 그대로)", placeholder="DG2 · D/G #2 · 2번 발전기")
        body = st.text_area("현상", placeholder="무엇이 어떻게 되고 있는가")
        if st.form_submit_button("등록", type="primary"):
            if not title.strip():
                st.error("제목은 있어야 한다")
                return
            bid = issues.create_block(
                title=title,
                block_type=block_type,
                owner_department_id=None if dept == "(없음)" else dept,
                body=body,
                hull_text=hull,
                equipment_text=equip,
            )
            st.success(f"{bid} 등록")
            st.rerun()


def _detail(block_id: str) -> None:
    st.markdown(f"### {block_id}")

    tab_hist, tab_tag = st.tabs(["주차별 진행 (F4)", "지식 매핑 (F3)"])

    with tab_hist:
        note = st.text_input("이번 주 한 줄", key=f"note_{block_id}")
        col1, col2 = st.columns([1, 2])
        new_status = col1.selectbox("상태", ["(그대로)", *issues.STATUSES], key=f"st_{block_id}")
        if col2.button("진행 추가", key=f"add_{block_id}", type="primary"):
            if not note.strip():
                st.error("한 줄은 있어야 한다")
            else:
                issues.add_history(block_id, note, None if new_status == "(그대로)" else new_status)
                st.rerun()
        rows = issues.history(block_id)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("아직 적은 진행이 없다")

    with tab_tag:
        rows = issues.tags(block_id)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            if any(r["상태"] == "미등록" for r in rows):
                st.caption(
                    "「미등록」은 기준정보에 없는 표기다. 설정 화면에서 기준정보에 더하거나, "
                    "별칭으로 이어 주면 다음부터 자동으로 걸린다."
                )
        else:
            st.caption("아직 태그가 없다")

        col1, col2 = st.columns([1, 2])
        kind = col1.selectbox("갈래", issues.MAPPING_KINDS, key=f"kind_{block_id}")
        raw = col2.text_input("현장 표기", key=f"raw_{block_id}")
        if st.button("태그 더하기", key=f"tag_{block_id}"):
            if not raw.strip():
                st.error("표기는 있어야 한다")
            else:
                ok = issues.add_tag(block_id, kind, raw)
                st.success("기준정보에 걸렸다" if ok else "기준정보에 없다 — 「미등록」으로 남는다")
                st.rerun()


def render() -> None:
    st.header("이슈 원장")

    counts = issues.counts()
    cols = st.columns(len(issues.STATUSES) + 1)
    cols[0].metric("전체", sum(counts.values()))
    for col, status in zip(cols[1:], issues.STATUSES):
        col.metric(status, counts.get(status, 0))

    depts = _departments()
    col1, col2 = st.columns(2)
    f_status = col1.selectbox("상태", ["(전체)", *issues.STATUSES], key="f_status")
    f_dept = col2.selectbox(
        "부서", ["(전체)", *depts], format_func=lambda d: depts.get(d, d), key="f_dept"
    )

    rows = issues.ledger(
        status=None if f_status == "(전체)" else f_status,
        department_id=None if f_dept == "(전체)" else f_dept,
    )

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("조건에 맞는 이슈가 없다. 아래에서 등록할 수 있다.", icon="📭")

    st.divider()
    _new_issue_form(depts)

    if rows:
        st.divider()
        picked = st.selectbox(
            "자세히 볼 이슈",
            [r["ID"] for r in rows],
            format_func=lambda i: f"{i} — {next(r['제목'] for r in rows if r['ID'] == i)}",
            key="pick_block",
        )
        _detail(picked)
