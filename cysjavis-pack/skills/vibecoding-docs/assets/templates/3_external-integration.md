---
# === NLC 계약 골격 (수정 금지 영역) ===
sot:
  - /docs/_root-sot.md
  - /rules.md
context:
  - /docs/_root-sot.md
  - /docs/rules/uepp.md
  - /docs/rules/scdp.md
  - /docs/rules/rcmp.md
  - /docs/requirement.md
  - /docs/tech-stack.md
layer: 2.95
identity: external-integration
relation:
  parent: requirement.md
  next: prd.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_boundary_between_internal_and_external
rules:
  - classify_sdk_api_webhook
  - security_first_design
  - interface_contract_required
  - official_docs_priority
outputs:
  - service_boundary
  - interface_contract
  - auth_model
  - error_modes
validation:
  - each_external_has_sot_doc
  - auth_designed_before_prd
path:
  output: /docs/external/<service>.md
---

# External Integration Spec (`/docs/external/<service>.md`)

> NLC 10단계 · 3 · 성격: 경계 명세 · 핵심 질문: "무엇과 연결되는가?"
> 외부 서비스 연동은 requirement와 PRD **사이**의 "환경·연동 정의 단계". requirement 확정 직후, PRD 작성 전에 한다.
> 핵심 명제: requirement는 "내가 할 일"을, external-integration은 "내가 하지 않을 일(외부 의존)"을 정의한다.
> 이 둘이 모두 있어야 PRD가 과도하게 확장되지 않고 현실적 범위를 갖는다.

## 왜 PRD 이전에 확정하는가 (4가지)
1. 설계 왜곡 방지(결제를 직접 구현한 뒤 SDK가 필요해지는 중복 작업 차단).
2. Userflow/DB의 입출력 인터페이스(Interface Contract)를 미리 결정.
3. **보안·인증(API Key/OAuth/Webhook secret/JWT)을 가장 먼저 설계** — PRD 이후 추가 시 전체 재설계.
4. 후속 5문서(userflow/database/spec/state-management/test)의 기술적 기반 SOT.

## 서비스별 명세 (채움)
- 서비스명: [FILL]
- 분류: [FILL: SDK | API | Webhook]
- Interface Contract(입력/출력): [FILL]
- 인증 모델: [FILL: API Key | OAuth PKCE | Webhook secret | JWT]
- Error Modes: [FILL: network·timeout·auth·quota·malformed·partial]
- SDK 버전 pin: [FILL]

## 조사 규율
딥리서치 + 출처 교차검증(공식 문서 우선, 블로그는 최근 3개월 이내만).
