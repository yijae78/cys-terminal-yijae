# ruler/migration.md — 데이터/스키마/계약 이동 SOP

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: 마이그레이션은 **개선(dev)이 아니라 이동(operation)** — 비가역 변경을 '시간을 나눠' 옮긴다.
> ⚠ 이 런북엔 HOW가 아니라 **HOW를 판단하는 RULE만** 담는다(구체 작업 지시를 넣으면 구조가 깨진다).

## 1. Applicability
데이터·스키마·계약의 비가역 변경. 환경 이전(Environment Migration)·replatforming도 포함하되, 순수
"물리 이전"만이면 rules 계층 생략 가능. 그 외엔 rules 계층을 **먼저** 세운다.

## 2. Mandatory Context
현행 스키마/계약의 SOT(`database.md`·`external/*.md`) · 백업 상태 · Risk 등급 근거. rules 계층
(AGENTS·rules·@ruler/migration)이 없으면 "AI는 복사기"가 된다 — 먼저 세운다.

## 3. Output Contract
- **Risk** — `[LOW(가산)|MEDIUM(dual-read/write)|HIGH(파괴·데이터 손실)]`.
- **Compatibility Strategy** — dual-write/read · shadow fields · versioned.
- **Phased Plan** — Phase0 Preparation(백업·비파괴 확장·flag) → Phase1 Compatibility
  Window(dual-read/write·모니터링) → Phase2 Cutover → Phase3 Cleanup.
- **Rollback / Roll-forward Plan** — 없으면 invalid.

## 4. Rules
- **백업 없이 삭제 금지 · 파괴 먼저 금지 · 즉시 cutover 가정 금지**.
- 명시된 모든 table·column이 누락되지 않도록 꼼꼼히 점검.
- 확장(비파괴)을 먼저, 파괴(정리)를 맨 나중(Phase3)에.
- **rollback/roll-forward 없으면 invalid**(Non-Negotiable).

## 5. Verification
각 Phase에서 dual-read/write 정합·데이터 무손실을 관측. Compatibility Window 모니터링 지표가 정상일
때만 Cutover. Cleanup 전 롤백 가능성 유지.

## 6. Checklist
착수: [ ] Risk 판정 [ ] 백업 확인 [ ] Compatibility Strategy 확정 [ ] rules 계층 존재.
완료: [ ] Phase0~3 순서 준수 [ ] 데이터 무손실 검증 [ ] rollback/roll-forward 실행 가능.

## 7. Stop Conditions (즉시 중단)
- **백업 없이 파괴적 변경을 하려 할 때 / rollback·roll-forward 계획이 없을 때** (Non-Negotiable).
- 파괴(삭제·컬럼 drop)를 Compatibility Window 이전에 하려 할 때.
- 즉시 cutover를 가정하고 dual-read/write 단계를 건너뛰려 할 때.
