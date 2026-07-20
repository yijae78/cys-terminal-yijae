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
  - /docs/prd.md
layer: 5
identity: database-design
relation:
  parent: userflow.md
  next: spec.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_dataflow_and_schema
rules:
  - use_userflow_data_only
  - model_read_write_delete_only
  - ui_ux_alignment
  - logical_model_required
outputs:
  - dataflows
  - erd
  - tables
  - migrations
validation:
  - no_extra_entities_beyond_userflow
  - each_flow_has_dataflow_defined
  - each_entity_used_by_at_least_one_flow
  - naming_consistency
  - schema_conformance
path:
  output: /docs/database.md
---

# Data Flow & Schema (`/docs/database.md`)

> NLC 10단계 · 6 · 성격: 데이터 구조 · 핵심 질문: "어떤 데이터를 다루는가?"
> 도구: Codex CLI **모델 GPT5-codex** 선택 후 실행(또는 Google AI Studio에 context md를 '먼저' 입력).
> userflow → dataflow · ERD · tables · migrations. migration SQL은 `/supabase/migrations`에 둔다.
> migration 강조: "명시된 모든 table과 column이 절대 누락되지 않도록 꼼꼼히 점검."

## Data Flows (채움 — userflow 데이터만)
- [FILL: flow → 읽기/쓰기/삭제 대상 엔티티]

## ERD (채움)
```
[FILL: 엔티티·관계]
```

## Tables (채움)
```sql
-- [FILL: CREATE TABLE ...]
```

## Migrations
`/supabase/migrations/[FILL].sql` — 모든 table/column 누락 없이.

<!-- type B('O to Z', SuperNext 미사용) 추가 지시: `@docs/techstack.md 고려해 gitignore 생성`. -->
