---
# === NLC 계약 골격 (수정 금지 영역) ===
sot:
  - /docs/_root-sot.md
  - /rules.md
context:
  - /docs/_root-sot.md
  - /docs/rules/uepp.md            # universal-error-preventive
  - /docs/rules/scdp.md            # system-context-directive
  - /docs/rules/rcmp.md            # root-context-map
  - /docs/persona.md
  - /docs/project.md
  - /docs/tech-stack.md
  - /docs/codebase-structure.md
  - /docs/requirement.md
  - /docs/external/<service>.md
layer: 3
identity: prd
relation:
  parent: external-integration.md
  next: design/ui.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_page_feature_entity_structure
rules:
  - separate_feature_entity
  - entity_is_db_view
  - map_feature_to_entity_rw
outputs:
  - pages
  - features
  - entities
  - feature_entity_map
validation:
  - feature_refs_entity
  - entity_persistence_only
  - techstack_consistent
  - schema_conformance
path:
  output: /docs/prd.md
---

# PRD — Product Requirements (`/docs/prd.md`)

> NLC 10단계 · 4 · 성격: 제품 설계도 · 핵심 질문: "어떤 제품 구조인가?"
> **도구: Codex CLI + GPT5-추론 모델** 선택 후 이 YAML 프롬프트로 실행. (AI Studio 대안: 아래 Context를 전부 입력 + 기술스택/페르소나/요구사항/코드베이스 첨부.)
> PRD는 페이지·기능·엔티티 구조를 정의한다. Feature와 Entity를 분리하고(Entity는 DB view), Feature를 Entity의 R/W로 매핑한다.

## Pages (채움)
- [FILL: route] — 목적: [FILL]

## Features (채움)
- [FILL: feature] → 참조 Entity: [FILL] (read/write)

## Entities (채움 — DB view만, 파생값 금지)
- [FILL: entity] — 필드: [FILL]

## Feature ↔ Entity Map
- [FILL: feature → entity(R/W)]

---
> 완료 후 `ruler apply`. 이어서 4(prd-critic)로 일관성·확대해석을 적대 감사한다.

## 부속 — prd-critic (`/docs/prd-critic.md`)
PRD의 일관성·확대해석을 검증하는 별도 비판 문서. Codex CLI GPT5-추론. layer:3.1, identity:prd-critic, parent:prd.md.
- goal: prd_consistency_check.
- checks: scope_diff · missing_items · integration_alignment · feature_entity_mapping · annotation_presence · techstack_consistency · env_reference_integrity.
- rules: add_nothing_unless_specified · no_feature_without_entity · integration_follows_external_spec · techstack_must_match_requirement · nodes_must_have_entities.
- output_schema: `summary`, `findings[{id, type(scope_diff|missing_item|integration_error|mapping_error|annotation_missing|tech_mismatch|env_gap), where, description, severity(blocker|major|minor), fix}]`, `patches`, `validation_result{ok, counts}`.
- 의도: "PRD에서 확대해석된 기능이 없는지 점검. 20년차 시니어 관점으로 깐깐하게." requirement를 넘어 임의 기능을 부풀리지 않았는지 적대적으로 감사.
