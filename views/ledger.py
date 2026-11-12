"""이슈 원장 (S5) — F2 그리드 · F3 지식 매핑 · F4 주간 업데이트 · F5 1차 초안 ·
F21 일정 경보 · F23 일괄 정리 (`requirements.md` §1-3-2).

`st_aggrid` 를 쓰지 않는다. 사외망에서 설치가 막힐 수 있어 `st.dataframe` 으로 간다
(`code-gen.md` §4⑦). Enterprise 기능(rowGroup·pivot)은 애초에 범위 밖이다.

**담당은 부서까지만이다.** 담당자가 아니어도 누구나 고칠 수 있고, 고친 사실은 이력에 남는다 (F2).
**역할 전환은 표시용 분기**라 여기서 권한을 막지 않는다 (`CLAUDE.md` §9).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from sqlalchemy import select

from modules import issues
from modules import models as m
from modules.db import session
from views import theme


def _departments() -> dict[str, str]:
    with session() as s:
        rows = s.execute(select(m.Department).order_by(m.Department.order_no)).scalars().all()
        return {r.id: r.name for r in rows}


def _bulk(rows: list[dict[str, object]], depts: dict[str, str]) -> None:
    """F23 — 여러 건을 골라 담당 부서·상태·중요를 한꺼번에 바꾼다."""
    with st.expander("일괄 정리 (F23)"):
        st.caption("이관해도 ID 는 그대로다. 바뀐 것은 주차별 진행에 한 줄로 남는다.")
        picked = st.multiselect(
            "고른 이슈",
            [r["ID"] for r in rows],
            format_func=lambda i: f"{i} — {next(r['제목'] for r in rows if r['ID'] == i)}",
            key="bulk_pick",
        )
        col1, col2, col3 = st.columns(3)
        dept = col1.selectbox(
            "담당 부서", ["(그대로)", *depts], format_func=lambda d: depts.get(d, d), key="bulk_dept"
        )
        status = col2.selectbox(
            "상태", ["(그대로)", *issues.ASSIGNABLE_STATUSES], key="bulk_status",
            help="「종결」은 부서가 하지 않는다 — 공유회 진행 화면이나 기획 주관자가 승인한다",
        )
        important = col3.selectbox("중요", ["(그대로)", "중요", "보통"], key="bulk_important")

        if st.button("한꺼번에 바꾸기", disabled=not picked, key="bulk_go", type="primary",
                     help="바꿀 이슈를 먼저 고른다"):
            n = issues.bulk_update(
                picked,
                department_id=None if dept == "(그대로)" else dept,
                status=None if status == "(그대로)" else status,
                important=None if important == "(그대로)" else (important == "중요"),
            )
            st.toast(f"{n}건 바꿨다" if n else "바뀐 것이 없다", icon=":material/check:")
            st.rerun()


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


def _draft_tab(block_id: str) -> None:
    """F5 — 1차 초안 「상세 한 장」 + 사진."""
    d = issues.draft(block_id)
    st.caption(f"초안 상태: **{ {'none': '시작 전', 'wip': '작성 중', 'ok': '완료'}[d['draft_state']] }**")

    values = {}
    values["body"] = st.text_area("현상", value=d["body"], key=f"body_{block_id}")
    col1, col2 = st.columns(2)
    values["cause_text"] = col1.text_area("원인", value=d["cause_text"], key=f"cause_{block_id}")
    values["action_text"] = col2.text_area("조치", value=d["action_text"], key=f"act_{block_id}")
    values["decision_needed"] = st.text_input(
        "결정 필요", value=d["decision_needed"], key=f"dec_{block_id}",
        placeholder="회의에서 정해 주어야 하는 것",
    )

    col1, col2 = st.columns([1, 1])
    if col1.button("저장", key=f"dsave_{block_id}"):
        issues.save_draft(block_id, values, done=False)
        st.rerun()
    if col2.button("초안 완료", key=f"ddone_{block_id}", type="primary"):
        issues.save_draft(block_id, values, done=True)
        st.rerun()

    st.divider()
    st.markdown("**사진**")
    st.caption("원본은 그대로 저장하고 다시 건드리지 않는다. 마킹은 사진 위에 굽지 않고 좌표로 따로 둔다.")

    shots = issues.photos(block_id)
    if shots:
        cols = st.columns(min(3, len(shots)))
        for col, p in zip(cols * ((len(shots) // 3) + 1), shots):
            path = Path(p["path"])
            if path.exists():
                try:
                    col.image(str(path), caption=f"{p['role']} · {p['caption']}", use_container_width=True)
                except Exception:
                    col.caption(f"{p['role']} · {p['caption']} ({p['sha']}) — 미리보기 불가")
            else:
                col.caption(f"{p['role']} · 파일 없음 ({p['sha']})")
    else:
        st.caption("아직 붙인 사진이 없다")

    up = st.file_uploader("사진 올리기", type=["png", "jpg", "jpeg"], key=f"up_{block_id}")
    col1, col2 = st.columns([1, 2])
    role = col1.selectbox("구분", issues.PHOTO_ROLES, key=f"role_{block_id}")
    cap = col2.text_input("설명", key=f"cap_{block_id}", max_chars=80)
    if st.button("붙이기", key=f"attach_{block_id}", disabled=up is None,
                 help="올릴 사진을 먼저 고른다"):
        issues.attach_photo(block_id, up.name, up.getvalue(), role, cap)
        st.rerun()


def _alert_tab(block_id: str) -> None:
    """F21 — 「~전 해결」 목표와 경보."""
    info = issues.due_of(block_id)
    if not info["hull"]:
        st.warning("호선이 매핑돼야 일정 경보가 걸린다. 「지식 매핑」 탭에서 호선을 이어 주십시오.", icon=":material/warning:")

    col1, col2, col3 = st.columns(3)
    evt = col1.selectbox(
        "~전 해결", issues.DUE_EVENTS,
        index=issues.DUE_EVENTS.index(info["due_event"]) if info["due_event"] in issues.DUE_EVENTS else 0,
        format_func=lambda e: {"": "(없음)", "DATE": "직접 날짜"}.get(e, e),
        key=f"evt_{block_id}",
    )
    day = col2.date_input("날짜", value=info["due_date"], key=f"day_{block_id}") if evt == "DATE" else None
    days = col3.number_input("경보 일수 (D-n)", 1, 365, int(info["alert_days"]), key=f"days_{block_id}")

    if st.button("목표 저장", key=f"due_{block_id}", type="primary"):
        issues.set_due(block_id, evt, day, int(days))
        st.rerun()

    st.divider()
    if info["target"]:
        left = info["left"]
        if info["label"] == "기한 지남":
            st.error(f"**기한 지남** — 목표 {info['target']} (D{left:+d})", icon=":material/error:")
        elif info["label"] == "일정 임박":
            st.warning(f"**일정 임박** — 목표 {info['target']} (D{left:+d})", icon=":material/schedule:")
        else:
            st.info(f"목표 {info['target']} (D{left:+d})", icon=":material/event:")
        st.caption(
            f"날짜는 저장하지 않는다. {info['hull']}의 일정에서 볼 때마다 다시 잡는다 — "
            "일정이 당겨지면 경보가 저절로 다시 켜진다."
        )
    else:
        st.caption("목표를 정하지 않았다")


def _detail(block_id: str, row: dict[str, object] | None = None) -> None:
    if row:
        chips = " ".join(
            theme.chip(str(row[k]))
            for k in ("유형", "상태", "경보")
            if str(row.get(k) or "").strip()
        )
        st.markdown(
            f'### {block_id} <span style="font-size:var(--fs-2)">{chips}</span>',
            unsafe_allow_html=True,
        )
        st.caption(str(row["제목"]))
    else:
        st.markdown(f"### {block_id}")

    tab_hist, tab_tag, tab_draft, tab_alert = st.tabs(
        ["주차별 진행 (F4)", "지식 매핑 (F3)", "1차 초안 (F5)", "일정 경보 (F21)"]
    )

    with tab_draft:
        _draft_tab(block_id)
    with tab_alert:
        _alert_tab(block_id)

    with tab_hist:
        note = st.text_input("이번 주 한 줄", key=f"note_{block_id}")
        col1, col2 = st.columns([1, 2])
        new_status = col1.selectbox(
            "상태", ["(그대로)", *issues.ASSIGNABLE_STATUSES], key=f"st_{block_id}",
            help="「종결」은 부서가 하지 않는다 — 공유회 진행 화면이나 기획 주관자가 승인한다",
        )
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
                st.toast("기준정보에 걸렸다" if ok else "기준정보에 없다 — 「미등록」으로 남는다",
                         icon=":material/check:" if ok else ":material/help:")
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
        st.info("조건에 맞는 이슈가 없다. 아래에서 등록할 수 있다.", icon=":material/inbox:")

    if rows:
        st.divider()
        _bulk(rows, depts)

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
        _detail(picked, next((r for r in rows if r["ID"] == picked), None))
