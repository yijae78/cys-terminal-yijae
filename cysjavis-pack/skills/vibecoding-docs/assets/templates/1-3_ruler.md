# ruler/*.md — Execution Rulers (시행령 · 런북)

> NLC 10단계 · 1-3 (`/ruler/*.md`) · 성격: 집행 규칙(HOW-NOW) · 핵심 질문: "이 단계는 어떻게 수행하는가?"
> AGENT = 누구인지, rules = 무엇이 불변인지, **ruler = 이번 작업을 어떻게 수행하는지**(선택 적용).
> 이 파일은 필수 ruler 10종의 공통 골격 + 인덱스 템플릿이다. 각 런북을 `ruler/<name>.md`로 실체화한다.

<!--
[.ruler vs @ruler 절대 구분 — 치명적]
- 실제 규칙 파일은 `ruler/`에 둔다.
- `.ruler/`는 시스템/툴/엔진의 기록실(applied.lock·index.json·history.log) — 규칙 내용을 넣지 말 것.
- `@ruler`는 프롬프트에서 "적용하라"고 호출하는 표기(사람의 스위치).
- 비유: ".ruler는 AI의 기억, @ruler는 인간의 명령 / .ruler는 배선, @ruler는 스위치."

[rules.md vs @ruler 결정트리 — 3문항]
① 항상 지켜야 하는가  ② 작업 종류가 바뀌어도 유효한가  ③ 위반 시 즉시 중단인가
→ YES 2개 이상 = rules.md 로.  NO 2개 이상 = @ruler 로.

[@ruler 절대 금지] 윤리·안전·품질 하한선·테스트 의무·권한 제한은 @ruler에 넣지 않는다(작전이 헌법을 무력화 금지).
-->

## 공통 골격 (모든 ruler 파일 공유)
```
1. Applicability          # 이 런북이 적용되는 작업 유형
2. Mandatory Context      # 반드시 읽어야 할 상위 문서
3. Output Contract        # 산출물의 정형 구조
4. Rules                  # 이 작업의 행동 규칙
5. Verification           # 완료 검증 방법(pass/fail 신호)
6. Checklist              # 착수·완료 체크리스트
7. Stop Conditions        # 즉시 중단해야 하는 조건
```

## 필수 ruler 파일 10종 (인덱스 — 각각 위 골격으로 작성)
- **coding.md** — 코드 변경 SOP. Output 8종: Intent Summary → Change Type[bugfix|feature|refactor|performance|security|chore] → Assumptions → Impact Analysis → Change Plan → Code Change Summary → Verification Plan → Propagation Checklist. Breaking change는 정책 없이 금지.
- **refactor.md** — 행동 동일성(Behavior Equivalence) 보장 하에서 구조·결합도만 변경. 외부 행동 불변·입출력 동등·public contract 안정·새 기능 없음·버그 안 고침. Type[extract|inline|rename|split|merge|reorder|simplify|decouple].
- **hotfix.md** — 비상 프로덕션. "최소 변경으로 멈추는 것"(설계 개선·구조·미학 금지). Severity[SEV0~3]. mitigation > 완벽, flag/kill-switch > 깊은 변경, config > code. rollback plan 없는 hotfix = 실패.
- **migration.md** — 데이터/스키마/계약의 비가역 변경을 시간을 나눠 이동. Risk[LOW|MEDIUM(dual-read/write)|HIGH(파괴·손실)]. Phased: Phase0 Preparation → Phase1 Compatibility Window → Phase2 Cutover → Phase3 Cleanup. HOW가 아니라 HOW를 판단하는 RULE만.
- **test-only.md** — 프로덕션 코드 절대 미변경, 검증만. Given-When-Then·관측 행동 테스트. Forbidden(Hard): 프로덕션 수정·assertion 약화로 통과·실패 은폐.
- **doc-sync.md** — 코드 변경 시 문서(SOT·Spec·RCMP) 동반 갱신 강제. Change Classification[behavioral|structural|contractual|stateful|config]. Affected Documents는 명시적 파일 나열("documentation updated" 만으론 invalid).
- **state.md** — 상태 다루는 방법(HOW 런북). ⚠ `/docs/state-management.md`(WHAT 설계 SOT)와 대체 불가. Core: State=Memory not Variables · Single SOT · No Shadow State · Unidirectional Flux. Boundary(Local/Page/App-global/Server). Async&Race(dedupe·cancellation·optimistic·stale-while-revalidate).
- **security.md** — 로그인/DB/외부연동/로그/분석 있으면 필수. Threat Model top5(credential stuffing·broken access control·injection·XSS/CSRF·secrets 노출). 특권 연산은 서버사이드 only. AuthZ: 모든 특권 엔드포인트 서버 검사·deny by default·ownership 검사·UI 숨김은 보안 아님. Verification에 negative test 강제.
- **integration.md** — 외부 API/SDK/Webhook. security.md 종속. 외부는 unreliable·slow·version-unstable로 취급, 핵심 도메인을 외부에 직접 결합 금지, boundary layer(adapter/client)로 래핑. SOT = `/docs/external/[service].md`. Error Modes + retry/backoff/circuit breaker/fallback. SDK 버전 pin.
- **release.md** — 배포/CI-CD/버전/롤백. security·integration 종속. Versioning(SEMVER·monotonic·production immutable). Deployment[BLUE_GREEN|CANARY|ROLLING|FULL_REPLACE|SERVERLESS]. Feature Flags(auth·billing·핵심 flow 필수, prod 기본 OFF). "배포하는 용기가 아니라 배포를 되돌릴 책임을 강제."

## 추천 폴더 배치
`rules.md`(짧고 강함) + `ruler/`(00_global · 10_coding · 20_testing · 30_dependency · 40_security).

## ruler.toml (배포 오케스트레이터 설정 — 채움)
```toml
default_agents = ["cursor", "codex", "claude"]
# [agents.claude] output_path = "CLAUDE.md"
# [mcp_servers.*] ...
```
