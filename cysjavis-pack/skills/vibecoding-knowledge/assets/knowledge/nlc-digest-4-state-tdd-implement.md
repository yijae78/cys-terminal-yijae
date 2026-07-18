# NLC 다이제스트 (6장 데이터플로우 ~ 10장 실행 · 9~10 자동수행 프롬프트) — 16480~19758행 전 범위 정독 완료

## 전체 파이프라인 위상
저자는 이 구간을 **"기획 → 코드"의 경계선**으로 규정. `requirement/prd/userflow`=인간 사고 정리, `spec.md`=AI·코드 언어 번역, `plan.md/implement`=기계적 실행. 모든 문서 프롬프트는 동일한 **YAML front-matter 계약 골격**을 공유: `SOT`(2종 고정) → `Context`(상속 문서 목록) → `layer`/`identity` → `relation`(parent/next) → `inheritance`(6종 불변: additive-only, override-prohibited, root-sot-priority, uepp-auto, scdp-auto, rcmp-auto, context-propagation-invariant) → `goal`/`rules`/`outputs`/`validation` → `path.output`. layer 번호가 순서 결정(5→7→7.1→7.2→8→8.0→8.1→9→10).

---
## 6. 데이터플로우·스키마 (layer 5, database-design)
- 역할: userflow→dataflow·ERD·tables·migrations. parent=ux.md, next=spec.md. 출력=`/docs/database.md`(+migration SQL은 `/supabase/migrations`).
- 도구: Codex CLI **모델 GPT5-codex 선택** 후 프롬프트. 또는 Google AI Studio(context md '먼저' 입력).
- rules: use_userflow_data_only, model_read_write_delete_only, ui_ux_alignment, logical_model_required.
- validation: no_extra_entities_beyond_userflow, each_flow_has_dataflow_defined, each_entity_used_by_at_least_one_flow, naming_consistency, schema_conformance.
- migration 강조: "명시된 모든 table과 column이 절대 누락되지 않도록 꼼꼼히 점검."
- type B('O to Z', SuperNext 미사용): `@docs/techstack.md 고려해 gitignore 생성` 추가.

---
## 7. 유스케이스(spec) — "바이브코딩의 중추 신경"
### Subagent ① usecase-writer.md
- 경로: `/claude/agents/usecase-writer.md`. front-matter: `name: usecase-writer` / `description: 특정 기능에 대한 Usecase 문서를 /docs/usecases/N-name/spec.md 경로에 생성한다.` / `model: sonnet` / `color: yellow`
- spec 스키마(verbatim): primary_actor, precondition, trigger, main_scenario[], edge_cases[], business_rules[], sequence_diagram{participants:[User,FE,BE,DB], plantuml}
- validation: userflow_alignment, ux_alignment, db_alignment, naming_compliance, schema_conformance. Output=`/docs/usecases/N-name/spec.md`
### 구동 프롬프트 핵심
- userflow 기반 기능단위(Feature-unit)별 유스케이스 생성. 필수 7항목: Primary Actor/Precondition(사용자관점)/Trigger/Main Scenario/Edge Cases/Business Rules/PlantUML Sequence Diagram(User·FE·BE·Database).
- 절차: userflow 읽기→기능별 분리→subagent 호출→N-name/spec.md 저장(자동번호)→완료 시 `/docs/spec.md`(UCS 통합)에 자동 등록.
- ⚠️유의: subagent가 이미 전체 컨텍스트 상속하므로 별도 참조 추가 금지. **"코드가 아닌 행동 기반 명세(Executable Narrative)만."** PlantUML 표준·구분선 없이.
- **검토 프롬프트(spec 이후 모든 단계 반복)**: "언급되지 않은 내용 확대해석 없는지 엄밀 검토… 쓸데없이 추가 개발 절대 금지… 20년차 이상 최고급 시니어 관점 최대한 깐깐하게."
- 저자 강조: 유스케이스=파이프라인 핵심 전환점·기획↔코드 경계선. PRD/Userflow=사람용 기획서, spec=AI/개발자용 코드 스펙화 문서.

---
## 8. 상태관리 설계(필수 단계, layer 7, state-management)
개념 교육 비중이 압도적. 저자가 "필수"로 못박은 근거 집약.
### 왜 필수인가 (State = A Component's Memory)
- **State는 "변수"가 아니라 "기억"**. 기억=책임, 그 책임 경계 정하는 것이 상태관리.
- State 판별: 시간지나도 유지/행동 후 남아야/다음 렌더링 영향 = State. 계산가능하면 State 아님(totalPrice·isMorning·버튼색=derived).
- 상태관리=화면이 언제(Trigger)·왜(Reason/guard)·어떻게(Transition) 변하는지 통제. 큰 서비스일수록 상태머신(FSM)에 근접.
- State는 spec 이후에만 정확히 정의 가능, 행동의 결과(effect), SOT.
### 저자 핵심 경고 — AI 한계
- **"AI는 상태 비슷한 코드는 만들지만, 상태의 경계는 정의하지 못한다."** AI가 망치는 것: 경계·파생/중복 제거·비동기 레이스·이벤트-상태 일관성.
- AI는 SOT 유지 못함(props/local/context/API에 중복된 진실 동시 허용). "하나로 정리 강박이 없다."
- 인간이 할 단 하나: 상태 정의·전이 규칙을 먼저 고정 → AI가 "즉흥 연주자→악보 읽는 연주자". → **"AI는 상태관리를 '한다'기보다 우리가 설계한 상태관리 위에서 '연주한다'."**
- 상태관리 없을 때 5대 치명 문제: ①이유 모름 ②기능추가 시 기존 랜덤 파손 ③디버깅 불가('현상'만 존재) ④AI가 멍청해짐(상태관리=AI 추론 좌표계) ⑤재사용 아닌 '재봉'.
### Flux · Context
- **Flux**: 단방향 `Action→Store→View`. Store=상태변화 유일 장소, View=결과만(결정권 없음). 패턴 아닌 **규율(rule)**·"AI 통제 계약서". AI 학습데이터에 저품질 많아 **인간이 명령해야** 함.
- **Context**: 상태+Flux 공유 메커니즘(props drilling 제거, 로직 중앙화)="상태의 외부 배포 채널". 컴포넌트는 View만. 단점=단순 기능엔 오버엔지니어링, 복잡 화면(에디터·필터·채팅방)엔 반필수.
- 3자 한 문장: **State=기억의 내용, Flux=기억의 법칙, Context=기억의 배포망.**
- 올바른 순서: 1)spec → 2)State 정의 → 3)Flux(같은 문서) → 4)Context. **Context는 항상 마지막.**
### 상태관리 프롬프트(layer 7)
- parent=spec.md, next=page-state-mapping.md, 출력=`/docs/state-management.md`. state_types:[persistent, derived].
- rules: userflow_data_only, classify_source_lifetime_storage, define_trigger_condition_effect, flux_required, store_interface_required, **no_redundant_state**, alignment_ui_ux_db_spec.
- outputs: state_list{name,type,source,lifetime,storage}, change_table, flux_diagrams, stores{name,state,actions,scope}, mapping.
### [참고] 유스케이스↔상태관리 관계
- **State = f(User Action, System Process, Context)** — 상태는 유스케이스(행동)의 함수. 유스케이스=원인(cause), 상태관리=결과(effect).
- 순서 이유: ①정확한 Scope 결정(실제상태vs derived) ②변경조건·사이드이펙트 명확화 ③Flux·Context 자동화.
- 병행 위험: 상태부터→dead state / 동시→race·중복 / 나중합침→async 일관성 오류. 그래서 **"논리상 이후지만 부분적 동시성 갖는 종속 병행 단계"**.

## 8-1. 페이지 상태 매핑 (layer 7.1, page-state-mapping)
- parent=state-management, next=design/visual, 출력=`/docs/page-state-mapping.md`.
- rules: map_state_to_page, classify_scope, provider_tree_required, state_dependency_required, page_implementation_boundary, fds_alignment, ui_ux_alignment, **no_unmapped_state**.
- 저자: spec=무엇을, state-management=어떻게 변하나, page-state=**어디서 일어나나**. "Context Scope가 곧 Page Boundary." 논리상 state-management 포함이나 시간상 동시 설계.

## 8-2. Visual Design (layer 7.2, visual-design)
- parent=page-state-mapping, next=test.md, 출력=`/docs/design/visual.md`. "어떻게 반응하는가?" 구현 디자인 단계.
- rules: fds_compliance, component_state_style_required, token_reference_required, conditional_visual_effect_required, ui_ux_state_alignment.
- outputs: component_state_style_map, token_map, visual_effects, sequences, style_guide{layout,color,typography,interaction,responsive,accessibility}.

---
## 9. TDD — "Why after spec, before plan"
### 위치 논리(핵심)
- 시점: spec.md 직후 + state-management.md 병행 구간 = 공식 시점. "기능 정의 직후(what&how 명확)" + "구현 시작 전(before plan.md)".
- 본질: 테스트가 설계의 일부(test-first). 코드 존재 전 "올바르게 동작 판단 기준(=테스트 조건)"을 먼저 문서화. 기준은 spec.md에서 시작→test.md 확장.
- **3대 논리**: ①spec 이후여야(기준이 spec에서 나옴, 없으면 무엇 검증할지 정의불가) ②plan 이전이어야(테스트 없이 나누면 검증불가 구조) ③병행 효율성(상태변화 전후 테스트 동시 정의).
### repomix
- 목적: 테스트 실행 전 외부 AI에게 프로젝트 이해시키는 정적 스냅샷(repomix-output.xml). 테스트 실행과 별개. Claude Code/Codex CLI가 폴더 직접 열람 가능하면 불필요. 명령: `npx repomix --ignore "./**/*.md"`.
### 문서 체인 5종
1. **test-e2e.md**(layer8, test-e2e): parent=spec, next=test. rules: scenario_required, gwt_structure_required(Given-When-Then), coverage_required, ci_config_reference_only, **no_code_inclusion**.
2. **test-report.md**(layer8.1, e2e-verification, Codex GPT-5 coder): inputs=repomix-output.xml+package.json. rules: compare_structure/dependencies, detect_missing/extra_folders, no_framework_assumption, no_example_code.
3. **test-setup-orchestrator**(layer8.0, 출력 test-setup-orchestrator.md, Codex GPT-5 coder): ③단계(폴더·샘플작성) 직전까지 자동 설계·준비하는 런처/오케스트레이터. rules: select_runner_from_techstack, create_runner_config, generate_sample_unit_test, generate_sample_e2e_test, summary_required, reviewer_prompt_required, no_extra_frameworks.
4. **/docs/rules/tdd.md** — "테스트 루프의 법전(Constitution)". 0-규칙계층, `/docs/rules/`에 UEPP/SCDP/RCMP와 함께 전역 상속. verbatim 핵심: **Red→Green→Refactor** / **FIRST**(Fast·Independent·Repeatable·Self-validating·Timely) / **AAA**(Arrange-Act-Assert) / Test Pyramid(Unit70·Integration20·Acceptance10) / Outside-In vs Inside-Out / 안티패턴 회피. 생성=Smoke Test 이전 또는 test.md 직전.
5. **test.md**(layer8, tdd-root-spec, Codex GPT-5 coder): TDD 중심문서. "무엇을 어떻게 테스트?". unit_scenarios/e2e_scenarios, qa_plan{coverage,commands,failure_policy,report_path}.
6. **test-plan.md**(layer8.1, test-plan): "테스트 통과 위해 무엇을 어떻게 구현?"=구현 계획서(Implementation Bridge). rules: task_minimal_unit, apply_rgr_cycle.
- 대비: test.md=검증 목표 정의서 / test-plan.md=목표 달성 구현 계획서. **실제 TDD 구현은 '9-구현계획 도출'에서 실시**(저자 명시).
- Smoke Test 강조: 성공/실패 자체가 아니라 **"실행되어 보고를 남길 수 있느냐"**가 핵심.
- 참고: TDD 창시자 Kent Beck(kentback-spring GitHub).
- 환경 6단계: Playwright 설치→config 생성→/tests/e2e·unit 폴더+Smoke Test→npx playwright test→test-report.md 기록→TDD 루트(test.md).

---
## 4대 Subagent 정의(.md) — 구조·역할 분담
모두 model:sonnet, 동일 SOT/Context/inheritance 골격, 색상으로 역할 구분.
- **common-task-planner**(cyan): "프로젝트 전역 공통 모듈·유틸·테스트 환경 설계 후 /docs/common-modules.md에 기록". 출력=common-modules.md. rules: identify_global_modules, define_test_support_layer, define_global_ui_state_layer, define_external_service_common_layer, define_ci_cd_quality_layer, **no_page_specific_logic**.
- **plan-writer**(orange): "특정 페이지 세부 실행 계획서를 /docs/pages/{page-name}/plan.md에 작성". 출력=pages/{page_name}/plan.md. rules: use_spec/state/page_state_mapping/test_cases, connect_feature_entity_state_ui_test, validate_crud_completeness, validate_no_circular_reference.
- **design-agent**(blue): "FDS 규칙과 Spec·TDD 기반 UI·UX·Visual 문서 생성·검토·갱신 디자인 통합". 출력=ui/ux/visual/design-plan/validation_report 다중. rules: generate_ui/ux/visual/design_plan, validate_fds_compliance, validate_state_visual_mapping, validate_test_alignment.
- **implementer**(green): "작성된 구현 계획·테스트 명세 기반 실제 코드 구현·검증". result_log=test-report, summary=initial-implement. rules: use_plan_tasks, generate_code, generate_tests, ensure_test_alignment, ensure_state_ui_consistency, ensure_fds_compliance, run_quality_pipeline, record_results.
- **역할 분담 체인**: common-task-planner(전역 공통, 페이지 로직 금지)→plan-writer(페이지별, 병렬)→design-agent(디자인 문서군 통합)→implementer(계획+테스트→코드·검증). plan-writer/implementer는 페이지 단위 **병렬 실행** 전제.

---
## 9~10 자동 수행 프롬프트 구조
### initial-implement.md (Claude CLI → 9~10 자동)
```
plan-writer로 모든 계획 병렬 작성 뒤 implementer 병렬 구현.
1. common-task-planner로 /docs/common-modules.md 공통모듈 계획 작성
2. implementer로 공통모듈 계획 정확히 구현
3. plan-writer로 PRD 페이지별 계획을 docs/pages/N-name/plan.md 작성 (병렬)
4. implementer로 구현 계획 정확히 구현 (병렬)
```
→ **공통모듈(계획→구현) 선행 → 페이지별(계획→구현) 병렬 후행**의 2단 파이프라인.
### 10-1. 구현 계획(Plan=Task) (layer9, implementation-plan)
- parent=test-plan.md, next=initial-implement.md, 출력=`./plan.md`. rules: use_spec/test_spec/test_plan/codebase_structure, feature_entity_task_mapping, module_path_design, ipo_test_binding, crud_flow_definition.
- 오버엔지니어링 제거: "너무 많은 모듈로 오버엔지니어링됐는지 검증. 단순화하여 다시 최종본 응답."
### 10-2. 실행(Implement) (layer10, implement)
- parent=plan.md, next=initial-implement.md, 출력=`/docs/implement.md`. Context에 전 문서 총동원.
- rules: use_plan_tasks, use_spec_scenarios, use_test_requirements, use_state_rules, use_page_state_mapping, use_database_schema, use_fds_rules, generate_code, generate_tests, run_quality_checks, update_test_report.
- outputs: code, tests, quality_checks, report(test-report), summary(initial-implement). 실행 `npm run dev`(localhost:3000). npm vs pnpm(하드링크) 부기.

---
## 저자 강조·경고 총괄
1. spec.md=기획↔코드 경계선, "행동 기반 명세(Executable Narrative)"만.
2. 상태관리 필수 — AI는 상태 '코드'는 만들어도 '책임'은 못 짐. 상태 정의·전이 규칙만은 인간이 먼저 고정해야 AI가 연주.
3. Flux=AI 통제 계약서, Context는 항상 마지막.
4. TDD는 spec 이후·plan 이전이어야 검증 가능 구조가 생김.
5. 모든 단계 검토 게이트: "확대해석·불필요 추가개발 금지 / 20년차 시니어 깐깐 기준".
6. 오버엔지니어링은 명시적 단순화 프롬프트로 제거.
7. 문서 계약 불변: **additive-only + override-prohibited + root-sot-priority** — 하위는 상위를 덮어쓸 수 없고 추가만 가능.

(19759행 이후 "10단계 개요 표"는 지정 범위 밖이라 미포함. 필요 시 별도 요청.)
