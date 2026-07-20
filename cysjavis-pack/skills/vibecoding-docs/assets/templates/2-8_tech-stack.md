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
  - /docs/project.md
  - /docs/environment/env.template.md
layer: 2
identity: tech-stack
relation:
  parent: environment/env.template.md
  next: codebase-structure.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: declare_final_tech_choices
rules:
  - declaration_not_comparison
  - no_duplicate_role
  - no_defer_decision
outputs:
  - runtime_framework
  - database
  - infra
  - key_libraries
validation:
  - each_choice_has_single_role
  - ai_implementability_considered
path:
  output: /docs/tech-stack.md
---

# Tech Stack Spec (`/docs/tech-stack.md`)

> NLC 10단계 · 2-8 · 성격: 기술 기반 · 핵심 질문: "어떤 기술로 구현할 것인가?"
> 기술 선택의 **최종 결과(선언문)**. 비교 문서가 아니다. 동일 역할 중복 금지, "나중에 바꾸자" 금지.
> SuperNext 템플릿 사용 시: 이 문서와 2-9 Codebase Structure를 생략하고 Requirement(2-10)부터 시작한다.

## 추천 시 핵심 3기준
1. **AI가 잘 구현**: 인기 기술이 유리(학습 데이터 풍부). Svelte/Tauri 등은 학습 데이터가 적어 품질이 낮다.
2. **잘 유지보수**: Next.js-Vercel / Flutter-Google 처럼 벤더 지원이 안정적인 조합. 개인 유지보수 의존(예: Nest.js) 주의.
3. **Breaking Change 적음**: Material UI는 나쁨, shadcn 유리.

## 선언 (채움)
- Runtime/Framework: [FILL: 예 — Next.js App Router + TypeScript (Default Lock)]
- Database: [FILL: 예 — Supabase]
- Infra/Deploy: [FILL: 예 — Vercel]
- Key Libraries: [FILL: 역할별 단일 선택]

## '간결함' 성찰 (precision pruning)
불필요한 단어·수식어·중복·서사형·감성 문구를 제거한다. 코드 오염은 오류·할루시네이션의 원천이다.

> 완료 후 `ruler apply`.
