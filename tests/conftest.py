"""공용 픽스처 — 앱 DB(`data/meeting.db`)를 건드리지 않는다.

`modules.db.session()` 은 `modules.db.get_engine()` 을 부른다. 그 이름을 `monkeypatch` 로
`tmp_path` 안의 SQLite 엔진으로 바꿔 끼운다 — 운영 코드는 그대로고, 테스트마다 새 DB 다.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from modules import db
from modules import models as m


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    m.Base.metadata.create_all(engine)
    monkeypatch.setattr(db, "get_engine", lambda: engine)
    with Session(engine) as s:
        s.add_all([
            m.Department(id="D1", code="D1", name="기획부", order_no=1),
            m.Department(id="D2", code="D2", name="전장부", order_no=2),
        ])
        s.commit()
    yield engine
    engine.dispose()
