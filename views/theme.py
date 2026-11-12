"""디자인 토큰을 앱에 입힌다 (SD). 규칙은 `docs/디자인_규칙.md`.

**이 파일에 색을 적지 않는다.** hex 를 직접 쓸 수 있는 곳은 `tokens.css` 와
`.streamlit/config.toml` 뿐이다 (디자인_규칙 §2-1). 여기는 **토큰 파일을 읽어 넣기만** 한다.

| 넣는 순서 | 파일 | |
|---|---|---|
| 1 | `docs/_시안/design/tokens.css` | 시안 원본. **고치지 않는다** |
| 2 | `static/tokens.css` | 앱에서 달라지는 값만 (흰 사이드바, `--sep`, `--warn-soft`) |

**라이트만 쓴다** (2026-11-12 결정). 시안 파일에는 `@media (prefers-color-scheme: dark)` 와
`[data-theme]` 블록이 있는데 `_light_only()` 가 걷어낸다.

색의 뜻은 디자인_규칙 §2-2 — `--share` 공유정보 · `--danger` 문제·빈 필수 ·
`--signal` 이슈·확인 필요·발행 뒤 바뀜 · `--accent` 주 동작·대기 · `--ok` 종결·완료 ·
`--decide` 결정. 장식에 쓰지 않는다.
"""
from __future__ import annotations

import re

import streamlit as st

from config.paths import APP_TOKENS, MOCKUP_TOKENS

# 상태·유형 → 의미 색 토큰. 화면이 색을 직접 고르지 않게 한 군데 둔다 (디자인_규칙 §2-2).
MEANING = {
    "신규": "signal",
    "진행": "accent",
    "종결요청": "decide",
    "종결": "ok",
    "issue": "signal",
    "problem": "danger",
    "share": "share",
    "dashboard": "accent",
    "일정 임박": "signal",
    "기한 지남": "danger",
    "미등록": "danger",
    "연결됨": "ok",
}

# 다크 블록을 걷어낸다 — @media(...){ :root...{...} } 와 :root[data-theme...]{...}
_DARK_MEDIA = re.compile(r"@media[^{]*prefers-color-scheme[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", re.S)
_DARK_ATTR = re.compile(r":root\[data-theme[^{]*\{[^{}]*\}", re.S)
_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _light_only(css: str) -> str:
    """라이트 블록만 남긴다. 주석도 턴다 (주석 안에 다크 값이 적혀 있다)."""
    return _DARK_ATTR.sub("", _DARK_MEDIA.sub("", _COMMENT.sub("", css))).strip()


def _tokens() -> str:
    """두 토큰 파일을 라이트만 남겨 이어 붙인다. 파일이 `:root{...}` 를 갖고 있으므로 그대로 쓴다."""
    parts = []
    for path in (MOCKUP_TOKENS, APP_TOKENS):
        if path.exists():
            parts.append(_light_only(path.read_text(encoding="utf-8")))
    return "\n".join(parts)


# 토큰 변수만 쓴다. 이 안에 hex 가 없어야 한다.
_LAYOUT = """
html, body, [class*="st-"], .stMarkdown, button, input, textarea, select {
  font-family: var(--body);
}
code, pre, .stCode { font-family: var(--mono); }

/* 아이콘은 글꼴이 바뀌면 글자로 보인다 (":material/flag:" 가 "flag" 로).
   위 규칙이 넓어서 아이콘 span 까지 덮으므로 여기서 되돌린다.
   이 글꼴은 Streamlit 이 함께 넣어 둬서 사외망·사내망 모두 뜬다. */
[data-testid="stIconMaterial"],
[data-testid="stAlertDynamicIcon"],
[data-testid="stElementToolbarButtonIcon"] {
  font-family: "Material Symbols Rounded";
}

/* 사이드바는 흰색 — 2026-11-13 결정 (디자인_규칙 §1). 시안 v2m 의 네이비를 따르지 않는다 */
section[data-testid="stSidebar"] {
  background: var(--side-bg);
  border-right: 1px solid var(--sep);
}
section[data-testid="stSidebar"] * { color: var(--side-fg); }
section[data-testid="stSidebar"] [data-testid="stMetricLabel"],
section[data-testid="stSidebar"] .stCaption { color: var(--side-muted); }
section[data-testid="stSidebar"] code {
  background: var(--surface-2); color: var(--side-fg);
}
/* 지금 메뉴 — 바탕 accent-soft, 글자 accent-ink, 왼쪽 막대 accent */
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: var(--accent-soft);
  border-left: 3px solid var(--accent);
  border-radius: 0 4px 4px 0;
  padding-left: 8px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {
  color: var(--accent-ink);
  font-weight: var(--fw-strong);
}

[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: var(--shadow);
}
h1, h2, h3 { font-weight: var(--fw-strong); letter-spacing: -.01em; color: var(--fg); }
h1 { font-size: var(--fs-5); }
h2 { font-size: var(--fs-4); }
h3 { font-size: var(--fs-3); }
.stCaption, small { font-size: var(--fs-1); color: var(--muted); }

/* ID·호선번호처럼 숫자가 줄 맞는 곳 */
[data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }

.sd-chip {
  display: inline-block; padding: 1px 8px; border-radius: 99px;
  font-size: var(--fs-1); font-weight: var(--fw-strong); line-height: 1.7;
}
"""


def apply() -> None:
    """화면을 그리기 전에 한 번 부른다. `app.py` 에서만 부른다."""
    st.markdown(f"<style>\n{_tokens()}\n{_LAYOUT}</style>", unsafe_allow_html=True)


def chip(text: str, kind: str | None = None) -> str:
    """의미 색이 붙은 작은 배지의 HTML.

    `kind` 를 주지 않으면 `text` 자체(상태·유형 이름)로 색을 찾는다.
    찾지 못하면 중립색이다 — 색을 지어내지 않는다.
    """
    token = MEANING.get(kind or text)
    if token is None:
        return f'<span class="sd-chip" style="background:var(--surface-2);color:var(--muted)">{text}</span>'
    return (
        f'<span class="sd-chip" style="background:var(--{token}-soft);'
        f'color:var(--{token})">{text}</span>'
    )
