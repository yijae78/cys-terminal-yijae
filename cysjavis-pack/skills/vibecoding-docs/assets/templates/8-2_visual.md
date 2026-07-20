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
  - /docs/page-state-mapping.md
  - /docs/rules/fds.md
  - /docs/design/ux.md
layer: 7.2
identity: visual-design
relation:
  parent: page-state-mapping.md
  next: test.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_state_driven_visual_response
rules:
  - fds_compliance
  - component_state_style_required
  - token_reference_required
  - conditional_visual_effect_required
  - ui_ux_state_alignment
outputs:
  - component_state_style_map
  - token_map
  - visual_effects
  - sequences
  - style_guide       # {layout, color, typography, interaction, responsive, accessibility}
validation:
  - every_component_state_has_style
  - tokens_referenced_not_hardcoded
path:
  output: /docs/design/visual.md
---

# Visual Spec — 비주얼 설계 (`/docs/design/visual.md`)

> NLC 10단계 · 8-2 · 성격: 시각 명세 · 핵심 질문: "어떻게 보이고 반응하는가?"
> "어떻게 반응하는가?"의 구현 디자인 단계. 상태별 UI 반응·스타일을 FDS 토큰 참조로 정의한다(하드코딩 금지).

## Component–State–Style Map (채움)
```yaml
- component: [FILL]
  states:
    - state: [FILL]        # default | hover | active | disabled | loading | error
      style: [FILL: 토큰 참조]
```

## Token Map
- [FILL: 사용하는 FDS 토큰 목록]

## Visual Effects / Sequences
- [FILL: 조건부 시각 효과 · 전이 시퀀스]

## Style Guide
```yaml
layout: [FILL]
color: [FILL]
typography: [FILL]
interaction: [FILL]
responsive: [FILL]
accessibility: [FILL]
```
