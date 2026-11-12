"""비밀값 창구 — 다른 파일은 `st.secrets` 를 직접 읽지 않고 여기만 쓴다.

    from config.settings import secrets
    url = secrets.get("llm_base_url")

값은 `.streamlit/secrets.toml` 에 둔다 (`.streamlit/secrets.toml.template` 을 복사).
그 파일은 `.gitignore` 에 있어 커밋되지 않는다.

**값을 로그·화면에 찍지 않는다.** 있는지 없는지만 보여 준다 (`has`).
사외망 작업본에서는 비어 있는 것이 정상이므로, 없을 때 터지지 않고 `default` 를 준다.
"""
from __future__ import annotations

from typing import Any


class _Secrets:
    """`.streamlit/secrets.toml` 읽기 전용 창구."""

    def get(self, key: str, default: Any = None) -> Any:
        """값 하나. 없거나 Streamlit 런타임 밖이면 `default`."""
        try:
            import streamlit as st
        except ImportError:
            return default  # 진단 스크립트처럼 streamlit 없이 돌 때
        try:
            # secrets.toml 이 없으면 **읽는 시점에** 예외가 난다 (속성 접근은 지연 평가라
            # 거기서는 안 터진다). 사외망에서는 없는 것이 정상이므로 default 를 준다.
            # 예외 이름이 Streamlit 판마다 달라 넓게 받는다.
            value = st.secrets.get(key, default)
        except Exception:
            return default
        return default if value == "" else value

    def has(self, key: str) -> bool:
        """값이 채워져 있는가. 값 자체는 돌려주지 않는다."""
        return bool(self.get(key))

    def section(self, name: str) -> dict[str, Any]:
        """`[db]` 처럼 묶음으로 둔 설정. 없으면 빈 사전."""
        value = self.get(name)
        return dict(value) if value else {}


secrets = _Secrets()
