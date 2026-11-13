"""모든 모듈·화면이 임포트되는지 본다.

슬라이스 테스트가 아니라 **바탕 테스트**다. 문법 오류·순환 참조·오타 난 이름은
화면을 띄워 봐야 알 수 있었는데(Streamlit 은 임포트한 모듈을 다시 읽지 않아 더 늦게 드러난다),
여기서 먼저 걸린다.

화면(`views/`)은 임포트만 한다. `render()` 를 부르면 Streamlit 실행 맥락이 필요하다.
"""
from __future__ import annotations

import importlib

import pytest

MODULES = [
    "config.paths",
    "config.settings",
    "modules.models",
    "modules.db",
    "modules.seed",
    "modules.sn_util",
    "modules.issues",
    "modules.extract",
    "modules.milestone",
    "modules.llm_client",
    "views.theme",
    "views.ui",
    "views.settings",
    "views.ledger",
    "views.inbox",
    "app",
]


@pytest.mark.parametrize("name", MODULES)
def test_임포트된다(name: str) -> None:
    importlib.import_module(name)


def test_화면마다_render_가_있다() -> None:
    """`app.py` 의 화면 분기가 부르는 것은 각 화면의 `render()` 하나다."""
    for name in ("views.settings", "views.ledger", "views.inbox"):
        module = importlib.import_module(name)
        assert callable(module.render), f"{name}.render 가 없다"
