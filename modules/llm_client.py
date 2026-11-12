"""사내 LLM 창구 — 전환 지점은 `_chat()` 하나다.

**이 저장소는 사외망 작업본이다.** 실제 호출 코드는 여기 넣지 않는다
(`code-gen.md` §3 — SOLA·프록시·외부 API 금지). 사내망 고정본(P5)에서
`_chat()` **한 함수만** 채우면 나머지는 그대로 돈다. 게이트웨이가 어떤 모양인지는
`SPEC.md` §11 에 적어 두었다.

**설정은 `config.settings.secrets` 를 거친다.** `st.secrets` 를 직접 읽지 않고,
값을 로그·화면에 찍지 않는다 — 있는지 없는지만 본다.

여기서 값이 있는 부분은 `parse_json()` 이다. 게이트웨이가 돌려주는 글에는
`<think>…</think>` 와 ``` 펜스가 섞여 오므로 벗겨내야 `json.loads` 가 통한다.
이 함수는 망과 무관한 순수 함수라 사외망에서도 시험할 수 있다.
"""
from __future__ import annotations

import json
import re
from typing import Any

from config.settings import secrets

# 설정 키 — `.streamlit/secrets.toml` (template 참조). diagnostics/check_llm.py 와 같아야 한다.
NEEDED = ("llm_base_url", "llm_model")

DEFAULT_SYSTEM = "너는 조선소 커미셔닝 현장의 기록을 정리한다. JSON 형식으로만 답한다."

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_OPEN = re.compile(r"^```(?:json)?\s*")
_FENCE_CLOSE = re.compile(r"\s*```$")
_BRACES = re.compile(r"\{.*\}", re.DOTALL)


class LLMNotConfigured(RuntimeError):
    """사내 LLM 설정이 없다. 사외망에서는 정상 상태다."""


def is_configured() -> bool:
    """사내 LLM 설정이 채워져 있는가. 값 자체는 보지 않는다."""
    return all(secrets.has(k) for k in NEEDED)


def parse_json(content: str) -> dict[str, Any] | None:
    """게이트웨이 응답에서 JSON 을 꺼낸다. 못 꺼내면 `None`.

    `<think>` 블록과 ``` 펜스를 벗기고, 그래도 안 되면 처음 나오는 `{...}` 를 집는다.

    >>> parse_json('```json\\n{"a": 1}\\n```')
    {'a': 1}
    >>> parse_json('<think>음…</think>{"b": 2}')
    {'b': 2}
    >>> parse_json('앞말 {"c": 3} 뒷말')
    {'c': 3}
    >>> parse_json('JSON 아님') is None
    True
    """
    text = _THINK.sub("", content or "").strip()
    text = _FENCE_OPEN.sub("", text)
    text = _FENCE_CLOSE.sub("", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _BRACES.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


def ask_json(prompt: str, system: str = DEFAULT_SYSTEM, temperature: float = 0.0) -> dict[str, Any] | None:
    """사내 LLM 에 묻고 JSON 으로 받는다. 설정이 없으면 `LLMNotConfigured`.

    부르는 쪽(S6 추출·S9 지식)은 이 함수만 쓴다. 게이트웨이가 바뀌어도 여기는 그대로다.
    """
    return parse_json(_chat(system, prompt, temperature))


def _chat(system: str, user_prompt: str, temperature: float) -> str:
    """★ 사내망 전환 지점 — 이 함수 하나만 채운다. 모양은 `SPEC.md` §11.

    사외망 작업본에는 호출 코드를 두지 않는다.
    """
    if not is_configured():
        raise LLMNotConfigured(
            "사내 LLM 설정이 없다 (" + ", ".join(NEEDED) + "). "
            "사외망에서는 정상이다. 사내망에서는 .streamlit/secrets.toml 을 채운다."
        )
    raise NotImplementedError(
        "사내망 고정본에서 구현한다 — SPEC.md §11 참조. "
        "OpenAI 호환 /chat/completions, Bearer 인증, max_tokens 미전송."
    )
