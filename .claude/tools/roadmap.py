"""ROADMAP.md 진행율 관리.

사용법
  python roadmap.py update [ROADMAP.md 경로]   진행율 표를 체크박스 기준으로 다시 계산해 파일에 반영
  python roadmap.py brief                      세션 시작 훅: 진행율·현재 단계·다음 할 일을 출력 (Claude 맥락에 들어감)
  python roadmap.py check                      종료 훅: 파일이 바뀌었는데 ROADMAP.md가 그대로면
                                               한 번 막고 갱신을 요청

ROADMAP.md 형식
  ### P1. 단계 이름           단계 제목
  - [x] 작업                  완료
  - [ ] 작업                  남음
  - [~] 작업                  진행 중 (남음으로 계산)
  - [!] 작업                  막힘 (남음으로 계산)
  - [-] 작업                  취소 (계산에서 제외)
  <!-- progress:start --> ... <!-- progress:end -->   이 사이를 스크립트가 다시 쓴다
  ## 다음 할 일                이 섹션의 내용을 세션 시작 때 보여준다
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROADMAP_NAME = "ROADMAP.md"
START, END = "<!-- progress:start -->", "<!-- progress:end -->"
PHASE_RE = re.compile(r"^###\s+(P\d+)\.\s*(.+?)\s*$")
TASK_RE = re.compile(r"^\s*-\s\[(.)\]\s+(.+)$")
BAR_WIDTH = 10
NEXT_HEADING = "## 다음 할 일"
IGNORED_FOR_CHECK = {ROADMAP_NAME, "workinglog.md"}
PATH_ARG_INDEX = 2


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())


def parse(text: str) -> list[dict]:
    phases, current = [], None
    for line in text.splitlines():
        m = PHASE_RE.match(line)
        if m:
            current = {"id": m.group(1), "name": m.group(2), "done": 0, "total": 0, "open": []}
            phases.append(current)
            continue
        t = TASK_RE.match(line)
        if t and current is not None:
            mark, title = t.group(1), t.group(2).strip()
            if mark == "-":
                continue
            current["total"] += 1
            if mark.lower() == "x":
                current["done"] += 1
            else:
                current["open"].append(title)
    return phases


def pct(done: int, total: int) -> int:
    return round(done * 100 / total) if total else 0


def bar(p: int) -> str:
    filled = round(p * BAR_WIDTH / 100)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def summary(phases: list[dict]) -> tuple[int, str]:
    done = sum(p["done"] for p in phases)
    total = sum(p["total"] for p in phases)
    overall = pct(done, total)
    current = next((p for p in phases if p["done"] < p["total"]), None)
    rows = [
        f"**전체 진행율 {overall}%** ({done}/{total}) {bar(overall)}",
        f"현재 단계: {current['id']}. {current['name']}" if current else "현재 단계: 모든 단계 완료",
        "",
        "| 단계 | 진행 | 진행율 | 막대 |",
        "|---|---|---|---|",
    ]
    for p in phases:
        pp = pct(p["done"], p["total"])
        rows.append(f"| {p['id']}. {p['name']} | {p['done']}/{p['total']} | {pp}% | {bar(pp)} |")
    return overall, "\n".join(rows)


def update(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"{path.name}: {START} / {END} 표시가 없어 갱신하지 못함", file=sys.stderr)
        return 1
    overall, table = summary(parse(text))
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    path.write_text(f"{head}{START}\n{table}\n{END}{tail}", encoding="utf-8")
    print(f"{path.name} 갱신: 전체 {overall}%")
    return 0


def next_section(text: str) -> str:
    if NEXT_HEADING not in text:
        return ""
    body = text.split(NEXT_HEADING, 1)[1]
    body = re.split(r"\n## ", body, maxsplit=1)[0]
    return body.strip()


def brief() -> int:
    path = project_dir() / ROADMAP_NAME
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    phases = parse(text)
    overall, _ = summary(phases)
    current = next((p for p in phases if p["done"] < p["total"]), None)
    lines = [f"[ROADMAP] {path.parent.name} 전체 진행율 {overall}%"]
    if current:
        lines.append(f"현재 단계: {current['id']}. {current['name']} ({current['done']}/{current['total']})")
    nxt = next_section(text)
    if nxt:
        lines += ["다음 할 일:", nxt]
    elif current:
        lines += ["다음 할 일 (미완료 작업 앞 3개):"] + [f"- {t}" for t in current["open"][:3]]
    branch = git_out(["git", "branch", "--show-current"])
    changed = changed_files()
    if branch:
        listed = f" ({', '.join(changed[:5])})" if changed else ""
        lines.append(f"브랜치: {branch} / 커밋 안 한 변경 {len(changed)}개{listed}")
    lines.append("작업을 마치면 ROADMAP.md의 체크박스와 '다음 할 일'을 고치고 roadmap.py update로 진행율을 갱신한다.")
    print("\n".join(lines))
    return 0


def git_out(args: list[str]) -> str:
    try:
        return subprocess.run(args, cwd=project_dir(), capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def changed_files() -> list[str]:
    out = git_out(["git", "status", "--porcelain"])
    return [line[3:].strip().strip('"') for line in out.splitlines() if line.strip()]


def check() -> int:
    data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    if data.get("stop_hook_active"):
        return 0  # 이미 한 번 요청했으면 다시 막지 않는다 (무한 반복 방지)
    if not (project_dir() / ROADMAP_NAME).exists():
        return 0
    changed = changed_files()
    names = {Path(f).name for f in changed}
    work = [f for f in changed if Path(f).name not in IGNORED_FOR_CHECK]
    if work and ROADMAP_NAME not in names:
        print(
            "작업 파일이 바뀌었는데 ROADMAP.md가 갱신되지 않았다. "
            "완료한 작업을 [x]로 바꾸고 '다음 할 일'을 고친 뒤 "
            "python .claude/tools/roadmap.py update 로 진행율을 갱신하라. "
            "로드맵에 해당하는 작업이 아니면 그 이유를 한 줄로 말하고 끝내도 된다.",
            file=sys.stderr,
        )
        return 2
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # Windows 기본 인코딩(cp949)에서 깨지지 않게
    cmd = sys.argv[1] if len(sys.argv) > 1 else "brief"
    if cmd == "update":
        path = Path(sys.argv[PATH_ARG_INDEX]) if len(sys.argv) > PATH_ARG_INDEX else project_dir() / ROADMAP_NAME
        return update(path)
    if cmd == "brief":
        return brief()
    if cmd == "check":
        return check()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
