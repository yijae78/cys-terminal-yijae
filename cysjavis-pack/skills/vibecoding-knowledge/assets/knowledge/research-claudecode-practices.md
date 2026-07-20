# Claude Code 고급 에이전틱 코딩 베스트 프랙티스 (2025–2026) — 리서치 보고

6개 영역 전부 공식 1차 출처(Anthropic 문서·엔지니어링 블로그)와 실전가 원문을 WebSearch 발견 후 WebFetch로 직접 정독·교차검증했습니다. 학습지식 단독 서술 없음.

## 0. 관통 대전제: "컨텍스트 윈도우가 유일한 제약"

공식 Best Practices가 명시: "거의 모든 베스트 프랙티스는 하나의 제약에서 나온다 — 컨텍스트 윈도우는 빨리 차고, 차오를수록 성능이 저하된다." 모든 기법(서브에이전트·/clear·skills 온디맨드·hooks)은 결국 컨텍스트를 아끼거나 격리하는 장치다. (https://code.claude.com/docs/en/best-practices)

## 1. 공식 Best Practices — 핵심 6원칙

① **검증 수단을 반드시 쥐여줘라(가장 중요)**: Claude는 "끝나 보이면" 멈춘다. pass/fail 신호(테스트·빌드 exit code·린터·fixture diff·스크린샷)를 준다. 게이트 강도 4단계 — 한 프롬프트 내 / `/goal` 조건(별도 evaluator 매 턴 재확인) / Stop hook(통과 전 턴 종료 차단, 단 8회 연속 차단 시 hook 무시하고 종료) / verification subagent가 fresh model로 반증. "검증할 수 없으면 배포하지 마라." 성공 단언 말고 증거 제시.

② **Explore→Plan→Code→Commit**: plan mode로 탐색·실행 분리(Ctrl+G로 계획 직접 편집). 단 "diff를 한 문장으로 설명 가능하면 plan 건너뛰라."

③ **CLAUDE.md 엄격 규칙**: `/init`로 시작. 매 세션 로드되니 넓게 적용되는 것만. 각 줄 자문 "지우면 실수하는가? 아니면 지워라." "비대하면 Claude가 실제 지시를 무시한다." 포함=추측불가 bash·기본값과 다른 스타일·테스트러너·repo예절·아키텍처 결정·env quirk / 제외=코드로 알 수 있는 것·표준 관례·상세 API문서·자주 바뀌는 정보. "IMPORTANT"/"YOU MUST"로 강조. 위치: 전역 ~/.claude·팀공유 ./CLAUDE.md·개인 .local·모노레포 상하위. @import 지원.

④ **권한 완화 3방식**: auto mode(분류기가 위험만 차단)·/permissions 허용목록·/sandbox.

⑤ **세션·컨텍스트 공격적 관리**: 무관 작업마다 /clear. "같은 이슈 2회 넘게 교정 → 컨텍스트 오염 → /clear+더 나은 프롬프트가 거의 항상 낫다." /compact·/rewind·/btw. CLAUDE.md에 compaction 커스터마이즈("압축 시 수정 파일 목록·테스트 명령 보존").

⑥ **흔한 실패 5패턴(공식 명시)**: kitchen sink세션→/clear, 반복교정→2회 후 /clear, 과도한 CLAUDE.md→가지치기, trust-then-verify갭→항상 검증, 무한탐색→서브에이전트 격리.

## 2. Steering 결정 프레임워크 (공식 결정표)

"매번 X면 항상 Y"→**Hooks**(결정론) / "절대 하지마"→Hooks·permissions / 30줄 절차→**Skills** / API 규칙→**path-scoped rules** / 개인선호→user-level / 팀관례→root CLAUDE.md(200줄 미만) / 절차적 리뷰→Skills+slash command.

핵심 구절: "절대 일어나면 안 되는 것에는 지시(instruction)가 잘못된 도구다. 진짜 가드레일은 결정론적이어야 하고 그 수단은 hooks와 permissions다." PreToolUse hook이 exit code 2로 tool call 거부. Subagent는 별도 컨텍스트에서 돌고 최종 요약만 반환("그 격리가 skill 대신 subagent 쓰는 이유"), 최대 5단계 중첩(v2.1.172+). Output Styles는 절대 compaction 안 됨. (https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)

## 3. Agent Skills 저작 (공식 가이드)

5패턴: 라우팅 규칙처럼 읽히는 description / 결정론 작업엔 결정론 코드 / detail은 companion 파일로 / 스킬당 하나의 일 / 추상 아닌 구체 예시. "8~12개 잘 고른 스킬이 시니어 하루 대부분 커버, 그 이상은 context tax."

- **Concise**: "컨텍스트는 공공재." Claude가 아는 건 넣지마.
- **자유도 매칭**: high(텍스트 지시)/medium(파라미터 스크립트)/low(정확한 스크립트, "명령 수정 마라"). 비유: 낭떠러지 좁은 다리 vs 열린 들판.
- **description 반드시 3인칭**("Processes~", "I can help" 금지 — 시스템 프롬프트 주입되어 시점 불일치가 발견 깨뜨림). 무엇+언제 둘 다. name 최대 64자 소문자/숫자/하이픈, "anthropic"·"claude" 예약어 금지. description 최대 1024자. gerund형 권장(processing-pdfs).
- **Progressive disclosure**: SKILL.md body 500줄 미만. 참조는 SKILL.md에서 1단계 깊이만(중첩 시 head -100 부분읽기로 누락). 100줄+ 참조엔 TOC 필수.
- **Eval-driven(핵심)**: "광범위 문서 쓰기 전 eval 먼저." 스킬없이 실행→실패문서화→3시나리오 eval→베이스라인→최소지시→반복. "eval이 효과 측정의 source of truth."
- **Claude A/Claude B 패턴**: A가 스킬 설계·개선, B(fresh)가 실전 테스트, 관찰을 A에 피드백. 최소 3 eval + Haiku/Sonnet/Opus 전부 테스트.
- 스크립트: "defer 말고 solve", voodoo constant 금지, plan-validate-execute. (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

## 4. 멀티에이전트 오케스트레이션 5패턴 (공식)

① **Generator-Verifier**: 명확 기준 있는 품질중심. 한계=기준 없으면 verifier가 "rubber-stamp". ② **Orchestrator-Subagent**: 분해되는 단기작업. 한계=orchestrator 병목·순차. "대부분 여기서 시작." ③ **Agent Teams**: 병렬·독립·장시간·지속컨텍스트. 한계=worker간 중간발견 공유 난이도. ④ **Message Bus**: 이벤트 파이프라인. 한계=silent failure. ⑤ **Shared State**: 서로 발견 위에 쌓기. 한계=종료조건 없으면 중복·반응루프.

**리서치 시스템 교훈**: orchestrator-worker(lead가 3-5 병렬 subagent spawn→종합→citation pass). 단일 Opus 대비 90.2% 향상, 토큰 15배, "토큰이 성능분산 80% 설명." **Subagent 계약 4요소(놓치면 drift)**: 목표·출력형식·도구/소스 가이드·task 경계. **Verification subagent 성공 이유**: "telephone game 우회 — 검증은 최소 컨텍스트 전달만 필요, verifier가 전체 히스토리 없이 blackbox 테스트." = "일한 에이전트가 채점 안 함"의 근거. (https://claude.com/blog/multi-agent-coordination-patterns)

## 5. Ralph Wiggum Loop & 자율 루프

창시자 **Geoffrey Huntley(2025)**. 본질="while true 배시 루프가 완료까지 같은 프롬프트 반복 투입." **Anthropic 공식 플러그인화**: anthropics/claude-code의 ralph-wiggum + 내장 /loop·/goal·/batch. 공식 구현은 외부 배시 아닌 **Stop hook으로 세션 내부 루프**(종료 시도→차단→동일 프롬프트 재투입→completion-promise 정확 문자열 매칭까지). 안전장치: --max-iterations(주 안전장치, 예 20)·--completion-promise. 좋은 프롬프트=명확 완료기준+단계목표+자가교정(TDD)+"막히면 뭐할지" escape hatch. 부적합=인간판단·one-shot·프로덕션 디버깅. 실적: YC 하룻밤 6 repo, $297로 $50k 계약. (https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md)

## 6. 실전 고수 하네스 (1차 원문)

**Boris Cherny(창시자)**: "검증이 가장 중요" — 자기검증 수단 주면 품질 2-3배. 하루 20-30 PR·5개 병렬 인스턴스. plan mode 시작→계획 반복→"좋은 계획 서면 거의 매번 one-shot." 팀 전체 단일 CLAUDE.md git 공유·주 여러번 기여, "잘못하면 즉시 CLAUDE.md 추가." verification subagent 자체 구축(통과 전 complete 안 함). /commit-push-pr slash command 매일 수십번(inline bash로 사전계산). Opus+thinking 모든 코딩에. (https://newsletter.pragmaticengineer.com/p/building-claude-code-with-boris-cherny)

**Simon Willison**: 에이전트="목표 향해 루프서 도구 돌리는 것, 기술은 어떤 도구·어떤 루프 설계할지." 테스트가 단일 최우선 검증. Brainstorm(spec)→Plan→Execute, spec을 SOT로(Vibe Coding 대척점). --dangerously-skip-permissions는 Docker 안에서. (https://simonwillison.net/2025/Jun/29/agentic-coding/)

**Armin Ronacher**: claude-yolo(--dangerously-skip-permissions) 전권+Docker, 거의 개입 안 함. MCP 거의 안 씀(일반 도구 직접 실행, Playwright만). 통합 로깅(make tail-logs로 자율 진단). 도구=빠를것(hang이 crash보다 나쁨)·명확 에러·관측성. 언어 Go 강추(명시적 context·낮은 churn), Python은 "상당한 도전." "동작하는 가장 멍청한 것 써라." (https://lucumr.pocoo.org/2025/6/12/agentic-coding/)

## 7. Context Engineering (2025.9 Anthropic 공식)

prompt→context engineering 전환("진화하는 정보 우주서 제한된 윈도우에 넣을 것 반복 큐레이션"). **Right altitude 시스템 프롬프트**: 너무 구체적(brittle)도 모호도 아닌 "강한 heuristic 줄 만큼 유연", XML/Markdown 섹션 구분. **도구**: self-contained·최소 중첩, "엔지니어가 어떤 도구 쓸지 확정 못하면 에이전트도 못한다." **Few-shot**: 정준적 예시 큐레이션("예시는 LLM에 천 마디 말 같은 그림"). **장기지평 3기법**: ①Compaction(요약 후 재개, "recall 최대화부터 precision 반복") ②Structured note-taking(컨텍스트 밖 파일 메모, Claude Code to-do·Pokémon 사례·memory tool) ③Sub-agent(각 수만 토큰 쓰되 1000-2000 토큰 정제 요약만 반환). Context rot=18 LLM서 토큰 증가에 단순작업도 비균일 저하. (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

## 8. 상충·대립 견해

- **권한**: Ronacher 전면 skip-permissions vs Willison·Anthropic Docker/샌드박스/분류기 신중론(무인 -p는 반복차단 시 자동 abort).
- **Ralph fresh context**: 공식 ralph-wiggum "fresh 불필요(프롬프트 불변·파일이 상태)" vs Huntley 원형·codecentric "fresh가 핵심(오염 회피)" — 구현 계보에 따라 갈림.
- **MCP**: 공식 "claude mcp add 적극 권장" vs Ronacher·Willison "MCP 최소화, CLI 직접이 context-efficient."
- **모델**: Boris Opus+thinking(품질) vs Ronacher Sonnet($100 Max, 실용).
- **Reviewer**: 공식 자체 경고 — "gap 찾으라 시킨 reviewer는 건전한 작업에도 gap 보고 → 과잉엔지니어링. correctness/요구사항 영향 gap만 flag하라."

## 9. 자비스 하네스 시사점 (관련)

공식 원칙과 정합: master/worker 위임·verifier(agy·codex) 분리·eval-driven(producer≠evaluator)·SESSION_STATE=structured note-taking·RSI 라운드=자율 루프 — 모두 위 공식 패턴의 직접 대응물.

**긴장 하나만 지적(개선제안 아닌 사실 대비)**: 공식 최우선 원리는 "CLAUDE.md 200줄 미만, 비대하면 절반 무시("important rules get lost in the noise")." 현 프로젝트/글로벌 MASTER 색인은 이 임계를 크게 초과. 공식 진단대로면 규칙 희석 리스크 실재. 다만 의도적 다층 앵커 설계이므로 판단은 master 몫.

## 1차 출처

- best-practices: https://code.claude.com/docs/en/best-practices
- steering: https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more
- skills: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- context eng: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- multi-agent: https://claude.com/blog/multi-agent-coordination-patterns
- ralph: https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md
- Boris: https://newsletter.pragmaticengineer.com/p/building-claude-code-with-boris-cherny
- Willison: https://simonwillison.net/2025/Jun/29/agentic-coding/
- Ronacher: https://lucumr.pocoo.org/2025/6/12/agentic-coding/
