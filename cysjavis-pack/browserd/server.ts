// server.ts — browserd 엔진 사이드카.
// 실제 Chromium headful 기동(설치된 Chrome 우선, 폴백 playwright chromium).
// 전송: 127.0.0.1 HTTP, port 0-bind, 경로 /<token>/rpc. state.json 원자 기록(0600).
//
// launchd 등록·부트 훅·preflight 무접점. lazy 사이드카 — 죽어도 이 기능만 상실.
// 클린룸: cmux 코드 무참조. 외부 의존 = playwright-core 단독.

import { chromium, type BrowserContext, type Page, type Dialog } from "playwright-core";
import { createHash, timingSafeEqual } from "node:crypto";
import { existsSync, mkdirSync, writeFileSync, rmSync, renameSync } from "node:fs";
import { join } from "node:path";
import {
  BrowserState,
  IDLE_TIMEOUT_MS,
  MAX_CONTEXTS,
  PICK_OVERLAY_JS,
  SNAPSHOT_LIMIT,
  UNTRUSTED_HEADER,
  browserRoot,
  capText,
  genToken,
  profileDir,
  writeState,
} from "./lib";

const HEADLESS = process.argv.includes("--headless") || process.env.CYS_BROWSER_HEADLESS === "1";

type Control = "agent" | "human";
interface Ctx {
  page: Page;
  control: Control;
  profile: "agent" | "human";
}

// --- 상태 ---
let persistentCtx: BrowserContext | null = null; // agent 프로필(무세션·기본)
let humanCtx: BrowserContext | null = null; // human 프로필(인증·SOT) — CEO 결재 통과 시에만 생성
// 진행중 launch Promise 캐시(프로필별) — 동시 첫 open 2건이 동일 userDataDir를 이중 launch 하지
// 않도록 첫 호출의 Promise를 공유하고, 실패 시 캐시를 비워 다음 호출이 재시도한다(F3).
let launchingCtx: { agent: Promise<BrowserContext> | null; human: Promise<BrowserContext> | null } = {
  agent: null,
  human: null,
};
const contexts = new Map<string, Ctx>();
let lastActivity = Date.now();
let lastEvidencePath: string | null = null; // 최근 evidence 번들 경로(관측 status·observe 반환용)
const dialogLog: string[] = [];
// P4 pick: exposeBinding은 페이지당 1회만 등록 가능 → 등록 여부와 현재 resolver를 페이지별로 추적.
const pickBound = new WeakSet<Page>();
const pickResolvers = new Map<Page, (data: any) => void>();

function touch() {
  lastActivity = Date.now();
}

class RpcError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

// --- 브라우저 기동 (Chrome 채널 우선, 폴백 chromium) ---
// 프로필별 persistentContext를 각각 기동한다. agent/human user-data-dir가 분리되어
// human 인증 세션(SOT)이 agent 검증 트래픽과 섞이지 않는다(§2A 프로필 2원화).
async function launchProfileCtx(profile: "agent" | "human"): Promise<BrowserContext> {
  const dir = profileDir(profile);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  const common = {
    headless: HEADLESS,
    viewport: { width: 1280, height: 800 },
    args: ["--no-first-run", "--no-default-browser-check"],
  };
  try {
    return await chromium.launchPersistentContext(dir, { ...common, channel: "chrome" });
  } catch (e) {
    // 설치된 Chrome 없음 → playwright chromium 폴백
    return await chromium.launchPersistentContext(dir, common);
  }
}

async function ensureBrowser(profile: "agent" | "human" = "agent"): Promise<BrowserContext> {
  if (profile === "human") {
    if (humanCtx) return humanCtx;
    // 진행중 launch가 있으면 그 Promise를 공유(이중 launch 방지).
    if (!launchingCtx.human) {
      launchingCtx.human = launchProfileCtx("human")
        .then((ctx) => (humanCtx = ctx))
        .finally(() => { launchingCtx.human = null; }); // 성공·실패 모두 캐시 해제(실패 시 재시도 가능)
    }
    return launchingCtx.human;
  }
  if (persistentCtx) return persistentCtx;
  if (!launchingCtx.agent) {
    launchingCtx.agent = launchProfileCtx("agent")
      .then((ctx) => (persistentCtx = ctx))
      .finally(() => { launchingCtx.agent = null; });
  }
  return launchingCtx.agent;
}

function getCtx(id: string): Ctx {
  const c = contexts.get(id);
  if (!c) throw new RpcError("NO_CONTEXT", `context '${id}' 없음 — 먼저 open 하라`);
  return c;
}

// 조작권 게이트: 변경성 동사는 control=human이면 거부.
function assertAgentControl(c: Ctx) {
  if (c.control === "human") {
    throw new RpcError("HUMAN_ACTIVE", "사람이 조작 중(control=human) — 에이전트 동사 거부");
  }
}

// 프로필 격리 게이트: human 프로필 컨텍스트는 읽기 전용(open/wait/screenshot/snapshot만).
// 에이전트 자동화 동사(click/fill/type/press/eval)는 사람이 로그인·브라우징하는 세션을
// 조작 못 하게 기본 거부한다(§2A · P3 예외 없음).
function assertNotHumanProfile(c: Ctx, verb: string) {
  if (c.profile === "human") {
    throw new RpcError("HUMAN_PROFILE_PROTECTED", `human 프로필은 읽기 전용 — 에이전트 동사 '${verb}' 거부`);
  }
}

function selectorFor(args: any): string {
  if (args.ref) return `[data-cys-ref="${String(args.ref).replace(/"/g, "")}"]`;
  if (args.selector) return String(args.selector);
  throw new RpcError("BAD_ARGS", "ref 또는 selector 필요");
}

// 페이지에 주입해 접근성/DOM 요약 + ref 부여.
const SNAPSHOT_JS = `(() => {
  document.querySelectorAll('[data-cys-ref]').forEach(e => e.removeAttribute('data-cys-ref'));
  let n = 0;
  const out = [];
  const INTERACTIVE = new Set(['A','BUTTON','INPUT','SELECT','TEXTAREA']);
  function visible(el){
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
  }
  function name(el){
    let t = (el.getAttribute && (el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.getAttribute('name')) ) || el.value || el.innerText || el.textContent || '';
    return String(t).replace(/\\s+/g,' ').trim().slice(0,120);
  }
  const walker = document.createTreeWalker(document.body || document.documentElement, NodeFilter.SHOW_ELEMENT);
  let node = walker.currentNode;
  while (node) {
    const el = node;
    if (el.nodeType === 1 && visible(el)) {
      const tag = el.tagName;
      const role = el.getAttribute('role');
      let kind = null;
      if (INTERACTIVE.has(tag)) kind = tag.toLowerCase();
      else if (role) kind = '[' + role + ']';
      else if (/^H[1-6]$/.test(tag)) kind = 'heading';
      if (kind) {
        const ref = 'e' + (++n);
        el.setAttribute('data-cys-ref', ref);
        let line;
        if (tag === 'INPUT') line = (el.type || 'text') + ' input "' + name(el) + '" [ref=' + ref + ']';
        else line = kind + ' "' + name(el) + '" [ref=' + ref + ']';
        out.push(line);
      }
    }
    node = walker.nextNode();
  }
  return { title: document.title, url: location.href, items: out };
})()`;

async function buildSnapshot(page: Page): Promise<{ text: string; truncated: boolean; raw: any }> {
  const raw: any = await page.evaluate(SNAPSHOT_JS);
  const body = [
    UNTRUSTED_HEADER,
    "",
    `Page: ${raw.title || "(untitled)"}`,
    `URL: ${raw.url}`,
    "",
    ...raw.items,
  ].join("\n");
  const { text, truncated } = capText(body, SNAPSHOT_LIMIT);
  return { text, truncated, raw };
}

// evidence 번들: screenshot.png → snapshot.txt → meta.json(마지막 = 완결 마커).
async function writeEvidence(
  page: Page,
  dir: string,
  verb: string,
  args: any,
  snapshotText?: string
): Promise<string> {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  // evidence_dir 재사용 시 이전 세대 4파일을 선삭제한다(F4). 안 그러면 이번 회차가
  // 중간 중단해도 이전 세대의 meta.json(완결 마커)이 남아 세대혼합 번들이 "완결"로 오판된다.
  for (const f of ["screenshot.png", "snapshot.txt", "dom.html", "meta.json"]) {
    rmSync(join(dir, f), { force: true });
  }
  await page.screenshot({ path: join(dir, "screenshot.png"), fullPage: false });
  const snap = snapshotText ?? (await buildSnapshot(page)).text;
  writeFileSync(join(dir, "snapshot.txt"), snap, "utf8");
  // dom.html: meta.json의 dom_sha256을 독립 재계산 가능하게 원본 DOM 보존.
  const html = await page.content();
  writeFileSync(join(dir, "dom.html"), html, "utf8");
  const meta = {
    url: page.url(),
    ts: new Date().toISOString(),
    dom_sha256: createHash("sha256").update(html).digest("hex"),
    verb,
    args,
  };
  // meta.json 반드시 마지막에 — 반쪽 번들 차단(완결 마커). tmp 기록 후 rename 으로 원자화해
  // 부분 기록된 meta.json 이 완결 마커로 보이지 않게 한다.
  const metaTmp = join(dir, "meta.json.tmp");
  writeFileSync(metaTmp, JSON.stringify(meta, null, 2), "utf8");
  renameSync(metaTmp, join(dir, "meta.json"));
  lastEvidencePath = dir; // 관측(observe·status)이 마지막 증거 위치를 노출
  return dir;
}

// --- 동사 디스패치 ---
async function dispatch(verb: string, args: any): Promise<any> {
  touch();
  const cid = args.context || "default";

  switch (verb) {
    case "status": {
      return {
        pid: process.pid,
        headless: HEADLESS,
        contexts: [...contexts.entries()].map(([id, c]) => ({ id, control: c.control, profile: c.profile, url: c.page.url() })),
        dialogs: dialogLog.length,
        idle_ms: Date.now() - lastActivity,
        last_evidence_path: lastEvidencePath,
      };
    }

    case "open": {
      const profile: "agent" | "human" = args.profile === "human" ? "human" : "agent";
      // human 프로필은 CEO 결재 경유(CLI가 cys feed push --wait exit 0 시 args.approved 전달)만 허용.
      // 결재 없이 온 요청은 거부 — 배선 부재가 아니라 정책적 거부.
      if (profile === "human" && !args.approved) {
        throw new RpcError("APPROVAL_REQUIRED", "human 프로필은 CEO 결재 필요 — 미결재 거부");
      }
      const url: string = args.url;
      if (!url) throw new RpcError("BAD_ARGS", "url 필요");
      if (!contexts.has(cid) && contexts.size >= MAX_CONTEXTS) {
        throw new RpcError("BUSY", `context 동시 상한 ${MAX_CONTEXTS} 초과 — backoff 후 재시도`);
      }
      const bc = await ensureBrowser(profile);
      let c = contexts.get(cid);
      if (!c) {
        const page = await bc.newPage();
        page.on("dialog", (d: Dialog) => {
          dialogLog.push(`${new Date().toISOString()} ${d.type()}: ${d.message()}`);
          d.dismiss().catch(() => {});
        });
        c = { page, control: "agent", profile };
        contexts.set(cid, c);
      }
      assertAgentControl(c);
      await c.page.goto(url, { waitUntil: "load", timeout: 30000 });
      let evidence_path: string | undefined;
      if (args.evidence_dir) evidence_path = await writeEvidence(c.page, args.evidence_dir, verb, args);
      return { context: cid, url: c.page.url(), title: await c.page.title(), profile: c.profile, evidence_path };
    }

    case "observe": {
      // P2-a 관측: 에이전트 동사와 동일 경로(open)로 headful 열되, 관측 상태를 반환한다.
      // 사람이 터미널 옆 headful 창을 직접 본다(창 배치 AppleScript 없음 — 런북 절차 참조).
      await dispatch("open", args);
      const c = getCtx(cid);
      return {
        context: cid,
        url: c.page.url(),
        control: c.control,
        profile: c.profile,
        last_evidence_path: lastEvidencePath,
      };
    }

    case "snapshot": {
      const c = getCtx(cid);
      const snap = await buildSnapshot(c.page);
      let evidence_path: string | undefined;
      if (args.evidence_dir) evidence_path = await writeEvidence(c.page, args.evidence_dir, verb, args, snap.text);
      return { text: snap.text, truncated: snap.truncated, count: snap.raw.items.length, evidence_path };
    }

    case "click": {
      const c = getCtx(cid);
      assertNotHumanProfile(c, verb);
      assertAgentControl(c);
      await c.page.click(selectorFor(args), { timeout: args.timeout || 10000 });
      return { ok: true };
    }

    case "fill": {
      const c = getCtx(cid);
      assertNotHumanProfile(c, verb);
      assertAgentControl(c);
      await c.page.fill(selectorFor(args), String(args.value ?? ""), { timeout: args.timeout || 10000 });
      return { ok: true };
    }

    case "type": {
      const c = getCtx(cid);
      assertNotHumanProfile(c, verb);
      assertAgentControl(c);
      const text = String(args.text ?? "");
      if (args.ref || args.selector) await c.page.locator(selectorFor(args)).pressSequentially(text, { timeout: args.timeout || 10000 });
      else await c.page.keyboard.type(text);
      return { ok: true };
    }

    case "press": {
      const c = getCtx(cid);
      assertNotHumanProfile(c, verb);
      assertAgentControl(c);
      await c.page.keyboard.press(String(args.key));
      return { ok: true };
    }

    case "eval": {
      const c = getCtx(cid);
      assertNotHumanProfile(c, verb);
      assertAgentControl(c);
      const result = await c.page.evaluate(String(args.expression));
      return { result };
    }

    case "screenshot": {
      const c = getCtx(cid);
      const path = args.path;
      if (!path) throw new RpcError("BAD_ARGS", "path 필요");
      await c.page.screenshot({ path, fullPage: !!args.full_page });
      let evidence_path: string | undefined;
      if (args.evidence_dir) evidence_path = await writeEvidence(c.page, args.evidence_dir, verb, args);
      return { path, evidence_path };
    }

    case "wait": {
      const c = getCtx(cid);
      const timeout = args.timeout || 15000;
      if (args.selector) await c.page.waitForSelector(args.selector, { timeout });
      else if (args.text) await c.page.getByText(args.text).first().waitFor({ timeout });
      else if (args.url) await c.page.waitForURL(args.url, { timeout });
      else await c.page.waitForLoadState(args.load || "load", { timeout });
      return { ok: true };
    }

    case "verify": {
      const c = getCtx(cid);
      const reasons: string[] = [];
      let pass = true;
      // 다중 기대값 계약: expect_text/expect_selector는 배열(여러 개)일 수 있고 전부 대조한다.
      // 하나라도 미발견이면 FAIL. 단수 문자열도 허용(하위호환) — asList가 정규화한다.
      const asList = (v: any): string[] =>
        v == null ? [] : (Array.isArray(v) ? v.map(String) : [String(v)]);
      const texts = asList(args.expect_text);
      const selectors = asList(args.expect_selector);
      if (texts.length === 0 && selectors.length === 0) {
        throw new RpcError("BAD_ARGS", "expect_text 또는 expect_selector 필요");
      }
      if (texts.length) {
        // 가시 텍스트(innerText)+title만 대조 — 주석·스크립트·속성 안의 문자열이
        // 게이트를 오통과(false PASS)시키지 않도록 raw HTML은 쓰지 않는다.
        const visible = String(
          await c.page.evaluate(
            "((document.body ? document.body.innerText : '') + ' ' + (document.title || ''))"
          )
        );
        for (const t of texts) {
          if (visible.includes(t)) reasons.push(`expect_text 확인: "${t}"`);
          else { pass = false; reasons.push(`expect_text 미발견: "${t}"`); }
        }
      }
      for (const sel of selectors) {
        const el = await c.page.$(sel);
        if (el) reasons.push(`expect_selector 확인: "${sel}"`);
        else { pass = false; reasons.push(`expect_selector 미발견: "${sel}"`); }
      }
      const verdict = pass ? "PASS" : "FAIL";
      let evidence_path: string | undefined;
      if (args.evidence_dir) evidence_path = await writeEvidence(c.page, args.evidence_dir, verb, args);
      return { verdict, reasons, evidence_path };
    }

    case "pick": {
      // P4 디자인 모드: 오버레이 주입 → 사람이 요소 클릭 → {selector,text,rect,url} 회수.
      // headless엔 클릭할 사람이 없어 timeout 후 에러(브리프 미생성).
      const c = getCtx(cid);
      const timeout = args.timeout || 60000;
      if (!pickBound.has(c.page)) {
        // 바인딩은 페이지당 1회 — 콜백은 그 시점 등록된 resolver로 위임(재-pick 지원).
        await c.page.exposeBinding("__cysPick", (_src: any, data: any) => {
          const r = pickResolvers.get(c.page);
          if (r) r(data);
        });
        pickBound.add(c.page);
      }
      const picked = await new Promise<any>((resolve, reject) => {
        const timer = setTimeout(() => {
          pickResolvers.delete(c.page);
          c.page.evaluate("window.__cysPickCleanup && window.__cysPickCleanup()").catch(() => {});
          reject(new RpcError("PICK_TIMEOUT", `pick 타임아웃(${timeout}ms) — 클릭 없음`));
        }, timeout);
        pickResolvers.set(c.page, (data) => {
          clearTimeout(timer);
          pickResolvers.delete(c.page);
          resolve(data);
        });
        c.page.evaluate(PICK_OVERLAY_JS).catch((e: any) => {
          clearTimeout(timer);
          pickResolvers.delete(c.page);
          reject(e);
        });
      });
      let screenshot_path: string | undefined;
      if (args.path) {
        await c.page.screenshot({ path: args.path, fullPage: false });
        screenshot_path = args.path;
      }
      return { picked, screenshot_path, url: c.page.url() };
    }

    case "control": {
      const c = getCtx(cid);
      const action = args.action;
      if (action === "acquire") {
        c.control = args.actor === "human" ? "human" : "agent";
      } else if (action === "release") {
        c.control = "agent";
      } else {
        throw new RpcError("BAD_ARGS", "action=acquire|release 필요");
      }
      return { context: cid, control: c.control };
    }

    case "close": {
      const c = contexts.get(cid);
      if (c) {
        await c.page.close().catch(() => {});
        contexts.delete(cid);
      }
      return { ok: true, closed: cid };
    }

    default:
      throw new RpcError("UNKNOWN_VERB", `미지 동사: ${verb}`);
  }
}

// --- HTTP 서버 (127.0.0.1, port 0) ---
const token = genToken();

// 상수시간 토큰 비교(F6) — 길이 불일치는 즉시 false(timingSafeEqual은 길이 다르면 throw).
// 둘 다 hex 토큰이라 latin1 바이트 인코딩으로 충분하고, 길이 정보 누출은 토큰 자릿수 고정이라 무해.
function tokenEqual(given: string, expected: string): boolean {
  const a = Buffer.from(given, "utf8");
  const b = Buffer.from(expected, "utf8");
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

const server = Bun.serve({
  hostname: "127.0.0.1",
  port: 0,
  async fetch(req) {
    const url = new URL(req.url);
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length !== 2 || !tokenEqual(parts[0], token) || parts[1] !== "rpc") {
      return new Response(JSON.stringify({ ok: false, error: { code: "FORBIDDEN", message: "bad token/path" } }), { status: 403 });
    }
    if (req.method !== "POST") {
      return new Response(JSON.stringify({ ok: false, error: { code: "BAD_METHOD", message: "POST only" } }), { status: 405 });
    }
    let body: any;
    try {
      body = await req.json();
    } catch {
      return new Response(JSON.stringify({ ok: false, error: { code: "BAD_JSON", message: "invalid json" } }), { status: 400 });
    }
    const { verb, args } = body || {};
    try {
      const result = await dispatch(String(verb), args || {});
      return new Response(JSON.stringify({ ok: true, result }), { headers: { "content-type": "application/json" } });
    } catch (e: any) {
      const code = e instanceof RpcError ? e.code : "ERROR";
      return new Response(JSON.stringify({ ok: false, error: { code, message: String(e?.message || e) } }), {
        headers: { "content-type": "application/json" },
      });
    }
  },
});

const state: BrowserState = { pid: process.pid, port: server.port, token };
writeState(state);

// 유휴 자동 종료
setInterval(async () => {
  if (Date.now() - lastActivity > IDLE_TIMEOUT_MS) {
    try {
      if (persistentCtx) await persistentCtx.close();
    } catch {}
    process.exit(0);
  }
}, 60 * 1000);

async function shutdown() {
  try {
    if (persistentCtx) await persistentCtx.close();
  } catch {}
  process.exit(0);
}
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

// eslint-disable-next-line no-console
console.error(`browserd up: pid=${process.pid} port=${server.port} headless=${HEADLESS}`);
