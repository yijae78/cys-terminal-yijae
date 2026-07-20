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
  - /docs/state-management.md
  - /docs/design/ui.md
  - /docs/rules/fds.md
layer: 7.1
identity: page-state-mapping
relation:
  parent: state-management.md
  next: design/visual.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: map_state_to_page_boundary
rules:
  - map_state_to_page
  - classify_scope
  - provider_tree_required
  - state_dependency_required
  - page_implementation_boundary
  - fds_alignment
  - ui_ux_alignment
  - no_unmapped_state
outputs:
  - page_state_map
  - provider_tree
  - scope_classification
validation:
  - every_state_mapped_to_page
  - context_scope_equals_page_boundary
path:
  output: /docs/page-state-mapping.md
---

# Page–State Mapping (`/docs/page-state-mapping.md`)

> NLC 10단계 · 8-1 · 성격: UI 경계 · 핵심 질문: "이 상태는 어디서 다뤄지는가?"
> spec = 무엇을, state-management = 어떻게 변하나, page-state = **어디서 일어나나**. "Context Scope가 곧 Page Boundary."
> 논리상 state-management에 포함되나 시간상 동시 설계된다.

## Page ↔ State Map (채움)
```yaml
- page: [FILL: route]
  states: [FILL]
  scope: local | page | app-global | server
```

## Provider Tree (채움)
```
[FILL: Context Provider 중첩 트리]
```

## State Dependency
- [FILL: 상태 간 의존 관계]

> 매핑되지 않은 상태(no_unmapped_state)가 없어야 한다.
