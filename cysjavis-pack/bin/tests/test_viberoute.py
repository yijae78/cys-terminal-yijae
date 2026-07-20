#!/usr/bin/env python3
"""test_viberoute.py — §C4 Route-Contract 결정론 검증.

3층 검증:
  ① 64조합 전수 기계 검증(§C4.2 전칭성) — 정규화 후 2^6 전 조합이 정확히 한 Level에 떨어짐을
     decide_level과 독립 오라클(first-match-wins 데이터 구조로 재기술)이 일치하는지로 단언.
  ② golden test 20개 — GT-1~11(설계 명세) + GT-12~20(신호 조합 의미론 경계, 근거 주석).
  ③ ledger 경로(critic advisory·재분류·silent 변경 차단·fail-closed) — CLI subprocess 실측.

관측 기법: 순수 함수는 모듈 import, ledger CLI는 임시 ledger(CYS_VIBEROUTE_LEDGER) subprocess.
"""
import itertools
import json
import os
import subprocess
import sys
import tempfile

SELF = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.dirname(SELF)
sys.path.insert(0, BIN)

import javis_viberoute as V  # noqa: E402

MOD = os.path.join(BIN, "javis_viberoute.py")

fails = []


def check(name, cond, detail=""):
    print("%s %s%s" % ("PASS" if cond else "FAIL", name, (" — " + detail) if detail else ""))
    if not cond:
        fails.append(name)


def _assert_no_new(start):
    """pytest 경로 vacuous-green 차단(G-1): 이 함수 구간에서 check() 실패가 하나라도 쌓였으면
    AssertionError로 실패시킨다. check()는 계속 fails에 누적만 하므로 직접 실행(main) 경로의
    '전 케이스 수집 후 요약' 동작은 불변 — main은 이 assert를 try/except로 흡수해 집계한다."""
    new = fails[start:]
    assert not new, "이 테스트에서 %d건 실패: %s" % (len(new), new)


# ── ① 64조합 전수 (§C4.2 전칭성) ───────────────────────────────────────────
def _oracle(sig):
    """decide_level과 독립한 first-match-wins 오라클 — 규칙을 (조건, Level) 데이터로 재기술.
    if-체인(decide_level)과 다른 코드 경로라 상호 검증이 tautology가 아니다."""
    rules = [
        (lambda s: s["deploy_exposure"] and
         (s["new_service"] or (s["persistent_data"] and s["external_integration"])), "L5"),
        (lambda s: any(s[k] for k in
                       ("persistent_data", "external_integration", "new_service", "deploy_exposure")), "L4"),
        (lambda s: s["scale_modules"] or s["brownfield"], "L3"),
        (lambda s: True, "L1-2"),
    ]
    for cond, lvl in rules:
        if cond(s=sig):
            return lvl


def test_64_totality():
    _s = len(fails)
    seen_none = 0
    disagree = 0
    invalid = 0
    for combo in itertools.product((False, True), repeat=len(V.SIGNAL_KEYS)):
        n = dict(zip(V.SIGNAL_KEYS, combo))
        got = V.decide_level(n)
        if got is None:
            seen_none += 1
        if got not in V.LEVELS:
            invalid += 1
        if got != _oracle(n):
            disagree += 1
    check("64조합: 미산출(None) 0", seen_none == 0, "None %d개" % seen_none)
    check("64조합: 전부 유효 Level", invalid == 0, "무효 %d개" % invalid)
    check("64조합: decide_level == 독립 오라클(전칭 일치)", disagree == 0, "불일치 %d개" % disagree)
    # 정규화 축: unknown→true. 각 신호가 unknown이면 true와 동일 판정을 내야 한다.
    skew = 0
    for combo in itertools.product(("false", "true", "unknown"), repeat=len(V.SIGNAL_KEYS)):
        signals = {k: {"value": v, "evidence": ""} for k, v in zip(V.SIGNAL_KEYS, combo)}
        norm = V.normalize(signals)
        # unknown을 true로 치환한 순수 bool과 정규화 결과가 같아야 한다
        want = {k: (v in ("true", "unknown")) for k, v in zip(V.SIGNAL_KEYS, combo)}
        if norm != want:
            skew += 1
    check("정규화: unknown→true 전수(3^6=729조합)", skew == 0, "%d개 어긋남" % skew)
    _assert_no_new(_s)


# ── ② golden test 20개 ─────────────────────────────────────────────────────
def _sig(**vals):
    """지정 신호만 값 세팅, 나머지 false. evidence는 형식만 채운다."""
    out = {}
    for k in V.SIGNAL_KEYS:
        out[k] = {"value": vals.get(k, "false"), "evidence": "%s=%s" % (k, vals.get(k, "false"))}
    return out


def _level_of(signals):
    return V.decide_level(V.normalize(signals))


# 각 GT: (id, signals, 기대 Level, 기대 needs_grill, 근거)
GOLDEN = [
    # ── 설계 명세 GT-1~11 (PROPOSAL §C4.6) ──
    ("GT-1", _sig(external_integration="true", deploy_exposure="true"), "L4", False,
     "배포 정적 1p+analytics: ei=true, 정적페이지≠new_service(pd/ns false) → 행2 L4"),
    ("GT-2", _sig(persistent_data="true", brownfield="true"), "L4", False,
     "기존 서비스 단일 DB migration: pd=true → 행2 L4(bf=true지만 행2 우선)"),
    ("GT-3", _sig(persistent_data="true", external_integration="true", deploy_exposure="true"), "L5", False,
     "flag 뒤 외부 결제 연동: 결제=거래 영속(pd)+외부API(ei)+배포(de) → 행1 L5"),
    ("GT-4", _sig(), "L1-2", False,
     "browser localStorage 데모: 로컬 휘발(pd=false)·미배포·비신규서비스 → 행4 L1-2"),
    ("GT-5", _sig(external_integration="unknown"), "L4", False,
     "신호 1개 unknown: ei=unknown→true 격상 → 행2 L4(unknown_count=1<2)"),
    ("GT-9", _sig(scale_modules="true"), "L3", False,
     "scale-only: sm=true·타 전부 false → 행3 L3(L4 과잉격상 아님·v3.1)"),
    ("GT-10", _sig(new_service="true"), "L4", False,
     "new-service-only·배포 없음: ns=true → 행2 L4(de 부재라 L5 아님·v3.1)"),
    ("GT-11", {k: {"value": "unknown", "evidence": ""} for k in V.SIGNAL_KEYS}, "L5", True,
     "전 신호 unknown: 정규화 전부 true → 행1 L5 + needs_grill(unknown 6≥2·v3.1)"),
    # ── 의미론 경계 GT-12~20 (워커 설계·근거 주석) ──
    ("GT-12", _sig(deploy_exposure="true"), "L4", False,
     "deploy-only: de=true지만 행1은 (ns∨(pd∧ei)) 동반 필요 → 미충족 → 행2 L4(노출 단독≠L5)"),
    ("GT-13", _sig(persistent_data="true", external_integration="true"), "L4", False,
     "data+integration·배포 없음: 행1은 de 필수 → de=false → 행2 L4(GT-3과의 de 유무 대조)"),
    ("GT-14", _sig(new_service="true", deploy_exposure="true"), "L5", False,
     "new-service+deploy: 행1 de∧ns 충족 → L5(데이터·연동 없어도 신규서비스 배포=L5·v3.1 경로)"),
    ("GT-15", _sig(brownfield="true"), "L3", False,
     "brownfield-only: bf=true·타 false → 행3 L3(GT-9 scale-only의 거울 사례)"),
    ("GT-16", _sig(scale_modules="true", persistent_data="true"), "L4", False,
     "scale+data: pd=true → 행2 L4(행2>행3 first-match — scale이 있어도 데이터면 L4로 상승)"),
    ("GT-17", _sig(deploy_exposure="true", persistent_data="true"), "L4", False,
     "deploy+data·연동無: 행1은 (pd∧ei) 둘 다 필요 → ei=false → 행2 L4(행1 내부 ∧ 경계 방어)"),
    ("GT-18", _sig(persistent_data="unknown", brownfield="unknown"), "L4", True,
     "unknown 2개(pd·bf): 정규화 pd/bf true → 행2 L4 + needs_grill(임계 정확히 2)"),
    ("GT-19", _sig(scale_modules="unknown"), "L3", False,
     "unknown 1개(sm): sm→true → 행3 L3·needs_grill=false(단일 unknown이 행3 계층 격상)"),
    ("GT-20", {k: {"value": "true", "evidence": ""} for k in V.SIGNAL_KEYS}, "L5", False,
     "전 신호 true(천장): 행1 → L5(GT-11 all-unknown과 같은 종착을 명시 true로 확인)"),
]


def test_golden():
    _s = len(fails)
    for gid, signals, want_level, want_grill, why in GOLDEN:
        problems = V.validate_schema({"signals": signals})
        if problems:
            check("%s 스키마 유효" % gid, False, "%s" % problems)
            continue
        got_level = _level_of(signals)
        got_grill = V.unknown_count(signals) >= 2
        check("%s Level=%s" % (gid, want_level), got_level == want_level,
              "got %s · %s" % (got_level, why))
        check("%s needs_grill=%s" % (gid, want_grill), got_grill == want_grill, why)
    _assert_no_new(_s)


# ── ③ ledger 경로 CLI 실측 (GT-6·GT-7·GT-8 + fail-closed) ──────────────────
def _run(args, stdin=None, ledger=None):
    env = dict(os.environ)
    if ledger:
        env["CYS_VIBEROUTE_LEDGER"] = ledger
    r = subprocess.run([sys.executable, MOD] + args, input=stdin,
                       capture_output=True, text=True, env=env, timeout=30)
    return r.returncode, r.stdout, r.stderr


def _payload(signals, task_id="T", with_hash=True):
    p = {"task_id": task_id, "signals": signals}
    if with_hash:
        p["input_hash"] = V.compute_input_hash(signals)
    return json.dumps(p, ensure_ascii=False)


def test_ledger_paths():
    _s = len(fails)
    tmp = tempfile.mkdtemp()
    ledger = os.path.join(tmp, "route-log.jsonl")

    # 기본 judge → 기록·Level 산출
    rc, out, err = _run(["judge", "--input", "-"], stdin=_payload(_sig(persistent_data="true"), "T-A"),
                        ledger=ledger)
    ok = rc == 0 and json.loads(out).get("level") == "L4"
    check("judge L4 기록", ok, "rc=%s out=%s" % (rc, out.strip()))
    check("input_hash 일치(judge 통과)", rc == 0, err.strip())

    # GT-6 (advisory 경로): critic 격하 finding + 승인 부재 → Level 불변, finding만 기록
    rc, out, err = _run(["critic", "--task-id", "T-A", "--direction", "down",
                        "--evidence", "주석뿐인 델타로 보임", "--confidence", "low"], ledger=ledger)
    check("GT-6 critic 기록(rc=0)", rc == 0, err.strip())
    rc, out, err = _run(["verify", "--task-id", "T-A"], ledger=ledger)
    v = json.loads(out) if rc == 0 else json.loads(err)
    check("GT-6 승인 부재 → Level 불변(L4)", rc == 0 and v.get("effective_level") == "L4",
          "rc=%s effective=%s" % (rc, v.get("effective_level")))
    recs = V._read_records(ledger, "T-A")
    check("GT-6 critic advisory 레코드 존재",
          any(r["type"] == "critic" and r["level_unchanged"] for r in recs))

    # GT-7 (재분류 경로): critic + master 승인(APR)+RC-02+기계증거 → 격하 반영·전 필드 기록
    rc, out, err = _run(["reclassify", "--task-id", "T-A", "--from-level", "L4", "--to-level", "L1-2",
                        "--approval-id", "APR-20260718-001", "--reason-code", "RC-02",
                        "--machine-evidence", "AST diff → 실행경로 무변경 확인"], ledger=ledger)
    check("GT-7 재분류 기록(rc=0)", rc == 0, err.strip())
    rc, out, err = _run(["verify", "--task-id", "T-A"], ledger=ledger)
    v = json.loads(out) if rc == 0 else json.loads(err)
    check("GT-7 격하 반영(effective L1-2)", rc == 0 and v.get("effective_level") == "L1-2",
          "rc=%s effective=%s" % (rc, v.get("effective_level")))
    recs = V._read_records(ledger, "T-A")
    rc_rec = [r for r in recs if r["type"] == "reclassification"]
    check("GT-7 재분류 전 필드 기록(APR·RC·기계증거)",
          bool(rc_rec) and rc_rec[-1]["approval_id"] == "APR-20260718-001"
          and rc_rec[-1]["reason_code"] == "RC-02" and rc_rec[-1]["machine_evidence"])

    # GT-8 (silent 변경 차단): 승인 기록 없이 Level만 바뀐 변조 레코드 → 게이트 fail
    ledger2 = os.path.join(tmp, "tampered.jsonl")
    _run(["judge", "--input", "-"], stdin=_payload(_sig(persistent_data="true"), "T-B"), ledger=ledger2)
    with open(ledger2, "a", encoding="utf-8") as f:  # 변조: 승인 없는 재분류 직접 주입
        f.write(json.dumps({"type": "reclassification", "task_id": "T-B",
                            "from_level": "L4", "to_level": "L1-2"}, ensure_ascii=False) + "\n")
    rc, out, err = _run(["verify", "--task-id", "T-B"], ledger=ledger2)
    v = json.loads(err) if rc != 0 else json.loads(out)
    check("GT-8 silent 변경 → 게이트 fail(rc=6)", rc == V.EXIT_GATE and v.get("gate") == "fail",
          "rc=%s violations=%s" % (rc, v.get("violations")))

    # GT-8b: 미지 type 변조 레코드도 차단
    ledger3 = os.path.join(tmp, "tampered2.jsonl")
    _run(["judge", "--input", "-"], stdin=_payload(_sig(external_integration="true"), "T-C"), ledger=ledger3)
    with open(ledger3, "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "level_change", "task_id": "T-C", "level": "L1-2"}) + "\n")
    rc, out, err = _run(["verify", "--task-id", "T-C"], ledger=ledger3)
    check("GT-8b 미지 레코드 type → 게이트 fail", rc == V.EXIT_GATE)

    # reclassify 자체가 무효 재분류(승인 부재)를 거부(fail-closed 기록 거부)
    rc, out, err = _run(["reclassify", "--task-id", "T-A", "--from-level", "L4", "--to-level", "L1-2",
                        "--approval-id", "", "--reason-code", "RC-02",
                        "--machine-evidence", "x"], ledger=ledger)
    check("재분류 무효(승인 부재) → 거부(rc=5)", rc == V.EXIT_RECLASS, "rc=%s" % rc)

    # 격하인데 기계증거 결여 → 거부
    rc, out, err = _run(["reclassify", "--task-id", "T-A", "--from-level", "L4", "--to-level", "L1-2",
                        "--approval-id", "APR-20260718-002", "--reason-code", "RC-02"], ledger=ledger)
    check("격하 기계증거 결여 → 거부(rc=5)", rc == V.EXIT_RECLASS, "rc=%s" % rc)

    # RC-01(격상 전용)을 격하에 사용 → 방향 불일치 거부
    rc, out, err = _run(["reclassify", "--task-id", "T-A", "--from-level", "L4", "--to-level", "L1-2",
                        "--approval-id", "APR-20260718-003", "--reason-code", "RC-01"], ledger=ledger)
    check("RC-01 방향 불일치(격하에 사용) → 거부", rc == V.EXIT_RECLASS, "rc=%s" % rc)
    _assert_no_new(_s)


def test_forged_judgment():
    """B-1/M-6: verify가 judgment의 signals로 level·input_hash를 재계산해 위조를 잡는지.
    기록된 level을 신뢰만 하던 사각(GT-8은 reclassification 위조만 커버)을 닫는다."""
    _s = len(fails)
    tmp = tempfile.mkdtemp()
    all_true = {k: {"value": "true", "evidence": ""} for k in V.SIGNAL_KEYS}  # 정답 L5
    base = {"type": "judgment", "task_id": "T-F", "input_hash": V.compute_input_hash(all_true),
            "signals": all_true, "normalized": V.normalize(all_true), "unknown_count": 0,
            "needs_grill": False, "level": "L5", "at": "x"}

    # B-1 공격: signals=전부 true(=L5)인데 level만 "L1-2"로 위조한 judgment 한 줄
    lg1 = os.path.join(tmp, "forge_level.jsonl")
    with open(lg1, "w", encoding="utf-8") as f:
        f.write(json.dumps({**base, "level": "L1-2"}, ensure_ascii=False) + "\n")
    rc, out, err = _run(["verify", "--task-id", "T-F"], ledger=lg1)
    v = json.loads(err) if rc != 0 else json.loads(out)
    check("B-1 judgment level 위조(all-true→L1-2) → 게이트 fail(rc=6)",
          rc == V.EXIT_GATE and v.get("gate") == "fail",
          "rc=%s violations=%s" % (rc, v.get("violations")))
    check("B-1 재계산 effective=L5(위조 level 불신·진짜값 노출)",
          v.get("effective_level") == "L5", "effective=%s" % v.get("effective_level"))

    # M-6 공격: level은 맞지만 input_hash를 signals와 불일치하게 위조
    lg2 = os.path.join(tmp, "forge_hash.jsonl")
    with open(lg2, "w", encoding="utf-8") as f:
        f.write(json.dumps({**base, "input_hash": "deadbeef"}, ensure_ascii=False) + "\n")
    rc, out, err = _run(["verify", "--task-id", "T-F"], ledger=lg2)
    check("M-6 input_hash 위조(signals 불일치) → 게이트 fail(rc=6)", rc == V.EXIT_GATE,
          "rc=%s" % rc)

    # M-6b: input_hash 필드 제거(재검증 우회 시도) → 부재도 위반
    lg3 = os.path.join(tmp, "forge_nohash.jsonl")
    nohash = {k: base[k] for k in base if k != "input_hash"}
    with open(lg3, "w", encoding="utf-8") as f:
        f.write(json.dumps(nohash, ensure_ascii=False) + "\n")
    rc, out, err = _run(["verify", "--task-id", "T-F"], ledger=lg3)
    check("M-6b input_hash 부재 → 게이트 fail(rc=6)", rc == V.EXIT_GATE, "rc=%s" % rc)

    # 회귀: 정상 judgment(재계산·해시 일치)는 pass 유지
    lg4 = os.path.join(tmp, "legit.jsonl")
    _run(["judge", "--input", "-"], stdin=_payload(all_true, "T-G"), ledger=lg4)
    rc, out, err = _run(["verify", "--task-id", "T-G"], ledger=lg4)
    check("정상 judgment 재계산 일치 → pass 유지(회귀 방지)",
          rc == 0 and json.loads(out).get("effective_level") == "L5",
          "rc=%s out=%s" % (rc, out.strip()))
    _assert_no_new(_s)


def test_vibecheck_mapping():
    """M-2: viberoute Level → vibecheck --level 매핑 + judge 출력에 vibecheck_level 포함."""
    _s = len(fails)
    check("매핑 L1-2→L1", V.to_vibecheck_level("L1-2") == "L1")
    check("매핑 L3/L4/L5 항등",
          V.to_vibecheck_level("L3") == "L3" and V.to_vibecheck_level("L4") == "L4"
          and V.to_vibecheck_level("L5") == "L5")
    check("매핑 밖 값→None(합성 파이프라인 판별)", V.to_vibecheck_level("L99") is None)
    # 전 산출 Level이 vibecheck LEVEL_DOCS 키(L1|L3|L4|L5)로만 매핑되는지 — 어휘 통일 전칭
    valid = {"L1", "L3", "L4", "L5"}
    check("전 Level 매핑값이 vibecheck 인자 집합 내",
          all(V.to_vibecheck_level(lv) in valid for lv in V.LEVELS))
    # judge 출력에 vibecheck_level 필드 존재·정합
    rc, out, err = _run(["judge", "--input", "-"],
                        stdin=_payload(_sig(scale_modules="true"), "T-M"),
                        ledger=os.path.join(tempfile.mkdtemp(), "m.jsonl"))
    j = json.loads(out)
    check("judge 출력 vibecheck_level 정합(L3→L3)",
          j.get("level") == "L3" and j.get("vibecheck_level") == "L3", "out=%s" % out.strip())
    _assert_no_new(_s)


def test_fail_closed():
    """스키마 위반 = fail-closed(Level 미산출·exit 4). 의도된 실패 배터리."""
    _s = len(fails)
    good = _sig(persistent_data="true")
    cases = [
        ("신호 누락", {"signals": {k: good[k] for k in list(V.SIGNAL_KEYS)[:-1]}}),
        ("enum 밖 값", {"signals": {**good, "brownfield": {"value": "maybe", "evidence": ""}}}),
        ("미지 신호(스키마 밖)", {"signals": {**good, "rogue_signal": {"value": "true", "evidence": ""}}}),
        ("input_hash 불일치", {"signals": good, "input_hash": "deadbeef"}),
        ("루트 비객체", [1, 2, 3]),
        ("signals 비객체", {"signals": "not-a-dict"}),
        ("신호가 객체 아님", {"signals": {**good, "new_service": "true"}}),
    ]
    for name, payload in cases:
        rc, out, err = _run(["judge", "--input", "-"], stdin=json.dumps(payload, ensure_ascii=False))
        body = err or out
        try:
            parsed = json.loads(body)
            level_none = parsed.get("level") is None
        except ValueError:
            level_none = True
        check("fail-closed[%s] → rc=4·Level 미산출" % name,
              rc == V.EXIT_FAILCLOSED and level_none, "rc=%s body=%s" % (rc, body.strip()[:120]))
    # 파싱 실패는 exit 3
    rc, out, err = _run(["judge", "--input", "-"], stdin="{not json")
    check("fail-closed[JSON 파싱 실패] → rc=3", rc == V.EXIT_PARSE, "rc=%s" % rc)
    _assert_no_new(_s)


def main():
    # 직접 실행: 전 케이스 수집 후 요약(집계). 각 test_의 말미 assert(pytest 실패 신호)는
    # try/except로 흡수 — check()가 이미 fails에 남겼으므로 아래 요약이 진짜 집계다.
    for fn in (test_64_totality, test_golden, test_ledger_paths,
               test_forged_judgment, test_vibecheck_mapping, test_fail_closed):
        try:
            fn()
        except AssertionError:
            pass
    print("\n" + "=" * 60)
    if fails:
        print("FAIL (%d):" % len(fails))
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("PASS: 64조합 전칭 + 정규화 729조합 + GT-1~20 + ledger 경로(GT-6/7/8) + "
          "B-1/M-6 judgment 위조 차단 + M-2 vibecheck 매핑 + fail-closed 전건 통과")


if __name__ == "__main__":
    main()
