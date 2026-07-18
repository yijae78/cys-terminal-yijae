#!/usr/bin/env bash
# test_negative_gate.sh — 음성(negative) 게이트 E2E.
# 결함 fixture에서 verify가 exit 5(FAIL), 정상 fixture에서 exit 0(PASS),
# evidence 번들 4파일(screenshot.png·snapshot.txt·dom.html·meta.json) 실재를 assert.
#
# browserd는 headless로 기동(창 포커스 훔침 방지). 실제 Chrome 채널 우선, 폴백 chromium.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
PACK="$(cd "$HERE/../.." && pwd)"
CLI="$PACK/bin/javis_browser.py"
FIX="$HERE/fixtures"
export CYS_BROWSER_HEADLESS=1
export CYS_ROLE="worker-test"

WORK="$(mktemp -d)"
EVID="$WORK/evidence"
FAILED=0

log(){ printf '\n=== %s ===\n' "$1"; }
fail(){ printf 'ASSERT FAIL: %s\n' "$1"; FAILED=1; }

cleanup(){
  python3 "$CLI" stop >/dev/null 2>&1 || true
  [ -n "${HTTP_PID:-}" ] && kill "$HTTP_PID" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

# --- fixture 서빙 ---
log "python http.server 기동"
# 빈 포트를 결정론으로 선점 후 명시 기동 (stderr 로그 파싱 의존 제거)
PORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"
( cd "$FIX" && exec python3 -m http.server "$PORT" --bind 127.0.0.1 ) >"$WORK/http.log" 2>&1 &
HTTP_PID=$!
# 서버가 실제 응답할 때까지 대기
BROKEN_URL="http://127.0.0.1:$PORT/broken.html"
OK_URL="http://127.0.0.1:$PORT/ok.html"
READY=0
for _ in $(seq 1 50); do
  if python3 -c "import urllib.request,sys;urllib.request.urlopen('$OK_URL',timeout=1)" 2>/dev/null; then READY=1; break; fi
  sleep 0.1
done
if [ "$READY" -ne 1 ]; then echo "http.server 응답 실패 (port $PORT)"; cat "$WORK/http.log"; exit 1; fi
echo "serving on port $PORT"

# --- doctor ---
log "doctor"
python3 "$CLI" doctor
DOC=$?
[ "$DOC" -eq 0 ] || fail "doctor exit $DOC (기대 0)"

# --- 결함 페이지: verify FAIL(exit 5) 기대 ---
log "결함 페이지 open + verify (기대 exit 5)"
python3 "$CLI" --headless open "$BROKEN_URL" >/dev/null
python3 "$CLI" --headless verify --expect-text "PAYMENT CONFIRMED"
RC_BROKEN=$?
echo "broken verify exit=$RC_BROKEN"
[ "$RC_BROKEN" -eq 5 ] || fail "결함 페이지 verify exit=$RC_BROKEN (기대 5=FAIL)"

# --- 정상 페이지: verify PASS(exit 0) + evidence 번들 ---
log "정상 페이지 open + verify --evidence-dir (기대 exit 0 + 4파일)"
python3 "$CLI" --headless open "$OK_URL" >/dev/null
python3 "$CLI" --headless verify --expect-text "PAYMENT CONFIRMED" --evidence-dir "$EVID"
RC_OK=$?
echo "ok verify exit=$RC_OK"
[ "$RC_OK" -eq 0 ] || fail "정상 페이지 verify exit=$RC_OK (기대 0=PASS)"

log "evidence 번들 4파일 실재 assert"
for f in screenshot.png snapshot.txt dom.html meta.json; do
  if [ -s "$EVID/$f" ]; then echo "  [OK] $f ($(wc -c <"$EVID/$f" | tr -d ' ') bytes)"; else fail "evidence 파일 없음/빈: $f"; fi
done

# meta.json 완결 마커 + dom_sha256 독립 재계산 대조
if [ -s "$EVID/meta.json" ] && [ -s "$EVID/dom.html" ]; then
  META_HASH="$(python3 -c "import json,sys;print(json.load(open('$EVID/meta.json'))['dom_sha256'])")"
  CALC_HASH="$(python3 -c "import hashlib;print(hashlib.sha256(open('$EVID/dom.html','rb').read()).hexdigest())")"
  if [ "$META_HASH" = "$CALC_HASH" ]; then echo "  [OK] dom_sha256 독립 재계산 일치"; else fail "dom_sha256 불일치 meta=$META_HASH calc=$CALC_HASH"; fi
fi

# --- 비신뢰 라벨 확인 (snapshot 헤더) ---
log "snapshot 비신뢰 라벨 확인"
if grep -q "UNTRUSTED WEB CONTENT" "$EVID/snapshot.txt"; then echo "  [OK] 비신뢰 헤더 존재"; else fail "snapshot에 비신뢰 라벨 없음"; fi

# --- 감사로그 기록 확인 ---
log "audit.jsonl 기록 확인"
AUDIT="$HOME/.cys/browser/audit.jsonl"
if [ -s "$AUDIT" ] && grep -q '"verb": "verify"' "$AUDIT"; then echo "  [OK] audit에 verify 기록"; else fail "audit.jsonl에 verify 기록 없음"; fi

log "결과"
if [ "$FAILED" -eq 0 ]; then echo "ALL ASSERTS PASSED (음성 게이트 통과)"; exit 0; else echo "SOME ASSERTS FAILED"; exit 1; fi
