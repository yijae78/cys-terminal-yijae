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
  - /docs/rules/tdd.md
  - /docs/test.md
layer: 8.1
identity: test-plan
relation:
  parent: test.md
  next: plan.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: map_tests_to_implementation
rules:
  - task_minimal_unit
  - apply_rgr_cycle           # Red-Green-Refactor
  - trace_each_task_to_test
outputs:
  - implementation_bridge     # 테스트 통과를 위해 무엇을 어떻게 구현?
validation:
  - every_test_has_impl_task
  - no_untested_task
path:
  output: /docs/test-plan.md
---

# Test Plan — 테스트 계획 (`/docs/test-plan.md`)

> NLC 10단계 · 9-1 · 성격: 구현 브릿지 · 핵심 질문: "무엇을 구현해야 통과하는가?"
> 대비: test.md = 검증 목표 정의서 / test-plan.md = 목표 달성 구현 계획서(Implementation Bridge).
> 실제 TDD 구현은 '10-1 구현 계획 도출'에서 실시된다(저자 명시).

## Test → Implementation Map (채움)
```yaml
- test: [FILL: test.md의 시나리오 id]
  minimal_task: [FILL: 통과에 필요한 최소 구현 단위]
  rgr_cycle: red → green → refactor
```

## 구현 브릿지 노트
- [FILL: 테스트를 통과시키기 위한 구현 접근·주의점]
