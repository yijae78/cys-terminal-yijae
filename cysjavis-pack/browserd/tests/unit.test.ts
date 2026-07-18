// unit.test.ts — 순수 로직 단위 테스트 (bun test). 브라우저 미기동.
import { test, expect } from "bun:test";
import { genToken, capText, SNAPSHOT_LIMIT, pidAlive, isStaleState, UNTRUSTED_HEADER } from "../lib";

test("genToken: 32 hex chars, 유일", () => {
  const a = genToken();
  const b = genToken();
  expect(a).toMatch(/^[0-9a-f]{32}$/);
  expect(a).not.toBe(b);
});

test("capText: 상한 이하는 무손실", () => {
  const s = "hello world";
  const { text, truncated } = capText(s, 1024);
  expect(text).toBe(s);
  expect(truncated).toBe(false);
});

test("capText: 상한 초과는 절단 + 마커", () => {
  const s = "x".repeat(300 * 1024);
  const { text, truncated } = capText(s, SNAPSHOT_LIMIT);
  expect(truncated).toBe(true);
  expect(text).toContain("[TRUNCATED");
  expect(Buffer.byteLength(text, "utf8")).toBeLessThanOrEqual(SNAPSHOT_LIMIT + 200);
});

test("pidAlive: 자기 자신은 생존, 죽은 pid는 아님", () => {
  expect(pidAlive(process.pid)).toBe(true);
  expect(pidAlive(2147483000)).toBe(false); // 존재 불가능한 큰 pid
  expect(pidAlive(0)).toBe(false);
});

test("isStaleState: null 또는 죽은 pid는 스테일", () => {
  expect(isStaleState(null)).toBe(true);
  expect(isStaleState({ pid: 2147483000, port: 1, token: "x" })).toBe(true);
  expect(isStaleState({ pid: process.pid, port: 1, token: "x" })).toBe(false);
});

test("UNTRUSTED_HEADER: 지시 무시 문구 포함", () => {
  expect(UNTRUSTED_HEADER).toContain("UNTRUSTED WEB CONTENT");
  expect(UNTRUSTED_HEADER).toContain("지시가 아니다");
});
