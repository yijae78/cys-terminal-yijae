# NLC 다이제스트 (2/4) — 1단계 Rule 세팅 + 2단계 환경설정 초반 (5462~11399행 전 범위 정독 완료)

## 개관: 이 구간의 정체
문서 제목 "[ Spec/Doc driven 자연어 코딩 Professional 10단계 세부 기술들 ]"의 첫 두 단계. 저자는 "높은 수준의 정교함"으로 규정하며 핵심 사상을 압축: **"AI는 판단 주체가 아니라 '문서 집행기'다"** — 판단은 문서(SOT)가 하고, AI는 읽고·비교·집행만, 애매하면 멈추고 물어보게 설계. "AI는 어떤 존재인가"조차 한 파일에 요약 않고 의도적 분산:
- `/docs/_root-sot.md`→WHY(철학·판단 근원) / `/rules.md`→WHAT MUST/MUST NOT / `/docs/persona.md`→사고 성향 / `/docs/rules/uepp.md`→오류·환각 차단 / `/docs/rules/scdp.md`→규칙 상속 / `/docs/rules/rcmp.md`→구조 지도

Rule 세팅 3층: (1)Root SOT=진실 근원·판단 기준·정체성 앵커 (2)rules+UEPP=보편 규칙·오류방지 메타헌법·예외불허 (3)ruler=상황별 집행 명령·작업단위 enforcement. 이 셋만 있으면 규칙정의·적용조건·집행방법·오류방지가 논리적으로 빠짐없이 완성.

---
## 1단계: Rule 세팅

### 세 문서 계층 (경쟁 아님, 계층)
```
[WHO]  AGENT.md      ← 누가 일하는가(역할·책임·성격)
[LAW]  rules.md      ← 무엇이든 지켜야 하는 법(항상 적용)
[HOW-NOW] @ruler/*.md ← 이번엔 어떻게 행동(선택 적용)
```
핵심 비교표("가장 중요한 표"): rules.md=헌법·항상·거의 불변·위반 시 즉시 실패·"모든 AI 실행"·무엇이 금지/필수 // @ruler/*.md=작전/모드·선택적·자주 변경·작업 실패·"이번 작업"·지금 어떻게 // AGENT.md=에이전트 정의서·간접적·거의 불변·역할 붕괴·"AI 자신"·나는 누구인가.
저자 강조: **"AGENT가 인격, rules가 법, ruler가 전술"**. 섞음 금지: rules에 AGENT→헌법이 인사규정, @ruler에 헌법→작업마다 법 바뀜, AGENT.md에 규칙 다넣기→역할변경=법변경(프롬프트 드리프트).
**생성 순서(매우 중요)**: ①AGENT.md(WHO)→②rules.md(WHAT MUST NEVER BREAK)→③.ruler/*.md(시행령·런북)→④_root-sot.md(WHY 철학)→⑤docs/rules/*.md(메타헌법). ※철학=Root SOT는 의도적으로 늦게.

### 1-1. AGENTS.md (전역 — '존재 조건')
역할: "나는 누구/무엇에 책임"까지만 = AI의 직무기술서(JD). 없으면 만능도우미·과잉친절·과잉추론. **md 작업은 Codex CLI로**(`brew install --cask codex`→`codex`), gemini `npm install -g @google/gemini-cli`.
`.ruler/AGENTS.md` 프롬프트: `/docs` 전체 참고해 `[…]` 채우기. 템플릿=**# AGENTS Constitution** 6섹션:
1. **Role Identity** — senior AI coding agent(software engineer+architect, 30년+ 대규모 코드베이스). 파일/스니펫 아닌 **system·architecture·dependency graph 수준** 추론. "any non-trivial codebase is already a system".
2. **Core Responsibility** — 아키텍처 무결성에 직접 책임. 모든 변경을 isolated edit 아닌 **system-level intervention**. source↔docs↔specs 정합. hidden coupling 발생 시 task는 incomplete.
3. **Decision Boundary** — MAY(내부 구현·행동보존 리팩토링·명시 가정하 기본값) / MUST NOT without approval(하위호환 파괴·SOT 변경·APPROVED_TECH_STACK 밖 새 패러다임·public API 제거). 의심 시 conservative interpretation+표면화.
4. **Quality Bar** — 아키텍처 일관성>국소 최적화, shotgun surgery/hidden coupling 회피. "그냥 동작하나 구조 위반=below acceptable bar".
5. **Reasoning Attitude** — 모호함으로 행동 회피 금지, 합리적 가정 명시. "responsible senior engineer이지 speculative code generator 아님".
6. **Interaction Contract** — 실행 막거나 SOT 위반 위험일 때만 질문.
- Closing: "You are not a passive assistant. You are a system-aware coding agent."
- 필수 채움: [PROJECT_NAME][DOC_ROOT_PATH][ROOT_SOT_PATH][PRIMARY_DOMAIN][APPROVED_TECH_STACK]. 선택: [PUBLIC_API_SCOPE][SPEC_DOCS_LIST][EXTERNAL_INTERFACE_DOCS].

두 번째 융합 블록 = **"Senior Developer Guidelines"**(Next.js+Hono+Supabase 실전 예시): Must(모든 컴포넌트 use client·page.tsx params promise·placeholder picsum·HTTP는 @/lib/remote/api-client·Hono 라우트 `/api` prefix·AppLogger는 info/error/warn/debug만·경로필드 z.string()), Library 12종(date-fns·ts-pattern·react-query·zustand·react-use·es-toolkit·lucide·zod·shadcn·tailwind·supabase·react-hook-form), Directory Structure(src/app·api/[[...hono]]·backend/hono·features/[featureName]/backend{route·service·error·schema}·supabase/migrations), Backend(runtime=nodejs·createHonoApp 싱글턴이되 dev는 매번 재생성 HMR·errorBoundary→withAppContext→withSupabase→registerRoutes·success/failure/respond), Solution Process 6단계, Key Mindsets 7·Code Guidelines 9(Early Returns·Constants>Functions·DRY·Pure Functions·Composition over inheritance), Korean Text(utf-8 한글 깨짐 확인·항상 한국어).

### 1-2. rules.md (전역 — 헌법)
역할: 불변 규범(헌법). 인간도 동의·AI 바뀌어도 유지·위반 시 "틀렸다" 판정. **인간이 반드시 책임지는 단계**(규칙=AI 통제 장치, 애매하면 AI가 '그럴듯한 임기응변'=가장 위험). "뒤에 올 문서 몰라도 완성돼야 정상"(방향·한계·판정기준만). 기능정의·구현방법 ❌, 판정기준·금지/강제·충돌 우선순위 ✅. 통합 장점=단일 진입점("여러 rules는 인간엔 구조적이나 AI엔 분산된 기억"). 실패패턴: 팁모음·좋은습관·권장/불변 혼합·암묵 예외→"헌법이 아니라 위키".
템플릿 **# rules.md** 9섹션: 0.Preamble(위반=invalid by definition) / 1.Constitutional(SOT 최고권위·문서갱신 없는 코드변경 금지·검증전략 없는 변경 무효·암묵동작 금지·**no exceptions**) / 2.System-wide Invariants(UEPP)(할루시네이션 API·SOT 없는 추론 요구·중복 SOT·silent breaking·"assume it works"→감지 시 **즉시 중단**) / 3.Context Inheritance(SCDP)(충돌 해소순서: ROOT_SOT→docs/rules/*.md→docs/*.md→ruler/*.md→Source code, 하위가 상위 override 금지) / 4.Change Propagation(RCMP)(Specs↔Code·State↔UI·External↔Tests·Config↔Runtime) / 5.State&SOT(하나의 SOT·파생값 저장 금지·shadow state 금지) / 6.Verification(테스트가 정답 기준·테스트 없는 기능 미완) / 7.Exception Clause(APPROVING_ROLE 승인+근거+시한) / 8.Amendment(명시 제안·리뷰·기록).

### 1-3. .ruler/*.md (지역 — 시행령/런북)
역할: AI 실행 절차(런북). AGENT=누구인지, .ruler=어떻게 일하는지.
**rules vs @ruler 결정트리(3문항)**: ①항상 지켜야 ②작업 종류 바뀌어도 유효 ③위반 시 즉시 중단 → YES 2개↑=rules.md, NO 2개↑=@ruler.
- rules.md에 들어갈 6가지: 개발철학/운영모드·품질게이트·의존성/상태변경 헌법·보안/프라이버시·리포구조/SOT·AI사용규정(AI=제안자, 책임=인간). 원칙: "무엇이 옳은가(판정)만, 어떻게(절차)는 뺀다".
- @ruler에 절대 금지: 윤리·안전·품질하한선·테스트의무·권한제한("작전이 헌법 무력화 금지").
- 추천 폴더: rules.md(짧고 강함)+@ruler/(00_global·10_coding·20_testing·30_dependency·40_security).
- 금지 2개: rules.md에 절차 과다(SOP되면 업데이트 지옥) / .ruler에 판결기준(헌법을 런북에 숨김).

**필수 ruler 파일 10종**(공통 골격: Applicability→Mandatory Context→Output Contract→규칙→Verification→Checklist→**Stop Conditions**):
① **coding.md** — 코드변경 SOP. Output 8종(Intent Summary→Change Type[bugfix|feature|refactor|performance|security|chore]→Assumptions→Impact Analysis→Change Plan→Code Change Summary→Verification Plan→Propagation Checklist). Impact=Code/Structural/Data&State/Supporting/Ripple("If X changes,Y may break because Z")/Coupling Risk. Breaking change는 정책 없이 금지.
② **refactor.md** — **행동 동일성(Behavior Equivalence) 보장** 하 구조/결합도만. 외부행동 불변·입출력 동등·public contract 안정·새 기능 없음·버그 안고침. 행동변경 의도면 coding.md로. Type[extract|inline|rename|split|merge|reorder|simplify|decouple]. 4장 Behavior Equivalence=Non-Negotiable(확신 못하면 중단). rename은 의미 명료화만.
③ **hotfix.md** — 비상 프로덕션. "최소 변경으로 멈추는 것"(설계개선·구조·미학 ❌)="개발 아닌 사고대응(Operation)". Severity[SEV0~3]. mitigation>완벽, flag/kill-switch>깊은변경, config>code. **rollback plan 없는 hotfix=실패**. 가설-증거 기반만(로그·에러·재현·diff). 없으면 "이왕 고치는 김에 리팩토링"→변경범위 폭발·2차장애.
④ **migration.md** — 데이터/스키마/계약 비가역 변경을 '시간을 나눠' 이동="이동(operation)이지 개선(dev) 아님". Risk[LOW 가산|MEDIUM dual-read/write|HIGH 파괴·데이터손실]. Compatibility Strategy 필수(dual-write/read·shadow fields·versioned). Phased: Phase0 Preparation(백업·비파괴 확장·flag)→Phase1 Compatibility Window(dual-read/write·모니터링)→Phase2 Cutover→Phase3 Cleanup. 백업 없이 삭제 금지·파괴 먼저 금지·즉시 cutover 가정 금지. rollback/roll-forward 없으면 invalid.
⑤ **test-only.md** — **프로덕션 코드 절대 미변경, 검증만**. Given-When-Then·관측행동 테스트·snapshot 남용 금지. Forbidden(Hard): 프로덕션 수정·assertion 약화로 통과·실패 은폐.
⑥ **doc-sync.md** — 코드변경 시 문서(SOT·Spec·RCMP) 동반 갱신 강제. "없으면 앞의 것 절반 유명무실". 0장 Core(Non-Negotiable): 행동/구조/계약/데이터/상태 바꾸는 변경은 문서 반영, 갱신 불가면 코드변경도 완료 불가. Change Classification[behavioral|structural|contractual|stateful|config]. Affected Documents는 명시적 파일 나열(나열 없는 "documentation updated"=invalid).
⑦ **state.md** — 상태 다루는 방법(HOW 런북). **⚠ /docs/state-management.md(WHAT 설계 SOT)와 대체 불가**: state.md=집행 매뉴얼(시작 즉시 존재, 쓰레기 상태코드 방지), state-management.md=헌법 조문(Userflow/Spec 이후, 너무 빨리 만들면 100% 망함). Core(Non-Negotiable): State=Memory not Variables(계산값 저장 금지)·Single SOT·No Shadow State·**Unidirectional Flux**(Event→Action/Reducer→State→View). Boundary(Local/Page/App-global/Server). Async&Race(dedupe·cancellation·optimistic·stale-while-revalidate).
⑧ **security.md** — 로그인/DB/외부연동/로그/분석 있으면 필수. "non-negotiable correctness". Threat Model(top5: credential stuffing·broken access control·injection·XSS/CSRF·secrets 노출). 특권연산 **서버사이드 only**, client 주장(user id·role·pricing·entitlement) 신뢰 금지. AuthN(ARGON2/BCRYPT·MFA·rate limit·httpOnly/secure/sameSite·OAuth PKCE). AuthZ(RBAC/ABAC·**모든 특권 엔드포인트 서버 검사·UI 숨김은 보안 아님·deny by default·ownership 검사**). Secrets(git 커밋 금지·client 임베드 금지·발견 시 즉시 제거). Verification에 negative tests(무권한·권한상승) 강제.
⑨ **integration.md** — 외부 API/SDK/Webhook(repo 경계 밖). security.md 종속. Boundary Contract(Non-Negotiable): 외부는 unreliable·slow·version-unstable·partially documented로 취급, 핵심 도메인을 외부 API에 직접 결합 금지, **boundary layer(adapter/client/service abstraction) 래핑**. SOT=/docs/external/[service].md 유일. Error Modes(network·timeout·auth·quota·malformed·partial)+retry/backoff/circuit breaker/fallback. SDK 버전 pin.
⑩ **release.md** — 배포/CI-CD/버전/롤백. security·integration 종속. "배포는 성공해도 롤백은 항상 가능"=가장 보수적. Classification(type·env·risk[LOW~CRITICAL]·downtime). Versioning(SEMVER·monotonic·production immutable). Deployment(BLUE_GREEN|CANARY|ROLLING|FULL_REPLACE|SERVERLESS). Env Safety(.env.local prod 승격 금지). Feature Flags(auth·billing·핵심 flow 필수, prod 기본 OFF). "배포하는 용기가 아니라 배포를 되돌릴 책임을 강제".

### .ruler vs @ruler 구분 (절대 규칙·치명적)
표기 차이 아니라 권한·의미·실행 방식이 완전히 다름. `.ruler/*.md`=시스템/툴/엔진(내부 기록/설정·applied.lock·index.json·history.log — **규칙 내용 넣으면 안 됨**·자동 로드) // `@ruler/*.md`=사람·프롬프트(의사결정 선언·명시 선택·헌법 우회 위험 없음). **실제 규칙 파일은 `ruler/`에, `@ruler`는 "적용하라" 호출 표기**. 비유: **".ruler는 AI의 기억, @ruler는 인간의 명령" / ".ruler는 배선, @ruler는 스위치"**. 구조: AGENT.md=정체성(WHO)·rules.md=헌법(LAW)·@ruler=작전규칙(HOW)·.ruler=기록실/엔진룸(META).

### ruler apply (도구 사용법)
**ruler=규칙 변환+배포 오케스트레이터**("만드는 도구 아니라 배포·변환 도구"). 실행 전 AGENT.md·rules.md·@ruler/*.md 먼저 선언 필수. 기능: 중앙집중(.ruler/), 자동 배포, ruler.toml(default_agents=["cursor","codex","claude"]·[agents.*] output_path·[mcp_servers.*] stdio/remote), .gitignore 자동 관리, ruler init/apply. **변환 흐름**: rules.md(헌법)→.ruler/*.md(실행규칙 원형)→ruler apply→AI별 파일(Claude→CLAUDE.md·Copilot→.github/copilot-instructions.md·Cursor→.cursor/rules.md·Aider→.aider.conf). "AI가 태어날 때부터 규칙을 들고 태어나게".
**⚠ 핵심 오해 제거**: ruler apply=등록(register)이지 즉시·항상 적용 아님. **rules.md만 자동·항상 적용(예외 없음)**, **@ruler/*.md는 "선택 가능 세트"로 인덱싱만**(특정 작업/모드/명시 호출 시만). "이걸 이해 못하면 이후 설계 전부 흔들림". 설치: github.com/intellectronica/ruler, 이미 설치 시 `ruler apply` 또는 `npx @intellectronica/ruler apply`.

---
## 2단계: 환경 설정 — 전역 '헌법'

### @docs vs @ruler 위치 논리 (권한 계층)
**UEPP·SCDP·RCMP는 @ruler 아니라 @docs에** — 취향 아닌 권한 계층. rules.md=WHAT must never break(법률 텍스트), UEPP/SCDP/RCMP=법을 성립·읽히게·판정하게 하는 **메타 헌법 계층**(법의 존재조건·상속 메커니즘·구조 지도). 계층:
```
[-1] UEPP ─ 절대 해서는 안 되는 구조적 오류 방지 헌법
[-1] SCDP ─ 헌법이 모든 문서에 자동 상속되게 하는 메타 규칙
[-1] RCMP ─ 문서/규칙/SOT 간 위계·참조·금지 관계 정의 구조 헌법
──────────
[ 0] rules.md ─ 프로젝트 헌법(불변 규범)
[ 1] @ruler/*.md ─ 시행령/집행(HOW)
```
"헌법 조항은 위반될 수 있지만 UEPP/SCDP/RCMP는 위반의 판정 기준 그 자체". 섞으면(@ruler에 두면) 헌법이 실행절차로 격하·선택적용으로 오해·무시 가능·판정 근거 소멸→"헌법이 헌법이 아니게 됨". **핵심: "헌법은 AI에게 지시하는 문서가 아니라 AI를 판정하는 문서다. 반드시 @docs에."** 파일: /docs/rules/에 uepp·scdp·rcmp, /ruler/에 coding 등.

### 2-1. Root SOT (/docs/_root-sot.md)
**가변은 오직 8번 섹션만 [ ]**. frontmatter: layer L-1/Sovereign·authority Supreme·mutability Highly Restricted. "모든 문서·규칙·코드·AI 판단의 최상위 단일 기준(SOT)". 실행규칙·구현·절차 미포함. 오직 **"왜 이 시스템이 존재하며 무엇을 옳고 그름 기준으로?"**.
10섹션: 1.Ontological Status(유일·항상 전제·선택적용 안됨·암묵 로딩된 전제) / 2.Scope(판단 정당성·충돌 최종판정·계층 존재이유. 구현/기술스택/절차 미포함) / 3.Worldview(AI는 판단하되 판단 기준을 스스로 정하지 않음) / 4.Supreme Principles(Meaning over Form·**Hierarchy Integrity**: Root SOT→Meta Rules→rules.md→@ruler→Domain·Minimal Authority) / 5.Semantic Consistency / 6.Conflict Resolution(상위 계층→명시 규칙→의미 일관성→최소 수정→안정성) / 7.Inheritance(자동·선언 없이·거부 불가) / 8.Project Anchors([WHY_THIS_PROJECT_EXISTS][NON_NEGOTIABLE_JUDGMENT_CRITERIA][FORBIDDEN_DECISION_PATTERNS]) / 9.Mutability(기본 불변, 3조건 충족 시만) / 10.Final Assertion("'무엇을 할 것인가' 아니라 '왜 옳거나 틀린가'만 판정", 위반=Systemic Fault).
**왜 늦게 만드는가(강조)**: HOW 없이 WHY만. @ruler보다 먼저 만들면 "철학이 전술규칙으로 오염". 비유 **"@ruler=전투기록, rules.md=군율, _root-sot.md=전쟁 끝난 뒤 쓰는 전쟁관. 전쟁관을 전투 전에 쓰는 군대는 반드시 망한다."** @ruler 먼저=실행이 철학을 폭로(질문의 잔여물residue이 Root SOT 내용)·"설명서 아닌 판결문"·권한 역전 방지. **"Root SOT는 지시자가 아니라 판정자."** 루트(/) 아닌 /docs에 두는 이유=루트는 "실행 관문"이라 규칙처럼 오독→"왜"가 "어떻게"를 침범=권한 붕괴. 파일명 `_` 붙여 "고립된 최상위 단일체".

### 2-2. UEPP (/docs/rules/uepp.md) — Universal Error-Preventive Prompt
frontmatter: L-2/Meta-Constitution·Meta-Supreme. "오류가 발생하기 '이전' 단계에서 차단하는 메타 헌법"=사후판정 아닌 **생성 이전 예방 헌법(Preventive Constitution)**. 오직 "이 산출물을 지금 만들어도 되는가? 구조적으로 허용되는가?".
10섹션: 1.Ontological(Root SOT 바로 아래·자동 전제·"암묵 로딩된 검문소") / 2.Scope(생성 이전 허용/차단·계층 위반 감지. "어떻게 만들 것인가 아니라 만들어도 되는 상태인가만 판정") / 3.Worldview(대부분 오류는 구현 실수 아닌 **판단 순서 오류**·LLM은 구체적 요청 우선→상위기준 희석·**사후교정 아닌 사전차단이 최선**) / 4.Hierarchy(생성 이전 7계층 검사, 위반=즉시 Blocked) / **5.Pre-Generation Gate**(4게이트: Hierarchy·Duplication·Assumption["보통/일반적으로/알아서" 금지·필요 가정은 [가정] 명시]·Propagation) / 6.Forbidden Patterns(상위가 하위 명령·정의 없는 구조 나열·기존 무시 재정의·문서-코드 불일치·중복 SOT·검증 없는 완료·Scope Creep·민감정보 → Systemic Fault) / 7.Self-Healing(위반 유형 명시→원인 특정→최소 수정→동기화→재검증. 재작성=최후 수단) / 8.Inheritance(요약/재진술 안됨·항상 전제) / 9.Anchors([FORBIDDEN_CREATION_PATTERNS][COMMON_STRUCTURAL_FAILURES]·강도[STRICT|NORMAL|LIGHT]) / 10.Final("규칙 지키라 요구 않고 규칙 어길 기회를 생성 단계에서 제거", 우회=Invalid by Construction).
**존재 이유**: Root SOT="재판관이지 검문소 아님", rules.md="법전이지 에러방지 아님"(LLM이 편리함·최근문맥·구체요구 우선해 무시="실수 아니라 LLM 정상 동작"). 비유 **"Root SOT=헌법정신, rules.md=법전, UEPP=공항 보안 검색대"**(없으면 위험물 항상 통과).

### 2-3. SCDP (/docs/rules/scdp.md) — System Context Directive Prompt
frontmatter: L-0.5·Context-Inheritance·inherits _root-sot·uepp. "상위 문맥이 어떻게·언제·어느 범위까지 자동 상속되는지" 정의. 규칙 아님 — 오직 **문맥 상속 방식**.
10섹션: 1.Directive Status(자동·Root SOT/UEPP 재서술 금지) / 2.Context Sources(_root-sot=WHY·uepp=예방·rules=WHAT NEVER BREAK) / **3.Inheritance Scope Matrix**(산출물별: Meta Docs=HARD/HARD/SOFT/NONE, Constitution=HARD/HARD/HARD/NONE, @ruler=HARD/HARD/HARD/SELF, Design/Spec=SOFT/HARD/HARD/NONE, Code/Tests=SOFT/HARD/HARD/CONTEXTUAL. 강도: HARD 절대위반불가·SOFT 존중하되 재서술금지·CONTEXTUAL 필요시 참조·NONE 상속금지) / 4.Strength Rules(Root SOT 재작성/요약/복제 금지·@ruler는 실행시점만·설계문서로 전파 금지) / 5.Temporal(생성·수정·병합·검토 시 적용, 누락=Context Break) / 6.Isolation("문맥은 항상 위→아래로만") / 7.Assumption(핵심질문 1개만 or [ASSUMPTIONS] 명시) / 8.Overrides([DOCUMENT_TYPES][EXCLUDED_DOCUMENTS][CRITICAL_CONTEXT_PATHS]) / 9.Validation / 10.Final("규칙 추가 않고 규칙이 항상 같은 방식으로 적용되도록 강제", 위반=Contextual Fault).
**존재 이유**: Root SOT는 "어떻게 스며드는지" 정의 안함, UEPP는 차단장치지 전파설계도 아님. 없으면 100% 발생: 과잉상속(철학 오염)·상속단절(문서마다 다른 세계관)·세션별 기준 붕괴(병렬 불가). 3가지만 함: 상속 범위·강도(HARD/SOFT/CONTEXTUAL 단계화, 없으면 다 HARD 해석 or 다 SOFT 무시=둘 다 붕괴)·시점. **"SCDP 없이는 '자동'이라는 단어가 성립 안함."**

### 2-4. RCMP (/docs/rules/rcmp.md) — Root Context Map Prompt
frontmatter: Meta-Constitution/Structural·Context Topology Definition·inherits _root-sot·uepp·scdp. 모든 문서·규칙·컨텍스트의 **구조적 위치·연결 관계** 정의 = **구조 지도(Map)**. 판단·규칙·실행 안함. 유일 목적="이 문서가 시스템 전체에서 어디에".
8섹션: 1.Nature(구조 지도, Context Topology Definition) / **2.Canonical Layers**(보편: L-2 Agent Definition WHO·L-1 Immutable Rules·L-0 Root SOT WHY·L-0.5 Meta Rules·L+1 Domain·L+2 Execution·L+3 Artifacts) / **3.Mandatory Positioning**(AGENT.md=L-2·rules.md=L-1·_root-sot.md=L-0·uepp/scdp/rcmp=L-0.5, "대체·병합·흡수 불가") / 4.Project-Dependent Zones([DOMAIN/DESIGN/EXECUTION_DOCUMENTS][ARTIFACT_TYPES]) / 5.Dependency Direction(상위→하위 허용·하위→상위 참조만·동일계층 명시선언 시. "위치 관계만 고정") / 6.Completeness(새 문서는 Layer·상위참조·전파여부 정의, 미정의=Unmapped) / 7.Scope Boundary(규칙해석·우선순위·절차·품질평가 안함) / 8.Final("판단하지 않지만 판단이 길을 잃지 않게").
**존재 이유**: 없으면 docs/를 "파일 묶음"으로 인식→"헌법이 PRD에 밀리고 Root SOT가 Spec에 무력화". 5책임: Document Ontology·Hierarchy(문서 동등취급 불법화)·Dependency Graph(Spec→Code·Userflow→DB·State→UI)·Context Flow(단방향)·Validation Anchors. **"SOT 체계 붕괴의 90%는 RCMP 부재에서 시작."** 비유 **"UEPP가 법이라면 RCMP는 지형도, SCDP는 물길"**(SCDP="전기는 흐른다"=상속규칙, RCMP="전선 배치도"=상속경로 지도).

---
## 문서 간 상속·참조 총괄
역할 분업: Root SOT=무엇이 옳은가(WHY) / UEPP=무엇을 하면 안되는가(생성 이전 차단) / **SCDP=그 기준이 어떻게 자동 흘러가는가(방식·강도·시점)** / **RCMP=어디로 흘러가는가(위치·경로·지도)** / rules.md=무엇이 깨지면 안되는가. ruler apply가 전체를 각 AI 파일로 배포하되 rules.md만 자동·항상, @ruler는 조건부. 메타헌법(UEPP/SCDP/RCMP)은 @docs에서 판정 기준으로 상주해 AI 툴이 바뀌어도 생존.

**후속 연결**: 바로 다음(11400행~, 내 범위 밖)은 저자 강조 — "md 문서를 만드는 것만으로는 아무것도 자동으로 안 일어난다. CLAUDE.md를 브릿지/부트스트랩으로 개조해야 한다(안 하면 모든 md 작업이 무의미)". 다음 다이제스트 담당 범위.
