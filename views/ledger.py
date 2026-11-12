"""이슈 원장 (S5) — F2 그리드 · F3 지식 매핑 · F4 주간 업데이트 · F5 1차 초안 ·
F21 일정 경보 · F23 일괄 정리 (`requirements.md` §1-3-2).

같은 일은 같은 방식으로 한다 (`docs/디자인_규칙.md` §3) — 목록은 `ui.card_list`,
거르기는 `ui.filter_pills` + 찾기 칸, 여러 건 처리는 `ui.check_list`.

**주 버튼은 「등록」 하나다** (규칙 2-5). 나머지는 보조 버튼이다.
**저장 버튼을 두지 않는다** — 칸을 고치면 바로 저장된다 (§3 "저장: 자동 저장").

**담당은 부서까지만이다.** 담당자가 아니어도 누구나 고칠 수 있고, 고친 사실은 이력에 남는다 (F2).
**「종결」은 부서가 고르지 않는다** (`CLAUDE.md` §6-7) — 공유회 진행 화면이나 기획 주관자가 승인한다.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st
from sqlalchemy import select

from modules import issues
from modules import models as m
from modules.db import session
from views import theme, ui


def _departments() -> dict[str, str]:
    with session() as s:
        rows = s.execute(select(m.Department).order_by(m.Department.order_no)).scalars().all()
        return {r.id: r.name for r in rows}


# ── 자동 저장 (§3 "저장: 자동 저장, 저장 버튼 없음") ───────────────────────
def _save_draft(block_id: str) -> None:
    issues.save_draft(
        block_id,
        {f: st.session_state.get(f"{f}_{block_id}", "") for f in issues.DRAFT_FIELDS},
        done=False,
    )
    st.toast("초안 저장됨", icon=":material/check:")


def _save_due(block_id: str) -> None:
    evt = st.session_state.get(f"evt_{block_id}", "")
    issues.set_due(
        block_id,
        evt,
        st.session_state.get(f"day_{block_id}") if evt == "DATE" else None,
        int(st.session_state.get(f"days_{block_id}") or issues.DEFAULT_ALERT_DAYS),
    )
    st.toast("목표 저장됨", icon=":material/check:")


# ── 상세 탭 ────────────────────────────────────────────────────────────────
def _tab_history(block_id: str) -> None:
    note = st.text_input("이번 주 한 줄", key=f"note_{block_id}")
    col1, col2 = st.columns([1, 2])
    new_status = col1.selectbox(
        "상태", ["(그대로)", *issues.ASSIGNABLE_STATUSES], key=f"st_{block_id}",
        help="「종결」은 부서가 하지 않는다. 공유회 진행 화면이나 기획 주관자가 승인한다",
    )
    if col2.button(
        "기록하고 다음", key=f"add_{block_id}", icon=":material/arrow_forward:",
        disabled=not note.strip(), help="한 줄을 적으면 누를 수 있다",
    ):
        issues.add_history(block_id, note, None if new_status == "(그대로)" else new_status)
        st.rerun()

    rows = issues.history(block_id)
    if not rows:
        st.caption("아직 적은 진행이 없다")
        return
    for r in rows:
        st.markdown(
            f'<div class="sd-card"><div class="sd-t">{r["한 줄"]}</div>'
            f'<div class="sd-m">{r["주차"]} · {r["상태"]} · {r["적은 때"]}</div></div>',
            unsafe_allow_html=True,
        )


def _tab_tags(block_id: str) -> None:
    rows = issues.tags(block_id)
    if rows:
        for r in rows:
            st.markdown(
                f'<div class="sd-card"><div class="sd-t">{r["현장 표기"]} {theme.chip(r["상태"])}</div>'
                f'<div class="sd-m">{r["갈래"]} · {r["연결"] or "기준정보에 없다"}</div></div>',
                unsafe_allow_html=True,
            )
        if any(r["상태"] == "미등록" for r in rows):
            st.caption(
                "「미등록」은 기준정보에 없는 표기다. 설정 화면에서 기준정보에 더하거나 "
                "별칭으로 이어 주면 다음부터 자동으로 걸린다."
            )
    else:
        st.caption("아직 태그가 없다")

    col1, col2, col3 = st.columns([1, 2, 1])
    kind = col1.selectbox("갈래", issues.MAPPING_KINDS, key=f"kind_{block_id}")
    text = col2.text_input("현장 표기", key=f"tagtext_{block_id}")
    if col3.button(
        "더하기", key=f"tag_{block_id}", icon=":material/add:",
        disabled=not text.strip(), help="표기를 적으면 누를 수 있다",
    ):
        ok = issues.add_tag(block_id, kind, text)
        st.toast(
            "기준정보에 걸렸다" if ok else "기준정보에 없다 — 「미등록」으로 남는다",
            icon=":material/check:" if ok else ":material/help:",
        )
        st.rerun()


def _tab_draft(block_id: str) -> None:
    d = issues.draft(block_id)
    state = {"none": "시작 전", "wip": "작성 중", "ok": "완료"}[d["draft_state"]]
    st.caption(f"초안 상태: **{state}** · 칸을 고치면 바로 저장된다")

    st.text_area("현상", value=d["body"], key=f"body_{block_id}",
                 on_change=_save_draft, args=(block_id,))
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("원인", value=d["cause_text"], key=f"cause_text_{block_id}",
                     on_change=_save_draft, args=(block_id,))
    with col2:
        st.text_area("조치", value=d["action_text"], key=f"action_text_{block_id}",
                     on_change=_save_draft, args=(block_id,))
    st.text_input("결정 필요", value=d["decision_needed"], key=f"decision_needed_{block_id}",
                  placeholder="회의에서 정해 주어야 하는 것",
                  on_change=_save_draft, args=(block_id,))

    if st.button("초안 완료", key=f"ddone_{block_id}", icon=":material/task_alt:"):
        issues.save_draft(
            block_id,
            {f: st.session_state.get(f"{f}_{block_id}", "") for f in issues.DRAFT_FIELDS},
            done=True,
        )
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
    col1, col2, col3 = st.columns([1, 2, 1])
    role = col1.selectbox("구분", issues.PHOTO_ROLES, key=f"role_{block_id}")
    cap = col2.text_input("설명", key=f"cap_{block_id}", max_chars=80)
    if col3.button(
        "붙이기", key=f"attach_{block_id}", icon=":material/attach_file:",
        disabled=up is None, help="올릴 사진을 먼저 고른다",
    ):
        issues.attach_photo(block_id, up.name, up.getvalue(), role, cap)
        st.rerun()


def _tab_alert(block_id: str) -> None:
    info = issues.due_of(block_id)
    if not info["hull"]:
        st.warning(
            "호선이 매핑돼야 일정 경보가 걸린다. 「지식 매핑」에서 호선을 이어 주십시오.",
            icon=":material/warning:",
        )

    st.caption("고치면 바로 저장된다")
    col1, col2, col3 = st.columns(3)
    evt = col1.selectbox(
        "~전 해결", issues.DUE_EVENTS,
        index=issues.DUE_EVENTS.index(info["due_event"]) if info["due_event"] in issues.DUE_EVENTS else 0,
        format_func=lambda e: {"": "(없음)", "DATE": "직접 날짜"}.get(e, e),
        key=f"evt_{block_id}", on_change=_save_due, args=(block_id,),
    )
    if evt == "DATE":
        col2.date_input("날짜", value=info["due_date"], key=f"day_{block_id}",
                        on_change=_save_due, args=(block_id,))
    col3.number_input("경보 일수 (D-n)", 1, 365, int(info["alert_days"]),
                      key=f"days_{block_id}", on_change=_save_due, args=(block_id,))

    st.divider()
    if info["target"]:
        left = info["left"]
        body = f"목표 {info['target']} (D{left:+d})"
        if info["label"] == "기한 지남":
            st.error(f"**기한 지남** — {body}", icon=":material/error:")
        elif info["label"] == "일정 임박":
            st.warning(f"**일정 임박** — {body}", icon=":material/schedule:")
        else:
            st.info(body, icon=":material/event:")
        st.caption(
            f"날짜는 저장하지 않는다. {info['hull']}의 일정에서 볼 때마다 다시 잡는다 — "
            "일정이 당겨지면 경보가 저절로 다시 켜진다."
        )
    else:
        st.caption("목표를 정하지 않았다")


def _detail(row: dict[str, object]) -> None:
    block_id = str(row["ID"])
    chips = " ".join(
        theme.chip(str(row[k])) for k in ("유형", "상태", "경보") if str(row.get(k) or "").strip()
    )
    st.markdown(
        f'### {block_id} <span style="font-size:var(--fs-2)">{chips}</span>',
        unsafe_allow_html=True,
    )
    st.caption(str(row["제목"]))

    tab_hist, tab_tag, tab_draft, tab_alert = st.tabs(
        ["주차별 진행", "지식 매핑", "1차 초안", "일정 경보"]
    )
    with tab_hist:
        _tab_history(block_id)
    with tab_tag:
        _tab_tags(block_id)
    with tab_draft:
        _tab_draft(block_id)
    with tab_alert:
        _tab_alert(block_id)


# ── 등록·일괄 ──────────────────────────────────────────────────────────────
def _new_issue(depts: dict[str, str]) -> None:
    with st.form("new_issue", clear_on_submit=True):
        st.markdown("**이슈 등록**")
        title = st.text_input("제목", placeholder="No.2 발전기 배기온도 편차")
        col1, col2, col3 = st.columns(3)
        block_type = col1.selectbox("유형", issues.BLOCK_TYPES, index=0)
        dept = col2.selectbox("담당 부서", ["(없음)", *depts], format_func=lambda d: depts.get(d, d))
        hull = col3.text_input("호선", placeholder="2511 · SN2511")
        equip = st.text_input("장비 (현장 표기 그대로)", placeholder="DG2 · D/G #2 · 2번 발전기")
        body = st.text_area("현상", placeholder="무엇이 어떻게 되고 있는가")
        # 이 화면의 **유일한** 주 버튼이다 (규칙 2-5)
        if st.form_submit_button("등록", type="primary", icon=":material/add:"):
            if not title.strip():
                st.error("제목은 있어야 한다")
                return
            bid = issues.create_block(
                title=title, block_type=block_type,
                owner_department_id=None if dept == "(없음)" else dept,
                body=body, hull_text=hull, equipment_text=equip,
            )
            st.toast(f"{bid} 등록", icon=":material/check:")
            st.rerun()


def _bulk(rows: list[dict[str, object]], depts: dict[str, str]) -> None:
    with st.expander("일괄 정리"):
        st.caption("체크한 뒤 한꺼번에 바꾼다. 이관해도 ID 는 그대로고, 바뀐 것은 주차별 진행에 남는다.")
        picked = ui.check_list(rows, ["ID", "호선", "제목", "상태"], key="bulk_check")

        col1, col2, col3 = st.columns(3)
        dept = col1.selectbox("담당 부서", ["(그대로)", *depts],
                              format_func=lambda d: depts.get(d, d), key="bulk_dept")
        status = col2.selectbox(
            "상태", ["(그대로)", *issues.ASSIGNABLE_STATUSES], key="bulk_status",
            help="「종결」은 부서가 하지 않는다. 공유회 진행 화면이나 기획 주관자가 승인한다",
        )
        important = col3.selectbox("중요", ["(그대로)", "중요", "보통"], key="bulk_important")

        if st.button(
            "한꺼번에 바꾸기", key="bulk_go", icon=":material/done_all:",
            disabled=not picked, help="바꿀 이슈를 먼저 체크한다",
        ):
            n = issues.bulk_update(
                picked,
                department_id=None if dept == "(그대로)" else dept,
                status=None if status == "(그대로)" else status,
                important=None if important == "(그대로)" else (important == "중요"),
            )
            st.toast(f"{n}건 바꿨다" if n else "바뀐 것이 없다", icon=":material/check:")
            st.rerun()


def render() -> None:
    st.header("이슈 원장")
    depts = _departments()
    counts = issues.counts()

    # 거르기 — 칩 + 찾기 칸 (§3). 건수는 칩 안에 넣어 지표를 따로 두지 않는다
    col1, col2 = st.columns([3, 2])
    with col1:
        f_status = ui.filter_pills("상태", issues.STATUSES, "f_status", counts=counts)
    with col2:
        q = ui.search_box("f_query")
    f_dept = st.pills("부서", list(depts), format_func=lambda d: depts[d], key="f_dept", default=None)

    rows = issues.ledger(status=f_status, department_id=f_dept)
    if q:
        low = q.lower()
        rows = [r for r in rows if low in f"{r['제목']} {r['호선']} {r['장비']} {r['ID']}".lower()]

    narrowed = bool(f_status or f_dept or q)
    st.caption(f"{len(rows)}건" + (f" · 전체 {sum(counts.values())}건" if narrowed else ""))

    picked = ui.card_list(
        rows, "ID",
        title=lambda r: f"{r['ID']}  {r['제목']}",
        meta=lambda r: " · ".join(
            x for x in (
                r["호선"], r["장비"], r["부서"],
                theme.chip(str(r["상태"])),
                theme.chip(str(r["경보"])) if r["경보"] else "",
                f"매핑 {r['매핑']}",
                r["금주 진행"],
            ) if x
        ),
        key="ledger_list",
        empty="조건에 맞는 이슈가 없다. 아래에서 등록할 수 있다.",
    )

    if rows:
        st.divider()
        _bulk(rows, depts)

    st.divider()
    _new_issue(depts)

    if picked:
        row = next((r for r in rows if str(r["ID"]) == picked), None)
        if row:
            st.divider()
            _detail(row)
