"""LLM 점검 — S3 이후용 뼈대.

지금은 **설정이 있는지만** 본다. 설정이 없으면 SKIP 으로 끝낸다(종료 코드 0) —
사외망 작업본에서는 없는 것이 정상이다.

의도적으로 하지 않는 것
- 프록시·SSL 우회 설정 (code-gen.md §3 이 금지)
- 외부 API(OpenAI·Upstage 등) 호출. 사내 LLM 창구는 `modules/llm_client.py` 한 군데뿐이다
- 실제 호출. S3 에서 `modules.llm_client` 가 생기면 아래 "호출 확인" 절을 채운다

사용법:  python -X utf8 diagnostics/check_llm.py
종료 코드 0 = 통과 또는 SKIP, 1 = 설정이 있는데 창구가 깨짐.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 비밀값은 config.settings 창구만 쓴다. st.secrets 를 직접 읽지 않는다.
NEEDED = ("llm_base_url", "llm_model")


def load_secrets() -> tuple[object | None, str]:
    try:
        from config.settings import secrets
    except ModuleNotFoundError as e:
        return None, f"config.settings 아직 없음 ({e.name}) — S0 에서 만든다"
    except Exception as e:
        return None, f"config.settings import 실패: {type(e).__name__}: {e}"
    return secrets, ""


def main() -> int:
    secrets, msg = load_secrets()
    if secrets is None:
        print(f"[SKIP] {msg}")
        print("사외망 작업본에서는 사내 LLM 설정이 없는 것이 정상이다.")
        return 0

    get = getattr(secrets, "get", None)
    if get is None:
        print("[FAIL] config.settings.secrets 에 get() 이 없다 — 창구 모양을 확인하라")
        return 1

    found = {k: bool(get(k)) for k in NEEDED}
    if not any(found.values()):
        print("[SKIP] 사내 LLM 설정 없음 (" + ", ".join(NEEDED) + " 비어 있음)")
        print("S3 에서 .streamlit/secrets.toml 에 채운다. 값은 로그에 찍지 않는다.")
        return 0

    for k, ok in found.items():
        print(f"  {'[OK]  ' if ok else '[--]  '} {k} {'설정됨' if ok else '없음'}")
    if not all(found.values()):
        print("\n일부만 설정돼 있다 — 빠진 값을 채워야 호출이 된다.")
        return 1

    # 호출 확인 — S3 에서 modules.llm_client 가 생기면 여기를 채운다.
    try:
        import modules.llm_client  # noqa: F401
    except ModuleNotFoundError:
        print("\n[SKIP] modules.llm_client 아직 없음 — S3 에서 만든다")
        return 0

    print("\n[OK] 설정과 창구가 둘 다 있다 (실제 호출은 아직 확인하지 않음)")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
