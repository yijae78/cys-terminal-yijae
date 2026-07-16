// ftdrop.ts 순수 함수 회귀 테스트 (bun test — 신규 의존성 0).
import { describe, expect, test } from "bun:test";
import { insertionText, isStreaming, relativize } from "./ftdrop";

describe("relativize", () => {
  test("cwd 안 경로는 상대화", () => {
    expect(relativize("/a/b/c.txt", "/a/b")).toBe("c.txt");
    expect(relativize("/a/b/d/e.md", "/a/b")).toBe("d/e.md");
  });
  test("cwd 자신은 .", () => {
    expect(relativize("/a/b", "/a/b")).toBe(".");
  });
  test("cwd 바깥·cwd 없음은 절대경로 유지", () => {
    expect(relativize("/x/y.txt", "/a/b")).toBe("/x/y.txt");
    expect(relativize("/a/bb/c.txt", "/a/b")).toBe("/a/bb/c.txt"); // 접두 오탐 방지
    expect(relativize("/x/y.txt", null)).toBe("/x/y.txt");
  });
});

describe("insertionText", () => {
  test("에이전트 pane은 @멘션 + 끝 공백", () => {
    expect(insertionText(["/a/b/c.txt"], { agent: true, isWin: false, cwd: "/a/b" })).toBe("@c.txt ");
  });
  test("에이전트 pane 다중 경로는 공백 연결", () => {
    expect(insertionText(["/a/b/c.txt", "/a/b/d.md"], { agent: true, isWin: false, cwd: "/a/b" })).toBe(
      "@c.txt @d.md ",
    );
  });
  test("에이전트 pane도 공백 포함 경로는 셸 인용 폴백(@멘션 파손 방지)", () => {
    expect(insertionText(["/a/b/my file.txt"], { agent: true, isWin: false, cwd: "/a/b" })).toBe(
      "'/a/b/my file.txt' ",
    );
  });
  test("미등록 pane은 셸 인용", () => {
    expect(insertionText(["/a/b/c.txt"], { agent: false, isWin: false, cwd: "/a/b" })).toBe("'/a/b/c.txt' ");
  });
});

describe("isStreaming", () => {
  test("threshold 내 출력=스트리밍", () => {
    expect(isStreaming(1000, 2000)).toBe(true);
    expect(isStreaming(1000, 4001)).toBe(false);
  });
  test("출력 이력 없음(0)은 스트리밍 아님", () => {
    expect(isStreaming(0, 1)).toBe(false);
  });
});
