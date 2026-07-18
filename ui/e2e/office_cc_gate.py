#!/usr/bin/env python3
"""office-cc v13 E2E 게이트 — 배치·개명·raw키·착석·강아지·상점 6군 불변식.

기존 ui/e2e/office_detail_gate.py(=계약 v1.1 회귀 게이트)와 별개다. 이 게이트는
office-cc v13 신규 유닛(D1 배치 SOT·D2 착석·D4 강아지·D5 개명·D6 상점)만 검증한다.

무엇을 단언하나 (실코드 window.__officeDebug 훅 기준):
  1) 배치 — dbg.floorPlanOf 열거(라벨 3종 × 노드수 1/5/12): 데스크 쌍별 최소거리>0.9 ·
     데스크∩(회의실·라운지) 비겹침(dbg.furnitureAabbs) · 링(gather+유도반경)∈회의실 ·
     patrol∈슬랩·가구 외부 · 같은 라벨=같은 plan(결정론) · 다른 라벨=상이 plan≥1.
  2) 개명 — /stream {t:'world'}(라벨만 변경) → buildWorld 재빌드 → 패널 라벨 갱신.
  3) raw 키 — 렌더 DOM 텍스트(패널 열기 포함)에 dept-\\d+@surface 패턴 부재.
  4) 착석 — dbg.teleportOwner(자리 존)→정지→ownerSeated=true·좌면 좌표 / dbg.setKey 이동→기립·보행고.
  5) 강아지 — /stream {t:'dog',kind:'kill'} → dbg.dogState.mode 전이(kill_run) · 미지 {t:'zzz'} 무예외.
  6) 상점 — dbg.shopItems()>0 (mock /skills). ※클릭 우선순위 런타임 단언은 훅 부재로 보고(§한계).

사전:  pip install playwright && playwright install chromium
실행:  python3 ui/e2e/office_cc_gate.py     # exit 0 = PASS
"""
import http.server
import json
import queue
import socket
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB_DIR = Path(__file__).resolve().parents[2] / "cysjavis-pack" / "web"
NOW = int(time.time())
STOP = threading.Event()
SSE = queue.Queue()          # 테스트가 런타임에 프레임 주입(개명 world·dog fx·미지 fx)
PEEK_KEYS: list[str] = []
SKILLS = {"skills": [
    {"name": "appbuild", "description": "웹/앱 자율 빌드 오케스트레이터",
     "accounts": ["pack", "claude", "cysinsight", "ysfuture"]},
    {"name": "deep-research", "description": "다출처 팩트체크 리서치", "accounts": ["claude"]},
    {"name": "diagnose", "description": "난해 버그 진단 루프", "accounts": ["pack", "claude"]},
]}


def node(key, role, label, presence="active", ctx=50, idle=0):
    return {"key": key, "role": role, "presence": presence, "presence_conf": 0.9,
            "ctx": {"pct": ctx}, "activity": 0.5, "agent": "claude", "dept_label": label,
            "task": "작업 중", "rate": [], "flags": [], "idle_secs": idle,
            "progress": None, "run": None}


def world(label_a="엔지니어링", label_b="디자인"):
    return {
        "v": 2, "seq": 1, "daemon": {"version": "0.12.92", "paused": False},
        "departments": [
            {"id": "eng", "floor": 1, "nodes": [
                node("eng@surface:5", "master", label_a),
                node("eng@surface:6", "worker", label_a, "waiting", 20, 120)]},
            {"id": "design", "floor": 2, "nodes": [
                node("design@surface:7", "worker", label_b, "active", 40)]},
        ],
        "lobby": {"unassigned": []}, "server_room": [], "todo": {}, "blocked": [],
        "kanban": {"ts": NOW, "tasks": []}, "review": {"ts": NOW, "items": []},
        "board": {"heat": {}, "cost_today": {"usd": 1.0, "tokens": 1000}},
    }


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self._json({"ok": True})

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/stream":
            return self._stream()
        if path == "/world":
            return self._json(world())
        if path == "/skills":
            return self._json(SKILLS)
        if path == "/history":
            return self._json({"events": []})
        if path == "/peek":
            q = parse_qs(urlparse(self.path).query)
            PEEK_KEYS.append(q.get("key", [""])[0])
            return self._json({"ok": True, "lines": ["peek 샘플"]})
        rel = "office3d.html" if path in ("/", "") else path.lstrip("/")
        fp = (WEB_DIR / rel).resolve()
        if not str(fp).startswith(str(WEB_DIR)) or not fp.is_file():
            self.send_response(404)
            self.end_headers()
            return
        data = fp.read_bytes()
        ctype = ("text/html" if fp.suffix == ".html"
                 else "application/javascript" if fp.suffix in (".js", ".mjs")
                 else "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def send(obj):
            self.wfile.write(("data: " + json.dumps(obj) + "\n\n").encode())
            self.wfile.flush()
        try:
            send({"t": "world", "world": world()})   # 초기 월드
            while not STOP.is_set():
                try:
                    send(SSE.get(timeout=0.3))        # 테스트 주입 프레임
                except queue.Empty:
                    self.wfile.write(b":hb\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return


# ── 배치 불변식 열거 (그룹 1) — dbg.floorPlanOf 순수함수 ──────────────────────
LAYOUT_JS = r"""
() => {
  const dbg = window.__officeDebug;
  if (!dbg || !dbg.floorPlanOf) return { error: 'floorPlanOf 훅 부재' };
  const aabbOf = dbg.furnitureAabbs || null;
  const overlap = (a,b)=> Math.abs(a.cx-b.cx) < (a.w+b.w)/2 && Math.abs(a.cz-b.cz) < (a.d+b.d)/2;
  const SLABX = 6.5, SLABZ = 4.3;
  const labels = ['엔지니어링','디자인','마케팅'];
  const counts = [1,5,12];
  const fails = []; const planByLabel = {};
  for (const L of labels){
    const s1 = JSON.stringify(dbg.floorPlanOf(L, null, 5));
    const s2 = JSON.stringify(dbg.floorPlanOf(L, null, 5));
    if (s1 !== s2) fails.push(`⑤비결정론 L=${L}`);   // 같은 라벨=같은 plan
    planByLabel[L] = s1;
    for (const n of counts){
      const plan = dbg.floorPlanOf(L, null, n);
      const m = plan.meeting;
      const rx = m.w/2 - 0.4, rz = m.d/2 - 0.4;      // ③ 링 ∈ 회의실(유도반경)
      if (!(rx > 0 && rz > 0 && plan.gather.x === m.x && plan.gather.z === m.z))
        fails.push(`③링∉회의실 L=${L} n=${n} m=${JSON.stringify(m)}`);
      // ① 데스크 쌍별 최소거리 > 0.9
      for (let i=0;i<plan.desks.length;i++) for (let j=i+1;j<plan.desks.length;j++){
        const a=plan.desks[i], b=plan.desks[j];
        const dist = Math.hypot(a[0]-b[0], a[1]-b[1]);
        if (dist <= 0.9) fails.push(`①데스크간격<=0.9 L=${L} n=${n} dist=${dist.toFixed(3)}`);
      }
      if (aabbOf){
        const fa = aabbOf(plan);
        const furn = [fa.meeting, fa.lounge, fa.kanban, fa.amenity].filter(Boolean);
        for (const d of (fa.desks||[])){                // ② 데스크 ∩ 회의실·라운지 비겹침
          if (fa.meeting && overlap(d, fa.meeting)) fails.push(`②데스크∩회의실 L=${L} n=${n}`);
          if (fa.lounge && overlap(d, fa.lounge)) fails.push(`②데스크∩라운지 L=${L} n=${n}`);
        }
        for (const p of plan.patrol){                   // ④ patrol ∈ 슬랩 · 가구 외부
          if (Math.abs(p[0])>SLABX || Math.abs(p[1])>SLABZ) fails.push(`④순찰∉슬랩 L=${L} n=${n} p=${JSON.stringify(p)}`);
          const pt = {cx:p[0], cz:p[1], w:0.02, d:0.02};
          for (const f of furn) if (overlap(pt, f)) fails.push(`④순찰∈가구 L=${L} n=${n} p=${JSON.stringify(p)}`);
        }
      }
    }
  }
  const distinct = new Set(Object.values(planByLabel)).size >= 2;   // 다른 라벨=상이 plan≥1
  return { failCount: fails.length, fails: fails.slice(0,20),
           distinctLabels: distinct, hasAabb: !!aabbOf };
}
"""

failures: list[str] = []
asserted = 0


def check(cond, msg):
    global asserted
    asserted += 1
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        failures.append(msg)


def main() -> int:
    if not (WEB_DIR / "office3d.html").is_file():
        print(f"FAIL: {WEB_DIR}/office3d.html 없음")
        return 2
    from playwright.sync_api import sync_playwright

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    page_errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--use-gl=angle"])
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{port}/office3d.html?debug=1")
            page.wait_for_function("()=>!!window.__officeDebug", timeout=8000)
            page.wait_for_function(
                "()=>window.__officeDebug.ownerState()!=null && window.__officeDebug.dogState!=null",
                timeout=10000)

            # ── 그룹 1: 배치 불변식 ──────────────────────────────────────────
            lay = page.evaluate(LAYOUT_JS)
            print("  배치:", json.dumps(lay, ensure_ascii=False))
            check(lay.get("error") is None, f"1-배치 floorPlanOf 훅 가용 (err={lay.get('error')})")
            check(bool(lay.get("hasAabb")), "1-배치 furnitureAabbs 훅 존재(가구 footprint SOT)")
            check(bool(lay.get("distinctLabels")), "1-배치 다른 라벨=상이 plan≥1(개성)")
            check(lay.get("failCount") == 0,
                  f"1-배치 불변식(데스크간격>0.9·데스크∩가구·링∈회의실·순찰·결정론) 위반 "
                  f"{lay.get('failCount')}건 (fails={lay.get('fails')})")

            # ── 그룹 4: 착석 상태기계 ────────────────────────────────────────
            # 자리 존으로 텔레포트 → 정지 시 자동 착석
            page.evaluate("()=>window.__officeDebug.teleportOwner(0.5, -3.0, null)")
            try:
                page.wait_for_function(
                    "()=>window.__officeDebug.ownerSeated===true", timeout=6000)
            except Exception:
                pass
            seated = page.evaluate("()=>window.__officeDebug.ownerState()")
            print("  착석:", json.dumps(seated, ensure_ascii=False))
            check(bool(seated) and seated.get("seated") is True,
                  f"4-착석 자리 존 정지→ownerSeated=true (state={seated})")
            check(bool(seated) and abs(seated.get("x", 9) - 0.5) < 0.06
                  and abs(seated.get("z", 9) + 3.65) < 0.06,
                  f"4-착석 좌표=왕좌 SOT(x=0.5,z=-3.65) (state={seated})")
            seat_y = seated.get("y") if seated else None
            # 이동 입력 → 기립(y 보행고 복원·seated=false)
            page.evaluate("()=>window.__officeDebug.setKey('up', true)")
            try:
                page.wait_for_function(
                    "()=>window.__officeDebug.ownerSeated===false", timeout=4000)
            except Exception:
                pass
            page.wait_for_timeout(300)
            page.evaluate("()=>window.__officeDebug.setKey('up', false)")
            stood = page.evaluate("()=>window.__officeDebug.ownerState()")
            print("  기립:", json.dumps(stood, ensure_ascii=False))
            check(bool(stood) and stood.get("seated") is False,
                  f"4-기립 이동 입력→seated=false (state={stood})")
            check(bool(stood) and seat_y is not None and stood.get("y", 0) > seat_y + 0.1,
                  f"4-기립 y=보행고 복원(좌면 {seat_y}보다 높음) (y={stood.get('y') if stood else None})")

            # ── 그룹 5: 강아지 fx ────────────────────────────────────────────
            mode0 = page.evaluate("()=>window.__officeDebug.dogState && window.__officeDebug.dogState.mode")
            SSE.put({"t": "dog", "kind": "kill", "pid": None})   # kill → 서버룸 질주
            hit_kill = False
            try:
                page.wait_for_function(
                    "()=>{const d=window.__officeDebug.dogState;"
                    "return d && (d.mode==='kill_run' || d.mode==='transit');}", timeout=6000)
                hit_kill = True
            except Exception:
                pass
            mode1 = page.evaluate("()=>window.__officeDebug.dogState && window.__officeDebug.dogState.mode")
            print(f"  강아지: mode {mode0} → {mode1} (kill 반응={hit_kill})")
            check(hit_kill, f"5-강아지 {{t:'dog',kind:'kill'}} → dogState 전이(kill_run/transit) (mode={mode1})")
            # 미지 fx 무예외 (switch default 부재 = 무시)
            errs_before = len(page_errors)
            SSE.put({"t": "zzz", "kind": "bogus"})
            page.wait_for_timeout(400)
            check(len(page_errors) == errs_before,
                  f"5-미지 fx {{t:'zzz'}} 주입 무예외 (new pageerror={page_errors[errs_before:]})")

            # ── 그룹 6: 상점 ─────────────────────────────────────────────────
            page.wait_for_timeout(300)   # /skills fetch 반영
            shop_n = page.evaluate("()=>window.__officeDebug.shopItems()")
            check(isinstance(shop_n, int) and shop_n > 0,
                  f"6-상점 진열 상품 수 shopItems()={shop_n} (>0, mock /skills 반영)")
            # ※6b(상품 클릭이 owner 이동 유발 안 함)는 런타임 단언 불가 — 아래 §한계 보고.

            # ── 그룹 2: 개명 → 재빌드 → 라벨 갱신 ────────────────────────────
            page.evaluate("()=>window.__officeDebug.openPanel('eng@surface:5')")
            page.wait_for_timeout(150)
            title_before = page.evaluate("()=>window.__officeDebug.panelTitle()")
            SSE.put({"t": "world", "world": world(label_a="엔지니어링부")})  # 라벨만 변경
            page.wait_for_timeout(600)   # buildWorld 재빌드
            has_eng_plan = page.evaluate("()=>!!window.__officeDebug.floorPlan('eng')")
            page.evaluate("()=>window.__officeDebug.openPanel('eng@surface:5')")
            page.wait_for_timeout(150)
            title_after = page.evaluate("()=>window.__officeDebug.panelTitle()")
            print(f"  개명: '{title_before}' → '{title_after}' · eng plan 재존재={has_eng_plan}")
            check(has_eng_plan, "2-개명 재빌드 후 floorPlan('eng') 재존재(재빌드 정상)")
            check(title_after and "엔지니어링부" in title_after,
                  f"2-개명 라벨 변경이 패널 라벨에 반영 (before={title_before!r} after={title_after!r})")

            # ── 그룹 3: raw 키 비노출 ────────────────────────────────────────
            body_text = page.evaluate("()=>document.body.innerText")
            import re
            raw_hits = re.findall(r"dept-\d+@surface", body_text)
            check(not raw_hits, f"3-raw키 화면 DOM 텍스트에 dept-N@surface 부재 (hits={raw_hits[:5]})")

            check(len(page_errors) == 0, f"콘솔 pageerror 0건 (got {page_errors})")
            page.screenshot(path=str(Path(__file__).resolve().parent / "office_cc_snapshot.png"))
            browser.close()
    finally:
        STOP.set()
        httpd.shutdown()

    print(f"\n{'PASS' if not failures else 'FAIL'} — 단언 {asserted}종 · 실패 {len(failures)}건")
    for f in failures:
        print(f"  ✗ {f}")
    if failures:
        return 1
    print("\n§한계(보고): 6b '상품 클릭이 owner 이동 유발 안 함'은 런타임 단언 불가 — office3d.html "
          "메인이 <script type=module>이라 camera/worldGroup/raycaster가 모듈 스코프에 갇혀 "
          "page.evaluate로 상품 화면좌표 투영·클릭 시뮬이 불가하다. 클릭 우선순위(nodeKey>shopItem>"
          "floorY)는 소스(office3d.html:2148-2151)에 구현돼 있으나, 게이트 자동화하려면 프론트에 "
          "dbg.clickShopItem() 또는 dbg.projectToScreen(x,y,z) 훅이 필요. (수정 금지·보고만)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
