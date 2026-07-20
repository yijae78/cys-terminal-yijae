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
  - /docs/persona.md
layer: 1
identity: project
relation:
  parent: persona.md
  next: requirement.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_project_purpose_scope
rules:
  - purpose_over_features
  - explicit_scope_boundary
  - success_criteria_measurable
outputs:
  - purpose
  - success_definition
  - scope
  - mvp
  - constraints
  - decision_principles
validation:
  - scope_in_out_present
  - success_criteria_testable
path:
  output: /docs/project.md
---

# Project Definition (`/docs/project.md`)

> NLC 10단계 · 2-6 · 성격: 기획 원형 · 핵심 질문: "무엇을, 왜 만드는가?"
> 프로젝트 단위 최상위 기획 기준점. Requirement/PRD의 상위. "무엇을"보다 **"왜·어디까지"**.

## 목적 (Purpose)
문제·의도 중심으로 서술한다. "잘 만들어보자" 류의 공허한 목적은 금지.
- [FILL: 해결하려는 문제]
- [FILL: 이 프로젝트의 의도]

## 성공의 정의 (Success Definition)
이후 PRD/테스트의 판단 기준점이 된다. 정성·정량 모두 명시.
- 정량: [FILL: 측정 가능한 지표]
- 정성: [FILL: 질적 기준]

## 범위 (Scope) — 스코프 크리프 방지
- In of Scope: [FILL]
- Out of Scope: [FILL]

## MVP
- [FILL: 최소 기능 집합]

## 제약 (Constraints)
- [FILL: 기술·일정·규제·자원 제약]

## 의사결정 원칙 (Decision Principles)
- [FILL: 트레이드오프 시 우선하는 가치]
