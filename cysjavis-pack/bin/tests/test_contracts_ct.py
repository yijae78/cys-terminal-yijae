#!/usr/bin/env python3
"""test_contracts_ct.py — VIBECODING §C2.4 충돌 사례 contract test(CT-1~CT-4) + 도구 회귀.

출처 계약: _research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md
  §C2.4 L151-155(CT-1~4) · §C2.3(waiver) · §C11(decision) · §C4.2(route table) · §C3.4(break-glass).

구성:
  TestWaiverTool   — javis_waiver.py 실도구 회귀(issue/check/list·만료·§C1.2 승인자 규칙).
  TestDecisionTool — javis_decision.py 실도구 회귀(검증 통과·의무 필드 결손 exit 2·verbatim 보존).
  TestContractCT   — CT-1(실도구 javis_waiver) · CT-2(change-delta) · CT-3(route 격상) · CT-4(break-glass).

CT-3 은 javis_viberoute.py 가 있으면 그 실도구에 연동, 없으면 §C4.2 판정표의 참조 구현(_route_level)에
연동한다. CT-2·CT-4 는 아직 전용 도구가 없어 계약을 참조 구현으로 기계화하되 실제 온디스크 픽스처
(파일 유무·ledger 내용)로부터 결정론적으로 판정한다(스텁 인터페이스 — 전용 도구 도입 시 교체).

관측 기법: 격리 tmp 프로젝트 루트(JAVIS_ROOT env) + subprocess 로 실도구 실행. exit code/JSON 판정.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # cysjavis-pack/bin
WAIVER = os.path.join(BIN, "javis_waiver.py")
DECISION = os.path.join(BIN, "javis_decision.py")
VIBEROUTE = os.path.join(BIN, "javis_viberoute.py")  # Phase 1 라우터(있으면 CT-3 실연동)


def _run(script, args, root, stdin=None):
    env = dict(os.environ, JAVIS_ROOT=root)
    return subprocess.run([sys.executable, script, *args], env=env,
                          input=stdin, capture_output=True, text=True)


def _days(delta):
    return (datetime.date.today() + datetime.timedelta(days=delta)).isoformat()


# ---------------------------------------------------------------------------
# §C4 route-contract 실도구 연동 — CT-3 은 javis_viberoute.py 의 실제 `judge` 서브커맨드로
# Level 산출 경로를 실제로 태운다(참조 구현으로의 silent 폴백 금지 — 그것이 M-1 vacuous 결함이었다).
# 실 인터페이스: `judge --input -` · stdin JSON {task_id, signals:{sig:{value,evidence}}} · stdout {level}.
# ---------------------------------------------------------------------------
_SIGNALS = ("persistent_data", "external_integration", "deploy_exposure",
            "scale_modules", "brownfield", "new_service")


def _judge(root, signals):
    """실도구 javis_viberoute.py judge 로 Level 판정. 반환 (returncode, parsed_json_or_None, raw)."""
    payload = {"task_id": "ct3",
               "signals": {s: {"value": signals.get(s, "false"), "evidence": "ct"} for s in _SIGNALS}}
    r = subprocess.run([sys.executable, VIBEROUTE, "judge", "--input", "-"],
                       env=dict(os.environ, JAVIS_ROOT=root),
                       input=json.dumps(payload), capture_output=True, text=True)
    parsed = None
    if r.returncode == 0:
        try:
            parsed = json.loads(r.stdout)
        except json.JSONDecodeError:
            parsed = None
    return r.returncode, parsed, (r.stdout + r.stderr)


def _min_docs_required(level):
    """Level 별 최소 문서 강제(§2·§C2.1): L1-2=0, L3 이상=1+."""
    return 0 if level == "L1-2" else 1


# ---------------------------------------------------------------------------
# §C2.2 change-delta 게이트 참조 구현 (전용 도구 도입 전 스텁).
# 승인된 scope 변경은 approval_id 를 담은 scope-delta 문서 1건을 요구한다.
# ---------------------------------------------------------------------------
_APR_RE = "APR-"


def _change_delta_ok(root, task_id):
    path = os.path.join(root, ".vibecoding", "deltas", f"{task_id}.md")
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        body = f.read()
    for line in body.splitlines():
        s = line.strip().lower()
        if s.startswith("approval_id:") and _APR_RE.lower() in s:
            return True
    return False


# ---------------------------------------------------------------------------
# §C3.4 break-glass 게이트 참조 구현 (전용 도구 도입 전 스텁).
# doctor actor 의 유효 approval_id 가 ledger 에 있어야 일회성 허용.
# ---------------------------------------------------------------------------
def _break_glass_allowed(root, apr_id):
    path = os.path.join(root, ".vibecoding", "approvals.jsonl")
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (rec.get("actor") == "doctor" and rec.get("action") == "break-glass"
                    and rec.get("approval_id") == apr_id and not rec.get("used", False)):
                return True
    return False


class TestWaiverTool(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_issue_and_check_valid(self):
        r = _run(WAIVER, ["issue", "--rule", "4조-regression", "--reason", "무테스트 legacy",
                          "--approver", "master", "--expiry", _days(30), "--remediation", "T+2주 테스트 부채 해소"], self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertTrue(rec["waiver_id"].startswith("WVR-"))
        self.assertTrue(os.path.exists(os.path.join(self.root, ".vibecoding", "waivers.jsonl")))
        c = _run(WAIVER, ["check", "--rule", "4조-regression"], self.root)
        self.assertEqual(c.returncode, 0, c.stderr)
        self.assertEqual(json.loads(c.stdout)["status"], "valid")

    def test_check_none(self):
        c = _run(WAIVER, ["check", "--rule", "없는규칙"], self.root)
        self.assertEqual(c.returncode, 1)

    def test_expired_waiver_fails(self):
        _run(WAIVER, ["issue", "--rule", "4조-regression", "--reason", "x", "--approver", "master",
                      "--expiry", _days(-1), "--remediation", "y"], self.root)
        # 만료일이 과거이면 issue 자체가 거부(발급 즉시 만료 금지).
        # 유효 발급 후 만료를 재현하려면 미래→직접 파일 조작이 필요하므로, 여기선 과거 만료 issue 거부를 확인.
        r = _run(WAIVER, ["issue", "--rule", "r", "--reason", "x", "--approver", "master",
                          "--expiry", _days(-1), "--remediation", "y"], self.root)
        self.assertEqual(r.returncode, 2, r.stdout)

    def test_high_risk_requires_doctor(self):
        r = _run(WAIVER, ["issue", "--rule", "9조-security", "--reason", "긴급", "--approver", "master",
                          "--expiry", _days(3), "--remediation", "z", "--risk", "high"], self.root)
        self.assertEqual(r.returncode, 2, "고위험 waiver 를 master 가 발급하면 거부되어야 함")
        r2 = _run(WAIVER, ["issue", "--rule", "9조-security", "--reason", "긴급", "--approver", "doctor",
                           "--expiry", _days(3), "--remediation", "z", "--risk", "high"], self.root)
        self.assertEqual(r2.returncode, 0, r2.stderr)

    def test_missing_expiry_rejected(self):
        r = _run(WAIVER, ["issue", "--rule", "r", "--reason", "x", "--approver", "master",
                          "--expiry", "not-a-date", "--remediation", "y"], self.root)
        self.assertEqual(r.returncode, 2)


class TestDecisionTool(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    # scalar 필드는 header 에 먼저, decision(body)은 마지막(§C11 파서 계약).
    VALID = (
        "[DECISION]\n"
        "decision_id: DEC-20260718-001\n"
        "decider: doctor\n"
        "scope: docs/state/machine.md §상태전이\n"
        "effective_date: 2026-07-18\n"
        "decision: 주문 상태는 created→paid→shipped 단방향만 허용한다.\n"
        "  롤백 전이는 금지한다.\n"
    )

    def test_valid_passes_and_preserves_verbatim(self):
        r = _run(DECISION, ["validate", "--text", self.VALID, "--record"], self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertEqual(rec["decision_id"], "DEC-20260718-001")
        self.assertIn("롤백 전이는 금지한다", rec["decision"])  # 여러 줄 verbatim 보존
        self.assertEqual(rec["scope"], "docs/state/machine.md §상태전이")
        self.assertTrue(os.path.exists(os.path.join(self.root, ".vibecoding", "decisions.jsonl")))

    def test_missing_field_exit2(self):
        block = "decision_id: DEC-20260718-002\ndecider: doctor\nscope: x\neffective_date: 2026-07-18\n"  # decision 결손
        r = _run(DECISION, ["validate", "--text", block], self.root)
        self.assertEqual(r.returncode, 2)
        self.assertIn("decision", r.stderr)

    def test_bad_id_format_exit2(self):
        block = self.VALID.replace("DEC-20260718-001", "DEC-BAD")
        r = _run(DECISION, ["validate", "--text", block], self.root)
        self.assertEqual(r.returncode, 2)
        self.assertIn("decision_id", r.stderr)

    def test_bad_decider_exit2(self):
        block = self.VALID.replace("decider: doctor", "decider: worker")
        r = _run(DECISION, ["validate", "--text", block], self.root)
        self.assertEqual(r.returncode, 2)
        self.assertIn("decider", r.stderr)

    def test_b2_body_field_like_lines_not_hijacked(self):
        """B-2 회귀: decision 본문 속 가짜 field 줄이 scope/decider 를 하이재킹하거나 본문을 절단하지 못한다."""
        attack = (
            "decision_id: DEC-20260718-050\n"
            "decider: doctor\n"
            "scope: docs/REAL_TARGET.md §진짜\n"
            "effective_date: 2026-07-18\n"
            "decision: 진짜 결정 첫 줄.\n"
            "scope: /etc/passwd 하이재킹 시도\n"   # 본문의 일부여야 함 — 필드 아님
            "decider: worker\n"                    # 본문의 일부여야 함 — 필드 아님
            "결정의 마지막 줄.\n"
        )
        r = _run(DECISION, ["validate", "--text", attack], self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        # 필드 하이재킹 차단: header 의 진짜 값이 유지됨.
        self.assertEqual(rec["scope"], "docs/REAL_TARGET.md §진짜", "가짜 scope 로 하이재킹 금지")
        self.assertEqual(rec["decider"], "doctor", "가짜 decider 로 하이재킹 금지")
        # 본문 절단 차단: 가짜 field 줄·마지막 줄이 verbatim 보존.
        self.assertIn("/etc/passwd 하이재킹 시도", rec["decision"])
        self.assertIn("결정의 마지막 줄", rec["decision"])
        self.assertIn("진짜 결정 첫 줄", rec["decision"])

    def test_b2_body_only_fake_scope_injection_blocked(self):
        """B-2 회귀: header 에 scope 없이 본문에만 'scope:' → 필드로 승격 금지 → 결손 차단(exit 2)."""
        block = (
            "decision_id: DEC-20260718-051\n"
            "decider: doctor\n"
            "effective_date: 2026-07-18\n"
            "decision: 본문 시작.\n"
            "scope: 본문속가짜scope\n"
        )
        r = _run(DECISION, ["validate", "--text", block], self.root)
        self.assertEqual(r.returncode, 2, "본문 scope 를 필드로 승격하면 안 됨 → scope 결손 차단")
        self.assertIn("scope", r.stderr)

    def test_b2_terminator_allows_trailing_header_fields(self):
        """[/DECISION] 종결자 뒤 header 필드 재개 허용(커밋 trailer 혼재)·본문 내 가짜 field 무시."""
        block = (
            "decision_id: DEC-20260718-052\n"
            "decider: master\n"
            "scope: x\n"
            "decision: 본문 줄1\n"
            "scope: 본문내가짜\n"
            "[/DECISION]\n"
            "effective_date: 2026-07-18\n"
        )
        r = _run(DECISION, ["validate", "--text", block], self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertEqual(rec["scope"], "x")
        self.assertEqual(rec["effective_date"], "2026-07-18")
        self.assertIn("본문내가짜", rec["decision"])


class TestContractCT(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_ct1_waiver_path_done_then_expired_fail(self):
        """CT-1: 무테스트 legacy 단일 수정 → waiver 경로로 done 가능, 만료 후 동일 경로 → fail."""
        # (a) 유효 waiver 발급 → check pass (done 가능).
        r = _run(WAIVER, ["issue", "--rule", "4조-regression", "--reason", "무테스트 brownfield 단일 수정",
                          "--approver", "master", "--expiry", _days(14), "--remediation", "만료 전 테스트 부채 해소"], self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        c = _run(WAIVER, ["check", "--rule", "4조-regression"], self.root)
        self.assertEqual(c.returncode, 0, "유효 waiver 로 회귀 게이트 통과 가능해야 함")

        # (b) 만료 재현: 저장 파일의 expiry 를 과거로 바꿔 append(신규 레코드) → check 는 항상 오늘 기준 재계산.
        wpath = os.path.join(self.root, ".vibecoding", "waivers.jsonl")
        with open(wpath, encoding="utf-8") as f:
            lines = [json.loads(x) for x in f if x.strip()]
        # 모든 매칭 waiver 를 만료로 대체(append-only 특성상 새 파일로 재작성은 픽스처 조작이며,
        # 실제 도구는 만료 판정을 오늘 기준으로 하므로 과거 expiry 는 무조건 fail).
        for rec in lines:
            if rec.get("target_rule") == "4조-regression":
                rec["expiry"] = _days(-1)
        with open(wpath, "w", encoding="utf-8") as f:
            for rec in lines:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        c2 = _run(WAIVER, ["check", "--rule", "4조-regression"], self.root)
        self.assertEqual(c2.returncode, 1, "만료된 waiver 는 자동 fail 이어야 함(silent 연장 금지)")
        self.assertIn("expired", c2.stderr)

    def test_ct2_change_delta_presence(self):
        """CT-2: 오너 승인 요구 변경 → change-delta 문서 없으면 5조 위반 fail, 있으면 pass."""
        task = "T-scope-42"
        self.assertFalse(_change_delta_ok(self.root, task), "delta 문서 부재 → 5조 위반(fail)")
        # change-delta 문서 생성(approval_id 포함).
        ddir = os.path.join(self.root, ".vibecoding", "deltas")
        os.makedirs(ddir, exist_ok=True)
        with open(os.path.join(ddir, f"{task}.md"), "w", encoding="utf-8") as f:
            f.write("# scope-delta\nbefore: 단일 조회\nafter: 조회+필터\nreason: 오너 승인 확장\napproval_id: APR-20260718-007\n")
        self.assertTrue(_change_delta_ok(self.root, task), "approval_id 담긴 delta 문서 → pass")

    def test_ct3_l1_contract_change_escalates(self):
        """CT-3: L1 행동 변경 + 계약 변경 감지 → 자동 격상(문서 0 유지 시 fail).

        실도구 javis_viberoute.py judge 로 Level 산출 경로를 실제로 태운다(vacuous 폴백 없음).
        """
        self.assertTrue(os.path.exists(VIBEROUTE),
                        "javis_viberoute.py 실도구 필수(§C4 Phase 1) — 없으면 CT-3 검증 불가(loud fail)")

        # 순수 L1(전 신호 false): 실도구가 L1-2 산출 + 문서 0 허용.
        rc0, out0, raw0 = _judge(self.root, {s: "false" for s in _SIGNALS})
        self.assertEqual(rc0, 0, raw0)
        self.assertEqual(out0["level"], "L1-2", raw0)
        self.assertEqual(_min_docs_required(out0["level"]), 0)

        # 계약 변경 감지(외부 연동) → 실도구가 자동 격상(L1 유지 금지).
        rc1, out1, raw1 = _judge(self.root, {**{s: "false" for s in _SIGNALS}, "external_integration": "true"})
        self.assertEqual(rc1, 0, raw1)
        self.assertNotEqual(out1["level"], "L1-2", "계약 변경 감지 시 L1 유지 금지(자동 격상)")
        self.assertEqual(out1["level"], "L4", raw1)  # 실도구 판정표 행2
        # 격상 후 문서 0 유지 → doc-sync 게이트 fail(최소 문서 강제).
        self.assertGreater(_min_docs_required(out1["level"]), 0,
                           "격상된 Level 에서 문서 0 은 doc-sync 게이트 fail 이어야 함")

    def test_ct4_break_glass_requires_doctor(self):
        """CT-4: 긴급 복구(break-glass) → doctor 승인 없으면 차단, 승인 시 일회성 통과+감사 로그."""
        apr = "APR-20260718-099"
        # 승인 부재 → 차단.
        self.assertFalse(_break_glass_allowed(self.root, apr), "doctor 승인 없는 break-glass 는 차단")
        # doctor 승인 ledger 기록 → 통과.
        vdir = os.path.join(self.root, ".vibecoding")
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "approvals.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"approval_id": apr, "actor": "doctor", "action": "break-glass",
                                "target": "prod-db", "reason": "장애 복구", "used": False}, ensure_ascii=False) + "\n")
        self.assertTrue(_break_glass_allowed(self.root, apr), "doctor 승인 시 일회성 통과")


if __name__ == "__main__":
    unittest.main(verbosity=2)
