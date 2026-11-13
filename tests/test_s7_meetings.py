"""S7 회의자료 — `modules/meetings.py` 의 업무 규칙 (F6 F7 F9 F10 F12 F13 F20, 결정 D·E).

DB 는 `conftest.py` 의 `tmp_db` (임시 파일 SQLite). 가상 데이터만 쓴다.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from modules import issues, meetings
from modules import models as m
from modules.db import session

WID = "2026-W46"


def _issue(title: str = "발전기 진동", dept: str = "D2", **fact: str) -> str:
    bid = issues.create_block(title, owner_department_id=dept)
    if fact:
        meetings.save_fact(bid, fact)
    return bid


def _status(bid: str, status: str) -> None:
    with session() as s:
        s.get(m.Block, bid).status = status
        s.commit()


def _block(bid: str) -> m.Block:
    with session() as s:
        b = s.get(m.Block, bid)
        s.expunge(b)
        return b


def _dept_meeting(dept: str = "D2", wid: str = WID) -> str:
    return meetings.create_meeting("dept", "부서 자료", wid=wid, dept_id=dept)


def _order(mid: str) -> list[str]:
    return [r["ID"] for r in meetings.items(mid)]


def _order_nos(mid: str) -> list[int]:
    with session() as s:
        return list(s.execute(
            select(m.ReportItem.order_no).where(m.ReportItem.meeting_id == mid)
            .order_by(m.ReportItem.order_no)).scalars())


# ── 1. 종결 ──────────────────────────────────────────────────────────────
def test_종결은_부서가_하지_못한다(tmp_db):
    """부서 쪽에는 종결로 가는 길이 없다 (CLAUDE.md 6-7). 두 길을 다 묶는다.
    1) 부서 자료 회의에서는 decide_closure 가 거부된다 (:test_공유회가_아닌_회의에서는_승인되지_않는다 와 같은 규칙을
       여기서는 「부서가 제출까지 마친 뒤」 상황으로 본다).
    2) 부서가 고를 수 있는 상태에 「종결」이 없다."""
    assert "종결" not in issues.ASSIGNABLE_STATUSES
    bid = _issue(action_text="교체 완료")
    _status(bid, "종결요청")
    mid = _dept_meeting()
    meetings.add_items(mid, [bid])
    meetings.submit(mid)
    with pytest.raises(meetings.NotAllowed, match="부서 현안 공유회"):
        meetings.decide_closure(mid, bid, "승인")
    meetings.add_comment(mid, bid, "확인", "comment")
    assert _block(bid).status == "종결요청"
    assert _closure_rows(bid) == []


def test_승인하면_종결이_되고_승인_기록이_남는다(tmp_db):
    bid = _issue(action_text="베어링 교체")
    _status(bid, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [bid])
    meetings.decide_closure(share, bid, "승인")
    assert _block(bid).status == "종결"
    with session() as s:
        row = s.execute(select(m.Closure).where(m.Closure.block_id == bid)).scalars().one()
        assert row.decision == "승인"
        assert row.decided_week_id == WID
        assert row.decided_at is not None
    assert any("종결 승인" in h["한 줄"] for h in issues.history(bid))


def test_보류하면_종결요청이_그대로고_보류가_남는다(tmp_db):
    bid = _issue(action_text="임시 조치")
    _status(bid, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [bid])
    meetings.decide_closure(share, bid, "보류")
    assert _block(bid).status == "종결요청"
    assert meetings.closure_pending(share)[0]["결정"] == "보류"


def test_종결요청_목록에는_종결요청_이슈만_나온다(tmp_db):
    a, b = _issue("가"), _issue("나")
    _status(a, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [a, b])
    assert [r["block_id"] for r in meetings.closure_pending(share)] == [a]



# ── 2. 결정 ──────────────────────────────────────────────────────────────
def test_결정을_남기면_결정_필요가_비워진다(tmp_db):
    bid = _issue(decision_needed="교체 시기 결정")
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_comment(mid, bid, "다음 입거 때 교체", "decision")
    assert _block(bid).decision_needed is None
    assert meetings.comments(mid, bid)[0]["글"] == "다음 입거 때 교체"


def test_일반_코멘트는_결정_필요를_비우지_않는다(tmp_db):
    bid = _issue(decision_needed="교체 시기 결정")
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_comment(mid, bid, "검토 중", "comment")
    assert _block(bid).decision_needed == "교체 시기 결정"


def test_진행_시작_시각은_처음_한_번만_적힌다(tmp_db):
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.start_run(mid)
    first = meetings.meeting(mid)["시작한 때"]
    meetings.start_run(mid)
    assert first is not None and meetings.meeting(mid)["시작한 때"] == first


# ── 3. 취합은 참조 ───────────────────────────────────────────────────────
def test_취합은_장을_복사하지_않고_src로_가리킨다(tmp_db):
    bid = _issue()
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1
    src_id = _order(dept)[0]
    with session() as s:
        row = s.execute(select(m.ReportItem).where(m.ReportItem.meeting_id == share)).scalars().one()
        assert row.src == src_id
        assert row.line is None and row.form is None  # 값을 베끼지 않았다
    assert meetings.items(share)[0]["참조"] == dept


def test_제출_뒤_부서가_표현을_고쳐도_공유회는_판_그대로다(tmp_db):
    """F10 (2026-11-13 변경): 옛 규칙은 「부서에서 고치면 공유회도 따라간다」였다.
    지금은 공유회가 최신 제출판을 참조하므로 표현(한 줄·형태·머리표)은 판에 굳는다."""
    bid = _issue()
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    iid = _order(dept)[0]
    meetings.set_line(iid, "제출 때 한 줄")
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    meetings.set_line(iid, "제출 뒤에 고친 한 줄")
    meetings.set_form(iid, "line")
    meetings.set_tag_on(iid, False)
    row = meetings.items(share)[0]
    assert row["한 줄"] == "제출 때 한 줄"
    assert row["형태"] == "detail"
    assert row["머리표"] is True
    assert row["참조 판"] == 1


def test_제출_뒤_다시_제출하면_공유회는_새_판의_표현을_본다(tmp_db):
    bid = _issue()
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    iid = _order(dept)[0]
    meetings.set_line(iid, "1판 한 줄")
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    meetings.set_line(iid, "2판 한 줄")
    assert meetings.submit(dept) == 2
    row = meetings.items(share)[0]
    assert row["한 줄"] == "2판 한 줄" and row["참조 판"] == 2


def test_제출_뒤_사실이_바뀌면_공유회는_지금_값을_따른다(tmp_db):
    """F10: 표현은 판에 굳지만 사실(이슈 값)은 block 한 벌이라 지금 값을 따른다."""
    bid = _issue(cause_text="체결 불량")
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    meetings.save_fact(bid, {"cause_text": "설계 결함"})
    assert meetings.item_detail(meetings.items(share)[0]["ID"])["cause_text"] == "설계 결함"


def test_취합을_두_번_해도_장이_늘지_않는다(tmp_db):
    """F10: 취합은 제출판만 본다 — 제출을 먼저 한다."""
    dept = _dept_meeting()
    meetings.add_items(dept, [_issue()])
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1
    assert meetings.collect(share, [dept]) == 0
    assert len(meetings.items(share)) == 1


def test_제출하지_않은_자료는_취합되지_않는다(tmp_db):
    dept = _dept_meeting()
    meetings.add_items(dept, [_issue()])
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 0
    assert meetings.items(share) == []


def test_제출_뒤_부서가_더한_장은_취합되지_않는다(tmp_db):
    dept = _dept_meeting()
    meetings.add_items(dept, [_issue("가")])
    meetings.submit(dept)
    meetings.add_items(dept, [_issue("나")])
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1


def test_제출된_부서_자료만_취합_거리로_나온다(tmp_db):
    a, b = _dept_meeting("D1"), _dept_meeting("D2")
    meetings.add_items(a, [_issue("가", "D1")])
    meetings.add_items(b, [_issue("나", "D2")])
    meetings.submit(a)
    assert [r["ID"] for r in meetings.submitted(WID)] == [a]


def test_요약_장도_참조로_실리고_이슈를_따라_읽는다(tmp_db):
    a, b = _issue("가"), _issue("나")
    dept = _dept_meeting()
    meetings.add_summary(dept, [a, b], "진동 2건")
    meetings.submit(dept)  # F10: 제출판만 취합된다
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1
    row = meetings.items(share)[0]
    assert row["종류"] == "summary" and row["요약 건수"] == 2
    with session() as s:
        assert s.execute(select(m.ReportItemBlock)
                         .where(m.ReportItemBlock.item_id == row["ID"])).first() is None


# ── 4. 제출·판 ───────────────────────────────────────────────────────────
def test_제출하면_판이_하나_늘고_상태가_제출이_된다(tmp_db):
    dept = _dept_meeting()
    meetings.add_items(dept, [_issue()])
    assert meetings.meeting(dept)["판"] == 0
    assert meetings.submit(dept) == 1
    assert meetings.submit(dept) == 2
    info = meetings.meeting(dept)
    assert info["상태"] == "제출" and info["판"] == 2
    assert [v["판"] for v in meetings.versions(dept)] == [2, 1]


def test_제출한_판은_뒤에_사실이_바뀌어도_그_시점_글이_남는다(tmp_db):
    bid = _issue(cause_text="체결 불량")
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.submit(dept)
    meetings.save_fact(bid, {"cause_text": "설계 결함"})
    with session() as s:
        snap = json.loads(s.execute(select(m.MeetingVersion.snapshot_json)).scalar_one())
    assert snap[0]["원인"] == "체결 불량"
    assert _block(bid).cause_text == "설계 결함"


def test_정기_회의는_주차마다_한_번만_만들어진다(tmp_db):
    assert meetings.ensure_regular(WID) == 4  # 공유회·정보회의 + 부서 2 (픽스처 부서 2개)
    assert meetings.ensure_regular(WID) == 0


# ── 5. 순서 ──────────────────────────────────────────────────────────────
def _three():
    ids = [_issue(t) for t in ("가", "나", "다")]
    mid = _dept_meeting()
    meetings.add_items(mid, ids)
    return mid


def test_맨_위_장은_위로_옮길_수_없다(tmp_db):
    mid = _three()
    before = _order(mid)
    assert meetings.move_item(before[0], up=True) is False
    assert _order(mid) == before


def test_맨_아래_장은_아래로_옮길_수_없다(tmp_db):
    mid = _three()
    before = _order(mid)
    assert meetings.move_item(before[-1], up=False) is False
    assert _order(mid) == before


def test_가운데_장을_위로_옮기면_둘이_자리를_바꾼다(tmp_db):
    mid = _three()
    a, b, c = _order(mid)
    assert meetings.move_item(b, up=True) is True
    assert _order(mid) == [b, a, c]
    assert meetings.move_item(b, up=False) is True
    assert _order(mid) == [a, b, c]


def test_옮긴_뒤에도_순서_번호가_끊기거나_겹치지_않는다(tmp_db):
    mid = _three()
    a, b, c = _order(mid)
    meetings.move_item(c, up=True)
    meetings.move_item(a, up=False)
    assert _order_nos(mid) == [1, 2, 3]


def test_장을_빼도_이슈는_원장에_남고_되돌리면_같은_자리로_온다(tmp_db):
    mid = _three()
    a, b, c = _order(mid)
    bid = str(meetings.items(mid)[1]["이슈"])
    undo = meetings.remove_item(b)
    assert _order(mid) == [a, c]
    assert _block(bid) is not None
    meetings.restore_item(undo)
    assert _order(mid) == [a, b, c]


def test_이미_실린_이슈는_다시_더해지지_않는다(tmp_db):
    bid = _issue()
    mid = _dept_meeting()
    assert meetings.add_items(mid, [bid]) == 1
    assert meetings.add_items(mid, [bid]) == 0


# ── 6. 요약 장 ───────────────────────────────────────────────────────────
def test_요약_장은_여러_이슈를_한_장에_잇고_이슈는_그대로다(tmp_db):
    a, b = _issue("가", body="현상 가"), _issue("나")
    mid = _dept_meeting()
    iid = meetings.add_summary(mid, [a, b], "진동 2건 묶음")
    rows = meetings.items(mid)
    assert len(rows) == 1 and rows[0]["종류"] == "summary" and rows[0]["요약 건수"] == 2
    assert meetings.item_detail(iid)["block_id"] == ""
    ids = {r["ID"] for r in issues.ledger()}
    assert {a, b} <= ids
    assert _block(a).status == "신규" and _block(a).body == "현상 가"


def test_요약에_든_이슈는_후보_목록에서_빠진다(tmp_db):
    a, b = _issue("가"), _issue("나")
    mid = _dept_meeting()
    meetings.add_summary(mid, [a], "한 건")
    assert [r["ID"] for r in meetings.candidates(mid)] == [b]


def test_종결된_이슈는_후보_목록에_오르지_않는다(tmp_db):
    a, b = _issue("가"), _issue("나")
    _status(a, "종결")
    assert [r["ID"] for r in meetings.candidates(_dept_meeting())] == [b]


def test_이어받기는_진행_중인_이슈만_가져온다(tmp_db):
    a, b = _issue("가"), _issue("나")
    last = _dept_meeting(wid=meetings.shift_week(WID, -1))
    meetings.add_items(last, [a, b])
    _status(b, "종결")
    now = _dept_meeting()
    assert meetings.carry_over(now) == 1
    assert [r["이슈"] for r in meetings.items(now)] == [a]
    assert meetings.meeting(now)["시작"] == "carry"


# ── 7. 지시사항 ──────────────────────────────────────────────────────────
def test_지시는_담당_부서의_다음_주_자료에_보인다(tmp_db):
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_directive(mid, "D2", "도면 재확인", "2026-W48")
    nxt = meetings.shift_week(WID, 1)
    assert [r["내용"] for r in meetings.directives_for("D2", nxt)] == ["도면 재확인"]
    assert meetings.directives_for("D1", nxt) == []


def test_지시는_낸_주보다_앞선_주_자료에는_보이지_않는다(tmp_db):
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_directive(mid, "D2", "도면 재확인", None)
    assert meetings.directives_for("D2", meetings.shift_week(WID, -1)) == []


def test_한_줄_보고로_지시가_완료되고_끝낸_주차에는_보고와_남고_다음_주부터_사라진다(tmp_db):
    """F20 (2026-11-13 변경): 옛 규칙은 완료 즉시 목록에서 사라졌다.
    지금은 「열림 + 이번 주 완료」를 보인다 — 끝낸 주차에는 보고와 함께 남는다."""
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    did = meetings.add_directive(mid, "D2", "도면 재확인", None)
    nxt = meetings.shift_week(WID, 1)
    meetings.finish_directive(did, "확인 완료", nxt)
    on_week = meetings.directives_for("D2", nxt)
    assert [(r["상태"], r["보고"]) for r in on_week] == [("완료", "확인 완료")]
    assert meetings.directives_for("D2", meetings.shift_week(WID, 2)) == []
    done = meetings.directives_of(mid)[0]
    assert done["상태"] == "완료" and done["보고"] == "확인 완료" and done["끝낸 주차"] == nxt


def test_보고가_비면_지시는_완료되지_않는다(tmp_db):
    """finish_directive 독스트링: 「보고가 비면 완료되지 않는다」."""
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    did = meetings.add_directive(mid, "D2", "도면 재확인", None)
    with pytest.raises(meetings.NotAllowed, match="한 줄 보고"):
        meetings.finish_directive(did, "   ")
    assert meetings.directives_of(mid)[0]["상태"] == "열림"


# ── 8. 표현과 사실의 경계 ────────────────────────────────────────────────
def test_한_줄_형태_머리표_고치기는_이슈를_바꾸지_않는다(tmp_db):
    bid = _issue(body="현상", cause_text="원인", action_text="조치", decision_needed="결정")
    mid = _dept_meeting()
    meetings.add_items(mid, [bid])
    iid = _order(mid)[0]
    before = _block(bid)
    meetings.set_line(iid, "회의용 한 줄")
    meetings.set_form(iid, "card")
    meetings.set_tag_on(iid, False)
    after = _block(bid)
    for f in ("title", "body", "cause_text", "action_text", "decision_needed", "status"):
        assert getattr(after, f) == getattr(before, f)
    d = meetings.item_detail(iid)
    assert (d["한 줄"], d["형태"], d["머리표"]) == ("회의용 한 줄", "card", False)


def test_회의자료에서_사실을_고치면_이슈가_바뀌고_장의_표현은_그대로다(tmp_db):
    bid = _issue(body="현상")
    mid = _dept_meeting()
    meetings.add_items(mid, [bid])
    iid = _order(mid)[0]
    meetings.set_line(iid, "한 줄")
    meetings.save_fact(bid, {"cause_text": "새 원인", "action_text": "새 조치"})
    b = _block(bid)
    assert (b.cause_text, b.action_text, b.body) == ("새 원인", "새 조치", "현상")
    assert meetings.item_detail(iid)["한 줄"] == "한 줄"
    assert meetings.item_detail(iid)["cause_text"] == "새 원인"


def test_report_item_에는_사실_칸이_없고_block_에는_표현_칸이_없다(tmp_db):
    ri = {c.name for c in m.ReportItem.__table__.columns}
    bl = {c.name for c in m.Block.__table__.columns}
    assert not ri & {"body", "cause_text", "action_text", "decision_needed"}
    assert not bl & {"line", "form", "order_no", "tag_on", "src"}


@pytest.mark.parametrize("fact", ["body", "cause_text", "action_text", "decision_needed"])
def test_사실을_빈_글로_저장하면_빈_값이_된다(tmp_db, fact):
    bid = _issue(**{fact: "내용"})
    meetings.save_fact(bid, {fact: "  "})
    assert getattr(_block(bid), fact) is None


# ── 9. 막는 규칙과 그 까닭 (NotAllowed) ──────────────────────────────────
def _closure_rows(bid: str) -> list:
    with session() as s:
        return list(s.execute(select(m.Closure).where(m.Closure.block_id == bid)).scalars())


def _logs(bid: str) -> list:
    with session() as s:
        return list(s.execute(select(m.AiFieldLog).where(m.AiFieldLog.block_id == bid)).scalars())


@pytest.mark.parametrize("status", ["신규", "진행"])
def test_종결요청이_아닌_이슈는_승인되지_않는다(tmp_db, status):
    bid = _issue(action_text="조치")
    _status(bid, status)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [bid])
    with pytest.raises(meetings.NotAllowed, match="종결요청"):
        meetings.decide_closure(share, bid, "승인")
    assert _block(bid).status == status
    assert _closure_rows(bid) == []


def test_공유회가_아닌_회의에서는_승인되지_않는다(tmp_db):
    """CLAUDE.md 6-7: 부서 자료에서 승인되면 부서가 스스로 종결하는 길이 열린다."""
    bid = _issue(action_text="조치")
    _status(bid, "종결요청")
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    with pytest.raises(meetings.NotAllowed, match="부서 현안 공유회"):
        meetings.decide_closure(dept, bid, "승인")
    assert _block(bid).status == "종결요청"
    assert _closure_rows(bid) == []


def test_결정_값은_승인_보류만_받는다(tmp_db):
    bid = _issue(action_text="조치")
    _status(bid, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [bid])
    with pytest.raises(meetings.NotAllowed, match="승인 · 보류"):
        meetings.decide_closure(share, bid, "아무말")
    assert _block(bid).status == "종결요청"
    assert _closure_rows(bid) == []


def test_조치_없는_승인이_막히는_까닭은_조치_내용이다(tmp_db):
    """CLAUDE.md 6-7 「조치 내용 필수」. 예전에 따로 있던 「조치 내용 없이는 종결을 승인할 수 없다」 시험은
    아무 예외나 삼키고 상태만 봐서 이 시험과 겹치면서 더 약했다 — 까닭 문구까지 묶는 이쪽으로 합쳤다."""
    bid = _issue()
    _status(bid, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [bid])
    with pytest.raises(meetings.NotAllowed, match="조치 내용"):
        meetings.decide_closure(share, bid, "승인")
    assert _block(bid).status == "종결요청"
    assert _closure_rows(bid) == []


def test_보류_뒤_승인해도_closure_행은_하나다(tmp_db):
    bid = _issue(action_text="조치")
    _status(bid, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [bid])
    meetings.decide_closure(share, bid, "보류")
    meetings.decide_closure(share, bid, "승인")
    rows = _closure_rows(bid)
    assert len(rows) == 1 and rows[0].decision == "승인"
    assert _block(bid).status == "종결"


def test_빈_결정_글은_기록되지_않고_결정_필요도_지워지지_않는다(tmp_db):
    bid = _issue(decision_needed="교체 시기 결정")
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    with pytest.raises(meetings.NotAllowed, match="빈 글"):
        meetings.add_comment(mid, bid, "   ", "decision")
    assert _block(bid).decision_needed == "교체 시기 결정"
    assert meetings.comments(mid) == []


def test_결정은_그_이슈의_결정_필요만_비운다(tmp_db):
    a = _issue("가", decision_needed="가 결정")
    b = _issue("나", decision_needed="나 결정")
    mid = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_comment(mid, a, "정했다", "decision")
    assert _block(a).decision_needed is None
    assert _block(b).decision_needed == "나 결정"


def test_참조_장의_표현은_고칠_수_없다(tmp_db):
    """판에 굳은 글이라 고치면 조용히 사라진다 (F10) — 막고 까닭을 알린다."""
    bid = _issue()
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.set_line(_order(dept)[0], "원래 한 줄")
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    ref = _order(share)[0]
    with pytest.raises(meetings.NotAllowed, match="참조"):
        meetings.set_line(ref, "바꾼 줄")
    with pytest.raises(meetings.NotAllowed, match="참조"):
        meetings.set_form(ref, "card")
    with pytest.raises(meetings.NotAllowed, match="참조"):
        meetings.set_tag_on(ref, False)
    row = meetings.items(share)[0]
    assert (row["한 줄"], row["형태"], row["머리표"]) == ("원래 한 줄", "detail", True)


def test_장을_빼서_번호가_끊긴_뒤_옮겨도_번호가_끊기거나_겹치지_않는다(tmp_db):
    mid = _three()
    a, b, c = _order(mid)
    meetings.remove_item(b)
    assert meetings.move_item(c, up=True) is True
    assert _order(mid) == [c, a]
    assert _order_nos(mid) == [1, 2]


def test_장을_빼고_새로_더해도_순서_번호가_겹치지_않는다(tmp_db):
    mid = _three()
    a, b, c = _order(mid)
    meetings.remove_item(a)
    meetings.add_items(mid, [_issue("라")])
    nos = _order_nos(mid)
    assert len(nos) == len(set(nos)) == 3
    assert _order(mid)[:2] == [b, c]


@pytest.mark.parametrize("kind", ["share", "exec"])
def test_공유회와_팀장_정보회의는_제출되지_않는다(tmp_db, kind):
    """「발행」은 S8 — 여기서는 NotAllowed 로 막고 판도 오르지 않는다."""
    mid = meetings.create_meeting(kind, "회의", wid=WID)
    with pytest.raises(meetings.NotAllowed, match="발행"):
        meetings.submit(mid)
    info = meetings.meeting(mid)
    assert info["판"] == 0 and info["상태"] == "구성 중"
    assert meetings.versions(mid) == []


def test_사실을_고치면_작성_중으로_내려가고_AI_값과_사람_값이_남는다(tmp_db):
    """CLAUDE.md 6-2."""
    import datetime

    bid = _issue()
    with session() as s:
        s.get(m.Block, bid).cause_text = "AI 가 쓴 원인"
        s.get(m.Block, bid).draft_state = "ok"
        s.add(m.AiFieldLog(id="AFL-seed", block_id=bid, field="cause_text",
                           ai_value="AI 가 쓴 원인", human_value=None, model="fake",
                           created_at=datetime.datetime(2026, 11, 1)))
        s.commit()
    meetings.save_fact(bid, {"cause_text": "사람이 고친 원인"})
    assert _block(bid).draft_state == "wip"
    mine = [r for r in _logs(bid) if r.human_value == "사람이 고친 원인"]
    assert len(mine) == 1
    assert mine[0].field == "cause_text" and mine[0].ai_value == "AI 가 쓴 원인"


def test_사실이_그대로면_작성_중으로_내려가지_않고_기록도_없다(tmp_db):
    bid = _issue(cause_text="처음")
    with session() as s:
        s.get(m.Block, bid).draft_state = "ok"
        s.commit()
    before = len(_logs(bid))
    meetings.save_fact(bid, {"cause_text": "처음"})
    assert _block(bid).draft_state == "ok"
    assert len(_logs(bid)) == before


def test_두_번_고쳐도_두_번째_기록에_AI_값이_남는다(tmp_db):
    """CLAUDE.md 6-2: 사람이 두 번 고쳐도 (AI 값, 사람 값)의 AI 값은 이어진다."""
    import datetime

    bid = _issue()
    with session() as s:
        s.get(m.Block, bid).cause_text = "AI 가 쓴 원인"
        s.add(m.AiFieldLog(id="AFL-seed", block_id=bid, field="cause_text",
                           ai_value="AI 가 쓴 원인", human_value=None, model="fake",
                           created_at=datetime.datetime(2026, 11, 1)))
        s.commit()
    meetings.save_fact(bid, {"cause_text": "첫 수정"})
    meetings.save_fact(bid, {"cause_text": "둘째 수정"})
    second = [r for r in _logs(bid) if r.human_value == "둘째 수정"]
    assert len(second) == 1 and second[0].ai_value == "AI 가 쓴 원인"


# ── 9. 값 어휘 — 저장 값과 화면 라벨 (결정 K) ────────────────────────────
def test_시작_방식은_carry로_저장되고_이어받기로_보인다(tmp_db):
    """저장 값은 원본 docs/03 어휘(carry/blank), 화면 말은 「이어받기」·「빈 자료」.
    둘이 섞이면 사내망 데이터와 안 맞는다."""
    a = _issue()
    last = _dept_meeting(wid=meetings.shift_week(WID, -1))
    meetings.add_items(last, [a])
    now = _dept_meeting()
    assert meetings.carry_over(now) == 1
    with session() as s:
        assert s.get(m.Meeting, now).start_mode == "carry"  # DB 에 든 값
    info = meetings.meeting(now)
    assert (info["시작"], info["시작 이름"]) == ("carry", "이어받기")
    blank = _dept_meeting("D1")
    with session() as s:
        assert s.get(m.Meeting, blank).start_mode == "blank"
    info = meetings.meeting(blank)
    assert (info["시작"], info["시작 이름"]) == ("blank", "빈 자료")
    assert meetings.START_MODE_LABELS == {"blank": "빈 자료", "carry": "이어받기"}


# ── 10. 참조는 판에서 읽는다 ─────────────────────────────────────────────
def test_부서가_제출한_뒤_장을_빼도_공유회는_옛_판에서_계속_읽는다(tmp_db):
    bid = _issue("발전기 진동", body="현상 글")
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    iid = _order(dept)[0]
    meetings.set_line(iid, "제출 때 한 줄")
    meetings.set_form(iid, "card")
    meetings.set_tag_on(iid, False)
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1
    meetings.remove_item(iid)  # 부서가 제출 뒤에 그 장을 뺀다
    assert meetings.items(dept) == []
    rows = meetings.items(share)  # 전에는 여기서 AttributeError
    assert len(rows) == 1
    row = rows[0]
    assert row["빠진 장"] is False
    assert (row["한 줄"], row["형태"], row["머리표"]) == ("제출 때 한 줄", "card", False)
    assert (row["참조"], row["참조 판"]) == (dept, 1)
    assert row["제목"] == "발전기 진동" and row["이슈"] == bid
    d = meetings.item_detail(row["ID"])
    assert d["빠진 장"] is False
    assert (d["한 줄"], d["형태"], d["머리표"]) == ("제출 때 한 줄", "card", False)
    assert (d["참조"], d["참조 판"]) == (dept, 1)
    assert d["body"] == "현상 글"


def test_요약_장이_잇는_이슈도_부서가_장을_빼면_판에서_읽는다(tmp_db):
    a, b = _issue("가"), _issue("나")
    dept = _dept_meeting()
    meetings.add_summary(dept, [a, b], "진동 2건")
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    meetings.remove_item(_order(dept)[0])  # report_item_block 행도 함께 지워진다
    with session() as s:
        assert s.execute(select(m.ReportItemBlock)).first() is None
    row = meetings.items(share)[0]
    assert row["빠진 장"] is False
    assert row["종류"] == "summary" and row["요약 건수"] == 2  # 「요약 0건」이 아니다
    assert set(str(row["이슈"]).split(", ")) == {a, b}
    assert row["제목"] == "진동 2건"
    d = meetings.item_detail(row["ID"])
    assert sorted(bid for bid, _ in d["요약"]) == sorted([a, b])
    assert sorted(t for _, t in d["요약"]) == ["가", "나"]


def test_어느_판에도_없는_장은_빠진_장으로_드러난다(tmp_db):
    bid = _issue("발전기 진동")
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    with session() as s:  # 참조가 가리키는 장 ID 가 어느 판에도 없게 만든다
        ref = s.execute(select(m.ReportItem).where(m.ReportItem.meeting_id == share)).scalars().one()
        ref.src = "RI-없는장"
        s.commit()
    row = meetings.items(share)[0]
    assert row["빠진 장"] is True
    assert row["참조 판"] == 0
    assert meetings.item_detail(row["ID"])["빠진 장"] is True
    # 빠진 장도 고칠 수 없고, 까닭에 「빠진 장」이 적힌다
    with pytest.raises(meetings.NotAllowed, match=meetings.MISSING_SRC):
        meetings.set_line(row["ID"], "바꾼 줄")


# ── 11. 안건에 없는 이슈 ─────────────────────────────────────────────────
def test_안건에_없는_이슈는_승인도_보류도_되지_않는다(tmp_db):
    bid = _issue(action_text="교체 완료")
    _status(bid, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)  # bid 를 장으로 올리지 않았다
    for decision in ("승인", "보류"):
        with pytest.raises(meetings.NotAllowed, match="안건에 없는 이슈"):
            meetings.decide_closure(share, bid, decision)
    assert _block(bid).status == "종결요청"
    assert _closure_rows(bid) == []
    assert meetings.closure_pending(share) == []
    meetings.add_items(share, [bid])  # 안건에 올리면 같은 호출이 통과한다
    meetings.decide_closure(share, bid, "승인")
    assert _block(bid).status == "종결"


def test_어느_판에도_없는_요약_장은_제목이_빠진_장이고_요약_0건이_아니다(tmp_db):
    """이슈 한 건짜리는 block 제목이 남지만, 요약 장은 이슈가 없어 제목이 MISSING_SRC 로 드러난다."""
    a, b = _issue("가"), _issue("나")
    dept = _dept_meeting()
    meetings.add_summary(dept, [a, b], "진동 2건")
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.collect(share, [dept])
    with session() as s:
        ref = s.execute(select(m.ReportItem).where(m.ReportItem.meeting_id == share)).scalars().one()
        ref.src = "RI-없는장"
        s.commit()
    row = meetings.items(share)[0]
    assert row["빠진 장"] is True and row["제목"] == meetings.MISSING_SRC
    assert "요약 0건" not in str(row["제목"])
    d = meetings.item_detail(row["ID"])
    assert d["빠진 장"] is True and d["제목"] == meetings.MISSING_SRC


# ── 마지막 회귀 4건 (spec-guard 3차 지적을 고친 동작) ─────────────────────
def test_요약_장으로만_실린_종결요청도_공유회에서_승인_보류된다(tmp_db):
    """고치기 전: 참조 요약 장은 report_item_block 을 베끼지 않아 안건 판정(_block_ids_on)이
    그 이슈를 못 세었다. closure_pending 에 안 나오고 decide_closure 는 「안건에 없다」며
    막았다 — 보이는데 승인은 못 하는 상태. 같은 함수가 candidates·collect 도 지킨다."""
    a = _issue("가", action_text="베어링 교체")
    b = _issue("나", action_text="센서 교체")
    _status(a, "종결요청")
    _status(b, "종결요청")
    dept = _dept_meeting()
    meetings.add_summary(dept, [a, b], "종결요청 2건")
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1
    # 장은 요약 하나뿐이고 report_item_block 은 베껴지지 않았다
    with session() as s:
        ref = s.execute(select(m.ReportItem).where(m.ReportItem.meeting_id == share)).scalars().one()
        assert ref.block_id is None
        assert s.execute(select(m.ReportItemBlock).where(m.ReportItemBlock.item_id == ref.id)).first() is None
    assert {r["block_id"] for r in meetings.closure_pending(share)} == {a, b}
    meetings.decide_closure(share, a, "승인")
    meetings.decide_closure(share, b, "보류")
    assert _block(a).status == "종결"
    assert _block(b).status == "종결요청"
    # 같은 이슈가 후보에 다시 오르지 않고, 재취합은 0건
    _status(a, "신규")  # 후보 조건(열린 상태)을 채워도 이미 실린 이슈라 빠져야 한다
    assert {r["ID"] for r in meetings.candidates(share)}.isdisjoint({a, b})
    assert meetings.collect(share, [dept]) == 0


def test_팀장_정보회의에서는_취합이_모듈에서_막힌다(tmp_db):
    """고치기 전: 「취합」을 공유회에만 보이는 것은 화면뿐이라 collect(exec, ...) 를 직접 부르면
    장이 1개 실렸다. 지금은 NotAllowed 이고 공유회에서는 그대로 된다."""
    bid = _issue()
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.submit(dept)
    exe = meetings.create_meeting("exec", "팀장 정보회의", wid=WID)
    with pytest.raises(meetings.NotAllowed, match="부서 현안 공유회에서 한다"):
        meetings.collect(exe, [dept])
    assert meetings.items(exe) == []
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1


def test_src에는_FK가_없어_FK를_켜도_참조된_장을_뺄_수_있다(tmp_db):
    """src 는 살아 있는 행이 아니라 제출판에 굳은 장의 ID 다. FK 를 걸면 부서의 장 빼기가
    FOREIGN KEY constraint failed 로 막힌다. SQLite 는 기본이 FK 꺼짐이라 일반 시험으로는
    이 회귀가 안 잡힌다 — 그래서 이 시험 안에서만 연결마다 PRAGMA foreign_keys=ON 을 켠다."""
    from sqlalchemy import event

    @event.listens_for(tmp_db, "connect")
    def _fk_on(dbapi_conn, _rec):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    tmp_db.dispose()  # 이미 열린 연결을 버려 새 연결에서 PRAGMA 가 걸리게 한다
    with tmp_db.connect() as c:
        assert c.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    assert not [fk for fk in m.ReportItem.__table__.foreign_keys if fk.parent.name == "src"]

    bid = _issue()
    dept = _dept_meeting()
    meetings.add_items(dept, [bid])
    meetings.submit(dept)
    share = meetings.create_meeting("share", "공유회", wid=WID)
    assert meetings.collect(share, [dept]) == 1
    dept_item = _order(dept)[0]
    meetings.remove_item(dept_item)  # IntegrityError 가 나면 실패
    row = meetings.items(share)[0]
    assert row["빠진 장"] is False
    assert row["참조 판"] == 1


def test_closure_decision에는_승인과_보류만_저장되고_대기는_화면_말이다(tmp_db):
    """고치기 전 위험: 「대기」를 저장 값으로 넣으면 requirements §2-K 어휘가 깨진다.
    결정 전에는 closure 행이 없거나 decision 이 비어 있고, 화면(closure_pending)에서만 「대기」다."""
    a, b, c = (_issue(t, action_text="조치") for t in "가나다")
    for x in (a, b, c):
        _status(x, "종결요청")
    share = meetings.create_meeting("share", "공유회", wid=WID)
    meetings.add_items(share, [a, b, c])
    assert {r["결정"] for r in meetings.closure_pending(share)} == {"대기"}
    meetings.decide_closure(share, a, "승인")
    meetings.decide_closure(share, b, "보류")
    with session() as s:
        saved = set(s.execute(select(m.Closure.decision)).scalars().all())
    assert saved == {"승인", "보류"}
    shown = {r["block_id"]: r["결정"] for r in meetings.closure_pending(share)}
    assert shown[b] == "보류" and shown[c] == "대기"
    assert a not in shown  # 승인되어 종결이 된 이슈는 더 이상 종결요청 목록에 없다
    assert meetings.DECISIONS == ("승인", "보류")
