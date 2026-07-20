// transfer.ts 순수 함수 회귀 테스트 (bun test — 신규 의존성 0).
import { describe, expect, test } from "bun:test";
import { appendPane, transferTrees, treeSids, type TNode } from "./transfer";

const pane = (sid: number): TNode => ({ type: "pane", sid });
const split = (a: TNode, b: TNode): TNode => ({ type: "split", dir: "row", a, b });

describe("transferTrees", () => {
  test("단일 pane 트리에서 떼어내면 src=null, dest에 편입", () => {
    const r = transferTrees(pane(1), null, 1)!;
    expect(r.src).toBeNull();
    expect(treeSids(r.dest)).toEqual([1]);
  });
  test("분할 트리에서 떼면 형제로 붕괴 + dest 말단 분할", () => {
    const r = transferTrees(split(pane(1), pane(2)), pane(9), 2)!;
    expect(treeSids(r.src)).toEqual([1]);
    expect(treeSids(r.dest)).toEqual([9, 2]);
    expect(r.dest.type).toBe("split");
  });
  test("src에 없는 sid는 null(무변경 신호)", () => {
    expect(transferTrees(pane(1), null, 7)).toBeNull();
    expect(transferTrees(null, pane(1), 1)).toBeNull();
  });
  test("dest에 같은 sid가 이미 있으면 거부(유령 pane 차단)", () => {
    expect(transferTrees(split(pane(1), pane(2)), pane(1), 1)).toBeNull();
  });
  test("깊은 트리에서도 제거·유일성 보존", () => {
    const src = split(split(pane(1), pane(2)), pane(3));
    const r = transferTrees(src, split(pane(8), pane(9)), 2)!;
    expect(treeSids(r.src)).toEqual([1, 3]);
    expect(treeSids(r.dest)).toEqual([8, 9, 2]);
    // 원본 불변(순수성)
    expect(treeSids(src)).toEqual([1, 2, 3]);
  });
});

describe("appendPane", () => {
  test("빈 트리는 pane 단독", () => {
    expect(appendPane(null, 5)).toEqual({ type: "pane", sid: 5 });
  });
});
