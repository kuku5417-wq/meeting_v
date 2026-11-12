"""토큰 밖 색과 이모지 찾기.

사용: python -X utf8 .claude/tools/design_check.py views modules app.py
찾으면 파일:줄과 내용을 보여주고 종료 코드 1. 없으면 0.
tokens.css, .streamlit/config.toml, docs/_시안 은 검사하지 않는다 (색을 정의하는 곳).
"""

import re
import sys
from pathlib import Path

EXTS = {".py", ".css", ".js", ".html"}
SKIP_PARTS = {"_시안", ".venv", "__pycache__", ".git"}
SKIP_NAMES = {"tokens.css", "config.toml", "design_check.py"}

EMOJI = re.compile("[\U0001f000-\U0001faff☀-➿⬀-⯿️]")
COLOR = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b|\b(?:rgba?|hsla?)\(")


def files(args: list[str]):
    for a in args:
        p = Path(a)
        cands = [p] if p.is_file() else sorted(p.rglob("*")) if p.is_dir() else []
        for f in cands:
            if f.suffix in EXTS and f.name not in SKIP_NAMES and not SKIP_PARTS & set(f.parts):
                yield f


def scan(path: Path) -> list[str]:
    hits = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for no, line in enumerate(text.splitlines(), 1):
        code = line.lstrip()
        if EMOJI.search(line):
            hits.append(f"{path}:{no}: 이모지/기호 문자 -> 아이콘으로: {code[:80]}")
        if path.suffix == ".py" and code.startswith("#"):
            continue
        if COLOR.search(line):
            hits.append(f"{path}:{no}: 토큰 밖 색 -> var(--토큰): {code[:80]}")
    return hits


def main() -> int:
    args = sys.argv[1:] or ["."]
    hits = [h for f in files(args) for h in scan(f)]
    for h in hits:
        print(h)
    print(f"[design_check] {len(hits)}건")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
