// pick.test.ts — P4 디자인 모드 캡처 파이프 실측.
// 실제 chromium(headless)에 fixture를 로드하고, PICK_OVERLAY_JS를 주입한 뒤
// 프로그래매틱 클릭(playwright)으로 사람 클릭을 시뮬레이션해 __cysPick 회수 데이터를 검증한다.
// (서버 exposeBinding 대신 테스트가 직접 바인딩을 심어 오버레이 로직만 격리 실측.)
import { test, expect, afterAll } from "bun:test";
import { chromium, type BrowserContext } from "playwright-core";
import { PICK_OVERLAY_JS } from "../lib";

let ctx: BrowserContext | null = null;

afterAll(async () => {
  if (ctx) await ctx.close().catch(() => {});
});

async function launch(): Promise<BrowserContext | null> {
  const common = { headless: true, args: ["--no-first-run", "--no-default-browser-check"] };
  try {
    return await chromium.launchPersistentContext("", { ...common, channel: "chrome" } as any);
  } catch {
    try {
      return await chromium.launchPersistentContext("", common as any);
    } catch {
      return null; // 브라우저 미가용 환경 — 스킵
    }
  }
}

const OK_FIXTURE =
  "data:text/html;charset=utf-8," +
  encodeURIComponent(
    '<!doctype html><html><head><meta charset="utf-8"></head><body><h1>주문</h1>' +
      '<button id="retry">다시 시도</button>' +
      '<p class="s">a</p><p class="s">타깃 문단</p></body></html>'
  );

test("pick 오버레이: 프로그래매틱 클릭 → selector·text·rect·url 회수", async () => {
  ctx = await launch();
  if (!ctx) {
    console.warn("chromium 미가용 — pick 캡처 테스트 스킵");
    return;
  }
  const page = await ctx.newPage();
  await page.goto(OK_FIXTURE, { waitUntil: "load" });

  // 서버의 exposeBinding 역할을 테스트가 대신 — 클릭 데이터를 resolve하는 바인딩 주입.
  let resolve!: (v: any) => void;
  const picked = new Promise<any>((r) => (resolve = r));
  await page.exposeBinding("__cysPick", (_src, data) => resolve(data));

  const installed = await page.evaluate(PICK_OVERLAY_JS);
  expect(installed).toBe("installed");

  // 사람 클릭 시뮬레이션 — id 있는 버튼.
  await page.click("#retry");
  const data = await picked;

  expect(data.selector).toBe("#retry");
  expect(data.text).toBe("다시 시도");
  expect(data.url).toContain("data:text/html");
  expect(typeof data.rect.width).toBe("number");
  expect(data.rect.width).toBeGreaterThan(0);
});

test("pick 오버레이: id 없는 요소는 nth-of-type 경로 selector", async () => {
  if (!ctx) return; // 위 테스트에서 스킵된 경우
  const page = await ctx.newPage();
  await page.goto(OK_FIXTURE, { waitUntil: "load" });

  let resolve!: (v: any) => void;
  const picked = new Promise<any>((r) => (resolve = r));
  await page.exposeBinding("__cysPick", (_src, data) => resolve(data));
  await page.evaluate(PICK_OVERLAY_JS);

  // 두 번째 .s 문단(id 없음) → nth-of-type 포함 경로.
  await page.click("p.s:nth-of-type(2)");
  const data = await picked;

  expect(data.selector).toContain("nth-of-type");
  expect(data.text).toBe("타깃 문단");
});
