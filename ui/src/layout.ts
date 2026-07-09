// 정렬(균등 배치)의 순수 트리 변형 로직 (DOM·데몬 무접촉 — main.ts의 actionEqualize·자동입양이 호출).
//
// ★순서 보존형 정렬(오너 요구 R2-3): 정렬은 현재 트리의 좌→우 pane 순서를 그대로 보존하고
// **폭만 균등화**한다 — "내가 옮긴 곳이 내 자리". 역할(role) 기반 재배치는 정렬에서 제거됐다.
// 역할 기반 초기 배치는 자동입양 시점의 rolePri 정렬(main.ts refreshPaneTitles)로만 유지되므로
// 부트 시 master·cso·worker·리뷰어 순서는 종전과 동일하고, dashboard는 입양 시 끝에 붙어
// 자연히 오른쪽 끝이 된다. 트리 위상만 새로 짜므로 divider 드래그 배선은 호출측에서 그대로 보존.

// main.ts의 Node와 구조 동일(구조적 타이핑으로 상호 대입 가능) — reorder.ts의 ReorderWs 패턴.
export type LayoutNode =
  | { type: "split"; dir: "row" | "col"; ratio?: number; a: LayoutNode; b: LayoutNode }
  | { type: "pane"; sid: number };

export function evenComb(nodes: LayoutNode[], dir: "row" | "col"): LayoutNode {
  let acc = nodes[nodes.length - 1];
  for (let i = nodes.length - 2; i >= 0; i--) {
    acc = { type: "split", dir, ratio: 1 / (nodes.length - i), a: nodes[i], b: acc };
  }
  return acc;
}

// 순서 보존 균등화: 좌→우 sid 순서(liveSids)를 그대로 같은 폭 가로 컬럼으로 짠다.
export function orderPreservingEqualize(liveSids: number[]): LayoutNode {
  return evenComb(liveSids.map((sid): LayoutNode => ({ type: "pane", sid })), "row");
}

// 자동입양 후 균등화(codex R1 issue1): 입양이 일어난 workspace들만 각자 균등 배치한다 —
// 활성 ws가 아니라 "입양된 그 ws"가 대상(비활성 부서 ws 입양 시 활성 ws만 균등화되던 버그 수정).
// liveOf: 그 ws의 현재 트리 좌→우 순서에서 실존 pane sid만(순서 보존의 원천).
// 입양 안 된 ws의 tree는 절대 건드리지 않는다(참조 그대로).
export function equalizeAdoptedTrees<W extends { tree: LayoutNode | null }>(
  adopted: Iterable<W>,
  liveOf: (w: W) => number[],
): void {
  for (const w of adopted) {
    const live = liveOf(w);
    if (live.length < 2) continue; // 0~1개는 정렬할 대상이 없음
    w.tree = orderPreservingEqualize(live);
  }
}
