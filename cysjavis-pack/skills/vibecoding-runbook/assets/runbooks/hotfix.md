# ruler/hotfix.md — 비상 프로덕션 대응 SOP

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: 핫픽스는 **개발이 아니라 사고 대응(Operation)** — "최소 변경으로 멈추는 것".

## 1. Applicability
프로덕션에서 지금 발생 중인 장애의 긴급 완화. 설계 개선·구조 정리·미학은 **금지 영역**이다.

## 2. Mandatory Context
장애의 가설-증거(로그·에러·재현·diff). 증거 없는 핫픽스는 착수 금지("이왕 고치는 김에
리팩토링"→변경 범위 폭발·2차 장애).

## 3. Output Contract
- **Severity** — `[SEV0|SEV1|SEV2|SEV3]`.
- **가설-증거** — 원인 가설 + 뒷받침 로그/에러/재현.
- **Mitigation Plan** — 무엇으로 멈추는가(우선순위: mitigation > 완벽 · flag/kill-switch > 깊은
  변경 · config > code).
- **Rollback Plan** — 되돌리는 절차(필수).
- **사후 항목** — 근본 원인 추적·정식 수정 티켓.

## 4. Rules
- 최소 변경으로 출혈만 멈춘다. 설계·구조·미학 개선 금지.
- flag/kill-switch로 끌 수 있으면 코드 깊이 파지 않는다. config로 될 일을 code로 하지 않는다.
- 가설-증거 기반만. 추측 수정 금지.
- **rollback plan 없는 hotfix = 실패**(Non-Negotiable).

## 5. Verification
장애 지표(에러율·다운·데이터 오염)가 실제로 멈췄는지 관측 검증. rollback을 실제로 실행 가능한지
사전 확인(가상의 롤백 금지).

## 6. Checklist
착수: [ ] Severity 판정 [ ] 가설-증거 확보 [ ] rollback plan 작성.
완료: [ ] 장애 지표 회복 관측 [ ] rollback 실행 가능 확인 [ ] 사후 정식 수정 티켓 발행.

## 7. Stop Conditions (즉시 중단)
- **rollback plan이 없거나 실행 불가일 때** (Non-Negotiable).
- 가설-증거 없이 추측으로 고치려 할 때.
- 핫픽스 범위가 "멈추기"를 넘어 개선·리팩터로 번질 때.
