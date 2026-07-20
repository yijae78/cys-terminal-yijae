# rules.md — Global Immutable Rules (프로젝트 헌법)

> NLC 10단계 · 1-2 (`/rules.md`) · 성격: 헌법(불변 규범) · 핵심 질문: "무엇이 절대 변하지 않는가?"
> 이 문서는 판정 기준이다. 기능 정의·구현 방법은 담지 않는다 — 방향·한계·판정 기준·금지/강제·충돌 우선순위만.
> "뒤에 올 문서를 몰라도 이 문서 하나로 완성돼야 정상"이다. 위반 = invalid by definition.
> 인간이 반드시 책임지는 단계다(규칙 = AI 통제 장치). 수정 후 `ruler apply`.

<!--
[채움 지시] 9섹션 구조를 유지한다. [FILL: ...]만 프로젝트 값으로 치환.
실패 패턴 회피: 팁 모음·좋은 습관·권장/불변 혼합·암묵 예외를 넣지 말 것(→ "헌법이 아니라 위키"가 된다).
-->

## 0. Preamble
이 문서의 규칙을 위반한 산출물은 정의상(by definition) invalid하다. 예외는 7장의 절차로만 발생한다.

## 1. Constitutional Rules
- SOT는 최고 권위를 가진다(SOT_PRIORITY: [ROOT_SOT_PATH]).
- 문서 갱신 없는 코드 변경 금지.
- 검증 전략 없는 변경은 무효.
- 암묵적 동작(implicit behavior) 금지 — 모든 계약은 명시.
- No exceptions (7장 예외 절차 외).

## 2. System-wide Invariants (UEPP 연동)
다음을 감지하면 즉시 중단(halt)한다:
- 할루시네이션 API(존재하지 않는 함수·엔드포인트).
- SOT 없는 추론을 요구하는 산출.
- 중복 SOT(같은 진실이 두 곳에).
- silent breaking(경고 없는 하위 호환 파괴).
- "assume it works" 식의 검증 없는 완료 선언.

## 3. Context Inheritance (SCDP 연동)
충돌 해소 순서(위 → 아래):
`ROOT_SOT → docs/rules/*.md → docs/*.md → ruler/*.md → Source code`.
하위 계층은 상위 계층을 override할 수 없다(additive-only).

## 4. Change Propagation (RCMP 연동)
동반 갱신이 강제되는 결합 쌍:
Specs ↔ Code · State ↔ UI · External ↔ Tests · Config ↔ Runtime.

## 5. State & SOT
- 하나의 상태는 하나의 SOT를 가진다.
- 파생값(derived) 저장 금지.
- shadow state 금지.

## 6. Verification
- 테스트가 정답의 기준이다.
- 테스트 없는 기능은 미완(incomplete)이다.

## 7. Exception Clause
예외는 다음을 모두 충족할 때만 유효하다:
- APPROVING_ROLE의 승인: [FILL: 승인 주체]
- 명시된 근거(rationale)
- 시한(expiry) 지정

## 8. Amendment
규칙 변경은 명시적 제안 → 리뷰 → 기록의 절차를 거친다. 기록 없는 개정은 무효.

---

## Project Immutables (프로젝트 고유 불변 — 채움)
- [FILL: 절대 금지 1, 예: 프로덕션 DB에 에이전트 write 커넥션 금지]
- [FILL: 절대 강제 1, 예: 모든 특권 엔드포인트는 서버측 인가 검사]
- [FILL: 충돌 우선순위 추가 조항]
