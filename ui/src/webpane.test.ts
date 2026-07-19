// webpane.ts 순수 로직 회귀 테스트 (bun test — 신규 의존성 0).
//
// ①레이아웃 직렬화 왕복(web 노드 포함) ②v2→v3 마이그레이션 ③다운그레이드 불변식
// ④URL 하드 가드. DOM(iframe·타이틀 스트립)은 main.ts WebPaneView가 담당하고, 여기선
// 검증 대상인 순수 판단부만 돌린다.
import { describe, it, expect } from "bun:test";
import {
  LAYOUT_KEY_V2,
  LAYOUT_KEY_V3,
  isAllowedWebPaneUrl,
  makeWebNode,
  viewerAppUrl,
  extractViewerPath,
  loadPersistedLayout,
  persistLayout,
  collectWebWids,
} from "./webpane";

// 테스트용 in-memory localStorage 대역(getItem/setItem만).
function fakeStore(init: Record<string, string> = {}) {
  const m = new Map<string, string>(Object.entries(init));
  return {
    getItem: (k: string) => (m.has(k) ? m.get(k)! : null),
    setItem: (k: string, v: string) => void m.set(k, v),
    raw: m,
  };
}

// web 노드가 섞인 레이아웃 트리(split 아래 터미널 pane + web pane).
function layoutWithWeb() {
  return {
    workspaces: [
      {
        id: 1,
        name: "ws1",
        tree: {
          type: "split",
          dir: "row",
          ratio: 0.5,
          a: { type: "pane", sid: 7 },
          b: makeWebNode(3, "http://127.0.0.1:51234/tok/app/?path=%2Ftmp%2Fa.md", "a.md"),
        },
      },
    ],
    groups: [],
    active: 0,
    counter: 2,
    groupCounter: 1,
  };
}

describe("① 레이아웃 직렬화 왕복 — web 노드 보존", () => {
  it("web 노드 포함 트리를 v3에 저장→로드하면 동일하다", () => {
    const s = fakeStore();
    const data = layoutWithWeb();
    persistLayout(s.setItem, data);
    const loaded = loadPersistedLayout(s.getItem);
    expect(loaded).toEqual(data);
    // web 노드 필드가 JSON 왕복에서 유실되지 않았는지 직접 확인
    const web = loaded.workspaces[0].tree.b;
    expect(web).toEqual({
      type: "web",
      wid: 3,
      url: "http://127.0.0.1:51234/tok/app/?path=%2Ftmp%2Fa.md",
      title: "a.md",
    });
  });

  it("저장은 v3 키에만 쓴다(v2 미기록)", () => {
    const s = fakeStore();
    persistLayout(s.setItem, layoutWithWeb());
    expect(s.raw.has(LAYOUT_KEY_V3)).toBe(true);
    expect(s.raw.has(LAYOUT_KEY_V2)).toBe(false);
  });
});

describe("② v2→v3 마이그레이션", () => {
  it("v3 없고 v2만 있으면 v2를 읽어온다(passthrough)", () => {
    const v2data = { workspaces: [{ id: 1, name: "old", tree: { type: "pane", sid: 1 } }], active: 0 };
    const s = fakeStore({ [LAYOUT_KEY_V2]: JSON.stringify(v2data) });
    const loaded = loadPersistedLayout(s.getItem);
    expect(loaded).toEqual(v2data);
  });

  it("v2 로드 후 v3로 저장해도 v2 원본은 그대로 보존된다", () => {
    const v2raw = JSON.stringify({ workspaces: [{ id: 1, name: "old", tree: null }], active: 0 });
    const s = fakeStore({ [LAYOUT_KEY_V2]: v2raw });
    const loaded = loadPersistedLayout(s.getItem);
    persistLayout(s.setItem, { ...loaded, migrated: true });
    // v3 신규 기록
    expect(s.raw.has(LAYOUT_KEY_V3)).toBe(true);
    // v2 원본은 바이트 단위로 불변
    expect(s.raw.get(LAYOUT_KEY_V2)).toBe(v2raw);
  });

  it("v3가 있으면 v2를 무시하고 v3를 읽는다(v3 우선)", () => {
    const s = fakeStore({
      [LAYOUT_KEY_V2]: JSON.stringify({ tag: "v2" }),
      [LAYOUT_KEY_V3]: JSON.stringify({ tag: "v3" }),
    });
    expect(loadPersistedLayout(s.getItem)).toEqual({ tag: "v3" });
  });

  it("손상 저장본은 null(폴백)", () => {
    expect(loadPersistedLayout(fakeStore({ [LAYOUT_KEY_V3]: "{bad" }).getItem)).toBeNull();
    expect(loadPersistedLayout(fakeStore().getItem)).toBeNull();
  });

  it("손상 v3 + 정상 v2 → v2로 폴백 복원한다(F5)", () => {
    const v2data = { workspaces: [{ id: 1, name: "before-upgrade", tree: null }], active: 0 };
    const s = fakeStore({
      [LAYOUT_KEY_V3]: "{corrupt json",
      [LAYOUT_KEY_V2]: JSON.stringify(v2data),
    });
    // v3 손상이어도 전손실(null) 대신 v2 스냅샷으로 부팅한다
    expect(loadPersistedLayout(s.getItem)).toEqual(v2data);
  });

  it("손상 v3 + 손상 v2 → null(최종 폴백)", () => {
    const s = fakeStore({ [LAYOUT_KEY_V3]: "{bad", [LAYOUT_KEY_V2]: "{also bad" });
    expect(loadPersistedLayout(s.getItem)).toBeNull();
  });
});

describe("③ 다운그레이드 불변식 — 구 빌드는 v2를 읽는다", () => {
  it("신 빌드가 v3에 써도, v2만 읽는 구 빌드는 업그레이드 전 스냅샷을 본다", () => {
    const v2raw = JSON.stringify({ workspaces: [{ id: 1, name: "before-upgrade", tree: null }], active: 0 });
    const s = fakeStore({ [LAYOUT_KEY_V2]: v2raw });
    // 신 빌드: v2 마이그레이션 로드 → web 포함 레이아웃을 v3에 저장
    loadPersistedLayout(s.getItem);
    persistLayout(s.setItem, layoutWithWeb());
    // 구 빌드 시뮬레이션: v2 키만 읽는다
    const oldBuildRead = JSON.parse(s.getItem(LAYOUT_KEY_V2)!);
    expect(oldBuildRead).toEqual(JSON.parse(v2raw));
    // v3는 존재하지만 구 빌드는 이 키를 모른다
    expect(s.raw.has(LAYOUT_KEY_V3)).toBe(true);
  });
});

describe("④ URL 하드 가드", () => {
  it("허용: loopback+포트+경로", () => {
    expect(isAllowedWebPaneUrl("http://127.0.0.1:51234/tok/app/?path=x")).toBe(true);
    expect(isAllowedWebPaneUrl("http://localhost:8642/app/")).toBe(true);
  });
  it("차단: https·file·임의 host·포트없음·userinfo·port위장", () => {
    expect(isAllowedWebPaneUrl("https://127.0.0.1:51234/app/")).toBe(false);
    expect(isAllowedWebPaneUrl("file:///etc/passwd")).toBe(false);
    expect(isAllowedWebPaneUrl("http://evil.com/app/")).toBe(false);
    expect(isAllowedWebPaneUrl("http://127.0.0.1/app/")).toBe(false); // 포트 없음
    expect(isAllowedWebPaneUrl("http://localhost/app/")).toBe(false); // 포트 없음
    expect(isAllowedWebPaneUrl("http://127.0.0.1:80@evil.com/")).toBe(false); // userinfo 위장
    expect(isAllowedWebPaneUrl("http://127.0.0.1:80.evil.com/")).toBe(false); // port 위장
    expect(isAllowedWebPaneUrl("http://127.0.0.1.evil.com:80/")).toBe(false); // host 위장
    expect(isAllowedWebPaneUrl("")).toBe(false);
  });
});

describe("⑤ web pane 정리(teardown) — collectWebWids", () => {
  it("split 아래 섞인 web 노드 wid를 전부 수집한다", () => {
    const tree = {
      type: "split",
      dir: "row",
      ratio: 0.5,
      a: makeWebNode(3, "http://127.0.0.1:1/tok/app/?path=a", "a"),
      b: {
        type: "split",
        dir: "col",
        ratio: 0.5,
        a: { type: "pane", sid: 7 }, // 터미널 pane은 건너뛴다
        b: makeWebNode(9, "http://127.0.0.1:1/tok/app/?path=b", "b"),
      },
    };
    expect(collectWebWids(tree).sort((x, y) => x - y)).toEqual([3, 9]);
  });

  it("web 노드 없는 트리(터미널만)는 빈 배열", () => {
    const tree = { type: "split", dir: "row", ratio: 0.5, a: { type: "pane", sid: 1 }, b: { type: "pane", sid: 2 } };
    expect(collectWebWids(tree)).toEqual([]);
  });

  it("단일 web 리프·null 처리", () => {
    expect(collectWebWids(makeWebNode(5, "http://127.0.0.1:1/t/app/?path=x"))).toEqual([5]);
    expect(collectWebWids(null)).toEqual([]);
  });
});

describe("보조 — URL 조립·경로 회수 왕복", () => {
  it("viewerAppUrl은 가드를 통과하고 extractViewerPath로 원 경로가 복원된다", () => {
    const url = viewerAppUrl(51234, "tok-en_123", "/tmp/report file.md");
    expect(isAllowedWebPaneUrl(url)).toBe(true);
    expect(extractViewerPath(url)).toBe("/tmp/report file.md");
  });
  it("extractViewerPath는 비URL에 null", () => {
    expect(extractViewerPath("not a url")).toBeNull();
  });
});
