#!/usr/bin/env bash
# javis_prod_deny_e2e.sh — VIBECODING §C3 prod 권한 거부 E2E (target 플러거블 하네스).
#
# 계약(출처: PROPOSAL-jarvis-vibecoding-system-v3.md §C3 L161):
#   agent identity 로 prod 쓰기 시도 → 거부(exit 비0)를 실측하는 테스트를 CI 에 상설 배치.
#   통과 못 하면 배포 게이트 차단.
#
# 인프라 종속(실 prod 커넥션 필요)이므로 target 은 PROD_WRITE_CMD 로 주입한다(플러거블):
#   - PROD_WRITE_CMD = "agent identity 자격증명으로 prod 데이터플레인 쓰기를 시도하는 명령"
#     (예: psql INSERT/UPDATE/DELETE, aws cli 인프라 변경 등).
#
# 판정(성공 기준 = 거부가 실측되어야 함):
#   - PROD_WRITE_CMD 실행이 exit 비0(권한 거부) → 이 하네스 exit 0 (게이트 통과).
#   - PROD_WRITE_CMD 실행이 exit 0(쓰기 성공)     → 이 하네스 exit 1 (인프라 강제 미배선 · 배포 차단).
#   - PROD_WRITE_CMD 미주입                       → 이 하네스 exit 2 (미배선 · fail-closed).
#
# 실측은 배포 단계에서 실 target 을 주입해 수행한다(이 파일은 하네스·명세만 제공).
set -u

if [ -z "${PROD_WRITE_CMD:-}" ]; then
  echo "SKIP-FAIL: PROD_WRITE_CMD 미주입 — prod 쓰기 시도 target 이 없어 거부 실측 불가(fail-closed)." >&2
  echo "  사용법: PROD_WRITE_CMD='<agent identity 로 prod 쓰기 시도 명령>' bash $0" >&2
  exit 2
fi

echo "[prod-deny-e2e] target 실행: $PROD_WRITE_CMD" >&2
set +e
# shellcheck disable=SC2086
bash -c "$PROD_WRITE_CMD" >/dev/null 2>&1
rc=$?
set -e 2>/dev/null || true

if [ "$rc" -ne 0 ]; then
  echo "PASS: prod 쓰기 시도가 거부됨(exit $rc) — 인프라 레벨 read-only 강제 확인." >&2
  exit 0
else
  echo "FAIL: prod 쓰기 시도가 성공(exit 0) — agent identity 가 prod 쓰기 권한 보유. 인프라 강제 미배선 · 배포 차단." >&2
  exit 1
fi
