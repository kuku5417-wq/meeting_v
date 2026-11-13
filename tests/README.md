# tests/ — 테스트는 `test-writer` 가 쓴다

```bash
uv run python -X utf8 -m pytest
```

**`-X utf8` 을 빼지 않는다.** 시험 이름을 한글로 적으므로, 빼면 Windows 콘솔(cp949)에서
실패 줄이 `test_����Ʈ��_…` 로 나와 **무엇이 실패했는지 읽을 수 없다.**
`tests/conftest.py` 로 출력 인코딩을 바꿔 보려 했지만 pytest 가 더 먼저 출력을 잡아 소용없었다
(2026-11-13에 확인). `CLAUDE.md` §5 의 다른 명령들과 같은 이유·같은 방식이다.

## 누가 쓰는가

슬라이스를 끝낸 뒤 **`test-writer` 에이전트**가 그 슬라이스의 테스트를 여기에 쓴다
(`.claude/agents/test-writer.md`). `code-gen` 은 테스트를 직접 쓰지 않고,
`code-reviewer` 가 `uv run pytest` 를 돌려 통과 여부를 본다. 이 한 바퀴는 `/slice` 가 묶는다.

## 이름

`tests/test_<슬라이스>_<무엇>.py` — 예: `test_s5_issues.py`.
아래 두 개는 슬라이스에 매이지 않은 **바탕 테스트**라 `test_base_*` 로 둔다.

| 파일 | 무엇을 지키는가 |
|---|---|
| `test_base_imports.py` | 모든 모듈·화면이 **임포트된다.** 문법 오류·순환 참조·오타 난 이름이 여기서 걸린다 |
| `test_base_doctests.py` | 독스트링 안의 예제가 **실제로 그 값을 낸다.** `locate`·`find_date`·`ensure_sn` 처럼 규칙이 까다로운 함수들이다 |

## 무엇을 쓰지 않는가

- **실제 회사 메모·사진을 넣지 않는다** (`CLAUDE.md` §6-9). 샘플·가상 데이터만 쓴다.
- 사내망 요소(`pymysql`·`pyodbc`·NAS 경로·Outlook)를 부르지 않는다. 여기는 사외망 작업본이다.
- 앱 DB(`data/meeting.db`)를 건드리지 않는다. DB 가 필요한 테스트는 임시 파일에 따로 만든다.
