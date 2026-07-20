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
  - /docs/project.md
layer: 1.5
identity: environment-template
relation:
  parent: project.md
  next: tech-stack.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_runtime_environment_contract
rules:
  - uppercase_snake_case
  - comment_required
  - no_secret_values
  - no_unused_vars
  - no_hardcoding
  - fail_fast_on_missing
outputs:
  - env_variable_list
  - validation_policy
validation:
  - every_var_documented
  - no_undeclared_var_allowed
  - test_vars_excluded_from_prod
path:
  output: /docs/environment/env.template.md
---

# Environment Template (`/docs/environment/env.template.md`)

> NLC 10단계 · 2-7 · 성격: 환경 계약 · 핵심 질문: "어떤 실행 환경이 필요한가?"
> 실행 환경의 SOT. 코드보다 먼저 검증된다. **정의되지 않은 변수는 존재해선 안 된다.**
> 규칙: 대문자 SNAKE_CASE · comment 필수 · secret 값 금지 · 미사용 금지 · 하드코딩 금지. 검증 실패 시 fail-fast.
> 검증기 부산물: `/scripts/validate-env.js`(SOT = 이 문서). `npm run validate:env`. env 변경은 문서 변경이 아니므로 ruler apply 불필요.

```dotenv
# ── NODE_ENV ──
NODE_ENV=                # development | test | production

# ── App Core ──
APP_NAME=                # [FILL] 앱 이름
APP_BASE_URL=            # [FILL] 기본 URL

# ── Security & Auth ──
AUTH_SECRET=             # [FILL] 서버 전용 · 절대 커밋 금지 (secret은 값 없이 키만 선언)

# ── External Services (서비스 단위로 분리) ──
# [FILL: SERVICE]_API_KEY=   # [FILL] 외부 서비스 키

# ── Database ──
DATABASE_URL=            # [FILL] DB 연결 문자열

# ── Storage ──
STORAGE_BUCKET=          # [FILL] 스토리지 버킷

# ── Logging ──
LOG_LEVEL=               # info | error | warn | debug

# ── Test 전용 (프로덕션 금지) ──
# TEST_ONLY_FLAG=        # [optional] 테스트 환경 전용
```

## 검증 정책 (validate-env.js)
- 필수 누락 → FAIL · 미지 변수 → FAIL · 빈 필수값 → FAIL.
- optional 마커: `# optional` 또는 `[optional]`.
- 실행 시점: RCMP 작성 직후부터 즉시. env 추가/삭제/이름변경마다, External/DB/Auth 진입마다, 배포/CI 직전.
