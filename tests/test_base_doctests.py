"""독스트링 안의 예제가 실제로 그 값을 내는지 본다.

규칙이 까다로운 함수들은 설명 대신 **예제**로 적어 두었다 — `extract.locate`(근거 구간 찾기),
`extract.find_date`(메모에서 발생일 읽기), `sn_util.ensure_sn`(호선번호 정규화).
그 예제가 문서로만 남고 틀어지면 「근거 없는 AI 값은 표시하지 않는다」(`CLAUDE.md` §6-3)
같은 규칙이 조용히 깨진다. 그래서 예제를 **테스트로 돌린다.**

여기 적는 모듈은 **예제가 실제로 있는 것만**이다. 예제가 없는 모듈을 적으면
`doctest` 가 0개를 돌리고 그냥 통과해 — 아무것도 지키지 않는 테스트가 된다.
`issues`·`milestone` 의 업무 규칙은 예제가 아니라 `test-writer` 가 쓰는 슬라이스 테스트로 지킨다.
"""
from __future__ import annotations

import doctest
import importlib

import pytest

# 모듈 → 적어도 이만큼의 예제가 있어야 한다. 예제를 지우면 이 테스트가 먼저 알려 준다.
MODULES = {
    "modules.extract": 10,
    "modules.sn_util": 2,
    "modules.meetings": 2,  # shift_week 예제 2개 — 해를 넘는 ISO 주차
}


@pytest.mark.parametrize("name", list(MODULES))
def test_독스트링_예제가_맞는다(name: str) -> None:
    module = importlib.import_module(name)
    result = doctest.testmod(module, verbose=False, report=True)
    assert result.failed == 0, f"{name}: 예제 {result.failed}개가 적힌 값과 다르다"
    assert result.attempted >= MODULES[name], (
        f"{name}: 예제가 {result.attempted}개뿐이다 — {MODULES[name]}개는 있어야 한다. "
        "예제를 지웠다면 그 규칙을 지킬 테스트를 대신 써야 한다"
    )
