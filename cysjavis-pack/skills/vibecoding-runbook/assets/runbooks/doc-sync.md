# ruler/doc-sync.md — 문서 동반 갱신 SOP

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: 행동·구조·계약·데이터·상태를 바꾸는 변경은 **문서 반영 없이 완료 불가**.

## 1. Applicability
코드 변경이 문서(SOT·Spec·RCMP 그래프)에 영향을 주는 모든 경우. 이 규칙이 없으면 앞선 모든
문서 작업이 절반 유명무실해진다.

## 2. Mandatory Context
변경이 닿는 SOT 문서(`spec.md`·`state-management.md`·`database.md`·`external/*.md`) ·
RCMP(문서 의존 그래프). 단, **인간 결정 영역 문서(상태 명세 등)는 §C11 전사 프로토콜로만** 갱신한다
(에이전트 자율 갱신 금지).

## 3. Output Contract
- **Change Classification** — `[behavioral|structural|contractual|stateful|config]`.
- **Affected Documents** — **명시적 파일 나열**("documentation updated"만으론 invalid).
- **문서 델타** — 각 문서에 반영된 변경(delta-only, 전면 재작성 금지).

## 4. Rules — 0장 Core (Non-Negotiable)
- 행동/구조/계약/데이터/상태를 바꾸는 변경은 문서에 반영한다.
- **문서 갱신이 불가능하면 코드 변경도 완료로 인정하지 않는다**.
- Affected Documents는 반드시 실제 파일 경로를 나열한다.
- 인간 결정 영역 문서는 DECISION block(§C11) 참조 없이 갱신 금지 — 참조 없는 갱신 시도는 차단.

## 5. Verification
`javis_vibecheck docs`로 문서체인 무결성(코드↔문서 100% 일치) 검증. Change Classification별 대상
문서가 실제로 갱신됐는지 대조. 미수행분은 주석 처리하고 "구현 대상 아님"을 명기한다.

## 6. Checklist
착수: [ ] Change Classification 판정 [ ] Affected Documents 나열.
완료: [ ] 나열된 각 문서 갱신 [ ] 코드↔문서 일치 [ ] 인간 결정 영역은 전사 프로토콜 준수.

## 7. Stop Conditions (즉시 중단)
- **문서를 갱신할 수 없는데 코드만 완료로 넘기려 할 때** (Non-Negotiable — done 보류).
- 인간 결정 영역 문서를 DECISION block 없이 에이전트가 자율 갱신하려 할 때.
- Affected Documents를 구체 파일 없이 "문서 갱신함"으로 뭉뚱그릴 때.
