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
  - /docs/prd.md
layer: 3.1
identity: fds-root-spec
relation:
  parent: prd.md
  next: design/ui.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_design_constitution
rules:
  - tokens_are_sot
  - naming_convention_enforced
  - accessibility_wcag_aa
  - mobile_first
outputs:
  - ethos
  - tokens
  - components
  - naming
  - layout
  - accessibility
  - responsiveness
  - governance
validation:
  - all_ui_docs_inherit_fds
  - token_change_requires_ruler_apply
path:
  output: /docs/rules/fds.md
---

# FDS Root Spec — 디자인 헌법 (`/docs/rules/fds.md`)

> NLC 10단계 · 4-1 · 성격: 디자인 헌법 · 핵심 질문: "UI의 법은 무엇인가?"
> 도구: Codex CLI GPT5-추론. 디자인 토큰·UI 규칙의 SOT. 모든 UI 문서가 이 문서를 상속한다.

## ethos
clarity_over_complexity · function_over_aesthetics · predictable_over_surprising · accessible_over_exclusive.

## tokens (채움)
- color: [FILL]
- typography: [FILL]
- spacing: [FILL]
- radius: [FILL]
- shadow: [FILL]
- theme: [light, dark, system]

## components
atomic → composite → pattern → template.

## naming
`Component__Variant--State`.

## layout / responsiveness
mobile_first. 컴포넌트당 최소 2 breakpoint.

## accessibility
WCAG 2.1 AA. motion-safe 준수.

## governance
- ui_docs_inherit_fds: true
- token_change_requires_ruler_apply: true
- validation_extension: `.ruler/fds-checker.yml`

> 완료 후 `ruler apply`. 토큰 변경 시에도 `ruler apply` 필수.
