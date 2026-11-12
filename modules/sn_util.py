"""호선번호 정규화 — `ensure_sn` 하나.

`2511` · `S2511` · `sn2511` · 앞뒤 공백 붙은 ` SN2511 ` → 모두 `SN2511`.

**이 함수는 한 군데만 둔다** (`code-gen.md` §4③). 별칭 사전(F3)이 여기 걸려 있어서,
같은 호선을 두 가지로 적으면 별칭이 다른 호선을 가리킨다.

**사내망 전환 주의** — `data_manager/sn_util.py` 의 `ensure_sn` 과 **같은 규칙이어야 한다.**
그쪽이 `pjtlist.SHIPNUM` · `milestone.project` 를 이 형태로 수렴시켜 내보내므로,
규칙이 어긋나면 호선이 이어지지 않는다. 그쪽은 pandas 를 쓰고 이쪽은 표준 라이브러리만
쓴다는 차이뿐이다 (진단 스크립트가 pandas 없이도 돌아야 한다).

차이가 하나 있다: 그쪽은 `float('nan')` 을 pandas 로 걸러내고, 이쪽은 문자열로 바꾼 뒤
`"NAN"` 으로 걸러낸다. 결과는 같다.
"""
from __future__ import annotations

_EMPTY = ("", "NAN", "NAT", "NONE")


def ensure_sn(val: object) -> str:
    """호선번호를 `SN` + 숫자 형태로 통일한다. 빈값은 `""`.

    `SN` 또는 `S`+숫자 또는 순수 숫자만 바꾸고, 그 밖의 형태는 원본을 그대로 둔다
    (예상치 못한 값을 조용히 망가뜨리지 않기 위해).

    >>> ensure_sn("2511"), ensure_sn("S2511"), ensure_sn(" sn2511 ")
    ('SN2511', 'SN2511', 'SN2511')
    >>> ensure_sn(""), ensure_sn(None), ensure_sn("미정")
    ('', '', '미정')
    """
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s in _EMPTY:
        return ""
    if s.startswith("SN"):
        return s
    if s.startswith("S") and s[1:].isdigit():
        return "SN" + s[1:]
    if s.isdigit():
        return "SN" + s
    return s
