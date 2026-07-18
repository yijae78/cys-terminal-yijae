# NLC 다이제스트 (11400–16478행 전 범위 정독 완료): 브릿지/부트스트랩 개조 + 문서 파이프라인 (2-5 ~ 4-2)

## 저자 최상위 경고 (11400행, 섹션 제목 verbatim)
> **"[ 필독 / 필수 시행 : CLAUDE.md를 브릿지/부트스트랩으로 개조 ← 이 작업 하지 않으면 모든 md 작업이 무의미!!! ]"**

핵심 질문: "문서를 만들어 놓으면 자동 반영되는가?" → **답: 자동으로 일어나지 않는다.**
- verbatim: "md 문서를 만들어 놓는 것만으로는 아무 일도 자동으로 일어나지 않는다. **'언제, 어떤 경로로, 어떤 AI에게 먹일 것인가'를 명시적으로 수행해야 비로소 작동한다.**"
- "❌ 문서 생성 = 자동 반영 ❌ / ✅ 문서 생성 + 적용 행위 = 시스템 작동"

---

## 1. CLAUDE.md 브릿지/부트스트랩 개조 — 방법·이유·구조 (최우선)

### 1-1. "헌법은 완성, 집행은 아직" — 문서 지위표
| 단계 | 문서 | 성격 |
|---|---|---|
| 1-1 | AGENT.md | 정체성(WHO) |
| 1-2 | rules.md | 불변 규범(WHAT MUST NEVER BREAK) |
| 1-3 | @ruler/*.md | 집행 절차(HOW) |
| 2-1 | _root-sot.md | 판단의 근원(WHY) |
| 2-2 | uepp.md | 오류 예방 장치 |
| 2-3 | scdp.md | 자동 상속 규칙 |
| 2-4 | rcmp.md | 구조 지도 |
이것들은 "규칙 그 자체"이지 "자동으로 AI가 읽는 메커니즘"이 아니다.

### 1-2. "자동"의 오해 제거 (핵심 개념)
- **"SCDP의 '자동'은 의미 자동이지, 로딩 자동이 아니다."** 자동 상속 = AI가 문서를 읽은 이후의 행동 규칙 / 자동 로딩 = 그런 기능 없음.
- **"AI는 파일 시스템을 스스로 훑지 않는다."**

### 1-3. "사용한다"의 3방법: A. 컨텍스트 명시적 주입 / B. Ruler로 강제 적용 / C. 인간이 작업 프로토콜로 강제.

### 1-4. `ruler apply`의 본질 (경우 1: IDE + Ruler CLI)
- **apply = 배포, 로드 = 실행 시 사용. 둘 다 되어야 "아무것도 안 해도 되는 상태".**
- ruler apply가 하는 일: ① rules.md + @ruler/*.md 읽음 → ② 에이전트별 규칙 파일 형식으로 변환 → ③ `.ruler/`에 기록(applied lock/index/history). 요약: "규칙을 가공해 에이전트가 읽을 형태로 배포".

### 1-5. "apply 후 끝" 3가지 필요조건 (동시 충족)
1. ruler apply가 에이전트가 자동으로 읽는 파일을 생성/갱신
2. 에이전트가 매 세션 그 파일을 자동 로드
3. 규칙 변경 시마다 ruler apply 반드시 수행
- 하나라도 빠지면 "apply 했는데 세션에서 규칙 안 붙는 사고"가 반드시 난다.

### 1-6. Auto-load 2가지 정석
- **A안(브릿지, 깔끔)**: .ruler/는 에이전트가 안 읽으므로, ruler apply 결과를 에이전트 네이티브 파일(Claude=CLAUDE.md, Cursor=.cursorrules, Windsurf=.windsurfrules)로 sync.
- **B안(부트스트랩 래퍼, 권장·에이전트 불문)**: 실행 자체를 래퍼로 강제 — 매 실행 ①ruler apply ②규칙 파일 최신 확인 ③에이전트 실행을 한 덩어리로. 구현: make/just agent, scripts/agent.sh, 쉘 alias(claude()/codex()) 가로채기. 규율: "직접 실행 말고 래퍼로만".

### 1-7. ★ CLAUDE.md에 넣을 부트스트랩 로더 (전문 verbatim, 11760행)
```
# =========================================================
# Claude Code Bootstrap Loader
# (Single Entry Point for Project Constitution)
# =========================================================

# --- 1. Agent Identity (WHO) ---
@AGENT.md

# --- 2. Global Immutable Rules (WHAT MUST NEVER BREAK) ---
@rules.md

# --- 3. Root Source of Truth (WHY) ---
@docs/_root-sot.md

# --- 4. Meta-Constitution (HOW RULES PROPAGATE) ---
@docs/rules/uepp.md
@docs/rules/scdp.md
@docs/rules/rcmp.md

# --- 5. Always-On Execution Rules (OPTIONAL, CAREFUL) ---
# 아래는 "항상 적용해도 되는 것만" 넣어라
# @ruler/security.md
# @ruler/state.md
```
- Claude Code는 실행 시 `./CLAUDE.md`(또는 `./.claude/CLAUDE.md`) 자동 로드, `@path/to/file` import 지원. 표준 구조: CLAUDE.md(최우선) / .claude/rules/*.md(모듈) / ~/.claude/CLAUDE.md(전역 개인) / CLAUDE.local.md(로컬, 자동 gitignore).
- 부트스트랩 추가 후 **ruler apply** 실행.
- 검증 루틴(필수): 세션 첫 턴에 "지금 로드된 규칙/메모리 요약을 말해봐" sanity check → '규칙 미적용 세션' 참사 예방(실제 안 읽히는 이슈 리포트 존재, GitHub anthropics/claude-code#7953 인용).

### 1-8. 언제 무엇을 (실행 타이밍 표, 11733행)
| 상황 | 해야 할 일 |
|---|---|
| 새 프로젝트 시작 | AGENT→rules→@ruler→_root-sot→docs/rules |
| 새 AI 세션 | 상위 문서 전체 재주입 |
| **규칙 수정** | **ruler apply** |
| 설계 문서 수정 | ❌ 안 함 |
| 코드 수정 | ❌ 안 함 |
| AI 이상 판단 | Root SOT 재주입 |
| 구조 헷갈림 | RCMP 재확인 |

### 1-9. 저자 핵심 철학 (11747행)
> "이 시스템은 '자동화된 AI 프레임워크'가 아니다. **'인간이 통제권을 유지하기 위한 헌법 체계'다.**" → "AI가 자율적으로 읽으면 실패 / 인간이 적용 시점을 통제하면 성공."

---

## 2. 도구별 브릿지 방법 (어떤 AI에서 무엇을) — 도구 분담 핵심

공통 원칙: "규칙 SOT는 rules.md + ruler/*.md로 유지하되, 각 AI가 '시작 시 반드시 읽는 1번 파일'을 공통으로 만들고 연결한다." 공통 부트스트랩 파일 = **AGENTS.md**(또는 PROJECT_BOOTSTRAP.md).

**AGENTS.md에 들어갈 4가지** (짧고 강제적 — "길게 쓰면 망한다"):
1. 규칙 SOT 선언(rules.md+ruler/*.md가 유일한 법) 2. 적용본 우선순위(.ruler/ 존재 시 1순위) 3. 작업 시작 절차(규칙 읽기→작업→필요시 ruler apply) 4. 트리거 정의(언제 재실행).
- ★철칙: **"AGENTS.md는 '규칙 내용'이 아니라 '규칙을 로드하는 절차'만 담는다."**

### 도구별 자동 로드 진입점 (매핑표)
| 도구 | 진입점/방식 | 비고 |
|---|---|---|
| **Claude Code** | CLAUDE.md 자동 로드 + @import | "프로젝트 들어오면 헌법이 자동으로 깔림" |
| **Codex CLI** | ❌ 자동 로드 없음 → **부트스트랩 스크립트 + 단일 컨텍스트 파일(codex-context.md)** | "법전을 들고 들어가서 일을 시킨다". `codex --prompt-file codex-context.md` |
| **Cursor** | .cursor/rules/*.mdc (자동 적용) | 00_bootstrap.mdc(항상 로더) + 상황별 .mdc |
| **VS Code+Copilot** | .github/copilot-instructions.md | @import 약함 → '헌법 색인(index)'으로 |
| **VS Code+Continue** | .continue/rules/*.md | 파일명 사전순, rules 무시 이슈 → 로드 확인 루틴 |
| **VS Code+Claude 확장** | CLAUDE.md / .claude/rules/* | Claude 방식 그대로 |
| **Antigravity** | "주력 전제 성립 안 함"(파이썬 이스터에그) | 래퍼 + 단일 컨텍스트 파일 |
| **ChatGPT/Claude/Gemini 대화형** | ❌ → 수동 주입 | AGENT/rules/_root-sot/docs/rules 붙여넣고 "전역 컨텍스트다" 선언 후 persona/project/requirement |
| **Google AI Studio/외부 LLM** | ❌❌ 구조적 우회 | _root-sot.md + docs/rules/*.md를 Context 선언 블록으로 먼저 먹인 뒤 persona/project/spec |

### ★ Codex CLI 정석 (저자 특별 강조 — "자동 로드 개념이 훨씬 약하다")
- 파이프라인: **문서 수정 → ruler apply → codex-context 빌드 → codex 실행**. (Claude와 달리 ruler apply는 "반쪽짜리", 반드시 컨텍스트 빌드가 뒤따름)
- `scripts/run-codex.sh`가 유일 진입점: ①ruler apply ②AGENT/rules/_root-sot/uepp/scdp/rcmp(+선택 @ruler) 합침 ③codex-context.md 생성 ④System/Context 주입 후 사용자 프롬프트.
- Context 설계 원칙: Root SOT/UEPP/SCDP/RCMP/rules.md/AGENT.md는 **전문 그대로(축약 금지)**, @ruler만 선택 포함. "Codex는 항상 '의식(ritual)'으로 시작해야 한다."

### ★ `#`는 주석이 아니다 — 프리프로세서 vs 프리로드 (14971행)
- 마크다운 `#`는 헤더/**지시어(header pragma)**이지 주석 아님. `#include "..."`는 Ruler CLI 프리프로세서가 처리하는 전처리 명령.
- **프리프로세서 방식(codex cli 등)**: #include를 맨 윗줄 단독 라인 배치 → 반드시 ruler apply해야 확장·병합. /out/docs/...가 확장 결과물.
- **전방 선언(Forward Declaration)**: 아직 없는 파일을 미리 #include 선언하는 것은 오류 아닌 Ruler 의도적 설계 — "상속 포인트(Anchor)" 미리 고정(C언어 forward declaration과 동일).
- **프리로드 방식(AI Studio 등 LLM 직접 먹임)**: #include는 장식일 뿐 → 해당 파일 내용을 컨텍스트로 선주입하는 것이 실동작.

---

## 3. 각 문서 역할·경로·프롬프트 핵심 조항 (2-5 ~ 2-10)

### 2-5. Persona (/docs/persona.md)
- 지위: AGENT.md 이후, Root SOT/UEPP/SCDP/RCMP 존재 전제에서 **"사고 성향·판단 스타일만" 정의**. rules도 @ruler도 아님.
- "조건부 자동": A(CLAUDE.md 존재)+B(1-1~2-4 명시 참조)+C(세션이 그 CLAUDE.md 로드) 충족 시 persona.md는 1-1~2-4를 "헌법처럼 깔고" 생성. **"CLAUDE.md는 '자동 상속 엔진'이지 '마법 버튼'이 아니다."** 세션·문서·툴 바뀌면 "다시 로드됐는지 확인하는 의식(ritual)" 필수.
- 프롬프트 구조: 판단 우선순위(일관성>재현가능성>명시적근거>구조적명확성>최소가정), 경계 먼저 정의, Anti-Patterns, 충돌 우선순위(_root-sot>rules>uepp>scdp>rcmp>persona).
- ★ **Claude Code Auto-Load Addendum (Persona Enforcement Layer)**: 자동 로드 선언(초기 사고 프레임 pre-apply, 사용자 프롬프트보다 우선), 상속 규칙(모든 /docs/*.md 해석 렌즈), Hard Stops("빨리 대충" 거부), 세션 지속성(단 한 번 로드), Final Lock("자동 로드 환경에서 Persona 흐려짐 방지 고정 장치").

### 2-6. Project (/docs/project.md)
- 지위: 프로젝트 단위 최상위 기획 기준점. Persona가 해석할 대상, Requirement/PRD 상위. "무엇을"보다 **"왜·어디까지"**.
- 핵심: 목적(문제/의도 중심, "잘 만들어보자" 류 금지), 성공의 정의(정성/정량=이후 PRD/테스트 판단 기준점), 범위(In/Out of Scope=스코프 크리프 방지), MVP, 제약, 의사결정 원칙.

### 2-7. env.template (/docs/environment/.env.template.md)
- 지위: 실행 환경의 SOT, 코드보다 먼저 검증. .env 템플릿이자 검증 기준. **정의 안 된 변수는 존재해선 안 됨.**
- 규칙: 대문자 SNAKE_CASE, comment 필수, secret 금지, 미사용 금지, 하드코딩 금지. 섹션: NODE_ENV/App Core/Security&Auth/External(서비스 단위 분리)/DB/Storage/Logging/Test전용(프로덕션 금지). 검증 실패 시 fail-fast.

### 2-7-1. validate-env.js (/scripts/validate-env.js)
- SOT=.env.template.md, .env/.env.local 검증. 정책: 필수 누락→FAIL, 미지 변수→FAIL, optional 마커(# optional/[optional]), 빈 필수값→FAIL. `npm run validate:env`.
- **언제**: "즉시, RCMP 작성 직후부터". env 추가/삭제/이름변경마다, PRD/External/DB/Auth 진입마다, 배포/CI 직전. ★ **env 변경은 문서 변경 아니므로 ruler apply 불필요**(별개 층위).

### 2-8. Tech Stack (/docs/tech-stack.md)
- 지위: 기술 선택의 최종 결과(선언문), 비교 문서 아님. SuperNext(Next.js App Router+TS=Default Lock), Supabase, Vercel. 동일 역할 중복 금지, "나중에 바꾸자" 금지.
- ★ 추천 시 핵심: ①AI가 잘 구현(인기 기술 유리, Svelte/Tauri는 학습데이터 적어 품질 낮음) ②잘 유지보수(Next.js-Vercel/Flutter-Google 안전, Nest.js 개인 유지보수 주의) ③Breaking Change 적음(Material UI 나쁨, shadcn 유리).
- 성찰 프롬프트: **'간결함' precision pruning** — "불필요한 단어·수식어·중복·서사형·감성 문구 제거. 코드 오염=오류·할루시네이션 원천."

### 2-9. Codebase Structure (/docs/codebase-structure.md)
- 지위: 코드베이스 구조 SOT(구조 헌법), 현재 코드 설명 아님. 구현 이전 확정.
- 4레이어(Presentation⟂Application⟂Domain⟂Infrastructure) + **의존성은 항상 안쪽을 향한다**. Tree: src/{presentation,application,domain,infrastructure,shared,tests}.
- SOLID: S(변경 이유 하나)/O(고치지 말고 추가)/L(치환해도 안 깨짐)/I(작게 쪼개라)/D(구현 아닌 계약에 의존).
- 4대 분리 판단 기준(AI Studio 추천용 verbatim): ①presentation↔business logic ②pure business logic↔persistence ③internal logic↔외부연동 contract/caller ④하나의 모듈=하나의 책임.
- 핵심 원리: "요구사항 변경 시 **영향 범위가 좁고 명확할수록** 좋은 구조. 고칠 곳이 적은 것보다 '어디인지 명확한 것'이 중요. 구조 품질=속도 아니라 **변경 대응 비용**." RCMP가 영향 그래프 정의→문서 구조가 "변경 시뮬레이터". 완료 후 ruler apply.

### 2-10. Requirement (/docs/requirement.md)
- 지위: **"무엇을 만들어야 하는가"의 최종 판결문(SRS)**. "흐릿하면 뒤 문서 전부 흐릿. AI는 요구사항 공백을 창의력으로 채운다→대형 사고 출발점. 차갑고 건조하게, 법률 문서처럼."
- 명시 안 된 기능=존재하지 않는 것. 전제(Next.js/Supabase/Vercel=변경 대상 아님). FR-[번호] 형식(설명/입력조건/처리규칙/결과조건/예외조건, UI 안 다룸). 명확성 체크리스트("AI가 빈칸을 창의력으로 메울 필요 없는가?").
- **SuperNext 템플릿 사용 시: Requirement부터 시작(2-8 Tech Stack, 2-9 Codebase Structure 생략).**
- 부산물 **RTSV(/docs/rules/requirement-techstack-validation.md)**: 요구사항↔기술스택 일관성 자동 판정 규칙(설명서 아닌 판정 규칙), 위배 시 구현 즉시 중단. "요구사항은 계약, 기술 스택은 능력이 아니라 **책임**, AI는 이 경계를 넘지 않는다."

---

## 4. 실전4: 마이그레이션 후 고난도 풀스택 (15025행)
- ★ **마이그레이션 전에 rules 계층을 먼저 만드는 것이 정석·거의 필수.** "마이그레이션은 코드를 옮기는 게 아니라 기존 코드의 의미를 새 체계로 재해석하는 작업", 재해석 기준이 rules 계층. rules 없이 시작하면 "AI는 복사기"(의미 해석 없이 구조만 흉내)→"프레임워크만 바뀐 리팩토링".
- 최소 세트: ①AGENTS.md(태도 고정 — "복사자 아닌 재설계자") ②rules.md(의사결정 헌법) ③**@ruler/migration.md**(전용 시행령 — 목적/허용·금지 변경/롤백/SOT 정의). ★migration.md엔 **HOW가 아니라 HOW를 판단하는 RULE만**(구체 작업 지시 넣으면 구조 깨짐).
- 정석 순서: AGENTS→rules→@ruler/migration→(선택)_root-sot→**마이그레이션 실행**→구조 안정화→PRD/Userflow/Spec. 예외: "단순 물리 이전"만 rules 없이 가능.
- 프롬프트: "모든 기능·코드베이스 빠짐없이 완벽 통합. **실행시간 단축 행위 절대 금지**." 이후 통합 코드↔@docs/*.md 일치(수행 안 한 내용은 **주석 처리**, "주석은 실제 구현 대상 아님" 명기).
- ★컨텍스트 엔지니어링(15539행, 카파시 《메멘토》 비유): "더 나은 토큰=더 나은 결과". 최악=부정확>누락>노이즈. **컨텍스트 창 40%부터 효용 체감**. ①서브 에이전트(역할 아닌 컨텍스트 제어) ②빈번·의도적 압축 ③점진적 공개 ④온디맨드 압축("나쁜 한 줄의 계획=수백 줄 나쁜 코드"). MCP 절약: `export ENABLE_EXPERIMENTAL_MCP_CLI=true`.
- TDD 프롬프트: "Let's use a Test-driven development approach where we write the tests for the feature first and then implement it."
- 외부 DB: "**DB 설계는 초반, 실제 연결 코드는 후반**"(DB 구조=도메인 구조, Supabase RLS/Auth가 설계에 영향).

## 실전2-1: 목업 후 md 문서만으로 바닥부터 (15410행)
- SOT 프로토콜 숙지 프롬프트: SOT 필요조건 7(가장 먼저 정의/유일성SSOT/불변성/전역성/접근용이/간결/항상 참조). "SOT=전체 생태계 좌우 헌법, AI·개발자·코드가 공유하는 유일한 진실."
- Vibe Coding Architect V3.0: 인터뷰(서비스/대상/디자인/유지보수)→웹검색 프레임워크 선정(데이터→Streamlit, 빠른출시→Rails, 화려한UI→Next.js/Svelte)→PRD.md/TRD.md/Tasks.md 3종 출력.
- 목업 TSX/geminiService.ts/CSS는 Next.js 재활용 가능(브라우저 직접 호출→서버 Route 설계). Antigravity에서 Claude CLI 제어: `claude --model opus --prompt "..."`, 자동 실행 "set SafeToAutoRun to true".

---

## 5. ★ 경계의 정의 (Boundary Definition) — 15703행
- **외부 서비스 연동은 requirement와 PRD 사이 "환경·연동 정의 단계"**. requirement(무엇을 만들 것인가) 확정 **직후, PRD 작성 전**에 해야 한다.
- ★핵심 명제: "설계에서 가장 중요한 것은 **경계(boundary)** — 내부(내가 만들 영역)와 외부(가져올 영역)를 나누는 선. **requirement는 '내가 할 일'을 정의하고, external-integration은 '내가 하지 않을 일(외부 의존)'을 정의**한다. 이 둘이 모두 있어야 PRD가 과도하게 확장되지 않고 현실적 범위를 가진다."
- 3단계 경계표: ①requirement.md(무엇을 만들?→경계의 필요성) ②external-integration.md(무엇을 외부에서?→경계의 위치·형태) ③prd.md 이후(안쪽 설계?→경계 내부 구조).
- PRD 이전 확정 이유 4: ①설계 왜곡 방지(결제 직접 구현 후 SDK 필요=중복작업) ②Userflow/DB 입출력 인터페이스(Interface Contract) 미리 결정 ③**보안·인증(API Key/OAuth/Webhook secret/JWT) 가장 먼저 설계** — PRD 이후 추가 시 전체 재설계 ④후속 5문서(userflow/database/spec/state-management/test) 기술적 기반 SOT. "②단계 늦어지면 userflow·DB 모두 재작업=현장 가장 비싼 실수."
- 저장: /docs/external/서비스이름.md. SDK/API/Webhook 분류 후 딥리서치+출처 교차검증(공식문서 우선, 블로그는 최근 3개월).

---

## 6. ★ PRD 및 prd-critic (섹션 4, 15785행)

### PRD (/docs/prd.md)
- **Codex CLI + GPT5-추론 모델** 선택하여 YAML 프롬프트. 헤더: SOT/Context(_root-sot, universal-sot-prompt, system-context-directive, root-context-map, persona, project, tech-stack, codebase-structure, requirement), layer:3, identity:prd, relation(parent:external-integration.md, next:design/ui.md), inheritance(additive-only, override-prohibited, root-sot-priority, uepp/scdp/rcmp-auto, context-propagation-invariant).
- goal: define_page_feature_entity_structure. rules: separate_feature_entity, entity_is_db_view, map_feature_to_entity_rw. validation: feature_refs_entity, entity_persistence_only, techstack_consistent, schema_conformance.
- **AI Studio 대안**: 위 내용 전부 입력 + <사용 기술 스택>/<페르소나>/<프로젝트 요구사항>/<코드베이스 구조> 첨부.

### ★ prd-critic (/docs/prd-critic.md) — 비판 문서 개념
- **PRD의 일관성·확대해석을 검증하는 별도 비판 문서.** Codex CLI GPT5-추론. layer:3.1, identity:prd-critic, parent:prd.md.
- goal: prd_consistency_check. **checks**: scope_diff, missing_items, integration_alignment, feature_entity_mapping, annotation_presence, techstack_consistency, env_reference_integrity.
- **rules**: add_nothing_unless_specified(명시 안 된 것 추가 금지), no_feature_without_entity, integration_follows_external_spec, techstack_must_match_requirement, nodes_must_have_entities.
- **output_schema**: summary, findings[{id, type(scope_diff/missing_item/integration_error/mapping_error/annotation_missing/tech_mismatch/env_gap), where, description, severity(blocker/major/minor), fix}], patches, validation_result{ok, counts}.
- 핵심 의도: **"PRD에서 확대해석된 기능이 없는지 점검. 빠른 프로젝트 완성 최우선. 20년차 시니어 관점으로 깐깐하게."** = PRD가 requirement를 넘어 임의 기능을 부풀리지 않았는지 적대적으로 감사하는 층. 완료 후 ruler apply.

---

## 7. FDS 및 UI 기획서 (4-1, 4-2)

### 4-1. FDS Root Spec (/docs/rules/fds.md)
- Codex CLI GPT5-추론. layer:3.1, identity:fds-root-spec, parent:prd.md.
- sections: ethos/tokens/components/naming/layout/accessibility/responsiveness/governance.
- **ethos**: clarity_over_complexity, function_over_aesthetics, predictable_over_surprising, accessible_over_exclusive.
- tokens(color/typography/spacing/radius/shadow/theme[light,dark,system]), components(atomic→composite→pattern→template), naming(`Component__Variant--State`), accessibility(WCAG 2.1 AA, motion-safe), responsiveness(mobile_first, 컴포넌트당 최소 2 breakpoint).
- **governance**: ui_docs_inherit_fds:true, **token_change_requires_ruler_apply:true**, validation_extension .ruler/fds-checker.yml.

### 4-2. UI Design 기획서 (/docs/design/ui.md)
- PRD 기반, 페이지의 **구조·정보·메시지 계층** 정의 = "무엇을 어떻게 배치할까?"(스타일은 visual.md로 defer).
- Codex CLI GPT5-추론. layer:3.2, identity:ui-design, parent:prd.md, next:design/ux.md. Context에 **fds.md 포함**.
- goal: ui_information_architecture. outputs: ia_tree, pages[{route, purpose, sections[{id, content, cta, entity_refs, layout, hierarchy{h1,h2,h3}, notes}]}], mapping(feature_entity_map_ref, page_entity_annotation).
- rules: fds_compliance, style_deferred_to_visual, section_structure_required, ia_requires_entity_annotation. 완료 후 ruler apply.

*(범위 끝단 16247~16478행: 후속 Userflow(layer 4, IPO 구조·엣지케이스 필수), UX Design(layer 4.1, ESDX flow), DB 문서(layer 5, GPT5-codex 모델) 시작부 포함 — 모두 동일 SOT/Context/inheritance YAML 헤더 패턴, 각 완료 후 ruler apply.)*

---

## ★ ruler apply 재실행 시점 & 저자 강조 총정리
- **ruler apply 재실행 시점**: ①CLAUDE.md 부트스트랩 추가 후 ②rules.md/@ruler/*.md 수정 직후 ③Codebase Structure(2-9) 완료 후 ④Requirement/RTSV(2-10) 완료 후 ⑤PRD/prd-critic(4) 완료 후 ⑥UI(4-2) 완료 후. **규칙: 규칙·헌법·설계 문서 변경 후엔 ruler apply, 단 코드/env 변경만으론 불필요.**
- 반복 자체검증 프롬프트: "20년차 이상 최고급 시니어 개발자 관점, 깐깐한 기준, step by step" + "확대해석/멋대로 추가한 신규 기능 없는지 검토"(스코프 크리프 차단) + '간결함' precision pruning(할루시네이션 방지).
- 최상위 경고 재확인: **"CLAUDE.md를 브릿지/부트스트랩으로 개조하지 않으면 지금까지 만든 모든 md 문서 작업이 무의미하다."**
