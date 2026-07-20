// pane 전출(동일 socket 워크스페이스 간)의 순수 트리 변형 로직 (DOM 무접촉 — main.ts transferPaneToWs가 배선).
//
// 불변식: ①원자성 — 실패(null 반환) 시 호출측이 두 트리 모두 무변경 유지 ②sid 유일성 —
// src에서 제거한 노드만 dest에 붙이고, dest에 같은 sid가 이미 있으면 거부(유령 pane 차단).

import type { WebNode } from "./webpane";

export type TNode =
  | { type: "split"; dir: "row" | "col"; ratio?: number; a: TNode; b: TNode }
  | { type: "pane"; sid: number }
  // web pane 리프 — 전출은 터미널 sid만 옮기고 web 노드는 제자리 보존(sid 없음 → 순회 스킵).
  | WebNode;

export function treeSids(node: TNode | null, out: number[] = []): number[] {
  if (!node) return out;
  if (node.type === "pane") out.push(node.sid);
  else if (node.type === "split") {
    treeSids(node.a, out);
    treeSids(node.b, out);
  }
  return out;
}

// sid pane 노드를 제거하고 형제로 붕괴시킨다(main.ts replaceNode의 제거 특수형과 동일 의미).
function removeSid(node: TNode, sid: number): TNode | null {
  if (node.type === "pane") return node.sid === sid ? null : node;
  if (node.type === "web") return node; // web 리프: 전출 대상 아님 — 제자리 보존
  const a = removeSid(node.a, sid);
  const b = removeSid(node.b, sid);
  if (a && b) return { ...node, a, b };
  return a ?? b;
}

// 트리 말단(우측 row 분할)에 pane을 덧붙인다 — actionNew의 삽입 규칙과 동일.
export function appendPane(tree: TNode | null, sid: number): TNode {
  const moved: TNode = { type: "pane", sid };
  return tree ? { type: "split", dir: "row", a: tree, b: moved } : moved;
}

// src에서 sid를 떼어 dest 끝에 붙인 새 (src, dest) 트리 쌍. 원천 부재·대상 중복이면 null.
export function transferTrees(
  src: TNode | null,
  dest: TNode | null,
  sid: number,
): { src: TNode | null; dest: TNode } | null {
  if (!src || !treeSids(src).includes(sid)) return null;
  if (dest && treeSids(dest).includes(sid)) return null;
  return { src: removeSid(src, sid), dest: appendPane(dest, sid) };
}
