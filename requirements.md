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
| 10 | `installed_equipment` | `id, hull_id, equipment_model_id, system_id, name, unit_no, position` | 7 | ✅ `installed_equipment.csv` | 호선별 탑재 장비. 7행 — 진행 호선만 남기면서 끊긴 참조 4행을 뺐다(`SPEC.md` §6) |
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
| ~~`meeting_deck`~~ → **`meeting`** (§1-2-2) | — | **2026-11-13 결정: 회의자료는 `meeting` 하나로 만든다.** `meeting_deck` 은 쓰지 않는다. v2e-studio URL 의 `?kind=dept·share·exec` 는 `meeting.kind` 로 읽고, 시안의 「제출」은 `meeting.status` 다. 판(`version`)·호선 회의·취합이 `meeting` 에만 있어 F8·F10 이 여기서만 선다 |
| ~~`deck_slide`~~ → **`report_item`** (§1-2-2) | — | **2026-11-13 결정 D: 회의자료의 한 장은 `report_item` 하나다.** 원본 `docs/03` 이 그 표를 「회의자료의 한 장」이라고 적어 두었고, 형태(`form`)·순서(`order_no`)·요약(`kind=summary` + `report_item_block`)·지표·기간 표가 이미 거기 달려 있다. 시안의 `slides[].id·form·hullText·issueId` 는 각각 `report_item.id·form·(호선 태그에서 그린다)·block_id` 로 읽는다 |
| ~~`slide_object`~~ | — | **선언하지 않는다** (결정 D). 시안 v2e-studio 의 `objs[]`(1920×1080 절대 좌표·색·격자)는 **자유 캔버스 편집기**의 모형이다. Streamlit 에는 끌어서 놓는 캔버스가 없고(디자인_규칙 §3), 시안 자신도 저장·요약·제출이 미구현이다. 「편집 가능한 PPT」는 **S8 에서 `.pptx` 로 내보내 파워포인트에서 고치는 것**으로 푼다 (`CLAUDE.md` §1) |

> **그래서 1차 회의자료는 「틀을 고르고 값을 고치는」 화면이다.** 사람이 글상자를 끌어 옮기지 않는다.
> 시안 v2e-studio 의 자유 캔버스 편집기는 **다음에 만든다** — 버리는 것이 아니라 뒤로 미룬 것이다 (§1-2-3).
> 시안의 머리띠·바닥띠(잠금 개체)·쪽수 자동 계산은 **출력 틀**이 하는 일로 넘어간다 (S8).

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
| `block` | `id`, `block_type`(share/problem/issue/dashboard), `title`, `body`, `status`, `owner_department_id`, `created_week_id`, `valid_until`, **`occurred_on`**(2026-11-13 추가 — 일이 난 날. 적은 날이 아니다. 그 날의 호선 단계를 잡는 데 쓴다, §2-C), `origin`, `created_by`, `draft_state`(none/wip/ok), `cause_text`, `action_text`, `decision_needed`, `important`, `due_event`, `due_date`, `alert_days`, `alert_off_reason`, `alert_off_at`, `alert_off_date` | **S5의 중심.** 이관해도 `id`는 그대로, `owner_department_id`만 바뀐다 |
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
| `meeting` | `id`, `week_id`, `held_at`, `chair_id`, `kind`(dept/share/exec/hull/review), `title`, `owner_dept_id`, `held_on`, `status`, `start_mode`, `version`, `hull_id`, `order_json` | 부서 자료는 「제출」, 나머지는 「발행」. **값 어휘**(2026-11-13 결정 K, 원본 `docs/03` 그대로): `status` = **구성 중 / 제출 / 수정됨 / 발행 / 종료** — **1차에 쓰는 것은 「구성 중」·「제출」 둘**, 「수정됨」·「발행」은 **S8**, 「종료」는 회의 뒤. `start_mode` = **`carry` / `blank`** (화면에 보이는 말은 「이어받기」·「빈 자료」) |
| `meeting_version` | `id`, `meeting_id`, `version`, `published_at`, `snapshot_json` | 판 고정. 회의에서 본 그대로 남는다. **공유회는 부서 자료의 최신 제출판(`snapshot_json`)을 참조로 싣는다** — F10 (결정 H, §1-3-2 주). **`snapshot_json` 이 담는 키**(결정 K) — `ID` · `번호` · `종류` · `형태` · `제목` · `한 줄` · `이슈` · `상태` · `머리표` + 사실 4키(`현상` · `원인` · `조치` · `결정 필요`). 표의 칸이 아니라 **`Text` 칸 하나 안의 JSON 값**이다. **S8(PPTX)이 이 키를 읽는다** — 사실상의 계약이라 키 이름을 바꾸면 S8 이 깨진다 |
| `report_item` | `id`, `meeting_id`, `kind`(single/summary/metric/table), `block_id`, `line`, `tag_on`, `form`, `order_no`, `src`, `created_at`, `dept_id`, `table_id` | **표현은 여기, 사실은 `block`에.** 이 경계가 F8(사실 되먹임)의 전제다 — **장에서 사실을 고치면 `block` 이 바로 바뀐다(1차)**, 발행 뒤 「변경」 표시·양방향은 2차 (결정 F). **`src` = 참조한 제출판 장의 `id`**(F10 취합) — 2026-11-13 결정 J. `kind` 값 어휘 = **single / summary / metric / table** — 1차는 **single·summary**, `metric` 은 **S7-b**, `table` 은 **2차** (결정 K) |
| `report_item_block` | `item_id`, `block_id`, `order_no` | 요약 장이 잇는 이슈들 (F7) |
| `meeting_comment` | `id`, `meeting_id`, `block_id`, `text`, `author_id`, `kind`(comment/decision), `created_at` | 회의 진행 기록 (F12). `kind` 값 어휘 = **comment / decision** (결정 K) |
| `directive` | `id`, `meeting_id`, `block_id`, `dept_id`, `text`, `due_week_id`, `status`, `done_note`, `done_week_id`, `created_at` | 지시사항 (F20). **낸 주차부터** 「지난 지시사항」에 — **열림 + 이번 주 완료** (결정 I). `status` 값 어휘 = **열림 / 완료** (결정 K) |

**지식 (S9)**

| 표 | 주요 칸 |
|---|---|
| `case_card` | `id`, `block_id`, `symptom_text`, `cause_text`, `action_text`, `symptom_code_id`, `cause_code_id`, `installed_equipment_id`, `approved_week_id`, `validity`, `view_count` |
| `block_link` | `from_block_id`, `to_block_id`, `relation`(재발/동일원인/관련/참고) |

**사진 (S5 — F5 「상세 한 장」)** — 2026-11-12 결정으로 **4종 전부 1차**

| 표 | 주요 칸 | 비고 |
|---|---|---|
| `photo` | `id`, `file_path`, `sha256`, `width`, `height`, `taken_at`, `uploaded_by` | **원본 불변** (`CLAUDE.md` §6-1). 경로는 데이터 폴더 기준 `photos/<sha 앞 2자>/<sha>.<확장자>`, `width`·`height`는 EXIF 회전 적용 크기 |
| `photo_link` | `photo_id`, `block_id`, `role`(main/before/after), `order_no`, `caption`, `note` | 한 사진을 여러 블록에. 같은 구분에 여러 장 가능 |
| `annotation` | `id`, `photo_id`, `block_id`, `shapes_json`, `updated_at` | **사진 위에 굽지 않고 좌표 JSON으로 따로 저장한다.** 출력할 때만 합성 |
| `marker` | `id`, `annotation_id`, `no`, `x`, `y`, `label`, `component_id` | 번호 마커 → 부위 태그 → 사진 검색 |

> **강등 경로가 전제다.** `streamlit_drawable_canvas`가 사외망에서 막힐 수 있다 (`code-gen.md` §4⑦).
> 없으면 `st.image` + 좌표 수동 입력으로 떨어진다. 어느 쪽이든 저장되는 것은 **좌표 JSON**이라 모델은 같다.
> `config/paths.py`에 사진 폴더(`photos/`) 창구를 더해야 한다 — S5에서 한다.

**지표 (S7-b — F16)** — 2026-11-12 결정으로 **주간 지표만 1차**, 2026-11-13 결정 G로 **S7 에서 떼어 낸 별 슬라이스**

| 표 | 주요 칸 | 비고 |
|---|---|---|
| `metric_def` | `id`, `department_id`, `name`, `unit`, `order_no`, `normal_low`, `normal_high`, `hidden` | 지표 정의. 숨겨도 값은 남는다 |
| `metric_value` | `id`, `metric_def_id`, `week_id`, `value`, `comment`, `block_id`, `human` | 주차별 값. **이번 주만 입력.** `human`은 사람이 넣은 값 — AI가 덮지 않는다. `comment`는 차이 사유 |
| `app_setting` | `key`, `value` | 화면에서 바꾸는 업무 설정. `metric_range_weeks`(평소 범위를 잡는 최근 n주, 처음 8) · `alert_days:<이벤트>`(F21 기본 경보 일수, 처음 14) |

> 기간 표(`metric_table`·`metric_cell`)는 **2차**다. 그래서 1차 회의자료에는
> `report_item.kind`의 **`metric`(지표 요약) 장만 있고 `table`(기간 표) 장은 없다.**

> **왜 S7 에서 뗐나** (2026-11-13 결정 G) — 표 3종 + 지표 입력 화면 + 「평소 범위 = 정한 값 또는 최근 n주 평균 ±2σ」
> 계산이 한 덩어리로 딸려 오고, S7(회의자료)은 이미 1,512줄이다. 그 자체로 한 슬라이스라 **S7-b (지표)** 로 가른다.
> 바로 위 줄(「`metric` 장만 있고 `table` 장은 없다」)은 **그대로다** — 「지표 요약」 장은 1차 범위에서
> **빠진 것이 아니라 S7-b 로 미뤄진 것**이고, 「기간 표」 장은 S7-b 에서도 만들지 않는다(2차).

**사람**

| 표 | 주요 칸 | 비고 |
|---|---|---|
| `person` | `id`, `name`, `department_id` | 역할 전환은 **표시용 분기**다. 로그인·인증을 만들지 않는다 (`CLAUDE.md` §9) |

### §1-2-3. 2차로 미룬 표 (2026-11-12 확정)

| 묶음 | 표 | 왜 |
|---|---|---|
| 기간 표 | `metric_table`, `metric_cell` | 주간 지표만 1차로 했다. 회의자료의 「기간 표」 장도 함께 2차 |
| 외부 자료 | `import_job`, `import_piece`, `meeting_candidate` | F14를 F22와 함께 2차로 확정. **메일 수집은 Outlook이 필요해 사외망에서 못 만든다** (`code-gen.md` §3) |
| 운영 로그 | `llm_call_log` | 본문은 저장하지 않는다. 진단으로 충분하다 |
| 슬라이드 편집기 | `deck_slide`, `slide_object` | **2026-11-13 결정 D.** 1차 회의자료는 원본 `docs/03` 그대로 `report_item`(틀을 고르고 값을 고치는 화면)으로 만든다. 시안 v2e-studio 의 **자유 캔버스 편집기는 다음에 만든다** — 버리는 것이 아니다. 그때 `slide_object`(1920×1080 절대 좌표·색·격자)를 더하고, `report_item` 한 장이 그 장의 **사실**을, `slide_object` 가 **배치**를 맡는 식으로 잇는다 |

---

## §1-3. 화면·기능 F1~F23 배정 — v2e-studio 관련분만 (1차)

> 전체 F1~F23 정의는 원본 `docs/07_기능_업무흐름_기획서.md` §4 참고(참조용). 아래는 v2e-studio가 실제로 걸치는 F번호만 뽑아, `mockups/README.md`의 "구현 범위 현황"·1차/2차 분류를 그대로 승계해 적는다.

| F | 기능 | v2e-studio가 다루는 부분 | 1차/2차 범위 (README 기준) | 슬라이스 |
|---|---|---|---|---|
| F5 | 1차 초안 | **v2e-studio와 별개 화면·별개 데이터**(인터뷰 2026-11-11 확정). 이슈 작업대(`v2s-issue.html`/`v2m-issue-desk.html`)에서 이슈 1건 단위로 초안 레이아웃을 생성하는 기능 — 작성자가 자기 이슈를 처음 쓸 때 쓴다. v2e-studio의 "형태 전환"은 이름만 같고 대상이 회의자료 슬라이드 1장이라 F5가 아니라 F6에 속한다 | 1차 보완(㉘) | S5(이슈) `views/ledger.py` — S7(회의자료)과는 경계가 분리된 별개 코드 |
| F6 | 회의자료 구성 | v2e-studio의 핵심 — 슬라이드 추가·삭제(㉔ ✅)·순서(썸네일 드래그, ㉗ 미구현)·형태 전환. 이슈 후보 패널(㉜, 1차 보완)로 "후보 이슈 → 슬라이드" 연결 예정 | 1차 필수(㉔ 완료) + 1차 보완(㉗㉜㉝) | S7 `views/meeting.py`. **F5와 경계: 별개** — F6의 형태 전환은 회의자료 슬라이드 전용 코드, F5의 초안 생성과 공유하지 않는다 |
| F7 | 요약 항목 | 여러 슬라이드(이슈)를 한 장으로 요약 — 옛 `v2b/v2m-studio`에는 있었으나 v2e-studio 명세에서 빠졌던 기능. **회귀로 판단해 ㉝으로 "구현 범위 현황"에 재등록, 1차 보완 대상에 포함**(인터뷰 2026-11-11 확정) | 1차 보완(㉝ 신설) | S7 |
| F8 | 사실 되먹임 | 슬라이드(장)에서 고친 사실(현상·원인·조치·결정 필요)이 이슈 원장에 반영 | **1차**: 장에서 사실을 고치면 **그 이슈(`block`)가 바로 바뀐다.** 표현(한 줄·형태·순서·머리표)은 `report_item` 에만 남는다 / **2차**: 발행 뒤 이슈 사실이 바뀌면 「변경」만 표시하는 것, 그리고 양방향 반영. README 가 "이슈 연결(양방향)"을 2차로 적은 것은 **이 2차 쪽**을 가리키는 말이었다 (2026-11-13 결정 F) | S7 |
| F9 | 부서 제출 | v2e-studio ㉛ "제출" — 헤더 버튼, **상태 표시만**(`meeting.status` 의 「구성 중」·「제출」 — 결정 K. 옛 표현 「제출됨/초안」은 버렸다). 마감 시각·경고·재제출 등 F9 전체 규칙은 포함 안 함 | 1차 보완(㉛, 상태표시만) — 나머지는 2차로 이미 확정(README 기준, 범위 변경 없음) | S7 |
| F11 | 발행·PPT | README "구현 파일" 절에 `.pptx` 내보내기 언급 없음 — v2e-studio는 "발표 모드"(풀스크린 ←/→)만 ✅, 실제 `.pptx` export는 `code-gen` 슬라이스 순서상 S8에서 다룬다 | 발표 모드 1차 완료(⑫) / PPT export는 S8에서 구현(F11 범위에 포함, README 슬라이스 표 기준) | S8 `pptx_export.py` |

### §1-3-2. 나머지 F 배정 (2026-11-12 채움)

> 근거는 원본 `docs/07_기능_업무흐름_기획서.md` §4. 위 표(§1-3)는 v2e-studio 시안이 걸치는 F만
> 자세히 적은 것이고, 아래는 **전체 23개를 슬라이스에 배정**한 것이다.
> "사외망"은 지금 저장소에서 만들 수 있는지를 말한다.

| F | 기능 | 슬라이스 | 사외망 | 비고 |
|---|---|---|---|---|
| F1 | 메모 AI 정리 | S6 기록함 | ○ | LLM 창구는 S3에 있다. 사내 LLM 설정이 없으면 수동 입력으로 떨어진다. **발생일은 메모에서 읽어 미리 채운다** (§2-C) |
| F2 | 이슈 원장 | **S5** | ○ | 데이터 그리드. `st_aggrid` 없으면 `st.data_editor`로 강등 (§4⑦). 한 줄에 **「단계」**(사건 당시 호선 단계, §2-C)가 함께 보인다 |
| F3 | 지식 매핑 | **S5** | ○ | 별칭 사전 + `ensure_sn`. 둘 다 있다 |
| F4 | 주간 업데이트 | **S5** | ○ | `block_history` 한 줄 |
| F5 | 1차 초안 | **S5** | ○ | 사진 4종 1차 확정(2026-11-12). 마킹은 좌표 JSON, `drawable_canvas` 없으면 강등 |
| F6 | 회의자료 구성 | S7 | ○ | v2e-studio 시안의 핵심 (§1-3) |
| F7 | 요약 항목 | S7 | ○ | 회귀로 재등록된 기능 (§1-3) |
| F8 | 사실 되먹임 | S7 | ○ | **한쪽(장 → 이슈)은 1차**, 발행 뒤 「변경」 표시·양방향은 **2차** (결정 F, 아래 주). 표현(`report_item`)과 사실(`block`)의 경계가 전제다 |
| F9 | 부서 제출 | S7 | ○ | 1차는 **상태 표시만**. 마감·경고는 2차 (§1-3) |
| F10 | 취합 | S7 | ○ | 부서 자료의 **최신 제출판**(`meeting_version.snapshot_json`)을 참조로 싣는다 — **복사하지 않는다.** 표현은 판 그대로, 사실(이슈 값)은 지금 값 (결정 H, 아래 주). **1차: 취합은 부서 제출판 → 공유회 한 갈래만.** 팀장 정보회의(`exec`)는 **후보 이슈에서 직접 올린다** — 「공유회에서 가져오기」는 **2차** (결정 L) |
| F11 | 발행·PPT | S8 | ○ | `python-pptx` 설치돼 있다 |
| F12 | 회의 진행 | S7 | ○ | `meeting_comment`. 결정을 남기면 `decision_needed`를 비운다 |
| F13 | 종결·사례화 | S7 + S9 | ○ | 승인하면 `case_card` 생성 |
| F14 | 외부 자료 가져오기 | — | — | **2차 확정**(2026-11-12). F22와 한 묶음으로 미룬다 |
| F15 | 지식 검색 | **S9** | ○ | 답은 사례 카드 ID를 반드시 인용 (`CLAUDE.md` §6-3) |
| F16 | 지표 | **S7-b (지표)** | ○ | **주간 지표만 1차**(2026-11-12). **S7 에서 떼어 낸 별 슬라이스**(2026-11-13 결정 G) — 표 3종(`metric_def`·`metric_value`·`app_setting`) + 지표 입력 화면 + 「평소 범위 = 최근 n주 평균 ±2σ」 계산이 한 덩어리로 딸려 오고, S7(회의자료)은 이미 1,512줄이다. 1차 범위에서 **빠진 것이 아니라 뒤로 간 것**이다. 「지표 요약」 장은 1차, 「기간 표」 장은 2차 |
| F17 | 호선 연계 | S2·S4 | **×** | 중앙 `pjtlist`·`milestone` — 사내망 전용. 사외망에서는 §1-4의 샘플 CSV로 대신한다 |
| F18 | 설정 | **S4 ✅** | ○ | 완료 (2026-11-12). 기준정보 15종 CRUD·재시드 |
| F19 | 홈 | **S10** | ○ | 마지막. 앞 슬라이스가 다 있어야 숫자를 센다 |
| F20 | 지시사항 | S7 | ○ | `directive`. **낸 주차부터** 담당 부서 자료 맨 위 「지난 지시사항」에 등장 — **열림 + 이번 주 완료**를 함께 보인다. 다음 주를 기다리지 않는다 (결정 I, 아래 주) |
| F21 | 일정 경보 | S5 | **×** | 「~전 해결」 목표가 `milestone` 날짜에 걸린다 (`SPEC.md` §10). 사외망에서는 샘플로 |
| F22 | 메일 수집 | — | **×** | Outlook 폴더를 읽는다. 사외망 금지 (`code-gen.md` §3) |
| F23 | 일괄 정리 | **S5** | ○ | 원장 그리드에서 여러 건 한꺼번에 |

> **F8(사실 되먹임)의 1차/2차 경계** (2026-11-13 결정 F)
> - **1차** — 회의자료의 장에서 **사실**(현상·원인·조치·결정 필요)을 고치면 **그 이슈(`block`)가 바로 바뀐다.** 사실이 애초에 `block` 한 군데에만 적히니, 1차에서 따로 만들 「반영」 일거리가 없다. 근거: 원본 `docs/03` `report_item` 줄(M10) — 「표현은 `report_item`, 사실은 `block` 에 — 고치면 이슈에 바로 반영」.
> - **1차** — **표현**(회의용 한 줄·형태·순서·머리표)은 `report_item` 에만 남는다. 장의 표현을 고쳐도 이슈는 건드리지 않는다.
> - **2차** — **발행 뒤** 이슈 사실이 바뀌면 「변경」만 표시하는 것, 그리고 **양방향** 반영. `mockups/README.md` 가 「이슈 연결(양방향)」을 2차로 적은 것은 이쪽을 가리킨다.

> **F10(취합)은 「살아 있는 현재 장」이 아니라 「최신 제출판」을 가리킨다** (2026-11-13 결정 H)
> - 공유회 자료가 싣는 것은 부서 자료의 **최신 제출판** — `meeting_version.snapshot_json` 이다. 부서의 `report_item` 을 공유회로 **복사하지 않는다** (원본 `docs/03` `report_item` M11: 「부서 장은 여기 복사하지 않고 제출판을 참조」).
> - **표현**(한 줄·형태·머리표·순서)은 **판 그대로 굳는다.** 제출 뒤 부서가 자기 장을 고쳐도 — **제출하지 않은 수정은** — 공유회 자료가 흔들리지 않는다.
>   다만 부서가 **다시 제출하면 공유회는 새 판의 표현을 본다.** 「최신 제출판」이기 때문이다. 굳는 것은 **판**이지 **처음 참조한 그 판**이 아니다.
> - **사실**(이슈 값)은 **지금 값**을 따른다. 발행 전까지는 이슈를 고치면 공유회 자료에도 그 값이 보인다 (원본 `docs/03` `meeting_version` 줄).
> - 제출 **뒤에 부서가 더한 장은 취합되지 않는다.** 다음 제출판에 들어간다.

> **F20(지시사항)은 낸 주차부터 보인다** (2026-11-13 결정 I)
> 담당 부서 회의자료 맨 위 「지난 지시사항」에 **낸 주차부터** 올라오고, **열림 + 이번 주 완료**를 함께 보인다.
> 다음 주를 기다리지 않는 이유 — **그 주 안에 공유회가 또 열리면 그 자리에서 바로 보여야 한다.**
> 원본 `docs/03` `directive` 줄(M12)에도 주차 제한이 없다.

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

**함께 받는 표는 둘이다** (2026-11-12 확정)

| 표 | 쓰는 칸 | 무엇에 |
|---|---|---|
| `milestone.parquet` | `project` + `PLAN/PROS/PERF<EVT>` | 시운전·앵카링 구간, 인도일 |
| `pjtlist.parquet` | `SHIPNUM` · `WORKFINISH` | **Layup 의 시작**(공사 완료일). 나머지 칸은 `hull` 이 이미 갖고 있다 |

**사외망에서는** 둘 다 `data/samples/mirror/` 의 샘플 CSV로 대신한다. 사내망 전환 지점이고,
바꿀 곳은 `modules/milestone.py` 의 `_read()` 하나다.

> **샘플은 전체 칸을 담지 않는다.** 사내 `milestone` 은 17 이벤트 × 3계열 = 52칸이지만,
> 샘플에는 **계산에 쓰는 10 이벤트(31칸)만** 넣었다 — `COLD`·`ST`·`GAS`·`AC`·`WF`·`DL`.
> `milestone.events()` 가 칸 이름에서 이벤트를 읽어 내므로 칸이 늘거나 줄어도 그대로 돈다
> (사내 표가 `SELECT *` 라 실제로 늘 수 있다).

**선언 시점** — `modules/models.py`에는 **S1에서 넣지 않는다.** S1의 완료 판정이 "선언된 표가 15개"이고, 이 표는 기준정보가 아니다. 실제로 읽어 `stage`를 계산하는 **S2(DB·시드) 또는 S4(설정 화면)**에서 넣는다.

---

## §2. 정해야 할 것 (확인 필요 목록)

> 2026-11-12 오전에 범위 결정 4건을 닫았는데, 그날 오후 `spec-guard` 검사에서 **두 건이 다시 열렸다.**
> 그 둘은 **2026-11-13에 닫았다**(A~E). 이어서 **S7(회의자료)을 만들면서** `spec-guard` 가
> **문서끼리 어긋나는 곳 네 군데**를 더 찾아 같은 날 **F~I 로 닫았다.**
> 같은 날 `spec-guard` **2차**가 「**칸의 뜻과 값이 어디에도 정본이 없다**」를 짚어 **J~L 로 닫았다** — 칸 이름만 있고 **뜻**(`src`)·**값 어휘**·**취합 갈래**가 어디에도 안 적혀 있어 코드가 제각기 정하고 있었다.
> S7(회의자료)을 막는 결정은 이제 없다.

### 열려 있는 결정

**1차를 막는 것은 없다.**

- **2차에 다시 열린다 — `report_item.src` 의 자리** (결정 J). 2차에서 「**원장 채움**」·「**종결 요청 자동 채택**」 표시가 오면 **`src` 의 자리를 새로 정한다.** 한 칸에 「참조한 제출판 장의 `id`」와 「출처 구분」 **두 뜻을 담을 수 없다**는 것이 까닭이다. **칸을 더할지도 그때 묻는다** (`SPEC.md` §9-A — 칸 추가는 먼저 묻는다).

### 2026-11-13에 정한 것

| # | 결정 | 왜 | 반영 |
|---|---|---|---|
| A | **회의자료는 `meeting` 하나로 만든다.** `meeting_deck` 은 쓰지 않는다 | 판(`version`)·호선 회의·취합이 `meeting` 에만 있다. 판이 없으면 F8(사실 되먹임)·F10(취합)을 세울 수 없다. 표 이름을 원본 `docs/03` 그대로 쓰기로 한 것과도 맞는다 | §1-2 의 `meeting_deck` 줄을 `meeting` 으로 돌림. v2e-studio 의 `?kind=` 는 `meeting.kind`, 시안의 「제출」은 `meeting.status` 로 읽는다. `deck_slide.deck_id` 는 `meeting.id` 를 가리킨다 |
| B | **`hull.stage` 는 볼 때마다 계산한다.** DB 에는 쓰지 않는다 | 일정이 바뀌면 그 자리에서 따라간다. 일정 경보(F21)가 이미 같은 방식이다 — "날짜는 저장하지 않고 볼 때마다 다시 잡는다" | `views/settings.py` `COMPUTED` — 보일 때 `milestone.stage()` 로 그리고, 저장할 때는 DB 값으로 되돌린다. `stage` 칸 잠금은 그대로. `milestone._read()` 에 파일 시각 기준 캐시를 뒀다 |
| C | **`block` 에 발생일(`occurred_on`) 칸을 더하고, 「그때 단계」를 보인다** | 단계는 **언제를 기준으로 보느냐에 따라 달라지는 값**이다. SN2512 는 11-12 에 시운전기간, 11-13 에 안벽기간이다(`STTO` 11-12, `GASFROM` 11-17). 사례로 쌓을 때 중요한 것은 **일이 난 날의 단계**다 | `modules/extract.py` `find_date`·`date_for` 가 메모에서 날짜를 읽어 미리 채우고 근거 구간을 `source_span` 에 남긴다. `issues.stage_at()` 이 (그때, 지금)을 돌려준다. 보이는 곳: 원장 목록 카드(「단계」 칸), 이슈 상세 머리, 상세 「지식 매핑」 탭의 발생일 칸(**호선 옆** — 호선과 발생일이 한 쌍이어야 단계가 잡힌다), 원장 등록 폼. 사례 카드는 S8 에서 같은 함수를 쓴다 |
| D | **회의자료의 한 장은 `report_item` 하나다 — 원본 `docs/03` 그대로.** `deck_slide`·`slide_object` 는 1차에서 선언하지 않고 **다음에 만든다** (§1-2-3) | 원본 `docs/03` 이 `report_item` 을 「회의자료의 한 장」으로 정의하고 형태·순서·요약·지표·기간 표를 거기 달아 뒀다. F7(요약)·F8(사실 되먹임)·F10(취합)·F12·F13 이 전부 그 표에서 선다. 시안 v2e-studio 의 개체 모형은 **자유 캔버스**인데, Streamlit 에 끌어서 놓는 캔버스가 없고 시안 자신도 저장·요약·제출이 미구현이다 | §1-2 의 두 줄을 `report_item` 으로 돌림. 1차 회의자료는 **틀을 고르고 값을 고치는** 화면이다. 「편집 가능한 PPT」는 S8 의 `.pptx` 내보내기로 푼다 |
| E | **장 순서는 「↑ 위로 · ↓ 아래로」 버튼으로 바꾼다** | 시안의 썸네일 끌어 놓기는 Streamlit 기본 위젯에 없다 (`docs/디자인_규칙.md` §3 이 S7 에서 정하기로 미뤄 둔 것) | 디자인_규칙 §3 「순서 바꾸기」 칸 확정 |
| F | **F8(사실 되먹임)은 1차다.** 회의자료의 장에서 사실(현상·원인·조치·결정 필요)을 고치면 **그 이슈(`block`)가 바로 바뀐다.** 표현(한 줄·형태·순서·머리표)은 `report_item` 에만. **2차는** 발행 뒤 이슈 사실이 바뀌면 「변경」만 표시하는 것, 그리고 양방향 반영 | 원본 `docs/03` `report_item` 줄(M10)이 「표현은 `report_item`, 사실은 `block` 에 — **고치면 이슈에 바로 반영**」이라 적어 두었다. 사실이 `block` 한 군데에만 있으니 1차에서 따로 만들 일거리가 없다. `mockups/README.md` 가 「이슈 연결(양방향)」을 2차로 적은 것은 **양방향·발행 후**를 가리키는 말이었다 | §1-3 F8 줄과 §1-3-2 F8 줄을 1차/2차로 **가름**(지우지 않았다) + §1-3-2 표 아래 주. §1-2-2 `report_item` 비고에 「1차」 표시 |
| G | **F16(지표)은 S7 이 아니라 S7-b (지표) 다.** 슬라이스를 가르는 것이고 **범위는 그대로** | 표 3종(`metric_def`·`metric_value`·`app_setting`) + 지표 입력 화면 + 「평소 범위 = 최근 n주 평균 ±2σ」 계산이 한 덩어리인데, S7(회의자료)은 이미 1,512줄이다. 그 자체로 한 슬라이스다 | §1-2-2 「지표」 묶음 머리와 §1-3-2 F16 의 슬라이스 칸을 **S7-b (지표)** 로. **§1-2-2 끝줄(「`metric` 장만 있고 `table` 장은 없다」)은 그대로 뒀다** — 1차 범위에서 빠진 것이 아니라 S7-b 로 미뤄진 것이다 |
| H | **F10(취합)은 부서 자료의 「최신 제출판」을 가리킨다.** 표현은 판 그대로 굳고(**제출하지 않은 수정은 따라오지 않는다. 다시 제출하면 새 판의 표현을 본다**), 사실(이슈 값)은 지금 값. 제출 뒤에 더한 장은 취합되지 않는다 | 「제출본을 참조로 가져온다(복사 아님)」가 **살아 있는 현재 장**으로 읽혀 구현이 어긋났다. 원본 `docs/03` `meeting_version` 줄: 「공유회는 부서 자료의 **최신 제출판**을 참조로 싣고(**표현은 판 그대로, 사실은 발행 전까지 지금 이슈 값**)」, `report_item` 줄(M11): 「부서 장은 여기 복사하지 않고 제출판을 참조」 | §1-3-2 F10 줄을 `meeting_version.snapshot_json` 참조로 또렷하게 고치고, 표 아래에 네 줄 주를 더함. §1-2-2 `meeting_version` 비고에도 한 줄 |
| I | **F20(지시사항)은 낸 주차부터 보인다** — 열림 + **이번 주 완료**를 함께 | 원본 `docs/03` `directive` 줄(M12)에 주차 제한이 없다. **그 주 안에 공유회가 또 열리면 그 자리에서 바로 보여야 한다** — 다음 주까지 기다리면 그 회의에서 지시사항이 빠진다. **원본 `docs/07` 의 『다음 주』 표현은 버렸다** — 같은 자리가 다시 열리지 않게 적어 둔다 | §1-3-2 F20 줄을 「다음 주」 → 「**낸 주차부터**, 열림 + 이번 주 완료」로. §1-2-2 `directive` 비고에도 한 줄 |
| J | **`report_item.src` 는 「참조한 제출판 장의 `id`」다** (F10 취합). 원본 `docs/03` 이 같은 칸에 적어 둔 **출처 구분**(「종결 요청」 자동 채택·「원장 채움」) 쪽 뜻은 **1차에 쓰지 않는다** | 지금까지 `src` 의 뜻이 **어디에도 적혀 있지 않았다** — 그래서 코드가 칸 이름만 지키고 뜻을 제가 정했다. 원본의 「출처 구분」이 딸려 오는 기능(F10 의 「마감 지난 부서는 **원장으로 채우기**」)은 **1차에 없다.** 한 칸에 「참조한 장의 `id`」와 「출처 구분」 두 뜻을 담을 수 없으니, 1차에는 쓰는 쪽 하나만 정본으로 둔다 | §1-2-2 `report_item` 비고에 「`src` = 참조한 제출판 장의 `id`(F10 취합)」. **2차에 「원장 채움」·「종결 요청 자동 채택」 표시가 오면 자리를 새로 정한다 — 열린 채로 둔다**(위 「열려 있는 결정」). 칸을 더할지도 그때 묻는다 |
| K | **값 어휘를 원본 `docs/03` 것으로 정본화한다** — `directive.status`·`meeting.status`·`meeting.start_mode`·`report_item.kind`·`meeting_comment.kind` 다섯 칸 (아래 표) | §1-2-2 의 각 줄에 **값 어휘가 적혀 있지 않아** 문서·원본·코드가 제각각이었다. 칸 이름은 `SPEC.md` §9-A 로 묶여 있었는데 **값은 아무도 묶어 두지 않았다.** 원본 `docs/03` 이 다섯 칸 모두 괄호로 어휘를 적어 두었으니 그쪽을 정본으로 삼는다 | §1-2-2 의 `meeting`·`report_item`·`meeting_comment`·`directive` 비고에 값 어휘를 적음. **§1-3 F9 의 「제출됨/초안」을 `meeting.status` 어휘로 맞춤.** 아래 「K 의 값 어휘 — 정본」 표가 그 정본이다 |
| L | **1차에 취합은 공유회 한 갈래뿐이다** — 부서 제출판 → **공유회**. 팀장 정보회의(`exec`)는 **취합하지 않고 후보 이슈에서 직접 올린다.** 원본이 말한 「공유회 채택분을 가져오기」는 **2차** | 원본 `docs/07` 은 팀장 정보회의 자료를 「**공유회 채택분** + 원장에서 추가」로 적었는데, §1-3-2 F10 은 **무엇을 취합하는지 적지 않았다.** 취합 갈래를 둘로 열면 「공유회 판 → 팀장 회의 판」 참조가 하나 더 생겨 F10 의 판 규칙(결정 H)을 두 번 세워야 한다. 1차는 한 갈래만 세운다 | §1-3-2 F10 줄에 「1차: 취합은 부서 제출판 → 공유회 한 갈래만. 팀장 정보회의는 후보 이슈에서 직접 올린다. 「공유회에서 가져오기」는 2차」 |

> **B 와 C 는 같은 규칙의 두 쪽이다.** 단계는 저장하는 값이 아니라 **날짜를 주면 나오는 값**이다.
> 호선 표는 오늘로 묻고, 이슈는 발생일로 묻는다.

> **A 의 남은 몫은 D 로 닫혔다** (2026-11-13). 「회의자료의 한 장」은 `report_item` 이다.

> **F~I 는 모두 「문서 대 문서」 어긋남이었다** — 시안·README 와 원본 `docs/03` 이 다르게 적힌 자리들이다.
> 네 건 다 **원본 `docs/03` 쪽으로** 정했다: 표 정의에 업무 흐름이 가장 자세히 적혀 있고, 1차/2차를 가르는 근거가 거기 있다.
> **표 이름·칸 이름은 하나도 바뀌지 않았다** (`SPEC.md` §9-A). 바뀐 것은 **설명과 슬라이스 배정**뿐이다.

**K 의 값 어휘 — 정본** (원본 `docs/03` 그대로. 값은 바꿀 수 있지만 **칸 이름·칸 순서는 그대로**다 — `SPEC.md` §9-A)

| 칸 | 값 | 1차에 쓰는 것 |
|---|---|---|
| `directive.status` | **열림 / 완료** | 둘 다 |
| `meeting.status` | **구성 중 / 제출 / 수정됨 / 발행 / 종료** | 「구성 중」·「제출」 둘. 「수정됨」·「발행」은 **S8**, 「종료」는 회의 뒤 |
| `meeting.start_mode` | **`carry` / `blank`** | 둘 다. 화면에 보이는 말은 「이어받기」·「빈 자료」 |
| `report_item.kind` | **single / summary / metric / table** | single·summary. `metric` 은 **S7-b**(결정 G), `table` 은 **2차**(기간 표) |
| `report_item.form` | **detail / card / photo / line** | 넷 다. 원본 `docs/03` 과 코드가 이미 같은 어휘라 **확인만 하고 적는다** (2026-11-13) |
| `block.status` | **신규 / 진행 / 종결요청 / 종결** | 넷 다. **부서가 고를 수 있는 것은 앞 셋**(`issues.ASSIGNABLE_STATUSES`) — 「종결」은 공유회 승인으로만 (`CLAUDE.md` §6-7). S5 때부터 코드에만 있던 어휘라 여기 올린다 |
| `closure.decision` | **승인 / 보류** | 둘 다. **「대기」는 저장 값이 아니다** — 결정이 아직 없을 때 화면에 보이는 말이다 |
| `meeting_comment.kind` | **comment / decision** | 둘 다. `decision` 을 남기면 `block.decision_needed` 를 비운다 |

> **J~L 은 「칸 이름은 있는데 뜻과 값이 없다」였다.** `SPEC.md` §9-A 가 묶어 둔 것은 **이름**이고, **뜻**(`src`)·**값 어휘**·**취합 갈래**는 어디에도 정본이 없어 코드가 대신 정하고 있었다.
> 세 건 다 **원본 `docs/03`·`docs/07` 쪽으로** 정했고, **1차에 쓰지 않는 몫은 2차로 적어 두었다**(J 의 출처 구분, L 의 공유회 → 팀장 회의 취합).
> **표 이름·칸 이름·칸 순서는 한 글자도 바뀌지 않았다.** 바뀐 것은 **비고와 §2** 뿐이다.

### 2026-11-12에 정한 것

| # | 결정 | 반영 |
|---|---|---|
| 1 | **사진 표 4종 전부 1차** — `photo`·`photo_link`·`annotation`·`marker` | §1-2-2 사진. S5 범위가 커진다. `drawable_canvas` 강등 경로와 `config/paths.py`의 사진 폴더 창구가 따라온다 |
| 2 | **주간 지표만 1차** — `metric_def`·`metric_value`·`app_setting` | §1-2-2 지표. 기간 표(`metric_table`·`metric_cell`)는 2차 → 회의자료에 `report_item.kind` **`metric` 장만 있고 `table` 장은 없다** |
| 3 | **`slide_object.props`는 JSON 통칸 유지** | 2026-11-11 확정을 그대로 간다. 쪼개지 않는다 — 개체 타입이 늘어도 표가 바뀌지 않는다. 칸별 조회·검증은 코드에서 |
| 4 | **F14는 F22와 함께 2차** | §1-2-3. 원본 설계의 묶음을 그대로 지킨다 |

---

**결정이 필요 없는 것** (이미 정해져 여기 적지 않는다)

- 표 이름·칸 이름은 원본 `docs/03` 그대로 쓴다 (`SPEC.md` §9-A와 같은 이유)
- `block`의 ID 접두어는 최초 등록 유형으로 발급하고, 유형이 바뀌어도 **ID를 바꾸지 않는다**
- `section`의 「확정」 개념은 M12에서 없앴다 — `status`는 옛 기록일 뿐 아무것도 잠그지 않는다
- 역할 전환은 표시용 분기다. 로그인·인증·세션 토큰을 만들지 않는다
