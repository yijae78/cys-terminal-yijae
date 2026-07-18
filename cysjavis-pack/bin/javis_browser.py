#!/usr/bin/env python3
"""javis_browser.py — browserd 배선 CLI (P1 · 팩 인큐베이션).

설계: _research/cmux-distillation/DESIGN-v1.2-2026-07-19.md §2B.
- browserd(bun+playwright-core)에 127.0.0.1 HTTP로 동사를 중계한다.
- browserd 미기동 시 자동 기동(백그라운드 spawn + state 대기, 타임아웃 20s).
- 모든 동사를 ~/.cys/browser/audit.jsonl 에 append (reviewer2 감사 대상).
- P1은 cys 데몬·제품 코드 무변경. 제품 `cys browser` 승격은 제품화 게이트 이후.

결정론 exit 코드:
  0 성공 · 2 BUSY · 3 APPROVAL_REQUIRED · 4 기동실패 · 5 verify FAIL · 6 HUMAN_ACTIVE · 1 기타

stdlib only (오피스 브리지 계보).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BROWSER_ROOT = Path.home() / ".cys" / "browser"
STATE_PATH = BROWSER_ROOT / "state.json"
AUDIT_PATH = BROWSER_ROOT / "audit.jsonl"
BROWSERD_DIR = Path(__file__).resolve().parent.parent / "browserd"
SERVER_TS = BROWSERD_DIR / "server.ts"

# 에러 코드 → exit 코드 매핑
EXIT_BY_ERROR = {
    "BUSY": 2,
    "APPROVAL_REQUIRED": 3,
    "HUMAN_ACTIVE": 6,
}
EXIT_OK = 0
EXIT_OTHER = 1
EXIT_START_FAIL = 4
EXIT_VERIFY_FAIL = 5


def _pid_alive(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _read_state():
    if not STATE_PATH.exists():
        return None
    try:
        st = json.loads(STATE_PATH.read_text())
        if all(k in st for k in ("pid", "port", "token")):
            return st
        return None
    except Exception:
        return None


def _live_state():
    st = _read_state()
    if st and _pid_alive(st["pid"]):
        return st
    return None


def _which(name: str):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(d) / name
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    # bun 기본 설치 경로 폴백
    fallback = Path.home() / ".bun" / "bin" / name
    if fallback.exists():
        return str(fallback)
    return None


def _chrome_available() -> bool:
    mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac.exists():
        return True
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if _which(n):
            return True
    return False


def start_browserd(headless: bool, timeout: float = 20.0):
    """browserd를 백그라운드 spawn하고 live state가 뜰 때까지 대기."""
    bun = _which("bun")
    if not bun:
        return None, "bun 미설치 — https://bun.sh"
    if not SERVER_TS.exists():
        return None, f"server.ts 없음: {SERVER_TS}"
    BROWSER_ROOT.mkdir(parents=True, exist_ok=True)
    args = [bun, "run", str(SERVER_TS)]
    if headless:
        args.append("--headless")
    env = dict(os.environ)
    if headless:
        env["CYS_BROWSER_HEADLESS"] = "1"
    logf = open(BROWSER_ROOT / "browserd.log", "ab")
    # 부모와 분리 (detached), stdout/stderr 로그로
    subprocess.Popen(
        args,
        cwd=str(BROWSERD_DIR),
        stdout=logf,
        stderr=logf,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = _live_state()
        if st:
            return st, None
        time.sleep(0.3)
    # 실패 시 로그 tail 반환
    try:
        tail = (BROWSER_ROOT / "browserd.log").read_text()[-2000:]
    except Exception:
        tail = ""
    return None, f"browserd 기동 타임아웃({timeout}s)\n{tail}"


def ensure_browserd(headless: bool):
    st = _live_state()
    if st:
        return st, None
    return start_browserd(headless)


def rpc(st, verb: str, args: dict):
    url = f"http://127.0.0.1:{st['port']}/{st['token']}/rpc"
    data = json.dumps({"verb": verb, "args": args}).encode("utf8")
    req = urllib.request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf8"))


def audit(verb: str, args: dict, evidence_path, exit_code: int):
    try:
        BROWSER_ROOT.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "caller_role": os.environ.get("CYS_ROLE", "unknown"),
            "verb": verb,
            "url": args.get("url"),
            "profile": args.get("profile", "agent"),
            "evidence_path": evidence_path,
            "exit": exit_code,
        }
        with open(AUDIT_PATH, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# --- doctor ---
def cmd_doctor(a) -> int:
    checks = []

    bun = _which("bun")
    checks.append(("bun 실행파일", bool(bun), bun or "미설치"))

    node_modules = BROWSERD_DIR / "node_modules" / "playwright-core"
    dep_ok = node_modules.exists()
    checks.append(("playwright-core 설치", dep_ok, str(node_modules) if dep_ok else "미설치 — `bun install` 필요"))

    lock = (BROWSERD_DIR / "bun.lock").exists() or (BROWSERD_DIR / "bun.lockb").exists()
    checks.append(("lockfile 존재", lock, "bun.lock" if lock else "없음"))

    chrome = _chrome_available()
    checks.append(("Chrome/chromium 가용", chrome, "found" if chrome else "미설치 (channel 폴백 시 `bunx playwright install chromium`)"))

    server_ok = SERVER_TS.exists()
    checks.append(("server.ts 존재", server_ok, str(SERVER_TS)))

    # state 정합
    st = _read_state()
    if st is None:
        checks.append(("state 파일", True, "없음(정상 — lazy)"))
    else:
        alive = _pid_alive(st["pid"])
        checks.append(("state 정합(pid 생존)", alive, f"pid={st['pid']} port={st['port']} {'live' if alive else 'stale(교체됨)'}"))

    ok = all(c[1] for c in checks[:5])  # 핵심 5항목 (state 스테일은 비치명)
    print("browserd doctor:")
    for name, good, detail in checks:
        print(f"  [{'OK' if good else 'FAIL'}] {name}: {detail}")
    print(f"\n결과: {'PASS (exit 0)' if ok else 'FAIL (exit 1)'}")
    return EXIT_OK if ok else EXIT_OTHER


# --- 동사 실행 공통 ---
def run_verb(verb: str, args: dict, headless: bool) -> int:
    st, err = ensure_browserd(headless)
    if not st:
        audit(verb, args, None, EXIT_START_FAIL)
        _emit({"ok": False, "error": {"code": "START_FAIL", "message": err}})
        return EXIT_START_FAIL
    try:
        resp = rpc(st, verb, args)
    except urllib.error.URLError as e:
        audit(verb, args, None, EXIT_OTHER)
        _emit({"ok": False, "error": {"code": "RPC_FAIL", "message": str(e)}})
        return EXIT_OTHER

    if not resp.get("ok"):
        code = resp.get("error", {}).get("code", "ERROR")
        exit_code = EXIT_BY_ERROR.get(code, EXIT_OTHER)
        audit(verb, args, None, exit_code)
        _emit(resp)
        return exit_code

    result = resp.get("result", {})
    evidence_path = result.get("evidence_path")

    # verify FAIL → exit 5
    if verb == "verify" and result.get("verdict") == "FAIL":
        audit(verb, args, evidence_path, EXIT_VERIFY_FAIL)
        _emit(resp)
        return EXIT_VERIFY_FAIL

    audit(verb, args, evidence_path, EXIT_OK)
    _emit(resp)
    return EXIT_OK


def build_args(a) -> dict:
    """argparse 네임스페이스 → RPC args (None 제거)."""
    keys = [
        "url", "profile", "context", "ref", "selector", "value", "text", "key",
        "expression", "path", "timeout", "load", "expect_text", "expect_selector",
        "action", "actor", "evidence_dir", "full_page",
    ]
    out = {}
    for k in keys:
        v = getattr(a, k, None)
        if v is not None:
            out[k] = v
    return out


def main():
    p = argparse.ArgumentParser(prog="javis_browser", description="browserd 배선 CLI (P1)")
    p.add_argument("--headless", action="store_true", help="browserd를 headless로 기동")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="설치·경로·버전 결정론 점검")
    sub.add_parser("start", help="browserd 기동")
    sub.add_parser("stop", help="browserd 종료")
    sub.add_parser("status", help="browserd 상태")

    def add_common(sp):
        sp.add_argument("--context", default=None)
        sp.add_argument("--evidence-dir", dest="evidence_dir", default=None)

    sp = sub.add_parser("open"); sp.add_argument("url"); sp.add_argument("--profile", default=None); add_common(sp)
    sp = sub.add_parser("snapshot"); add_common(sp)
    sp = sub.add_parser("click"); sp.add_argument("--ref"); sp.add_argument("--selector"); sp.add_argument("--timeout", type=int); add_common(sp)
    sp = sub.add_parser("fill"); sp.add_argument("--ref"); sp.add_argument("--selector"); sp.add_argument("--value", required=True); sp.add_argument("--timeout", type=int); add_common(sp)
    sp = sub.add_parser("type"); sp.add_argument("--text", required=True); sp.add_argument("--ref"); sp.add_argument("--selector"); sp.add_argument("--timeout", type=int); add_common(sp)
    sp = sub.add_parser("press"); sp.add_argument("--key", required=True); add_common(sp)
    sp = sub.add_parser("eval"); sp.add_argument("--expression", required=True); add_common(sp)
    sp = sub.add_parser("screenshot"); sp.add_argument("--path", required=True); sp.add_argument("--full-page", dest="full_page", action="store_true", default=None); add_common(sp)
    sp = sub.add_parser("wait"); sp.add_argument("--selector"); sp.add_argument("--text"); sp.add_argument("--url"); sp.add_argument("--load"); sp.add_argument("--timeout", type=int); add_common(sp)
    sp = sub.add_parser("verify"); sp.add_argument("--expect-text", dest="expect_text"); sp.add_argument("--expect-selector", dest="expect_selector"); add_common(sp)
    sp = sub.add_parser("control"); sp.add_argument("action", choices=["acquire", "release"]); sp.add_argument("--actor", choices=["agent", "human"], default=None); add_common(sp)

    a = p.parse_args()
    headless = a.headless

    if a.cmd == "doctor":
        sys.exit(cmd_doctor(a))

    if a.cmd == "start":
        st, err = ensure_browserd(headless)
        if not st:
            _emit({"ok": False, "error": {"code": "START_FAIL", "message": err}})
            sys.exit(EXIT_START_FAIL)
        _emit({"ok": True, "result": {"pid": st["pid"], "port": st["port"]}})
        sys.exit(EXIT_OK)

    if a.cmd == "stop":
        st = _live_state()
        if not st:
            _emit({"ok": True, "result": "미기동"})
            sys.exit(EXIT_OK)
        try:
            os.kill(st["pid"], 15)
        except ProcessLookupError:
            pass
        _emit({"ok": True, "result": f"SIGTERM → pid {st['pid']}"})
        sys.exit(EXIT_OK)

    args = build_args(a)
    sys.exit(run_verb(a.cmd, args, headless))


if __name__ == "__main__":
    main()
