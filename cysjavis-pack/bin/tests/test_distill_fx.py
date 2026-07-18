#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_distill_fx.py — §C8.5 3저장소 불일치 fixture 전수(FX-1~FX-4).

설계 v3.2 §C8.5(L302-306) 4종 fixture를 결정론으로 핀한다. tmp 프로젝트를 동적 생성해
javis_distill.py CLI를 e2e로 구동(subprocess)하고, canonical(SOT)·memory(derivative)·
receipt(append-only) 3저장소의 불일치와 그 복구/거부를 단언한다.

  FX-1: canonical active인데 memory 색인에 없음 → sync 복구 절차 발동.
  FX-2: receipt(trailer)엔 있으나 canonical엔 없음 → candidate 등재(자동 active 아님).
  FX-3: memory 본문이 canonical과 다름 → canonical 우선 덮어쓰기 + 불일치 로그.
  FX-4: 비-locator 경로에 동일 rule_id active(이중 canonical) → exit 2 fail-closed +
        locator 경로만 정본 + 비-locator active 거부(C8.2-A).

기능시험(가짜 프로젝트 · 실 memory/git 무접촉) — 모듈 헬퍼는 assertion·fixture 조립에만 사용.
"""
import json
import os
import subprocess
import sys
import tempfile

SELF = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.dirname(SELF)
DISTILL = os.path.join(BIN, "javis_distill.py")
sys.path.insert(0, BIN)
import javis_distill as D  # noqa: E402 — assertion·fixture 조립용(포맷 단일 진실원)

fails = []


def check(name, cond, detail=""):
    print("%s %s%s" % ("PASS" if cond else "FAIL", name, (" — " + detail) if detail else ""))
    if not cond:
        fails.append(name)


def run(*args):
    r = subprocess.run([sys.executable, DISTILL] + list(args),
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    return r.returncode, r.stdout + r.stderr


def new_project():
    """tmp 프로젝트 + .vibecoding/distill.json(canonical_locator 1개) + memory dir."""
    proj = tempfile.mkdtemp(prefix="distill-fx-")
    os.makedirs(os.path.join(proj, ".vibecoding"))
    json.dump({"canonical_locator": "docs/rules/vibe-rules.md"},
              open(os.path.join(proj, ".vibecoding", "distill.json"), "w", encoding="utf-8"))
    mdir = os.path.join(proj, "memory")
    return proj, mdir


def cfg_of(proj):
    return D.load_config(proj)[0]


def canonical_rules(proj):
    return {r["rule_id"]: r for r in D.read_canonical(proj, cfg_of(proj))}


def seed_active_rule(proj, mdir):
    """propose→promote로 canonical active rule 1개 + memory 미러 생성. rule_id 반환."""
    rc, out = run("propose", "--project", proj, "--body", "외부 API 응답은 역참조 전 null 검사한다.",
                  "--root-cause", "null 반환 역참조 크래시", "--regression-test-ref", "tests/t.py::t")
    assert rc == 0, out
    rid = json.loads(out.strip().splitlines()[-1])["proposed"]
    rc, out = run("promote", "--project", proj, "--rule-id", rid, "--master",
                  "--holdout-evidence", "run#42 재발0", "--memory-dir", mdir)
    assert rc == 0, out
    return rid


# ══ FX-1: canonical active인데 memory 색인에 없음 → sync 복구 절차 발동 ══
proj, mdir = new_project()
rid = seed_active_rule(proj, mdir)
check("FX-1 setup: memory 미러 생성됨", rid in D.memory_map(mdir))
# memory 색인에서 제거(색인 누락 시뮬레이션)
os.unlink(os.path.join(mdir, D.memory_filename(rid)))
check("FX-1 setup: memory 색인에서 제거됨", rid not in D.memory_map(mdir))
# 탐지: sync-check(무-fix) → 드리프트 exit 1 + MISSING_IN_MEMORY finding
rc, out = run("sync-check", "--project", proj, "--memory-dir", mdir, "--json")
data = json.loads(out)
miss = [f for f in data["findings"] if f["type"] == "MISSING_IN_MEMORY" and f["rule_id"] == rid]
check("FX-1 탐지: exit 1(드리프트)", rc == 1, "rc=%d" % rc)
check("FX-1 탐지: MISSING_IN_MEMORY finding", len(miss) == 1, str(data["findings"]))
# 복구 절차 발동: --fix → memory 미러 재생성 + sync.log 기록 + exit 0
rc, out = run("sync-check", "--project", proj, "--memory-dir", mdir, "--fix", "--json")
check("FX-1 복구: --fix exit 0", rc == 0, out)
check("FX-1 복구: memory 미러 재생성됨(canonical SOT)", rid in D.memory_map(mdir))
synclog = os.path.join(proj, ".vibecoding", "sync.log")
check("FX-1 복구: 복구 절차 로그 발동", os.path.isfile(synclog)
      and "MISSING_IN_MEMORY" in open(synclog, encoding="utf-8").read())


# ══ FX-2: receipt(trailer)엔 있으나 canonical엔 없음 → candidate 등재(자동 active 아님) ══
proj, mdir = new_project()
# receipt에만 존재하는 rule(자동 active 유혹을 위해 event=promote/status=active로 기록).
recpath = os.path.join(proj, ".vibecoding", "receipts.jsonl")
with open(recpath, "w", encoding="utf-8") as f:
    f.write(json.dumps({"event": "promote", "rule_id": "VR-050", "status": "active",
                        "body": "타임아웃은 지수 백오프로 재시도한다."}, ensure_ascii=False) + "\n")
check("FX-2 setup: canonical엔 VR-050 없음", "VR-050" not in canonical_rules(proj))
# 탐지: TRAILER_ONLY finding
rc, out = run("sync-check", "--project", proj, "--memory-dir", mdir, "--json")
data = json.loads(out)
trail = [f for f in data["findings"] if f["type"] == "TRAILER_ONLY" and f["rule_id"] == "VR-050"]
check("FX-2 탐지: exit 1(드리프트)", rc == 1, "rc=%d" % rc)
check("FX-2 탐지: TRAILER_ONLY finding", len(trail) == 1, str(data["findings"]))
# 복구: --fix → canonical에 candidate로 등재(자동 active 승격 아님)
rc, out = run("sync-check", "--project", proj, "--memory-dir", mdir, "--fix", "--json")
rules = canonical_rules(proj)
check("FX-2 복구: --fix exit 0", rc == 0, out)
check("FX-2 복구: VR-050 canonical 등재됨", "VR-050" in rules)
check("FX-2 복구: status=candidate(자동 active 아님)",
      "VR-050" in rules and rules["VR-050"]["status"] == "candidate",
      rules.get("VR-050", {}).get("status"))
check("FX-2 복구: memory에 active로 새지 않음(candidate는 미러 없음)", "VR-050" not in D.memory_map(mdir))


# ══ FX-3: memory 본문이 canonical과 다름 → canonical 우선 덮어쓰기 + 불일치 로그 ══
proj, mdir = new_project()
rid = seed_active_rule(proj, mdir)
canonical_body = canonical_rules(proj)[rid]["body"]
# memory 미러 본문을 canonical과 다르게 변조
mpath = os.path.join(mdir, D.memory_filename(rid))
tampered = ("---\nname: vibe-rule-%s\ndescription: 변조\nmetadata:\n  type: feedback\n"
            "  vibe_rule_id: %s\n---\n\n오래된/틀린 본문 — canonical과 불일치.\n" % (rid.lower(), rid))
open(mpath, "w", encoding="utf-8").write(tampered)
check("FX-3 setup: memory 본문이 canonical과 다름", D.memory_map(mdir)[rid] != canonical_body)
# 탐지: MEMORY_BODY_DIVERGENT
rc, out = run("sync-check", "--project", proj, "--memory-dir", mdir, "--json")
data = json.loads(out)
div = [f for f in data["findings"] if f["type"] == "MEMORY_BODY_DIVERGENT" and f["rule_id"] == rid]
check("FX-3 탐지: exit 1(드리프트)", rc == 1, "rc=%d" % rc)
check("FX-3 탐지: MEMORY_BODY_DIVERGENT finding", len(div) == 1, str(data["findings"]))
# 복구: canonical 우선 덮어쓰기 + 불일치 로그
rc, out = run("sync-check", "--project", proj, "--memory-dir", mdir, "--fix", "--json")
check("FX-3 복구: --fix exit 0", rc == 0, out)
check("FX-3 복구: memory 본문 = canonical 본문(canonical 우선)",
      D.memory_map(mdir)[rid].strip() == canonical_body.strip())
synclog = os.path.join(proj, ".vibecoding", "sync.log")
check("FX-3 복구: 불일치 로그 기록", os.path.isfile(synclog)
      and "MEMORY_BODY_DIVERGENT" in open(synclog, encoding="utf-8").read())


# ══ FX-4: 이중 canonical 충돌 → exit 2 fail-closed + locator만 정본 + 비-locator active 거부 ══
proj, mdir = new_project()
rid = seed_active_rule(proj, mdir)  # canonical_locator(docs/rules/vibe-rules.md)에 active
# 비-locator 경로(CLAUDE.md 규칙 절)에 동일 rule_id를 서로 다른 본문·active로 위조 등재
stray = os.path.join(proj, "CLAUDE.md")
open(stray, "w", encoding="utf-8").write("# 규칙 절\n\n" + D.render_canonical([{
    "rule_id": rid, "status": "active", "canonical_locator": "docs/rules/vibe-rules.md",
    "regression_test_ref": None, "root_cause": None, "superseded_by": None,
    "body": "위조된 상이 본문 — 비-locator active 사본."}]))
# scan-dual-active → exit 2 fail-closed
rc, out = run("scan-dual-active", "--project", proj, "--json")
data = json.loads(out)
check("FX-4 fail-closed: exit 2", rc == 2, "rc=%d out=%s" % (rc, out[-200:]))
check("FX-4: ok=false(충돌)", data["ok"] is False)
conf = [c for c in data["conflicts"] if c["rule_id"] == rid]
check("FX-4: 충돌 검출(동일 rule_id 비-locator active)", len(conf) == 1, str(data["conflicts"]))
check("FX-4: locator 경로만 정본(authoritative)",
      len(conf) == 1 and conf[0]["authoritative_path"] == "docs/rules/vibe-rules.md")
check("FX-4: 비-locator 사본 위치=CLAUDE.md",
      len(conf) == 1 and conf[0]["found_at"] == "CLAUDE.md", str(conf))
check("FX-4: 비-locator active 거부(REJECTED_NON_LOCATOR)",
      len(conf) == 1 and conf[0]["verdict"] == "REJECTED_NON_LOCATOR")
# 대조: 위조 사본 제거 시 정상(exit 0)
os.unlink(stray)
rc, out = run("scan-dual-active", "--project", proj, "--json")
check("FX-4 대조: 비-locator 사본 제거 후 exit 0", rc == 0, out)


# ══ FX-4b (M-4 보강): dot-directory에 숨긴 이중 active도 fail-closed 검출 ══
# 공격: 비-locator active 사본을 .hidden/ 아래로 숨겨 scan-dual-active를 우회하려는 시도.
proj, mdir = new_project()
rid = seed_active_rule(proj, mdir)  # canonical_locator에 active
hidden_dir = os.path.join(proj, ".hidden")
os.makedirs(hidden_dir)
hidden = os.path.join(hidden_dir, "rules.md")
open(hidden, "w", encoding="utf-8").write("# 숨긴 규칙\n\n" + D.render_canonical([{
    "rule_id": rid, "status": "active", "canonical_locator": "docs/rules/vibe-rules.md",
    "regression_test_ref": None, "root_cause": None, "superseded_by": None,
    "body": "숨긴 경로의 비-locator active 사본."}]))
rc, out = run("scan-dual-active", "--project", proj, "--json")
data = json.loads(out)
conf = [c for c in data["conflicts"] if c["found_at"] == os.path.join(".hidden", "rules.md")]
check("FX-4b M-4: dot-dir 은폐 이중 active도 exit 2 fail-closed", rc == 2, "rc=%d out=%s" % (rc, out[-200:]))
check("FX-4b M-4: .hidden/rules.md 사본이 충돌로 검출됨(우회 차단)", len(conf) == 1, str(data["conflicts"]))
check("FX-4b M-4: 숨긴 사본도 REJECTED_NON_LOCATOR",
      len(conf) == 1 and conf[0]["verdict"] == "REJECTED_NON_LOCATOR")
# 대조: .git 등 명시 제외 디렉토리의 사본은 정본 후보가 아니므로 스캔 안 함(오탐 방지)
gitdir = os.path.join(proj, ".git")
os.makedirs(gitdir)
open(os.path.join(gitdir, "rules.md"), "w", encoding="utf-8").write(D.render_canonical([{
    "rule_id": rid, "status": "active", "canonical_locator": "docs/rules/vibe-rules.md",
    "regression_test_ref": None, "root_cause": None, "superseded_by": None, "body": "vcs 내부"}]))
os.unlink(hidden)  # .hidden 사본 제거 후 .git만 남김
rc, out = run("scan-dual-active", "--project", proj, "--json")
check("FX-4b 대조: .git 내부 사본은 제외(exit 0 · 명시 제외목록)", rc == 0, out)


print("\n%d FAIL" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
