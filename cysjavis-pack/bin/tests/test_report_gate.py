#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_report_gate.py — javis_report_gate.py + javis_gate_check.py 회귀.

DESIGN §C1 필수 케이스 10종을 Gate 코어에 대역 Runner를 주입해 핀한다(서버·데몬 기동 0).
외부 명령(javis_report/event/wakeup·cys)은 전부 FakeRunner로 대체 — 호출 여부·인자를 기록해
"배달 체인 완결(enqueue+drain)"·"emit 거부 폴백"·"fail-open 직송" 등 부작용을 검증한다.

실행: python3 test_report_gate.py   (unittest·표준 러너 — CI가 파일 직접 실행하는 관례 준거)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # cysjavis-pack/bin
sys.path.insert(0, BIN)
import javis_report_gate as G                                             # noqa: E402


def report(nodes=None, live_nodes=None, idle_nodes=None, feed=None,
           status_available=True, **extra):
    """javis_report.py --json 형태의 report 픽스처."""
    r = {
        "overall_pct": 0, "overall_done": 0, "overall_total": 0,
        "nodes": nodes or [], "live_nodes": live_nodes or [],
        "idle_nodes": idle_nodes or [], "feed_pending": feed,
        "paused": None, "status_available": status_available,
    }
    r.update(extra)
    return r


class FakeRunner:
    def __init__(self, report_ok=True, rep=None, err=None, emit_rc=0,
                 drain_delivered=1, collect_raises=False, enqueue_rc=0):
        self.report_ok, self.rep, self.err = report_ok, rep, err
        self.emit_rc, self.drain_delivered = emit_rc, drain_delivered
        self.collect_raises = collect_raises
        self.enqueue_rc = enqueue_rc            # enqueue 실패 주입(T21 원자성 검증용)
        self.emits, self.enqueues, self.drains, self.sends = [], [], [], []
        self.collect_calls = 0

    def collect_report(self):
        self.collect_calls += 1
        if self.collect_raises:
            raise RuntimeError("주입된 내부 오류")
        return self.report_ok, self.rep, self.err

    def emit(self, evt_type, fields, surface="auto"):
        self.emits.append((evt_type, fields))
        return self.emit_rc, "", ""

    def enqueue(self, to, task, reason, idem, payload=None):
        self.enqueues.append((to, task, reason, idem))
        return self.enqueue_rc

    def drain(self, target):
        self.drains.append(target)
        return 0, self.drain_delivered

    def send_queued(self, to, body):
        self.sends.append((to, body))
        return 0


class Clock:
    """주입 가능한 시계 — GAP·briefing 테스트용."""
    def __init__(self, epoch):
        self.epoch = epoch

    def now_epoch(self):
        return self.epoch

    def now_iso(self):
        return "2026-07-18T%02d:00:00+0900" % (int(self.epoch // 3600) % 24)


def gate(state_dir, runner, clock=None, stall_cycles=2, quiet_cycles=3, edge_cooldown=None):
    clk = clock or Clock(1_000_000.0)
    kw = {} if edge_cooldown is None else {"edge_cooldown": edge_cooldown}
    return G.Gate(state_dir, runner, cycle_minutes=5, stall_cycles=stall_cycles,
                  quiet_cycles=quiet_cycles,
                  now_epoch_fn=clk.now_epoch, now_iso_fn=clk.now_iso, **kw)


def ledger_entries(state_dir):
    path = os.path.join(state_dir, "ledger.jsonl")
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


class GateCore(unittest.TestCase):

    # ── ① BASELINE(스냅샷 부재) ──
    def test_baseline_records_no_delivery(self):
        with tempfile.TemporaryDirectory() as t:
            r = FakeRunner(rep=report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}]))
            gate(t, r).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "BASELINE")
            self.assertEqual(r.enqueues, [])
            self.assertEqual(r.emits, [])
            self.assertTrue(os.path.isfile(os.path.join(t, "last_snapshot.json")))

    # ── ② 무변화 → NOCHG / QUIET ──
    def test_no_change_in_progress_is_nochg(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}],
                         live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 10,
                                      "context_pct": 20}])
            r = FakeRunner(rep=rep)
            gate(t, r).run()                                  # baseline
            gate(t, r).run()                                  # 2nd = no change
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "NOCHG")
            self.assertEqual(r.enqueues, [])
            self.assertEqual(r.emits, [])

    def test_no_change_all_idle_no_work_is_quiet(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 3, "total": 3, "pct": 100}],
                         live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 600}],
                         idle_nodes=[{"role": "worker", "idle_secs": 600}])   # done이라 idle WARN 아님
            r = FakeRunner(rep=rep)
            gate(t, r).run()
            gate(t, r).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "QUIET")
            self.assertEqual(r.enqueues, [])

    # ── ③ 경고 주입 → WARN + 배달(enqueue+drain) 호출 ──
    def test_warning_triggers_wake_and_drain(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                         idle_nodes=[{"role": "worker", "idle_secs": 600}])
            r = FakeRunner(rep=rep)
            gate(t, r).run()                                  # baseline (no delivery)
            gate(t, r).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "WARN")
            self.assertEqual(len(r.enqueues), 1)
            self.assertEqual(r.enqueues[0][0], "master")
            self.assertEqual(r.drains, ["master"])            # 배달 체인 완결(drain 필수)
            self.assertEqual(e["delivered"], "wake")

    def test_multi_idle_nodes_separate_per_node_wake_keys(self):
        # master 승인 2026-07-18: idle 노드별로 task/idem 분리 → 큐 병합 최대화.
        # [v5 엣지] 무배정 리뷰어는 active→idle '전이' 시 엣지 1회. baseline에 이미 idle이면 disarm
        #   초기화라 발화하지 않으므로(§3.2·D7), baseline은 active·2주기에 idle 진입으로 셋업한다.
        with tempfile.TemporaryDirectory() as t:
            base = report(live_nodes=[{"role": "reviewer-codex", "agent_alive": True, "idle_secs": 10},
                                      {"role": "reviewer-gemini", "agent_alive": True, "idle_secs": 10}])
            gate(t, FakeRunner(rep=base)).run()               # baseline: 리뷰어 active(idle_nodes 없음)
            rep = report(live_nodes=[{"role": "reviewer-codex", "agent_alive": True, "idle_secs": 600},
                                     {"role": "reviewer-gemini", "agent_alive": True, "idle_secs": 700}],
                         idle_nodes=[{"role": "reviewer-codex", "idle_secs": 600},
                                     {"role": "reviewer-gemini", "idle_secs": 700}])
            r = FakeRunner(rep=rep)
            gate(t, r).run()                                  # 무배정 idle 전이 → 엣지 각 1회
            tasks = sorted(task for _to, task, _reason, _idem in r.enqueues)
            idems = sorted(idem for _to, _task, _reason, idem in r.enqueues)
            self.assertEqual(tasks, ["gate-idle-reviewer-codex", "gate-idle-reviewer-gemini"])
            self.assertEqual(idems, ["gate-idle-reviewer-codex", "gate-idle-reviewer-gemini"])
            self.assertEqual(r.drains, ["master"])            # 여러 enqueue·drain 1회(WARN 주기)

    def test_feed_pending_warns_with_approval_evt(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(feed=2)
            r = FakeRunner(rep=rep)
            gate(t, r).run()
            gate(t, r).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "WARN")
            self.assertIn("approval.needed", [t for t, _ in r.emits])

    # ── ④ 태스크별 stall(6주기·노드 idle) + busy 시 보류 ──
    def test_per_task_stall_promotes_when_idle(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                         live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 600}])
            r = FakeRunner(rep=rep)
            g = lambda: gate(t, r, stall_cycles=2).run()      # noqa: E731
            g()                                               # baseline
            g()                                               # count=0
            g()                                               # count=1
            g()                                               # count=2 → stall
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "WARN")
            self.assertIn("agent.silent", [t for t, _ in r.emits])
            self.assertTrue(any("stall:worker" in x for x in e["reasons"]))

    def test_stall_held_when_node_busy(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                         live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 30}])
            r = FakeRunner(rep=rep)
            for _ in range(6):
                gate(t, r, stall_cycles=2).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "NOCHG")           # busy → 승격 보류
            self.assertFalse(any("stall" in x for x in e["reasons"]))

    # ── ⑤ GAP re-baseline ──
    def test_gap_rebaselines_without_wake(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                         idle_nodes=[{"role": "worker", "idle_secs": 600}])
            clk = Clock(1_000_000.0)
            gate(t, FakeRunner(rep=rep), clock=clk).run()     # baseline at t0
            clk.epoch = 1_000_000.0 + 16 * 60                 # +16분 > 3주기(15분)
            r2 = FakeRunner(rep=rep)
            gate(t, r2, clock=clk).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "GAP")
            self.assertEqual(r2.enqueues, [])                 # wake 금지
            self.assertEqual(r2.drains, [])

    # ── ⑥ fail-open(내부 예외 주입 → 직송 호출) ──
    def test_fail_open_direct_sends_and_records(self):
        with tempfile.TemporaryDirectory() as t:
            r = FakeRunner(collect_raises=True)
            rc = gate(t, r).run()
            self.assertEqual(rc, 0)                            # 죽지 않는다
            self.assertEqual(len(r.sends), 1)
            self.assertEqual(r.sends[0][0], "master")
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "FAILOPEN")

    def test_fail_open_streak_note_after_three(self):
        with tempfile.TemporaryDirectory() as t:
            r = FakeRunner(collect_raises=True)
            for _ in range(3):
                gate(t, r).run()
            self.assertIn("게이트 자체 수리 필요", r.sends[-1][1])

    # ── P1-1: state_dir 접근 불가(권한/락 OSError)도 최상위 fail-open으로 exit 0 + 직송 ──
    @unittest.skipIf(os.geteuid() == 0, "root는 파일권한 무시 — chmod 555 재현 불가")
    def test_fail_open_when_state_dir_unwritable(self):
        with tempfile.TemporaryDirectory() as t:
            sd = os.path.join(t, "state")
            os.makedirs(sd)
            r = FakeRunner(rep=report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}]))
            os.chmod(sd, 0o555)                               # 읽기·실행만 — 락 mkdir 불가
            try:
                rc = gate(sd, r).run()
            finally:
                os.chmod(sd, 0o755)                           # 정리 위해 복구
            self.assertEqual(rc, 0)                            # 죽지 않는다(exit 1 금지)
            self.assertEqual(len(r.sends), 1)                  # master 직송 시도
            self.assertEqual(r.sends[0][0], "master")
            self.assertIn("state 기록 불가", r.sends[0][1])

    # ── ⑦ 블랙리스트 정규화(타임스탬프만 다른 입력 = 무변화) ──
    def test_blacklist_normalization_timestamp_only_no_change(self):
        with tempfile.TemporaryDirectory() as t:
            base = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                          live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 10}])
            gate(t, FakeRunner(rep=base), Clock(1000.0)).run()          # baseline
            # idle_secs(블랙리스트)·ts만 변화 → 정규화 후 동일 → 무변화
            drift = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                           live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 99}],
                           ts="2026-07-18T09:05:00+0900")
            r = FakeRunner(rep=drift)
            gate(t, r, Clock(1100.0)).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "NOCHG")
            self.assertEqual(e["delta_fields"], [])
            self.assertEqual(r.emits, [])

    # ── ⑧ 미지 신규 필드 = 변화로 감지 ──
    def test_unknown_new_field_detected_as_delta(self):
        with tempfile.TemporaryDirectory() as t:
            base = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                          live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 10}])
            gate(t, FakeRunner(rep=base)).run()               # baseline
            grown = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                           live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 10}],
                           brand_new_field={"x": 1})          # 화이트리스트 아님 → diff 대상
            r = FakeRunner(rep=grown)
            gate(t, r).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "DELTA")
            self.assertIn("brand_new_field", e["delta_fields"])
            self.assertIn("task_progress", [t for t, _ in r.emits])

    # ── ⑨ emit 거부 폴백(deny-by-default) ──
    def test_emit_reject_recorded_no_silent_loss(self):
        with tempfile.TemporaryDirectory() as t:
            base = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}])
            gate(t, FakeRunner(rep=base)).run()
            grown = report(nodes=[{"node": "worker", "done": 2, "total": 5, "pct": 40}])
            r = FakeRunner(rep=grown, emit_rc=6)              # 6 = deny-by-default 거부
            gate(t, r).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "DELTA")
            self.assertEqual(e["delivered"], "none")          # emit 실패 → 배달 없음
            self.assertTrue(any("evt_reject:task_progress(6)" in x for x in e["reasons"]))
            self.assertEqual(r.enqueues, [])                  # DELTA는 WARN급 아님 → 폴백 wake 안 함

    # ── P2-3: schema_version 부착(counters·snapshot·ledger) ──
    def test_schema_version_on_state_files(self):
        with tempfile.TemporaryDirectory() as t:
            r = FakeRunner(rep=report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}]))
            gate(t, r).run()
            counters = json.load(open(os.path.join(t, "counters.json"), encoding="utf-8"))
            snap = json.load(open(os.path.join(t, "last_snapshot.json"), encoding="utf-8"))
            self.assertEqual(counters.get("schema_version"), 2)   # counters v2(idle_edge·park_notified)
            self.assertEqual(snap.get("schema_version"), 1)       # snapshot·ledger는 v1 불변
            self.assertIn("data", snap)                       # 스냅샷 본문은 래퍼 안(diff 오탐 방지)
            self.assertEqual(ledger_entries(t)[-1]["schema_version"], 1)

    # ── T12: counters v1 로드 → v2 자연 마이그레이션(추가 전용) ──
    def test_counters_v1_migrates_to_v2(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}],
                         live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 10}])
            # v1 counters(구 스키마 — idle_edge/park_notified 부재) + 스냅샷 선기록
            gate(t, FakeRunner(rep=rep)).run()                # baseline → snapshot 생성
            with open(os.path.join(t, "counters.json"), "w", encoding="utf-8") as f:
                json.dump({"nodes": {}, "consecutive_nochg": 4, "schema_version": 1}, f)
            gate(t, FakeRunner(rep=rep)).run()                # v1 로드 → v2 기록
            counters = json.load(open(os.path.join(t, "counters.json"), encoding="utf-8"))
            self.assertEqual(counters.get("schema_version"), 2)
            self.assertIn("idle_edge", counters)              # 신규 필드 자연 마이그레이션

    def test_wrapped_snapshot_roundtrips_no_false_delta(self):
        # 래핑 스냅샷 로드→재정규화→diff가 schema_version 때문에 오탐 DELTA를 내지 않아야 한다.
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}],
                         live_nodes=[{"role": "worker", "agent_alive": True, "idle_secs": 10}])
            r = FakeRunner(rep=rep)
            gate(t, r).run()                                  # baseline (wrapped snapshot)
            gate(t, r).run()                                  # 무변화
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "NOCHG")
            self.assertEqual(e["delta_fields"], [])

    # ── P2-4: ledger tail-read + 5MB 로테이션 ──
    def test_ledger_rotation_at_threshold(self):
        with tempfile.TemporaryDirectory() as t:
            saved = G.LEDGER_MAX_BYTES
            G.LEDGER_MAX_BYTES = 200
            try:
                for _ in range(20):
                    G.ledger_append(t, {"ts": "x", "verdict": "NOCHG", "pad": "y" * 40})
            finally:
                G.LEDGER_MAX_BYTES = saved
            self.assertTrue(os.path.isfile(os.path.join(t, "ledger.jsonl")))
            self.assertTrue(os.path.isfile(os.path.join(t, "ledger.jsonl.1")))  # 1세대 보관

    def test_last_ledger_tail_read_returns_last(self):
        with tempfile.TemporaryDirectory() as t:
            for i in range(5):
                G.ledger_append(t, {"ts": "x", "verdict": "NOCHG", "seq": i})
            last = G.last_ledger(t)
            self.assertEqual(last["seq"], 4)                  # 마지막 줄

    # ── ⑩ 동시 실행 락 ──
    def test_concurrent_lock_skips(self):
        with tempfile.TemporaryDirectory() as t:
            os.makedirs(t, exist_ok=True)
            os.mkdir(os.path.join(t, "lock"))                 # 락 선점(비-stale)
            r = FakeRunner(rep=report())
            g = gate(t, r)
            rc = g.run()
            self.assertEqual(rc, 0)
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "SKIPPED_CONCURRENT")
            self.assertEqual(r.enqueues, [])

    # ── 최종 stdout 판정 요약 1줄(schedule.command_done 텔레메트리) ──
    def test_summary_line_emitted(self):
        with tempfile.TemporaryDirectory() as t:
            script = os.path.join(BIN, "javis_report_gate.py")
            env = dict(os.environ, CYS_REPORT_GATE_DIR=t)
            # collect 실패 유도(pack_bin의 javis_report가 없는 임시 pack) → WARN 경로·요약 출력
            env["CYS_PACK_DIR"] = tempfile.mkdtemp()
            p = subprocess.run([sys.executable, script, "run", "--shadow"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertTrue(p.stdout.strip().splitlines()[-1].startswith("verdict="),
                            p.stdout)


def _counters(state_dir):
    return json.load(open(os.path.join(state_dir, "counters.json"), encoding="utf-8"))


class IdleEdge(unittest.TestCase):
    """무배정 idle 엣지 1회 wake(DESIGN §3.2 v2.2) — T1~T7·T15·T21~T23."""

    ACTIVE = {"role": "worker", "agent_alive": True, "idle_secs": 10}
    IDLE = {"role": "worker", "agent_alive": True, "idle_secs": 600}

    def _idle_rep(self):
        return report(live_nodes=[dict(self.IDLE)], idle_nodes=[{"role": "worker", "idle_secs": 600}])

    def _active_rep(self):
        return report(live_nodes=[dict(self.ACTIVE)])

    # ── T1: 무배정 idle 진입 → wake 1회 + armed=False ──
    def test_t1_unassigned_idle_edge_fires_once_and_disarms(self):
        with tempfile.TemporaryDirectory() as t:
            gate(t, FakeRunner(rep=self._active_rep())).run()          # baseline active
            r = FakeRunner(rep=self._idle_rep())
            gate(t, r).run()                                           # idle 전이 → 엣지 발화
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "WARN")
            self.assertEqual([task for _to, task, _r, _i in r.enqueues], ["gate-idle-worker"])
            self.assertTrue(any("idle_edge:worker" in x for x in e["reasons"]))
            self.assertFalse(_counters(t)["idle_edge"]["worker"]["armed"])

    # ── T2: 동일 상태 지속 → 추가 wake 0 + QUIET 누적 ──
    def test_t2_persisting_idle_no_extra_wake_quiet_accumulates(self):
        with tempfile.TemporaryDirectory() as t:
            gate(t, FakeRunner(rep=self._active_rep())).run()
            r = FakeRunner(rep=self._idle_rep())
            gate(t, r).run()                                           # 엣지 1
            master_wakes = lambda: [e for e in r.enqueues if e[0] == "master"]
            self.assertEqual(len(master_wakes()), 1)
            for _ in range(3):
                gate(t, r).run()
            self.assertEqual(len(master_wakes()), 1)                   # 추가 master idle wake 0
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "QUIET")
            self.assertGreaterEqual(e["consecutive_quiet"], 1)

    # ── T3: 활동 재개 → re-arm → 쿨다운 경과 후 재진입 시 다시 1회 ──
    def test_t3_reactivate_rearms_and_refires_after_cooldown(self):
        with tempfile.TemporaryDirectory() as t:
            clk = Clock(1_000_000.0)
            gate(t, FakeRunner(rep=self._active_rep()), clock=clk, edge_cooldown=60).run()
            clk.epoch += 300
            r1 = FakeRunner(rep=self._idle_rep())
            gate(t, r1, clock=clk, edge_cooldown=60).run()             # 발화 #1
            self.assertEqual(len(r1.enqueues), 1)
            clk.epoch += 300
            gate(t, FakeRunner(rep=self._active_rep()), clock=clk, edge_cooldown=60).run()  # 활동 재개→재무장
            clk.epoch += 300
            r2 = FakeRunner(rep=self._idle_rep())
            gate(t, r2, clock=clk, edge_cooldown=60).run()             # 쿨다운 경과 재진입 → 발화 #2
            self.assertEqual(len(r2.enqueues), 1)

    # ── T4: pending-todo idle → 레벨 WARN 유지(현행 동등) ──
    def test_t4_pending_todo_idle_level_warn_persists(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 1, "total": 5, "pct": 20}],
                         live_nodes=[dict(self.IDLE)],
                         idle_nodes=[{"role": "worker", "idle_secs": 600}])
            r = FakeRunner(rep=rep)
            gate(t, r).run()                                           # baseline
            for _ in range(3):
                gate(t, r).run()
            warns = [e for e in ledger_entries(t) if e["verdict"] == "WARN"]
            self.assertGreaterEqual(len(warns), 3)                     # 레벨: 매 주기 발화
            self.assertTrue(all(any("idle_5min:worker" in x for x in e["reasons"]) for e in warns))

    # ── T5: done==total idle → 무발화(현행 동등) ──
    def test_t5_done_total_idle_no_fire(self):
        with tempfile.TemporaryDirectory() as t:
            rep = report(nodes=[{"node": "worker", "done": 3, "total": 3, "pct": 100}],
                         live_nodes=[dict(self.IDLE)],
                         idle_nodes=[{"role": "worker", "idle_secs": 600}])
            r = FakeRunner(rep=rep)
            gate(t, r).run()
            gate(t, r).run()
            self.assertEqual(r.enqueues, [])
            self.assertEqual(ledger_entries(t)[-1]["verdict"], "QUIET")

    # ── T6: BASELINE에 이미 idle이던 role → disarmed(파도 없음) ──
    def test_t6_baseline_idle_disarmed_no_flood(self):
        with tempfile.TemporaryDirectory() as t:
            r = FakeRunner(rep=self._idle_rep())
            gate(t, r).run()                                           # baseline: 이미 idle → disarm
            gate(t, r).run()                                           # 차기: disarmed → 발화 0
            self.assertEqual(r.enqueues, [])
            self.assertFalse(_counters(t)["idle_edge"]["worker"]["armed"])

    # ── T7: GAP 후 → disarmed + 사망 미발화(조기 반환) ──
    def test_t7_gap_disarms_and_no_death_fire(self):
        with tempfile.TemporaryDirectory() as t:
            clk = Clock(1_000_000.0)
            gate(t, FakeRunner(rep=self._active_rep()), clock=clk).run()   # baseline
            clk.epoch += 16 * 60                                       # +16분 > 3주기 = GAP
            r = FakeRunner(rep=self._idle_rep())
            gate(t, r, clock=clk).run()
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "GAP")
            self.assertEqual(r.enqueues, [])                           # GAP wake 금지·엣지 disarm
            self.assertFalse(_counters(t)["idle_edge"]["worker"]["armed"])

    # ── T15: 검증기 자체 검증(네거티브의 네거티브) — disarm 무력화 시 재발화 검출력 ──
    def test_t15_disarm_regression_is_detectable(self):
        with tempfile.TemporaryDirectory() as t:
            gate(t, FakeRunner(rep=self._active_rep())).run()
            gate(t, FakeRunner(rep=self._idle_rep())).run()           # 발화 → disarm
            cpath = os.path.join(t, "counters.json")
            c = json.load(open(cpath, encoding="utf-8"))
            c["idle_edge"]["worker"] = {"armed": True, "last_fired": 0}   # 고의 파손: disarm 무력화 모사
            json.dump(c, open(cpath, "w", encoding="utf-8"))
            r = FakeRunner(rep=self._idle_rep())
            gate(t, r).run()
            self.assertEqual(len(r.enqueues), 1)                      # 재발화 = 회귀 검출 가능(정상은 0)

    # ── T21: enqueue 실패(rc≠0) → armed 유지·재시도 / 성공 시 disarm ──
    def test_t21_enqueue_failure_keeps_armed_retries(self):
        with tempfile.TemporaryDirectory() as t:
            gate(t, FakeRunner(rep=self._active_rep())).run()
            r_fail = FakeRunner(rep=self._idle_rep(), enqueue_rc=1)
            gate(t, r_fail).run()                                     # enqueue 실패
            self.assertEqual(len(r_fail.enqueues), 1)                 # 시도는 함
            self.assertNotIn("worker", _counters(t).get("idle_edge", {}))  # disarm 안 됨(default armed 유지)
            r_ok = FakeRunner(rep=self._idle_rep())
            gate(t, r_ok).run()                                       # 다음 주기 재시도
            self.assertEqual(len(r_ok.enqueues), 1)                   # 재발화
            self.assertFalse(_counters(t)["idle_edge"]["worker"]["armed"])  # 성공 → disarm

    # ── T22: 진동 노드 → wake ≤1회/쿨다운창 ──
    def test_t22_oscillating_node_wake_capped_per_cooldown(self):
        with tempfile.TemporaryDirectory() as t:
            clk = Clock(1_000_000.0)
            gate(t, FakeRunner(rep=self._active_rep()), clock=clk, edge_cooldown=1000).run()
            total = 0
            for i in range(10):
                clk.epoch += 100                                      # 100s 토글 · 쿨다운 1000s
                r = FakeRunner(rep=(self._idle_rep() if i % 2 == 0 else self._active_rep()))
                gate(t, r, clock=clk, edge_cooldown=1000).run()
                total += len(r.enqueues)
            self.assertGreaterEqual(total, 1)
            self.assertLessEqual(total, 2)                            # 진동 5회에도 쿨다운창당 ≤1

    # ── T23: counters 파손 복원 주기 → idle_edge 초기화 → 재-파도 0(Sim O-1) ──
    def test_t23_counters_corruption_restore_no_edge_flood(self):
        roles = ("a", "b", "c", "d")
        idle_rep = report(live_nodes=[{"role": r, "agent_alive": True, "idle_secs": 600} for r in roles],
                          idle_nodes=[{"role": r, "idle_secs": 600} for r in roles])
        with tempfile.TemporaryDirectory() as t:
            gate(t, FakeRunner(rep=idle_rep)).run()                   # baseline → 4노드 disarm
            gate(t, FakeRunner(rep=idle_rep)).run()                   # QUIET
            with open(os.path.join(t, "counters.json"), "w", encoding="utf-8") as f:
                f.write("{corrupt json")                              # counters 파손
            r = FakeRunner(rep=idle_rep)
            gate(t, r).run()                                          # 복원 주기 → init_idle_edge
            self.assertEqual(r.enqueues, [])                          # 재-파도 0(미적용 시 4발화)


class ShadowChecker(unittest.TestCase):
    """javis_gate_check.py — 독립 키워드 규칙 검사기(producer≠evaluator)."""
    CHECK = os.path.join(BIN, "javis_gate_check.py")

    def _run(self, ledger, push_dir, window="300"):
        return subprocess.run([sys.executable, self.CHECK, "--ledger", ledger,
                               "--push-dir", push_dir, "--window", window],
                              capture_output=True, text=True)

    def test_suppressed_with_warning_keyword_is_violation(self):
        with tempfile.TemporaryDirectory() as t:
            ledger = os.path.join(t, "ledger.jsonl")
            with open(ledger, "w", encoding="utf-8") as f:
                f.write(json.dumps({"ts": "x", "ts_epoch": 1000.0, "verdict": "NOCHG"}) + "\n")
            pd = os.path.join(t, "push")
            os.makedirs(pd)
            body = os.path.join(pd, "push1.txt")
            with open(body, "w", encoding="utf-8") as f:
                f.write("주인님께 보고\n  • ⚠ idle 5분+ 노드: worker\n")
            os.utime(body, (1000.0, 1000.0))                  # 억제 시점과 동일 창
            p = self._run(ledger, pd)
            self.assertEqual(p.returncode, 1, p.stdout)       # 오억제 발견
            self.assertIn("오억제 발견 1건", p.stdout)
            self.assertIn("push1.txt", p.stdout)

    def test_clean_suppression_passes(self):
        with tempfile.TemporaryDirectory() as t:
            ledger = os.path.join(t, "ledger.jsonl")
            with open(ledger, "w", encoding="utf-8") as f:
                f.write(json.dumps({"ts": "x", "ts_epoch": 1000.0, "verdict": "NOCHG"}) + "\n")
            pd = os.path.join(t, "push")
            os.makedirs(pd)
            body = os.path.join(pd, "push1.txt")
            with open(body, "w", encoding="utf-8") as f:
                f.write("주인님께 보고\n  • 전체 진행: 40% (2/5 완료)\n")   # 경고 키워드 없음
            os.utime(body, (1000.0, 1000.0))
            p = self._run(ledger, pd)
            self.assertEqual(p.returncode, 0, p.stdout)


class LaunchdMinimalEnv(unittest.TestCase):
    """★fire_command는 launchd 데몬 최소 env를 상속(CYS_PACK_DIR·CYS_SOCKET 부재, PATH에
    /usr/local/bin 없을 수 있음, HOME은 존재). 경로/바이너리 해석이 그 env에서도 성립하는지 핀."""

    def _with_env(self, env, fn):
        saved = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update(env)
            return fn()
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def test_pack_bin_resolves_without_cys_pack_dir(self):
        # CYS_PACK_DIR 부재 → __file__ 형제(javis_report.py 동거) 디렉터리로 해석.
        home = os.path.expanduser("~")
        got = self._with_env({"HOME": home}, G.default_pack_bin)
        self.assertTrue(os.path.isfile(os.path.join(got, "javis_report.py")),
                        "pack_bin=%s 에 javis_report.py 없음" % got)

    def test_cys_bin_absolute_fallback_when_path_lacks_cys(self):
        # PATH 비움·CYS_BIN 부재 → which 실패 → 절대경로 후보 또는 최후 'cys'. crash 없이 문자열.
        got = self._with_env({"HOME": os.path.expanduser("~"), "PATH": "/nonexistent"},
                             G.resolve_cys_bin)
        self.assertIsInstance(got, str)
        self.assertTrue(got == "cys" or os.path.isabs(got), got)

    def test_cys_bin_env_wins(self):
        got = self._with_env({"HOME": os.path.expanduser("~"), "CYS_BIN": "/custom/cys"},
                             G.resolve_cys_bin)
        self.assertEqual(got, "/custom/cys")

    def test_gate_runs_under_minimal_env(self):
        # 최소 env + 존재하지 않는 pack_bin → collect 실패(WARN 경로) → exit 0(fail-open 계약).
        with tempfile.TemporaryDirectory() as t:
            r = FakeRunner(report_ok=False, err="수집 실패(최소 env)")
            rc = gate(t, r).run()
            self.assertEqual(rc, 0)
            self.assertEqual(ledger_entries(t)[-1]["verdict"], "WARN")


class ForeignDaemonGuard(unittest.TestCase):
    """외부 데몬 가드 — socket-pack 부정합(부서 데몬이 본사 팩 로드) 시 SKIP(핫픽스)."""

    def _with_env(self, env, fn):
        saved = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update(env)
            return fn()
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def test_hq_pack_with_dept_socket_skips_no_state_touch(self):
        with tempfile.TemporaryDirectory() as t:
            env = {"HOME": os.path.expanduser("~"),
                   "CYS_PACK_DIR": os.path.expanduser("~/.cys/pack"),
                   "CYS_SOCKET": "/tmp/cys-dept-1/cys.sock"}   # 본사 팩 + dept 소켓 = 오염
            r = FakeRunner(rep=report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}]))
            rc = self._with_env(env, lambda: gate(t, r).run())
            self.assertEqual(rc, 0)
            e = ledger_entries(t)[-1]
            self.assertEqual(e["verdict"], "SKIPPED_FOREIGN_DAEMON")
            self.assertIn("cys-dept-1", e["reasons"][0])        # socket 값 포함
            self.assertFalse(os.path.isfile(os.path.join(t, "counters.json")))  # 카운터 무접촉
            self.assertEqual(r.collect_calls, 0)                # 수집·stall 무접촉
            self.assertEqual(r.enqueues, [])                    # 배달 무접촉

    def test_hq_pack_socket_unset_proceeds(self):
        with tempfile.TemporaryDirectory() as t:
            env = {"HOME": os.path.expanduser("~"),
                   "CYS_PACK_DIR": os.path.expanduser("~/.cys/pack")}   # 소켓 unset = 정합
            r = FakeRunner(rep=report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}]))
            self._with_env(env, lambda: gate(t, r).run())
            self.assertEqual(ledger_entries(t)[-1]["verdict"], "BASELINE")  # 정상 진행

    def test_dept_pack_matching_socket_proceeds(self):
        with tempfile.TemporaryDirectory() as t:
            deptpack = os.path.join(t, "pack-dept-1")
            os.makedirs(deptpack)
            sd = os.path.join(t, "state")
            env = {"HOME": os.path.expanduser("~"),
                   "CYS_PACK_DIR": deptpack,
                   "CYS_SOCKET": "/tmp/cys-dept-1/cys.sock"}    # 부서 팩 + 해당 dept 소켓 = 정합
            r = FakeRunner(rep=report(nodes=[{"node": "worker", "done": 1, "total": 3, "pct": 33}]))
            self._with_env(env, lambda: gate(sd, r).run())
            self.assertEqual(ledger_entries(sd)[-1]["verdict"], "BASELINE")  # 미래 부서 게이트 호환


class C16ReportScheduleGate(unittest.TestCase):
    """C16이 델타게이트 잡을 5분 보고 체계로 인정하는지(마이그레이션 되돌림 방지) 회귀."""

    import importlib
    P = importlib.import_module("javis_preflight")

    def _c16(self, tmp, jobs, fix=False):
        with open(os.path.join(tmp, "schedule.json"), "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False)
        saved = dict(os.environ)
        os.environ["CYS_PACK_DIR"] = tmp
        try:
            pf = self.P.Preflight(fix=fix, skips=set(), mode=("fix" if fix else "report"))
            pf.c16_report_schedule()
            with open(os.path.join(tmp, "schedule.json"), encoding="utf-8") as f:
                after = json.load(f)
            return pf.results[-1], after
        finally:
            os.environ.clear()
            os.environ.update(saved)

    GATE_JOB = {"id": "owner-progress-gate-5min", "every_minutes": 5, "action": "command",
                "command": "python3 \"${CYS_PACK_DIR:-$HOME/.cys/pack}/bin/javis_report_gate.py\" run",
                "if_absent": "skip"}
    PUSH_JOB = {"id": "owner-progress-report-5min", "every_minutes": 5, "action": "push",
                "to": "master", "text_command": "python3 x", "if_absent": "skip"}

    def test_gate_job_only_passes_and_fix_is_noop(self):
        with tempfile.TemporaryDirectory() as t:
            res, _ = self._c16(t, [dict(self.GATE_JOB)])
            self.assertEqual(res["status"], "PASS", res)
            # --fix: 게이트 잡 존재 → 재추가 없음(마이그레이션 보존)
            res2, after = self._c16(t, [dict(self.GATE_JOB)], fix=True)
            self.assertEqual(res2["status"], "PASS")
            ids = [j["id"] for j in after["jobs"]]
            self.assertEqual(ids, ["owner-progress-gate-5min"])   # 구 push 잡 재생성 안 됨

    def test_no_report_job_fails_and_fix_adds_gate_job(self):
        # reviewer1 P1: --fix는 구 push 잡이 아니라 게이트 잡을 추가해야 한다.
        with tempfile.TemporaryDirectory() as t:
            res, _ = self._c16(t, [])
            self.assertEqual(res["status"], "FAIL", res)
            res2, after = self._c16(t, [], fix=True)
            self.assertEqual(res2["status"], "FIXED")
            added = [j for j in after["jobs"] if j["id"] == "owner-progress-gate-5min"]
            self.assertEqual(len(added), 1, after)
            self.assertEqual(added[0]["action"], "command")
            self.assertIn("javis_report_gate.py", added[0]["command"])
            # 구 push 보고 잡은 부활하지 않는다(제거 대상).
            self.assertFalse(any(j["id"] == "owner-progress-report-5min" for j in after["jobs"]))

    def test_legacy_push_job_still_passes(self):
        with tempfile.TemporaryDirectory() as t:
            res, _ = self._c16(t, [dict(self.PUSH_JOB)])
            self.assertEqual(res["status"], "PASS", res)   # 하위호환


if __name__ == "__main__":
    unittest.main()
