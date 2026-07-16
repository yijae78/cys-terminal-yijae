#!/usr/bin/env python3
"""test_dept_doctrine_v1.py — 증분2 '부서 교리 기계'(D1 옵션 1') 통합(subprocess) 회귀.

순수 로직(티켓 TTL·자원 게이트 결정)은 javis_bootstrap `--self-test`가 밀폐 검증한다. 이 파일은
프로세스 경계가 필요한 부트 흐름을 핀한다(모듈 전역이 import 시 HOME/PACK로 고정):
  (h) 부서 레인 + 티켓 부재 → 팀 기동(④) 생략·exit 0·단독 각성 메시지(cys boot 미호출).
  (i) 부서 레인 + 유효 티켓 + 결손>0 → 팀 기동 경로 진입(cys boot 관측)·티켓 .used 소비.
  (j) 결손 0(재선언) → 자원 게이트 미호출(오탐 hard-block 방지)·티켓 미소비.
  (k) 자원 게이트 hard(servers) 목 → 팀 기동 0·exit 9·escalation 흔적(cys boot 미호출).
  (l) issue-ticket base 레인 전용 가드(부서 레인 거부).
  (m) javis_dept_migrate 멱등(2회 --fix 동일 결과·백업 생성).

관측 기법(증분1 test_lane_isolation_v1 계승): 격리 HOME + PATH 앞 목 cys(호출 로깅) + 목 팩
(mock orchestra·resource_gate)로 실행. exit code·boot-last.json·목 로그로 판정. 라이브 데몬 무접촉.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

BIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # cysjavis-pack/bin
BOOTSTRAP = os.path.join(BIN, "javis_bootstrap.py")
MIGRATE = os.path.join(BIN, "javis_dept_migrate.py")


def _write_exec(path, content):
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def _mock_cys(mockbin, cys_log, list_file):
    """목 cys — 모든 서브명령 exit 0(데몬 생존 재현) + 호출 args를 cys_log에 append.
    list는 list_file(존재 시)을 cat(결손 산출 제어 — cys list 라이브 노드 수), 그 외는 무출력."""
    _write_exec(os.path.join(mockbin, "cys"),
                '#!/bin/bash\n'
                'echo "$@" >> "%s" 2>/dev/null\n'
                'case "$1" in\n'
                '  surface-role) echo ""; exit 0;;\n'
                '  list) [ -f "%s" ] && cat "%s"; exit 0;;\n'
                '  *) exit 0;;\n'
                'esac\n' % (cys_log, list_file, list_file))


def _node_list(n):
    """cys list 형식(ref\\trole=..\\tpid=..\\texited=false\\t..) 노드 surface n줄 생성(결손 0 재현)."""
    roles = ["cso", "worker", "reviewer-gemini", "reviewer-codex", "reviewer-grok"]
    return "".join("surface:%d\trole=%s\tpid=%d\texited=false\t\t\n"
                   % (i, roles[i % len(roles)], 100 + i) for i in range(n))


def _mock_pack(pack, orch_check_exit=1, gate_exit=0, gate_json="",
               orch_log=None, gate_log=None):
    """목 팩(bin/javis_orchestra.py·javis_resource_gate.py) — exit·출력을 인자로 고정."""
    binp = os.path.join(pack, "bin")
    os.makedirs(binp, exist_ok=True)
    _write_exec(os.path.join(binp, "javis_orchestra.py"),
                '#!/usr/bin/env python3\n'
                'import os,sys\n'
                'cmd = sys.argv[1] if len(sys.argv)>1 else ""\n'
                'log = %r\n'
                'if log: open(log,"a").write(cmd+"\\n")\n'
                'if cmd=="check": sys.exit(%d)\n'
                'sys.exit(0)\n' % (orch_log, orch_check_exit))
    _write_exec(os.path.join(binp, "javis_resource_gate.py"),
                '#!/usr/bin/env python3\n'
                'import sys\n'
                'log = %r\n'
                'if log: open(log,"a").write(" ".join(sys.argv[1:])+"\\n")\n'
                'out = %r\n'
                'if out: print(out)\n'
                'sys.exit(%d)\n' % (gate_log, gate_json, gate_exit))


def _run_bootstrap(home, pack, mockbin, socket=None):
    env = dict(os.environ)
    env["HOME"] = home
    env["CYS_PACK_DIR"] = pack
    env["PATH"] = mockbin + os.pathsep + env.get("PATH", "")
    if socket is None:
        env.pop("CYS_SOCKET", None)
    else:
        env["CYS_SOCKET"] = socket
    # 부트 check 재시도 상한을 짧게(테스트 속도·⑤가 목 orchestra라 즉시 확정)
    env["CYS_BOOT_CHECK_RETRIES"] = "1"
    env["CYS_BOOT_CHECK_INTERVAL_S"] = "0"
    r = subprocess.run([sys.executable, BOOTSTRAP, "run"],
                       capture_output=True, text=True, timeout=60, env=env)
    bl = os.path.join(home, ".cys", "state", "boot-last.json")
    data = json.load(open(bl, encoding="utf-8")) if os.path.isfile(bl) else None
    return r.returncode, data


def _steps(data):
    return [s["step"] for s in (data or {}).get("steps", [])]


class DeptTicketGate(unittest.TestCase):
    def _setup(self, name="dept-1", orch_check_exit=0, gate_exit=0, gate_json="",
               ticket=None, live_nodes=0):
        home = tempfile.mkdtemp()
        pack = os.path.join(home, ".cys", "pack-dept-%s" % name)  # 레인↔팩 정합(부서)
        mockbin = tempfile.mkdtemp()
        self.cys_log = os.path.join(home, "cys-calls.log")
        self.gate_log = os.path.join(home, "gate-calls.log")
        self.list_file = os.path.join(home, "cys-list.txt")
        with open(self.list_file, "w") as f:
            f.write(_node_list(live_nodes))   # live_nodes>=4 → 결손 0
        _mock_cys(mockbin, self.cys_log, self.list_file)
        _mock_pack(pack, orch_check_exit=orch_check_exit, gate_exit=gate_exit,
                   gate_json=gate_json, gate_log=self.gate_log)
        if ticket is not None:
            tdir = os.path.join(home, ".cys", "state", "dept-boot-tickets")
            os.makedirs(tdir, exist_ok=True)
            with open(os.path.join(tdir, "%s.ticket" % name), "w") as f:
                json.dump(ticket, f)
        sock = "%s/.local/state/cys-dept-%s/cys.sock" % (home, name)
        self.home, self.pack, self.mockbin, self.sock, self.name = home, pack, mockbin, sock, name
        return home, pack, mockbin, sock

    def _cys_called(self, sub):
        if not os.path.isfile(self.cys_log):
            return False
        return any(line.split()[0:1] == [sub] for line in open(self.cys_log))

    # (h) 부서 레인 + 티켓 부재 → 단독 각성(팀 기동 생략·exit 0)
    def test_h_dept_no_ticket_solo_awakening(self):
        home, pack, mockbin, sock = self._setup(ticket=None)
        rc, data = _run_bootstrap(home, pack, mockbin, socket=sock)
        self.assertEqual(rc, 0, "티켓 부재 부서 레인인데 exit≠0(단독 각성 강등 실패)")
        self.assertIn("③″ceo-ticket", _steps(data))
        self.assertNotIn("④boot", _steps(data), "티켓 부재인데 팀 기동 단계 진입")
        self.assertTrue((data.get("result") or {}).get("solo_awakening"),
                        "solo_awakening 미표기")
        self.assertFalse(self._cys_called("boot"), "티켓 부재인데 cys boot 호출됨")

    # (i) 부서 레인 + 유효 티켓 + 결손>0 → 팀 기동 진입·티켓 소비
    def test_i_dept_valid_ticket_boots_and_consumes(self):
        ticket = {"dept": "dept-1", "issued_at": time.time(), "issuer": "base-master"}
        # live_nodes=0 → 결손>0 → 게이트 발동(gate_exit=0 allow) → 티켓 소비 → ④boot → ⑤(orch 0) 통과.
        home, pack, mockbin, sock = self._setup(orch_check_exit=0, gate_exit=0,
                                                ticket=ticket, live_nodes=0)
        rc, data = _run_bootstrap(home, pack, mockbin, socket=sock)
        self.assertIn("③″ceo-ticket-consume", _steps(data), "티켓 소비 단계 부재(팀 기동 미진입)")
        self.assertTrue(self._cys_called("boot"), "유효 티켓인데 cys boot 미호출(팀 기동 미진입)")
        tdir = os.path.join(home, ".cys", "state", "dept-boot-tickets")
        self.assertFalse(os.path.exists(os.path.join(tdir, "dept-1.ticket")), "티켓 미소비(잔존)")
        self.assertTrue(os.path.exists(os.path.join(tdir, "dept-1.ticket.used")), ".used 미생성")

    # (j) 결손 0(재선언) → 자원 게이트 미호출·티켓 미소비
    def test_j_no_deficit_skips_gate_and_keeps_ticket(self):
        ticket = {"dept": "dept-1", "issued_at": time.time(), "issuer": "base-master"}
        # live_nodes=4(의무 수) → 결손 0 → 게이트 생략·티켓 미소비.
        home, pack, mockbin, sock = self._setup(orch_check_exit=0, ticket=ticket, live_nodes=4)
        rc, data = _run_bootstrap(home, pack, mockbin, socket=sock)
        self.assertEqual(rc, 0, "결손 0 재선언인데 exit≠0")
        self.assertFalse(os.path.isfile(self.gate_log), "결손 0인데 자원 게이트 호출됨(오탐 위험)")
        gate_step = [s for s in (data or {}).get("steps", []) if s["step"] == "④′resource-gate"]
        self.assertTrue(gate_step and "결손 0" in gate_step[0]["detail"], "게이트 생략 흔적 부재")
        tdir = os.path.join(home, ".cys", "state", "dept-boot-tickets")
        self.assertTrue(os.path.exists(os.path.join(tdir, "dept-1.ticket")),
                        "결손 0 재선언인데 티켓 소비됨(재사용 불가)")
        self.assertNotIn("③″ceo-ticket-consume", _steps(data), "결손 0인데 티켓 소비 단계 발생")

    # (k) 자원 게이트 hard(servers) → 팀 기동 0·exit 9·escalation
    def test_k_resource_hard_blocks_boot_exit9(self):
        gate_json = json.dumps({"verdict": "hard_block",
                                "trips": [{"metric": "servers", "level": "hard", "value": 5}],
                                "measured": {"nodes_hard_effective": 18}})
        # base 레인으로 격리(티켓 게이트 무관) — 결손>0(라이브 노드 0) → 게이트 hard(gate exit 2)
        home = tempfile.mkdtemp()
        pack = os.path.join(home, ".cys", "pack")  # base 레인 ↔ 메인 팩(정합)
        mockbin = tempfile.mkdtemp()
        self.cys_log = os.path.join(home, "cys-calls.log")
        self.gate_log = os.path.join(home, "gate-calls.log")
        list_file = os.path.join(home, "cys-list.txt")
        open(list_file, "w").close()   # 빈 목록 → 라이브 노드 0 → 결손>0
        _mock_cys(mockbin, self.cys_log, list_file)
        _mock_pack(pack, orch_check_exit=1, gate_exit=2, gate_json=gate_json,
                   gate_log=self.gate_log)
        rc, data = _run_bootstrap(home, pack, mockbin, socket=None)  # base
        self.assertEqual(rc, 9, "자원 hard인데 exit≠9(hard-block 미발동)")
        self.assertEqual((data.get("result") or {}).get("failed_step"), "resource-gate")
        self.assertNotIn("④boot", _steps(data), "hard-block 후에도 팀 기동으로 진행")
        self.assertIn("④′resource-gate-notify", _steps(data), "CEO escalation 알림 흔적 부재")
        self.assertFalse(any(line.split()[0:1] == ["boot"] for line in open(self.cys_log)),
                         "hard-block인데 cys boot 호출됨")


class IssueTicketGuard(unittest.TestCase):
    # (l) issue-ticket base 전용 가드
    def test_l_issue_ticket_base_only(self):
        home = tempfile.mkdtemp()
        env = dict(os.environ)
        env["HOME"] = home
        # base 레인: 발급 성공
        env.pop("CYS_SOCKET", None)
        r = subprocess.run([sys.executable, BOOTSTRAP, "issue-ticket", "--dept", "dept-1"],
                           capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(r.returncode, 0, "base 레인 발급 실패:\n%s" % r.stderr)
        tpath = os.path.join(home, ".cys", "state", "dept-boot-tickets", "dept-1.ticket")
        self.assertTrue(os.path.isfile(tpath), "티켓 파일 미생성")
        # 부서 레인: 발급 거부
        env["CYS_SOCKET"] = "%s/.local/state/cys-dept-dept-2/cys.sock" % home
        r2 = subprocess.run([sys.executable, BOOTSTRAP, "issue-ticket", "--dept", "dept-2"],
                            capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(r2.returncode, 2, "부서 레인 발급이 거부되지 않음")
        self.assertFalse(os.path.exists(os.path.join(
            home, ".cys", "state", "dept-boot-tickets", "dept-2.ticket")), "거부인데 티켓 생성됨")


class MigrateIdempotent(unittest.TestCase):
    # (m) javis_dept_migrate 멱등(2회 --fix 동일 결과·백업 생성)
    def test_m_migrate_idempotent(self):
        home = tempfile.mkdtemp()
        # 메인 팩(소스) — 훅·부트스트랩 실체
        main_pack = os.path.join(home, ".cys", "pack")
        os.makedirs(os.path.join(main_pack, "hooks"), exist_ok=True)
        os.makedirs(os.path.join(main_pack, "bin"), exist_ok=True)
        _write_exec(os.path.join(main_pack, "hooks", "role-bootstrap.sh"), "#!/bin/bash\nexit 0\n")
        _write_exec(os.path.join(main_pack, "bin", "javis_bootstrap.py"), "#!/usr/bin/env python3\n")
        # 기존 부서 config(UserPromptSubmit 부재 — 풀 세트 중 SessionStart만 있는 상태 재현)
        acctdir = os.path.join(home, ".cys", "claude-default-dept-1")
        os.makedirs(acctdir, exist_ok=True)
        settings = os.path.join(acctdir, "settings.json")
        with open(settings, "w") as f:
            json.dump({"hooks": {"SessionStart": [
                {"hooks": [{"type": "command", "command": "sh /x/hooks/session-start.sh"}]}]}}, f)
        # 부서 팩(훅 부재 — 복사 대상)
        dept_pack = os.path.join(home, ".cys", "pack-dept-dept-1")
        os.makedirs(dept_pack, exist_ok=True)

        env = dict(os.environ)
        env["HOME"] = home
        env["CYS_PACK_DIR"] = main_pack

        def run_fix():
            return subprocess.run([sys.executable, MIGRATE, "--fix", "--json"],
                                  capture_output=True, text=True, timeout=30, env=env)

        r1 = run_fix()
        self.assertEqual(r1.returncode, 0, "1차 --fix 실패:\n%s" % r1.stderr)
        content1 = open(settings, encoding="utf-8").read()
        self.assertIn("UserPromptSubmit", content1, "UserPromptSubmit 미등록")
        self.assertIn("role-bootstrap.sh", content1, "role-bootstrap.sh 명령 미등록")
        self.assertTrue(os.path.isfile(settings + ".bak-migrate"), "백업 미생성")
        self.assertTrue(os.path.isfile(os.path.join(dept_pack, "hooks", "role-bootstrap.sh")),
                        "부서 팩에 훅 미복사")
        self.assertTrue(os.path.isfile(os.path.join(dept_pack, "bin", "javis_bootstrap.py")),
                        "부서 팩에 부트스트랩 미복사")

        r2 = run_fix()
        self.assertEqual(r2.returncode, 0, "2차 --fix 실패")
        content2 = open(settings, encoding="utf-8").read()
        self.assertEqual(content1, content2, "멱등 위반 — 2차 실행이 settings.json을 변경(중복 등록 등)")
        # 2차 dry-run: 모두 ok(이미 등록·존재)
        r3 = subprocess.run([sys.executable, MIGRATE, "--json"],
                            capture_output=True, text=True, timeout=30, env=env)
        rep = json.loads(r3.stdout)
        d = rep["depts"][0]
        self.assertEqual(d["hook"]["action"], "ok", "멱등 상태인데 hook action≠ok: %s" % d["hook"])
        self.assertTrue(all(pf["action"] == "ok" for pf in d["pack_files"]),
                        "멱등 상태인데 pack_files action≠ok")


if __name__ == "__main__":
    unittest.main()
