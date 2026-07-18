---
layer: L-0.5
authority: Meta-Constitution / Structural
type: Context Topology Definition
inherits: [_root-sot, uepp, scdp]
identity: rcmp
---

# RCMP — Root Context Map Prompt (`/docs/rules/rcmp.md`)

> NLC 10단계 · 2-4 · 성격: 구조 지도 · 핵심 질문: "문서들은 어떻게 연결되는가?"
> 모든 문서·규칙·컨텍스트의 구조적 위치와 연결 관계를 정의한다 = 구조 지도(Map).
> 판단·규칙·실행을 하지 않는다. 유일 목적: "이 문서가 시스템 전체에서 어디에 있는가."

<!--
[존재 이유] 없으면 docs/를 "파일 묶음"으로 인식 → 헌법이 PRD에 밀리고 Root SOT가 Spec에 무력화된다.
"SOT 체계 붕괴의 90%는 RCMP 부재에서 시작한다."
비유: "UEPP가 법이라면 RCMP는 지형도, SCDP는 물길."
[가변] 4번 섹션의 [ ] 앵커만 채운다.
-->

## 1. Nature
구조 지도(Context Topology Definition). 판단하지 않고 위치만 정의한다.

## 2. Canonical Layers (보편 계층)
- L-2  Agent Definition (WHO)
- L-1  Immutable Rules
- L-0  Root SOT (WHY)
- L-0.5 Meta Rules (UEPP/SCDP/RCMP)
- L+1  Domain Documents
- L+2  Execution Documents
- L+3  Artifacts

## 3. Mandatory Positioning
`AGENT.md = L-2` · `rules.md = L-1` · `_root-sot.md = L-0` · `uepp/scdp/rcmp = L-0.5`.
이 위치는 대체·병합·흡수 불가.

## 4. Project-Dependent Zones (채움)
- DOMAIN_DOCUMENTS: [FILL]
- DESIGN_DOCUMENTS: [FILL]
- EXECUTION_DOCUMENTS: [FILL]
- ARTIFACT_TYPES: [FILL]

## 5. Dependency Direction
상위 → 하위 허용. 하위 → 상위는 참조만. 동일 계층은 명시 선언 시에만 연결. 위치 관계만 고정한다.
대표 의존 그래프: `Spec → Code` · `Userflow → DB` · `State → UI`.

## 6. Completeness
새 문서는 Layer·상위 참조·전파 여부를 정의해야 한다. 미정의 = Unmapped.

## 7. Scope Boundary
규칙 해석·우선순위·절차·품질 평가를 하지 않는다.

## 8. Final Assertion
RCMP는 판단하지 않지만, 판단이 길을 잃지 않게 한다.
