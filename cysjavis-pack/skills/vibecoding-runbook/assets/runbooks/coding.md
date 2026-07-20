# ruler/coding.md — 코드 변경 SOP

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: 모든 코드 변경은 **isolated edit이 아니라 system-level intervention**이다.

## 1. Applicability
일반 코드 변경 전반 — 버그 수정·기능 추가·성능 개선·잡무. 단, 행동 불변 구조 변경은 `refactor.md`,
비상 프로덕션은 `hotfix.md`, 데이터/스키마 비가역 이동은 `migration.md`로 분기한다.

## 2. Mandatory Context
`requirement.md`(무엇을) · 관련 `spec.md`(어떻게 작동) · `codebase-structure.md`(구조 경계) ·
변경이 닿는 `state-management.md`·`external/*.md`. 컨텍스트 없이 착수 금지.

## 3. Output Contract (8종 — 순서 고정)
1. **Intent Summary** — 무엇을·왜.
2. **Change Type** — `[bugfix|feature|refactor|performance|security|chore]` 중 택1.
3. **Assumptions** — 명시 가정([가정] 라벨). "보통/일반적으로/알아서" 금지.
4. **Impact Analysis** — Code / Structural / Data&State / Supporting / Ripple("If X changes, Y may
   break because Z") / Coupling Risk.
5. **Change Plan** — 변경 단계.
6. **Code Change Summary** — 실제 변경 요약.
7. **Verification Plan** — pass/fail 신호(테스트·명령).
8. **Propagation Checklist** — doc-sync·연쇄 갱신 대상.

## 4. Rules
- 아키텍처 일관성 > 국소 최적화. "그냥 동작하나 구조 위반=허용 수준 이하".
- source ↔ docs ↔ specs 정합. hidden coupling 발생 시 task는 incomplete.
- 승인 없이 금지: 하위호환 파괴 · SOT 변경 · APPROVED_TECH_STACK 밖 새 패러다임 · public API 제거.
- 의심 시 conservative interpretation + 표면화(가정을 숨기지 말고 드러낸다).

## 5. Verification
Verification Plan의 자동 검증(테스트·lint·type·regression)이 pass여야 완료. 검증 신호 없는 변경은
"검증 불가=미완"(헌법 2조).

## 6. Checklist
착수: [ ] Change Type 확정 [ ] Impact Analysis 작성 [ ] 상위 문서 로드.
완료: [ ] 8종 Output 채움 [ ] 검증 pass [ ] Propagation Checklist 이행 [ ] hidden coupling 0.

## 7. Stop Conditions (즉시 중단)
- **Breaking change를 정책·승인 없이 도입하려 할 때** (Non-Negotiable).
- SOT 변경·public API 제거가 필요한데 승인이 없을 때.
- Impact Analysis에서 Ripple을 특정할 수 없을 때(영향 범위 불명 → 중단·질문).
- 요구사항 공백을 창의력으로 메우려는 충동이 감지될 때.
