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
  - /docs/design/ui.md
layer: 4
identity: userflow
relation:
  parent: prd.md
  next: design/ux.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_user_behavior_flow
rules:
  - ipo_structure_required        # Input-Process-Output
  - edge_cases_required
  - align_with_prd_pages
outputs:
  - flows
  - edge_cases
validation:
  - each_flow_has_ipo
  - every_page_reachable
path:
  output: /docs/userflow.md
---

# User Flow Spec (`/docs/userflow.md`)

> NLC 10단계 · 5 · 성격: UX 흐름 · 핵심 질문: "사용자는 어떻게 이동하는가?"
> 사용자 행동 흐름을 IPO(Input-Process-Output) 구조로 정의한다. 엣지 케이스는 필수.

## Flows (채움)
```yaml
- flow: [FILL: 흐름명]
  input: [FILL]
  process: [FILL]
  output: [FILL]
  pages: [FILL: 경유 페이지]
```

## Edge Cases (필수)
- [FILL: 비정상 입력 · 중단 · 권한 거부 · 네트워크 실패 등]
