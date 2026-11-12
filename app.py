"""Streamlit 진입점 — S0 골격.

화면은 아직 없다. `views/` 는 S4 이후에 붙고, 여기서 분기한다 (멀티페이지를 쓰지 않는다).
지금 이 파일이 하는 일은 하나다: **설정·경로 창구가 실제로 동작하는지 보여 준다.**

실행:  uv run streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from config import paths
from config.settings import secrets

st.set_page_config(page_title="회의자료·지식화", page_icon="📋", layout="wide")

st.title("커미셔닝팀 주간 회의자료 · 지식화")
st.caption("S0 골격 — 화면은 다음 슬라이스에서 붙는다")

with st.sidebar:
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

st.subheader("홈")
st.write("앱이 떴다. 이 화면은 S10에서 홈(F19)으로 바뀐다.")

st.info(
    "기준정보 15표가 선언되고(S1) 적재됐다(S2). 다음 슬라이스는 **S3 LLM**, "
    "화면은 **S4 설정**부터 붙는다. 단계와 진행율은 `ROADMAP.md`, 만들 것은 `requirements.md`.",
    icon="📌",
)
