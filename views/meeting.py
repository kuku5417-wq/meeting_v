"""회의자료 (S7·S8) — F6 장 구성 · F7 요약 · F8 사실 되먹임 · F9 부서 제출 · F10 취합 ·
F11 발행·PPT · F12 회의 진행 · F13 종결 승인 · F20 지시사항 (`requirements.md` §1-3-2).

**회의자료의 한 장은 `report_item` 하나다** (2026-11-13 결정 D). 1차 회의자료는
**틀(`form`)을 고르고 값을 고치는** 화면이다 — 사람이 글상자를 끌어 옮기지 않는다.
자유 캔버스(절대 좌표·색·격자)는 2차고, 「편집 가능한 PPT」는 S8 의 `.pptx` 내보내기다.

같은 일은 같은 방식으로 한다 (`docs/디자인_규칙.md` §3) — 목록은 `ui.card_list`,
거르기는 `ui.filter_pills` + 찾기 칸, 여러 건은 `ui.check_list`, **저장 버튼은 없다**(자동 저장),
빼기는 **바로 하고 되돌리기**, 장 **순서는 「↑ 위로 · ↓ 아래로」 버튼**(§2-E — 끌어 놓기는 쓰지 않는다).

**표현은 `report_item`, 사실은 `block`.** 「장」 탭의 한 줄·형태·머리표는 회의자료 것이고,
현상·원인·조치·결정 필요는 이슈 원장과 같은 한 벌이다 — 여기서 고치면 원장이 따라간다.

**주 버튼은 한 화면에 하나다** (규칙 2-5) — 탭마다 하나다. 「장 구성」은 부서 자료면
「제출」(F9)·나머지 회의면 「발행」(F11)이고, 「회의 진행」은 「기록하고 다음」이다.
**발행은 되돌릴 수 없어 확인을 받는다** (규칙 2-6) — 그 자리만 그렇다.
**「종결」은 부서가 하지 않는다** (`CLAUDE.md` §6-7) — 승인은 부서 현안 공유회의 진행 화면이다.
"""
from __future__ import annotations

import datetime
import html
from pathlib import Path

import streamlit as st

from modules import meetings as mg
from modules import pptx_export
from views import theme, ui


# ── 자동 저장 (§3 "저장: 자동 저장, 저장 버튼 없음") ───────────────────────
def _save_held_on(meeting_id: str) -> None:
    mg.set_held_on(meeting_id, st.session_state.get(f"held_{meeting_id}"))
    st.toast("회의 날짜 저장됨", icon=":material/check:")


def _save_line(item_id: str) -> None:
    mg.set_line(item_id, st.session_state.get(f"line_{item_id}", ""))
    st.toast("한 줄 저장됨", icon=":material/check:")


def _save_form(item_id: str) -> None:
    mg.set_form(item_id, st.session_state.get(f"form_{item_id}", "detail"))
    st.toast("형태 바뀜 — 틀만 바뀌고 사실은 그대로다", icon=":material/check:")


def _save_tag(item_id: str) -> None:
    mg.set_tag_on(item_id, bool(st.session_state.get(f"tag_{item_id}")))


def _save_fact(item_id: str, block_id: str) -> None:
    mg.save_fact(
        block_id,
        {f: st.session_state.get(f"fact_{f}_{item_id}", "") for f in mg.FACT_FIELDS},
    )
    st.toast("사실 저장됨 — 이슈 원장도 함께 바뀐다", icon=":material/check:")


# ── F20 받은 지시사항 — 부서 자료 맨 위 ────────────────────────────────────
def _received_directives(info: dict[str, object]) -> None:
    """받은 지시 — **낸 주차부터** 보이고, 그 주에 끝낸 것도 보고와 함께 남아 있다 (F20)."""
    rows = mg.directives_for(str(info["부서 ID"]), str(info["주차"]))
    if not rows:
        return
    st.markdown("**받은 지시사항** — 한 줄 보고로 끝낸다")
    for r in rows:
        with st.container(border=True):
            st.markdown(
                f'{theme.chip(str(r["상태"]))} {html.escape(str(r["내용"]))}',
                unsafe_allow_html=True,
            )
            st.caption(
                f'{r["낸 회의"]} · 기한 {r["기한"] or "없음"}'
                + (f' · {r["이슈"]}' if r["이슈"] else "")
            )
            if r["상태"] == "완료":
                st.caption(f'보고: {r["보고"]}')
                continue
            col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
            note = col1.text_input("한 줄 보고", key=f'dn_{r["ID"]}')
            if col2.button(
                "완료 보고", key=f'df_{r["ID"]}', icon=":material/check_circle:",
                disabled=not note.strip(), help="한 줄을 적으면 누를 수 있다",
            ):
                mg.finish_directive(str(r["ID"]), note, str(info["주차"]))
                st.toast("지시 완료", icon=":material/check_circle:")
                st.rerun()
    st.divider()


# ── F6 장 구성 ─────────────────────────────────────────────────────────────
def _item_props(item_id: str) -> None:
    """고른 장의 속성 — **표현**(한 줄·형태·머리표)과 **사실**(현상·원인·조치·결정 필요)."""
    d = mg.item_detail(item_id)
    if d["빠진 장"]:
        # 참조한 판에서 그 장을 못 찾았다 (F10 `_src_ref`) — 보통 장처럼 보이게 두지 않는다.
        # 표현은 그래도 고치지 못한다 — 참조로 실은 장이다.
        st.warning(
            f'{d["참조"] or "부서 자료"} 에서 **{mg.MISSING_SRC}**이다 — 참조한 판에서 '
            "이 장을 찾지 못했다. 회의에서 다룰 것이면 부서에 다시 올려 달라고 하고, "
            "아니면 이 장을 뺀다. 아래 **사실**은 이슈 것이라 그대로 보인다.",
            icon=":material/link_off:",
        )
    elif d["참조"]:
        # 참조 장의 표현은 그 판에 굳었다 (F10) — 고치는 칸을 내보이지 않는다.
        # 아래 「사실」은 이슈 것이라 고치면 원장·부서 자료에도 함께 반영된다.
        st.info(
            f'{d["참조"]} 의 {d["참조 판"]}판을 **참조로** 실었다. 한 줄·형태·머리표는 '
            "그 판에 굳어 여기서 고치지 않는다 — 고칠 것이 있으면 부서가 고쳐 다시 제출한다. "
            "아래 **사실**은 이슈 것이라 고치면 원장에도 함께 반영된다.",
            icon=":material/link:",
        )
        st.caption(
            f'{mg.FORM_LABELS.get(str(d["형태"]), str(d["형태"]))} · '
            f'한 줄: {d["한 줄"] or "없음"} · 머리표 {"보임" if d["머리표"] else "숨김"}'
        )
    else:
        col1, col2 = st.columns([1, 3])
        col1.selectbox(
            "형태", mg.FORMS,
            index=mg.FORMS.index(str(d["형태"])) if d["형태"] in mg.FORMS else 0,
            format_func=lambda f: mg.FORM_LABELS[f],
            key=f"form_{item_id}", on_change=_save_form, args=(item_id,),
            help="틀만 바뀌고 사실은 그대로다",
        )
        col2.text_input(
            "회의용 한 줄", value=str(d["한 줄"]), key=f"line_{item_id}",
            placeholder="회의에서 읽을 한 줄", on_change=_save_line, args=(item_id,),
        )
        st.checkbox(
            "머리표 보이기", value=bool(d["머리표"]), key=f"tag_{item_id}",
            on_change=_save_tag, args=(item_id,),
            help="호선·장비 머리표를 그 장 위에 보인다",
        )

    if d["종류"] == "summary":
        st.divider()
        st.markdown(f'**요약한 이슈 {len(d["요약"])}건** — 요약해도 이슈는 원장에 그대로 있다')
        for bid, title in d["요약"]:
            ui.card(title, bid)
        return

    if not d["block_id"]:
        return

    st.divider()
    st.markdown("**사실** — 여기서 고치면 그 이슈가 바뀐다 (원장·부서 자료도 같은 값을 본다)")
    st.caption(f'{d["block_id"]} · 상태 {d["상태"]} · 고치면 초안은 「작성 중」으로 내려간다')
    st.text_area(
        mg.FACT_LABELS["body"], value=str(d["body"]), key=f"fact_body_{item_id}",
        on_change=_save_fact, args=(item_id, str(d["block_id"])),
    )
    col1, col2 = st.columns(2)
    with col1:
        st.text_area(
            mg.FACT_LABELS["cause_text"], value=str(d["cause_text"]),
            key=f"fact_cause_text_{item_id}",
            on_change=_save_fact, args=(item_id, str(d["block_id"])),
        )
    with col2:
        st.text_area(
            mg.FACT_LABELS["action_text"], value=str(d["action_text"]),
            key=f"fact_action_text_{item_id}",
            on_change=_save_fact, args=(item_id, str(d["block_id"])),
        )
    st.text_input(
        mg.FACT_LABELS["decision_needed"], value=str(d["decision_needed"]),
        key=f"fact_decision_needed_{item_id}",
        placeholder="회의에서 정해 주어야 하는 것",
        on_change=_save_fact, args=(item_id, str(d["block_id"])),
    )


def _order_buttons(meeting_id: str, rows: list[dict[str, object]], picked: str) -> None:
    """장 순서 — 「↑ 위로 · ↓ 아래로」 (§2-E). 끝에서는 그쪽 버튼이 잠긴다 (규칙 2-7)."""
    at = [str(r["ID"]) for r in rows].index(picked)
    col1, col2, col3 = st.columns([1, 1, 3])
    if col1.button(
        "위로", key=f"up_{picked}", icon=":material/arrow_upward:",
        disabled=at == 0, help="맨 위 장이다" if at == 0 else "한 칸 위로 옮긴다",
    ):
        mg.move_item(picked, up=True)
        st.rerun()
    if col2.button(
        "아래로", key=f"down_{picked}", icon=":material/arrow_downward:",
        disabled=at == len(rows) - 1,
        help="맨 아래 장이다" if at == len(rows) - 1 else "한 칸 아래로 옮긴다",
    ):
        mg.move_item(picked, up=False)
        st.rerun()
    # 빼기는 확인을 묻지 않고 바로 하고 되돌리기를 준다 (§3 "삭제·취소")
    if col3.button("장 빼기", key=f"del_{picked}", icon=":material/delete:"):
        st.session_state[f"undo_{meeting_id}"] = mg.remove_item(picked)
        st.session_state.pop(f"items_{meeting_id}__sel", None)
        st.rerun()


def _undo_bar(meeting_id: str) -> None:
    undo = st.session_state.get(f"undo_{meeting_id}")
    if not undo:
        return
    col1, col2 = st.columns([4, 1], vertical_alignment="center")
    # 한 일을 알리는 것이다 — 「확인 필요」가 아니라 알림이다
    col1.info("장 하나를 뺐다. 이슈는 원장에 그대로 있다.", icon=":material/delete:")
    if col2.button("되돌리기", key=f"undo_btn_{meeting_id}", icon=":material/undo:"):
        item_id = mg.restore_item(undo)
        st.session_state.pop(f"undo_{meeting_id}", None)
        st.session_state[f"items_{meeting_id}__sel"] = item_id
        st.toast("장을 되돌렸다", icon=":material/check:")
        st.rerun()


def _add_from_ledger(info: dict[str, object], expanded: bool) -> None:
    """후보 이슈 → 장 (F6) · 여러 이슈 → 한 장으로 요약 (F7).

    거르기는 **칩 + 찾기 칸**이고 건수는 칩 안에 넣는다 (`docs/디자인_규칙.md` §3).
    """
    mid = str(info["ID"])
    with st.expander("후보 이슈에서 장 만들기", expanded=expanded):
        all_rows = mg.candidates(mid)
        if not all_rows:
            st.caption("올릴 후보가 없다. 이슈 원장에서 이슈를 등록하거나, 이미 다 실었다.")
            return

        depts = mg.departments()
        by_name: dict[str, int] = {}
        for r in all_rows:
            by_name[str(r["부서"])] = by_name.get(str(r["부서"]), 0) + 1
        counts = {d: by_name[n] for d, n in depts.items() if n in by_name}

        col1, col2 = st.columns([3, 1])
        with col1:
            only = ui.filter_pills(
                "부서", list(counts), f"cdept_{mid}",
                counts=counts, format_func=lambda d: depts[d],
            )
            q = ui.search_box(f"cquery_{mid}", placeholder="제목·호선·장비로 찾기")
        form = col2.selectbox(
            "형태", mg.FORMS, format_func=lambda f: mg.FORM_LABELS[f], key=f"cform_{mid}"
        )

        rows = all_rows if only is None else mg.candidates(mid, department_id=only)
        if q:
            low = q.lower()
            rows = [
                r for r in rows
                if low in f'{r["제목"]} {r["호선"]} {r["장비"]} {r["ID"]}'.lower()
            ]
        if not rows:
            st.caption("걸러낸 후보가 없다. 칩을 지우거나 찾는 말을 바꾼다.")
            return
        st.caption("아직 이 자료에 없는 열린 이슈다")
        picked = ui.check_list(rows, ["ID", "호선", "제목", "단계", "상태"], key=f"cand_{mid}")

        col1, col2, col3 = st.columns([1, 1, 2])
        if col1.button(
            "장으로 더하기", key=f"addi_{mid}", icon=":material/add:",
            disabled=not picked, help="올릴 이슈를 먼저 체크한다",
        ):
            n = mg.add_items(mid, picked, form)
            st.toast(f"{n}장 더했다" if n else "이미 실린 이슈다", icon=":material/check:")
            st.rerun()
        line = col3.text_input(
            "요약 한 줄", key=f"sumline_{mid}", placeholder="예: 조타기 관련 2건"
        )
        if col2.button(
            "한 장으로 요약", key=f"adds_{mid}", icon=":material/compress:",
            disabled=len(picked) < 2,
            help="두 건 이상 체크하면 누를 수 있다 — 요약해도 이슈는 그대로 남는다",
        ):
            item_id = mg.add_summary(mid, picked, line)
            st.session_state[f"items_{mid}__sel"] = item_id
            st.toast(f"{len(picked)}건을 한 장으로 요약했다", icon=":material/check:")
            st.rerun()


def _collect(info: dict[str, object]) -> None:
    """F10 취합 — 부서 제출판을 **참조로** 싣는다. 복사하지 않는다."""
    mid = str(info["ID"])
    with st.expander("부서 제출판 취합"):
        rows = mg.submitted(str(info["주차"]))
        if not rows:
            st.caption(f'{info["주차"]} 에 제출된 부서 자료가 없다. 부서가 제출하면 여기 보인다.')
            return
        st.caption(
            "베끼지 않고 **최신 제출판**을 가리킨다 — 한 줄·형태·머리표는 그 판 그대로 굳고, "
            "사실(현상·원인·조치)만 지금 값을 따른다. 제출 뒤에 부서가 더한 장은 실리지 않고, "
            "이미 실은 장·이슈는 건너뛴다."
        )
        picked = ui.check_list(rows, ["ID", "부서", "장", "판"], key=f"coll_{mid}")
        if st.button(
            "참조로 싣기", key=f"collgo_{mid}", icon=":material/library_add:",
            disabled=not picked, help="실을 부서 자료를 먼저 체크한다",
        ):
            n = mg.collect(mid, picked)
            st.toast(f"{n}장 실었다" if n else "더 실을 장이 없다", icon=":material/check:")
            st.rerun()


def _tab_items(info: dict[str, object], rows: list[dict[str, object]]) -> None:
    mid = str(info["ID"])
    _undo_bar(mid)

    if not rows:
        st.caption("아직 장이 없다. 아래 「후보 이슈에서 장 만들기」로 이슈를 골라 장으로 만든다.")
        if st.button(
            "지난주 이어받기", key=f"carry_{mid}", icon=":material/history:",
            help="지난 주 같은 자료에서 **진행 중인 이슈**만 장으로 가져온다",
        ):
            n = mg.carry_over(mid)
            st.toast(
                f"{n}장 이어받았다" if n else "지난 주에 이어받을 장이 없다",
                icon=":material/check:" if n else ":material/info:",
            )
            st.rerun()
    else:
        picked = ui.card_list(
            rows, "ID",
            title=lambda r: f'{r["번호"]}. {r["제목"]}',
            meta=lambda r: " · ".join(
                str(x) for x in (
                    r["종류 이름"], r["형태 이름"], r["한 줄"], r["이슈"], r["부서"],
                    (
                        f'{r["참조"]} 에서 {mg.MISSING_SRC}' if r["빠진 장"]
                        else f'{r["참조"]} {r["참조 판"]}판 참조'
                    ) if r["참조"] else "",
                ) if x
            ),
            chips=lambda r: theme.chip(str(r["상태"])) if r["상태"] else "",
            key=f"items_{mid}",
            empty="아직 장이 없다",
        )
        if picked:
            st.divider()
            _order_buttons(mid, rows, picked)
            _item_props(picked)

    st.divider()
    # 장이 없으면 안내가 가리키는 자리를 펴 준다 (규칙 2-7 빈 상태)
    _add_from_ledger(info, expanded=not rows)
    # 취합은 **부서 현안 공유회에만** 있다 (2026-11-13 결정). 원본 `docs/07` 의 팀장 정보회의
    # 자료는 「공유회 채택분 + 원장에서 추가」라 부서 제출판을 바로 가져가지 않는다 —
    # 「공유회에서 가져오기」는 **2차**고, 1차의 팀장 정보회의는 후보 이슈에서 장을 올린다
    if info["갈래"] == "share":
        _collect(info)
    elif info["갈래"] == "exec":
        st.caption(
            "팀장 정보회의 자료는 후보 이슈에서 장을 직접 올린다. 공유회에서 채택한 장을 "
            "그대로 가져오는 「공유회에서 가져오기」는 2차다."
        )

    st.divider()
    if info["갈래"] == "dept":
        _submit(info, rows)
    else:
        _publish(info, rows)


def _submit(info: dict[str, object], rows: list[dict[str, object]]) -> None:
    """F9 부서 제출 — **상태 표시만**이다. 마감·경고·재제출 규칙은 2차다."""
    mid = str(info["ID"])
    done = info["상태"] == "제출"
    if done:
        st.success(
            f'{info["판"]}판으로 제출됐다. 그 판은 회의에서 본 그대로 남는다.',
            icon=":material/check_circle:",
        )
    st.caption(
        "제출하면 판이 하나 오르고 그 판의 글이 굳는다. 「종결」은 이슈에 쓰는 말이라 "
        "여기 없다. PPT 는 「판」 탭에서 판마다 내려받는다."
    )
    # 이 화면의 **유일한** 주 버튼이다 (규칙 2-5)
    if st.button(
        "제출", key=f"submit_{mid}", type="primary", icon=":material/send:",
        disabled=done or not rows,
        help=(
            "재제출 규칙은 2차다 — 1차는 상태 표시까지다" if done
            else "실은 장이 있어야 제출할 수 있다" if not rows
            else "부서 현안 공유회로 넘긴다"
        ),
    ):
        v = mg.submit(mid)
        st.toast(f"{v}판으로 제출했다", icon=":material/check:")
        st.rerun()


def _publish(info: dict[str, object], rows: list[dict[str, object]]) -> None:
    """F11 발행 — 판으로 고정한다. **「제출」과 쌍이고 부서 자료가 아닌 회의의 말이다.**

    **되돌릴 수 없는 일이라 확인을 받는다** (`docs/디자인_규칙.md` §2-6) — 장 빼기처럼
    바로 하고 되돌리기를 주는 자리가 아니다. 판은 지워지지 않는다.
    막는 것은 화면이 아니라 `mg.publish()` 다 — 여기 버튼은 거들기만 한다.
    """
    mid = str(info["ID"])
    if info["상태"] == "발행":
        st.success(
            f'{info["판"]}판으로 발행됐다. 그 판은 회의에서 본 그대로 남는다.',
            icon=":material/check_circle:",
        )
    elif info["상태"] == "수정됨":
        # `--signal` 의 뜻 「발행 뒤 바뀜」 — 상태 칩도 같은 색이다 (`views/theme.py`)
        st.warning(
            f'{info["판"]}판을 발행한 뒤 장이 바뀌었다 — 다시 발행하면 '
            f'{int(info["판"] or 0) + 1}판이 되고 {info["판"]}판은 그대로 남는다.',
            icon=":material/edit_note:",
        )
    st.caption(
        "발행하면 판이 하나 오르고 그 판의 글이 굳는다. 발행 뒤 장을 고치면 「수정됨」으로 "
        "보이고, 다시 발행하면 다음 판이다. PPT 는 「판」 탭에서 판마다 내려받는다."
    )
    can = bool(rows) and info["상태"] != "발행"
    ok = st.checkbox(
        "판으로 굳히는 것을 확인했다", key=f"pubok_{mid}", disabled=not can,
        help="발행은 되돌릴 수 없다 — 옛 판은 지워지지 않고 그대로 남는다",
    )
    # 이 탭의 **유일한** 주 버튼이다 (규칙 2-5). 부서 자료에서는 「제출」이 그 자리다
    if st.button(
        "발행", key=f"publish_{mid}", type="primary", icon=":material/campaign:",
        disabled=not can or not ok,
        help=(
            "고친 것이 없다 — 장을 고치면 「수정됨」이 되고 그때 다시 발행한다"
            if info["상태"] == "발행"
            else "실은 장이 있어야 발행할 수 있다" if not rows
            else "확인에 체크하면 누를 수 있다" if not ok
            else "이 회의자료를 판으로 고정한다"
        ),
    ):
        v = mg.publish(mid)
        st.toast(f"{v}판으로 발행했다", icon=":material/check:")
        st.rerun()


# ── F12 회의 진행 · F13 종결 승인 ──────────────────────────────────────────
def _closures(info: dict[str, object]) -> None:
    mid = str(info["ID"])
    st.markdown("**종결요청**")
    if info["갈래"] != "share":
        st.caption(
            "종결 승인은 **부서 현안 공유회**에서 한다 (또는 기획 주관자가 홈에서). "
            "이 회의에서는 승인하지 않는다."
        )
        return
    rows = mg.closure_pending(mid)
    if not rows:
        st.caption("이 회의에 올라온 종결요청이 없다")
        return
    for r in rows:
        with st.container(border=True):
            st.markdown(
                f'{theme.chip(str(r["결정"]))} {html.escape(str(r["제목"]))}',
                unsafe_allow_html=True,
            )
            st.caption(f'{r["block_id"]} · 조치: {r["조치"] or "적혀 있지 않다"}')
            col1, col2 = st.columns([1, 1])
            can = bool(str(r["조치"]).strip())
            if col1.button(
                "종결 승인", key=f'ca_{mid}_{r["block_id"]}', icon=":material/verified:",
                disabled=not can,
                help="조치 내용이 있어야 승인할 수 있다" if not can else "이슈가 「종결」이 된다",
            ):
                mg.decide_closure(mid, str(r["block_id"]), "승인")
                st.toast("종결 승인 — 사례 카드 만들기는 지식창고에서 한다",
                         icon=":material/verified:")
                st.rerun()
            if col2.button("보류", key=f'ch_{mid}_{r["block_id"]}', icon=":material/pause:",
                           help="상태는 「종결요청」 그대로다 — 다음 주에 다시 올라온다"):
                mg.decide_closure(mid, str(r["block_id"]), "보류")
                st.toast("보류했다", icon=":material/check:")
                st.rerun()


def _tab_run(info: dict[str, object], rows: list[dict[str, object]]) -> None:
    mid = str(info["ID"])
    if not rows:
        st.caption("실은 장이 없다. 「장 구성」에서 이슈를 골라 장으로 만든다.")
        return

    # 안건을 옮기는 값은 **위젯을 만들기 전에** 넣어야 한다 — 버튼 안에서 위젯 key 를 고치면
    # Streamlit 이 `StreamlitWidgetAlreadyInstantiatedError` 를 낸다. 그래서 버튼은
    # `jump_` 에 적어 두고, 다시 도는 머리에서 그 값을 위젯 key 로 옮긴다.
    key = f"agenda_{mid}"
    jump = st.session_state.pop(f"jump_{mid}", None)
    if jump is not None:
        st.session_state[key] = jump
    if st.session_state.get(key) not in range(len(rows)):
        st.session_state[key] = 0
    labels = [f'{r["번호"]}. {r["제목"]}' for r in rows]
    at = st.selectbox(
        "안건", range(len(rows)), format_func=lambda i: labels[i], key=key
    )
    row = rows[at]
    d = mg.item_detail(str(row["ID"]))

    with st.container(border=True):
        st.markdown(
            f'**{html.escape(str(d["제목"]))}** '
            f'{theme.chip(str(d["상태"])) if d["상태"] else ""}',
            unsafe_allow_html=True,
        )
        if d["한 줄"]:
            st.caption(str(d["한 줄"]))
        for f in mg.FACT_FIELDS:
            if d[f]:
                st.markdown(f'{mg.FACT_LABELS[f]} — {str(d[f])}')
        if d["decision_needed"]:
            st.markdown(theme.chip("결정 필요"), unsafe_allow_html=True)
            st.caption("결정을 남기면 이 칸이 비워진다 — 다음 주에 같은 안건이 또 올라오지 않는다.")

    col1, col2, col3 = st.columns([3, 1, 1], vertical_alignment="bottom")
    text = col1.text_input("기록", key=f"ctext_{mid}_{at}", placeholder="코멘트 또는 결정")
    kind = col2.selectbox(
        "갈래", mg.COMMENT_KINDS, format_func=lambda k: mg.COMMENT_LABELS[k],
        key=f"ckind_{mid}_{at}",
    )
    # 이 화면의 **유일한** 주 버튼이다 (규칙 2-5). 부서 자료에서는 「제출」이 그 자리다
    if col3.button(
        "기록하고 다음", key=f"crec_{mid}_{at}", type="primary",
        icon=":material/arrow_forward:",
        disabled=not text.strip(), help="기록을 적으면 누를 수 있다",
    ):
        mg.start_run(mid)
        mg.add_comment(mid, str(d["block_id"]) or None, text, kind)
        st.session_state[f"jump_{mid}"] = min(at + 1, len(rows) - 1)
        st.toast("기록했다", icon=":material/check:")
        st.rerun()

    col1, col2 = st.columns([1, 1])
    if col1.button(
        "이전 장", key=f"prev_{mid}", icon=":material/arrow_back:",
        disabled=at == 0, help="첫 장이다" if at == 0 else "한 장 앞으로",
    ):
        st.session_state[f"jump_{mid}"] = at - 1
        st.rerun()
    if col2.button(
        "다음 장", key=f"next_{mid}", icon=":material/arrow_forward:",
        disabled=at == len(rows) - 1,
        help="마지막 장이다" if at == len(rows) - 1 else "한 장 뒤로",
    ):
        st.session_state[f"jump_{mid}"] = at + 1
        st.rerun()

    st.divider()
    _closures(info)

    st.divider()
    st.markdown("**이 회의 기록**")
    logs = mg.comments(mid)
    if not logs:
        st.caption("아직 적은 기록이 없다")
    else:
        for r in logs:
            ui.card(
                str(r["글"]),
                " · ".join(str(x) for x in (r["이슈"], r["때"]) if x),
                chips=theme.chip(str(r["갈래"])),
            )


# ── F20 지시사항 ───────────────────────────────────────────────────────────
def _tab_directives(info: dict[str, object], rows: list[dict[str, object]]) -> None:
    mid = str(info["ID"])
    wid = str(info["주차"])
    depts = mg.departments()

    st.markdown("**지시 남기기** — 낸 주차부터 그 부서 회의자료 맨 위에 나온다")
    text = st.text_input("내용", key=f"dtext_{mid}", placeholder="무엇을 언제까지 하는가")
    col1, col2, col3 = st.columns([2, 2, 2])
    dept = col1.selectbox(
        "담당 부서", list(depts), format_func=lambda d: depts[d], key=f"ddept_{mid}"
    )
    weeks = [mg.shift_week(wid, i) for i in range(4)]
    due = col2.selectbox(
        "기한 주차", weeks, index=1, key=f"ddue_{mid}",
        help="그 주차의 부서 자료까지다",
    )
    labels = {"": "(없음)"} | {str(r["이슈"]): str(r["제목"]) for r in rows if r["이슈"]}
    block = col3.selectbox(
        "이슈 연결", list(labels), format_func=lambda b: labels[b], key=f"dblk_{mid}"
    )
    if st.button(
        "지시 남기기", key=f"dadd_{mid}", icon=":material/add:",
        disabled=not text.strip(), help="내용을 적으면 누를 수 있다",
    ):
        mg.add_directive(mid, dept, text, due, block or None)
        st.toast("지시를 남겼다", icon=":material/check:")
        st.rerun()

    st.divider()
    st.markdown("**이 회의에서 낸 지시**")
    got = mg.directives_of(mid)
    if not got:
        st.caption("아직 낸 지시가 없다")
        return
    for r in got:
        ui.card(
            str(r["내용"]),
            " · ".join(
                str(x) for x in (
                    r["부서"], f'기한 {r["기한"]}' if r["기한"] else "", r["이슈"],
                    f'보고: {r["보고"]}' if r["보고"] else "",
                ) if x
            ),
            chips=theme.chip(str(r["상태"])),
        )


# ── F11 PPT 내보내기 ──────────────────────────────────────────────────────
def _ppt(mid: str, ver: int, made: dict[int, str]) -> None:
    """판 하나를 `.pptx` 로 — **편집 가능한 PPT** 다 (F11).

    만드는 일과 내려받는 일을 가른다. 판마다 미리 만들어 두면 화면을 그릴 때마다
    파일을 다 만들어야 한다 — 누른 판만 만든다. 파일은 `out/` 에 남는다
    (`config.paths.ensure_out`, 사내망 전환 지점).

    `python-pptx` 가 없으면 **발행은 그대로 되고 이 버튼만 잠긴다** (`code-gen.md` §4⑦).
    """
    has = pptx_export.available()
    col1, col2 = st.columns([1, 1])
    if col1.button(
        "PPT 만들기", key=f"pptmk_{mid}_{ver}", icon=":material/slideshow:", disabled=not has,
        help=pptx_export.UNAVAILABLE if not has else "판에 굳은 글로 .pptx 를 만든다 — 파워포인트에서 글상자를 옮길 수 있다",
    ):
        path = pptx_export.export(mid, ver)
        made[ver] = str(path)
        st.toast(f"{path.name} 만들었다", icon=":material/check:")
        st.rerun()
    made_path = Path(made[ver]) if made.get(ver) else None
    if made_path is None or not made_path.exists():
        return
    col2.download_button(
        "PPT 내려받기", data=made_path.read_bytes(), file_name=made_path.name,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        key=f"pptdl_{mid}_{ver}", icon=":material/download:",
    )
    st.caption(f"{made_path} 에 있다")


def _tab_versions(info: dict[str, object]) -> None:
    mid = str(info["ID"])
    rows = mg.versions(mid)
    st.caption("판은 회의에서 본 그대로 남는다. 뒤에 사실이 바뀌어도 이 글은 바뀌지 않는다.")
    if not rows:
        st.caption(
            "아직 판이 없다 — 부서 자료는 「제출」, 나머지 회의는 「발행」을 하면 1판이 된다"
        )
        return
    made: dict[int, str] = st.session_state.setdefault(f"ppt_{mid}", {})
    for r in rows:
        with st.container(border=True):
            st.markdown(f'**{r["판"]}판**')
            st.caption(f'{r["때"]} · 장 {r["장"]}개')
            _ppt(mid, int(str(r["판"])), made)


# ── 회의 한 건 ─────────────────────────────────────────────────────────────
def _meeting(meeting_id: str) -> None:
    info = mg.meeting(meeting_id)
    # 갈래는 **회의 종류**다 — 의미 색은 뜻으로만 쓴다 (규칙 2-2). `share`(공유 정보 블록)
    # 색을 「부서 현안 공유회」에 쓰지 않는다. 갈래 칩은 중립색이다
    chips = " ".join(
        [theme.chip(str(info["갈래 이름"])), theme.chip(str(info["상태"]))]
        + ([theme.chip(f'{info["판"]}판')] if info["판"] else [])
    )
    st.markdown(
        f'### {html.escape(str(info["제목"]))} '
        f'<span style="font-size:var(--fs-2)">{chips}</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        " · ".join(
            str(x) for x in (
                info["ID"], info["주차"], info["부서"], info["호선"],
                # 저장 값은 코드(`carry`/`blank`)고 **보이는 말은 「시작 이름」**이다 —
                # 화면이 코드를 번역하지 않는다 (`mg.START_MODE_LABELS` 한 군데)
                f'장 {info["장"]}개',
                f'시작 {info["시작 이름"]}' if info["시작 이름"] else "",
            ) if x
        )
    )
    col1, col2 = st.columns([1, 3], vertical_alignment="center")
    col1.date_input(
        "회의 날짜", value=info["날짜"], key=f"held_{meeting_id}", format="YYYY-MM-DD",
        on_change=_save_held_on, args=(meeting_id,),
        help="모르면 비워 둔다 — 주차만 보인다",
    )
    col2.caption("고치면 바로 저장된다")

    if info["갈래"] == "dept":
        st.divider()
        _received_directives(info)

    rows = mg.items(meeting_id)
    if info["갈래"] == "dept":
        tab_items, tab_ver = st.tabs(["장 구성", "판"])
        with tab_items:
            _tab_items(info, rows)
        with tab_ver:
            _tab_versions(info)
        return

    tab_items, tab_run, tab_dir, tab_ver = st.tabs(["장 구성", "회의 진행", "지시사항", "판"])
    with tab_items:
        _tab_items(info, rows)
    with tab_run:
        _tab_run(info, rows)
    with tab_dir:
        _tab_directives(info, rows)
    with tab_ver:
        _tab_versions(info)


# ── 수시 회의 만들기 ───────────────────────────────────────────────────────
def _new_meeting(wid: str) -> None:
    with st.expander("수시 회의 만들기"):
        st.caption(
            "정기 회의(부서 자료 8건·공유회·팀장 정보회의)는 주차마다 저절로 생긴다. "
            "여기서는 호선별 회의와 문제점·장비 리뷰만 만든다."
        )
        col1, col2, col3 = st.columns(3)
        kind = col1.selectbox(
            "종류", mg.ADHOC_KINDS, format_func=lambda k: mg.KIND_LABELS[k], key="nm_kind"
        )
        hull_list = ["(없음)", *mg.hulls()]
        hull = col2.selectbox("호선", hull_list, key="nm_hull")
        day = col3.date_input("회의 날짜", value=None, format="YYYY-MM-DD", key="nm_day")
        title = st.text_input(
            "제목", key="nm_title", placeholder=f"{mg.KIND_LABELS[kind]} — 비우면 종류 이름을 쓴다"
        )
        if st.button("만들기", key="nm_go", icon=":material/add:"):
            mid = mg.create_meeting(
                kind, title, wid,
                hull_id=None if hull == "(없음)" else hull,
                held_on=day if isinstance(day, datetime.date) else None,
            )
            st.session_state["meeting_list__sel"] = mid
            st.toast(f"{mid} 만들었다", icon=":material/check:")
            st.rerun()


def render() -> None:
    st.header("회의자료")

    # 이번 주 정기 회의는 저절로 생긴다 (시안 "매주 자동으로 생겨 「만들기」가 필요 없습니다").
    # **이번 주만** 만든다 — 지난 주차를 보려고 고른 것이 새 자료를 만들어서는 안 된다.
    mg.ensure_regular()

    # 주차는 **무엇을 볼지 옮기는 것**이라 칩이 아니라 고르는 칸이다 (디자인_규칙 §3)
    col1, col2 = st.columns([1, 3])
    wid = col1.selectbox("주차", mg.week_options(), key="mt_week")
    rows = mg.meetings(wid)

    with col2:
        counts: dict[str, int] = {}
        for r in rows:
            counts[str(r["갈래"])] = counts.get(str(r["갈래"]), 0) + 1
        f_kind = ui.filter_pills(
            "갈래", [k for k in mg.KINDS if k in counts], "f_mkind",
            counts=counts, format_func=lambda k: mg.KIND_LABELS[k],
        )
        q = ui.search_box("f_mquery", placeholder="제목·부서·호선으로 찾기")

    if f_kind:
        rows = [r for r in rows if r["갈래"] == f_kind]
    if q:
        low = q.lower()
        rows = [
            r for r in rows
            if low in f'{r["제목"]} {r["부서"]} {r["호선"]} {r["ID"]}'.lower()
        ]

    # 건수는 거르기 칩 안에 있다 (`docs/디자인_규칙.md` §3) — 따로 적지 않는다
    picked = ui.card_list(
        rows, "ID",
        title=lambda r: f'{r["갈래 이름"]}  {r["제목"]}',
        meta=lambda r: " · ".join(
            str(x) for x in (
                r["주차"], r["부서"], r["호선"],
                r["날짜"].strftime("%Y-%m-%d") if r["날짜"] else "",
                f'장 {r["장"]}개',
            ) if x
        ),
        chips=lambda r: " ".join(
            [theme.chip(str(r["상태"]))] + ([theme.chip(f'{r["판"]}판')] if r["판"] else [])
        ),
        key="meeting_list",
        empty="그 주차에는 회의가 없다. 아래에서 수시 회의를 만들 수 있다.",
        auto_select=False,
    )

    st.divider()
    _new_meeting(wid)

    if picked:
        st.divider()
        _meeting(picked)
