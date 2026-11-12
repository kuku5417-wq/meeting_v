"""DB 엔진·세션 창구.

엔진은 `@st.cache_resource` 다 — Streamlit 은 상호작용마다 스크립트를 처음부터 다시 도는데
(`code-gen.md` §4④), 매번 엔진을 새로 만들면 연결이 쌓인다. `@st.cache_data` 는 쓰지 않는다
(Engine·Session 은 캐시 키로 쓸 수 없다).

접속 문자열은 `config.paths.db_url()` 이 정본이고, 사내망에서 다른 DB 로 갈 때만
`.streamlit/secrets.toml` 의 `[db] url` 이 그 자리를 대신한다. 둘 다 창구를 거친다 —
여기서 경로를 직접 쓰거나 `st.secrets` 를 직접 읽지 않는다.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import streamlit as st
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from config.paths import DB_PATH, db_url
from config.settings import secrets
from modules.models import Base


@st.cache_resource
def get_engine() -> Engine:
    """엔진 하나를 만들고 표를 없으면 만든다. 프로세스당 한 번만 돈다."""
    url = secrets.section("db").get("url") or db_url()
    if url.startswith("sqlite"):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def session() -> Iterator[Session]:
    """세션 하나. 블록을 벗어나면 닫힌다.

        with session() as s:
            ...
    """
    with Session(get_engine()) as s:
        yield s
