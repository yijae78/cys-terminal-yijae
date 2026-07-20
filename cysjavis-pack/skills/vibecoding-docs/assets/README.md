# vibecoding-docs 템플릿 팩

NLC(자연어 코딩, Natural Language Coding) "Spec/Doc driven 10단계"를 그대로 옮긴 md 문서 템플릿 팩이다.
프로젝트에 인스턴스화하면 헌법(rules)부터 실행(implement)까지의 문서 계층이 한 벌로 깔린다.

> 최상위 경고(NLC): "md 문서를 만들어 놓는 것만으로는 아무 일도 자동으로 일어나지 않는다."
> 반드시 `bootstrap/CLAUDE.md.template`로 브릿지 개조를 하고, 규칙·설계 문서 변경 후 `ruler apply`를 수행해야 작동한다.

## 구성

```
assets/
  templates/     10단계 28문서 템플릿 (1-1_AGENTS.md ~ 10-2_initial-implement.md)
  bootstrap/     CLAUDE.md.template (브릿지 로더) · AGENTS_MASTER_PROMPT.md (관제탑 AGENTS.md 생성 프롬프트)
  agents/        서브에이전트 6종 (usecase-writer · common-task-planner · plan-writer · design-agent · implementer · design-reviewer)
  design/        design-principles.md.template · style-guide.md.template (시각 검증 토큰)
  README.md      이 문서
```

## 28문서 → 프로젝트 경로 대응 (개요 표 그대로)

| 단계 | 템플릿 | 프로젝트 경로 | 명칭 |
|---|---|---|---|
| 1-1 | templates/1-1_AGENTS.md | /AGENTS.md | Agents Constitution |
| 1-2 | templates/1-2_rules.md | /rules.md | Global Immutable Rules |
| 1-3 | templates/1-3_ruler.md | /ruler/*.md | Execution Rulers |
| 2-1 | templates/2-1_root-sot.md | /docs/_root-sot.md | Root SOT |
| 2-2 | templates/2-2_uepp.md | /docs/rules/uepp.md | UEPP |
| 2-3 | templates/2-3_scdp.md | /docs/rules/scdp.md | SCDP |
| 2-4 | templates/2-4_rcmp.md | /docs/rules/rcmp.md | RCMP |
| 2-5 | templates/2-5_persona.md | /docs/persona.md | Persona |
| 2-6 | templates/2-6_project.md | /docs/project.md | Project Definition |
| 2-7 | templates/2-7_env.template.md | /docs/environment/env.template.md | Environment Template |
| 2-8 | templates/2-8_tech-stack.md | /docs/tech-stack.md | Tech Stack |
| 2-9 | templates/2-9_codebase-structure.md | /docs/codebase-structure.md | Codebase Structure |
| 2-10 | templates/2-10_requirement.md | /docs/requirement.md | SRS |
| 3 | templates/3_external-integration.md | /docs/external/*.md | External Integration |
| 4 | templates/4_prd.md | /docs/prd.md | PRD (+prd-critic) |
| 4-1 | templates/4-1_fds.md | /docs/rules/fds.md | FDS Root Spec |
| 4-2 | templates/4-2_ui.md | /docs/design/ui.md | UI IA Spec |
| 5 | templates/5_userflow.md | /docs/userflow.md | User Flow |
| 5-1 | templates/5-1_ux.md | /docs/design/ux.md | UX Design |
| 6 | templates/6_database.md | /docs/database.md | Data Flow & Schema |
| 7 | templates/7_spec.md | /docs/spec.md | Use Case Spec |
| 8 | templates/8_state-management.md | /docs/state-management.md | State & Flux Model |
| 8-1 | templates/8-1_page-state-mapping.md | /docs/page-state-mapping.md | Page–State Mapping |
| 8-2 | templates/8-2_visual.md | /docs/design/visual.md | Visual Spec |
| 9 | templates/9_test.md | /docs/test.md | TDD Spec |
| 9-1 | templates/9-1_test-plan.md | /docs/test-plan.md | Test Plan |
| 10-1 | templates/10-1_plan.md | /docs/plan.md | Implementation Plan |
| 10-2 | templates/10-2_initial-implement.md | /docs/initial-implement.md | Execution & Report |

## Level별 필수 템플릿 (복잡도 라우팅)

작업 복잡도에 따라 어느 템플릿까지 필수인지가 달라진다. 격상은 허용, 격하는 금지(Constitution 7조).

- **L1~L2 (경량/스크립트)**: 필수 문서 없음. 단순 요청은 문서 없이 직접 구현. (헌법 계층은 선택.)
- **L3 (기능 단위)**: `requirement` + `spec` + `test`. — "무엇을 만들지 → 어떻게 작동 → 어떻게 검증"의 최소 3종.
- **L4 (다중 상태/데이터 기능)**: L3 + `state-management`(8) + `database`(6) + `external-integration`(3, 경계). — 상태·데이터·외부 경계가 얽히면 추가.
- **L5 (풀스택 제품)**: **풀 세트(28문서 전체)**. 헌법 계층(1-1~2-4) + 기획(2-5~2-10) + 설계(3~8-2) + 검증·실행(9~10-2) 전부.

> Level 판정은 격상만 허용된다. 애매하면 상위 Level로 올린다(과소 발화가 안전).

## 사용 절차

1. **인스턴스화**: 필요한 Level의 템플릿을 프로젝트의 대응 경로로 복사하고 `[FILL: ...]` 앵커를 채운다.
2. **브릿지 개조**: `bootstrap/CLAUDE.md.template`를 프로젝트 `./CLAUDE.md`로 두고 `@import` 경로를 확인한다.
3. **관제탑 AGENTS.md**: `bootstrap/AGENTS_MASTER_PROMPT.md`를 실행해 루트 `./AGENTS.md`(Context Map 라우팅)를 생성한다.
4. **서브에이전트 배치**: `agents/*.md`를 `/claude/agents/`(또는 프로젝트 에이전트 경로)로 복사한다.
5. **시각 검증**: `design/*.template`를 `context/`로 두고 `design-reviewer`가 대조하게 한다.
6. **ruler apply**: 규칙·헌법·설계 문서를 만들거나 고칠 때마다 실행한다(코드/env 변경만으론 불필요).
7. **세션 sanity check**: 매 새 세션 첫 턴에 "지금 로드된 규칙/메모리 요약을 말해봐"로 로드 여부를 확인한다.

## 생성 순서 (헌법 계층)

`AGENTS.md → rules.md → ruler/*.md → _root-sot.md → docs/rules/*.md`.
(철학=Root SOT는 의도적으로 늦게 만든다 — @ruler보다 먼저 만들면 철학이 전술 규칙으로 오염된다.)

## 계약 골격 불변 (모든 pipeline 템플릿 공유)

각 템플릿 YAML front-matter의 `sot`(2종 고정) · `context`(상속 목록) · `inheritance`(additive-only · override-prohibited · root-sot-priority · uepp-auto · scdp-auto · rcmp-auto · context-propagation-invariant)는 **수정 금지 영역**이다. 하위 문서는 상위를 override할 수 없고 추가만 가능하다.
