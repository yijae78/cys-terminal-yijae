// web pane 순수 로직 — DOM 무의존(bun test 대상). main.ts의 WebPaneView(iframe·타이틀 스트립)는
// 이 모듈의 URL 가드·URL 조립·레이아웃 버전 판정만 호출하고, 부수효과(iframe.src·localStorage)는
// 호출측이 쥔다. seam 커밋(PaneView)에 이어 web pane 편입의 검증 가능한 판단부를 여기 모은다.

// 레이아웃 저장 키. v3=web 노드 포함 신 포맷. v2=구 포맷(구조 동일 — web 노드만 신규라 passthrough).
// ★다운그레이드 안전: 신 빌드는 v3에만 쓰고 v2는 읽기만 한다(삭제·수정 금지). 구 빌드로 롤백해도
// v2 스냅샷을 그대로 읽어 부팅한다(업그레이드 이후 v2는 프리즈된 마지막 구-포맷 상태).
export const LAYOUT_KEY_V2 = "cys-layout-v2";
export const LAYOUT_KEY_V3 = "cys-layout-v3";

// web pane 노드 — pane(터미널 sid)과 달리 sid가 없고 wid(단조증가 고유 id)로 식별한다.
// url = 뷰어 사이드카 앱 URL(loopback+토큰). 직렬화 대상(레이아웃 트리에 저장).
export type WebNode = { type: "web"; url: string; title?: string; wid: number };

export function makeWebNode(wid: number, url: string, title?: string): WebNode {
  return title === undefined ? { type: "web", url, wid } : { type: "web", url, title, wid };
}

// URL 하드 가드 — iframe src로 실릴 수 있는 것은 loopback(127.0.0.1|localhost)+명시 포트+경로뿐.
// 임의 인터넷 사이트·file://·https·userinfo(@) 위장 host는 전부 차단(예외 없음). 포트 뒤 첫 문자가
// '/'여야 하므로 `http://127.0.0.1:80@evil/`·`http://127.0.0.1:80.evil/`는 매칭 실패 → 거부.
export function isAllowedWebPaneUrl(url: string): boolean {
  return /^http:\/\/(127\.0\.0\.1|localhost):\d+\//.test(url);
}

// 뷰어 앱 URL 조립 — 사이드카가 넘긴 {port, token}과 렌더 대상 파일 경로로 만든다.
// token은 secrets.token_urlsafe(무-예약문자)라 그대로 삽입(app.js가 pathname 첫 세그먼트로 raw 대조).
export function viewerAppUrl(port: number, token: string, path: string): string {
  return `http://127.0.0.1:${port}/${token}/app/?path=${encodeURIComponent(path)}`;
}

// 저장된(스테일 token) web URL에서 원 파일 경로만 회수 — 복원 시 새 {port,token}으로 재조립하기 위함.
export function extractViewerPath(url: string): string | null {
  try {
    return new URL(url).searchParams.get("path");
  } catch {
    return null;
  }
}

// 레이아웃 로드 — v3 우선, 없으면 v2 읽어 마이그레이션(구조 동일 passthrough). 손상 저장본은 null.
// v2는 절대 쓰지/지우지 않는다(다운그레이드 안전).
export function loadPersistedLayout(getItem: (key: string) => string | null): any | null {
  const rawV3 = getItem(LAYOUT_KEY_V3);
  if (rawV3) {
    try {
      return JSON.parse(rawV3);
    } catch {
      return null;
    }
  }
  const rawV2 = getItem(LAYOUT_KEY_V2); // v2→v3 마이그레이션(첫 v3 로드 전까지 구 저장본 승계)
  if (rawV2) {
    try {
      return JSON.parse(rawV2);
    } catch {
      return null;
    }
  }
  return null;
}

// 레이아웃 저장 — v3에만 쓴다(v2 미변경 = 다운그레이드 안전 불변식).
export function persistLayout(setItem: (key: string, value: string) => void, data: unknown): void {
  setItem(LAYOUT_KEY_V3, JSON.stringify(data));
}
