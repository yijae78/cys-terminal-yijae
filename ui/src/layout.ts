// 정렬(균등 배치)의 순수 트리 변형 로직 (DOM·데몬 무접촉 — main.ts의 actionEqualize·자동입양이 호출).
//
// 역할(role) 기반 고정 배치: 살아있는 surface를 역할 순서(master·cso·worker·agy·codex)로
// 전부 같은 폭 가로 컬럼으로 균등 재배치한다 — 세로 분열 없이 모두 옆으로 나란히(f3a2986).
// 트리 위상만 새로 짜므로 divider 드래그 등 수동 크기 조절 배선은 호출측에서 그대로 보존된다.

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

export function firstWithRole(sids: number[], roleOf: Map<number, string | null>, role: string): number | null {
  for (const sid of sids) if (roleOf.get(sid) === role) return sid;
  return null;
}

export function roleLayout(sids: number[], roleOf: Map<number, string | null>): LayoutNode {
  const master = firstWithRole(sids, roleOf, "master");
  const cso = firstWithRole(sids, roleOf, "cso");
  const agy = firstWithRole(sids, roleOf, "reviewer-gemini"); // 안티그래피티
  const codex = firstWithRole(sids, roleOf, "reviewer-codex");
  const corners = new Set([master, cso, agy, codex].filter((x): x is number => x != null));
  const middle = sids.filter((sid) => !corners.has(sid)); // worker·미분류 전부 가운데
  const pane = (sid: number): LayoutNode => ({ type: "pane", sid });

  const columns: LayoutNode[] = [];
  // 전부 가로 균등 배치 — master · cso · worker(미분류 포함) · agy · codex 순서로 각자 개별 컬럼.
  // (세로 분열 없이 모든 pane을 같은 폭 가로 컬럼으로 정렬)
  if (master != null) columns.push(pane(master));
  if (cso != null) columns.push(pane(cso));
  for (const sid of middle) columns.push(pane(sid));
  if (agy != null) columns.push(pane(agy));
  if (codex != null) columns.push(pane(codex));

  return evenComb(columns, "row"); // 컬럼들을 같은 폭으로 가로 배치
}

// 자동입양 후 균등화(R1): 입양이 일어난 workspace들만 각자 균등 배치한다 — 활성 ws가 아니라
// "입양된 그 ws"가 대상(비활성 부서 ws 입양 시 활성 ws만 균등화되던 버그 수정).
// adopted: [ws, 그 ws 소켓의 roleOf] 쌍 — roleOf는 호출측(refreshPaneTitles)이 이미 받은
// surface.list 응답에서 만들므로 추가 데몬 호출이 없다. liveOf: 그 ws에서 실존 pane sid만.
// 입양 안 된 ws의 tree는 절대 건드리지 않는다(참조 그대로).
export function equalizeAdoptedTrees<W extends { tree: LayoutNode | null }>(
  adopted: Iterable<[W, Map<number, string | null>]>,
  liveOf: (w: W) => number[],
): void {
  for (const [w, roles] of adopted) {
    const live = liveOf(w);
    if (live.length < 2) continue; // 0~1개는 정렬할 대상이 없음
    w.tree = roleLayout(live, roles);
  }
}
