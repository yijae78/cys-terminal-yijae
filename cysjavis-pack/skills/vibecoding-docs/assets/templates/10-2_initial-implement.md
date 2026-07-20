---
# === NLC 계약 골격 (수정 금지 영역) ===
sot:
  - /docs/_root-sot.md
  - /rules.md
context:
  - /docs/_root-sot.md
  - /docs/rules/uepp.md
  - /docs/rules/scdp.md
  - /docs/rules/rcmp.md
  - /docs/plan.md
  - /docs/spec.md
  - /docs/test.md
  - /docs/state-management.md
  - /docs/page-state-mapping.md
  - /docs/database.md
  - /docs/rules/fds.md
layer: 10
identity: initial-implement
relation:
  parent: plan.md
  next: initial-implement.md      # 자기 참조 오케스트레이터 (반복 실행)
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: execute_plan_and_report
rules:
  - use_plan_tasks
  - use_spec_scenarios
  - use_test_requirements
  - use_state_rules
  - use_page_state_mapping
  - use_database_schema
  - use_fds_rules
  - generate_code
  - generate_tests
  - run_quality_checks
  - update_test_report
outputs:
  - code
  - tests
  - quality_checks
  - report            # /docs/test-report.md
  - summary           # /docs/initial-implement.md
validation:
  - all_tests_pass
  - state_ui_consistent
  - fds_compliant
path:
  output: /docs/initial-implement.md
---

# Execution & Report — 실행 (`/docs/initial-implement.md`)

> NLC 10단계 · 10-2 · 성격: 실행 증거 · 핵심 질문: "실제로 동작하는가?" · 도구: Claude CLI(9~10 자동 수행).
> Context에 전 문서를 총동원한다. 실행: `npm run dev`(localhost:3000). (npm vs pnpm — pnpm은 하드링크.)

## 오케스트레이션 프롬프트 (2단 파이프라인)
plan-writer로 모든 계획을 병렬 작성한 뒤 implementer로 병렬 구현한다:
```
1. common-task-planner 로 /docs/common-modules.md 공통모듈 계획 작성
2. implementer 로 공통모듈 계획을 정확히 구현
3. plan-writer 로 PRD 페이지별 계획을 docs/pages/N-name/plan.md 작성 (병렬)
4. implementer 로 구현 계획을 정확히 구현 (병렬)
```
→ 공통모듈(계획→구현) 선행 → 페이지별(계획→구현) 병렬 후행.

## 산출·검증
- code / tests / quality_checks 생성.
- 결과 로그 → `/docs/test-report.md`.
- 요약 → 이 문서(`/docs/initial-implement.md`).
- 완료 판정: 모든 테스트 통과 · state↔UI 일관 · FDS 준수.

## 에러 수정 반복 프롬프트
"모든 type, lint, build 에러를 수정할 때까지 반복해서 개선하세요."
