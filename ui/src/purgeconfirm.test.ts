// purgeconfirm.ts 순수 함수 회귀 테스트 (bun test — 신규 의존성 0). 실사고(2026-07-16) 픽스처 잠금:
// 입력 "Dept-4"(자동 대문자화)·'"dept-4"'(따옴표 포함)가 dept-4 요구에 불일치로 판정되고
// 힌트가 사유를 말해주는지, 입력 가드 속성 3종이 계약대로인지 결정론 검증.
import { describe, it, expect } from "bun:test";
import { purgeNameMatches, purgeMismatchHint, PURGE_INPUT_GUARDS } from "./purgeconfirm";

describe("purgeNameMatches — 대소문자·따옴표 함정 판정", () => {
  it("정확 일치만 통과(공백 관용)", () => {
    expect(purgeNameMatches("dept-4", "dept-4")).toBe(true);
    expect(purgeNameMatches("  dept-4  ", "dept-4")).toBe(true);
  });
  it("실사고 입력들은 전부 불일치", () => {
    expect(purgeNameMatches("Dept-4", "dept-4")).toBe(false); // macOS 자동 대문자화
    expect(purgeNameMatches('"Dept-4"', "dept-4")).toBe(false); // 스크린샷 그대로
    expect(purgeNameMatches('"dept-4"', "dept-4")).toBe(false); // 따옴표 포함
    expect(purgeNameMatches("", "dept-4")).toBe(false);
  });
});

describe("purgeMismatchHint — 불일치 사유 실시간 표시", () => {
  it("빈 입력·일치 시 빈 문자열(힌트 소음 금지)", () => {
    expect(purgeMismatchHint("", "dept-4")).toBe("");
    expect(purgeMismatchHint("   ", "dept-4")).toBe("");
    expect(purgeMismatchHint("dept-4", "dept-4")).toBe("");
  });
  it("불일치 시 요구 부서명을 명시", () => {
    const h = purgeMismatchHint("Dept-4", "dept-4");
    expect(h).toContain("일치하지 않습니다");
    expect(h).toContain("dept-4");
  });
});

describe("PURGE_INPUT_GUARDS — macOS 자동 교정 차단 계약", () => {
  it("자동 대문자화·자동수정·맞춤법 3종이 고정된다", () => {
    const m = new Map(PURGE_INPUT_GUARDS);
    expect(m.get("autocapitalize")).toBe("off");
    expect(m.get("autocorrect")).toBe("off");
    expect(m.get("spellcheck")).toBe("false");
    expect(PURGE_INPUT_GUARDS.length).toBe(3);
  });
});
