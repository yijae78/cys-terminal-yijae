#!/usr/bin/env python3
"""javis_dept_migrate.py — 기존 부서 config 마이그레이션 (증분2 D · D1 옵션 1' 배선).

배경: 결정론 부트스트랩 발화 훅(role-bootstrap.sh → UserPromptSubmit)은 preflight C28
(SELFCORR_HOOKS)이 부서 데몬 컨텍스트에서 --fix 될 때 부서 account config(settings.json)에
등록된다. 그러나 그 배선(2026-07-15) **이전에 생성된 기존 부서**의 config는 UserPromptSubmit이
부재해, 부서 pane에서 "너는 마스터다" 선언이 부트스트랩을 발화하지 못한다(RC1). 이 도구는
그 기존 부서들을 **부트 재실행 없이** 멱등 백필한다(신규 부서는 preflight가 이미 처리).

집행(양대):
  ① ~/.cys/claude-*(basename에 'dept-') account config settings.json 에 UserPromptSubmit →
     `sh <부서팩>/hooks/role-bootstrap.sh`(preflight `_cys_hook_cmd` 와 byte-identical) 등록.
  ② 부서 팩(~/.cys/pack-dept-<name>)에 hooks/role-bootstrap.sh · bin/javis_bootstrap.py 부재 시
     메인 팩(CYS_PACK_DIR|~/.cys/pack)에서 복사(훅 명령이 참조하는 실체 보장).

관례(preflight `_register_event_hook` 동형): symlink 거부 · 파싱 실패 거부 · 백업(.bak-migrate)
· 구/파손 우리-훅 엔트리 prune 후 재등록(중복 append 0) · 원자적 교체.

기본 --dry-run(파괴 없음·계획만) · --fix 로 집행. 실행 주체는 CSO(도구만 제공).
exit: 0=성공(dry/fix) / 2=오류 존재(메인 팩에도 소스 부재 등).
"""
import argparse
import glob
import json
import os
import shutil
import sys

HOME = os.path.expanduser("~")
CYS_DIR = os.path.join(HOME, ".cys")
MAIN_PACK = os.environ.get("CYS_PACK_DIR") or os.path.join(CYS_DIR, "pack")
EVENT = "UserPromptSubmit"
SCRIPT_NAME = "role-bootstrap.sh"
HOOK_REL = os.path.join("hooks", "role-bootstrap.sh")
BOOTSTRAP_REL = os.path.join("bin", "javis_bootstrap.py")
REQUIRED_PACK_FILES = [HOOK_REL, BOOTSTRAP_REL]


def _hook_cmd(pack):
    """UserPromptSubmit 훅 명령 — preflight `_cys_hook_cmd("role-bootstrap.sh")` · Rust
    role_bootstrap_hook_command 와 **byte-identical**(중복 등록 0). unix `sh <abs>` / win `bash "<정슬래시>"`."""
    script = os.path.join(pack, "hooks", "role-bootstrap.sh")
    if os.name == "nt":
        return 'bash "%s"' % script.replace("\\", "/")
    return "sh " + script


def _dept_name(acct_basename):
    """account dir basename(claude-<acct>-dept-N) → 부서명 'dept-N'(pack/socket 규약과 일치).
    첫 'dept-' 성분부터가 부서명(acct='default' 등은 'dept-' 미포함 전제)."""
    i = acct_basename.find("dept-")
    return acct_basename[i:] if i != -1 else None


def _dept_pack(name):
    return os.path.join(CYS_DIR, "pack-dept-%s" % name)


def _discover_dept_configs():
    """~/.cys/claude-* 중 basename에 'dept-'가 있는 account config dir → [(acctdir, dept명)]."""
    out = []
    for d in sorted(glob.glob(os.path.join(CYS_DIR, "claude-*"))):
        if not os.path.isdir(d):
            continue
        name = _dept_name(os.path.basename(d))
        if name:
            out.append((d, name))
    return out


def _event_registered(settings_path, cmd):
    try:
        with open(settings_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    for entry in data.get("hooks", {}).get(EVENT, []):
        if not isinstance(entry, dict):
            continue
        for h in entry.get("hooks", []):
            if isinstance(h, dict) and h.get("command", "") == cmd:
                return True
    return False


def _register_hook(settings_path, cmd, do_fix):
    """returns (action, detail). action ∈ ok|would|fixed|skip|error."""
    if os.path.islink(settings_path):
        return "skip", "symlink 거부: %s" % settings_path
    if not os.path.isfile(settings_path):
        return "skip", "settings.json 부재 — 부트 시 preflight가 생성(백필 대상 아님)"
    if _event_registered(settings_path, cmd):
        return "ok", "이미 등록됨(멱등)"
    if not do_fix:
        return "would", "UserPromptSubmit←role-bootstrap.sh 등록 예정(--fix)"
    try:
        with open(settings_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return "error", "기존 settings.json 파싱 실패 — 거부: %s" % e
    if not isinstance(data, dict):
        return "error", "settings.json 루트가 객체 아님 — 거부"
    backup = settings_path + ".bak-migrate"
    if not os.path.exists(backup):
        shutil.copy2(settings_path, backup)
    arr = data.setdefault("hooks", {}).setdefault(EVENT, [])
    # 구/파손 우리-훅 엔트리 prune 후 재등록(preflight _prune_stale_hook_entries 동형)
    kept, have = [], False
    for entry in arr:
        if not isinstance(entry, dict):
            kept.append(entry)
            continue
        cmds = [h.get("command", "") for h in entry.get("hooks", []) if isinstance(h, dict)]
        ours = any(SCRIPT_NAME in c and "hooks" in c for c in cmds)
        if not ours:
            kept.append(entry)
        elif cmd in cmds:
            kept.append(entry)
            have = True
        # else: 우리 훅이나 desired 불일치(구·파손) → 제거(교체 유도)
    if not have:
        kept.append({"hooks": [{"type": "command", "command": cmd}]})
    arr[:] = kept
    tmp = settings_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    os.replace(tmp, settings_path)
    return "fixed", "UserPromptSubmit←role-bootstrap.sh 등록(백업 .bak-migrate)"


def _ensure_pack_files(pack, do_fix):
    """부서 팩에 훅·부트스트랩 실체 보장. returns [(rel, action, detail)]."""
    results = []
    for rel in REQUIRED_PACK_FILES:
        dst = os.path.join(pack, rel)
        if os.path.isfile(dst):
            results.append((rel, "ok", "존재"))
            continue
        src = os.path.join(MAIN_PACK, rel)
        if not os.path.isfile(src):
            results.append((rel, "error", "메인 팩에도 부재: %s" % src))
            continue
        if not do_fix:
            results.append((rel, "would", "메인 팩에서 복사 예정(--fix)"))
            continue
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            if os.name == "posix":
                os.chmod(dst, 0o755)  # shell/py 직접 실행 — exec 비트 보존
            results.append((rel, "fixed", "메인 팩에서 복사"))
        except OSError as e:
            results.append((rel, "error", "복사 실패: %s" % e))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="기존 부서 config 마이그레이션 (증분2 D)")
    ap.add_argument("--fix", action="store_true", help="집행(기본: dry-run — 계획만)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    do_fix = a.fix

    report = {"mode": "fix" if do_fix else "dry-run", "main_pack": MAIN_PACK, "depts": []}
    had_error = False
    for acctdir, name in _discover_dept_configs():
        pack = _dept_pack(name)
        cmd = _hook_cmd(pack)
        settings = os.path.join(acctdir, "settings.json")
        pack_files = _ensure_pack_files(pack, do_fix)   # 훅 실체 먼저 보장
        h_action, h_detail = _register_hook(settings, cmd, do_fix)
        if h_action == "error" or any(ac == "error" for _, ac, _ in pack_files):
            had_error = True
        report["depts"].append({
            "dept": name, "acctdir": acctdir, "pack": pack, "settings": settings,
            "hook": {"action": h_action, "detail": h_detail},
            "pack_files": [{"rel": r, "action": ac, "detail": dt} for r, ac, dt in pack_files],
        })

    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print("[dept-migrate] 모드: %s · 메인 팩: %s" % (report["mode"], MAIN_PACK))
        if not report["depts"]:
            print("  대상 부서 config 없음(~/.cys/claude-*dept-* 미발견)")
        for d in report["depts"]:
            mark = {"ok": "·", "would": "→", "fixed": "✓", "skip": "⚠", "error": "✗"}
            print("  %s %s (%s)" % (mark.get(d["hook"]["action"], "?"), d["dept"], d["acctdir"]))
            print("     hook: %s — %s" % (d["hook"]["action"], d["hook"]["detail"]))
            for pf in d["pack_files"]:
                print("     pack %s: %s — %s" % (pf["rel"], mark.get(pf["action"], "?"), pf["detail"]))
        if not do_fix and report["depts"]:
            print("  (dry-run — 집행하려면 --fix)")
    return 2 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
