# ruler/security.md — 보안 집행 런북

> 성격: 집행 규칙(HOW-NOW) · 상속: rules.md · _root-sot.md · uepp/scdp/rcmp (additive-only·override 금지)
> 한 문장: 보안은 **non-negotiable correctness** — 편의·속도로 면제되지 않는다(우선순위 1).

## 1. Applicability
로그인·DB·외부연동·로그·분석이 있으면 **필수**. 사용자 데이터·인증·권한·비밀정보를 다루는 모든 변경.

## 2. Mandatory Context
`external/*.md`(연동 경계) · `state-management.md`(권한 상태) · `env.template`(비밀 변수 정책) ·
Threat Model. AI 코드는 인간 대비 취약도가 높다 — 인프라 레벨 강제를 전제한다.

## 3. Output Contract
- **Threat Model (top5)** — credential stuffing · broken access control · injection · XSS/CSRF ·
  secrets 노출.
- **AuthN** — ARGON2/BCRYPT · MFA · rate limit · httpOnly/secure/sameSite 쿠키 · OAuth PKCE.
- **AuthZ** — RBAC/ABAC · 특권 엔드포인트별 서버 검사 · ownership 검사.
- **Secrets 처리** — 저장·주입·회수 경로.
- **Negative Test 목록** — 무권한·권한 상승 시도.

## 4. Rules — Non-Negotiable
- **특권 연산은 서버사이드 only**. client 주장(user id·role·pricing·entitlement) 신뢰 금지.
- **모든 특권 엔드포인트는 서버에서 검사** · **deny by default** · **ownership 검사**.
  **UI 숨김은 보안이 아니다**.
- Secrets는 git 커밋 금지 · client 임베드 금지 · **발견 시 즉시 제거**.
- 프로덕션 데이터플레인에 에이전트는 read-only(헌법 9조 · 인프라 레벨 강제).

## 5. Verification
`javis_vibecheck security`(Tier 1: secrets 스캔·git 이력 포함 / 전 테이블 RLS 활성 / 서버측 인가 /
관리자 도구 노출)를 배포 전 필수 통과. **negative test 강제** — 무권한·권한 상승이 실제로 차단되는지
자동 검증(막을 대상이 없는 게이트=미완).

## 6. Checklist
착수: [ ] Threat Model 작성 [ ] 특권 엔드포인트 목록화.
완료: [ ] 서버측 인가 전수 [ ] deny by default [ ] secrets 스캔 clean [ ] RLS 전 테이블 [ ]
negative test pass.

## 7. Stop Conditions (즉시 중단)
- **특권 연산을 클라이언트에서 처리하거나 client 주장을 신뢰하려 할 때** (Non-Negotiable).
- secrets가 코드·git 이력·client 번들에 노출된 것을 발견했을 때(즉시 제거·회수).
- 특권 엔드포인트에 서버측 인가·ownership 검사가 없을 때.
- 보안 게이트를 다른 규칙(속도·doc-sync 등)으로 면제하려 할 때(우선순위 1 — 면제 불가).
