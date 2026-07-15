#!/bin/bash
# javis 결정론 부트스트랩 발화 — UserPromptSubmit hook
#
# 절대요구(오너 2026-07-15): "너는 마스터다" 류 마스터 선언이 입력되면, LLM의 재량·환각·누락과
# 무관하게 하네스가 부트스트랩을 100% 예외없이 발화한다. 부트 완료 = master·CSO·워커·리뷰어2
# (5노드)가 화면에 뜨는 것. 종전엔 "각성한 마스터가 cys boot를 실행한다"가 산문 계약이라 LLM이
# 건너뛰면(부서장 단독 대기 환각) 팀이 안 떴다 — 그 호출 자체를 코드 결정론(이 훅)으로 격상한다.
#
# 메커니즘: UserPromptSubmit은 프롬프트 제출 시 하네스가 강제 실행하는 훅이다. 프롬프트에 마스터
# 선언이 있으면 javis_bootstrap.py(preflight→master 등록→cys boot 팀 기동→생존확인)를 백그라운드로
# 발화한다(수백초라 프롬프트 무블록). env 상속 → 부서 pane이면 CYS_SOCKET=부서소켓으로 그 부서 데몬
# 대상. 멱등: bootstrap 체인·cys boot 락이 중복을 흡수한다.
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

# 마스터 선언 감지 — 너는/넌/당신은 + 마스터/master + 종결어미. 워커/CSO/리뷰어 선언은 대상 아님
# (그들은 마스터의 cys boot가 스폰). 부정("마스터가 아니다/말고")은 제외.
echo "$PROMPT" | grep -Eiq '(너는|넌|당신은|너)[[:space:]]*(마스터|master)[[:space:]]*(다|야|이다|입니다|임|이야|이다\.|다\.)' || exit 0
echo "$PROMPT" | grep -Eq '(마스터|master)[[:space:]]*(가|는|를)?[[:space:]]*(아니|아냐|말고)' && exit 0

PACK="${CYS_PACK_DIR:-$HOME/.cys/pack}"
BOOT="$PACK/bin/javis_bootstrap.py"
[ -f "$BOOT" ] || exit 0

# 중복 발화 억제(60초 쿨다운) — 같은 선언 연타·재제출 방지. cys boot 소켓별 락이 최종 방어선.
STATE="$HOME/.cys/state"; mkdir -p "$STATE" 2>/dev/null
MARK="$STATE/.role-bootstrap-firing"
NOW=$(date +%s 2>/dev/null || echo 0)
if [ -f "$MARK" ]; then
  PREV=$(cat "$MARK" 2>/dev/null || echo 0)
  if [ "$NOW" != 0 ] && [ "$PREV" != 0 ] && [ $((NOW - PREV)) -lt 60 ]; then
    echo "[결정론 부트스트랩] 이미 발화 중(쿨다운) — 재실행 안 함. cys list로 진행 확인."
    exit 0
  fi
fi
printf '%s' "$NOW" > "$MARK" 2>/dev/null

# 결정론 부트스트랩 백그라운드 발화(env 상속). 부모(claude) 종료와 무관하게 완주(setsid/nohup).
LOG="$STATE/role-bootstrap.log"
if command -v setsid >/dev/null 2>&1; then
  setsid "$CYS_PY" "$BOOT" >"$LOG" 2>&1 &
else
  nohup "$CYS_PY" "$BOOT" >"$LOG" 2>&1 &
fi

# LLM 컨텍스트 주입 — 재실행(중복)·환각 차단.
cat <<'NOTE'
[결정론 부트스트랩 발화됨 — 하네스 강제] "너는 마스터다" 선언을 UserPromptSubmit 훅이 감지해
javis_bootstrap.py를 백그라운드로 실행 중이다: preflight → master 역할 등록 → cys boot(CSO·워커·
리뷰어2 팀 기동) → 생존확인. 부트 완료 = master·cso·worker·reviewer×2 (5노드)가 화면에 뜨는 것.
지침: 너(LLM)는 이 부트스트랩을 재실행하지 마라(훅이 이미 결정론 집행 중·중복 방지). "부서장은
단독 대기" 같은 규칙은 존재하지 않는다(환각 금지) — 모든 마스터는 팀을 갖는다. `cys list`로 팀
5노드 기동을 확인하고, 완료되면 오너 지시를 받아 지휘하라. 부트 로그: ~/.cys/state/role-bootstrap.log
NOTE
exit 0
