"""LLM 창구 — 전환 지점은 `_chat()` 하나다.

갈래가 **둘**이다. `llm_provider` 설정이 가른다.

| 갈래 | 언제 | 무엇 |
|---|---|---|
| `inhouse` (비우면 이것) | **사내망 고정본**(P5) | 사내 게이트웨이. `_chat()` 을 채운다 — `SPEC.md` §11 |
| `claude` | **공개 데모에서만** (2026-11-13) | Anthropic API. `docs/데모_배포.md` |

> **`claude` 갈래는 규칙의 예외다.** `CLAUDE.md` §3·§6-9 는 외부 API 호출을 금지한다
> (「보고 내용은 사내 LLM 으로만」). 발표용 공개 데모에서 **가상 데이터만** 다루는 자리에 한해
> 열어 둔 것이고, **사내망 고정본은 `inhouse` 그대로다.** 두 갈래가 이 파일 한 군데에서만 갈리므로
> 사내망으로 갈 때 지울 것도 여기뿐이다.
> 화면(`views/inbox.py`)은 `claude` 로 돌 때 **「실제 회사 메모를 넣지 마십시오」** 를 띄운다.

**설정은 `config.settings.secrets` 를 거친다.** `st.secrets` 를 직접 읽지 않고
**키 값을 로그·화면에 찍지 않는다** — 있는지 없는지만 본다.

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
INHOUSE_NEEDED = ("llm_base_url", "llm_model")
CLAUDE_NEEDED = ("llm_api_key",)
NEEDED = INHOUSE_NEEDED  # 옛 이름 — 사내 갈래를 가리킨다

PROVIDER_KEY = "llm_provider"
INHOUSE, CLAUDE = "inhouse", "claude"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-5-5"

DEFAULT_SYSTEM = "너는 조선소 커미셔닝 현장의 기록을 정리한다. JSON 형식으로만 답한다."

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_OPEN = re.compile(r"^```(?:json)?\s*")
_FENCE_CLOSE = re.compile(r"\s*```$")
_BRACES = re.compile(r"\{.*\}", re.DOTALL)


class LLMNotConfigured(RuntimeError):
    """LLM 설정이 없다. 설정을 채우지 않은 상태에서는 **정상**이다 — 화면은 「직접 적기」로 간다."""


class LLMFailed(RuntimeError):
    """설정은 있는데 **부르다가 실패**했다 — 키가 틀렸거나 연결이 안 되거나 한도에 걸렸다.

    「설정이 없다」와 갈라 둔다. 앞엣것은 정상 상태이고 이것은 **사람이 고쳐야 하는 것**이다.
    """


def provider() -> str:
    """지금 쓰는 갈래. 비어 있으면 **사내**다 — 기본값이 바뀌지 않게 한다."""
    name = str(secrets.get(PROVIDER_KEY, "") or "").strip().lower()
    return CLAUDE if name == CLAUDE else INHOUSE


def is_configured() -> bool:
    """설정이 채워져 있는가. **값 자체는 보지 않는다** — 있는지만 본다."""
    needed = CLAUDE_NEEDED if provider() == CLAUDE else INHOUSE_NEEDED
    return all(secrets.has(k) for k in needed)


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
    """LLM 에 묻고 JSON 으로 받는다. 설정이 없으면 `LLMNotConfigured`.

    부르는 쪽(S6 추출·S9 지식)은 이 함수만 쓴다. 게이트웨이가 바뀌어도 여기는 그대로다.
    """
    return parse_json(_chat(system, prompt, temperature))


def _chat(system: str, user_prompt: str, temperature: float) -> str:
    """전환 지점 — 갈래가 여기서 갈린다. 부르는 쪽은 이 함수를 모른다.

    `inhouse` 는 사내망 고정본에서 채운다 (`SPEC.md` §11).
    `claude` 는 **공개 데모 전용**이다 (위 머리글).
    """
    which = provider()
    if not is_configured():
        needed = CLAUDE_NEEDED if which == CLAUDE else INHOUSE_NEEDED
        raise LLMNotConfigured(
            f"LLM 설정이 없다 ({which}: " + ", ".join(needed) + "). "
            "설정이 없는 것은 **정상**이다 — 화면은 「직접 적기」로 간다. "
            ".streamlit/secrets.toml 을 채우면 돈다."
        )
    if which == CLAUDE:
        return _chat_claude(system, user_prompt, temperature)
    raise NotImplementedError(
        "사내망 고정본에서 구현한다 — SPEC.md §11 참조. "
        "OpenAI 호환 /chat/completions, Bearer 인증, max_tokens 미전송."
    )


def _chat_claude(system: str, user_prompt: str, temperature: float) -> str:
    """Anthropic API — **공개 데모 전용 갈래**. 사내망에서는 쓰지 않는다.

    `anthropic` 은 **선택 의존성**이다. 없으면 설치하라고 말해 준다 —
    없는 채로 앱이 죽지 않게 한다 (`code-gen.md` §4⑦ 강등 경로와 같은 방식).
    """
    try:
        import anthropic
    except ImportError as e:  # 선택 의존성
        raise LLMNotConfigured(
            "`anthropic` 이 깔려 있지 않다. `uv sync` 또는 "
            "`python -m pip install -r requirements.txt` 로 깐다."
        ) from e

    # `temperature` 는 **보내지 않는다** — 이 SDK 판의 `messages.create()` 가 받지 않는다
    # (대신 `thinking`·`output_config` 가 있다). 사내 게이트웨이(OpenAI 호환) 쪽만 쓰는 인자다.
    # 答을 일정하게 만드는 것은 프롬프트가 맡는다 — `extract.PROMPT` 가 JSON 만 내라고 못박는다.
    client = anthropic.Anthropic(api_key=secrets.get("llm_api_key"))
    try:
        answer = client.messages.create(
            model=str(secrets.get("llm_model") or DEFAULT_CLAUDE_MODEL),
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        # 키가 틀리거나 연결이 안 되거나 한도에 걸린 경우. **키 값은 적지 않는다.**
        raise LLMFailed(f"Claude 를 부르지 못했다 — {type(e).__name__}") from e
    # 글 조각만 잇는다. 생각 블록이 섞여 와도 `parse_json()` 이 벗긴다.
    return "".join(b.text for b in answer.content if getattr(b, "type", "") == "text")
