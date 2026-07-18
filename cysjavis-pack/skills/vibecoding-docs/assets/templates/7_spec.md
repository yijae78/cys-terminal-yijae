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
  - /docs/userflow.md
  - /docs/database.md
  - /docs/design/ui.md
  - /docs/design/ux.md
layer: 6
identity: usecase-spec
relation:
  parent: database.md
  next: state-management.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_executable_narrative_per_feature
rules:
  - behavior_based_not_code
  - seven_fields_required
  - plantuml_standard
  - no_scope_expansion
outputs:
  - usecases            # /docs/usecases/N-name/spec.md
  - ucs_index           # /docs/spec.md 통합
validation:
  - userflow_alignment
  - ux_alignment
  - db_alignment
  - naming_compliance
  - schema_conformance
path:
  output: /docs/spec.md
---

# Use Case Spec — 유스케이스 (`/docs/spec.md`)

> NLC 10단계 · 7 · 성격: 실행 논리 · 핵심 질문: "기능은 어떻게 작동하는가?"
> 유스케이스 = 파이프라인의 핵심 전환점·**기획↔코드 경계선**. PRD/Userflow는 사람용 기획서, spec은 AI/개발자용 코드 스펙화 문서.
> **"코드가 아닌 행동 기반 명세(Executable Narrative)만."** userflow 기반 기능단위(Feature-unit)별로 생성한다.
> 서브에이전트 `usecase-writer`가 각 기능을 `/docs/usecases/N-name/spec.md`에 생성 → 완료 시 `/docs/spec.md`(UCS 통합)에 자동 등록.

## Use Case 필수 7항목 (각 기능마다)
```yaml
- primary_actor: [FILL]
  precondition: [FILL]           # 사용자 관점
  trigger: [FILL]
  main_scenario: [FILL...]
  edge_cases: [FILL...]
  business_rules: [FILL...]
  sequence_diagram:              # PlantUML 표준, 구분선 없이
    participants: [User, FE, BE, DB]
    plantuml: |
      [FILL: @startuml ... @enduml]
```

## 검토 프롬프트 (spec 이후 모든 단계에서 반복)
"언급되지 않은 내용을 확대해석하지 않았는지 엄밀히 검토. 쓸데없는 추가 개발 절대 금지. 20년차 이상 최고급 시니어 관점으로 최대한 깐깐하게."

> ⚠ 서브에이전트는 이미 전체 컨텍스트를 상속하므로 별도 참조를 추가하지 말 것.
