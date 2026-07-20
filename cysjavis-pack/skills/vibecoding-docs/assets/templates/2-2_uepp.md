---
layer: L-2
authority: Meta-Constitution / Meta-Supreme
inherits: [_root-sot]
identity: uepp
---

# UEPP — Universal Error-Preventive Prompt (`/docs/rules/uepp.md`)

> NLC 10단계 · 2-2 · 성격: 예방 헌법 · 핵심 질문: "무엇을 하면 안 되는가?"
> 오류가 발생하기 "이전" 단계에서 차단하는 메타 헌법 = 생성 이전 예방 헌법(Preventive Constitution).
> 오직 "이 산출물을 지금 만들어도 되는가? 구조적으로 허용되는가?"만 판정한다.

<!--
[존재 이유] Root SOT는 재판관이지 검문소가 아니고, rules.md는 법전이지 에러 방지 장치가 아니다.
LLM은 편리함·최근 문맥·구체 요구를 우선해 상위 기준을 희석한다 — 이는 실수가 아니라 LLM의 정상 동작.
비유: "Root SOT = 헌법 정신, rules.md = 법전, UEPP = 공항 보안 검색대."
[가변] 9번 섹션의 [ ] 앵커와 강도(STRICT|NORMAL|LIGHT)만 채운다.
-->

## 1. Ontological Status
Root SOT 바로 아래에 위치하며 자동 전제된다 — "암묵적으로 로딩된 검문소".

## 2. Scope
생성 이전(pre-generation)의 허용/차단과 계층 위반 감지. "어떻게 만들 것인가"가 아니라 "만들어도 되는 상태인가"만 판정.

## 3. Worldview
대부분의 오류는 구현 실수가 아니라 **판단 순서 오류**다. LLM은 구체적 요청을 우선해 상위 기준을 희석한다. 사후 교정이 아니라 사전 차단이 최선이다.

## 4. Hierarchy Check
생성 이전에 7계층을 검사한다. 위반 = 즉시 Blocked.

## 5. Pre-Generation Gate (4게이트)
- Hierarchy Gate: 상위 계층과 충돌하지 않는가.
- Duplication Gate: 중복 SOT를 만들지 않는가.
- Assumption Gate: "보통/일반적으로/알아서" 금지. 필요한 가정은 `[가정]`으로 명시.
- Propagation Gate: 변경이 전파되어야 할 문서를 빠뜨리지 않는가.

## 6. Forbidden Patterns (감지 시 Systemic Fault)
상위가 하위에 명령 · 정의 없는 구조 나열 · 기존을 무시한 재정의 · 문서-코드 불일치 · 중복 SOT · 검증 없는 완료 · Scope Creep · 민감정보 노출.

## 7. Self-Healing
위반 유형 명시 → 원인 특정 → 최소 수정 → 동기화 → 재검증. 재작성(rewrite)은 최후 수단.

## 8. Inheritance
요약·재진술될 수 없다. 항상 전제된다.

## 9. Anchors (채움)
- FORBIDDEN_CREATION_PATTERNS: [FILL: 이 프로젝트에서 생성 자체가 금지된 패턴]
- COMMON_STRUCTURAL_FAILURES: [FILL: 자주 나는 구조적 실패]
- STRENGTH: [FILL: STRICT | NORMAL | LIGHT]

## 10. Final Assertion
UEPP는 "규칙을 지키라"고 요구하지 않고, "규칙을 어길 기회"를 생성 단계에서 제거한다. 우회 = Invalid by Construction.
