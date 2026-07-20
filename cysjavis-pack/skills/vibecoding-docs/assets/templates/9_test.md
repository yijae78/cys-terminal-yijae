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
  - /docs/rules/tdd.md
  - /docs/spec.md
  - /docs/state-management.md
layer: 8
identity: tdd-root-spec
relation:
  parent: spec.md
  next: test-plan.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_verification_criteria
rules:
  - given_when_then
  - test_first_before_plan
  - no_code_inclusion
  - coverage_required
outputs:
  - unit_scenarios
  - e2e_scenarios
  - qa_plan          # {coverage, commands, failure_policy, report_path}
validation:
  - each_criterion_traces_to_spec
  - smoke_test_reports
path:
  output: /docs/test.md
---

# TDD Spec — 테스트 명세 (`/docs/test.md`)

> NLC 10단계 · 9 · 성격: 검증 기준 · 핵심 질문: "어떻게 올바름을 증명하는가?" · 도구: Codex CLI GPT5-coder.
> 위치 논리: spec.md 직후 + state-management.md 병행 구간이 공식 시점. "기능 정의 직후(what & how 명확)" + "구현 시작 전(before plan.md)".
> 3대 논리: ① spec 이후여야(기준이 spec에서 나옴) ② plan 이전이어야(테스트 없이 나누면 검증 불가 구조) ③ 병행 효율성.

## 문서 체인 (참고 — 각 별도 파일)
- `/docs/rules/tdd.md`: 테스트 루프의 법전(0-규칙 계층, 전역 상속). Red→Green→Refactor · FIRST · AAA · Test Pyramid(Unit70/Integration20/Acceptance10).
- `test-e2e.md`(layer8): Given-When-Then 시나리오, no_code_inclusion.
- `test-report.md`(layer8.1): repomix-output.xml + package.json 입력, 구조/의존성 비교.
- `test-setup-orchestrator.md`(layer8.0): runner 선택·config·샘플 테스트 생성.

## Unit Scenarios (채움)
```yaml
- scenario: [FILL]
  given: [FILL]
  when: [FILL]
  then: [FILL]
```

## E2E Scenarios (채움)
```yaml
- scenario: [FILL]
  given: [FILL]
  when: [FILL]
  then: [FILL]
```

## QA Plan
```yaml
coverage: [FILL]
commands: [FILL: 예 — npx playwright test]
failure_policy: [FILL]
report_path: /docs/test-report.md
```

> Smoke Test 강조: 성공/실패 자체가 아니라 **"실행되어 보고를 남길 수 있느냐"**가 핵심.
> repomix(선택): `npx repomix --ignore "./**/*.md"` — 외부 AI에 프로젝트를 이해시키는 정적 스냅샷. Claude Code/Codex가 폴더를 직접 열람 가능하면 불필요.
