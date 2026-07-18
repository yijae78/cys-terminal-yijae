# vibecoding hooks — 옵트인 넛지 3종

자비스 바이브코딩 마스터 체계(`_research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md`)의
헌법 4·8·10조를 **경고·넛지**로 배선한 훅 묶음이다. **세 훅 전부 옵트인** — 어떤 settings.json에도
자동 등록하지 않으며, 아래 "등록 방법"으로 명시 등록해야만 발동한다.

> ⚠ 이 디렉토리의 훅은 기존 부트스트랩·온보딩 훅 체인과 **완전히 분리**돼 있고, 기존 훅 파일은
> 하나도 수정하지 않는다. 등록 전까지는 순수 소스 파일일 뿐 어떤 세션에도 영향을 주지 않는다.

## 훅 3종

| 훅 | 이벤트 | 트리거 | 동작 |
|---|---|---|---|
| `vibe-doc-sync.sh` | PostToolUse(Edit\|Write) | 코드 파일 편집 + working tree에 `.md` 변경 0 | stderr 경고 (헌법 8조 doc-sync) |
| `vibe-regression.sh` | PostToolUse(Bash) | `javis_task … set-status … done` 감지 | stderr 경고 (헌법 4조 회귀 게이트·테스트 스위트 존재/실행 점검) |
| `vibe-distill-nudge.sh` | PostToolUse(Bash) | 에러 수정·리뷰 종결형 `git commit` 감지 | additionalContext 넛지 (헌법 10조 증류 의무 → `javis_distill propose`) |

세 훅 모두 **non-blocking**이다: 세션을 차단(deny/exit 2)하지 않고 경고·넛지만 낸다.
`vibe-doc-sync`·`vibe-regression`은 stderr 경고(사람에게 보임), `vibe-distill-nudge`는
`additionalContext`(에이전트 컨텍스트에 주입 — 기존 `commit-memory-nudge.sh`와 동일 방식)를 쓴다.

## 부트체인 안전 3원칙 (전 훅 공통 — 스크립트 주석에도 명시)

1. **5초 이내 종료** — 무거운 스캔·네트워크 금지(`find`는 `-maxdepth 2` 얕은 검사, git status만).
2. **어떤 실패에도 `exit 0`** — 훅 실패가 세션·부트체인을 절대 차단하지 않는다(`set +e`).
3. **의존 도구·경로 부재 시 조용히 skip** — git 부재(doc-sync)·대상 명령 아님(regression)·
   `javis_distill.py` 부재(distill-nudge) 시 에러 없이 `exit 0`.

## 등록 방법 (settings.json)

배포 경로(`~/.cys/pack/hooks/vibecoding/`)를 기준으로 `settings.json`의 `hooks`에 추가한다.
훅은 팩 배포로 소스(`cysjavis-pack/hooks/vibecoding/`) → 배포처(`~/.cys/pack/hooks/vibecoding/`)로 반영된다.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "$HOME/.cys/pack/hooks/vibecoding/vibe-doc-sync.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "$HOME/.cys/pack/hooks/vibecoding/vibe-regression.sh" },
          { "type": "command", "command": "$HOME/.cys/pack/hooks/vibecoding/vibe-distill-nudge.sh" }
        ]
      }
    ]
  }
}
```

세 훅은 독립적이라 원하는 하나만 등록해도 된다. 파일럿 대상 세션(프로필)에만 국소 등록하는 것을 권장한다.

## 왜 옵트인인가 (측정 계약이 구현에 선행)

제안서 **§C6(Pilot Protocol)**와 로드맵 "Phase 순서 불변 원칙"은 **측정 계약(§C6·§C7)이
구현·전면 배포(Phase 2~4)에 선행**한다고 못박는다 — "거대한 규율을 먼저 구축한 뒤 효과를 확인"하는
순서 역전(codex R1 issue 8)을 구조적으로 차단하기 위함이다. 따라서:

- pilot 2건(L3 brownfield 1건 + L5 1건)으로 문서량·리뷰시간·재작업률을 실측하고 사전등록 임계값
  (§C6.2)을 **pass** 하기 전까지, 이 훅들을 전 세션에 강제 배선하지 않는다.
- 강제 배선은 파급효과가 커(hooks는 전 세션 영향) pilot 데이터 없이 켜면 false-positive 넛지가
  전 워커의 컨텍스트를 오염시키고 부트체인 안정성을 위협한다.
- 그래서 현 단계 산출물은 **경고·넛지(non-blocking)**뿐이다. 이는 §C6의 "구현 전 측정" 규율과
  헌법 8조 doc-sync의 pilot 게이트(제안서 §C6.3~C6.4 rollback 경로)에 정합한다.

## 차단(blocking) 모드 전환 조건

아래를 **모두** 충족했을 때만 non-blocking → blocking(exit 2 deny) 전환을 검토한다:

1. **§C6 pilot pass**: L3·L5 pilot 2건이 사전등록 임계값(문서량·리뷰시간·재작업률·회귀/보안 게이트)을
   전부 충족(§C6.3 판정 규칙의 `pass`).
2. **오탐률 실측 확보**: pilot 기간 각 훅의 false-positive 비율을 측정해 차단으로 전환해도 워커 흐름을
   막지 않음을 확인(특히 `vibe-doc-sync`의 "문서 불필요 변경" 오탐).
3. **오너(doctor) 재가**: 헌법 조문의 집행 강도 격상은 정지 경계(디렉티브·헌법 집행 변경)에 해당 —
   전환은 `[DECISION]`(§C11) 또는 오너 승인(approval_id) 기록 후에만.

전환 시에도 대상 훅만 각 조문의 §C1 enforcement contract·§C2 precedence를 준수하는 exit 2 경로로
바꾸고, 나머지는 non-blocking으로 유지한다(단계적 격상).
