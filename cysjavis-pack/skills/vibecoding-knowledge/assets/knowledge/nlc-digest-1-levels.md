# 최윤식 박사 NLC 교본 v4.0 — `[Vibe/자연어 coding Level]` 구간(146~5461행) 충실 다이제스트

지정 범위를 6개 청크로 offset을 나눠 전 범위(건너뛰기 없이) 정독 완료. 이 구간은 바이브코딩(자연어 코딩, NLC)을 **6개 Level**로 계층화한 커리큘럼이며, Level이 오를수록 "잘 돌아가느냐"가 아니라 **"통제 가능하냐(재현성·책임성)"**를 기준으로 기술을 쌓는다.

## Level 체계 전체 구조 (6단계)

| Level | 명칭 | 핵심 도구·기법 | 성격 |
|---|---|---|---|
| **1. 워밍업** | 풀스택 노코딩 맛보기 | vercel v0·Replit·lovable = "(자연어 기반) 풀스택 생성·운영 레이어(Full-Stack Generation Layer)" | 인간은 가장 간단한 설계만 지시, 나머지 AI 전적 위임 |
| **2. 입문용** | 프로토타입 노코딩, 초급 자유도 | Google AI Studio Build, Git/GitHub(필수), Spec/Doc 일부 | 점진적 개선 개발 |
| **3. 초급용** | 초급 자유도 / **Regression Testing** | 목업→md 역작성→외부 연동(Supabase), System Prompt | IDE 진입 준비(node·python·CLI) |
| **4. 중급용** | 중급 자유도 / **Prompt Driven Restart / Context Engineering** | AI Studio Build→IDE 이전(Migration)·Replatforming·Refactoring, Claude Code CLI 심화 | AaaS 완성 |
| **5. 고급용** | 최고 자유도 / **Professional 10단계 전체** | Spec/Doc driven 완벽, CI/CD, Token Optimization, Nano-Service | 바닥부터 AaaS 완성 |
| **6. AI Pipe coding** | 최고 자유도 / 완전 자동화 | AI agents 오케스트레이션(Agentic automation system), Pipe coding 4단계 | AI가 주체, 사람은 감독·검토 |

박사 강조 분기 원칙(필독): "**'수준'을 나누는 기준은 '잘 돌아가느냐'가 아니다. '통제 가능하냐'이다.**" / "**4단계부터는 성능이 아니라 '재현성·책임성'에서 갈린다. 통제 아래 두려면 반드시 4단계 이상을 습득해야 한다.**"

---

## Level 1 — 워밍업
핵심 개념(원문 명명, "반드시 기억할 것"): **스택**(기술 층 묶음) / **풀스택**(스택 전반 설계·구현·연결) / **Full-Stack Generation Layer**(v0·Replit·lovable의 정확 명칭) / **비즈니스 로직=실행 로직(Execution Logic)**("시스템이 무엇을 해야 할지 판단·행동", 업무 규칙 아님) / **API**("소유가 아니라 호출, 복사가 아니라 위임") / **스케일링** / **배포**(인터넷 공개↔localhost) / **레이어=추상화된 조작면(control surface)** / **플랫폼**('판') / **툴**(Task-level 최적화).
**Prototype Generation Layer**: 자연어 UI·간단 로직·LLM 호출 O, DB/Infra/CI/CD·운영·책임이전 X. 이상적 위치 = **Spec/Doc driven 전**(PRD 초안·userflow 검증·edge case 발견).

## Level 2 — 입문용
**[난이도1] 문서 없이**: AI Studio Build 3방법(From Scratch/Sample Website/Sample code).
**필수기술 Git/GitHub**("깃허브 모르면 바이브코딩 못한다"): GitHub="코드+문서+변경이력+책임 기록 표준 플랫폼"="AI-인간 협업 기억장치+책임추적장치". GitHub≠Git(GitHub 선택·Git 필수). 워크플로우 git init/status/add/commit(=**인간의 책임 도장**)/log/checkout. **Branch=코드 복사 아닌 커밋 포인터="서로 다른 시간선(세계선)"** → AI 작업=무조건 branch. Merge가 기본값(Rebase는 흔적 지움). 네이밍 feature/·fix/·refactor/·ai/. **5원칙**: AI작업=branch/branch1개=목적1개/merge=인간승인/실패는 삭제/main=안전지점. 결론: "**Branch는 판단을 분리하는 기술. 프로 개발자는 어떤 판단을 main에 올릴지 결정하는 사람.**" Git 내부=압축+해시 객체저장소(blob/tree/commit). Repository=git init 순간 로컬 생성. **push=저장 아닌 복사/공유**(commit=기억, push=공유). git pull은 여러 컴퓨터/PR merge/UI수정/봇/협업 시 필수. **PR**=git 아닌 GitHub 기능="AI 작업을 인간 언어로 검증하는 관문". README="AI와 인간이 처음 만나는 계약서". 최소 명령어세트 8개(init/clone/status/add/commit/branch/checkout -b/push). PR 프롬프트 목표="리뷰어가 코드 안 열고 merge 판단"(변경요약 왜 중심/영향범위/설계문서 매핑).
**[난이도2] 문서 일부 적용 — # NLC 대원칙: '설계 문서'가 코드다. 설계 문서로 AI를 제어한다.**
- **Spec Driven**(Spec을 SOT로): Spec="AI가 코드로 해석·실행 가능한 로직 정의서". **SOT="AI-개발자-코드가 공유하는 유일한 진실"="전체 생태계를 좌우하는 헌법". SSOT 필요조건**: 가장 먼저 정의/**유일성**/**불변성(Immutable)**/**전역성(자동 상속)**/쉬운 접근/간결/항상 기준 참조.
- **Doc Driven**: SOT Spec을 Doc으로 구조화→AI-개발자 공유 Context 변환. 3축: ①SOT로 정의된 Spec("진실의 단일 원천") ②문서 구조화(Doc Structuring Layer, /docs 트리 requirement·userflow·spec·state-management.md=실행 가능한 설계 그래프, **Doc=살아있는 인터페이스**) ③AI–개발자 공동 Context("문서로 움직이는 코드 생태계", 개발자=**오케스트레이터**, AI=**문서-기반 실행 주체**). 정의="코드 짜는 대신 문서 설계하면 코드가 생기는 방식", 자가일관형(Self-consistent).
- 이 단계는 인간 책임(정답 아닌 **의사결정**): MVP 경계·성공지표·운영현실 결정. 통과기준="MVP 밖 요청에 '아니오'를 칼같이 말할 근거가 문서에".
- md 문서(persona/rules/project/requirement/prd/tech-stack)는 GPTs로 제작. 클로드 스킬 제작 프롬프트(PRD·user journey·TRD·code/UI guideline·tasks).
- **AI Studio Build 내부 DB**: 데이터는 Session Storage(임시, 브라우저 끄면 소멸). 용어: sessionStorage/Cache/localStorage(5~10MB)/**IndexedDB**("브라우저 안 하드디스크급 창고", 개발자가 직접 설계). IndexedDB 영속저장 프롬프트 전문(deep_news_db·news_items·스키마·검증시나리오 3·"캐시로 해결 금지"), 설교원고 응용판(sermon_writer_db·autosave 디바운스).
- **[참고] AI 적합 언어=TypeScript**: "**AI가 TS를 좋아하는 게 아니라, TS가 AI를 덜 틀리게 만드는 언어**". JS=추측 많은 세계, TS=규칙 안에서만 생각. 어원(script=미리 쓴 지시, type=형태). **TS는 힌트, Schema는 법률**(환각 방지 계층 아이디어→TS→Schema→Runtime). 확장자 정리: .ts/.tsx/**`.md`=AI의 헌법·통제장치**/.yaml(사람 친화 선언형)/.toml(설정 계약서=법률)/.json(시스템 간 법률)/.py.

## Level 3 — 초급용 / Regression Testing
**System Prompt(verbatim)**: "**30년차 시니어 소프트웨어 엔지니어·아키텍트**", 핵심="**의존성/결합도/변경 파급 효과(Dependency/Coupling/Ripple Effect)**까지 고려한 일관 수정"(의도파악→영향범위분석→Change Plan, 역호환 유지). **저작권 표시(중요)**: 헤더 우측에 저작자 저작권 표시(개인 연락처는 배포판에서 생략).
**md 업데이트 규칙(verbatim)**: "code structure/codebase는 절대 추가 수정 말라, 지금은 md 일치 작업" + "실제 수행 내용 제외 나머지는 **주석 처리**"(AI가 나중에 구현 내용 아님을 명기) + "docs와 code '100%' 일치".
**외부 DB**: ERD 추출 프롬프트("하드코딩 금지·확인 불가는 UNKNOWN·이상적 설계 창작 금지·최소 모델 V0"), Supabase 연결.
**Regression Testing**("선택 아닌 생명줄"): 정의=수정 후 기존 기능 유지 확인(새 기능 아님). 바이브코딩 재정의="AI 수정으로 의도 안 한 변화 없는지 자동 검증하는 안전장치"=환각 방지·과신 억제·기억력 한계 대체. 막는 것: "이거만 고쳤다" 거짓말/**상태(State) 오염(제일 무서움)**/암묵적 계약(API Contract) 붕괴("컴파일·런타임 OK, 비즈니스 로직만 망함"). 형태: 자동테스트(Unit/Integration/**Snapshot**)/**골든 데이터(Golden Master)**/시나리오.
**진입 준비**: **Node.js="실행 인프라"**(없으면 결과물은 텍스트뿐, AI 오케스트레이션 불가). **Python="두뇌 처리기"**("느낌상 맞음을 증명됨으로 바꾸는 언어", AI 에이전트는 95% Python). **Next.js="애플리케이션 헌법"**("AI는 자유보다 경계에서 더 잘 일한다", 일관성 최고). Node=실행기/React=UI언어/Next.js=헌법. 패키지매니저(npm·pnpm) vs 환경(venv 필수). 실전3규칙(lockfile 보존/전역 최소화/한 방식 유지).

## Level 4 — 중급용 / Prompt Driven Restart / Context Engineering
**[난이도1]** AI Studio Build→IDE 이전→Replatforming·Refactoring→외부연동(로그인·DB·결제)→AaaS.
- **Migration**="실행·개발 환경 이전(Environment Migration)"="운영 주체·실행 책임의 이전". **"빌드 해줘"=통합 진단 명령**("돌아가느냐?가 0번 질문", 상태 수리+환경 복원, package.json/lockfile/의존성/환경변수/버전충돌 일괄 검증). npm install vs npm ci(재현성·CI 표준). Cursor 마이그레이션 프롬프트(Lovable→로컬, cursor-migration.md).
- **Replatforming**="도는 코드를 Next.js 규칙에 맞게 재배열"(로직 유지).
- **Refactoring 3대 불변조건**: ①기능 동일 ②입출력 동일 ③사용자 관점 변화 없음("아무도 눈치 못 채야 성공").
- **4종 비교표**: Migration(환경·아키텍처 변경·롤백 가능)/Refactoring(내부 구조만)/Rewrite(폐기·재구현·"실패하면 회사 연옥")/Porting("컴파일만 바뀐다"). 오해 TOP3(Next.js 이전=마이그레이션이지 리팩토링 아님 등).
- **Prompt Driven Restart**: 코드 아닌 지시체계(prompt) 오염 시 컨텍스트 리셋. "**같은 코드베이스를 다른 사고 체계로 재접근**". 템플릿 `[RESET][PROBLEM][SCOPE][CONSTRAINT: Regression 100%][GOAL: 최소 수정으로 원인만]`.
- Codebase 업데이트: Knip/tidying/**오류 밀도 체크**/eslint/대용량 파일 분리.
**[클로드 코드 기술]**: `--dangerously-skip-permissions`. **CLAUDE.md="세션마다 자동 로드되는 최상위 컨텍스트"="가장 먼저 읽는 문서"**(로딩순서: Anthropic 내부 SP→CLAUDE.md→import 문서→유저입력). 6단계 검증 체크리스트(verbatim: UX/Test/App/Stress/Code/Implementation). hooks(PostToolUse→git add .). 슬래시(/config·/clear·/context 등), think<think hard<think harder<**ultrathink**. **RULES.md는 "필요 없을 뿐 아니라 있으면 위험"**(규칙 이중화=통제 붕괴). **중복 AGENTS.md도 위험**("AI는 판단 주체 아닌 **문서 집행기**", 공존 시 모델 평균 인간 회귀=통제 붕괴). **Ralph Loop**=단일 패스 문제 해결 위한 **강제적 지속성(forced persistence)**. 서브에이전트(컨텍스트 분리·병렬), 초보는 **plan mode** 권장.
**[난이도2] 개발 프로세스**(SuperNext, "앞 단계일수록 꼼꼼히"): ①Tech Stack(🚨인기 기술 유리·믿을 기업·신구 호환 shadcn) ②Codebase Structure(**Layered Architecture+SOLID**, 4분리) ③Data Model(초기 확정) ④Usecase("행위자가 유용한 일 달성하는 시나리오 집합"=Spec Driven 핵심, System/Actor/Scenario/Relation). **Context Engineering**("quality comes from context, not just capability", AI briefing packet).

## Level 5 — 고급용 / Professional 10단계
바닥부터 AaaS, Source+Spec/Doc versioning, **Token Optimization**("Maximum signal, minimum noise"). **Professional 10단계 개요표**(문서경로 매핑): 1-1 /AGENTS.md(에이전트 헌법)·1-2 /rules.md(전역 불변규칙)·1-3 /ruler/*.md(시행령)·2-1 _root-sot.md·2-2 uepp.md(UEPP)·2-3 scdp.md(SCDP)·2-4 rcmp.md(RCMP)·2-5 persona·2-6 project·2-7 env.template·2-8 tech-stack·2-9 codebase-structure·2-10 requirement(SRS)·3 external·4 prd·4-1 fds(디자인 헌법)·4-2 ui·5 userflow·5-1 ux·6 database·7 spec(유스케이스)·8 state-management·8-1 page-state-mapping·8-2 visual·9 test(TDD)·9-1 test-plan·10-1 plan·10-2 initial-implement.
**CI/CD 재정의**="AI의 즉흥적 수정을 현실 시스템에 반영할 자격을 심사하는 자동 검증 관문"("코드가 스스로 무죄를 입증"). CI(살아있는가: build/lint/type/regression/contract)/CD(단계적 Preview→Flag→Canary→Full, "즉시 전면 배포 없다"). 흐름=**AI→CI→(통과 시에만)인간**. 역할: 과신 방지("말보다 증거")/변경범위 통제/**품질 기준의 헌법화**.

## Level 6 — AI Pipe coding
완전 자동화(Agentic automation system). 2026 신조어 "cracked engineer"(구 10x engineer 대체). **Pipe coding**=출력(stdout)→입력(stdin) 파이프라인 chain. **바이브 vs 파이프 대비**: 바이브=창의·비정형, 주체=사람·AI 조수 / 파이프=규칙적(Well-Defined)·반복적(Repeatable)·**검증가능(Self-Verifiable)**, 설계 후 implement 완전 위임, **주체=AI·사람은 감독·검토만**. **Pipeline coding 4단계**: ①Specify ②Explore ③Plan ④Implement. 설계 시 **context token 길이 성능 변화(컨텍스트 로트, 할루시네이션)** 반영 필수.

---

## 인용 외부자료·도구(전수)
서비스: vercel v0·Replit·lovable·Google AI Studio Build·Supabase·Firebase·Vercel·Netlify·Next.js/React/Vite·Tailwind/Shadcn·Playwright/Vitest·Claude Code·Codex CLI·Cursor·Gemini CLI·Antigravity·n8n·Knip·IndexedDB·GitHub Actions·SuperNext. 클로드 생태계: SuperClaude·클로드템플릿(aitmpl.com)·ccusage·**Ralph Loop**(anthropics/claude-code ralph-wiggum)·Auto Claude·oh my zsh·Warp·IndyDevDan. 공식문서: OpenAI Platform·code.claude.com(sub-agents·skills)·Anthropic Engineering·IBM 오케스트레이션·metr.org(Measuring AI Ability to Complete Long Tasks). Notion: 6 Core Areas of Context Files·Top 5 Tips·CLAUDE.md Starter Template·Common Mistakes. 30+ YouTube(How I Claude Code=Pipeline 4단계 근거영상, 앤스로픽 5가지 패턴, 20 Agentic Design Patterns 등).

## 저자 강조 대목 총정리
①"설계 문서가 코드다"(NLC 대원칙) ②"SOT=전체 생태계 헌법"·SSOT 유일·불변·전역 ③레벨은 성능 아닌 "통제 가능하냐" ④Commit=인간의 책임 도장 ⑤"Branch는 판단을 분리하는 기술" ⑥Regression=생명줄 ⑦"빌드 해줘"=통합 진단("돌아가느냐가 0번 질문") ⑧TS는 힌트 Schema는 법률·.md=AI 헌법 ⑨RULES/중복 AGENTS.md=위험("AI는 문서 집행기") ⑩Tech Stack 🚨(인기·믿을 기업·신구호환) ⑪파이프코딩=주체 AI·사람은 감독 ⑫CI/CD=무죄 입증 관문(AI→CI→인간).

※ 참고: 5462행부터 시작되는 `[Spec/Doc driven Professional 10단계 세부 기술들]`(Rule 세팅 등)은 배정 범위(~5461) 밖으로, Level 5 개요표의 각 단계 상세 구현이 후속 구간에서 전개됨.
