# requirements.md

> **정본.** `code-gen`은 이 문서를 기준으로 코드를 만든다. 칸 이름이 CSV 헤더와 어긋나면 **CSV 헤더가 이긴다**(§1-1 "CSV" 열 참고).
> 작성 2026-11-11 · `.claude/agents/spec-writer.md` 절차로 1차 작성. 근거: `SPEC.md`(호선 기준정보) · `data/samples/masters/*.csv`(칸 이름 정본) · `docs/_시안/design/mockups/README.md`+`v2e-studio.html`(화면·인터랙션) · 원본 기획서(`C:\Users\shiset1\Downloads\meeting-main.zip` 안 `docs/01·02·03·06·07`, 참조용 — 의도·F번호만 가져옴, FastAPI/Jinja2 구조는 안 가져옴. 이 저장소는 Streamlit).
>
> **범위**: 이번 1차 작성은 §1-1(기준정보 15종)을 전부 채우고, §1-2·§1-3은 **v2e-studio(회의자료 스튜디오) 화면과 직접 관련된 부분만** 채운다. 나머지 F 번호·운영 표는 "미정 — 다음 라운드에 채움"으로 남긴다. 임의로 범위를 넓히지 않는다.

---

## §1-1. 기준정보 (마스터) 15종

시드 순서 = FK 순서(`code-gen.md` §4-②와 동일, 바꾸면 적재가 깨진다):
`department → ship_type → ship_model → owner → sister_group → hull → system → maker → equipment_model → installed_equipment → component → test_item → symptom_code → cause_code → alias`

| # | 테이블 | 주요 칸 | 칸 수 | 샘플 CSV | 비고 |
|---|---|---|---|---|---|
| 1 | `department` | `id, code, name, order_no` | 4 | ✅ `department.csv` | 8개 부서: 기획운영·시운전기술·시운전1부·시운전2부·시운전3부·해운부·안벽의장그룹·친환경실증Lab |
| 2 | `ship_type` | `id, code, name` | 3 | ✅ `ship_type.csv` | — |
| 3 | `ship_model` | `id, ship_type_id, code, name, capacity, capacity_unit` | 6 | ✅ `ship_model.csv` | `SPEC.md` §3-1 신설 표. 적재량은 숫자(`capacity`)·단위(`capacity_unit`) 분리 |
| 4 | `owner` | `id, code, name` | 3 | ✅ `owner.csv` | 가명 허용(선주 A~G) |
| 5 | `sister_group` | `id, name` | 2 | ✅ `sister_group.csv` | — |
| 6 | `hull` | `id, ship_type_id, model_id, owner_id, sister_group_id, series_no, stage, delivery_date, title, dock, ship_class, source` | 12 | ✅ `hull.csv` | `SPEC.md` §3-2. `model_id`·`series_no` 신설 칸(원본 `docs/03`에는 없음 — CSV 헤더가 정본). `stage` 어휘 5종 고정(`SPEC.md` §3-3) |
| 7 | `system` | `id, code, name, parent_id` | 4 | ✅ `system.csv` | 자기참조(parent_id) — 시드 시 부모 행 먼저 |
| 8 | `maker` | `id, name` | 2 | ✅ `maker.csv` | — |
| 9 | `equipment_model` | `id, maker_id, name, model_no` | 4 | ✅ `equipment_model.csv` | — |
| 10 | `installed_equipment` | `id, hull_id, equipment_model_id, system_id, name, unit_no, position` | 7 | ✅ `installed_equipment.csv` | 호선별 탑재 장비. 9행(`SPEC.md` §6-2 수치와 일치) |
| 11 | `component` | `id, equipment_model_id, name` | 3 | ✅ `component.csv` | `equipment_model_id`는 CSV상 공란 허용 |
| 12 | `test_item` | `id, code, name, system_id` | 4 | ✅ `test_item.csv` | 시운전 절차서 출처(원본 기준) |
| 13 | `symptom_code` | `id, code, name, parent_id` | 4 | ✅ `symptom_code.csv` | 자기참조. 4행(`SPEC.md` §6-2 수치와 일치) |
| 14 | `cause_code` | `id, code, name, parent_id` | 4 | ✅ `cause_code.csv` | 자기참조. 6행(`SPEC.md` §6-2 수치와 일치) |
| 15 | `alias` | `text, target_kind, target_id, scope_hull_id, source` | 5 | ✅ `alias.csv` | 별칭 사전. 14행(`SPEC.md` §6-2 수치와 일치). **CSV 헤더가 정본** — 원본 `docs/03`은 `id`·`created_by` 칸도 적었으나 실제 CSV엔 없음(5칸만). `modules/sn_util.py`의 `ensure_sn` 정규화에 걸림(호선 별칭만) |

**정리**: 15종 전부 이 저장소에 CSV 샘플이 반영됐다(2026-11-11, 원본 zip `C:\Users\shiset1\Downloads\meeting-main.zip`의 `data/samples/masters/`에서 10종을 그대로 복사 — 행 수가 `SPEC.md` §6-2 수치와 일치함을 확인). `code-gen`의 시드(S2)가 15종 전부에 대해 경고 없이 돌아갈 수 있는 상태.

---

## §1-2. 운영 표 — v2e-studio 관련분만 (1차)

> 원본 `docs/03`의 `block`(이슈)·`section`·`meeting_candidate` 등 전체 운영 표는 이번 라운드 범위 밖. 여기서는 **v2e-studio 화면이 다루는 "회의자료·슬라이드" 쪽만** `slides[].objs[]`(브라우저 메모리 모델, `v2e-studio.html`)를 DB 표 언어로 옮긴다.

| 테이블 | 주요 칸 | 근거 |
|---|---|---|
| `meeting_deck` | `id, kind(dept/share/exec), issue_id(FK, null 허용), status(draft/submitted), created_at, updated_at` | v2e-studio URL `?kind=dept·share·exec`. `status`는 ㉛(제출) 범위 — "제출됨/초안"만, 서버 상태 전파·잠금 없음(README "제출" 절) |
| `deck_slide` | `id, deck_id(FK), seq(정수, 순서), form(cover/line/card/... — `FORMS` 딕셔너리 키), hull_text, issue_id(FK, null 허용)` | `slides[]`의 `id·form·hullText·issueId`. `seq`는 바닥띠 "n / total" 재계산(`syncFooters()`)의 근거 — 슬라이드 삭제·추가 때마다 전체 재계산 |
| `slide_object` | `id, slide_id(FK), type(strip/text/image/shape), locked(bool), z_order(정수), x, y, w, h, props(JSON)` | `objs[]`. `objs[0]`=머리띠, `objs[1]`=바닥띠 불변식은 `locked=true` + `z_order` 최솟값 2개로 표현(코드처럼 배열 인덱스에 의존하지 않는다 — DB에는 순서 보장이 없기 때문) |

**props 설계**: 지금은 JSON 통칸으로 둔다(인터뷰 2026-11-11 확정). 타입별 칸(텍스트 서식·이미지 필터·도형 색 등)으로 쪼갤지는 `code-gen` S1(모델) 구현 시점에 결정 — v2e-studio README "개체 타입"·"편집 가능한 개체" 표(각 타입별 속성 목록)가 그 쪼갤 칸의 근거가 된다.

### §1-2-2. 나머지 운영 표 (2026-11-12 채움)

> 근거는 원본 `docs/03_데이터모델.md` §3. **표 이름·칸 이름을 원본 그대로 쓴다** — 바꿀 이유가 없고,
> 원본 기획서·화면 설계가 전부 이 이름으로 적혀 있다. 아래는 **1차 범위**만이다.
> 어느 슬라이스가 쓰는지 표시했다.

**원천·작성 (S6 기록함 · S5 이슈 원장)**

| 표 | 주요 칸 | 쓰는 곳 |
|---|---|---|
| `week` | `id`(`2026-W42` ISO 주차), `start_date`, `end_date` | 전부 |
| `section` | `id`, `week_id`, `department_id`, `status`, `confirmed_by`, `confirmed_at` | S6. 주차×부서 1행. **확정 개념은 M12에서 없앴다** — `status`는 옛 기록으로만 남고 아무것도 잠그지 않는다 |
| `memo` | `id`, `section_id`, `author_id`, `raw_text`, `created_at`, `revises_id` | S6. **수정 금지.** 원문을 고치면 새 행을 만들고 `revises_id`로 앞 판을 가리킨다 (`CLAUDE.md` §6-1) |
| `block` | `id`, `block_type`(share/problem/issue/dashboard), `title`, `body`, `status`, `owner_department_id`, `created_week_id`, `valid_until`, `origin`, `created_by`, `draft_state`(none/wip/ok), `cause_text`, `action_text`, `decision_needed`, `important`, `due_event`, `due_date`, `alert_days`, `alert_off_reason`, `alert_off_at`, `alert_off_date` | **S5의 중심.** 이관해도 `id`는 그대로, `owner_department_id`만 바뀐다 |
| `section_block` | `section_id`, `block_id`, `order_no`, `carried_over` | S5. 어느 주차 섹션에 실렸는지 |
| `block_history` | `id`, `block_id`, `week_id`, `department_id`, `status`, `note`, `created_at` | S5. 주차별 진행 한 줄 (F4) |
| `source_span` | `id`, `block_id`, `field`, `memo_id`, `start`, `end`, `quote` | S6. 근거 구간 (`CLAUDE.md` §6-3) |
| `ai_field_log` | `id`, `block_id`, `field`, `ai_value`, `human_value`, `model`, `created_at` | S6. AI 값과 사람 값 (§6-2) |
| `closure` | `id`, `block_id`, `action_text`, `requested_by`, `requested_week_id`, `decision`, `decided_week_id`, `decided_at` | S5·S7. 종결 요청·승인 (F13) |

**태그 (S5 — F3 지식 매핑)**

| 표 | 주요 칸 | 비고 |
|---|---|---|
| `block_tag` | `id`, `block_id`, `kind`, `target_id`, `raw_text`, `confidence`, `confirmed`, `confirmed_by`, `dismissed` | `kind`: hull · installed_equipment · system · component · test_item · symptom · cause · owner_person · next_action. `target_id`가 비고 `raw_text`만 있으면 **미연결**. 사람이 고르면 채우고 `alias`에 더한다 |
| `block_table` | `id`, `block_id`, `title`, `rows_json`, `order_no`, `updated_at` | 이슈에 붙인 표. 최대 20행 × 8열 |

**회의 (S7 회의자료 · S8 발행)**

| 표 | 주요 칸 | 비고 |
|---|---|---|
| `meeting` | `id`, `week_id`, `held_at`, `chair_id`, `kind`(dept/share/exec/hull/review), `title`, `owner_dept_id`, `held_on`, `status`, `start_mode`, `version`, `hull_id`, `order_json` | 부서 자료는 「제출」, 나머지는 「발행」 |
| `meeting_version` | `id`, `meeting_id`, `version`, `published_at`, `snapshot_json` | 판 고정. 회의에서 본 그대로 남는다 |
| `report_item` | `id`, `meeting_id`, `kind`(single/summary/metric/table), `block_id`, `line`, `tag_on`, `form`, `order_no`, `src`, `created_at`, `dept_id`, `table_id` | **표현은 여기, 사실은 `block`에.** 이 경계가 F8(사실 되먹임)의 전제다 |
| `report_item_block` | `item_id`, `block_id`, `order_no` | 요약 장이 잇는 이슈들 (F7) |
| `meeting_comment` | `id`, `meeting_id`, `block_id`, `text`, `author_id`, `kind`(comment/decision), `created_at` | 회의 진행 기록 (F12) |
| `directive` | `id`, `meeting_id`, `block_id`, `dept_id`, `text`, `due_week_id`, `status`, `done_note`, `done_week_id`, `created_at` | 지시사항 (F20) |

**지식 (S9)**

| 표 | 주요 칸 |
|---|---|
| `case_card` | `id`, `block_id`, `symptom_text`, `cause_text`, `action_text`, `symptom_code_id`, `cause_code_id`, `installed_equipment_id`, `approved_week_id`, `validity`, `view_count` |
| `block_link` | `from_block_id`, `to_block_id`, `relation`(재발/동일원인/관련/참고) |

**사람**

| 표 | 주요 칸 | 비고 |
|---|---|---|
| `person` | `id`, `name`, `department_id` | 역할 전환은 **표시용 분기**다. 로그인·인증을 만들지 않는다 (`CLAUDE.md` §9) |

### §1-2-3. 1차에 넣지 않는 표 — 범위 결정이 필요하다

아래는 원본에 있지만 **이번 라운드 범위를 정하지 않았다.** §2에서 결정한다.

| 묶음 | 표 | 왜 미뤘나 |
|---|---|---|
| 사진 | `photo`, `photo_link`, `annotation`, `marker` | F5 「상세 한 장」에 사진이 들어간다. `streamlit_drawable_canvas`가 사외망에서 막힐 수 있어 강등 경로(좌표 수동 입력)가 전제다 |
| 지표 | `metric_def`, `metric_value`, `metric_table`, `metric_cell`, `app_setting` | F16. 회의자료의 「지표 요약」·「기간 표」 장이 여기 걸린다 |
| 외부 자료 | `import_job`, `import_piece`, `meeting_candidate` | F14·F22. **메일 수집은 Outlook이 필요해 사외망에서 못 만든다** (`code-gen.md` §3) |
| 운영 로그 | `llm_call_log` | 본문은 저장하지 않는다 |

---

## §1-3. 화면·기능 F1~F23 배정 — v2e-studio 관련분만 (1차)

> 전체 F1~F23 정의는 원본 `docs/07_기능_업무흐름_기획서.md` §4 참고(참조용). 아래는 v2e-studio가 실제로 걸치는 F번호만 뽑아, `mockups/README.md`의 "구현 범위 현황"·1차/2차 분류를 그대로 승계해 적는다.

| F | 기능 | v2e-studio가 다루는 부분 | 1차/2차 범위 (README 기준) | 슬라이스 |
|---|---|---|---|---|
| F5 | 1차 초안 | **v2e-studio와 별개 화면·별개 데이터**(인터뷰 2026-11-11 확정). 이슈 작업대(`v2s-issue.html`/`v2m-issue-desk.html`)에서 이슈 1건 단위로 초안 레이아웃을 생성하는 기능 — 작성자가 자기 이슈를 처음 쓸 때 쓴다. v2e-studio의 "형태 전환"은 이름만 같고 대상이 회의자료 슬라이드 1장이라 F5가 아니라 F6에 속한다 | 1차 보완(㉘) | S5(이슈) `views/ledger.py` — S7(회의자료)과는 경계가 분리된 별개 코드 |
| F6 | 회의자료 구성 | v2e-studio의 핵심 — 슬라이드 추가·삭제(㉔ ✅)·순서(썸네일 드래그, ㉗ 미구현)·형태 전환. 이슈 후보 패널(㉜, 1차 보완)로 "후보 이슈 → 슬라이드" 연결 예정 | 1차 필수(㉔ 완료) + 1차 보완(㉗㉜㉝) | S7 `views/meeting.py`. **F5와 경계: 별개** — F6의 형태 전환은 회의자료 슬라이드 전용 코드, F5의 초안 생성과 공유하지 않는다 |
| F7 | 요약 항목 | 여러 슬라이드(이슈)를 한 장으로 요약 — 옛 `v2b/v2m-studio`에는 있었으나 v2e-studio 명세에서 빠졌던 기능. **회귀로 판단해 ㉝으로 "구현 범위 현황"에 재등록, 1차 보완 대상에 포함**(인터뷰 2026-11-11 확정) | 1차 보완(㉝ 신설) | S7 |
| F8 | 사실 되먹임 | 슬라이드에서 고친 사실(원인·조치·결정 등)이 이슈 원장에 반영 | 2차(서버 구현 필요) — README "이슈 연결(양방향)" 절 | S7 |
| F9 | 부서 제출 | v2e-studio ㉛ "제출" — 헤더 버튼, **상태 표시만**(제출됨/초안). 마감 시각·경고·재제출 등 F9 전체 규칙은 포함 안 함 | 1차 보완(㉛, 상태표시만) — 나머지는 2차로 이미 확정(README 기준, 범위 변경 없음) | S7 |
| F11 | 발행·PPT | README "구현 파일" 절에 `.pptx` 내보내기 언급 없음 — v2e-studio는 "발표 모드"(풀스크린 ←/→)만 ✅, 실제 `.pptx` export는 `code-gen` 슬라이스 순서상 S8에서 다룬다 | 발표 모드 1차 완료(⑫) / PPT export는 S8에서 구현(F11 범위에 포함, README 슬라이스 표 기준) | S8 `pptx_export.py` |

### §1-3-2. 나머지 F 배정 (2026-11-12 채움)

> 근거는 원본 `docs/07_기능_업무흐름_기획서.md` §4. 위 표(§1-3)는 v2e-studio 시안이 걸치는 F만
> 자세히 적은 것이고, 아래는 **전체 23개를 슬라이스에 배정**한 것이다.
> "사외망"은 지금 저장소에서 만들 수 있는지를 말한다.

| F | 기능 | 슬라이스 | 사외망 | 비고 |
|---|---|---|---|---|
| F1 | 메모 AI 정리 | S6 기록함 | ○ | LLM 창구는 S3에 있다. 사내 LLM 설정이 없으면 수동 입력으로 떨어진다 |
| F2 | 이슈 원장 | **S5** | ○ | 데이터 그리드. `st_aggrid` 없으면 `st.data_editor`로 강등 (§4⑦) |
| F3 | 지식 매핑 | **S5** | ○ | 별칭 사전 + `ensure_sn`. 둘 다 있다 |
| F4 | 주간 업데이트 | **S5** | ○ | `block_history` 한 줄 |
| F5 | 1차 초안 | **S5** | △ | 사진이 들어간다 — 사진 표 범위 결정 필요(§2) |
| F6 | 회의자료 구성 | S7 | ○ | v2e-studio 시안의 핵심 (§1-3) |
| F7 | 요약 항목 | S7 | ○ | 회귀로 재등록된 기능 (§1-3) |
| F8 | 사실 되먹임 | S7 | ○ | **2차.** 표현(`report_item`)과 사실(`block`)의 경계가 전제다 |
| F9 | 부서 제출 | S7 | ○ | 1차는 **상태 표시만**. 마감·경고는 2차 (§1-3) |
| F10 | 취합 | S7 | ○ | 제출본을 **참조로** 가져온다(복사 아님) |
| F11 | 발행·PPT | S8 | ○ | `python-pptx` 설치돼 있다 |
| F12 | 회의 진행 | S7 | ○ | `meeting_comment`. 결정을 남기면 `decision_needed`를 비운다 |
| F13 | 종결·사례화 | S7 + S9 | ○ | 승인하면 `case_card` 생성 |
| F14 | 외부 자료 가져오기 | — | △ | **2차.** `.pptx`·`.html`은 사외망에서도 되지만 메일(F22)과 묶여 있다 |
| F15 | 지식 검색 | **S9** | ○ | 답은 사례 카드 ID를 반드시 인용 (`CLAUDE.md` §6-3) |
| F16 | 지표 | S7 | ○ | 지표 표 범위 결정 필요(§2). 회의자료의 「지표 요약」 장이 여기 걸린다 |
| F17 | 호선 연계 | S2·S4 | **×** | 중앙 `pjtlist`·`milestone` — 사내망 전용. 사외망에서는 §1-4의 샘플 CSV로 대신한다 |
| F18 | 설정 | **S4 ✅** | ○ | 완료 (2026-11-12). 기준정보 15종 CRUD·재시드 |
| F19 | 홈 | **S10** | ○ | 마지막. 앞 슬라이스가 다 있어야 숫자를 센다 |
| F20 | 지시사항 | S7 | ○ | `directive`. 다음 주 부서 자료 맨 위에 자동 등장 |
| F21 | 일정 경보 | S5 | **×** | 「~전 해결」 목표가 `milestone` 날짜에 걸린다 (`SPEC.md` §10). 사외망에서는 샘플로 |
| F22 | 메일 수집 | — | **×** | Outlook 폴더를 읽는다. 사외망 금지 (`code-gen.md` §3) |
| F23 | 일괄 정리 | **S5** | ○ | 원장 그리드에서 여러 건 한꺼번에 |

**S5(이슈 원장)가 가장 무겁다** — F2·F3·F4·F5·F21·F23 여섯 개가 몰려 있다.
**사외망에서 못 만드는 것은 F17·F21·F22 셋**이고, 앞의 둘은 `milestone` 샘플 CSV로 대신할 수 있다.
F22는 사내망 고정본(P5)에서만 가능하다.

---

## §1-4. 사내 시스템 미러 표 — `milestone`

> **기준정보 15종(§1-1)에도 운영 표(§1-2)에도 넣지 않는다.** 우리가 만드는 표가 아니라
> 사내 `data_manager`가 내보내는 것을 **그대로 받는 표**이기 때문이다. 15종이라는 수와
> 소문자 스네이크 칸 이름 규칙이 §1-1에만 적용되도록 자리를 따로 둔다.
> 근거와 계산 규칙은 `SPEC.md` §10.

**무엇에 쓰나** — `hull.stage`(안벽기간·시운전기간·앵카링기간·Layup·인도선)를 **계산**한다. `stage`는 사람이 고르는 값이 아니라 이 표에서 나오는 파생 값이다.

| | |
|---|---|
| 출처 | `data_manager`의 `milestone.parquet` (운영 MySQL `pjtevnt` 미러) |
| 모양 | **wide 그대로. unpivot 하지 않는다** |
| 키 | `project` — 호선번호. `ensure_sn` 적용돼 있어 우리 `hull.id`와 같은 값이고 **이름만 다르다** |
| 칸 | `PLAN<EVT>` 계획일 · `PROS<EVT>` 예정일(전망) · `PERF<EVT>` 실적일 — 17 이벤트 × 3계열 = 51칸 + 키 = **52칸** |
| 이벤트 17종 | `LC` · `SP` · `BT` · `GT` · `CMR` · `ACFROM`/`ACTO` · `COLDFROM`/`COLDTO` · `IE` · `MT` · `GASFROM`/`GASTO` · `STFROM`/`STTO` · `WF` · `DL` |

**칸 이름은 헤더 그대로 쓴다** (`SPEC.md` §9-A). 사내망 전환 때 헤더 값만 매칭하면 되도록.

**함께 읽어야 하는 것** — `Layup` 경계에 `pjtlist.WORKFINISH`(공사 완료일)가 필요하다. `pjtlist`는 우리 `hull`의 실데이터 출처이기도 하다 (`SHIPNUM`↔`id`, `SEQNO`↔`series_no`, `MAINHULLNUM`↔`sister_group_id` 등).

**사외망에서는** 이 표를 샘플 CSV로 대신한다. 사내망 전환 지점이다.

**선언 시점** — `modules/models.py`에는 **S1에서 넣지 않는다.** S1의 완료 판정이 "선언된 표가 15개"이고, 이 표는 기준정보가 아니다. 실제로 읽어 `stage`를 계산하는 **S2(DB·시드) 또는 S4(설정 화면)**에서 넣는다.

---

## §2. 정해야 할 것 (확인 필요 목록)

> 2026-11-12에 **운영 표(§1-2-2)와 F 배정(§1-3-2)을 채웠다.** 아래는 그러면서 남은 결정이다.
> 급한 순서로 적었다 — 1번이 다음 슬라이스(S5)를 막는다.

**1. 사진 표 4종을 1차에 넣는가** — *S5를 막는다*

`photo` · `photo_link` · `annotation` · `marker`. **F5(1차 초안)의 「상세 한 장」에 사진이 들어간다.**
넣기로 하면 `streamlit_drawable_canvas`가 사외망에서 막힐 수 있어 **강등 경로**(`st.image` + 좌표 수동 입력,
`code-gen.md` §4⑦)가 전제다. 빼기로 하면 F5는 글만 있는 초안이 된다.

마킹을 사진 위에 굽지 않고 **좌표 JSON으로 따로 저장**한다는 원칙(`CLAUDE.md` §6-1)은 어느 쪽이든 유지된다.

**2. 지표 표 5종을 1차에 넣는가** — *S7을 막는다*

`metric_def` · `metric_value` · `metric_table` · `metric_cell` · `app_setting`. F16이고,
회의자료의 「지표 요약」·「기간 표」 **장(`report_item.kind` = metric/table)**이 여기 걸린다.
빼면 그 두 장이 회의자료에서 빠진다.

**3. `slide_object.props`를 타입별 칸으로 쪼개는가** — *S7*

JSON 통칸 유지는 2026-11-11에 확정했다. 쪼갠다면 세부 칸 목록이 필요하고,
근거는 v2e-studio README의 「개체 타입」·「편집 가능한 개체」 표다.
*원래 "S1에서 결정"이라고 적어 뒀는데, `slide_object`는 기준정보가 아니라 운영 표라 S1에서 다루지 않았다.
실제로 쓰는 **S7 전에** 정하면 된다.*

**4. 외부 자료 가져오기(F14)를 2차로 확정하는가** — *범위*

`.pptx`·`.html` 조각내기는 사외망에서도 되지만, 메일 수집(F22)과 한 묶음으로 설계돼 있고
F22는 Outlook이 필요해 사외망에서 못 만든다. **F14만 떼어 1차에 넣을지**, 둘 다 2차로 둘지.

---

**결정이 필요 없는 것** (이미 정해져 여기 적지 않는다)

- 표 이름·칸 이름은 원본 `docs/03` 그대로 쓴다 (`SPEC.md` §9-A와 같은 이유)
- `block`의 ID 접두어는 최초 등록 유형으로 발급하고, 유형이 바뀌어도 **ID를 바꾸지 않는다**
- `section`의 「확정」 개념은 M12에서 없앴다 — `status`는 옛 기록일 뿐 아무것도 잠그지 않는다
- 역할 전환은 표시용 분기다. 로그인·인증·세션 토큰을 만들지 않는다
