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
  - /docs/spec.md
  - /docs/test.md
  - /docs/test-plan.md
  - /docs/codebase-structure.md
layer: 9
identity: implementation-plan
relation:
  parent: test-plan.md
  next: initial-implement.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: decompose_into_tasks_and_modules
rules:
  - use_spec_test_spec_test_plan_codebase_structure
  - feature_entity_task_mapping
  - module_path_design
  - ipo_test_binding
  - crud_flow_definition
outputs:
  - tasks
  - module_paths
  - crud_flows
validation:
  - not_overengineered
  - each_task_binds_to_test
path:
  output: /docs/plan.md
---

# Implementation Plan — 구현 계획 (Plan = Task) (`/docs/plan.md`)

> NLC 10단계 · 10-1 · 성격: 실행 계획 · 핵심 질문: "어떤 순서로 구현할까?"
> spec/test/test-plan/codebase-structure를 근거로 Task·모듈을 분해한다. feature-entity-task를 매핑하고 IPO를 테스트에 바인딩한다.

## Tasks (채움)
```yaml
- task: [FILL]
  feature: [FILL]
  entity: [FILL]
  module_path: [FILL]
  ipo: { input: [FILL], process: [FILL], output: [FILL] }
  bound_test: [FILL: test.md 시나리오]
```

## CRUD Flows
- [FILL: 생성/조회/수정/삭제 흐름 정의]

## 오버엔지니어링 제거 프롬프트
"너무 많은 모듈로 오버엔지니어링되었는지 검증하라. 단순화하여 다시 최종본으로 응답하라."
