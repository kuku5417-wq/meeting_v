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
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session

from config.paths import DB_PATH, db_url
from config.settings import secrets
from modules.models import Base


def add_new_columns(engine: Engine) -> list[str]:
    """모델에 생겼는데 DB 표에는 없는 칸을 더한다 — **사외망 작업본(SQLite) 전용**.

    `create_all` 은 없는 표만 만들고 **이미 있는 표는 고치지 않는다.** 칸을 하나 더할 때마다
    DB 파일을 지우면 적어 둔 이슈·메모가 함께 사라지므로, 여기서 칸만 더한다.
    더하는 칸은 널을 받는 칸이다 — 기존 줄에는 빈 값이 들어간다.

    **사내망 고정본(`ROADMAP.md` P5)에서는 정식 마이그레이션으로 바꾼다.** 여기 것은
    작업본을 이어 쓰기 위한 수단이지 이력을 남기는 도구가 아니다.
    """
    if engine.dialect.name != "sqlite":
        return []
    added: list[str] = []
    insp = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                kind = col.type.compile(engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {kind}'))
                added.append(f"{table.name}.{col.name}")
    return added


@st.cache_resource
def get_engine() -> Engine:
    """엔진 하나를 만들고 표를 없으면 만든다. 프로세스당 한 번만 돈다."""
    url = secrets.section("db").get("url") or db_url()
    if url.startswith("sqlite"):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    add_new_columns(engine)
    return engine


@contextmanager
def session() -> Iterator[Session]:
    """세션 하나. 블록을 벗어나면 닫힌다.

        with session() as s:
            ...
    """
    with Session(get_engine()) as s:
        yield s
