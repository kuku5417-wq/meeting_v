"""라이브러리 점검 — 필수가 깔렸는지, 선택이 없으면 어디로 강등되는지 본다.

선택 라이브러리는 사외망에서 설치가 막힐 수 있다. 없는 것이 정상이고,
`code-gen.md` §4⑦ 의 강등 경로를 쓰면 된다. 그래서 선택은 오류로 세지 않는다.

사용법:  python -X utf8 diagnostics/check_libs.py
종료 코드 0 = 필수 전부 있음, 1 = 필수 빠짐.
"""
from __future__ import annotations

import importlib
import importlib.metadata as md
import sys

REQUIRED = [
    ("streamlit", "앱"),
    ("sqlalchemy", "DB"),
    ("pandas", "표 다루기"),
]

OPTIONAL = [
    ("st_aggrid", "표 고급 기능", "없으면 st.data_editor 로 강등 (Community 범위만 쓴다)"),
    ("streamlit_drawable_canvas", "사진 마킹", "없으면 st.image + 좌표 수동 입력으로 강등"),
    ("pptx", "PPTX 발행", "없으면 S8 발행이 막힌다 — python-pptx 설치 필요"),
]

DIST = {"st_aggrid": "streamlit-aggrid", "pptx": "python-pptx",
        "streamlit_drawable_canvas": "streamlit-drawable-canvas"}


def version(mod: str) -> str:
    try:
        return md.version(DIST.get(mod, mod))
    except md.PackageNotFoundError:
        return "?"


def probe(mod: str) -> str:
    try:
        importlib.import_module(mod)
    except ImportError:
        return ""
    except Exception as e:  # import 중에 터지는 경우도 없는 것으로 보지 않는다
        return f"!{type(e).__name__}"
    return version(mod)


def main() -> int:
    print(f"python {sys.version.split()[0]}  ({sys.executable})")
    print()
    missing: list[str] = []

    print("필수")
    for mod, why in REQUIRED:
        got = probe(mod)
        if got and not got.startswith("!"):
            print(f"  [OK]   {mod:<28} {got:<10} {why}")
        elif got:
            print(f"  [FAIL] {mod:<28} {got:<10} {why} — import 중 예외")
            missing.append(mod)
        else:
            print(f"  [FAIL] {mod:<28} {'없음':<10} {why}")
            missing.append(mod)

    print()
    print("선택 (없어도 통과 — 강등 경로를 쓴다)")
    for mod, why, fallback in OPTIONAL:
        got = probe(mod)
        if got and not got.startswith("!"):
            print(f"  [OK]   {mod:<28} {got:<10} {why}")
        else:
            print(f"  [--]   {mod:<28} {'없음':<10} {why}")
            print(f"         → {fallback}")

    print()
    if missing:
        print(f"필수 {len(missing)}개 빠짐: {missing}")
        print("S0 에서 pyproject.toml 을 만들고 `uv sync` 로 깔면 된다.")
        return 1
    print("[OK] 필수 전부 있음")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
