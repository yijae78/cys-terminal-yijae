#!/usr/bin/env python3
"""office-cc v1.3 브리지 단위 테스트 — stdlib unittest만 (신규 의존성 0).

대상:
  · D4 watchdog → 강아지 fx 변환 (kill/alert·코얼레싱·백로그·음성: 비-watchdog 무누출)
  · D5 merge_fleet 형상 비교 확장 (라벨만 변경 → structural True)
  · D6 scan_skills 카탈로그 파서 (frontmatter·폴백·accounts 병합·절단·'_' skip)
음성 케이스 포함(코얼레싱 2건째 폐기·watchdog 이외 무누출·라벨 무변경 False).
"""
import os
import shutil
import tempfile
import time
import unittest

BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin")
if BIN not in __import__("sys").path:
    __import__("sys").path.insert(0, BIN)

import javis_hud_bridge as B  # noqa: E402


# ------------------------------------------------------------------ D4 강아지 fx
class DogFx(unittest.TestCase):
    def _ev(self, name, **kw):
        ev = {"name": name, "timestamp": time.time()}
        ev.update(kw)
        return ev

    def test_duplicate_procs_to_kill(self):
        coal = B.Coalescer()
        ev = self._ev("watchdog.duplicate_procs",
                      payload={"cmdline": "bun server.ts", "count": 3, "pids": [111, 222, 333]})
        frames, poke = B.route_event(ev, None, coal, now=ev["timestamp"])
        self.assertFalse(poke)
        self.assertEqual(frames, [{"t": "dog", "kind": "kill", "pid": 111, "count": 3}])

    def test_duplicate_procs_no_pids_pid_none(self):
        coal = B.Coalescer()
        ev = self._ev("watchdog.duplicate_procs", payload={"count": 2})
        frames, _ = B.route_event(ev, None, coal, now=ev["timestamp"])
        self.assertEqual(frames, [{"t": "dog", "kind": "kill", "pid": None, "count": 2}])

    def test_proc_count_high_to_alert(self):
        coal = B.Coalescer()
        ev = self._ev("watchdog.proc_count_high", surface_id=7,
                      payload={"count": 42, "threshold": 20})
        frames, _ = B.route_event(ev, None, coal, now=ev["timestamp"])
        self.assertEqual(frames, [{"t": "dog", "kind": "alert", "sid": 7, "count": 42}])

    def test_other_watchdog_blocked_no_dog(self):
        # 음성: tick_panic·load_high 등 그 외 watchdog.* 은 강아지 fx 로 새지 않고 차단
        coal = B.Coalescer()
        for name in ("watchdog.tick_panic", "watchdog.load_high",
                     "watchdog.duplicates_killed", "watchdog.proc_count"):
            frames, poke = B.route_event(self._ev(name, payload={"count": 9}), None, coal)
            self.assertEqual(frames, [], name)
            self.assertFalse(poke, name)

    def test_non_watchdog_event_never_dog(self):
        # 음성: watchdog 이외 이벤트에는 t:'dog' 프레임이 절대 섞이지 않는다
        w = B.World()
        w.departments = [{"department": "본부", "surfaces": [
            {"role": "worker", "surface_ref": "surface:5", "surface_id": 5}]}]
        coal = B.Coalescer()
        ev = {"name": "todo.updated", "timestamp": time.time(),
              "payload": {"path": "/x/WORKER_TODO.md", "done": 1, "total": 3}}
        frames, _ = B.route_event(ev, w, coal, now=ev["timestamp"])
        self.assertTrue(frames)
        self.assertFalse(any(fr.get("t") == "dog" for fr in frames))

    def test_coalesce_second_within_window_dropped(self):
        # 음성: 10s 창 내 2건째 폐기, 창 경과 후 재허용 (kill·alert 공유 창)
        coal = B.Coalescer()
        t0 = 1000.0
        f1, _ = B.route_event(self._ev("watchdog.duplicate_procs",
                              timestamp=t0, payload={"count": 2, "pids": [1]}),
                              None, coal, now=t0)
        self.assertEqual(len(f1), 1)
        f2, _ = B.route_event(self._ev("watchdog.proc_count_high",
                              timestamp=t0 + 5, surface_id=3, payload={"count": 30}),
                              None, coal, now=t0 + 5)
        self.assertEqual(f2, [])   # 5s < 10s 창 → 2건째 폐기(공유 창)
        f3, _ = B.route_event(self._ev("watchdog.proc_count_high",
                              timestamp=t0 + 11, surface_id=3, payload={"count": 31}),
                              None, coal, now=t0 + 11)
        self.assertEqual(len(f3), 1)   # 11s > 10s → 재허용

    def test_backlog_suppressed(self):
        coal = B.Coalescer()
        now = 5000.0
        ev = self._ev("watchdog.duplicate_procs",
                      timestamp=now - (B.BACKLOG_FX_SECS + 1), payload={"count": 2, "pids": [9]})
        frames, _ = B.route_event(ev, None, coal, now=now)
        self.assertEqual(frames, [])   # 과거 이벤트 → 연출 억제


# ----------------------------------------------------- D5 merge_fleet 형상 비교
def _fleet(label, socket=None):
    return {"departments": [{
        "dept": "eng", "department": label, "socket": socket,
        "surfaces": [{"role": "worker", "surface_ref": "surface:3", "surface_id": 3}]}]}


class MergeFleetShape(unittest.TestCase):
    def test_label_only_change_triggers_structural(self):
        w = B.World()
        _, s1 = w.merge_fleet(_fleet("옛이름"), None)
        self.assertTrue(s1)   # 첫 등장 → 재빌드
        _, s2 = w.merge_fleet(_fleet("옛이름"), None)
        self.assertFalse(s2)  # 동일 → 재빌드 없음(오탐 없음)
        _, s3 = w.merge_fleet(_fleet("새이름"), None)
        self.assertTrue(s3)   # display_name(label)만 변경 → structural True (D5 핵심)

    def test_slug_stable_across_rename(self):
        # 개명해도 slug 는 dept 필드(불변) 파생 → 키는 유지, 형상 비교가 라벨을 잡아야 한다
        w = B.World()
        w.merge_fleet(_fleet("옛이름"), None)
        w.merge_fleet(_fleet("새이름"), None)
        self.assertEqual(w.departments[0]["_slug"], "eng")
        self.assertEqual(w.departments[0]["_dept_label"], "새이름")


# --------------------------------------------------------- D6 scan_skills 파서
def _mk_skill(base, name, frontmatter=None, body="", make_md=True):
    d = os.path.join(base, name)
    os.makedirs(d, exist_ok=True)
    if not make_md:
        return
    parts = []
    if frontmatter is not None:
        parts.append("---")
        for k, v in frontmatter.items():
            parts.append(f"{k}: {v}")
        parts.append("---")
    parts.append(body)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


class ScanSkills(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hud-skills-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.a = os.path.join(self.tmp, "a")
        self.b = os.path.join(self.tmp, "b")

    def _scan(self):
        return B.scan_skills(sources=[(self.a, "pack"), (self.b, "claude")])["skills"]

    def test_frontmatter_and_accounts_merge(self):
        _mk_skill(self.a, "alpha", {"name": "alpha", "description": '"desc A"'})
        _mk_skill(self.a, "beta", {"name": "beta", "description": "beta desc"})
        _mk_skill(self.b, "alpha", {"name": "alpha", "description": '"desc A2"'})
        _mk_skill(self.b, "gamma", {"name": "gamma", "description": "g"})
        skills = {s["name"]: s for s in self._scan()}
        self.assertEqual(skills["alpha"]["accounts"], ["pack", "claude"])  # 동일 name 병합
        self.assertEqual(skills["beta"]["accounts"], ["pack"])
        self.assertEqual(skills["gamma"]["accounts"], ["claude"])
        self.assertEqual(skills["alpha"]["description"], "desc A")  # 첫 소스·따옴표 제거

    def test_fallback_dirname_and_first_paragraph(self):
        # frontmatter 없음 → name=디렉토리명, description=첫 문단(헤딩·구분선 skip)
        _mk_skill(self.a, "delta", None, body="# 제목\n\n첫 문단 내용입니다.\n둘째 줄")
        s = {x["name"]: x for x in self._scan()}
        self.assertIn("delta", s)
        self.assertEqual(s["delta"]["description"], "첫 문단 내용입니다.")

    def test_description_truncated_200(self):
        long = "x" * 500
        _mk_skill(self.a, "long", {"name": "long", "description": long})
        s = {x["name"]: x for x in self._scan()}
        self.assertEqual(len(s["long"]["description"]), 200)

    def test_skips_underscore_and_missing_md(self):
        _mk_skill(self.a, "_VENDOR", {"name": "_VENDOR", "description": "x"})  # '_' 접두 skip
        _mk_skill(self.a, "nomd", None, make_md=True, body="")  # SKILL.md 있으나 내용 없음
        _mk_skill(self.a, "empty_dir", None, make_md=False)     # SKILL.md 없음 → skip
        # 파일(디렉토리 아님)도 안전 무시
        with open(os.path.join(self.a, "loose.txt"), "w") as f:
            f.write("x")
        names = [s["name"] for s in self._scan()]
        self.assertNotIn("_VENDOR", names)
        self.assertNotIn("empty_dir", names)
        self.assertNotIn("loose.txt", names)

    def test_missing_source_dir_ignored(self):
        # 존재하지 않는 소스 → OSError 무시하고 계속 (계정 미설치 케이스)
        _mk_skill(self.a, "solo", {"name": "solo", "description": "s"})
        skills = B.scan_skills(sources=[(self.a, "pack"),
                                        (os.path.join(self.tmp, "nope"), "claude")])["skills"]
        self.assertEqual([s["name"] for s in skills], ["solo"])


if __name__ == "__main__":
    unittest.main()
