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
  - /docs/spec.md
layer: 7
identity: state-management
relation:
  parent: spec.md
  next: page-state-mapping.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_state_transitions_and_flux
state_types: [persistent, derived]
rules:
  - userflow_data_only
  - classify_source_lifetime_storage
  - define_trigger_condition_effect
  - flux_required
  - store_interface_required
  - no_redundant_state
  - alignment_ui_ux_db_spec
outputs:
  - state_list          # {name, type, source, lifetime, storage}
  - change_table
  - flux_diagrams
  - stores              # {name, state, actions, scope}
  - mapping
validation:
  - no_derived_stored_as_state
  - single_sot_per_state
path:
  output: /docs/state-management.md
---

# State & Flux Model — 상태관리 (`/docs/state-management.md`)

> NLC 10단계 · 8 · 성격: 상태 머신 · 핵심 질문: "행동 후 무엇이 변하는가?" · 저자가 "필수"로 못박은 단계.
> ⚠ `/docs/rules/state.md`(HOW 집행 런북)와 대체 불가 — 이 문서는 WHAT 설계 SOT(헌법 조문)다. spec 이후에만 정확히 정의 가능하다.

## 왜 필수인가 (State = A Component's Memory)
- State는 "변수"가 아니라 "기억"이다. 기억 = 책임. 그 책임의 경계를 정하는 것이 상태관리.
- State 판별: 시간이 지나도 유지 / 행동 후 남아야 / 다음 렌더링에 영향 = State. 계산 가능하면 State 아님(totalPrice·isMorning·버튼색 = derived).
- 저자 경고: "AI는 상태 비슷한 코드는 만들지만, 상태의 경계는 정의하지 못한다." 인간이 상태 정의·전이 규칙을 먼저 고정해야 AI가 "악보를 읽는 연주자"가 된다.

## 올바른 순서
1) spec → 2) State 정의 → 3) Flux(같은 문서) → 4) Context. **Context는 항상 마지막.**
- State = 기억의 내용, Flux = 기억의 법칙, Context = 기억의 배포망.
- Flux는 단방향 `Action → Store → View`. Store가 상태 변화의 유일한 장소, View는 결과만(결정권 없음).

## State List (채움)
```yaml
- name: [FILL]
  type: persistent | derived
  source: [FILL]
  lifetime: [FILL]
  storage: [FILL]
```

## Change Table (Trigger · Condition/guard · Effect)
- [FILL: 언제(Trigger) · 왜(Reason/guard) · 어떻게(Transition)]

## Flux Diagrams
- [FILL: Action → Store → View]

## Stores
```yaml
- name: [FILL]
  state: [FILL]
  actions: [FILL]
  scope: [FILL]
```

## Mapping
- [FILL: state ↔ ui/ux/db/spec 정합]

> 참고: State = f(User Action, System Process, Context). 유스케이스 = 원인(cause), 상태관리 = 결과(effect).
