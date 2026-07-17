#!/bin/bash
# ★W-C1 pack-guard(커스텀 생존 설계 2026-07-17) — PostToolUse(Write|Edit|MultiEdit):
#   vendor(system·임베드) 팩 파일 수정 감지 → "다음 부트 치유" 예고 + 정식 영속 경로 안내.
# 채널: additionalContext(모델 주입) — commit-memory-nudge.sh 와 동일한 검증된 패턴.
# 경계: 오너 Rejected "오버레이 BLOCK 게이트(자기발화 봉쇄)" 준수 — 어떤 실패에도 exit 0(비차단).
# 판정 SOT: `cys pack-ownership --quiet`(임베드 여부 포함 effective 등급) — sh 재구현 금지(SOT 분산 차단).
# 코얼레싱: 세션·파일당 1회만 경고(경고 피로 → 무시 학습 방지).
set +e

INPUT=$(cat 2>/dev/null)
FP=$(printf '%s' "$INPUT" | python3 -c "import json,sys
try:
  ti = json.load(sys.stdin).get('tool_input', {})
  print(ti.get('file_path', '') or ti.get('path', ''))
except Exception:
  print('')" 2>/dev/null)
[ -z "$FP" ] && exit 0

PACK="${CYS_PACK_DIR:-$HOME/.cys/pack}"
case "$FP" in
  "$PACK"/*) ;;
  *) exit 0 ;;
esac
REL="${FP#"$PACK"/}"

# 세션·파일당 1회 코얼레싱 스탬프.
SID=$(printf '%s' "$INPUT" | python3 -c "import json,sys
try: print(json.load(sys.stdin).get('session_id', 'nosession'))
except Exception: print('nosession')" 2>/dev/null)
STAMP_DIR="${TMPDIR:-/tmp}/cys-pack-guard"
mkdir -p "$STAMP_DIR" 2>/dev/null
KEY=$(printf '%s' "$REL" | tr '/. ' '___')
STAMP="$STAMP_DIR/${SID:-nosession}-${KEY}"
[ -e "$STAMP" ] && exit 0

# effective 등급 판정(임베드 vendor system 만 경고 대상 — 자작 신규 파일 'custom' 은 불가침이라 침묵).
OWN=$(cys pack-ownership --quiet "$REL" 2>/dev/null)
[ "$OWN" = "system" ] || exit 0
: > "$STAMP" 2>/dev/null

MSG="[pack-guard] '$REL' 은 vendor(system) 파일 — 이 수정은 다음 부트 설치 스윕에 vendor 본으로 치유됩니다(수정본은 $REL.user 로 보존·병합 원장 기록). 영속 경로: ① 자작 기능은 새 파일로(비임베드=업데이트 불가침) ② 스킬 커스텀은 ~/.cys/local/skills(shadowing, cys pack-merge --to-local) ③ vendor 개선 제안은 cys pack-merge --file $REL --propose. (WARN — 차단 아님·개발 기계의 upstream 승격 작업이면 무시)"

printf '%s' "$MSG" | python3 -c "import json,sys
print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse','additionalContext':sys.stdin.read()}}, ensure_ascii=False))" 2>/dev/null
exit 0
