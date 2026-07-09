// deptlabel.ts 순수 함수 회귀 테스트 (bun test — 신규 의존성 0). WP-10 잠금 픽스처 대응.
//
// '＋부서' 클릭 후 부서 데몬 준비 동안 탭 라벨이 진행 상태를 명시하는지(멈춘 줄 오해 방지),
// 확정 후엔 실제 표시명으로 바뀌는지 결정론으로 검증한다.
import { describe, it, expect } from "bun:test";
import { deptPlaceholderLabel, ccNodeLabel, DEPT_PENDING_LABEL } from "./deptlabel";

describe("deptPlaceholderLabel — 부서 제작 중 표시", () => {
  it("pending 부서 탭은 '부서 제작 중' 표시", () => {
    expect(deptPlaceholderLabel({ pending: true, name: "…" })).toContain("부서 제작 중");
  });
  it("확정된 부서는 실제 표시명", () => {
    expect(deptPlaceholderLabel({ pending: false, name: "리서치부" })).toBe("리서치부");
  });
  it("pending 미지정(undefined)은 실제 이름 취급(확정 탭 회귀)", () => {
    expect(deptPlaceholderLabel({ name: "dept-1" })).toBe("dept-1");
  });
  it("pending 라벨은 상수 DEPT_PENDING_LABEL 과 일치", () => {
    expect(deptPlaceholderLabel({ pending: true, name: "무엇이든" })).toBe(DEPT_PENDING_LABEL);
  });
});

describe("ccNodeLabel — Control Center 노드 행 라벨 (오너 지시 R2-4)", () => {
  it("dashboard role + title '체크판' → '체크판' 렌더, master는 여전히 'master'", () => {
    expect(ccNodeLabel("dashboard", "체크판")).toBe("체크판");
    expect(ccNodeLabel("master", "무시되는 제목")).toBe("master");
  });
  it("표준 역할(cso·worker-2·reviewer-gemini)은 title 무관 role 그대로", () => {
    expect(ccNodeLabel("cso", "다른제목")).toBe("cso");
    expect(ccNodeLabel("worker-2", "다른제목")).toBe("worker-2");
    expect(ccNodeLabel("reviewer-gemini", "다른제목")).toBe("reviewer-gemini");
  });
  it("비표준 role의 title 부재·자동제목('surface N')은 role 폴백", () => {
    expect(ccNodeLabel("dashboard", null)).toBe("dashboard");
    expect(ccNodeLabel("dashboard", "  ")).toBe("dashboard");
    expect(ccNodeLabel("dashboard", "surface 7")).toBe("dashboard");
  });
  it("role null은 '?' (title 있으면 title)", () => {
    expect(ccNodeLabel(null, "체크판")).toBe("체크판");
    expect(ccNodeLabel(null, null)).toBe("?");
  });
});
