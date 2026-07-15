#!/bin/bash
# javis 결정론 부트스트랩 발화 — UserPromptSubmit hook
#
# 절대요구(오너 2026-07-15): "너는 마스터다" 류 마스터 선언이 입력되면, LLM의 재량·환각·누락과
# 무관하게 하네스가 부트스트랩을 100% 예외없이 발화한다. 부트 완료 = master·CSO·워커·리뷰어2
# (5노드)가 화면에 뜨는 것. 종전엔 "각성한 마스터가 cys boot 실행"이 산문 계약이라 LLM이 건너뛰면
# (부서장 단독 대기 환각) 팀이 안 떴다 — 그 호출 자체를 코드 결정론(이 훅)으로 격상한다.
#
# 메커니즘: UserPromptSubmit은 프롬프트 제출 시 하네스가 강제 실행하는 훅이다(모델 우회 불가).
# 마스터 선언 감지 시 javis_bootstrap.py(preflight[비치명]→master 등록→cys boot 팀 기동→생존확인)를
# 백그라운드로 발화한다. env 상속 → 부서 pane이면 CYS_SOCKET=부서소켓으로 그 부서 데몬 대상.
#
# ★2회 성찰(적대검증+30년차 아키텍트) 반영:
#  - role-aware 게이트: 워커·CSO·리뷰어 pane에서 "너는 마스터다"(인용·과제문 포함)를 받아도 마스터
#    부트를 오발화하지 않는다(role-blind 결합 결함 수리·arch#1). 미claim(빈)·master pane만 발화.
#  - 감지 정밀화: 토큰 사이 filler 허용("너는 이제 마스터다")·너가 추가·로/명령형 어미·인용/의문
#    오발화 억제·부정 범위 축소(adv#2/7/8).
#  - 쿨다운: 소켓별 + 진행 pid 기반(실패한 부트가 재시도를 60초 막던 결함 수리·adv#3/9).
#  - 출력: hookSpecificOutput.additionalContext JSON(팩 javis_memory_inject.py 관례·adv#6).
#  - 발화 폴백: setsid→nohup→& (adv#12).
#
# 안전: 모든 단계 graceful, 반드시 exit 0 (훅 실패가 세션을 깨지 않게).
set +e

INPUT=$(cat 2>/dev/null)
[ -z "$INPUT" ] && exit 0
CYS_PY="$(command -v python3 || command -v python || command -v py || echo python3)"

# 프롬프트 추출(JSON stdin의 prompt 필드)
PROMPT=$(printf '%s' "$INPUT" | "$CYS_PY" -c "import json,sys
try: print(json.load(sys.stdin).get('prompt',''))
except Exception: print('')" 2>/dev/null)
[ -z "$PROMPT" ] && exit 0

# ── role-aware 게이트(arch#1): 이 pane의 데몬 권위 역할이 비-마스터면 오발화 금지 ──
# 워커/CSO/리뷰어 pane이 "너는 마스터다"를 포함한 프롬프트(위임 과제·인용·이 성찰문 자체)를 받아도
# 마스터 부트를 발화하면 안 된다. cys surface-role은 CYS_SURFACE_ID로 자기 surface 역할을 반환(미claim=빈).
MYROLE="$(cys surface-role 2>/dev/null | head -1 | tr -d '[:space:]')"
case "$MYROLE" in
  worker|cso|reviewer-*|reviewer) exit 0 ;;   # 비-마스터 pane — 마스터 부트 금지
esac

# ── 마스터 선언 감지 ──
# 첫 200자만 검사(선언은 프롬프트 앞머리·긴 문서 본문 오발화 억제). trim.
HEAD="$(printf '%s' "$PROMPT" | tr '\n' ' ' | cut -c1-200)"
# 의문/인용 오발화 억제(adv#8): "'너는 마스터다'가 무슨 뜻?" 류.
echo "$HEAD" | grep -Eq '(무슨|무엇|뜻|의미|가 뭐|가 무|\?|라고 (말|하지|입력)|처럼|예시|예를)' && exit 0
# 선언 감지: 너는/넌/너가/당신은/너 + (filler 최대 12자) + 마스터/master + 종결(다/야/이다/입니다/임/
# 이야/로 각성/로 승격/가 되/가 돼/가 된다). you are ... master(영문). 부정은 선언 인접만 억제(adv#7).
FIRE=0
if echo "$HEAD" | grep -Eiq '(너는|넌|너가|당신은|너).{0,15}(마스터|master).{0,2}(다|야|이다|입니다|임|이야|여|로 *각성|로 *승격|가 *되|가 *돼|가 *된)'; then FIRE=1; fi
if echo "$HEAD" | grep -Eiq 'you[[:space:]]+are[[:space:]]+(the[[:space:]]+|our[[:space:]]+|now[[:space:]]+)*master'; then FIRE=1; fi
# 부정 인접 억제: "너는 마스터가 아니다/말고" (선언 자리 자체가 부정).
echo "$HEAD" | grep -Eq '(마스터|master)[^가-힣A-Za-z]{0,3}(가|는|를)?[^가-힣A-Za-z]{0,3}(아니|아냐|말고)' && FIRE=0
[ "$FIRE" = 1 ] || exit 0

PACK="${CYS_PACK_DIR:-$HOME/.cys/pack}"
BOOT="$PACK/bin/javis_bootstrap.py"
[ -f "$BOOT" ] || exit 0

# ── 소켓별 진행-가드(adv#3/9): 살아있는 부트 pid가 있으면 skip. 실패로 죽은 pid는 재시도 허용 ──
STATE="$HOME/.cys/state"; mkdir -p "$STATE" 2>/dev/null
SOCK_KEY="$(basename "${CYS_SOCKET:-base}" 2>/dev/null)"; [ -z "$SOCK_KEY" ] && SOCK_KEY="base"
PIDF="$STATE/.role-bootstrap-firing.$SOCK_KEY"
if [ -f "$PIDF" ]; then
  OLDPID="$(cat "$PIDF" 2>/dev/null)"
  if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[결정론 부트스트랩] 이 데몬의 부트가 이미 진행 중입니다 — 중복 실행하지 않습니다. cys list로 팀 기동을 확인하세요."}}'
    exit 0
  fi
fi

# 결정론 부트스트랩 백그라운드 발화(env 상속). 부모(claude) 종료와 무관하게 완주.
LOG="$STATE/role-bootstrap.log"
if command -v setsid >/dev/null 2>&1; then
  setsid "$CYS_PY" "$BOOT" >"$LOG" 2>&1 &
  FPID=$!
elif command -v nohup >/dev/null 2>&1; then
  nohup "$CYS_PY" "$BOOT" >"$LOG" 2>&1 &
  FPID=$!
else
  "$CYS_PY" "$BOOT" >"$LOG" 2>&1 &
  FPID=$!
  disown 2>/dev/null
fi
printf '%s' "$FPID" > "$PIDF" 2>/dev/null

# LLM 컨텍스트 주입(hookSpecificOutput.additionalContext JSON — 팩 관례) — 재실행/환각 차단.
"$CYS_PY" -c 'import json,sys
note=("[결정론 부트스트랩 발화됨 — 하네스 강제] \"너는 마스터다\" 선언을 UserPromptSubmit 훅이 감지해 "
      "javis_bootstrap.py를 백그라운드로 실행 중이다: preflight(비치명) → master 역할 등록 → cys boot"
      "(CSO·워커·리뷰어2 팀 기동) → 생존확인(최대 120s). 완료 = master·cso·worker·reviewer×2 (5노드)가 "
      "화면에 뜨는 것. 지침: 너(LLM)는 이 부트스트랩을 재실행하지 마라(훅이 이미 결정론 집행 중). "
      "\"부서장은 단독 대기\" 같은 규칙은 존재하지 않는다(환각 금지) — 모든 마스터는 팀을 갖는다. "
      "cys list로 팀 기동을 확인하고, 완료되면 오너 지시를 받아 지휘하라. 만약 팀이 안 뜨면 원인이 "
      "~/.cys/state/role-bootstrap.log·boot-last.json에 있고 실패 시 승인 Feed에 알림이 뜬다.")
print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":note}}, ensure_ascii=False))'
exit 0
