#!/usr/bin/env python3
"""javis_bootstrap.py — master 부트 시퀀스의 결정론 격상 (BOOTSTRAP_HARDENING WP-1).

"너는 마스터다" 이후의 기계적 절차 전부를 단일 exit-code 체인으로 수행한다.
LLM(master)의 역할은 이 스크립트 실행·출력 인용·이후 지휘뿐이다 — 산문 단계 수행 금지.

단계 체인 (실패 시 즉시 중단·단계명+원인을 stderr와 boot-last.json에 기록):
  ① preflight --fix READY        ② cys ping                ③ cys claim-role master
  ④ cys boot                     ⑤ orchestra check (bounded retry 3s×10 — 노드 스폰은
  비동기·check는 무대기 스냅샷이므로 레이스 봉쇄)          ⑥ 완료 마커 write
  ⑦ cys-dept promote-if-pending --request-only (비대기 — 부트와 승격 동의의 분리)
  ⑧ 기계 요약 JSON 출력 (master는 이것을 인용해 보고한다)

완료 마커 ~/.cys/.master-bootstrapped 는 base 데몬 전용 단일-writer 마커다:
  - writer = 이 스크립트의 성공 경로(⑤ exit 0 후 ⑥) 유일. 삭제 주체 없음(버전 필드로 stale 판정).
  - ★소켓 격리: CYS_SOCKET이 base가 아니면(부서 pane 부트) write하지 않는다 — 부서장 부트가
    base 마커를 오염시키면 CEO 승격 게이트(cys-dept)가 오개방된다.

exit: 0=부트 완료 / 2=preflight / 3=ping / 7=claim 거부(이 surface는 master 아님 — 지휘 중단·인계)
      4=boot / 6=check 최종 실패 / 5=assert-ready 게이트 실패(하위 게이트 전용)
      8=레인↔팩 정합 실패(부서 소켓↔부서 팩 교차 오염 차단 — 팀 기동 전 중단)
안전밸브: CYS_BOOT_GATE=warn(assert-ready 실패를 경고로 강등)|off(게이트 무력).
"""
import json
import os
import subprocess
import sys
import tempfile
import time

# ★R3(D-IMPL-3): Windows 파이프 환경(cp949/cp1252)에서 한글 출력 UnicodeEncodeError 크래시 방어 —
# PYTHONUTF8 export는 cys-dept 경로에만 있어 이 스크립트의 직접 실행을 보호하지 못한다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HOME = os.path.expanduser("~")
CYS_DIR = os.path.join(HOME, ".cys")
PACK = os.environ.get("CYS_PACK_DIR") or os.path.join(CYS_DIR, "pack")
MARKER = os.path.join(CYS_DIR, ".master-bootstrapped")
STATE_DIR = os.path.join(CYS_DIR, "state")
BOOT_LAST = os.path.join(STATE_DIR, "boot-last.json")
# ⑤ bounded retry — 무한 대기 금지(자원 거버넌스). env 오버라이드는 테스트 하네스 전용.
# ★예산 확대(오너 2026-07-15 적대검증 adv#4): 냉시작 claude는 모델 로드+MCP init로 30초 내
# agent_alive/set-status ack가 안 나 check가 조기 실패(팀은 아직 뜨는 중)했다. 노드 기동은 비동기라
# 넉넉히 기다린다 — 24×5s ≈ 120초 상한(무한 아님·자원 거버넌스 유지).
CHECK_RETRIES = max(1, int(os.environ.get("CYS_BOOT_CHECK_RETRIES", "24")))
CHECK_INTERVAL_S = float(os.environ.get("CYS_BOOT_CHECK_INTERVAL_S", "5"))  # 총 상한 ≈ 120초


def _atomic_write_json(path, obj):
    """CRLF 함정 회피(newline='\\n')·원자 교체 — Windows 재직렬화 원복 교훈."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-boot-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _progress(msg):
    """★R12: 단계 시작 신호(stderr 1줄) — 진행 중 무출력이면 최악 수 분의 침묵 창이 생겨
    관찰자(초보·master)가 '멈춤'으로 오인한다(실사고 증상②의 형태적 재생산 방지).
    기계 계약(exit code·⑧ JSON)과 별개의 인간 관찰자용 인터페이스."""
    sys.stderr.write("[bootstrap] %s\n" % msg)
    try:
        sys.stderr.flush()
    except Exception:
        pass


def _run(cmd, timeout=120):
    """서브프로세스 실행 — (exit, stdout+stderr 병합 텍스트). shell 미사용(경로 quoting 안전)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except FileNotFoundError:
        return 127, "명령 없음: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return 124, "timeout(%ss): %s" % (timeout, " ".join(cmd))


def _socket_is_base(sock):
    """순수 판정: 소켓 경로 문자열 → base 여부(§4.1 소켓 격리). CYS_SOCKET 미설정('')=base.
    ★경로 기반(basename 아님): 부서 소켓 ~/.local/state/cys-dept-<name>/cys.sock 은 basename이
    본부와 동일한 'cys.sock'이라 basename 판정이 부서를 base로 오판했다(마커 오염·ceo_promote 오개방).
    경로 성분에 'cys-dept-' 프리픽스 디렉토리가 있으면 부서 레인(비-base), 없으면 base.
    Windows named pipe(백슬래시.백슬래시 pipe 형식)는 성분 분해가 부적합하므로 기존 basename 동작을 보존한다."""
    sock = (sock or "").strip()
    if not sock:
        return True
    norm = sock.replace("\\", "/")
    if sock.startswith("\\\\") or norm.lower().startswith("//./pipe/"):  # win named pipe — 기존 동작 보존
        return os.path.basename(norm) in ("cys", "cys.sock")
    for part in norm.split("/"):
        if part.startswith("cys-dept-"):
            return False
    return True


def _is_base_socket():
    """CYS_SOCKET env 래퍼(호출부 하위호환)."""
    return _socket_is_base(os.environ.get("CYS_SOCKET", ""))


def _sanitize_sock_key(sock):
    """소켓 전체 경로 → 파일명 안전 락 키(레인마다 유일). 부서 소켓은 basename(cys.sock)이 동일해
    basename 키를 쓰면 모든 레인이 같은 락 파일을 공유했다 — 전체 경로 새니타이즈로 레인 유일화.
    경로 구분자(os.sep·'/'·'\\')·':'를 '_'로 치환. 파일명 길이 상한(255) 여유 — 과길면 앞부분+경로
    해시로 유일성 보존(절단만 하면 서로 다른 긴 경로가 같은 키로 충돌)."""
    raw = (sock or "").strip() or "base"
    for ch in (os.sep, "/", "\\", ":"):
        raw = raw.replace(ch, "_")
    raw = raw.strip("_") or "base"
    if len(raw) > 160:
        import hashlib
        raw = raw[:120] + "-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return raw


def _socket_dept(sock=None):
    """순수 판정: 소켓 경로 → 부서명(cys-dept-<name> 성분) 또는 None(base). _socket_is_base와 정합
    (base ⟺ dept None). 기본값은 CYS_SOCKET env."""
    sock = os.environ.get("CYS_SOCKET", "") if sock is None else sock
    sock = (sock or "").strip()
    if not sock:
        return None
    for part in sock.replace("\\", "/").split("/"):
        if part.startswith("cys-dept-"):
            return part[len("cys-dept-"):] or None
    return None


def _pack_dept(pack=None):
    """순수 판정: 팩 경로 마지막 성분 pack-dept-<name> → name, 아니면 None(메인 팩). 기본값은 PACK."""
    pack = PACK if pack is None else pack
    base = os.path.basename((pack or "").replace("\\", "/").rstrip("/"))
    if base.startswith("pack-dept-"):
        return base[len("pack-dept-"):] or None
    return None


def _lane_pack_mismatch(sock=None, pack=None):
    """레인(소켓 부서)↔팩(부서 팩) 정합 판정. 정합이면 None, 불일치면 (sock_dept, pack_dept).
    교차 오염(UT-14): dept-X 레인이 메인/다른 부서 팩을 쓰거나 base 레인이 부서 팩을 쓰면 위험."""
    sd = _socket_dept(sock)
    pd = _pack_dept(pack)
    return None if sd == pd else (sd, pd)


def _notify_loud(title, body):
    """실패를 시끄럽게 알림 — feed push(승인 채널) 우선, 실패 시 cys send --queued --to master 폴백.
    둘 다 best-effort·짧은 timeout(데몬 부재 시 행 금지·graceful). 성공 채널명 또는 'none' 반환(흔적)."""
    for name, cmd in (
        ("feed", ["cys", "feed", "push", "--kind", "bootstrap-fail", "--title", title, "--body", body]),
        ("send", ["cys", "send", "--queued", "--to", "master", "[부트 중단] %s — %s" % (title, body)]),
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=10)
            if r.returncode == 0:
                return name
        except Exception:
            continue
    return "none(데몬 부재 등 — 비제로 exit·boot-last.json이 최종 증거)"


def _pack_version():
    v = None
    for cand in (os.path.join(CYS_DIR, ".pack-version"), os.path.join(PACK, ".pack-version")):
        try:
            with open(cand, encoding="utf-8") as f:
                v = f.read().strip() or None
            if v:
                break
        except OSError:
            continue
    return v or "unknown"


def _binary_version():
    code, out = _run(["cys", "--version"], timeout=10)
    return out.strip().splitlines()[0] if code == 0 and out.strip() else "unknown"


class _Log:
    """단계 결과를 boot-last.json에 누적(진단 가시성 — 각 retry 시도 포함)."""

    def __init__(self):
        self.data = {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": [],
                     "socket": os.environ.get("CYS_SOCKET", ""), "base_socket": _is_base_socket()}

    def step(self, name, code, detail=""):
        self.data["steps"].append({"step": name, "exit": code,
                                   "detail": detail.strip()[-2000:]})
        _atomic_write_json(BOOT_LAST, self.data)

    def fail(self, name, code, detail, exit_code):
        self.step(name, code, detail)
        self.data["result"] = {"ok": False, "failed_step": name, "exit": exit_code}
        _atomic_write_json(BOOT_LAST, self.data)
        sys.stderr.write("[bootstrap] 단계 실패: %s (exit %d)\n%s\n" % (name, code, detail.strip()))
        # ★실패 가시화(오너 2026-07-15 적대검증 adv#5): 훅이 배경 실행이라 stderr가 화면에 안 보인다.
        # 훅 NOTE는 "팀이 뜬다"고 알렸는데 부트가 조용히 실패하면 사용자는 원인을 모른다 — feed 알림으로
        # 승격(best-effort·데몬 다운 등 실패 무해). ②ping 실패(데몬 자체 부재)는 feed도 불가라 skip.
        if name != "②ping":
            hint = {"③claim-role": "다른 pane이 이미 master입니다 — 기존 master 탭을 쓰세요(조직당 master 1명).",
                    "④boot": "팀(CSO·워커·리뷰어) 기동 실패 — claude CLI 설치를 확인하세요.",
                    "⑤check": "팀 노드가 제 시간에 안 떴습니다 — cys list로 확인하고 필요시 재선언하세요."
                    }.get(name, "부트스트랩이 %s 단계에서 실패했습니다 — cys list·boot-last.json 확인." % name)
            try:
                subprocess.run(["cys", "feed", "push", "--kind", "bootstrap-fail",
                                "--title", "부트스트랩 미완(%s)" % name, "--body", hint],
                               capture_output=True, timeout=10)
            except Exception:
                pass
        return exit_code


def _acquire_singleflight():
    """부트스트랩 전체 단일 실행 락(오너 2026-07-15 적대검증·아키텍트: preflight 300s는 boot 락으로
    직렬화되지 않아 중복 fire가 settings.json read-modify-write를 경쟁하고 300s 프리플라이트를 중복
    실행했다). 소켓별 flock 비차단 — 이미 진행 중이면 None 반환(호출부가 no-op 종료). unix 전용
    실효(windows는 항상 락 획득=직렬화 없음, boot 락이 최종 방어). 반환 fd를 프로세스 수명동안 보유."""
    sock = os.environ.get("CYS_SOCKET", "base")
    key = _sanitize_sock_key(sock)  # ★전체 경로 새니타이즈 — 부서 소켓 basename 동일 충돌 방지(레인 유일화)
    lock_path = os.path.join(STATE_DIR, "bootstrap-%s.lock" % key)
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    except OSError:
        return True  # 락 못 열면 직렬화 없이 진행(보수적 허용)
    if os.name == "posix":
        import fcntl
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return None  # 다른 부트스트랩 진행 중 — no-op
    _acquire_singleflight._fd = fd  # GC로 fd 닫혀 락 풀리지 않게 프로세스 수명동안 보유
    return True


def cmd_run():
    # ★단일 실행 게이트 — 진행 중이면 즉시 성공 반환(중복 preflight/boot 방지·pile-up 차단).
    if _acquire_singleflight() is None:
        _progress("부트스트랩 이미 진행 중(단일 실행 락) — 중복 실행 skip. 진행은 cys list로 확인.")
        return 0
    log = _Log()
    py = sys.executable or "python3"

    # ★레인↔팩 정합 가드(증분1 · UT-14 교차 오염 차단): 부서 소켓 레인은 그 부서 팩(pack-dept-X)을,
    # base 레인은 메인 팩을 써야 한다. 불일치면 잘못된 데몬/팩 조합이 마커·승격·디렉티브를 오염시키므로
    # 팀 기동(④) 전에 시끄럽게 실패한다(조용한 진행이 최악 — adv#5 실패 가시화 계열).
    mismatch = _lane_pack_mismatch()
    if mismatch is not None:
        sd, pd = mismatch
        detail = ("레인↔팩 불일치(교차 오염·UT-14): 소켓 부서=%s · 팩 부서=%s. CYS_SOCKET과 "
                  "CYS_PACK_DIR이 같은 부서를 가리켜야 한다(base↔메인팩 / dept-X↔pack-dept-X). "
                  "팀 기동 중단." % (sd or "base", pd or "메인"))
        log.step("③′lane-pack", 1, detail)
        _progress("⚠ " + detail)
        notified = _notify_loud("레인↔팩 불일치(부트 중단)", detail)
        log.step("③′lane-pack-notify", 0, "알림 채널: %s" % notified)
        log.data["result"] = {"ok": False, "failed_step": "lane-pack", "exit": 8}
        _atomic_write_json(BOOT_LAST, log.data)
        return 8

    # ★TCC 보조 경고(오너 2026-07-15): macOS 폴더 권한 리셋(서명 변경 업그레이드) 시 pane 자식이
    # EPERM으로 죽는 실사고 — 부트가 살아있는 세션에서라도 조기 경고(주 안내는 GUI perm-warning).
    if sys.platform == "darwin":
        try:
            os.listdir(os.path.join(HOME, "Desktop"))
        except PermissionError:
            _progress("⚠ macOS 데스크탑 폴더 접근 거부 — 시스템 설정→개인정보 보호 및 보안→"
                      "파일 및 폴더에서 cys 허용 후 앱 재시작(미허용 시 pane의 claude가 EPERM으로 꺼짐)")
        except OSError:
            pass

    # ① preflight --fix — ★비치명화(오너 2026-07-15 적대검증 adv#1 CRITICAL): 종전엔 preflight가
    # 완전-green(exit 0)이 아니면 여기서 abort해 ④ 팀 부팅이 영영 안 됐다. preflight는 60+ 체크
    # 표면이라 자동수리 불가 FAIL 하나(구 hook·수동 디렉티브 핀·git 부재)만 있어도 팀 0개 — "5노드
    # 100%" 요구와 정면 충돌(이 기계도 잔여 FAIL 존재). 팀 부팅의 진짜 게이트는 ⑤ check다. 따라서
    # preflight FAIL은 경고로 강등하고 ④로 계속한다. 부팅-치명 전제(데몬·claude)는 ②ping·cys boot가
    # 각자 검증하므로 preflight와 분리해도 안전. 마커가 현재 pack_version이면 300s preflight 자체를
    # 생략(재선언 fast path — pile-up·재실행 비용 제거).
    preflight = os.path.join(PACK, "bin", "javis_preflight.py")
    _marker = _read_json(MARKER) or {}
    _marker_fresh = (_is_base_socket() and _marker.get("pack_version") == _pack_version()
                     and _marker.get("pack_version") not in (None, "unknown"))
    if _marker_fresh:
        log.step("①preflight", 0, "base 마커가 현재 pack_version — preflight 생략(fast path)")
    elif os.path.isfile(preflight):
        _progress("① preflight --fix 실행 중(최대 300s · 비치명 — FAIL이어도 팀 부팅 계속)…")
        code, out = _run([py, preflight, "--fix"], timeout=300)
        log.step("①preflight", code, out)
        if code != 0:
            _progress("⚠ preflight 잔여 FAIL(비치명) — 팀 부팅 계속·진짜 게이트는 ⑤ check. 상세 boot-last.json")
    else:
        log.step("①preflight", 0, "preflight 부재 — 생략(팩 불완전 가능·계속)")

    # ② 데몬 생존 — 이후 ③의 비정상 exit를 '거부'로 해석하는 전제(데몬 생존 보증)
    _progress("② 데몬 생존 확인…")
    code, out = _run(["cys", "ping"], timeout=15)
    log.step("②ping", code, out)
    if code != 0:
        return log.fail("②ping", code, out, 3)

    # ③ claim-role master — 거부=exit 7(유령 master 차단: 이 surface는 master가 아니다)
    _progress("③ master 역할 등록…")
    code, out = _run(["cys", "claim-role", "master"], timeout=15)
    log.step("③claim-role", code, out)
    if code != 0:
        msg = ("이 surface는 master가 아님(claim 거부). 살아있는 master가 레지스트리에 존재한다 — "
               "선언을 중단하고 기존 master에 인계하라.\n%s" % out)
        return log.fail("③claim-role", code, msg, 7)

    # ④ 4종 의무 노드 기동
    _progress("④ 4종 의무 노드 기동 중(최대 300s)…")
    code, out = _run(["cys", "boot"], timeout=300)
    log.step("④boot", code, out)
    if code != 0:
        return log.fail("④boot", code, out, 4)

    orchestra = os.path.join(PACK, "bin", "javis_orchestra.py")

    # ④-b 리뷰어 감지·무구독 폴백(R1·D-IMPL-1 — 산문 §0 ④-b의 코드 전사): cys boot는 미설치
    # CLI를 건너뛰므로 agy/codex 부재 기계(초보 전원)에서 대체 리뷰어(reviewer-claude-*)를 기동할
    # 주체가 없으면 ⑤ check가 영영 실패한다. 실패=기록만(best-effort) — 최종 게이트는 ⑤ check.
    _progress("④-b 리뷰어 감지·폴백 기동 중(최대 320s — 대체 리뷰어 2슬롯 순차)…")
    code, out = _run([py, orchestra, "boot-reviewers"], timeout=320)
    log.step("④b-boot-reviewers", code, out)

    # ⑤ orchestra check — bounded retry(노드 ready는 비동기·check는 스냅샷)
    _progress("⑤ 노드 생존 결정론 확인(check · 최대 %d회×%.0fs 재시도)…" % (CHECK_RETRIES, CHECK_INTERVAL_S))
    code, out = 1, "orchestra 부재"
    for attempt in range(1, CHECK_RETRIES + 1):
        code, out = _run([py, orchestra, "check"], timeout=60)
        log.step("⑤check#%d" % attempt, code, out)
        if code == 0:
            break
        if attempt < CHECK_RETRIES:
            time.sleep(CHECK_INTERVAL_S)
    if code != 0:
        return log.fail("⑤check", code,
                        "%d회 재시도 후에도 의무 노드 미기동:\n%s" % (CHECK_RETRIES, out), 6)

    # ⑥ 완료 마커 — ⑤ exit 0에서만 도달. base 소켓 가드(부서 부트는 base 마커 무접촉).
    if _is_base_socket():
        _atomic_write_json(MARKER, {
            "pack_version": _pack_version(), "binary_version": _binary_version(),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "surface_ref": os.environ.get("CYS_SURFACE_ID", ""),
            "socket": os.environ.get("CYS_SOCKET", ""), "orchestra_check": "exit 0"})
        log.step("⑥marker", 0, MARKER)
        marker_note = "base 마커 기록"
    else:
        log.step("⑥marker", 0, "부서 소켓 컨텍스트 — base 마커 무접촉(부서장 부트 완료)")
        marker_note = "부서장 부트 — base 마커 무접촉"

    # ⑦ 승격 pending 해소 요청(비대기) — 동의·실제 승격은 부트 밖(배지/feed·차기 lifecycle)
    if _is_base_socket():
        dept = os.path.join(PACK, "bin", "cys-dept")
        if os.path.isfile(dept):
            code, out = _run(["bash", dept, "promote-if-pending", "--request-only"], timeout=30)
            log.step("⑦promote-request", code, out)  # best-effort — 실패해도 부트는 성공
        else:
            log.step("⑦promote-request", 0, "cys-dept 부재 — 생략")
    else:
        log.step("⑦promote-request", 0, "부서 컨텍스트 — 생략")

    # ⑧ 기계 요약 — master는 이 JSON을 인용해 '기동 완료'를 보고한다(다른 근거 인용 금지)
    summary = {"ok": True, "marker": marker_note,
               "steps": [(s["step"], s["exit"]) for s in log.data["steps"]],
               "boot_last": BOOT_LAST}
    log.data["result"] = {"ok": True}
    _atomic_write_json(BOOT_LAST, log.data)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def cmd_status():
    print(json.dumps({"marker": _read_json(MARKER), "boot_last": _read_json(BOOT_LAST),
                      "base_socket": _is_base_socket()}, ensure_ascii=False, indent=1))
    return 0


def cmd_assert_ready():
    """하위 게이트 전용: 마커 부재/pack_version 불일치 → exit 5.
    stale 정책(설계 §4.1): assert-ready는 버전 대조(ceo_promote 게이트는 존재만 — cys-dept 측)."""
    gate = os.environ.get("CYS_BOOT_GATE", "").strip().lower()
    if gate == "off":
        return 0
    m = _read_json(MARKER)
    ok = bool(m) and m.get("pack_version") == _pack_version()
    if ok:
        return 0
    why = "마커 부재" if not m else "pack_version 불일치(%s≠%s) — 재부트 필요" % (
        m.get("pack_version"), _pack_version())
    sys.stderr.write("[bootstrap assert-ready] %s\n" % why)
    return 0 if gate == "warn" else 5


def cmd_self_test():
    """레인 격리 3종 순수 판정 자체검증(orchestra 관례 — assert 배터리 → OK/FAIL).
    결정론·밀폐: env·데몬·파일 무접촉(순수 함수만 호출)."""
    try:
        # ── t1: base/dept 판정 매트릭스(unix base·unix dept·win pipe) ──
        assert _socket_is_base("") is True, "unset=base"
        assert _socket_is_base("/Users/x/.local/state/cys/cys.sock") is True, "unix base"
        assert _socket_is_base("/Users/x/.local/state/cys-dept-dept-1/cys.sock") is False, \
            "unix dept 소켓이 base로 오판(원 버그 — basename cys.sock 동일)"
        assert _socket_is_base("/Users/x/.local/state/cys-dept-ceo/cys.sock") is False, "unix dept(ceo)"
        assert _socket_is_base("\\\\.\\pipe\\cys") is True, "win base pipe(basename 보존)"
        assert _socket_is_base("\\\\.\\pipe\\cys-dept-foo") is False, "win dept pipe"
        assert _socket_is_base("/tmp/whatever.sock") is True, "cys-dept- 성분 없는 소켓=base(브리프 계약)"

        # ── t2: 락 키 유일성(부서 basename 동일 → 전체 경로 유일화) ──
        k1 = _sanitize_sock_key("/Users/x/.local/state/cys-dept-dept-1/cys.sock")
        k2 = _sanitize_sock_key("/Users/x/.local/state/cys-dept-dept-2/cys.sock")
        kb = _sanitize_sock_key("")
        assert k1 != k2, "동일 basename 두 부서 소켓이 같은 락 키(원 버그)"
        assert kb == _sanitize_sock_key("base") == "base", "미설정=base 키"
        assert k1 != kb and k2 != kb, "부서 키가 base 키와 충돌"
        for k in (k1, k2, kb):
            assert k and "/" not in k and os.sep not in k and ":" not in k and "\\" not in k, \
                "락 키에 경로 구분자/공백 잔존: %r" % k
        klong = _sanitize_sock_key("/" + "a" * 400 + "/cys-dept-z/cys.sock")
        assert len(klong) <= 180, "과길이 소켓 키 미절단: %d" % len(klong)
        assert klong == _sanitize_sock_key("/" + "a" * 400 + "/cys-dept-z/cys.sock"), "새니타이즈 비결정론"
        assert klong != _sanitize_sock_key("/" + "b" * 400 + "/cys-dept-z/cys.sock"), "과길이 경로 해시 충돌"

        # ── t3: 레인↔팩 정합(부서명 추출 + 불일치 판정) ──
        assert _socket_dept("") is None, "base 소켓 dept=None"
        assert _socket_dept("/s/cys-dept-dept-1/cys.sock") == "dept-1", "부서명 추출"
        assert _socket_dept("/s/cys/cys.sock") is None, "본부 소켓 dept=None"
        assert _pack_dept("/h/.cys/pack") is None, "메인 팩 dept=None"
        assert _pack_dept("/h/.cys/pack-dept-dept-1") == "dept-1", "부서 팩명 추출"
        assert _pack_dept("/h/.cys/pack-dept-dept-1/") == "dept-1", "trailing slash 관용"
        assert _lane_pack_mismatch("", "/h/.cys/pack") is None, "base+메인팩=정합"
        assert _lane_pack_mismatch("/s/cys-dept-dept-1/cys.sock", "/h/.cys/pack-dept-dept-1") is None, \
            "dept-X+pack-dept-X=정합"
        assert _lane_pack_mismatch("/s/cys-dept-dept-1/cys.sock", "/h/.cys/pack") == ("dept-1", None), \
            "dept 소켓+메인 팩=불일치(UT-14)"
        assert _lane_pack_mismatch("", "/h/.cys/pack-dept-dept-2") == (None, "dept-2"), \
            "base 소켓+부서 팩=불일치"
        assert _lane_pack_mismatch("/s/cys-dept-dept-1/cys.sock", "/h/.cys/pack-dept-dept-2") \
            == ("dept-1", "dept-2"), "교차 부서=불일치"
    except AssertionError as e:
        print("javis_bootstrap self-test FAIL: %s" % e, file=sys.stderr)
        return 1
    print("javis_bootstrap self-test OK (레인 격리 3종 — base/dept 판정·락 키 유일성·레인↔팩 정합)")
    return 0


def main(argv):
    # preflight/CI 호환: `--self-test`는 subcommand 없이도 동작(가로채기).
    if "--self-test" in argv:
        return cmd_self_test()
    cmd = argv[1] if len(argv) > 1 else "run"
    return {"run": cmd_run, "status": cmd_status,
            "assert-ready": cmd_assert_ready}.get(cmd, cmd_run)()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
