# Spec-Driven Development (SDD) 생태계 2025–2026 정밀 조사 보고

(WebSearch/WebFetch로 GitHub·Kiro·OpenSpec 공식 문서 + 1차 벤치마크·비평 글 실제 출처 교차확인. 학습지식 단독 서술 없음.)

## 0. 개괄 — SDD 정의와 부상 배경
**핵심 명제**: "명세(spec)가 산출물이고 코드는 빌드 결과물이다 — .c 파일이 바이너리로 컴파일되듯." 2025년 LLM "vibe coding" 실패(컨텍스트 소실·일관성 붕괴·문서 부재)에 대한 반작용. 2026년까지 OpenSpec·BMAD·Tessl·Kiro가 각자 SDD 버전 출시. 초기 도입자 기준 비자명 태스크에서 AI first-pass 성공률 3–10배 주장(단 5번 비평 참조).

**SDD 성숙도 3단계** (cameronsjo/spec-compare):
1. Spec-First: 명세가 코딩에 선행하나 폐기됨 → Spec-Kit, Kiro, BMAD
2. Spec-Anchored: 명세 영속·진화 → OpenSpec, Spec Kitty
3. Spec-as-Source: 명세만 편집·코드 자동생성 → Tessl

---

## 1. GitHub Spec Kit (specify CLI)
**현황**: v0.12.17 (2026-07-16), 122k stars, 193 릴리스. 30+ AI 에이전트 지원.
**설치**(uv 필수): `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z` → `specify init my-project --integration copilot`

**슬래시 커맨드 워크플로우**(공식 verbatim):
- `/speckit.constitution` — 프로젝트 지배 원칙·가이드라인 생성/갱신
- `/speckit.specify` — 무엇을 만들지 정의(요구사항·유저스토리)
- `/speckit.clarify` — 미명세 영역 명확화(선택, plan 전 권장)
- `/speckit.plan` — 선택 기술스택으로 기술 구현 계획
- `/speckit.tasks` — 실행 가능 태스크 목록 생성
- `/speckit.analyze` — 아티팩트 간 일관성·커버리지 분석(선택)
- `/speckit.implement` — 계획대로 모든 태스크 실행
- 추가: `/speckit.taskstoissues`(태스크→GitHub 이슈), `/speckit.converge`(코드베이스를 명세 대비 평가)

**산출 md 파일**: spec.md(요구사항·유저스토리, what/why 중심 기술스택 배제) / plan.md(아키텍처·데이터모델·API 계약) / tasks.md(의존성 순서 정렬 체크리스트, 각 태스크는 AI가 추가 컨텍스트 없이 실행 가능하게 구체적)

**Constitution**: 명세가 코드가 되는 방식을 지배하는 불변 원칙 = "시스템 아키텍처 DNA". `/speckit.plan`이 기술스택을 constitution 대비 검증.
**커스터마이징 계층**: `.specify/templates/overrides/` → `presets/templates/` → `extensions/templates/` → `templates/`. Extensions·Presets·Bundles 개념.
**성공/실패**: 명확한 상위 요구사항 있는 greenfield 최적. Brownfield는 코드 역공학 필요, 사소한 수정엔 "sledgehammer to crack a nut", 반복 변경엔 `/speckit.clarify` 우회 필요.

---

## 2. AWS Kiro
**현황**: v0.12.x, GA 2025년 11월, Amazon Q 대체. AWS 백엔드 agentic IDE(무료+유료+CLI). 2026-06 AWS Summit NY "항공우주 스펙 표준을 AI 코딩에" 홍보.

**Spec 3개 핵심 파일**(공식: "모든 spec은 3개 파일 생성"):
- requirements.md(버그시 bugfix.md) — 유저스토리+수락기준을 **EARS 표기법**으로
- design.md — 기술 아키텍처, 시퀀스 다이어그램, 설계 근거
- tasks.md — 추적 가능 개별 구현 태스크

**3단계**: Requirements(또는 Bug Analysis) → Design → Tasks. 변형: Requirements-First / Design-First / Quick Plan(3개 자동생성). Bugfix Spec은 진단→수정설계→회귀방지.
**태스크 실행**: 의존성 그래프→**wave(웨이브)** 조직. 웨이브 내 독립 태스크 동시실행, 웨이브 간 순차실행. in-progress/completed 추적.
**EARS 실제 예시(verbatim)**: "WHEN a user submits a form with invalid data THE SYSTEM SHALL display validation errors next to the relevant fields"

**Steering Files**: 위치 `.kiro/steering/`(전역 `~/.kiro/steering/`). 자동로드 표준파일: product.md(제품정의)·tech.md(프레임워크·라이브러리·제약, 구현 제안 시 이 스택 우선)·structure.md(파일조직·네이밍·import·아키텍처 결정).
**Agent Hooks**: 자연어로 작성된 이벤트 구동 자동화("로컬용 GitHub Actions이되 AI 구동"). 위치 `.kiro/hooks/`(JSON). 트리거: agentSpawn·userPromptSubmit·preToolUse·postToolUse·stop. 파일저장·커밋 시 문서갱신·단위테스트 백그라운드 자동실행. IDE·CLI·웹 간 전이. `.kiro` 구조: agents/·hooks/·steering/·settings/.

---

## 3. EARS 표기법 (Easy Approach to Requirements Syntax)
**출처**: Alistair Mavin + Rolls-Royce 팀 2009년 개발(제트엔진 제어시스템 감항성 요구사항 추출용). 공식: alistairmavin.com/ears.
**5개 패턴**:
1. Ubiquitous(편재) — 항상 활성, 키워드 없음. 예: "The mobile phone shall have a mass of less than XX grams."
2. Event-Driven — **When**. `When <trigger>, the <system name> shall <system response>.`
3. State-Driven — **While**. `While <precondition(s)>, the <system name> shall <system response>.`
4. Unwanted Behavior — **If/Then**. `If <trigger>, then the <system name> shall <system response>.`
5. Optional Features — **Where**. 해당 기능 포함 제품에만 적용.
Spec Kit에도 EARS 통합 요청 이슈(#1356) 존재 → EARS가 SDD 요구사항 문법 사실상 표준으로 수렴 중.

---

## 4. 대안 SDD 프레임워크

**OpenSpec (Fission-AI)** — v1.3.1, MIT, 무료, 리포 상주(API key/MCP 불필요), 20+ 어시스턴트, 락인 없음.
설치: `npm install -g @fission-ai/openspec@latest`(Node 20.19.0+), `openspec init`.
4단계: `/opsx:new <name>`(변경 폴더·제안 생성) → `/opsx:ff`(fast-forward: **proposal.md, specs/, design.md, tasks.md 자동생성**) → `/opsx:apply`(태스크 실행) → `/opsx:archive`(아카이브 이동·명세 갱신).
시그니처 = **Delta-Tracking**: 전체 재생성 없이 **ADDED/MODIFIED/REMOVED** 마커로 증분변경만. 변경별 폴더 `openspec/changes/`, 완료시 `openspec/changes/archive/[date-feature-name]/`. Spec delta 리뷰로 수초 내 리뷰.
자기규정(verbatim): "Spec Kit: Thorough but heavyweight. Rigid phase gates, lots of Markdown, Python setup. OpenSpec: Lighter and lets you iterate freely. No Python required." → **Brownfield·반복 변경 최적**(예: 버튼 색 변경). 델타 마커가 기존동작 hallucination 방지.

**BMAD-METHOD** (Breakthrough Method for Agile AI-Driven Development) — v6.8.0, 오픈소스. 전체 애자일 팀 시뮬레이션(21개 전문 AI 에이전트).
파이프라인(verbatim): `Analyst → PM(PRD) → Architect → Scrum Master(stories) → Developer → QA`. 산출: PRD, architecture.md, stories. 각 에이전트가 버전관리 아티팩트를 다음 단계 입력으로. **"프로세스 생성기가 아니라 증폭기"** — 팀이 이미 PRD·아키텍처문서·스프린트로 사고하면 가속·감사가능화. **컴플라이언스/감사 중심에 적합**(핸드오프 전반 내장 감사추적). 소규모 변경엔 과잉("long path").

**Tessl** — Framework+Registry 공개(과거 9개월 closed beta). 최고 성숙도 **Spec-as-Source**(명세만 편집·코드 자동재생성, 명세=단일 진실원 영속·완전 추적성). 한계: 독점(락인), JS 전용, **동일 명세로부터 비결정론적 출력**(재생성 엔진 미성숙).

**Spec Kitty** — v3.1.9, 커뮤니티 포크. **git worktree 자동 오케스트레이션 병렬개발**(기능별 worktree 자동생성·병합시 정리). SDD 도구 중 최고 worktree 관리. 병렬 기능격리 필요 팀에 적합. Spec-Anchored.

---

## 5. Anthropic 공식 — Claude Code의 spec/plan 워크플로우
**주의**: Anthropic은 "spec-driven development" 용어를 1차 문서 브랜딩으로 쓰지 않음. 대신 **Plan Mode + CLAUDE.md + Skills + Subagents + Hooks** 조합으로 동등 접근 권장.

**Plan Mode**(code.claude.com/docs): Claude가 소스편집 없이 조사·변경제안만. 진입 `/plan` 또는 Shift+Tab. 권장흐름: plan mode 진입→계획 정제→auto-accept edits 전환→one-shot 구현. "계획에 노력을 쏟아 구현을 한 방에 끝내게 하라." diff를 한 문장으로 기술 가능하면 계획 생략.
**Subagents/CLAUDE.md**: `.claude/agents/`의 md(YAML frontmatter+본문=시스템프롬프트). **Explore·Plan 서브에이전트만 CLAUDE.md·git status 생략**(조사 저렴화), 나머지는 둘 다 로드. SDD식 흐름: spec 읽고→Task1 서브에이전트 스핀업(스코프된 신선 컨텍스트)→구현·커밋→다음 서브에이전트 Task2.

**공식 블로그 "Steering Claude Code" 7개 조종 방법**(claude.com/blog):
1. CLAUDE.md — 세션시작 로드·지속. "200줄 이하, 소유자 지정, 코드처럼 리뷰."
2. Rules — path-scoped, 관련시만 로드. 파일특정 제약("migrations are append-only")은 paths: frontmatter rule로.
3. Skills — **절차는 CLAUDE.md 아니라 skill에**(배포·릴리스체크리스트·리뷰프로세스).
4. Subagents — 딥서치·로그분석·의존성감사 격리.
5. Hooks — 결정론적 자동화(린터·Slack알림·명령차단).
6. Output Styles — 시스템프롬프트 전체교체.
7. System Prompt Appends — 코딩표준·도메인지식(양 늘면 준수도 감소).
**안티패턴**: 절차를 CLAUDE.md에 넣지말것(skill) / 절대금지를 instruction으로 표현말것(hook·permission) / 스코프없는 rule 금지.

---

## 6. SDD 실전 비판·한계
**대표 벤치마크 — Scott Logic Colin Eberhardt 실측**(2025-11-26): KartLog(고카트 PWA) 회로관리 기능(~1,000줄) 제거 후 Spec Kit 재구축.
- Spec Kit: 에이전트 실행 33.5분 + **인간 리뷰 3.5시간**(Planning 리뷰 2시간, Tasks 리뷰 2시간)
- 전통 반복 프롬프트: 에이전트 8분, 1,000줄(md 오버헤드 0), 리뷰15분+테스트9분 → **총 32분, 10배 빠름**

**핵심 실패모드**:
- "Markdown Avalanche": 첫 기능 하나에 md 2,577줄(planning만 5문서 2,026줄 — "quick start" 500줄+"research justification" 406줄). 저자: "상당수가 spec의 명백하고 무가치한 변환." 트랙에서 "장갑 껴야 한다" 같은 무의미 가짜 컨텍스트도.
- 구현 버그: 광범위 명세에도 circuitsData 미채움 결함 → "vibe coding 스타일" 수동수정.
- 버그 해결 모호성: SDD는 명세를 불변 취급 → 실패시 "이 버그를 명세 관점에서 어떻게 표현?" 불명확, 워크플로우 붕괴.

**"Reinvented Waterfall" 논쟁**:
- Eberhardt: 경직된 순차단계(Constitution→Specify→Plan→Tasks→Implement)가 AI의 반복적 이점 제거. "산업으로서 워터폴에서 벗어났는데 Spec Kit은 과거로 끌고 간다."
- 반론(Marc Brooker): AI가 빌드사이클을 수개월→수분 압축하면 계산이 달라짐. 피드백 루프가 5–15분(스펙→구현→리뷰→갱신·재생성, 전체 한나절)이라 형태만 닮았을 뿐 워터폴 아님.

**언제 오버헤드 부당한가(실전 합의)**: 2시간 버그수정에 spec은 절약<비용(개발자 이미 이해·국소적·완료된 것의 문서화). 반대로 여러 서비스 걸친 2주 기능은 선행비용이 모든 구현결정에 분산상각·중간 모호성 재작업 방지. **결론**: SDD는 실제 문제(컨텍스트소실·일관성·문서화) 해결하나 **복잡·안정·대규모 팀 프로젝트에서만 회수** → 팀은 **복잡도 임계값** 설정 필요. Eberhardt 최종: "순수형태로는 실행가능 프로세스로 안 봄", 단 제품오너·비기술 이해관계자엔 적합할 수도.

**공통 갭 — "Modification Problem"**: 대부분 도구가 반복적 정제에 취약. OpenSpec만 델타추적으로 "short path", BMAD는 "long path", 나머지는 우회책/전체재생성 필요.

---

## 7. 도구 선택 결정 프레임워크
- 기존 코드베이스 기능추가 → **OpenSpec**(델타 마커가 hallucination 방지)
- 새 greenfield → **Spec Kit**
- 컴플라이언스·감사 중심 → **BMAD**(내장 감사추적)
- 병렬개발·worktree 격리 → **Spec Kitty**
- 통합 IDE·AWS 생태계 → **Kiro**
- Spec-as-Source·재생성 → **Tessl**
- 불확실하면(기본값) → **OpenSpec**(도입마찰 최소·양용·락인없음)

---

## 출처 URL
Spec Kit: github.com/github/spec-kit · github.github.com/spec-kit/quickstart.html · github.com/github/spec-kit/issues/1356 · blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html
Kiro: kiro.dev/docs/specs/ · kiro.dev/docs/specs/feature-specs/ · kiro.dev/docs/steering/ · kiro.dev/docs/cli/steering/ · kiro.dev/docs/hooks/
EARS: alistairmavin.com/ears/ · en.wikipedia.org/wiki/Easy_Approach_to_Requirements_Syntax · iaria.org(Terzakis tutorial PDF)
OpenSpec/BMAD/Tessl/Spec Kitty: openspec.pro/ · github.com/cameronsjo/spec-compare · dev.to/willtorber/spec-kit-vs-bmad-vs-openspec-choosing-an-sdd-framework-in-2026-d3j · reenbit.com/bmad-vs-spec-kit-vs-openspec-choosing-your-spec-driven-ai-framework/ · thebcms.com/blog/spec-driven-development · codemyspec.com/blog/spec-driven-development
Anthropic: claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more · code.claude.com/docs/en/sub-agents · code.claude.com/docs/en/common-workflows · code.claude.com/docs/en/best-practices · claude.com/blog/subagents-in-claude-code
비판/워터폴: brooker.co.za/blog/2026/04/09/waterfall-vs-spec.html · augmentcode.com/guides/spec-driven-development-vs-waterfall · rogerwong.me/2026/03/spec-driven-development

**조사 한계**: Kiro design.md·tasks.md verbatim 예시와 Tessl 최신 세부는 공식 페이지에서 완전노출 안 됨 → 다수 2차 출처 일치내용으로 교차확정. BMAD 21개 에이전트 개별명칭은 핵심 6개 역할만 확인, 전체목록 미확정.
