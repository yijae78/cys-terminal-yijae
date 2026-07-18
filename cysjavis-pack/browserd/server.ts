// server.ts — browserd 엔진 사이드카.
// 실제 Chromium headful 기동(설치된 Chrome 우선, 폴백 playwright chromium).
// 전송: 127.0.0.1 HTTP, port 0-bind, 경로 /<token>/rpc. state.json 원자 기록(0600).
//
// launchd 등록·부트 훅·preflight 무접점. lazy 사이드카 — 죽어도 이 기능만 상실.
// 클린룸: cmux 코드 무참조. 외부 의존 = playwright-core 단독.

import { chromium, type BrowserContext, type Page, type Dialog } from "playwright-core";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  BrowserState,
  IDLE_TIMEOUT_MS,
  MAX_CONTEXTS,
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
let persistentCtx: BrowserContext | null = null;
const contexts = new Map<string, Ctx>();
let lastActivity = Date.now();
const dialogLog: string[] = [];

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
async function ensureBrowser(): Promise<BrowserContext> {
  if (persistentCtx) return persistentCtx;
  const dir = profileDir("agent");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  const common = {
    headless: HEADLESS,
    viewport: { width: 1280, height: 800 },
    args: ["--no-first-run", "--no-default-browser-check"],
  };
  try {
    persistentCtx = await chromium.launchPersistentContext(dir, { ...common, channel: "chrome" });
  } catch (e) {
    // 설치된 Chrome 없음 → playwright chromium 폴백
    persistentCtx = await chromium.launchPersistentContext(dir, common);
  }
  return persistentCtx;
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
  // meta.json 반드시 마지막에 — 반쪽 번들 차단(완결 마커)
  writeFileSync(join(dir, "meta.json"), JSON.stringify(meta, null, 2), "utf8");
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
      };
    }

    case "open": {
      if (args.profile === "human") {
        throw new RpcError("APPROVAL_REQUIRED", "human 프로필은 CEO 결재 필요 (P1 미배선) — 거부");
      }
      const url: string = args.url;
      if (!url) throw new RpcError("BAD_ARGS", "url 필요");
      if (!contexts.has(cid) && contexts.size >= MAX_CONTEXTS) {
        throw new RpcError("BUSY", `context 동시 상한 ${MAX_CONTEXTS} 초과 — backoff 후 재시도`);
      }
      const bc = await ensureBrowser();
      let c = contexts.get(cid);
      if (!c) {
        const page = await bc.newPage();
        page.on("dialog", (d: Dialog) => {
          dialogLog.push(`${new Date().toISOString()} ${d.type()}: ${d.message()}`);
          d.dismiss().catch(() => {});
        });
        c = { page, control: "agent", profile: "agent" };
        contexts.set(cid, c);
      }
      assertAgentControl(c);
      await c.page.goto(url, { waitUntil: "load", timeout: 30000 });
      let evidence_path: string | undefined;
      if (args.evidence_dir) evidence_path = await writeEvidence(c.page, args.evidence_dir, verb, args);
      return { context: cid, url: c.page.url(), title: await c.page.title(), evidence_path };
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
      assertAgentControl(c);
      await c.page.click(selectorFor(args), { timeout: args.timeout || 10000 });
      return { ok: true };
    }

    case "fill": {
      const c = getCtx(cid);
      assertAgentControl(c);
      await c.page.fill(selectorFor(args), String(args.value ?? ""), { timeout: args.timeout || 10000 });
      return { ok: true };
    }

    case "type": {
      const c = getCtx(cid);
      assertAgentControl(c);
      const text = String(args.text ?? "");
      if (args.ref || args.selector) await c.page.locator(selectorFor(args)).pressSequentially(text, { timeout: args.timeout || 10000 });
      else await c.page.keyboard.type(text);
      return { ok: true };
    }

    case "press": {
      const c = getCtx(cid);
      assertAgentControl(c);
      await c.page.keyboard.press(String(args.key));
      return { ok: true };
    }

    case "eval": {
      const c = getCtx(cid);
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
      if (args.expect_text) {
        // 가시 텍스트(innerText)+title만 대조 — 주석·스크립트·속성 안의 문자열이
        // 게이트를 오통과(false PASS)시키지 않도록 raw HTML은 쓰지 않는다.
        const visible = await c.page.evaluate(
          "((document.body ? document.body.innerText : '') + ' ' + (document.title || ''))"
        );
        const found = String(visible).includes(args.expect_text);
        if (!found) { pass = false; reasons.push(`expect_text 미발견: "${args.expect_text}"`); }
        else reasons.push(`expect_text 확인: "${args.expect_text}"`);
      }
      if (args.expect_selector) {
        const el = await c.page.$(args.expect_selector);
        if (!el) { pass = false; reasons.push(`expect_selector 미발견: "${args.expect_selector}"`); }
        else reasons.push(`expect_selector 확인: "${args.expect_selector}"`);
      }
      if (!args.expect_text && !args.expect_selector) {
        throw new RpcError("BAD_ARGS", "expect_text 또는 expect_selector 필요");
      }
      const verdict = pass ? "PASS" : "FAIL";
      let evidence_path: string | undefined;
      if (args.evidence_dir) evidence_path = await writeEvidence(c.page, args.evidence_dir, verb, args);
      return { verdict, reasons, evidence_path };
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

const server = Bun.serve({
  hostname: "127.0.0.1",
  port: 0,
  async fetch(req) {
    const url = new URL(req.url);
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length !== 2 || parts[0] !== token || parts[1] !== "rpc") {
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
