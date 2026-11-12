"""시안 디자인 토큰을 앱에 입힌다 (SD).

정본은 `docs/_시안/design/tokens.css` 다. **값을 여기서 새로 만들지 않는다** — 옮겨 적을 뿐이다.
시안이 바뀌면 여기도 같이 고친다. 토큰이 두 군데로 갈리면 화면마다 색이 달라진다.

**라이트만 쓴다** (2026-11-12 결정). 시안에는 `prefers-color-scheme` 다크도 있지만 받지 않는다.
그래서 여기 값은 `tokens.css` 의 `:root` 블록(라이트)만이다.

**글꼴은 대체 사슬로 간다.** 시안의 서브셋(`docs/_시안/app/static/fonts/*.woff2`, 823KB)은
아직 저장소 앱 쪽에 두지 않았다 — 그 결정이 남아 있다(`ROADMAP.md` 「디자인」 절).
지금은 `tokens.css` 가 적어 둔 대체 사슬(IBM Plex Sans KR → Apple SD Gothic Neo → 맑은 고딕)로
떨어진다. 서브셋을 넣으면 시안과 똑같아진다.

색의 뜻 (시안 그대로)
  --share  공유정보 · --danger 문제점/빈 필수 · --signal 이슈/확인 필요
  --ok     종결/완료 · --decide 결정 필요 · --accent 주 색/대기 중인 일
"""
from __future__ import annotations

import streamlit as st

# tokens.css :root (라이트) 에서 앱 화면이 쓰는 것만 옮겼다. 슬라이드·사진 토큰은 S8 에서.
TOKENS = """
  --bg:#eef1f5; --surface:#ffffff; --surface-2:#f3f5f8;
  --fg:#111114; --muted:#48484d; --line:#dfe4ea; --field-line:#7d8693;
  --accent:#0963c4; --accent-soft:#e5f0fd; --accent-fg:#ffffff; --accent-ink:#0857b0;
  --side-bg:#1c2f4f; --side-fg:#dbe3ee; --side-muted:#a9b6c8; --side-bar:#4c9bff;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 0 0 1px rgba(16,24,40,.04);
  --signal:#9a5a00; --signal-soft:#fbefd9;
  --danger:#b83a26; --danger-soft:#f8e3df;
  --ok:#276d43; --ok-soft:#dff0e5;
  --share:#35589c; --share-soft:#e2e9f6;
  --decide:#6a3fb5; --decide-soft:#ece4f8;
  --body:"Meeting Sans KR","IBM Plex Sans KR","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;
  --mono:"Meeting Mono","IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
  --fs-1:12px; --fs-2:14px; --fs-3:16px; --fs-4:20px; --fs-5:26px;
  --fw-strong:600;
"""

# 상태·유형 → 의미 색 토큰. 화면이 색을 직접 고르지 않게 한 군데 둔다.
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

_CSS = f"""
<style>
:root {{{TOKENS}}}

html, body, [class*="st-"], .stMarkdown, button, input, textarea, select {{
  font-family: var(--body);
}}
code, pre, .stCode {{ font-family: var(--mono); }}

/* 사이드바는 시안의 네이비 */
section[data-testid="stSidebar"] {{ background: var(--side-bg); }}
section[data-testid="stSidebar"] * {{ color: var(--side-fg); }}
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{ color: #ffffff; }}
section[data-testid="stSidebar"] [data-testid="stMetricLabel"],
section[data-testid="stSidebar"] .stCaption {{ color: var(--side-muted); }}
section[data-testid="stSidebar"] code {{ background: rgba(255,255,255,.08); color: var(--side-fg); }}

/* 본문 카드 — 흰 바탕에 옅은 테두리 (시안의 --shadow) */
[data-testid="stMetric"], div[data-testid="stExpander"], div[data-testid="stForm"],
div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"]:has(> div) {{
  background: var(--surface);
}}
[data-testid="stMetric"] {{
  border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; box-shadow: var(--shadow);
}}
h1, h2, h3 {{ font-weight: var(--fw-strong); letter-spacing: -.01em; }}
h1 {{ font-size: var(--fs-5); }}
h2 {{ font-size: var(--fs-4); }}
h3 {{ font-size: var(--fs-3); }}
.stCaption, small {{ font-size: var(--fs-1); color: var(--muted); }}

/* ID·호선번호처럼 숫자가 줄 맞는 곳 */
[data-testid="stDataFrame"] {{ font-variant-numeric: tabular-nums; }}

.sd-chip {{
  display:inline-block; padding:1px 8px; border-radius:99px;
  font-size: var(--fs-1); font-weight: var(--fw-strong); line-height:1.7;
}}
</style>
"""


def apply() -> None:
    """화면을 그리기 전에 한 번 부른다. `app.py` 에서만 부른다."""
    st.markdown(_CSS, unsafe_allow_html=True)


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
