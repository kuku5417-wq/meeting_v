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

나머지 운영 표(이슈 원장 `block`, 주차별 진행 `block_history`, 회의 `meeting`, 지표 `metric_def`/`metric_table` 등): **미정 — 다음 라운드에 채움**.

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

나머지 F1~F4, F10, F12~F23: **미정 — 다음 라운드에 채움** (v2e-studio 화면과 직접 관련 없음).

---

## §2. 다음 라운드에 할 일 (확인 필요 목록)

1. §1-2의 `props` 타입별 칸 분리 여부 — JSON 통칸 유지는 확정, 분리 시점(S1)에 세부 칸 목록 확정 필요
2. 이슈 원장(F2)·주차별 진행(F4) 등 §1-2 나머지 운영 표 — 다음 라운드에서 `docs/03`(원본) 참고해 채움
