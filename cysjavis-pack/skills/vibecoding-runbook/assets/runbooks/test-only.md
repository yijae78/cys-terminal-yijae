# ruler/test-only.md — 검증 전용(프로덕션 코드 미변경) SOP

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: **프로덕션 코드는 절대 건드리지 않고 검증만** 추가한다.

## 1. Applicability
기존 동작에 대한 테스트 추가·보강, 커버리지 확대, 회귀 방지 테스트 작성. 프로덕션 로직 변경이
필요해지면 이 런북을 벗어나 `coding.md`로 간다.

## 2. Mandatory Context
대상 기능의 `spec.md`(관측 행동 기준) · `test.md`/`test-plan.md`(TDD 계약) · 기존 테스트 스위트.

## 3. Output Contract
- **테스트 목록** — Given-When-Then 구조의 시나리오.
- **관측 행동 명세** — 무엇을(입력) 하면 무엇이(관측 가능한 출력) 되는가.
- **커버리지 델타** — 추가된 검증 표면.

## 4. Rules — Forbidden (Hard)
- **프로덕션 코드 수정 금지**.
- **assertion을 약화시켜 통과 금지**(green을 위해 기준을 낮추지 않는다).
- **실패 은폐 금지**(skip·주석 처리로 red를 감추지 않는다).
- Given-When-Then·관측 행동 기반. snapshot 남용 금지(구현 세부에 결합된 스냅샷은 회피).

## 5. Verification
추가 테스트가 실제로 대상 행동을 검증하는지 확인 — mutation/negative 관점에서 "막아야 할 입력을
실제로 잡는가". 프로덕션 소스 diff가 0인지 대조.

## 6. Checklist
착수: [ ] 대상 행동 기준(spec) 확보 [ ] 프로덕션 무변경 선언.
완료: [ ] GWT 시나리오 작성 [ ] 프로덕션 diff 0 [ ] assertion 실효성 확인 [ ] 은폐된 skip 0.

## 7. Stop Conditions (즉시 중단)
- **프로덕션 코드를 고쳐야 테스트가 통과할 때** (Non-Negotiable — coding.md로 전환).
- assertion 약화·실패 은폐로 green을 만들려는 충동이 감지될 때.
- 검증 대상 행동이 spec에 정의되어 있지 않아 무엇을 검증할지 불명일 때.
