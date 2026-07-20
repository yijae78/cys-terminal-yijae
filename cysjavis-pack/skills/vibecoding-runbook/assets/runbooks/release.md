# ruler/release.md — 배포/CI-CD 집행 런북

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> **security.md · integration.md 종속** — 가장 보수적으로 다룬다.
> 한 문장: **배포하는 용기가 아니라 배포를 되돌릴 책임을 강제한다** — 배포는 성공해도 롤백은 항상 가능.

## 1. Applicability
배포·CI/CD·버전 관리·롤백. CI/CD는 "AI의 즉흥적 수정을 현실 시스템에 반영할 자격을 심사하는 자동
검증 관문"이다(흐름: AI → CI → 통과 시에만 인간).

## 2. Mandatory Context
`security.md`(배포 전 보안 게이트) · `integration.md`(연동 상태) · `env.template`(환경 분리) ·
배포 대상 환경(dev/stage/prod)과 identity 분리(§C3).

## 3. Output Contract
- **Classification** — type · env · risk`[LOW~CRITICAL]` · downtime.
- **Versioning** — SEMVER · monotonic · **production immutable**.
- **Deployment Strategy** — `[BLUE_GREEN|CANARY|ROLLING|FULL_REPLACE|SERVERLESS]`.
- **Env Safety** — `.env.local`의 prod 승격 금지.
- **Feature Flags** — auth·billing·핵심 flow 필수, **prod 기본 OFF**.
- **Rollback Plan** — 되돌리는 절차(항상).

## 4. Rules — Non-Negotiable
- **즉시 전면 배포 없다** — 단계적(Preview → Flag → Canary → Full).
- production은 immutable · 버전은 monotonic(재사용 금지).
- CI 관문(build/lint/type/regression/contract) 통과 없이 배포 불가("코드가 스스로 무죄를 입증").
- 배포 전 보안 Tier 1 게이트 통과(security.md) + 에이전트 prod read-only(헌법 9조).
- 배포 identity와 에이전트 identity 분리 — 에이전트 환경변수에 prod 쓰기 자격증명 미배급(§C3).

## 5. Verification
CI 관문 전 통과 확인 · prod 권한 거부 E2E(agent identity로 prod 쓰기 시도 → 거부)를 상설 배치 ·
canary 지표 정상 후에만 확대 · rollback을 실제 실행 가능한지 사전 검증.

## 6. Checklist
착수: [ ] Classification·risk 판정 [ ] Deployment Strategy 선택 [ ] rollback plan 작성.
완료: [ ] CI 관문 pass [ ] 보안 Tier 1 pass [ ] 단계적 배포(canary) [ ] prod immutable/monotonic
[ ] rollback 실행 가능.

## 7. Stop Conditions (즉시 중단)
- **rollback plan 없이 배포하려 할 때 / 즉시 전면 배포하려 할 때** (Non-Negotiable).
- CI 관문·보안 Tier 1 게이트를 통과하지 못한 산출물을 배포하려 할 때.
- `.env.local`을 prod로 승격하거나 에이전트 identity로 prod에 쓰려 할 때.
- 이미 배포된 버전을 재사용(mutable)하려 할 때.
