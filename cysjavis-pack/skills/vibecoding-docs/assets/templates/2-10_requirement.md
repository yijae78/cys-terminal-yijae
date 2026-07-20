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
  - /docs/project.md
  - /docs/tech-stack.md
  - /docs/codebase-structure.md
layer: 2.9
identity: requirement
relation:
  parent: codebase-structure.md
  next: external-integration.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_what_must_be_built
rules:
  - fr_numbered_format
  - no_ui_details
  - unspecified_equals_nonexistent
  - dry_and_legal_tone
outputs:
  - functional_requirements
  - assumptions
  - clarity_checklist
validation:
  - every_fr_numbered
  - no_creative_gap_filling
  - techstack_consistent
path:
  output: /docs/requirement.md
---

# Requirement / SRS (`/docs/requirement.md`)

> NLC 10단계 · 2-10 · 성격: 요구 정의 · 핵심 질문: "무엇을 만들어야 하는가?"
> "무엇을 만들어야 하는가"의 **최종 판결문(SRS)**. 흐릿하면 뒤 문서가 전부 흐릿해진다.
> AI는 요구사항의 공백을 창의력으로 채운다 → 대형 사고의 출발점. 차갑고 건조하게, 법률 문서처럼 쓴다.
> 명시되지 않은 기능 = 존재하지 않는 것. 전제(Next.js/Supabase/Vercel 등)는 변경 대상이 아니다. UI는 다루지 않는다.

## Functional Requirements (FR-번호 형식)
각 항목은 아래 5필드로 기술한다.

### FR-[번호]: [FILL: 기능명]
- 설명: [FILL]
- 입력 조건: [FILL]
- 처리 규칙: [FILL]
- 결과 조건: [FILL]
- 예외 조건: [FILL]

<!-- FR을 필요한 만큼 반복. UI/스타일은 여기서 다루지 않는다. -->

## 명확성 체크리스트
- [ ] AI가 빈칸을 창의력으로 메울 필요가 없는가?
- [ ] 각 FR이 입력/처리/결과/예외를 모두 갖는가?
- [ ] 기술 스택과 모순되는 요구가 없는가?

## 부산물 — RTSV (`/docs/rules/requirement-techstack-validation.md`)
요구사항 ↔ 기술 스택 일관성을 자동 판정하는 규칙(설명서가 아니라 판정 규칙). 위배 시 구현 즉시 중단.
"요구사항은 계약, 기술 스택은 능력이 아니라 **책임**. AI는 이 경계를 넘지 않는다."

> 완료 후 `ruler apply`.
