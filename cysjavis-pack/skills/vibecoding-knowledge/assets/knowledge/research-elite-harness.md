# 엘리트 에이전틱 코딩 하네스 실전 기법 — 갭 5개 리서치 보고 (2025–2026)

5개 갭 전부 1차 출처(창시자 원문·공식 문서·정본 리포지토리)를 WebSearch 발견 후 WebFetch로 직접 정독·교차검증. 학습지식 단독 서술 없음.

---

## 갭 1. Compounding Engineering — Kieran Klaassen (Every / Cora)

핵심 정의: **"각 엔지니어링 작업 단위가 다음 단위를 더 어렵게가 아니라 더 쉽게 만들어야 한다."** 매 PR이 시스템을 가르치고, 매 버그가 영구 교훈이 되고, 매 코드리뷰가 기본값을 갱신하는 **기억을 가진 시스템**. Claude Code 플러그인으로 오픈소스화(수천 개발자 사용).

### 에러→영구교훈 루프 (3단계)
버그 발생 시: ①깨진 기능 즉시 수정 → ②유사 문제 방지 테스트 작성 → ③교훈을 규칙으로 문서화. 실제 예: 이메일 전송 실패 시 "전송 누락" 테스트 작성 + 모니터링 규칙 갱신 + 지속 eval 구축. 원문: **"이제 시스템이 이 부류의 문제를 항상 감시한다(the system always watches for this category of problem)."**

### 지식 저장 계층 (파일별 역할 분담)
- **CLAUDE.md**: 개인 코딩 취향을 평문으로. "CLAUDE.md becomes your taste in plain language — 왜 중첩 if보다 guard clause를 선호하는지." (guard clause·네이밍·스타일)
- **llms.txt**: 아키텍처 결정·시스템 전역 설계 원칙(기능 재구조화에도 지속되는 것)
- **slash commands + agent files**: 전문 리뷰어 페르소나("Kieran reviewer"·"Rails expert reviewer"·"performance reviewer")

### PR 리뷰→학습 루프
Claude가 과거 PR에서 프롬프트 없이 자동 학습·적용. 실제 산출 예: **"PR #234 패턴에 맞춰 변수명 변경, PR #219 피드백 반영해 과도한 테스트 커버리지 제거."** 3개월치 누적 코드리뷰를 흡수해 패턴 추출·후속 코드에 자동 적용.

### 워크플로우 메커니즘
- **테스트 주도 반복**: 예시 대화 제공 → Claude가 테스트 작성 → 통과할 때까지 탐지 프롬프트 반복 → 테스트 10회 실행해 신뢰성 검증 → 실패 런 분석해 프롬프트 정제
- **3-터미널 병렬 오케스트레이션**: Planning lane(리서치·구현계획) / Building lane(코딩·테스트) / Review lane(CLAUDE.md 대조·개선제안)
- 인간 역할 전환: 코드 타이핑 → **"시스템을 설계하는 시스템을 설계한다(design the systems that design the systems)."**
출처: https://every.to/source-code/my-ai-had-already-fixed-the-code-before-i-saw-it · https://every.to/guides/compound-engineering

---

## 갭 2. 12-Factor Agents + Advanced Context Engineering — Dex Horthy (HumanLayer)

Dex Horthy는 April 2025 에세이 "12 Factor Agents"로 "Context Engineering" 용어를 사실상 창안했다고 평가받음. **10만 개발자 세션 분석**으로 "dumb zone"(큰 컨텍스트 윈도우의 중간 40-60% 구간, 모델 recall 저하·추론 붕괴) 발견. 핵심 주장: **"컨텍스트 윈도우가 아무리 커져도 적게 쓸수록 항상 더 나은 결과가 나온다."**

### 12 Factors 전체 (이름 + 의미)
1. **Natural Language to Tool Calls** — 사용자 의도를 구조화된 함수 호출로
2. **Own Your Prompts** — 프레임워크 기본값 아닌 프롬프트 텍스트·버전을 직접 소유
3. **Own Your Context Window** — LLM에 무엇이 들어갈지 능동 큐레이션(=context engineering 뿌리)
4. **Tools Are Just Structured Outputs** — tool call=결정론적 응답 포맷팅
5. **Unify Execution State and Business State** — 에이전트 진행상태와 도메인 데이터 동기화
6. **Launch/Pause/Resume with Simple APIs** — 워크플로우 중단·재개 가능
7. **Contact Humans with Tool Calls** — 인간 개입도 tool call과 같은 인터페이스로
8. **Own Your Control Flow** — LLM 위임 대신 명시적 의사결정 로직 구축
9. **Compact Errors into Context Window** — 실패를 간결한 형태로 증류해 계속 추론
10. **Small, Focused Agents** — 단일 거대 에이전트 대신 작업별 전문 소형 에이전트(환각 표면 축소)
11. **Trigger from Anywhere, Meet Users Where They Are** — 다중 호출·채널
12. **Make Your Agent a Stateless Reducer** — (input_state, event)→output_state 순수함수(재개·테스트 용이)
출처: https://github.com/humanlayer/12-factor-agents

### ACE-FCA (Advanced Context Engineering / Frequent Intentional Compaction) 정본
핵심 원리: **"컨텍스트 윈도우의 내용물이 출력 품질에 영향을 줄 수 있는 유일한 레버다."** "vibe coding"(장시간 왕복 대화=컨텍스트 비대·slop) 거부.

**3단계 워크플로우 (각 단계가 마크다운 산출물)**:
- **Research**: 코드베이스 이해·관련 파일·정보흐름·근본원인 → 구조화 마크다운. "나쁜 리서치가 수천 줄의 잘못된 코드를 낳는다 → 여기가 최고 레버리지 인간 리뷰 지점."
- **Plan**: 정확한 구현단계·파일경로·수정전략·검증절차 → 상세 계획서. "결함 있는 계획은 수백 줄 나쁜 코드로 전파. 계획 리뷰가 코드 리뷰보다 기하급수적 ROI."
- **Implement**: 계획을 단계별 증분 실행, 각 단계 검증 후 **상태를 계획서에 compaction**, git worktree에서 수행.

**40-60% 규칙 (FIC 핵심)**: 컨텍스트 활용률을 문제 복잡도에 따라 40-60% 사이로 유지. 부분 완료 시 done 표시·남은 작업으로 컨텍스트 리프레시. Geoff Huntley 인용: "컨텍스트를 많이 쓸수록 결과가 나빠진다." Compaction 메커니즘: 장황한 출력→구조화 산출물(검색결과→요약, 탐색로그→마크다운 로드맵, git 커밋=compaction 웨이포인트). 이상적 compacted 산출물=목표 진술+접근 프레임워크+완료 단계+현재 blocker/다음 단계.

**계획을 리뷰하지 코드를 리뷰하지 않는 이유**: 팀이 코드를 훨씬 많이 찍어내면 전통 코드리뷰가 붕괴. 진짜 문제=제품이 뭘 하는지에 대한 **정신적 정렬(mental alignment) 상실**. 해결=리뷰 부담을 spec·plan 상류로 이동. "복잡한 코드 2,000줄 매일 읽기는 지속 불가, 잘 쓴 계획서 200줄 읽기가 팀 응집 유지." **인간 레버리지 피라미드**: 리서치 리뷰(수천 줄 영향) > 계획 리뷰(수백 줄) > 코드 리뷰(개별 줄).

**QRSPI 확장**: Question → Research → Spec → Plan → Implement (질문/개요 단계를 명시 삽입, 인간이 계획서 아닌 코드를 읽게 강제).

**실측 지표**:
- BAML 300k LOC Rust 코드베이스: 아마추어 Rust 개발자(BAML 경험 0)가 ~1시간에 버그픽스, 메인테이너 승인·재작업 없이 머지
- Cancellation+WASM 복합기능: 35,000줄 프로덕션 코드를 2명(1명은 코드베이스 초심자)이 7시간(리서치·계획 3h + 구현 4h). 시니어 기준 baseline은 기능당 3-5일
- HumanLayer 내부팀 3명: 월 Claude Opus ~$12,000. 인턴이 day 1에 2 PR → day 8에 10 PR, 전문가 리뷰를 체계적 재작업 없이 통과
- 경고: **"이건 마법이 아니다."** 깊은 인간 개입 필수. race condition·깊은 아키텍처 리팩터는 완벽한 context engineering으로도 현 능력 한계 초과.
출처: https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md · https://www.humanlayer.dev/blog/advanced-context-engineering

---

## 갭 3. 병렬 에이전트 플릿 운용 (git worktree + 충돌·리뷰 병목)

### 공식 worktree 메커니즘 (Claude Code 문서)
문제: 한 repo에 여러 Claude를 돌리면 브랜치 충돌·stash 혼돈. git worktree=각 에이전트에 격리된 디렉토리 + 공유 git 히스토리.
- `claude --worktree feature-auth` (또는 `-w`): `.claude/worktrees/<name>/`에 `worktree-<name>` 브랜치로 생성·시작. 이름 생략 시 자동 생성(bright-running-fox). 다른 터미널서 다른 이름으로 재실행=2번째 격리 세션.
- 세션 중 "work in a worktree" 요청 시 `EnterWorktree` 도구로 생성. repo 밖 경로 진입은 승인 필요(bypassPermissions만 skip).
- 기본 base=`origin/HEAD`(원격 매칭 깨끗한 트리, 24h 내 fetch 없으면 5초 캡으로 refresh). `worktree.baseRef:"head"`로 로컬 HEAD 기반 전환(미푸시 커밋 포함). `claude --worktree "#1234"`로 특정 PR 기반.
- `.worktreeinclude`(.gitignore 문법): `.env` 등 gitignored 파일 자동 복사(tracked는 중복 안 됨).
- **서브에이전트 격리**: frontmatter에 `isolation: worktree` 추가 시 각 서브에이전트가 임시 worktree, 변경 없이 끝나면 자동 제거. (Agent 도구의 `isolation:"worktree"` 파라미터와 동일)
- 정리: 변경 없으면 worktree·브랜치 자동 제거. 변경/커밋 있으면 keep/remove 프롬프트. `-p` 비대화형은 자동정리 안 됨 → `git worktree remove` 수동.
- `.gitignore`에 `.claude/worktrees/` 추가 권장.
출처: https://code.claude.com/docs/en/worktrees

### 병렬 도구 생태계
Parallel Code(johannesjo, Claude/Codex/Gemini 병렬+worktree diff 리뷰·머지), Uzi, AI-fleet, Claude-flow, Claude-simone, Conductor. **container-use MCP 서버**: 에이전트가 다중 컨테이너 spawn(Claude parallel work·Cursor background agents가 사용). 공식도 devcontainer/컨테이너 실행 권장.
출처: https://github.com/johannesjo/parallel-code · https://www.developersdigest.tech/blog/git-worktrees-claude-code-parallel-agents-guide

### 실전 한계와 리뷰 병목 (상충 지점)
- **"진짜 병목은 에이전트나 모델이 아니라 한 번에 하나씩 오케스트레이션하는 인간이다."** 세션 전환·다음 작업 결정·단계 완료 시 진행이 인간 triage에 묶임.
- **리뷰 병목은 에이전트 수에 선형 비례**: 10 에이전트×15분 diff=시간당 10개 diff 리뷰. 파일 충돌·브랜치 충돌·자원 경합 동반.
- **실용 상한**: 노트북에서 웹개발 기준 **4-5 worktree가 실질 천장**(그 이상은 원격 머신+SSH로 브랜치 pull back). 대부분 개발자에겐 **2-4 병렬이 sweet spot**(각 산출물 리뷰·통합할 정신적 대역폭 한계).
- **Fan-out 패턴**: coordinator가 큰 작업을 병렬 하위작업 분할·디스패치·머지. 단 "orchestrator가 추론 무거운 일도 하면 단일 장애점·성능 제약." (앞 보고서 갭4의 orchestrator-subagent 한계와 정합)
출처: https://superset.sh/blog/parallel-coding-agents-guide · https://addyosmani.com/blog/code-agent-orchestra/

---

## 갭 4. UI/시각 검증 루프 — Playwright MCP self-loop

### 자율 루프 (6단계)
①프론트엔드 코드 수정 → ②Playwright로 해당 페이지 navigate → ③지정 viewport 스크린샷 → ④렌더링 결과를 디자인 문서와 비교 → ⑤불일치·콘솔에러 식별 → ⑥수정·재검증(인간 개입 없이). 원문: **"prompt-and-pray 한 사이클 대신, 모델이 코드 쓰고, 결과를 보고, 문제 식별하고, 고치고, 다시 검증한다. 자율적으로."**

### 설치·구성
`claude mcp add playwright -- npx @playwright/mcp@latest`. `/mcp`로 ~30개 도구 확인(navigate·click·type·screenshot·evaluate·wait_for_selector 등).

### 디자인 시스템을 AI에 강제하는 파일 구조
| 파일 | 역할 |
|---|---|
| `CLAUDE.md` | 시각적 개발 지시·변경 후 검증 단계 |
| `context/design-principles.md` | 미학 가이드라인(테마 원칙) |
| `context/style-guide.md` | 디자인 토큰(색·타이포·간격) |

### Design Reviewer 서브에이전트 패턴
`.claude/agents/design-reviewer.md`: 다중 viewport(데스크톱/태블릿/모바일) 스크린샷·접근성 체크·콘솔에러 로깅 → 등급·실행가능 수정안 구조화 리포트. `.claude/commands/design-review.md` slash command로 일관 호출.

### 핵심 제약 (상충 지점)
Playwright MCP는 **~30개 도구 스키마를 컨텍스트에 로드**해 추론에 쓸 토큰을 잠식. 기사는 대형 코드베이스에서 토큰 효율을 위해 **"SKILLS 기반 CLI 대안"이 MCP를 대체할 수 있다**고 지적 — 앞 보고서의 "MCP 최소화, CLI 직접"(Ronacher·Willison) 논지와 정합. Anthropic 공식도 브라우저 self-verification(스크린샷을 fixture/디자인과 비교)을 "검증 수단"의 한 형태로 권장(앞 보고서 §1①).
출처: https://ap7i.com/posts/giving-claude-code-eyes-with-playwright-mcp/ · https://www.builder.io/blog/playwright-mcp-server-claude-code

---

## 갭 5. 에이전트 메모리·지식 축적 — ADR / docs-as-memory

배경: AI 에이전트는 전통적 지식 전달 가정을 깬다. **"에이전트는 1분에 20개 파일을 건드리고 PR을 열고 다음 작업으로 넘어간다 — 지난 스탠드업의 공유기억도, 그 규칙을 낳은 장애의 흉터조직도 없이."** 생성이 이렇게 빠르면 **명시적으로 표현된 관례만 살아남는다.** ADR은 "AI 에이전트가 프로덕션을 건드리는 팀의 load-bearing 인프라."

### ADR 저장·포맷 (정본)
- 위치: **버전관리 안 `docs/adr/`**(외부 위키 아님). 순차번호 `ADR-001.md`, `ADR-002.md`.
- 템플릿: `# ADR-NNN: 제목(능동태)` / Status(Proposed|Accepted|Deprecated|Superseded|Rejected) / Date / Authors / **Context**(결정을 요구한 상황·비자명 제약: 과거 사건·컴플라이언스·벤더 SLA, 2-3문단) / **Decision**(능동태 1-2문장 "We will use X for Y") / **Consequences**(쉬워지는 것·어려워지는 것·2차 효과 3-7 bullet) / **Alternatives considered**(기각 이유) / **Related**(다른 ADR·사건·RFC 링크).
- 별칭 파일: `DECISIONS.md`(엄격 포맷의 ADR 로그, 에이전트가 orient용으로 읽음), `AGENTS.md`(범용 에이전트 지침 — ADR과 상보).

### 에이전트가 읽고 쓰는 법
- **검색**: 프레임워크가 계획 중 ADR 자동 인덱싱·관련 것을 제약으로 검색. 에이전트=**"이전 약속을 존중하는 제약된 플래너(constrained planner)"** (stateless 코드 생성기 아님).
- **인용**: 검색한 ADR을 PR 설명에 인용(사전 아키텍처 약속 이해 입증). "관련 ADR을 검색·인용하는 에이전트가 팀의 제도적 기억에 편입된 에이전트."

### 드리프트 방지 규칙 (핵심)
- **새 아키텍처 패턴은 코드 변경과 *같은 PR*에 ADR 포함**(후속 아님). 리뷰어는 ADR 없으면 PR 거부("작다"는 예외 없음).
- **삭제 금지**: ADR은 status만 바뀌고 제거 안 됨(에이전트가 결정 진화를 추론해야). 
- **스코프 규율**: 미래 작업을 제약하거나 되돌리기 비싼 결정만. 사소한 구현 선택은 자격 없음.
- 워크플로우: 아키텍처 중요 변경 생성 → 계획 중 기존 ADR 검색 → 새 패턴이면 같은 PR에 새 ADR → 리뷰어 ADR 부재 시 거부 → 머지된 PR=코드+제도기록.
출처: https://rickpollick.com/blog/adr-comeback-anchoring-agentic-engineering-teams · https://mnemehq.com/insights/how-ai-coding-agents-use-adrs/ · https://ai.gopubby.com/agents-md-is-the-ew-architecture-decision-record-adr-3cfb6bdd6f2c

관련 실험적 접근: **Lore**(git 커밋 메시지를 AI 에이전트용 구조화 지식 프로토콜로 재활용, arXiv 2603.15566), **"메모리는 파일 하나가 아니라 파일링 시스템"**(Brennan Moore) — 앞 보고서 Anthropic structured note-taking과 정합.

---

## 상충·대립 견해 종합

| 쟁점 | 견해 A | 견해 B |
|---|---|---|
| **컨텍스트 활용률** | Horthy FIC: 40-60% 아래로 강제 유지(넘으면 dumb zone) | Anthropic compaction: 한계 근접 시 요약. Horthy는 훨씬 공격적·선제적(예방 vs 대응) |
| **리뷰 대상** | Horthy: 코드 아닌 research·plan 리뷰(상류 레버리지) | 전통·Boris: 코드 diff 리뷰(fresh context reviewer). Horthy는 "코드리뷰는 스케일서 붕괴"로 격하 |
| **병렬 에이전트 수** | worktree 도구 진영: 5+ 에이전트 동시 가능 | 실전 합의: 인간 리뷰 대역폭 때문에 2-4가 sweet spot, 그 이상은 원격+비동기 |
| **MCP vs CLI(UI 검증)** | Playwright MCP로 브라우저 눈 부여 | ~30 도구 스키마가 토큰 잠식 → SKILLS/CLII 대안이 대체 전망(Ronacher·Willison 논지) |
| **메모리 매체** | ADR/DECISIONS.md(파일·git·삭제금지) | 벡터DB 기반 에이전트 메모리 프레임워크. ADR 진영은 "감사가능·소유권·추적" 우위 주장 |
| **자동화 수준** | Compounding: 시스템이 스스로 학습·자동 적용 | ACE-FCA: "마법 아니다, 깊은 인간 개입 필수" — 자동학습 낙관론과 긴장 |

---

## 자비스 하네스 시사점 (관련)
- **Compounding의 에러→규칙 영속화 루프**는 자비스의 memory(feedback 타입)·directive 축적과 정확히 같은 구조. Kieran의 "3개월치 PR 흡수" = 자비스 memory 색인의 목적.
- **Horthy의 QRSPI·40% 룰·계획 리뷰**는 자비스 SESSION_STATE compaction·60% /clear·grill-me 의도합의와 대응(단 자비스는 60%, Horthy는 40-60%로 더 공격적).
- **ADR 같은 PR 강제·삭제금지**는 자비스 커밋 trailer 규약(Constraint/Rejected/Directive)·handoff 계약과 동형. git log=경량 ADR 원칙이 이미 CLAUDE.md에 존재.
- **worktree isolation:worktree**는 자비스 워커/서브에이전트 격리에 직접 적용 가능한 공식 메커니즘.
- 판단·채택은 master 몫.

### 1차 출처
- Kieran Klaassen: https://every.to/source-code/my-ai-had-already-fixed-the-code-before-i-saw-it
- 12-Factor Agents: https://github.com/humanlayer/12-factor-agents
- ACE-FCA: https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md
- 공식 worktree: https://code.claude.com/docs/en/worktrees
- Playwright MCP 시각루프: https://ap7i.com/posts/giving-claude-code-eyes-with-playwright-mcp/
- ADR 메모리: https://rickpollick.com/blog/adr-comeback-anchoring-agentic-engineering-teams
- 병렬 병목: https://superset.sh/blog/parallel-coding-agents-guide
