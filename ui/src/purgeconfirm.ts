// 부서 완전삭제 확인 모달의 순수 판정·힌트 — main.ts purgeConfirmModal이 이 함수에 배선만 한다.
//
// 실사고(2026-07-16): ①비활성 버튼이 활성과 픽셀 동일해 "눌러도 무반응"으로 오인 ②macOS 자동
// 대문자화가 소문자 입력을 "Dept-4"로 재교정해 정확 재입력조차 불일치 ③불일치 사유 무표시.
// 판정·힌트를 순수 함수로 고정해 결정론 회귀 테스트(purgeconfirm.test.ts)로 잠근다.

// 확인 입력이 부서명과 정확히 일치하는가(공백만 관용 — 대소문자·따옴표는 불일치).
export function purgeNameMatches(input: string, name: string): boolean {
  return input.trim() === name;
}

// 불일치 시 사용자에게 보일 실시간 힌트(빈 입력·일치 = 빈 문자열).
export function purgeMismatchHint(input: string, name: string): string {
  const v = input.trim();
  if (!v || purgeNameMatches(input, name)) return "";
  return `부서명이 일치하지 않습니다 — "${name}" 을 그대로 입력하세요.`;
}

// macOS WKWebView 자동 교정 차단 속성 — 확인 입력 정확성의 전제(자동 대문자화·자동수정·맞춤법).
export const PURGE_INPUT_GUARDS: ReadonlyArray<[string, string]> = [
  ["autocapitalize", "off"],
  ["autocorrect", "off"],
  ["spellcheck", "false"],
];
