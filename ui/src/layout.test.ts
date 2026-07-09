// layout.ts 순수 함수 회귀 테스트 (bun test — 신규 의존성 0).
//
// R1 수용분: 자동입양 균등화가 "입양된 그 ws"에만 적용되고(비활성 부서 ws 입양 시 활성 ws만
// 균등화되던 버그), 입양 안 된 ws의 트리는 참조까지 그대로인지 검증한다.
// + roleLayout(f3a2986 가로 균등)·evenComb 결정론 회귀.
import { describe, it, expect } from "bun:test";
import { evenComb, roleLayout, equalizeAdoptedTrees, type LayoutNode } from "./layout";

const pane = (sid: number): LayoutNode => ({ type: "pane", sid });

// 트리를 좌→우 리프 sid 배열로 평탄화 (row 콤은 좌→우 순서 보존).
function leaves(n: LayoutNode | null, out: number[] = []): number[] {
  if (!n) return out;
  if (n.type === "pane") out.push(n.sid);
  else {
    leaves(n.a, out);
    leaves(n.b, out);
  }
  return out;
}

// 균등 row 콤인지: 모든 split이 dir=row이고 ratio가 1/(남은 리프 수)인지 검증.
function expectEvenRowComb(n: LayoutNode, total: number) {
  let node = n;
  let remain = total;
  while (node.type === "split") {
    expect(node.dir).toBe("row");
    expect(node.ratio).toBeCloseTo(1 / remain);
    expect(node.a.type).toBe("pane");
    node = node.b;
    remain--;
  }
  expect(remain).toBe(1); // 마지막 리프 1개
}

describe("evenComb — 균등 콤 결정론", () => {
  it("N개 리프를 1/N·1/(N-1)·…·1/2 ratio 체인으로 짠다", () => {
    const comb = evenComb([pane(1), pane(2), pane(3), pane(4)], "row");
    expect(leaves(comb)).toEqual([1, 2, 3, 4]);
    expectEvenRowComb(comb, 4);
  });
  it("리프 1개는 그 pane 자체", () => {
    expect(evenComb([pane(7)], "row")).toEqual(pane(7));
  });
});

describe("roleLayout — 역할 순서 가로 균등 배치 (f3a2986)", () => {
  it("master·cso·worker·agy·codex 순서로 전부 개별 가로 컬럼", () => {
    const roleOf = new Map<number, string | null>([
      [10, "reviewer-codex"],
      [11, "master"],
      [12, null], // 미분류 → 가운데
      [13, "cso"],
      [14, "reviewer-gemini"],
    ]);
    const tree = roleLayout([10, 11, 12, 13, 14], roleOf);
    expect(leaves(tree)).toEqual([11, 13, 12, 14, 10]); // master, cso, 미분류, agy, codex
    expectEvenRowComb(tree, 5);
  });
});

describe("equalizeAdoptedTrees — 입양된 ws만 균등화 (R1)", () => {
  type Ws = { tree: LayoutNode | null; socket?: string };
  const chain = (a: number, b: number, c: number): LayoutNode => ({
    // 자동입양의 나이브 체인 {split row, a: tree, b: pane} 형태 — ratio 없음(불균등)
    type: "split",
    dir: "row",
    a: { type: "split", dir: "row", a: pane(a), b: pane(b) },
    b: pane(c),
  });

  it("비활성 ws 입양 시 그 ws만 균등화되고 활성 ws 트리는 참조 그대로", () => {
    const activeTree = chain(1, 2, 3);
    const active: Ws = { tree: activeTree }; // 입양 없음(활성)
    const inactive: Ws = { tree: chain(21, 22, 23), socket: "dept-b" }; // 여기에 입양 발생(비활성)
    const roles = new Map<number, string | null>([
      [21, "master"],
      [22, "worker"],
      [23, "reviewer-codex"],
    ]);

    const adopted = new Map<Ws, Map<number, string | null>>([[inactive, roles]]);
    equalizeAdoptedTrees(adopted, (w) => leaves(w.tree));

    // 입양 안 된 활성 ws: 참조까지 무변경 (균등화 대상 아님)
    expect(active.tree).toBe(activeTree);
    // 입양된 비활성 ws: 역할 순서 균등 row 콤으로 재배치
    expect(leaves(inactive.tree)).toEqual([21, 22, 23]);
    expectEvenRowComb(inactive.tree as LayoutNode, 3);
  });

  it("live pane이 2개 미만인 ws는 건드리지 않는다", () => {
    const t = pane(5);
    const w: Ws = { tree: t };
    equalizeAdoptedTrees(new Map([[w, new Map<number, string | null>()]]), () => [5]);
    expect(w.tree).toBe(t);
  });

  it("liveOf가 거른 죽은 sid는 새 트리에서 빠진다", () => {
    const w: Ws = { tree: chain(31, 32, 99) }; // 99 = 죽은 pane
    const roles = new Map<number, string | null>([
      [31, "master"],
      [32, null],
      [99, "worker"],
    ]);
    equalizeAdoptedTrees(new Map([[w, roles]]), () => [31, 32]); // liveOf: 99 제외
    expect(leaves(w.tree)).toEqual([31, 32]);
    expectEvenRowComb(w.tree as LayoutNode, 2);
  });
});
