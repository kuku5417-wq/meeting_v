"""발행된 회의자료를 **편집 가능한 `.pptx`** 로 내보낸다 (F11, `requirements.md` §1-3).

1차 회의자료 화면은 **틀을 고르고 값을 고치는** 화면이다 (2026-11-13 결정 D) — 사람이
글상자를 끌어 옮기는 일은 **파워포인트에서** 한다. 그 파일을 만드는 것이 여기다.
그래서 모든 글은 보통 글상자고, 띠·뱃지는 도형이다 — 열어서 바로 고칠 수 있다.

**입력은 「판」이다.** `meeting_version.snapshot_json` 에서 읽고 (`meetings.snapshot`)
살아 있는 `report_item` 을 다시 긁지 않는다 — 판이 **회의에서 본 그대로**이기 때문이다
(결정 H). 판이 담는 키는 `requirements.md` §1-2-2 `meeting_version` 비고의 **계약**이다:
`ID` · `번호` · `종류` · `형태` · `제목` · `한 줄` · `이슈` · `상태` · `머리표` +
사실 4키(`현상` · `원인` · `조치` · `결정 필요`). **키 이름을 바꾸면 여기가 깨진다.**

**요약 장에는 사실 4키가 없다** — `meetings._snapshot()` 이 `종류 == "single"` 일 때만
넣는다. 요약 장은 판의 **「이슈」 키**로 그린다 (`_summary`) — 사실 키를 찾다가 빈 장이
되게 두지 않는다.

**색은 `tokens.css` 에서 읽는다.** `.py` 에 hex 를 적을 수 없고 (디자인_규칙 §2-1),
무엇보다 **화면과 PPT 가 같은 색이어야** 한다 — `views.theme.token()` 한 문으로 읽는다.

판에 없는 것 셋만 지금 값을 읽는다 (`_extras`) — **유형**(뱃지)·**호선**(머리표)·
**사진**이다. 판에는 글만 굳고 사진은 원본 파일이라 애초에 담기지 않는다.
**마킹 합성은 하지 않는다** (2026-11-13 결정) — `annotation`·`marker` 가 0행이고 마킹
화면이 없어 돌려볼 수가 없다. 사진은 **그대로** 넣고, 합성은 마킹 화면과 함께 만든다.

`python-pptx` 는 필수 의존성이지만 사외망에서 설치가 막힐 수 있다 (`code-gen.md` §4⑦).
없으면 **발행은 그대로 되고 PPT 내보내기만 잠긴다** — `available()` 이 거짓이고
화면은 왜 안 되는지 도움말을 단다 (`UNAVAILABLE`).
"""
from __future__ import annotations

from pathlib import Path

from config.paths import ensure_out
from modules import issues, meetings
from modules import models as m
from modules.db import session
from views.theme import token

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.dml.color import RGBColor
    from pptx.util import Emu, Inches, Pt
except ImportError:  # 선택 설치 — 아래 `available()` 이 거짓이 되고 화면이 버튼을 잠근다
    Presentation = None

UNAVAILABLE = (
    "`python-pptx` 가 없어 PPT 를 만들 수 없다 — 발행과 판은 그대로 되고 내보내기만 막힌다. "
    "`uv sync` 로 깔면 바로 쓸 수 있다 (`diagnostics/check_libs.py`)"
)

# 시안이 1920×1080 으로 그려져 있다 (`v2e-studio.html`). 같은 자리를 그대로 쓰려고
# 슬라이드를 16:9 로 두고 px 를 환산한다 — 1920px 이 13.333in 이라 **1px = 0.5pt** 다.
SLIDE_W_PX, SLIDE_H_PX = 1920, 1080
SLIDE_W_IN = 13.333

# 글꼴은 **파워포인트가 가진 것**만 쓴다. `--body` 사슬 가운데 윈도우에 깔려 있는 것이
# 「Malgun Gothic(맑은 고딕)」이다 — 앱 서브셋(「Meeting Sans KR」)은 PPT 에서 못 찾는다
FONT = "맑은 고딕"

# 유형 뱃지 — 블록 유형 넷 (`issues.BLOCK_TYPES` 가 어휘의 정본이다)
TYPE_LABELS = {"issue": "이슈", "problem": "문제점", "share": "공유정보", "dashboard": "대시보드"}
TYPE_TOKENS = {
    "issue": "--slide-issue",
    "problem": "--slide-problem",
    "share": "--slide-share",
    # 대시보드는 유형 색이 따로 없다 — 슬라이드 구역 색을 쓴다 (`tokens.css`)
    "dashboard": "--slide-sec",
}

# 사실 4키 — 판의 키 이름이다 (`meetings.FACT_LABELS` 의 값과 같은 말).
# 빈 칸은 지어내지 않고 **비어 있다고 적는다** (`CLAUDE.md` §6-3)
EMPTY = "적혀 있지 않다"

# 자리 (px, 1920×1080). 머리띠·바닥띠는 **모든 장**에 있다
BAND_H = 90
FOOT_Y = SLIDE_H_PX - BAND_H
PAD = 80
BODY_W = SLIDE_W_PX - PAD * 2
BADGE_Y, BADGE_H = 112, 56
TITLE_Y, TITLE_H = 182, 80
TOP = 290


def available() -> bool:
    """`python-pptx` 가 있나. 거짓이면 화면이 내보내기 버튼을 잠근다 (`UNAVAILABLE`)."""
    return Presentation is not None


# ── 단위·색 ────────────────────────────────────────────────────────────────
def _px(px: float) -> Emu:
    """시안 px → 슬라이드 길이."""
    return Inches(px * SLIDE_W_IN / SLIDE_W_PX)


def _fs(px: float) -> Pt:
    """시안 글자 px → pt. 1920px = 13.333in 이라 **절반**이다 (28px → 14pt)."""
    return Pt(px / 2)


def _rgb(name: str) -> RGBColor:
    """토큰 이름 → PPTX 색. **hex 는 `tokens.css` 에만 있다** (디자인_규칙 §2-1)."""
    return RGBColor.from_string(token(name).lstrip("#").upper())


# ── 그리는 손 ──────────────────────────────────────────────────────────────
def _rect(slide, x, y, w, h, fill, line=None, shape=None):
    box = slide.shapes.add_shape(shape or MSO_SHAPE.RECTANGLE, _px(x), _px(y), _px(w), _px(h))
    box.fill.solid()
    box.fill.fore_color.rgb = _rgb(fill)
    if line is None:
        box.line.fill.background()
    else:
        box.line.color.rgb = _rgb(line)
        box.line.width = Pt(1)
    box.shadow.inherit = False
    return box


def _write(frame, text, *, size, bold=False, color="--slide-fg", align=PP_ALIGN.LEFT, line=1.4):
    """글상자 하나에 줄마다 한 단락. **편집 가능한 글상자**다 — 글자를 그림으로 굽지 않는다."""
    frame.word_wrap = True
    for i, one in enumerate(str(text).split("\n")):
        para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        para.alignment = align
        para.line_spacing = line
        run = para.add_run()
        run.text = one
        run.font.size = _fs(size)
        run.font.bold = bold
        run.font.name = FONT
        run.font.color.rgb = _rgb(color)


def _text(slide, x, y, w, h, text, **kw):
    box = slide.shapes.add_textbox(_px(x), _px(y), _px(w), _px(h))
    box.text_frame.vertical_anchor = kw.pop("anchor", MSO_ANCHOR.TOP)
    _write(box.text_frame, text, **kw)
    return box


def _badge(slide, x, y, w, text, fill, fg) -> None:
    """색 칠한 도형 + 글자 — 유형 뱃지·머리표 (`v2e-studio` 의 뱃지 개체)."""
    box = _rect(slide, x, y, w, BADGE_H, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    _write(box.text_frame, text, size=24, bold=True, color=fg, align=PP_ALIGN.CENTER, line=1)


def _band(slide, left: str, right: str, y: int) -> None:
    """머리띠·바닥띠 — **모든 장에 있다** (시안의 잠금 개체)."""
    _rect(slide, 0, y, SLIDE_W_PX, BAND_H, "--slide-band")
    _text(
        slide, PAD, y, BODY_W - 500, BAND_H, left,
        size=28, color="--slide-band-fg", anchor=MSO_ANCHOR.MIDDLE,
    )
    _text(
        slide, SLIDE_W_PX - PAD - 500, y, 500, BAND_H, right,
        size=28, color="--slide-band-fg", align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE,
    )


def _soft(slide, x, y, w, h, label, text) -> None:
    """옅은 바탕 블록 — 상세 장의 현상·원인·조치."""
    _rect(slide, x, y, w, h, "--slide-soft", "--slide-line")
    _text(slide, x + 28, y + 18, w - 56, 48, label, size=24, bold=True, color="--slide-muted")
    _text(
        slide, x + 28, y + 72, w - 56, h - 92, str(text) or EMPTY,
        size=26, color="--slide-fg" if str(text) else "--slide-muted", line=1.5,
    )


def _decision(slide, x, y, w, h, text) -> None:
    """「결정 필요」 — 회의에서 정해 주어야 하는 것. 없으면 그 자리를 비운다."""
    if not str(text or "").strip():
        return
    _text(slide, x, y, w, h, f"결정 필요: {text}", size=28, color="--slide-decide", line=1.5)


def _photo(slide, x, y, w, h, shots: list[dict[str, str]]) -> None:
    """사진 **그대로**. 마킹 합성은 하지 않는다 (마킹 화면과 함께 만든다)."""
    path = next((s["path"] for s in shots if Path(s["path"]).exists()), None)
    if path is None:
        _rect(slide, x, y, w, h, "--slide-photo")
        _text(
            slide, x, y + h / 2 - 30, w, 60, "사진 없음",
            size=26, color="--slide-muted", align=PP_ALIGN.CENTER,
        )
        return
    pic = slide.shapes.add_picture(path, _px(x), _px(y), width=_px(w))
    if pic.height > _px(h):  # 긴 사진은 높이에 맞춘다 — 틀을 넘지 않게
        ratio = pic.width / pic.height
        pic.height = _px(h)
        pic.width = int(_px(h) * ratio)
    pic.left = _px(x) + int((_px(w) - pic.width) / 2)
    pic.top = _px(y) + int((_px(h) - pic.height) / 2)
    caption = next((s["caption"] for s in shots if s["path"] == path), "")
    if caption:
        _text(slide, x, y + h + 8, w, 48, caption, size=22, color="--slide-muted")


# ── 판에 없는 것만 지금 값을 읽는다 ────────────────────────────────────────
def _extras(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """장이 가리킨 이슈에서 **유형 · 호선 · 제목**을 읽는다.

    판에 없는 것만이다 — 유형 뱃지는 `block.block_type`(이관해도 ID 는 그대로라 접두어로
    세지 않는다), 머리표의 호선은 `block_tag`, 카드 장의 담당은 `block.owner_department_id`,
    요약 장이 잇는 이슈의 제목은 `block.title` 이다. 판은 요약 장에 「이슈」 ID 만 담는다.
    """
    bids = {b for row in rows for b in str(row.get("이슈") or "").split(", ") if b}
    out: dict[str, dict[str, object]] = {}
    with session() as s:
        for bid in bids:
            blk = s.get(m.Block, bid)
            dept = s.get(m.Department, blk.owner_department_id) if blk else None
            out[bid] = {
                "유형": blk.block_type if blk else "",
                "제목": blk.title if blk else "",
                "부서": dept.name if dept else "",
                "호선": issues.hull_of(s, bid) or "",
            }
    return out


# ── 장 ─────────────────────────────────────────────────────────────────────
def _new(prs):
    """빈 레이아웃. 틀에 글상자를 심지 않는다 — 파워포인트에서 자유롭게 고치게 둔다."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb("--slide")
    return slide


def _right(info) -> str:
    """머리띠 오른쪽 — 누구의 자료인가 (시안은 부서 이름을 둔다).

    부서도 호선도 없는 회의(공유회·팀장 정보회의)는 제목이 이미 갈래라 주차를 둔다.
    """
    return str(info["부서"] or info["호선"] or info["주차"])


def _cover(prs, info, ver: int, n_items: int) -> None:
    """표지 — 회의 제목 · 주차 · 부서 · 안건 수."""
    slide = _new(prs)
    _band(slide, str(info["제목"]), _right(info), 0)
    _band(slide, f"1 / {n_items + 1}" + (f' · {info["호선"]}' if info["호선"] else ""), "표지", FOOT_Y)
    _text(slide, PAD, 280, BODY_W, 200, str(info["제목"]),
          size=72, bold=True, color="--slide-band", line=1.2)
    _text(
        slide, PAD, 500, BODY_W, 70,
        " · ".join(str(x) for x in (info["주차"], info["부서"], info["호선"], f"{ver}판") if x),
        size=36, color="--slide-muted", line=1.5,
    )
    _rect(slide, PAD, 600, 300, 170, "--slide-soft", "--slide-line")
    _text(slide, PAD, 622, 300, 60, "안건", size=26, color="--slide-muted", align=PP_ALIGN.CENTER)
    _text(slide, PAD, 680, 300, 70, str(n_items),
          size=48, bold=True, color="--slide-band", align=PP_ALIGN.CENTER)


def _head(slide, row, info, no: int, total: int, extras) -> None:
    """머리띠·바닥띠·유형 뱃지·머리표·제목 — 모든 장에 같은 자리로 둔다."""
    bids = [b for b in str(row.get("이슈") or "").split(", ") if b]
    first = extras.get(bids[0], {}) if bids else {}
    hull = str(first.get("호선") or info["호선"] or "")
    _band(slide, str(info["제목"]), _right(info), 0)
    _band(
        slide,
        f"{no} / {total}" + (f" · {hull}" if hull else ""),
        meetings.FORM_LABELS.get(str(row["형태"]), str(row["형태"])),
        FOOT_Y,
    )
    if row["종류"] == "single":
        kind = str(first.get("유형") or "")
        _badge(slide, PAD, BADGE_Y, 220, TYPE_LABELS.get(kind, kind) or "블록",
               TYPE_TOKENS.get(kind, "--slide-sec"), "--slide-band-fg")
    else:
        _badge(slide, PAD, BADGE_Y, 220, f"요약 {len(bids)}건", "--slide-band", "--slide-band-fg")
    if row["머리표"] and hull:
        _badge(slide, PAD + 250, BADGE_Y, 260, hull, "--slide-tag", "--slide-tag-fg")
    _text(slide, PAD, TITLE_Y, BODY_W, TITLE_H, str(row["제목"]),
          size=40, bold=True, color="--slide-band", line=1.2)


def _summary(slide, row, extras) -> None:
    """요약 장 (F7) — 판의 **「이슈」 키**로 그린다. 사실 4키는 애초에 없다.

    판은 ID 만 담으므로 제목은 지금 값(`block.title`)을 붙인다 — 요약해도 이슈는
    원장에 그대로 있다.
    """
    bids = [b for b in str(row.get("이슈") or "").split(", ") if b]
    if row["한 줄"]:
        _text(slide, PAD, TOP, BODY_W, 70, str(row["한 줄"]), size=32, color="--slide-fg")
    _text(slide, PAD, TOP + 90, BODY_W, 60, f"묶은 이슈 {len(bids)}건",
          size=24, bold=True, color="--slide-muted")
    _text(
        slide, PAD, TOP + 160, BODY_W, 500,
        "\n".join(f'{b} — {extras.get(b, {}).get("제목", "")}' for b in bids) or EMPTY,
        size=28, color="--slide-fg", line=1.8,
    )


def _single(slide, row, extras) -> None:
    """이슈 한 건 — `form` 네 가지가 레이아웃 네 가지다 (시안 `makeSlide`)."""
    form = str(row["형태"])
    one = str(row["한 줄"] or "")
    dec = str(row.get("결정 필요") or "")
    bids = [b for b in str(row.get("이슈") or "").split(", ") if b]

    if form == "line":
        _text(slide, PAD, 420, BODY_W, 200, one or str(row["제목"]),
              size=44, color="--slide-fg", line=1.4)
        return

    if form == "photo":
        _photo(slide, PAD, TOP, 850, 640, issues.photos(bids[0]) if bids else [])
        _text(slide, 980, TOP, 860, 420, one or str(row.get("현상") or EMPTY),
              size=30, color="--slide-fg", line=1.6)
        _decision(slide, 980, 740, 860, 200, dec)
        return

    if form == "card":
        _text(slide, PAD, TOP, 1200, 130, one, size=32, color="--slide-fg", line=1.6)
        dept = extras.get(bids[0], {}).get("부서", "") if bids else ""
        _text(slide, PAD, 450, 560, 60, f'담당: {dept or "없음"}', size=26, color="--slide-muted")
        _text(slide, 660, 450, 560, 60, f'상태: {row["상태"] or "없음"}',
              size=26, color="--slide-ok" if row["상태"] == "종결" else "--slide-muted")
        _photo(slide, 1360, TOP, 480, 540, issues.photos(bids[0]) if bids else [])
        _decision(slide, PAD, 560, 1200, 140, dec)
        return

    # detail — 현상·원인·조치 3블록 + 결정 필요
    _text(slide, PAD, TOP, BODY_W, 60, one, size=30, color="--slide-muted", line=1.6)
    _soft(slide, PAD, 370, 860, 250, "현상", row.get("현상") or "")
    _soft(slide, 980, 370, 860, 250, "원인", row.get("원인") or "")
    _soft(slide, PAD, 640, BODY_W, 200, "조치", row.get("조치") or "")
    _decision(slide, PAD, 860, BODY_W, 90, dec)


def _deck(info, ver: int, rows: list[dict[str, object]]):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W_IN)
    prs.slide_height = Inches(SLIDE_H_PX * SLIDE_W_IN / SLIDE_W_PX)
    extras = _extras(rows)
    _cover(prs, info, ver, len(rows))
    total = len(rows) + 1
    for no, row in enumerate(rows, start=2):
        slide = _new(prs)
        _head(slide, row, info, no, total, extras)
        # **요약 장에는 사실 4키가 없다** — 판의 「이슈」로 그린다. 형태를 보고 갈라서
        # 사실 키를 찾다가 조용히 빈 장이 되게 두지 않는다
        if row["종류"] == "single":
            _single(slide, row, extras)
        else:
            _summary(slide, row, extras)
    return prs


# ── 내보내기 ───────────────────────────────────────────────────────────────
def file_name(meeting_id: str, version: int) -> str:
    return f"{meeting_id}-{version}판.pptx"


def export(meeting_id: str, version: int | None = None) -> Path:
    """그 회의의 **판**을 `.pptx` 로 쓴다. 판을 주지 않으면 최신 판. 돌려주는 것은 파일 경로.

    파일은 `config.paths.ensure_out()` 아래 떨어진다 — **사내망 전환 지점**이다.
    """
    ver, rows = meetings.snapshot(meeting_id, version)
    if not ver:
        raise meetings.NotAllowed(
            f"{meeting_id} 는 판이 없어 내보낼 글이 없다 — 부서 자료는 「제출」, "
            "나머지 회의는 「발행」을 하면 판이 하나 생긴다"
        )
    path = ensure_out() / file_name(meeting_id, ver)
    _deck(meetings.meeting(meeting_id), ver, rows).save(path)
    return path
