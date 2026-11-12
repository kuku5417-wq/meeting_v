"""Streamlit 진입점 — 화면 분기.

멀티페이지를 쓰지 않는다. 화면은 `views/` 에 두고 여기서 하나를 골라 그린다.
새 화면이 생기면 `SCREENS` 에 한 줄 더한다.

실행:  uv run streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from config import paths
from config.settings import secrets
from views import inbox as inbox_view
from views import ledger as ledger_view
from views import settings as settings_view
from views import theme

st.set_page_config(page_title="회의자료·지식화", page_icon="📋", layout="wide")

# 시안 토큰을 입힌다 (SD). 화면을 그리기 전에 한 번만.
theme.apply()


def home() -> None:
    st.subheader("홈")
    st.write("앱이 떴다. 이 화면은 S10에서 홈(F19)으로 바뀐다.")
    st.info(
        "기준정보(S1·S2)·사내 LLM 창구(S3)·설정(S4)·이슈 원장(S5)·기록함(S6)까지 와 있다. "
        "다음은 **S7 회의자료**(후보 이슈 → 회의자료 구성). "
        "단계와 진행율은 `ROADMAP.md`, 만들 것은 `requirements.md`.",
        icon="📌",
    )


# 화면 이름 → 그리는 함수. 슬라이스마다 여기에 한 줄씩 더한다.
SCREENS = {
    "홈": home,
    "기록함": inbox_view.render,
    "이슈 원장": ledger_view.render,
    "설정": settings_view.render,
}

with st.sidebar:
    choice = st.radio("화면", list(SCREENS), key="screen")

    st.divider()
    st.header("상태")

    csv_count = len(sorted(paths.MASTERS_DIR.glob("*.csv"))) if paths.MASTERS_DIR.is_dir() else 0
    st.metric("기준정보 CSV", f"{csv_count}장")

    if paths.DB_PATH.exists():
        from modules.seed import counts

        st.metric("적재된 행", f"{sum(counts().values())}행")
    else:
        st.write("**DB**", "없음 (S2에서 만든다)")

    st.write("**사내 LLM 설정**", "있음" if secrets.has("llm_base_url") else "없음 (사외망에서는 정상)")

    st.divider()
    st.caption("경로 창구")
    st.code(
        f"ROOT        {paths.ROOT}\n"
        f"MASTERS_DIR {paths.MASTERS_DIR.relative_to(paths.ROOT)}\n"
        f"DB_PATH     {paths.DB_PATH.relative_to(paths.ROOT)}\n"
        f"OUT_DIR     {paths.OUT_DIR.relative_to(paths.ROOT)}",
        language=None,
    )

st.title("커미셔닝팀 주간 회의자료 · 지식화")

SCREENS[choice]()
