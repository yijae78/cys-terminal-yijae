#!/usr/bin/env python3
"""무중단(재시작 0) 팩 업데이트 실측 E2E — DESIGN-noshutdown-pack-update §5-2·§7-⑥.

라이브 cysd에 `cys pack-update --from <테스트팩>`을 가해 **반영 전/후 스냅샷 동등성**을 검증한다:

  | 생존 대상 | RPC(실측)         | 읽는 필드                     | 합격 조건            |
  |-----------|-------------------|-------------------------------|----------------------|
  | cysd      | system.identify   | daemon_pid                    | 전/후 동일           |
  | 세션      | surface.list      | surfaces[].surface_id·exited  | 집합 불변·전부 false |
  | 팩 반영   | 파일              | <pack_dir>/.pack-version      | 새 버전으로 범프     |

★불합격(hard fail): daemon_pid 변동 = 데몬 재시작 = 무중단 위반 = FAIL.
  --app-pid 를 주면 cys-app(Tauri) OS 프로세스 pid·기동시각 동일성(재시작 0)도 검증한다.

★노드 각성 검증: pack-update 후 `system.topology`의 surface별 `pack_reinject` 마커가
  새 pack_version으로 갱신됐는지 확인한다(부분/낡은 각성 = FAIL). 디렉티브 해시 불변 시
  reinject는 스킵되므로(설계 §7-② step1) 마커 변동 없음은 정상으로 본다.

출력·exit code는 SKIP/PASS/FAIL을 명확히 구분한다:
  - PASS  → exit 0   (모든 검사 통과)
  - FAIL  → exit 1   (검사 1건 이상 실패 = 무중단/각성 위반)
  - SKIP  → exit 77  (라이브 데몬/테스트 팩 부재 — 평시 graceful skip, pass와 구분)

릴리스/승인용 hard gate 모드:
  --require-live  → 라이브 cysd 부재 = skip 아니라 FAIL(non-zero).
  --require-pack  → 테스트 팩(--from) 부재/불완전 = skip 아니라 FAIL(non-zero).

실행:
  python3 docs/noshutdown_verify.py --from /path/to/testpack   # pack.tar.gz+manifest+.minisig
  python3 docs/noshutdown_verify.py --from ... --require-live --require-pack   # 릴리스 게이트
  python3 docs/noshutdown_verify.py --from ... --app-pid 12345                 # Tauri 앱 동일성도
  CYS_SOCKET=... CYS_PACK_DIR=... python3 docs/noshutdown_verify.py --from ...
"""
import argparse
import json
import os
import socket
import subprocess
import sys


def default_socket():
    """src/lib.rs::socket_path()와 동일 규칙 — CYS_SOCKET 우선, 없으면 ~/.local/state/cys/cys.sock."""
    for k in ("CYS_SOCKET", "JAVIS_SOCKET", "AITERM_SOCKET"):
        v = os.environ.get(k)
        if v:
            return v
    home = os.path.expanduser("~")
    return os.path.join(home, ".local", "state", "cys", "cys.sock")


def default_pack_dir():
    """src/pack.rs::pack_dir()와 동일 규칙 — CYS_PACK_DIR 우선, 없으면 ~/.cys/pack."""
    for k in ("CYS_PACK_DIR", "JAVIS_PACK_DIR", "AITERM_JARVIS_DIR"):
        v = os.environ.get(k)
        if v:
            return v
    return os.path.join(os.path.expanduser("~"), ".cys", "pack")


def find_cys_bin():
    """cys 바이너리 — target/release > target/debug > PATH."""
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (
        os.path.join(here, "..", "target", "release", "cys"),
        os.path.join(here, "..", "target", "debug", "cys"),
    ):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return os.path.abspath(cand)
    return "cys"  # PATH 폴백


class DaemonUnavailable(Exception):
    pass


def rpc(sock_path, method, params, timeout=5.0):
    """Unix 소켓 1-shot JSON-RPC(개행 종단) — docs/*_e2e.py 패턴."""
    try:
        s = socket.socket(socket.AF_UNIX)
        s.settimeout(timeout)
        s.connect(sock_path)
    except OSError as e:
        raise DaemonUnavailable(f"소켓 연결 실패 {sock_path}: {e}")
    try:
        s.sendall((json.dumps({"id": 1, "method": method, "params": params}) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    finally:
        s.close()
    if not buf:
        raise DaemonUnavailable(f"빈 응답({method})")
    resp = json.loads(buf)
    if "error" in resp and resp["error"]:
        raise RuntimeError(f"RPC 오류({method}): {resp['error']}")
    return resp.get("result", resp)


def read_pack_version(pack_dir):
    p = os.path.join(pack_dir, ".pack-version")
    try:
        with open(p) as f:
            return f.read().strip()
    except OSError:
        return ""


def snapshot(sock_path, pack_dir):
    """무중단 불변식 스냅샷: daemon_pid + {surface_id: exited} + .pack-version."""
    ident = rpc(sock_path, "system.identify", {})
    daemon_pid = ident.get("daemon_pid")
    surfaces = rpc(sock_path, "surface.list", {}).get("surfaces", [])
    surf = {int(s["surface_id"]): bool(s.get("exited", False)) for s in surfaces if "surface_id" in s}
    return {
        "daemon_pid": daemon_pid,
        "surfaces": surf,
        "pack_version": read_pack_version(pack_dir),
    }


def parse_semver(v):
    """src/pack.rs::parse_semver와 동일 규칙 — 'v' 접두 제거, '-'/'+' suffix 분리, major 결측=None."""
    v = (v or "").strip().lstrip("v")
    parts = v.split(".")
    if not parts or parts[0] == "":
        return None
    out = []
    for i in range(3):
        seg = parts[i] if i < len(parts) else "0"
        seg = seg.split("-")[0].split("+")[0]
        if not seg.isdigit():
            if i == 0:
                return None
            seg = "0"
        out.append(int(seg))
    return tuple(out)


def version_bumped(before, after):
    """after가 before보다 strictly-newer(semver). 둘 다 파싱되면 비교, 아니면 문자열 상이로 폴백."""
    b, a = parse_semver(before), parse_semver(after)
    if a is not None and b is not None:
        return a > b
    return bool(after) and after != before


SKIP_EXIT = 77  # skip을 pass(0)·fail(1)과 명확히 구분하는 종료코드.


def proc_alive(pid):
    """pid 프로세스 생존 여부 — signal 0(존재 검사, 미전달)."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # 존재하나 시그널 권한 없음 = 살아있음.
    except OSError:
        return False


def proc_starttime(pid):
    """프로세스 기동시각(ps lstart) — 동일 pid 재사용(재시작) 판별용. 실패 시 빈 문자열."""
    try:
        out = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def topology_markers(sock_path):
    """system.topology의 saved 엔트리에서 {키: pack_version} reinject 마커 맵 추출.

    키 = session_id 우선(없으면 role) — surface별 마커를 안정 식별. RPC 미지원/오류 시 None.
    """
    try:
        topo = rpc(sock_path, "system.topology", {})
    except (DaemonUnavailable, RuntimeError, OSError):
        return None
    markers = {}
    for e in topo.get("saved", []) or []:
        if not isinstance(e, dict):
            continue
        pr = e.get("pack_reinject")
        if isinstance(pr, dict) and pr.get("pack_version"):
            key = e.get("session_id") or e.get("role") or repr(sorted(e.items()))
            markers[key] = pr.get("pack_version")
    return markers


def main():
    ap = argparse.ArgumentParser(description="무중단 팩 업데이트 실측 E2E")
    ap.add_argument("--from", dest="from_dir",
                    help="테스트 팩 디렉터리(pack.tar.gz + pack-manifest.json + pack-manifest.json.minisig)")
    ap.add_argument("--socket", default=default_socket(), help="cysd Unix 소켓 경로")
    ap.add_argument("--pack-dir", default=default_pack_dir(), help="설치 팩 디렉터리(.pack-version 위치)")
    ap.add_argument("--require-live", action="store_true",
                    help="라이브 cysd 부재 시 skip이 아니라 FAIL(릴리스/승인 게이트)")
    ap.add_argument("--require-pack", action="store_true",
                    help="테스트 팩(--from) 부재/불완전 시 skip이 아니라 FAIL(릴리스/승인 게이트)")
    ap.add_argument("--app-pid", type=int, default=None,
                    help="cys-app(Tauri) OS 프로세스 pid — 주면 pack-update 전후 동일성(재시작 0) 검증")
    args = ap.parse_args()

    fails = []

    def check(name, cond, detail=""):
        tag = "PASS" if cond else "FAIL"
        print(f"[{tag}] {name}" + (f" — {detail}" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    # 게이트 0: 라이브 데몬 — 평시 graceful skip(exit 77), --require-live면 FAIL(exit 1).
    try:
        rpc(args.socket, "system.ping", {})
    except (DaemonUnavailable, OSError) as e:
        msg = f"라이브 cysd 없음({args.socket}): {e}"
        if args.require_live:
            print(f"[FAIL] {msg} — --require-live 게이트(skip 불가).")
            return 1
        print(f"[SKIP] {msg} — 무중단 실측 생략(로직은 완성).")
        return SKIP_EXIT

    # 게이트 0': 서명된 테스트 팩 — 평시 graceful skip(exit 77), --require-pack면 FAIL(exit 1).
    def pack_gate_skip(reason):
        if args.require_pack:
            print(f"[FAIL] {reason} — --require-pack 게이트(skip 불가).")
            return 1
        print(f"[SKIP] {reason} 실측 생략(로직은 완성).")
        return SKIP_EXIT

    if not args.from_dir:
        return pack_gate_skip("--from 미지정 — 서명된 테스트 팩이 있어야 실측 가능.")
    needed = ["pack.tar.gz", "pack-manifest.json", "pack-manifest.json.minisig"]
    missing = [f for f in needed if not os.path.isfile(os.path.join(args.from_dir, f))]
    if missing:
        return pack_gate_skip(f"테스트 팩 불완전({args.from_dir}) — 누락 {missing}.")

    # cys-app(Tauri) 기동시각 — pack-update가 OS 앱 프로세스를 재시작하지 않음을 보장(재시작 0).
    app_before = None
    if args.app_pid is not None:
        if not proc_alive(args.app_pid):
            check(f"cys-app(pid {args.app_pid}) 반영 전 생존", False,
                  "프로세스 부재 — --app-pid 확인")
        else:
            app_before = proc_starttime(args.app_pid)
            print(f"[snap-before] app_pid={args.app_pid} starttime={app_before!r}")

    # ★노드 각성 — 반영 전 reinject 마커 베이스라인(session_id→pack_version).
    markers_before = topology_markers(args.socket) or {}

    # 반영 전 스냅샷.
    before = snapshot(args.socket, args.pack_dir)
    print(f"[snap-before] daemon_pid={before['daemon_pid']} "
          f"surfaces={sorted(before['surfaces'])} pack_version={before['pack_version']!r}")
    # 반영 전에도 모든 세션이 살아있어야(exited:false) 비교 기준이 유효하다.
    check("반영 전 전 세션 생존(exited:false)",
          all(not e for e in before["surfaces"].values()),
          f"exited 세션 존재: {[s for s, e in before['surfaces'].items() if e]}")

    # pack-update 실행.
    cys = find_cys_bin()
    print(f"[run] {cys} pack-update --from {args.from_dir}")
    proc = subprocess.run(
        [cys, "pack-update", "--from", args.from_dir],
        capture_output=True, text=True,
        env=dict(os.environ, CYS_SOCKET=args.socket, CYS_PACK_DIR=args.pack_dir),
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    check("pack-update 종료코드 0", proc.returncode == 0, f"exit={proc.returncode}")

    # 반영 후 스냅샷.
    after = snapshot(args.socket, args.pack_dir)
    print(f"[snap-after]  daemon_pid={after['daemon_pid']} "
          f"surfaces={sorted(after['surfaces'])} pack_version={after['pack_version']!r}")

    # ★무중단 불변식 검증.
    check("cysd 생존 — daemon_pid 동일(재시작 0)",
          before["daemon_pid"] is not None and before["daemon_pid"] == after["daemon_pid"],
          f"{before['daemon_pid']} != {after['daemon_pid']} (재시작 = 무중단 위반)")
    check("세션 집합 불변 — surface_id set 동일",
          set(before["surfaces"]) == set(after["surfaces"]),
          f"before={sorted(before['surfaces'])} after={sorted(after['surfaces'])}")
    check("반영 후 전 세션 생존(exited:false)",
          all(not e for e in after["surfaces"].values()),
          f"exited 세션 존재: {[s for s, e in after['surfaces'].items() if e]}")
    check("팩 반영 — .pack-version 범프",
          version_bumped(before["pack_version"], after["pack_version"]),
          f"{before['pack_version']!r} → {after['pack_version']!r} (범프 안 됨)")

    # ★cys-app(Tauri) 동일성 — 재시작 0(같은 프로세스 인스턴스 유지).
    if app_before is not None:
        app_after = proc_starttime(args.app_pid)
        check(f"cys-app(pid {args.app_pid}) 생존 — 재시작 0",
              proc_alive(args.app_pid) and app_after == app_before,
              f"기동시각 {app_before!r} → {app_after!r} (변동 = 앱 재시작 = 무중단 위반)")

    # ★노드 각성 검증 — pack_reinject 마커가 새 pack_version으로 갱신됐는지.
    markers_after = topology_markers(args.socket)
    if markers_after is None:
        print("[awaken] system.topology 미응답 — 각성 마커 확인 생략(RPC 미노출 가능).")
    else:
        new_ver = after["pack_version"]
        changed = {k: v for k, v in markers_after.items() if markers_before.get(k) != v}
        awakened = [k for k, v in changed.items() if v == new_ver]
        stale = {k: v for k, v in changed.items() if v != new_ver}
        print(f"[awaken] reinject 마커: 새 버전({new_ver!r}) 각성 {len(awakened)}개, "
              f"마커 변동 없음 {len(markers_after) - len(changed)}개 "
              f"(디렉티브 해시 불변 시 reinject 스킵 — 설계 §7-② step1).")
        # 마커가 '변했다면' 반드시 새 버전이어야 한다(부분/낡은 각성 = FAIL).
        check("노드 각성 — 변경된 reinject 마커는 새 pack_version",
              not stale,
              f"낡은/오류 마커: {stale} (기대 {new_ver!r})")

    if fails:
        print(f"\n[FAIL] {len(fails)}건: {fails}")
        return 1
    print("\n[PASS] 무중단 검증 통과 — cysd·세션·앱 생존, 팩만 갱신(재시작 0), 노드 각성 정합.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
