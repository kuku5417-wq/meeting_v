"""경로 창구 — 경로 문자열을 다른 파일에 직접 쓰지 않는다.

`C:\\...` 나 `./data/` 를 코드에 박으면 사내망 전환 때 전부 찾아 고쳐야 한다.
여기만 고치면 된다. 사내망에서 바뀌는 곳은 `DB_PATH` 와 `OUT_DIR` 둘이다.
"""
from __future__ import annotations

from pathlib import Path

# 이 파일은 <저장소>/config/paths.py 다.
ROOT = Path(__file__).resolve().parent.parent

# 문서·명세
DOCS_DIR = ROOT / "docs"
MOCKUPS_DIR = DOCS_DIR / "_시안" / "design" / "mockups"

# 데이터
DATA_DIR = ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
MASTERS_DIR = SAMPLES_DIR / "masters"  # 기준정보 CSV 15종. 실데이터 전환 시 CSV만 교체
# 사내 시스템 미러(milestone·pjtlist)를 사외망에서 대신하는 샘플 — requirements §1-4.
# 사내망에서는 data_manager 의 parquet 을 그대로 읽는다. **전환 지점이다.**
MIRROR_DIR = SAMPLES_DIR / "mirror"
DB_PATH = DATA_DIR / "meeting.db"  # .gitignore 로 커밋되지 않는다

# 사진 원본 (CLAUDE.md §6-1 — 원본은 고치지 않는다. 마킹은 좌표 JSON 으로 따로 둔다)
PHOTOS_DIR = DATA_DIR / "photos"

# 산출물 (원본을 고치지 않고 결과는 여기에 쓴다 — CLAUDE.md §6-1)
OUT_DIR = ROOT / "out"

# 점검
DIAGNOSTICS_DIR = ROOT / "diagnostics"


def db_url() -> str:
    """SQLAlchemy 접속 문자열. 사내망에서 바뀌는 지점."""
    return f"sqlite:///{DB_PATH.as_posix()}"


def ensure_out() -> Path:
    """산출물 폴더를 만들고 돌려준다."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUT_DIR


def master_csv(name: str) -> Path:
    """기준정보 CSV 한 장의 경로. 예: master_csv("hull") -> .../masters/hull.csv"""
    return MASTERS_DIR / f"{name}.csv"


def photo_path(sha256: str, suffix: str) -> Path:
    """사진 원본의 자리. `photos/<sha 앞 2자>/<sha>.<확장자>` (requirements §1-2-2).

    같은 사진을 두 번 올려도 같은 자리에 떨어진다 — 해시가 이름이기 때문이다.
    """
    return PHOTOS_DIR / sha256[:2] / f"{sha256}{suffix if suffix.startswith('.') else '.' + suffix}"
