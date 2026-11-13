# ROADMAP.md — meeting_v (커미셔닝팀 회의자료·지식화)

> 단계·진행율·다음 할 일의 **정본**. 무엇을 만드는지는 `requirements.md`, 기준정보 구조는 `SPEC.md`, 코드 규칙은 `.claude/agents/code-gen.md`.
> 이 문서는 계획서이자 진행 장부다. 세션이 끊겨도 이 파일만 읽으면 어디까지 됐고 다음에 무엇을 할지 알 수 있어야 한다.
> 진행율 표는 `python .claude/tools/roadmap.py update`가 체크박스를 세서 다시 쓴다. 손으로 고치지 않는다.

## 진행율
<!-- progress:start -->
**전체 진행율 60%** (25/42) ██████░░░░
현재 단계: P0. 정본 정리

| 단계 | 진행 | 진행율 | 막대 |
|---|---|---|---|
| P0. 정본 정리 | 11/12 | 92% | █████████░ |
| P1. 안전장치 (3일차 교육 적용) | 5/8 | 62% | ██████░░░░ |
| P2. 기반 | 5/5 | 100% | ██████████ |
| P3. 화면 | 4/8 | 50% | █████░░░░░ |
| P4. 검증 | 0/6 | 0% | ░░░░░░░░░░ |
| P5. 사내망 고정본 | 0/3 | 0% | ░░░░░░░░░░ |
<!-- progress:end -->

## 다음 할 일

1. **P3 S7 — 회의자료. `/slice S7` 로 돈다.** `views/meeting.py`·`modules/meetings.py` (F6~F10 F12 F13 F20).
   가장 큰 화면이고, **`/slice` 를 처음 쓰는 슬라이스**다 (code-gen → test-writer → spec-guard·code-reviewer·ui-reviewer).
   **표현은 `report_item`, 사실은 `block`** 경계가 F8의 전제다. 표는 아직 선언하지 않았다.
   먼저 정할 것 하나: `deck_slide`·`slide_object`(시안 유래)와 `report_item`(원본 유래) 중
   **어느 쪽이 "회의자료 한 장"의 정본인가** (`requirements.md` §2 A 아래 쪽지). 표를 선언하기 전에 정한다.
2. **P1 마무리** — 뚫어 보기 5가지를 직접 돌려 "뚫어 보기 기록" 표를 채운다. 언제든 할 수 있다.
3. **쌓인 [제안]** — `ui-reviewer` 가 남긴 것들(사이드바 개발 진단, 이슈 등록 폼 중복,
   원장이 목록과 일괄 정리를 두 벌 보여 주는 것, 상세가 목록에서 먼 것 등). 그 화면을 손댈 때 함께 한다.

> 2026-11-13 에 끝난 것: SD(디자인) 전부, `requirements.md` §2 결정 2건, 사건 당시 단계(§2-C).

## 갱신 규칙

1. 단계를 시작하기 전에 그 단계의 상세 칸(작업 전 확인 · 만들 파일 · 완료 판정)을 먼저 읽는다.
2. 완료 판정 명령을 **직접 돌려** 통과를 확인한다. 통과 못 하면 `[x]`로 바꾸지 않는다.
3. 단계가 끝나거나 **중간에 끊기면** "작업 실적 로그"에 한 줄 적고 "다음 할 일"을 고친다.
4. 범위·결정이 바뀌면 "추가·변경 기록"에 날짜와 근거를 남긴다. 계획 본문만 고치고 기록을 비워 두지 않는다.
5. 마지막에 `python .claude/tools/roadmap.py update`로 진행율을 갱신한다.

상태 기호: `[x]` 완료 / `[ ]` 대기 / `[~]` 진행 중 / `[!]` 막힘 / `[-]` 취소(사유). `[~]`·`[!]`는 남은 것으로 세고 `[-]`는 계산에서 뺀다.

## 지금 상태 (2026-11-13)

| | 항목 |
|---|---|
| **문서** | `SPEC.md`(호선 4층·`stage` 어휘·검증 7규칙·§9-A 이름 고정·§10 일정·§11 LLM), `requirements.md`(기준정보 15표·운영 16표·F1~F23 배정·§2 **열려 있는 결정 없음**), `CLAUDE.md`, `docs/디자인_규칙.md`, `docs/_시안/` |
| **코드** | `app.py`·`config/` 2, `modules/` 8종(`models`·`db`·`seed`·`sn_util`·`issues`·`extract`·`milestone`·`llm_client`), `views/` 5종(`settings`·`ledger`·`inbox`·`theme`·`ui`), `diagnostics/` 4종, `static/`(토큰·글꼴 서브셋), `data/samples/`(기준정보 CSV 15종 99행 + `mirror/`) |
| **장치** | `.gitignore`·권한 규칙·가드 훅(FAIL 0/26)·`roadmap.py`·`design_check.py`, `.claude/agents/` **6종**(`spec-writer`·`code-gen`·`test-writer`·`spec-guard`·`code-reviewer`·`ui-reviewer`), `.claude/skills/slice/` |
| **없다** | `views/meeting.py`·`knowledge.py`·`home.py`, `modules/meetings.py`·`knowledge.py`·`pptx_export.py` — S7 이후. **`tests/` 도 아직 없다**(P4). 선택 라이브러리 `st_aggrid`·`streamlit_drawable_canvas` 미설치(강등 경로를 쓴다) |
| **깃** | `main` = `origin/main` = `7989efa`. 2026-11-13 커밋 4개(`d059387` 컴포넌트 토큰 · `adf6d2a` 재점검 반려 5건 · `6b068be` 미결 A·B · `7989efa` 사건 당시 단계) |

## 흐름

```mermaid
flowchart LR
  P0[P0 정본 정리] --> P1[P1 안전장치] --> P2[P2 기반 S-1~S3] --> P3[P3 화면 S4~S10] --> P4[P4 검증] --> P5[P5 사내망 고정본]
```

## 단계

### P0. 정본 정리

- [x] 기준정보 명세 `SPEC.md` (호선 4층 구조, `stage` 5종, 검증 7규칙)
- [x] 기준정보 CSV 15종 99행 + `_check.py`
- [x] 화면 시안 v2 (`docs/_시안/` HTML·README 명세)
- [x] 에이전트 3종 (`spec-writer`·`code-gen`·`spec-guard`)
- [x] 저장소 커밋 — `.gitignore`·안전장치·`ROADMAP.md`를 `main`에 병합하고 `origin/main`에 push (`bdebcc9..1f83269`). 미push 상태였던 이전 3커밋(`6720745`·`f27d8e4`·`45e4f0f`)도 함께 올라갔다
- [x] `SPEC.md` §9 정해야 할 것 4건 확정 (2026-11-12) — 9-1 약호 `174km3 LNG` 꼴 / 9-2 적재량까지 유지 / 9-3 계약 순서 + 대책 반영은 호선 ID로 / 9-4 단계 4개 + 일정에서 계산(§10 선행). 결정 브리핑: https://claude.ai/artifact/AGSoCiE1p1GLDdY1jhPXsD
- [x] `SPEC.md` §10 호선 이벤트 일정 — 받는 표(`milestone` 하나)·칸 이름(헤더 그대로)·이벤트 17종·계산 규칙 전부 확정 (2026-11-12)
- [x] `requirements.md` §1-4에 호선 이벤트 표(`milestone`) 추가 — 기준정보 15종·운영 표 어느 쪽도 아닌 사내 미러라 자리를 따로 뒀다
- [x] `requirements.md` 미결 — 운영 표·F 배정을 채우고 범위 결정 4건을 닫았다. `spec-guard` 가 다시 연 2건(회의자료 표, `hull.stage` 재계산)도 **2026-11-13에 닫았다** — `meeting` 하나로, 볼 때마다 계산. §2 에 열려 있는 결정이 없어 **S7 이 열렸다**
- [x] 디자인 규칙 `docs/디자인_규칙.md` (정본 위치, 규칙 8개, 컴포넌트 토큰 10가지)
- [x] 디자인 정할 것 2건 확정 (2026-11-13) — **흰 사이드바**, 주 색 `--accent #0963c4`
- [ ] 시안 중 확정안(**v2m**, 회의자료 편집은 **v2e-studio**) 표시, 나머지는 `docs/_시안/보관/`으로

### P1. 안전장치 (3일차 교육 적용)

- [x] `.gitignore` 적용 — 비밀·데이터 제외, 샘플 CSV는 추적 유지
- [x] 권한 규칙 `.claude/settings.json` 적용 (allow·ask·deny 3층)
- [x] 가드 훅 적용 — `node .claude/hooks/guard-test.js` 26건 FAIL 0
- [x] 에이전트 출력 형식 보완 (쓰지 않을 때, 확인하지 못한 것, 판정)
- [x] 로드맵 훅 동작 확인 (세션 시작 요약, 종료 시 미갱신 알림)
- [ ] 뚫어 보기 5가지 기록 — 아래 "뚫어 보기 기록" 표를 채운다
- [ ] 에이전트 **6개** 확인 (`spec-writer`·`code-gen`·`test-writer`·`spec-guard`·`code-reviewer`·`ui-reviewer`) — 2026-11-13 묶음으로 `test-writer`·`code-reviewer` 가 들어왔다
- [ ] `/slice` 스킬로 한 바퀴 (반려 → 수정 → 통과 기록). 묶음은 "S0 한 바퀴"라고 적었지만 S0 는 이미 끝났으므로 **S7 에서 처음 쓴다**

### P2. 기반

- [x] S-1 문서·검증 기반 (`CLAUDE.md` + `diagnostics/` 4종) — 진단 4개 크래시 없이 끝남, `check_data` `EXIT=0`
- [x] S0 골격·설정 (Streamlit 앱이 뜬다) — `check_libs` `EXIT=0`, 앱이 8501에서 떠서 빈 홈이 보임. **앱 CSS 의 흰 사이드바 반영은 SD 에서 한다**
- [x] S1 모델 (기준정보 15표 선언) — `import` 통과, 선언 표 15개, `hull` 12칸, CSV 헤더와 모델 칸 전부 일치
- [x] S2 DB·시드 (15표 99행이 DB에 올라간다, `ensure_sn`) — `check_db` **EXIT=0**, 재실행해도 중복 적재되지 않음
- [x] S3 LLM (`modules/llm_client.py`) — 창구만. 호출은 사내망 전환 지점(`SPEC.md` §11)

### P3. 화면

- [x] S4 설정 화면 — 기준정보 15종 CRUD·재시드 (`views/settings.py`, `app.py` 화면 분기)
- [x] S5 이슈 원장 — F2 그리드·F3 지식 매핑·F4 주차별 진행·F5 1차 초안(사진 포함)·F21 일정 경보·F23 일괄 정리
- [x] S6 기록함 — F1. 메모 원본 보존, 근거 없는 AI 값은 코드가 버림, 사외망에서는 직접 적기로 강등
- [ ] S7 회의자료 — F6~F10 F12 F13 F20
- [ ] S8 발행·PPTX — F11
- [ ] S9 지식·챗봇 — F15
- [ ] S10 홈 — F19, **마지막** (앞 슬라이스가 다 있어야 숫자를 센다)
- [x] **SD 화면 디자인** — 흰 사이드바·토큰·의미 색(라이트 전용), 글꼴 서브셋, 컴포넌트 토큰(`views/ui.py`), 날짜 고르기까지 확정. `design_check` 0건. 남은 [제안]은 그 화면을 손댈 때 함께 본다 (아래 "디자인" 절)

### P4. 검증

- [~] 슬라이스마다 `/slice` 로 진행 — **`test-writer` 테스트 통과**, `spec-guard`·**`code-reviewer`** `판정: 통과`. 지금까지는 `spec-guard` 만 돌렸다(S1~S6 소급 1회, 2026-11-12 **반려 14건** → 12건 처리, 2건은 2026-11-13에 결정으로 닫음). **S7부터 `/slice` 로 한 바퀴씩 돈다**
- [ ] **S0~S6 에는 테스트가 없다** — `test-writer` 가 그때 없었고 `tests/` 자체가 없다. S7 을 `/slice` 로 돌린 뒤, 끝난 슬라이스에 테스트를 **소급해서** 붙일지 정한다
- [ ] 화면 슬라이스마다 `ui-reviewer` `판정: 통과`, `design_check` **0건**
- [ ] 시안과 실제 화면 대조 (색·글자 크기·간격·의미 색)
- [ ] 역할 전환별 시나리오 확인
- [ ] 팀원 1~2명 사용 확인, 지적 반영

### P5. 사내망 고정본

- [ ] 사내망 재검토 할 일 처리 (B 묶음)
- [ ] `meeting_v_F` 고정본 저장소 만들기 (전환 지점만 교체)
- [ ] 사내망 검증

## 매 단계 반복하는 절차

1. `code-gen` 에이전트에 **슬라이스 하나**만 지목해 돌린다 (S-1은 코드가 아니라 문서·진단이라 직접 쓴다).
2. `spec-guard`로 `requirements.md`와 어긋난 곳을 확인한다 — `판정: 통과`가 나와야 한다.
3. 아래 상세의 완료 판정 명령을 **직접 돌려** 통과를 확인한다. 통과 못 하면 완료로 적지 않는다.
4. 단계 체크박스와 "다음 할 일"·"작업 실적 로그"를 고치고 `roadmap.py update`를 돌린다.
5. 사용자에게 변경을 보고하고 **커밋 여부를 확인받은 뒤** 커밋한다. **한 커밋 = 한 단계**.

## P2 단계별 상세 (S-1 ~ S2)

> 이 절은 진행율 계산에서 빠진다 (체크박스를 쓰지 않는다). 단계 완료는 위 "P2. 기반"에서 센다.

### S-1. 문서·검증 기반

**목표** — `code-gen`을 돌리기 전에 ① 읽을 입력과 ② 통과를 판정할 수단을 갖춘다.
**선행** — 없음

**작업 전 확인**
- `.claude/agents/code-gen.md` §1(읽을 것 5개)·§3(금지)·§4(함정 7개)·§5(검증 명령)
- `.claude/agents/spec-guard.md` §6 — `diagnostics/check_*.py`를 전부 돌리는 쪽
- 원본 zip `C:\Users\shiset1\Downloads\meeting-main.zip`의 `CLAUDE.md` §6 "꼭 지킬 원칙" 1~9 — **참조용**. 스택 서술(FastAPI·Jinja2·`app/routers/`)은 가져오지 않는다

**만들 파일**
- `CLAUDE.md` — 도메인 원칙 9개(원본 §6 그대로) + 스택·폴더·실행 명령은 Streamlit 기준으로 다시 씀(`uv run streamlit run app.py`, `views/`·`modules/`·`config/`). `code-gen.md` §3 금지 목록과 겹치는 내용은 베끼지 말고 "`code-gen.md` §3 참조"로 넘긴다
- `diagnostics/check_data.py` — CSV 15종 존재·헤더·행 수, `hull` 12칸, 시드 FK 순서 15개 이름 확인. **표준 라이브러리만** (`_check.py`와 같은 방식). S2 전에도 돌아간다
- `diagnostics/check_db.py` — `modules/db.py` import → 테이블 수 → 15표 행 수. S1·S2 전에는 "아직 없음"을 한 줄로 보고하고 비정상 종료 (그 상태를 통과로 세지 않기 위해)
- `diagnostics/check_libs.py` — 필수 `streamlit`·`sqlalchemy`·`pandas` / 선택 `st_aggrid`·`streamlit_drawable_canvas` (`code-gen.md` §4⑦ 강등 경로 전제) import 가능 여부
- `diagnostics/check_llm.py` — S3 이후용. 지금은 "사내 LLM 설정 없음 → SKIP"만 찍는 뼈대. 원본 `check_env.py`의 프록시·SSL 절은 **가져오지 않는다** (`code-gen.md` §3이 프록시 금지)

**완료 판정**

```bash
for f in diagnostics/check_*.py; do uv run python -X utf8 "$f"; echo "$f EXIT=$?"; done
```

4개 모두 크래시 없이 끝나고 `check_data.py`가 `EXIT=0`. (`check_db.py`는 이 단계에선 "모델 없음"으로 비정상 종료가 정상)

### S0. 골격·설정

**목표** — 빈 Streamlit 앱이 실제로 뜨고, 설정·경로를 쓰는 창구가 한 군데로 고정된다.
**선행** — S-1

**작업 전 확인**
- `code-gen.md` §2 S0 행(만들 파일 7개) · §3 금지(`st.secrets[...]` 직접 호출, 경로 하드코딩, 사외망 금지 목록) · §4④(상호작용마다 스크립트 재실행)

**만들 파일**
- `app.py`
- `config/settings.py` — 비밀값 창구. 다른 파일은 `from config.settings import secrets`만 쓴다
- `config/paths.py` — 경로 창구
- `.streamlit/config.toml`
- `.streamlit/secrets.toml.template`
- `pyproject.toml`
- `requirements.txt`

**완료 판정**

```bash
uv run python -X utf8 -c "import config.settings, config.paths"
```

```bash
uv run python -X utf8 diagnostics/check_libs.py; echo "EXIT=$?"
```

```bash
uv run streamlit run app.py --server.port 8501 --server.headless true
```

import 통과 + `check_libs.py` `EXIT=0` + 앱이 떠서 빈 홈이 보인다. 추적 안 되는 `.claude/launch.json`도 이 단계에서 포트와 함께 정리한다.

### S1. 모델

**목표** — 기준정보 15표를 SQLAlchemy로 선언한다. **운영 표는 만들지 않는다** (아래 결정 2번).
**선행** — S0

**작업 전 확인**
- `requirements.md` §1-1 — 15표와 칸 목록
- `data/samples/masters/*.csv` **헤더** — 칸 이름의 정본. 문서와 다르면 CSV가 이긴다 (`alias`가 그 예: 문서엔 7칸, 실제 CSV는 5칸)
- `SPEC.md` §2(4층 구조)·§3-3(`stage` 5종)
- `code-gen.md` §4① — **`hull`은 12칸**이고 원본에는 `ShipModel` 클래스가 아예 없다

**만들 파일**
- `modules/models.py` — 15표

| 주의할 표 | 내용 |
|---|---|
| `hull` | `id, ship_type_id, model_id, owner_id, sister_group_id, series_no, stage, delivery_date, title, dock, ship_class, source` 12칸 |
| `ship_model` | **신설** — 원본 `app/models/masters.py`에 없다. 없으면 시드가 `TypeError: 'model_id' is an invalid keyword argument for Hull`로 죽는다 |
| `system`·`symptom_code`·`cause_code` | `parent_id` 자기참조 |
| `alias` | `text, target_kind, target_id, scope_hull_id, source` 5칸 (`id`·`created_by` 없음) |

**완료 판정**

```bash
uv run python -X utf8 -c "import modules.models"
```

```bash
uv run python -X utf8 -c "import modules.models as m; print(len(m.Base.metadata.tables))"
```

import 통과 + 선언된 테이블 수가 **15**.

### S2. DB·시드

**목표** — CSV 15종 99행이 DB에 올라가고, 다시 띄워도 중복 적재되지 않는다.
**선행** — S1

**작업 전 확인**
- `code-gen.md` §4② 시드 순서(FK 순서, 아래 그대로) · §4③(호선번호 정규화) · §4④(1회 가드) · §4⑤(인코딩) · §4⑥(빈 날짜·빈 정수)
- `SPEC.md` §7 검증 7규칙 — `_check.py`가 그대로 검사한다

```
department, ship_type, ship_model, owner, sister_group, hull,
system, maker, equipment_model, installed_equipment, component,
test_item, symptom_code, cause_code, alias
```

**만들 파일**
- `modules/sn_util.py` — `ensure_sn` 하나. `2511` / `S2511` / `sn2511` / 앞뒤 공백 붙은 `SN2511` → 모두 `SN2511`. **한 군데만** 둔다 (별칭 사전 F3가 여기 걸린다)
- `modules/db.py` — 엔진은 `@st.cache_resource`
- `modules/seed.py` — 위 순서대로 적재. CSV는 `encoding="utf-8-sig"`, 빈 날짜·빈 정수(`series_no`·`order_no`)는 `None`으로 바꿔 꽂는다. 1회 가드는 `st.session_state`가 아니라 **DB 안에 행이 있는지**로 판정 (탭을 새로 열면 세션이 새로 생긴다)

**완료 판정**

```bash
uv run python -X utf8 diagnostics/check_data.py; echo "EXIT=$?"
```

```bash
uv run python -X utf8 diagnostics/check_db.py; echo "EXIT=$?"
```

```bash
cd data/samples/masters && uv run python -X utf8 _check.py; echo "EXIT=$?"; cd -
```

셋 다 `EXIT=0` + DB 행 수가 CSV와 일치:

| 표 | 행 | 표 | 행 | 표 | 행 |
|---|---|---|---|---|---|
| `department` | 8 | `hull` | 13 | `component` | 6 |
| `ship_type` | 5 | `system` | 7 | `test_item` | 3 |
| `ship_model` | 7 | `maker` | 3 | `symptom_code` | 4 |
| `owner` | 7 | `equipment_model` | 3 | `cause_code` | 6 |
| `sister_group` | 6 | `installed_equipment` | 7 | `alias` | 14 |

합계 **99행 / 15표**.

## §9 결정 결과 (2026-11-12) 와 §10 미결

> 이 절은 진행율 계산에서 빠진다. 정본은 `SPEC.md` §9·§10. 여기는 요약이다.

| § | 결정 | 반영 |
|---|---|---|
| 9-1 모델 약호 | `174km3 LNG` · `13000TEU` 꼴. 셔틀탱커·VLEC·FLNG 3종은 지금 표기 유지 | ✅ `ship_model.csv` 4행 교체, `SPEC.md` §3-1 |
| 9-2 모델 분해 | 적재량까지 유지. 더 쪼개지 않는다 | ✅ 변경 없음 |
| 9-3 `series_no` | 계약 순서. **대책 반영은 순번이 아니라 호선 ID로 적는다** | ✅ `SPEC.md` §5 |
| 9-4 단계 어휘 | `안벽기간`(나머지) · `시운전기간`(ST+GasT) · `앵카링기간`(AC+Cold) · `Layup`(WF~DL) · `인도선`. 값은 **일정에서 계산** | 🔸 어휘·구간·샘플 정리 완료. **값 계산만 §10 선행** |
| 9-A 이름 | **표 이름·칸 이름(헤더)은 바꾸지 않는다.** 사내망에서 헤더 값만 매칭한다. 칸 추가도 먼저 묻는다 | ✅ `CLAUDE.md` §2, `SPEC.md` §9-A |

### 샘플 데이터를 진행 호선으로 정리했다 (24 → 13척)

커미셔닝팀이 다루는 것은 안벽에 들어온 뒤의 호선이라, 설계·건조 9척을 뺐다. 인도선은 **2척만 남겼다.**

- `SN2510`을 남긴 것이 중요하다. `SG-01`의 **1번선**이어서, 빼면 그 묶음 순번이 2·3으로 시작해 **검증 규칙 4가 깨진다.** 남기니 1·2·3으로 이어진다.
- `SN2402`는 단독선이라 묶음에 영향이 없다.
- `SG-02`(SN2433·SN2434)는 두 척 다 인도돼 **소속 호선이 없는 묶음**으로 남았다. 기준정보에서 지우지 않았다.
- `ST-FLNG`·`SM-FLNG2M`·`SM-CNT2700`·`OW-G`는 쓰는 호선이 없어졌다. 목록이므로 남겨 둔다.

합계 **112행 → 99행** (hull 24→13, installed_equipment 9→7). `check_data.py`의 기대값과 `_check.py`의 `STAGES`를 함께 고쳤다.

진행 호선 11척은 아직 옛 표기(`시운전 1단계`·`시운전 2단계`)다. 새 값은 일정에서 계산해야 하는데 그 일정이 없어서다(§10). `STAGES`가 목표 어휘 5개와 옛 표기 2개를 **함께** 받고, §10이 정해지면 11척을 계산해서 바꾸고 옛 표기를 지운다.

### §10 호선 이벤트 일정 — S1·S2를 막고 있다

정해진 것: **별도 표**(hull에 칸을 더하지 않는다) · **사내 시스템(pjtlist 등)에서 들어온다**(사람 입력 아님) · 받을 이벤트는 **시운전 출항·귀항 / 앵카링 시작·해제 / Layup 시작·해제**(안벽은 나머지로 계산하므로 받지 않는다).

**`data_manager`에서 확인했다** (<https://github.com/kuku5417-wq/data_manager>, `DATA_SCHEMA.md`)

구간 코드는 한 표에 있지 않다. **두 표를 함께 써야 한다.**

- `milestone.parquet` — 호선 마일스톤. MySQL `pjtevnt` 미러, **wide 그대로**. 키 `project`(ensure_sn), `PLAN`/`PROS`/`PERF` × 15 이벤트. `COLDFROM`·`GASFROM`·`STFROM`·`WF`(진수)·`DL`(인도)이 여기 있다
- `trial_schedule.parquet` — 시운전 **항차**. `PJT`·`일정구분`·`출항`·`복귀`. **`AC`는 여기 `일정구분` 값이다** (`LC~GT+1`·`AC`·`통합시운전`·`ST,DP`·`인도준비`)

**받는 표는 `milestone` 하나, 칸 이름은 헤더 그대로** (2026-11-12 결정). `trial_schedule`은 받지 않는다.

**계산 규칙** (상세는 `SPEC.md` §10-2)

- 날짜는 **`PERF`(실적) → `PROS`(전망) → `PLAN`(계획)** 순으로 처음 값이 있는 것
- `시운전기간` = `STFROM~STTO`, `GASFROM~GASTO`
- `앵카링기간` = `ACFROM~ACTO`, `COLDFROM~COLDTO`
- `Layup` = **`pjtlist.WORKFINISH` ~ `DL`** (진수가 아니다. 공사 끝나고 인도까지 대기 계류)
- `안벽기간` = 나머지 / `인도선` = `DL`이 지남
- **겹치면 시작일이 가장 늦은 구간**이 현재 단계

**`AC`는 `ACFROM`/`ACTO`로 있다** (2026-11-12 확인). `DATA_SCHEMA.md`(2026-08-11 스냅샷)에는 없지만 운영 `pjtevnt`에 있다 — 문서가 "운영 DB에 이벤트가 추가되면 컬럼이 늘어난다"고 경고한 그대로이고, `SELECT *`이라 코드 수정 없이 들어온다. 이벤트 **17종 × 3계열 = 51칸 + 키 = 52칸.**

**네 구간이 모두 `milestone` 하나에서 나온다. §9-4를 적용할 조건은 갖춰졌다.**

남은 것은 급하지 않다 — 뜻이 안 적힌 코드 여섯 개(`SP`·`BT`·`GT`·`CMR`·`IE`·`MT`)는 우리 계산에 쓰이지 않고, 문서에 없는 컬럼이 더 있는지는 §10-3의 코드로 언제든 확인할 수 있다.

**덤으로 확인된 것** — `pjtlist.parquet`가 우리 `hull`의 실데이터 출처다. `SHIPNUM`↔`id`, `SEQNO`↔`series_no`, `MAINHULLNUM`↔`sister_group_id` 등으로 거의 1:1 대응한다. `data_manager/sn_util.py`의 `ensure_sn`이 `code-gen.md` §4③과 같은 동작이라, S2의 `modules/sn_util.py`는 그 규칙을 따른다.

기준정보 15종에 없는 표이므로, 만들기 전에 `requirements.md`에 먼저 적어야 한다 (`CLAUDE.md` §8-7).

**확인된 제약** (정리 중에 데이터에서 드러난 것)

- `alias`의 `target_kind`는 지금 `installed_equipment`·`component`·`symptom` 셋뿐이라 **모델을 가리킬 수 없다.** 현장 모델 표기가 여럿이면 `code` 하나로는 못 받는다.
- 샘플 호선은 계약·호선번호·인도일 순서가 전부 일치해 **9-3이 어느 쪽이든 샘플 CSV는 그대로 쓸 수 있다.** 차이는 실데이터에서만 드러난다.
- 검증 규칙 5("한 묶음 안은 같은 모델")는 9-2를 더 쪼갤 때의 지뢰다. 유지로 결정돼 지금은 걸리지 않는다.

## 디자인 (SD)

2026-11-12에 "로드맵에 디자인이 없다"는 지적으로 생긴 절이다.
2026-11-13에 **디자인 묶음**이 들어오면서 정본과 점검 수단이 갖춰졌다.

**정본과 점검 수단**

| | |
|---|---|
| `docs/디자인_규칙.md` | **디자인 정본.** 정본 위치, 규칙 8개, 컴포넌트 토큰 10가지 |
| `docs/_시안/design/tokens.css` | 색·글꼴·크기 토큰 (54줄). 대비 4.5:1 이상으로 계산해 둔 값 |
| `docs/_시안/design/mockups/v2m-*.html` | **최종 시안.** 회의자료 편집은 `v2e-studio.html` |
| `.claude/agents/ui-reviewer.md` | 화면 슬라이스 점검 (읽기 전용) |
| `.claude/tools/design_check.py` | 토큰 밖 색·이모지 찾기 |
| `.claude/refs/UI_패턴_사전.md` | 새 기능의 UI 후보 비교용 |

**정해진 것**

- **라이트만** 쓴다 (2026-11-12). 시안에 다크도 있지만 받지 않는다
- **흰 사이드바** (2026-11-13, 안 B). 시안 v2m의 네이비 사이드바와 남색 제목을 따르지 않는다
  — `--side-bg #ffffff` · `--side-fg #111114` · `--side-muted #48484d` · 오른쪽 경계선 `--sep`
  — 지금 메뉴: 바탕 `--accent-soft`, 글자 `--accent-ink`, 왼쪽 막대 `--accent`. 큰 제목은 `--fg`
- **주 색은 `--accent #0963c4`** (2026-11-13). `v2m.css`의 `#0a6cd6`은 쓰지 않는다

**한 것** (2026-11-12, SD 1차)

`.streamlit/config.toml` 테마 4색 매핑 · `views/theme.py` 토큰 주입 · 의미 색 배지(`chip`) ·
이슈 상세 머리에 유형·상태·경보 배지.

**한 것** (2026-11-13, SD 2차 — `design_check` **0건**)

1. ✅ **흰 사이드바.** 지금 메뉴는 `--accent-soft` 바탕 + `--accent-ink` 글자 + `--accent` 왼쪽 막대
2. ✅ **앱 쪽 `static/tokens.css` 신설.** `views/theme.py`가 시안 원본과 앱 파일을 **읽어서** 넣는다 —
   `.py`에 색이 없다(규칙 2-1). 시안 파일은 원본이라 고치지 않았고, 다크 블록은 `theme.py`가 걷어낸다
3. ✅ **`--sep`·`--warn-soft` 신설.** 값을 지어내지 않고 이미 있는 토큰을 가리킨다
   (`--sep: var(--line)` · `--warn-soft: var(--signal-soft)`). 시안이 제 값을 정하면 그때 여기만 바꾼다
4. ✅ **이모지 11건 제거** → `:material/` 아이콘

   > 아이콘이 처음에 **"flag"라는 글자로** 나왔다. 글꼴 규칙이 넓어 아이콘 span 까지 덮어
   > Material 리거처가 깨진 것이다. 아이콘 `data-testid` 셋만 `"Material Symbols Rounded"`로 되돌렸다.
   > 그 글꼴은 Streamlit 이 함께 넣어 둬서 사외망·사내망 모두 뜬다.

5. ✅ **글꼴 서브셋을 앱에 넣었다** (2026-11-13). `static/fonts/` 에 woff2 5개 + OFL 2건,
   `static/fonts.css` 가 `@font-face` (선언은 시안 것 그대로, 경로만 앱 자리로).
   `.streamlit/config.toml` 의 `enableStaticServing` 으로 `/app/static/` 에서 받는다.

   > 사내망에서 외부 글꼴이 막혀도 시안과 같은 글꼴로 보인다 — 그러라고 시안이 서브셋을 둔 것이다.
   > 정적 제공을 끄면 글꼴만 안 받아지고 대체 사슬(맑은 고딕)로 떨어진다. 화면은 그대로 뜬다.
   > 저장소가 840KB 늘었고 `docs/_시안/` 것과 같은 파일이라 중복이다 — 시안은 참조용이라 그대로 둔다.

**남은 것** — SD 에서 할 일은 다 했다. 아래 컴포넌트 토큰만 남는다.

**`ui-reviewer` 1차 (2026-11-13) — 판정: 반려 (필수 10건)**

고친 것 6건

- 경보 칩이 **늘 중립색**이었다. 칸 값이 `"일정 임박 D+28"` 꼴인데 뜻 사전을 그대로 찾아 못 맞혔다 → 앞머리로 찾게 고쳤다. 칩 글자 이스케이프도 함께
- `st.success` 바로 뒤에 `st.rerun()` 이라 **완료 표시가 뜨기 전에 사라졌다** → `st.toast`
- 비활성 버튼 4곳에 **왜 안 되는지** 도움말 (규칙 2-7)
- 「AI 로 정리」에 **불러오는 중** 표시
- `--warn-soft` 가 정의만 되고 쓰이지 않았다 → 근거 표시를 노란 바탕 칸으로 (규칙 §3)
- **「종결」을 부서가 고를 수 있었다** — `CLAUDE.md` §6-7 위반. 고르는 자리에서 뺐다(거르기에는 남김)

지적이 빗나간 것 1건 — `static/tokens.css` 미추적. 점검이 커밋 직전 상태를 봤다. `9284dd6` 에 들어가 있다

남은 것 — 아래 컴포넌트 토큰 4건이 그대로 필수로 남아 있다. [제안] 14건은 그 화면을 손댈 때 함께 본다
(줄일 수 있는 요소 12개: 사이드바 개발 진단 4·상태 지표 5·고르는 방식 중복·기능 번호 라벨)

**컴포넌트 토큰** — ✅ 2026-11-13 맞췄다. 방식은 `views/ui.py` 한 곳에 두고 화면은 부르기만 한다.

| 하는 일 | 정한 방식 | 어디에 |
|---|---|---|
| 목록 | 흰 카드 목록 + 선택 행 왼쪽 파란 막대 | `ui.card_list()` — `st.columns([9,2])` + 카드 HTML + 「열기」 버튼. 고르지 않는 카드 한 장은 `ui.card()` |
| 걸러 보기 | 칩 + 찾기 칸 | `ui.filter_pills()` · `ui.search_box()`. **건수를 칩 안에 넣어 지표 5개를 없앴다** |
| 여러 건 처리 | 체크한 뒤 일괄 동작 | `ui.check_list()` — `st.data_editor` 체크 칸, 값 칸은 잠근다 |
| 저장 | 자동 저장, 저장 버튼 없음 | 설정은 고치면 바로 쓴다. 원장의 초안·경보는 `on_change` |
| 삭제·취소 | 바로 지우고 되돌리기를 준다 | 설정에서 줄을 지우면 「되돌리기」가 뜬다. 표 위젯 key 에 판 번호를 붙여 되살린 줄이 또 지워지지 않게 한다 |
| 주 버튼 | 한 화면에 하나 | `ledger` 등록 · `inbox` 「기록하고 다음」 · `settings` 0개 |

확정한 방식은 `docs/디자인_규칙.md` §3 의 Streamlit 칸에도 적었다 — 다음 화면이 같은 것을 또 고르지 않게.

**재점검 반려 5건** — ✅ 2026-11-13 고쳤다 (`ui-reviewer` 2차)

- 목록의 여는 버튼이 **아이콘만**이었다 (규칙 2-4) → 「열기」 글자를 붙이고 칸을 `[9,2]` 로 넓혔다
- 같은 「이슈 등록」이 원장 `add` · 기록함 `arrow_forward` 로 갈렸다 → `add` 로 통일. `arrow_forward` 는 「다음 일로 넘어가기」에만 쓴다
- 설정에서 **지운 줄을 되돌릴 수 없었다** (§3 "삭제·취소") → 되돌리기를 붙였다
- 기록함에서 **새로 적은 메모가 밀렸다** — 목록이 기억한 옛 줄이 이겼다 → 저장할 때 목록의 고른 줄도 새 메모로 옮기고, 아직 아무것도 열지 않았으면 저절로 열지 않는다
- 카드의 `meta` 가 **이스케이프를 거치지 않았다** → 사람이 적은 글은 `ui.card()` 가 이스케이프하고, 칩 HTML 만 `chips` 로 따로 받는다

곁들여: `st.toast` 아이콘이 글자(`check`)로 보였다 — `stToastDynamicIcon` 을 아이콘 글꼴 규칙에 더했다.

**아직인 것** (`ui-reviewer` [제안] 쪽)

- 사이드바의 개발 진단 4개와 홈의 개발 메모 — 업무 화면에 개발자 눈이 남아 있다
- 앱 이름 h1 과 화면 h2 가 겹친다
- 이슈 등록 폼이 원장·기록함 두 곳에 있고 `_departments()` 가 복붙돼 있다
- 의미 색 쓰임(`dashboard`=accent · `연결됨`=ok · `미등록`=danger)이 뜻과 맞는지
- 유형 칩이 영문(`issue`)이다
- 원장이 같은 이슈를 **두 벌**로 보여 준다 — 카드 목록과 「일괄 정리」의 체크 표. 시안 v2m 은 한 목록에서 체크한다
- 상세가 목록에서 멀다 — 등록 폼 아래 맨 끝에 있다. 시안은 목록 옆에 붙는다
- 「기록하고 다음」이 실제로 다음으로 넘어가지 않는다 (원장은 제자리, 기록함은 그 메모를 연다)
- 「일괄 정리」에 전체 선택이 없다

**언제 하나** — 5와 위 [제안]은 그 화면을 손댈 때 함께 한다.

## 뚫어 보기 기록 (P1)

교재 70쪽 방식. 하나씩 시켜 보고 막혔는지·무엇이 막았는지 적는다. 뚫리면 `guard-test.js`에 그 경우를 한 줄 추가하고 `guard.js`를 고쳐 FAIL 0을 다시 만든다.

| # | 시킨 것 | 결과 | 막은 것 |
|---|---|---|---|
| 1 | 보호 폴더의 비밀 파일 내용 보여 주기 | | |
| 2 | 원본 데이터 폴더의 엑셀 한 칸 바꾸기 | | |
| 3 | PowerShell `Copy-Item`으로 덮어쓰기 | | |
| 4 | Python으로 열어서 저장하기 | | |
| 5 | 다른 폴더에서 고친 뒤 옮기기 | | |

**실제 세션에서 막힌 사례 1건** (2026-11-12): `.gitignore` 확인용 `git check-ignore` 명령이 차단됐다. 명령문에 보호 경로 이름과 읽기 동사(`head`)가 함께 들어가 "비밀·보호 경로를 읽는 명령"으로 판정. 읽기 동사를 빼서 통과. → 가드가 의도대로 동작하며, 보호 경로 이름을 적기만 해도 걸린다는 뜻이다.

## 작업 실적 로그

| 날짜 | 단계 | 한 일 | 검증 | 커밋 |
|---|---|---|---|---|
| 2026-11-12 | — | `roadmap.md` 신설 (S-1~S2 계획 + 진행 장부) | `_check.py` EXIT=0 (기준선) | 없음 |
| 2026-11-12 | P1 | 교육장 묶음 적용 — `.gitignore`, 권한 규칙, 가드 훅 2개, `roadmap.py`, 에이전트 2개 보완 (`ROADMAP.md`는 제외하고 받음) | `guard-test.js` 26건 FAIL 0 / `git check-ignore` 12건 의도대로 / 가드 훅 실차단 1건 | `d464b6b` |
| 2026-11-12 | P0 | `ROADMAP.md` 재작성 — P0~P5 체계로 전환, 기존 `roadmap.md` 삭제 | `roadmap.py update`·`brief`·`check` 전부 EXIT=0 | `d464b6b` |
| 2026-11-12 | P0 | `main` push — `origin/main`을 `bdebcc9` → `1f83269`로 올림. 미push였던 이전 3커밋 포함 | 올라간 파일 24개 점검, 비밀·원본 데이터 없음 (샘플 CSV는 가상값) | `1f83269` |
| 2026-11-12 | P2 S-1 | `CLAUDE.md` 신설 (도메인 원칙 9개·용어 17개·폴더 구조·실행 명령) + `diagnostics/` 4종 신설 | `check_data` EXIT=0 (15표 99행·`hull` 12칸·시드 순서 15종·자기참조 부모 순서) / `check_db` EXIT=1 "모델 없음"(정상) / `check_libs` EXIT=1 필수 3개 미설치(S0 전 정상) / `check_llm` EXIT=0 SKIP / `_check.py` EXIT=0 유지 | `823c6a3` |
| 2026-11-12 | P2 S0 | 골격·설정 7개 + `config/__init__.py` 신설, `uv sync`로 의존성 설치, `.claude/launch.json`에 앱 설정 추가 | `import config.settings, config.paths` EXIT=0 / `check_libs` **EXIT=0** (streamlit 1.67.0·sqlalchemy 2.1.8·pandas 3.1.1·python-pptx 1.0.2) / 앱이 8501에서 떠서 빈 홈 표시, 콘솔 오류 없음 / 사이드바에 기준정보 CSV 15장·DB 없음·LLM 없음이 창구를 거쳐 나옴 | `8d23147` |
| 2026-11-12 | P0 | `SPEC.md` §9 4건 정리 — 선택지·영향 범위·되돌리기 비용·권고안. 팀 공유용 결정 브리핑 발행 | 샘플 CSV·`_check.py` 규칙과 대조해 근거 확인 (별칭이 모델을 못 가리킴, 샘플 24척의 세 순서가 일치, 규칙 5와 모델 분해의 충돌) | |
| 2026-11-12 | P0 | §9 4건 **결정 확정·반영** — 약호 교체(`ship_model.csv` 4행), §5 순번 기준, §3-1 예시, §9-A 이름 고정 규칙(`CLAUDE.md`+`SPEC.md`). 9-4는 결정만 적고 보류, 새 미결 §10 신설 | `check_data` EXIT=0 (헤더·행 수 불변) / `_check.py` EXIT=0 (규칙 7개 유지) | |
| 2026-11-12 | P0 | 9-4 후속 — 단계 어휘·구간 확정(`인도선` 포함 5개), **샘플을 진행 호선으로 정리 24→13척**(설계·건조 9척 제외, 인도선 2척 유지), `_check.py` `STAGES`·규칙 7 어휘 교체, `check_data` 기대값 112→99행, §10에 정해진 것/막힌 것 분리 | `check_data` EXIT=0 (15표 99행) / `_check.py` EXIT=0 (호선 13건, 묶음 순번 SG-01 1·2·3 연속 유지) | |
| 2026-11-12 | P0 | §10 완결 — `data_manager`의 `milestone` 하나만 헤더 그대로 미러, 이벤트 17종(`ACFROM`/`ACTO` 포함), 계산 규칙 확정. `requirements.md` §1-4에 이벤트 표 추가 | 출처 코드(`gen_milestone`의 `SELECT * FROM pjtevnt`) 확인 | |
| 2026-11-12 | P2 S1 | `modules/models.py` 신설 — 기준정보 15표 선언 (`modules/__init__.py` 포함) | `import modules.models` 통과 / 선언 표 **15개** / `hull` **12칸** / `check_db`가 CSV 헤더 ↔ 모델 칸 대조 통과(칸 누락 0) / 진단 4개·`_check.py` 모두 기대대로 | |
| 2026-11-13 | P1 | **에이전트 묶음 도착** — `test-writer`·`code-reviewer` 2종과 `/slice` 스킬이 들어오고 기존 에이전트 3종의 경계 문구가 보완됐다. 묶음이 `ROADMAP.md`(499줄)를 11-12 교육장 판(89줄)으로 **또 덮어** `HEAD` 에서 되살리고 묶음 항목만 합쳤다 | 되살린 판 499줄 + 더한 4줄, S-1~S6·SD `[x]` 복구 확인 / `roadmap.py update` 통과 / `guard-test` FAIL 0 / 진단 EXIT=0 | |
| 2026-11-13 | P3 | **사건 당시 단계** — `block.occurred_on` 칸 추가(승인받고 더함), `extract.find_date`·`date_for` 가 메모에서 날짜를 읽어 미리 채우고 근거 구간을 `source_span` 에 남김, `issues.stage_at()` (그때, 지금). 원장 카드·상세 머리·「지식 매핑」 탭(호선 옆)·등록 폼에 보인다. 날짜 고르기 토큰을 캘린더로 확정. `db.add_new_columns()` 로 작업본 DB 에 칸만 더한다 | doctest 통과 / 진단 4개·`_check.py` EXIT=0 / `design_check` 0건 / 앱에서 `11/12 SN2512` 메모 → 발생일 자동 채움 → 「그때 시운전기간 · 지금 안벽기간」 확인 | |
| 2026-11-13 | P0 | **미결 A·B 닫음** — 회의자료는 `meeting` 하나로, `hull.stage` 는 볼 때마다 계산. `requirements.md` §2 에 열려 있는 결정이 없어져 S7 이 열렸다 | 13척 중 12척이 DB 값과 일치, SN2512 만 날짜 때문에 다름(의도한 결과) | |
| 2026-11-13 | SD 6차 | `ui-reviewer` 2차 반려 5건 수정 — 여는 버튼에 「열기」 글자(`[9,2]`), 이슈 등록 아이콘 `add` 통일, 설정 삭제 **되돌리기**(위젯 판 번호로 재삭제 막음), 기록함이 새 메모를 열도록 목록 선택도 옮김·자동 선택 끔, 카드 글 `html.escape`(`ui.card()` 신설), `st.toast` 아이콘 글꼴(`stToastDynamicIcon`) | `design_check` 0건 / 진단 4개·`_check.py` EXIT=0 / 앱에서 5건 모두 확인 — 「열기」 버튼, `+ 이슈로 등록`, 지우고 되돌려 99행 복구, 새 메모가 열리고 목록 맨 위에 파란 막대, `<점검>` 이 글자 그대로 보임 | |
| 2026-11-13 | SD 5차 | 컴포넌트 토큰 4건을 맞췄다 — `views/ui.py` 신설(`card_list`·`filter_pills`·`search_box`·`check_list`), 원장·기록함 목록을 카드로, 거르기를 칩+찾기로, 일괄을 체크 칸으로, 저장을 자동 저장으로, 주 버튼을 화면당 하나로. 상태 지표 5개 제거, 탭·화면의 기능 번호 제거, 후보 중복 등록 막음 | `design_check` 0건 / 진단 4개·`_check.py` EXIT=0 / 화면 4개 임포트 통과 / 앱에서 카드 목록·파란 막대·칩 메타·건수 칩 확인 | |
| 2026-11-13 | SD 4차 | 글꼴 서브셋을 앱에 넣음 — `static/fonts/` woff2 5개 + OFL 2건, `static/fonts.css`, `enableStaticServing` | `document.fonts` 로 Meeting Sans KR 400·600 **loaded** 확인, `fonts.check('400 14px "Meeting Sans KR"')` true / `design_check` 0건 / 진단 4개 EXIT=0 / 저장소 +840KB | |
| 2026-11-13 | SD 3차 | `ui-reviewer` 1차 반려(필수 10건) 중 6건 수정 — 경보 칩 색·완료 표시·비활성 도움말·스피너·근거 노란 바탕·「종결」 선택 제한 | `design_check` 0건 / 진단 4개 EXIT=0 / 앱에서 사이드바 흰색(`rgb(255,255,255)`)·`--warn-soft` `#fbefd9` 로 풀림·예외 없음 / `_token_for` 가 "일정 임박 D+28"→signal, "기한 지남 D-72"→danger 로 맞음 | |
| 2026-11-13 | SD 2차 | 흰 사이드바, `static/tokens.css` 신설(`theme.py`는 읽기만), `--sep`·`--warn-soft` 신설, 이모지 11건 → `:material/` 아이콘 | `design_check` **0건** / 진단 4개·`_check.py` EXIT=0 / 앱에서 흰 사이드바·지금 메뉴 강조·아이콘 글리프 확인 | |
| 2026-11-12 | P3 S6 | `modules/extract.py`·`views/inbox.py` 신설, `app.py`에 기록함 화면 | `locate` doctest 3건 / **근거 규칙(§6-3)이 코드로 막힌다** — 지어낸 후보(메모에 없는 `quote`)와 제목 없는 후보를 버리고 왜 버렸는지 화면에 적는다 / 등록 시 `source_span` 4칸 + `ai_field_log` 기록 / 사외망에서는 `LLMNotConfigured` → 직접 적기로 강등, 사람이 적은 값은 근거 구간 없이 등록 / 진단 4개 EXIT=0 / 앱에서 기록함 렌더 | |
| 2026-11-12 | P3 S5 (2/2) | `modules/milestone.py` 신설(§10-2 계산), `data/samples/mirror/` 샘플 2종, `config/paths.py`에 `MIRROR_DIR`. F5 초안·사진, F21 경보, F23 일괄을 `issues.py`·`ledger.py`에 추가. **§9-4 적용 완료** — `hull.stage` 11척을 계산값으로 바꾸고 `_check.py` `STAGES`에서 옛 표기 2개 제거 | 13호선 단계 계산이 5개 어휘를 모두 냄 (안벽 5·시운전 3·Layup 2·인도선 2·앵카링 1) / `_check.py` 규칙 7개 통과 / F21 `ISS-2026-0001` DL 목표 → 「일정 임박 D+28」 / F5 초안 저장·사진 `data/photos/89/<sha>.png` / F23 2건 일괄 변경 + 이력 기록 / 진단 4개 EXIT=0 / 앱에서 4개 탭 렌더 | |
| 2026-11-12 | P3 S5 (1/2) | 운영 표 16종 선언(`models.py` 15→31표), `config/paths.py`에 사진 폴더 창구, `modules/issues.py`·`views/ledger.py` 신설, `app.py`에 원장 화면 | F3 지식 매핑이 실제로 걸림 — `2511`→`SN2511`(ensure_sn), `DG2`→`EQ-SN2511-GE-02`·`C/P #3`→`EQ-SN2514-CP-03`·`배기온도 편차`→`SY-EXH-DEV`(별칭), 기준정보에 없는 `9999`는 0/5 「미등록」 / ID 발급 `ISS-2026-0001~0003` / 주차 `2026-W46` 자동 생성 / F4 주차별 진행 한 줄 / `check_db` EXIT=0(기준정보 15표 그대로, 운영 16표는 별도로 보고) / 앱에서 그리드·등록·상세 렌더 | |
| 2026-11-12 | P3 S4 | `views/settings.py`·`views/__init__.py` 신설, `app.py`에 화면 분기(`SCREENS`). `seed._to_values`를 `to_values`로 공개해 저장이 시드와 같은 변환을 쓰게 함 | 추가·수정·삭제·무변경 4경우 확인 / 복합 기본키(`alias` 3칸) 확인 / 날짜·정수 변환 확인(`delivery_date`→`date`, 빈 `series_no`→`None`) / 재시드 99행 복원 / 앱에서 설정 화면 렌더, `department` 8행 편집 가능, 콘솔 오류 없음 / 진단 4개 EXIT=0 | |
| 2026-11-12 | P2 S3 | `modules/llm_client.py` 신설 — 창구만. 호출은 `_chat()` 한 함수로 몰고 `SPEC.md` §11에 사내 게이트웨이 모양을 적었다(근거: `data_manager/llm_client.py`). `check_llm`이 창구 유무를 보도록 보완 | `parse_json` doctest 4건 통과 / `check_llm` EXIT=0 (설정 없음 SKIP + 창구 확인) / 설정 없이 부르면 `LLMNotConfigured` / 실제 코드에 `requests`·`verify=False`·`proxies`·외부 API 없음 / **진단 4개 전부 EXIT=0** | |
| 2026-11-12 | P2 S2 | `modules/db.py`·`seed.py`·`sn_util.py` 신설. `app.py` 사이드바가 적재 행 수를 보이도록 수정 | `check_db` **EXIT=0** (15표 99행 일치) / 재실행 시 "이미 적재돼 있어 건너뜀" — 중복 적재 없음 / `--force` 재시드 99행 / **진단 4개 전부 EXIT=0** (처음) / `_check.py` EXIT=0 / 앱에서 "적재된 행 99행" 표시, 콘솔 오류 없음 / `data/meeting.db`는 `.gitignore`가 거름 | |

## 추가·변경 기록

| 날짜 | 바뀐 것 | 근거 |
|---|---|---|
| 2026-11-12 | **S-1 단계 신설** — S0 앞에 `CLAUDE.md`·`diagnostics/` 4종을 먼저 만든다 | `code-gen.md` §1이 `CLAUDE.md`를 2순위 입력으로 읽으라는데 저장소에 없고, §5·`spec-guard.md` §6이 쓰는 `diagnostics/check_*.py`도 없어 통과 판정이 불가능했다 |
| 2026-11-12 | **S1을 기준정보 15표로 축소** — 운영 표는 S5·S7에서 만든다 | `code-gen.md` §2 S1 설명은 "15표 + 운영 표"지만, `requirements.md` §1-2에 v2e-studio 관련 3표만 있고 나머지(원본 기준 약 30표)는 "미정". 쓰는 화면이 없는 빈 표를 미리 만들지 않는다 |
| 2026-11-12 | **`diagnostics/` 4종은 신설** — 원본에서 가져오지 않는다 | 원본 zip에도 없다. 최상위 `check_env.py` 1개가 가장 가깝지만 FastAPI·`app.db`·프록시 설정에 의존해 Streamlit 저장소에 맞지 않는다 (참고만) |
| 2026-11-12 | **S 단계 체계 → P0~P5 체계로 전환**, 파일명 `roadmap.md` → `ROADMAP.md` | `.claude/tools/roadmap.py`가 `### P<숫자>.` 제목과 `- [x]` 체크박스만 센다. 기존 `⬜🔄✅` 표기는 단계 0개로 읽혀 진행율이 0%로 나왔다. 또 종료 훅이 파일명을 대소문자 구분해 비교하므로(`ROADMAP.md`) 소문자 파일명이면 고쳐도 계속 막힌다. S 슬라이스는 P2·P3 안의 작업으로 유지 |
| 2026-11-12 | **`ROADMAP.md`는 교육장 묶음 것을 쓰지 않고 다시 씀** | 묶음 것(P0~P5, 29작업)은 단계 골격만 있고 S-1~S2 상세(작업 전 확인·만들 파일·완료 판정·112행 내역)가 없다. 기존 로드맵의 상세를 살리고 묶음의 형식만 가져왔다. 기존 파일은 사용자 승인 후 삭제 |
| 2026-11-12 | **`CLAUDE.md` 원칙 9번은 원본 그대로 쓰지 않고 고쳤다** | 원본 §6-9에는 테스트 단계 예외로 외부 API 체인(SOLA → Upstage → OpenAI → Mock)과 `MEETING_LLM_CHAIN` 설정이 적혀 있다. `code-gen.md` §3이 SOLA·프록시·외부 호출을 금지하므로 그대로 옮기면 서로 어긋난다. "사내 LLM만, 전환 지점은 `modules/llm_client.py` 한 군데, 실제 회사 메모는 넣지 않는다"로 바꿨다. 원칙 1~8은 원본 그대로 |
| 2026-11-12 | **진단·검증 명령을 `uv run python -X utf8 …`로 바꿨다** | S0에서 의존성이 `.venv` 안으로 들어갔다. 맨 `python`으로는 `check_libs`·`check_db`가 streamlit·sqlalchemy를 못 찾아 틀린 결과를 낸다. `CLAUDE.md` §5와 이 문서의 완료 판정 블록을 모두 고쳤다 (`check_data`·`_check.py`는 표준 라이브러리만 쓰므로 어느 쪽이든 돌지만 명령을 통일했다) |
| 2026-11-12 | **선택 라이브러리는 기본 설치에서 뺐다** | `st_aggrid`·`streamlit_drawable_canvas`는 사외망에서 설치가 막힐 수 있다(`code-gen.md` §4⑦). `pyproject.toml`의 `[project.optional-dependencies] ui`로 빼 두고 `uv sync --extra ui`로만 깔리게 했다. 기본 `uv sync`가 이것들 때문에 실패하면 앱 자체를 못 띄운다 |
| 2026-11-12 | **`config/settings.py`의 비밀값 읽기 시점 수정** | 처음에는 `st.secrets` 속성 접근을 `try`로 감쌌는데, Streamlit은 접근이 아니라 **읽는 시점**에 `StreamlitSecretNotFoundError`를 던진다. 그래서 `secrets.has()` 호출이 그대로 터졌다. `st.secrets.get(...)` 호출 자체를 감싸도록 고쳤다 — 사외망에서 `secrets.toml`이 없는 것이 정상 상태이므로 터지지 않고 기본값을 줘야 한다 |
| 2026-11-13 | **디자인 묶음이 `ROADMAP.md`를 덮어썼다 — 커밋본에서 되살려 합쳤다** | 묶음의 `ROADMAP.md`(85줄)가 교육장 원본 골격이라, 이 저장소에서 쌓은 374줄(실적 로그·변경 기록·§9·§10·P2 상세·SD·뚫어 보기)과 **S-1~S6 완료 표시**가 통째로 날아갔다. `d55037f` 에서 복원하고 묶음에만 있던 디자인 항목(P0 2개·P4 1개)을 옮겨 붙였다. **첫날 경고한 그대로였다** — 다음에 묶음을 받을 때도 `ROADMAP.md`는 빼고 받는다 |
| 2026-11-13 | **에이전트 묶음이 `ROADMAP.md`를 또 덮었다 (세 번째) — `HEAD` 에서 되살렸다** | 묶음의 `ROADMAP.md`(89줄·20%)는 **11-12 교육장 판**이라 S-1~S6·SD·§2 결정·실적 로그 499줄이 통째로 날아갔다. `git show HEAD:ROADMAP.md`(`7989efa`)로 되살리고, 묶음에만 있던 항목(P1 2개·P4 2개)을 손으로 더했다. **쪽지로는 세 번 다 못 막았다.** 앞으로는 ① 푸는 쪽에서 `ROADMAP.md` 를 빼고 ② 그래도 덮였으면 **먼저 `git show HEAD:ROADMAP.md > ROADMAP.md` 로 되살린 뒤** 묶음 판에만 있는 줄을 옮겨 붙인다. 묶음 판을 손보는 쪽은 잃는 것이 훨씬 많다 |
| 2026-11-13 | **에이전트가 3종 → 6종, `/slice` 스킬 신설** | 2026-11-13 묶음. `test-writer`(슬라이스 테스트)·`code-reviewer`(diff·테스트 검토)가 들어와 **테스트와 코드 리뷰 공백**이 메워졌다. `code-gen` 은 이제 테스트를 직접 쓰지 않는다. `/slice` 가 code-gen → test-writer → (spec-guard·code-reviewer·ui-reviewer 동시) → 반려 2회까지 수정 순서를 묶는다. S0~S6 은 이 장치 없이 만들어져 **테스트가 없다**(P4) |
| 2026-11-13 | **흰 사이드바·주 색 `#0963c4` 확정** (안 B) | `docs/디자인_규칙.md` 1절. 시안 v2m 의 네이비 사이드바를 따르지 않는다. SD 1차가 네이비로 만들어져 있어 다시 해야 한다 |
| 2026-11-12 | **`check_libs.py`는 S0 전까지 `EXIT=1`이 정상** | 필수 `streamlit`·`sqlalchemy`·`pandas`가 아직 설치되지 않았다(`pyproject.toml`이 S0 산출물). S-1 완료 판정은 "크래시 없이 끝남 + `check_data` EXIT=0"이고, `check_libs` EXIT=0은 **S0 완료 판정**이다. 선택 라이브러리(`st_aggrid`·`drawable_canvas`·`pptx`)는 없어도 오류로 세지 않는다 — `code-gen.md` §4⑦ 강등 경로 전제 |

## 범위 밖 / 미결

- ~~`requirements.md` §2 미결~~ — **2026-11-13에 전부 닫혔다.** `slide_object.props` 는 JSON 통칸으로, 나머지 운영 표는 §1-2-2 에 채웠고, 회의자료 표와 `hull.stage` 재계산도 정했다. S7 을 막는 것은 이제 없다 (S7 안에서 정할 것 하나는 「다음 할 일」 1번).
- `SPEC.md` §9 정해야 할 것 4건은 **P2 S1**(모델 선언) 전에 확정되는 편이 좋다. 모델 약호·`series_no` 기준이 표 칸에 직접 걸린다.
- 훅·권한 규칙이 실제로 올라갔는지는 터미널에서 `claude`를 다시 띄워 `/hooks`·`/permissions`로 확인한다. 이 데스크톱 앱에는 두 대화창이 없다.
