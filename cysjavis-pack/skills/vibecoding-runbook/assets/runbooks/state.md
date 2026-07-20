# ruler/state.md — 상태 집행 런북 (HOW)

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> ⚠ **`/docs/state-management.md`(WHAT 설계 SOT)와 대체 불가**: 이 런북은 집행 매뉴얼(시작 즉시 존재,
> 쓰레기 상태 코드 방지), state-management.md는 헌법 조문(spec 이후에 정의). 둘은 층위가 다르다.
> 한 문장: **State는 변수가 아니라 기억(Memory)** 이고, 그 책임 경계를 정하는 것이 상태관리다.

## 1. Applicability
상태를 도입·수정하거나 상태 전이 규칙을 집행하는 작업. 상태의 **경계·전이 규칙 확정은 인간
결정권**(헌법 6조)이고, 에이전트는 그 위에서 '연주'만 한다.

## 2. Mandatory Context
`spec.md`(상태는 유스케이스의 함수 — State = f(User Action, System Process, Context)) ·
`state-management.md`(설계 SOT) · `page-state-mapping.md`(어디서 일어나나). spec 없이 상태 정의 불가.

## 3. Output Contract
- **State 판별** — 시간 지나도 유지/행동 후 남아야/다음 렌더링 영향 = State. 계산 가능하면 State
  아님(derived).
- **state_list** — `{name, type(persistent|derived), source, lifetime, storage}`.
- **change_table** — Trigger·Reason/guard·Transition.
- **Flux 다이어그램** — 단방향 `Event → Action/Reducer → Store → View`.
- **Boundary** — Local / Page / App-global / Server.

## 4. Rules — Core (Non-Negotiable)
- **State = Memory not Variables** — 계산 가능한 값(derived)은 상태로 저장 금지.
- **Single SOT** — 하나의 진실. props/local/context/API에 중복된 진실 동시 허용 금지.
- **No Shadow State** — 파생·그림자 상태 금지.
- **Unidirectional Flux** — Store가 상태 변화의 유일 장소, View는 결과만(결정권 없음).
- Async&Race: dedupe · cancellation · optimistic · stale-while-revalidate로 레이스 방어.
- **Context는 항상 마지막**(spec → State → Flux → Context 순서).

## 5. Verification
상태 전이가 정의된 Trigger·guard로만 일어나는지, SOT가 하나인지, derived가 저장되지 않았는지 검증.
비동기 레이스·이벤트-상태 불일치 시나리오 테스트.

## 6. Checklist
착수: [ ] spec 확보 [ ] 상태 경계·전이 규칙(인간 결정) 확정 [ ] state-management.md 존재.
완료: [ ] state_list·change_table·Flux 작성 [ ] Single SOT [ ] Shadow state 0 [ ] 레이스 방어.

## 7. Stop Conditions (즉시 중단)
- **상태 경계·전이 규칙이 인간에 의해 확정되지 않았을 때** (헌법 6조 — 에이전트가 임의 정의 금지).
- derived 값을 상태로 저장하려 하거나, 같은 진실이 두 곳에 동시 존재할 때.
- Flux 단방향을 우회해 View가 상태를 직접 바꾸려 할 때.
