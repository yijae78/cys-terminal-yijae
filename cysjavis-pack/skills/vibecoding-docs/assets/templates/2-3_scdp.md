---
layer: L-0.5
authority: Context-Inheritance
inherits: [_root-sot, uepp]
identity: scdp
---

# SCDP — System Context Directive Prompt (`/docs/rules/scdp.md`)

> NLC 10단계 · 2-3 · 성격: 상속 규칙 · 핵심 질문: "규칙은 어떻게 전파되는가?"
> 상위 문맥이 어떻게·언제·어느 범위까지 자동 상속되는지 정의한다. 규칙이 아니라 오직 **문맥 상속 방식**.
> "SCDP의 '자동'은 의미의 자동이지 로딩의 자동이 아니다. AI는 파일 시스템을 스스로 훑지 않는다."

<!--
[존재 이유] Root SOT는 "어떻게 스며드는지"를 정의하지 않고, UEPP는 차단 장치지 전파 설계도가 아니다.
없으면 100% 발생: 과잉 상속(철학 오염)·상속 단절(문서마다 다른 세계관)·세션별 기준 붕괴.
"SCDP 없이는 '자동'이라는 단어가 성립하지 않는다."
[가변] 8번 섹션의 [ ] 앵커만 채운다.
-->

## 1. Directive Status
자동 적용된다. Root SOT/UEPP를 재서술하지 않는다.

## 2. Context Sources
`_root-sot` = WHY · `uepp` = 예방 · `rules.md` = WHAT MUST NEVER BREAK.

## 3. Inheritance Scope Matrix
산출물 유형별 상속 강도(Root SOT / UEPP / rules / @ruler):

| 산출물 유형 | Root SOT | UEPP | rules.md | @ruler |
|---|---|---|---|---|
| Meta Docs | HARD | HARD | SOFT | NONE |
| Constitution | HARD | HARD | HARD | NONE |
| @ruler | HARD | HARD | HARD | SELF |
| Design / Spec | SOFT | HARD | HARD | NONE |
| Code / Tests | SOFT | HARD | HARD | CONTEXTUAL |

강도 정의: HARD = 절대 위반 불가 · SOFT = 존중하되 재서술 금지 · CONTEXTUAL = 필요 시 참조 · NONE = 상속 금지.

## 4. Strength Rules
Root SOT는 재작성/요약/복제 금지. @ruler는 실행 시점에만 적용. 설계 문서로의 전파 금지.

## 5. Temporal Rules
생성·수정·병합·검토 시점에 적용한다. 누락 = Context Break.

## 6. Isolation
문맥은 항상 위 → 아래로만 흐른다.

## 7. Assumption Handling
핵심 질문 1개만 하거나 `[ASSUMPTIONS]`로 명시한다.

## 8. Overrides (채움)
- DOCUMENT_TYPES: [FILL: 프로젝트 고유 문서 유형]
- EXCLUDED_DOCUMENTS: [FILL: 상속 제외 문서]
- CRITICAL_CONTEXT_PATHS: [FILL: 반드시 상속돼야 할 경로]

## 9. Validation
각 산출물 생성 시 상속 매트릭스 준수 여부를 검사한다.

## 10. Final Assertion
SCDP는 규칙을 추가하지 않고, 규칙이 항상 같은 방식으로 적용되도록 강제한다. 위반 = Contextual Fault.
