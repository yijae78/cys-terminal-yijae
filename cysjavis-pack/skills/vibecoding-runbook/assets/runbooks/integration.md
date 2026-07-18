# ruler/integration.md — 외부 연동 집행 런북

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> **security.md 종속** — 연동은 보안 위에서만 성립한다.
> 한 문장: 외부는 unreliable·slow·version-unstable·partially documented로 취급한다.

## 1. Applicability
외부 API·SDK·Webhook 등 repo 경계 밖 의존을 도입·변경할 때. 경계 정의는 requirement 확정 직후·
PRD 작성 전에 한다(늦으면 userflow·DB 재작업 = 가장 비싼 실수).

## 2. Mandatory Context
`external/[service].md`(연동 SOT — 유일) · `security.md`(인증·비밀·webhook secret) ·
`requirement.md`(내부 경계). 공식 문서 우선 딥리서치 + 출처 교차검증(블로그는 최근 3개월).

## 3. Output Contract — Boundary Contract (Non-Negotiable)
- **Boundary Layer** — 외부를 adapter/client/service abstraction으로 래핑.
- **Interface Contract** — 입출력·인증 방식(API Key/OAuth/Webhook secret/JWT).
- **Error Modes** — network · timeout · auth · quota · malformed · partial.
- **회복 전략** — retry/backoff · circuit breaker · fallback.
- **SDK 버전 pin** — 정확한 버전 고정.

## 4. Rules — Non-Negotiable
- **핵심 도메인을 외부 API에 직접 결합 금지** — 반드시 boundary layer로 래핑한다.
- 연동 SOT는 `/docs/external/[service].md` **유일**.
- 모든 Error Mode에 대한 처리 경로를 갖는다(부분 실패·타임아웃 무시 금지).
- SDK/API 버전을 pin한다(version-unstable 전제).
- 보안(security.md)을 상속·준수한다 — 특히 인증·비밀·webhook 검증.

## 5. Verification
Error Mode별 실패 주입 테스트(timeout·quota·malformed에서 회복 전략이 작동하는지). boundary layer가
핵심 도메인과 외부를 실제로 격리하는지 대조. webhook secret·서명 검증 테스트.

## 6. Checklist
착수: [ ] external/[service].md 작성 [ ] 인증 방식 확정 [ ] Error Modes 열거.
완료: [ ] boundary layer 래핑 [ ] retry/circuit/fallback 구현 [ ] SDK 버전 pin [ ] 실패 주입 테스트
pass [ ] security 상속.

## 7. Stop Conditions (즉시 중단)
- **핵심 도메인 로직이 외부 API/SDK에 직접 결합되려 할 때** (Non-Negotiable — boundary 래핑 강제).
- Error Mode(특히 partial·timeout) 처리 없이 happy-path만 구현하려 할 때.
- 연동 인증·webhook secret 검증이 security.md를 우회할 때.
- SDK 버전을 pin하지 않고 latest에 의존할 때.
