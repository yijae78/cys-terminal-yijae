# ruler/refactor.md — 구조/결합도 변경 SOP

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: **행동 동일성(Behavior Equivalence) 보장 하에서만** 구조·결합도를 바꾼다.

## 1. Applicability
외부 행동을 바꾸지 않는 내부 구조·결합도 개선. **행동을 바꿀 의도면 이 런북이 아니라 `coding.md`**
(feature/bugfix)로 간다. rename은 의미 명료화만 허용.

## 2. Mandatory Context
`codebase-structure.md`(SOLID·레이어 경계) · 대상 모듈의 `spec.md`(외부 계약) · 기존 테스트 스위트
(행동 고정판). 리팩터는 테스트가 있어야 안전하다.

## 3. Output Contract
- **Refactor Type** — `[extract|inline|rename|split|merge|reorder|simplify|decouple]`.
- **Behavior Equivalence 증명** — 외부 행동 불변·입출력 동등·public contract 안정 근거.
- **Before/After 구조** — 무엇이 어떻게 재배열되는가.
- **Verification Plan** — 동등성을 확인하는 테스트.

## 4. Rules — 4장 Behavior Equivalence = Non-Negotiable
- 외부 행동 불변 · 입출력 동등 · public contract 안정.
- **새 기능 없음 · 버그 안 고침**(버그 수정이 필요하면 별도 coding 작업으로 분리).
- 사용자 관점 변화 없음 — "아무도 눈치 못 채야 성공".
- **확신하지 못하면 중단**한다(동등성을 증명할 수 없으면 리팩터가 아니다).

## 5. Verification
리팩터 전 전 테스트 green → 리팩터 후 **동일 테스트가 무수정으로 green**. 테스트를 고쳐야 통과한다면
그것은 행동 변경이다(중단). 가능하면 characterization test로 기존 행동을 먼저 고정한다.

## 6. Checklist
착수: [ ] Refactor Type 확정 [ ] 기존 테스트 green 확인 [ ] 행동 변경 아님을 선언.
완료: [ ] 동일 테스트 무수정 green [ ] public contract diff 0 [ ] 새 기능·버그수정 혼입 0.

## 7. Stop Conditions (즉시 중단)
- **외부 행동·입출력·public contract가 바뀔 조짐이 보일 때** (Non-Negotiable — coding.md로 전환).
- 동등성을 보장할 테스트가 없고 만들 수도 없을 때.
- "이왕 하는 김에" 기능 추가·버그 수정을 끼워 넣으려 할 때.
