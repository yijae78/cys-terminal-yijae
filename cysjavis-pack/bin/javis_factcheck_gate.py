#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""javis_factcheck_gate — 대본 팩트체크 표 완비·미통과0 게이트 (SUBSTRATE_AUDIT 미니설계 #1).

factcheck-report.md(문장별 [원문|판정|출처] 3필드 표)를 **엄격 스키마**로 읽어,
미통과 판정이 1건이라도 남으면 exit 비0으로 음성 합성 단계 진행을 차단한다. LLM 판정을
대체하지 않는다 — 판정 산출물의 표 완비·미통과0만 잠근다(over-claim 금지). 잔여0이
환각0을 보장하지는 않는다 — 이 게이트는 보고서가 표로 완비되고 미통과가 없음만 확인한다.

이 게이트는 script-writer-factcheck 출력계약(판정 어휘 통과·보강·삭제·미통과)을 기계
파싱 가능한 파이프 표로 못박은 계약이다.

입력 형식 계약(엄격 계약 — 관용 파싱 없음):
  입력 factcheck-report.md 는 **마크다운 표 형식**(`| 원문 | 판정 | 출처 |`)이 유일 계약이다.
  헤더 행 = `| 원문 | 판정 | 출처 |` 정확히 일치. 구분 행 뒤 데이터 행 1개+.
  각 행은 파이프 3필드. 판정 어휘 ∈ VOCAB 4종 밖이면 스키마 위반(파싱불가).
  판정 어휘: 통과·보강·삭제(해소 — 게이트 통과 방향) / 미통과(잔여 — 차단).
  출처 필수: 통과·보강. (삭제는 문장 제거분이라 출처 불요.)

  표 밖 산문(요약 문단·헤딩)은 평가 대상이 아니다 — 표 데이터 행만 판정하고 표 밖
  텍스트는 무시한다. 정상 요약 문단("11개 통과, 1개 보강. 잔여 없음")이 판정 어휘를
  포함해도 차단하지 않는다.

종료 코드:
  0  표 완비 + 미통과0 + 필수 출처 완비 — 음성 단계 진행 허용
  2  미통과 잔여 1건+ 또는 통과/보강 빈 출처 — 진행 차단
  3  report 부재·읽기실패·파싱불가(3필드 미완비·헤더 불일치·미지 어휘·표 없음)

사용:
    python3 javis_factcheck_gate.py check <FILE> [--json]
    python3 javis_factcheck_gate.py --self-test        # 밀폐 자기검증(무 I/O)
의존성: 파이썬 표준 라이브러리만(네트워크·LLM·점수 없음).
"""

import argparse
import json
import os
import re
import sys

FIELDS = ["원문", "판정", "출처"]
PASS = {"통과", "보강", "삭제"}     # 해소 판정 — 게이트 통과 방향
RESIDUAL = {"미통과"}              # 잔여 판정 → exit 2
VOCAB = PASS | RESIDUAL            # 어휘 밖 = 스키마 위반 → exit 3
NEED_SOURCE = {"통과", "보강"}     # 출처 필수(삭제 제외)
_SEP = re.compile(r"^:?-+:?$")


def _split(line):
    """마크다운 표 행 → 셀 리스트(선행·후행 파이프 1개 제거)."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_sep(cells):
    return bool(cells) and all(_SEP.match(c) for c in cells)


def evaluate(text):
    """순수 CHECK — 원문 텍스트 → (exit_code, detail). I/O·전역상태 무접촉(밀폐).

    표 데이터 행만 평가한다. 표 밖 산문(요약 문단·헤딩)은 무시한다 —
    정상 요약이 판정 어휘를 담아도 false-block 하지 않는다.
    """
    errors, residual, empty_src = [], [], []
    lines = text.splitlines()
    rows = [_split(l) for l in lines if l.strip().startswith("|")]
    data = [r for r in rows if not _is_sep(r)]  # 구분 행 제거

    if not data:
        errors.append("파이프 표 없음 — [원문|판정|출처] 3필드 표 필수")
    else:
        if data[0] != FIELDS:
            errors.append("헤더 %s ≠ 계약 %s" % (data[0], FIELDS))
        body = data[1:]
        if not body:
            errors.append("데이터 행 0 — 완결성 위반(판정 산출물 미완)")
        for i, r in enumerate(body):
            if len(r) != 3:
                errors.append("행%d 셀수 %d≠3 — 3필드 미완비" % (i, len(r)))
                continue
            src_text, verdict, source = r
            if verdict not in VOCAB:
                errors.append("행%d 판정어휘 위반 %r — VOCAB %s 밖" % (i, verdict, sorted(VOCAB)))
                continue
            if verdict in RESIDUAL:
                residual.append(i)
            elif verdict in NEED_SOURCE and not source:
                empty_src.append(i)

    detail = {"data_rows": max(len(data) - 1, 0) if data else 0,
              "errors": errors, "residual_rows": residual, "empty_source_rows": empty_src}
    if errors:
        return 3, detail
    if residual or empty_src:
        return 2, detail
    return 0, detail


def cmd_check(path, as_json):
    if not os.path.isfile(path):
        return fail(3, "report 부재: %s" % path, as_json)
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return fail(3, "report 읽기 실패: %s (%s)" % (path, e), as_json)

    code, detail = evaluate(text)
    report = {"ok": code == 0, "exit": code, "file": path, **detail}
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for e in detail["errors"]:
            print("[SCHEMA] %s" % e)
        if detail["residual_rows"]:
            print("[RESIDUAL] 잔여 미통과 데이터행 %s — 음성 단계 차단" % detail["residual_rows"])
        if detail["empty_source_rows"]:
            print("[SOURCE]   통과/보강 빈 출처 행 %s — 음성 단계 차단" % detail["empty_source_rows"])
        verdict = {0: "GO(표 완비·미통과0)", 2: "BLOCK(잔여)", 3: "BLOCK(불완결)"}[code]
        print("gate: %s — exit %d" % (verdict, code))
        if code:
            print("이 출력 외 추론으로 팩트체크 완결을 선언하지 마라.")
    return code


def fail(code, msg, as_json):
    if as_json:
        print(json.dumps({"ok": False, "exit": code, "error": msg}, ensure_ascii=False))
    else:
        print("[GATE] %s" % msg, file=sys.stderr)
        print("gate: BLOCK(불완결) — exit %d" % code)
    return code


def self_test():
    """밀폐 배터리 — 각 위반이 정확한 exit로 잡히는지(파일시스템·전역상태 무접촉)."""
    H = "| 원문 | 판정 | 출처 |\n|---|---|---|\n"
    failures = []

    def check(name, text, want):
        code, _ = evaluate(text)
        if code != want:
            failures.append("%s: exit=%d 기대=%d" % (name, code, want))

    # exit 0 — 표 완비·미통과0 (실제 4어휘 통과·보강·삭제, 삭제는 출처 없어도 통과)
    check("happy", H + "| 지구는 둥글다 | 통과 | NASA |\n"
                      "| 물은 H2O | 보강 | 화학편람 |\n"
                      "| 낭설 문장 | 삭제 |  |\n", 0)
    # exit 2 — 잔여 미통과
    check("residual-미통과", H + "| x | 미통과 | y |\n", 2)
    # exit 2 — 통과/보강 빈 출처
    check("empty-src-통과", H + "| x | 통과 |  |\n", 2)
    check("empty-src-보강", H + "| x | 보강 |   |\n", 2)
    # exit 0 — 삭제 빈 출처 허용
    check("del-no-src-ok", H + "| x | 삭제 |  |\n", 0)
    # exit 3 — 스키마 위반
    check("bad-header", "| 문장 | 상태 | 근거 |\n|---|---|---|\n| x | 통과 | y |\n", 3)
    check("cell-count", H + "| x | 통과 |\n", 3)           # 2필드
    check("unknown-verdict", H + "| x | 확인중 | y |\n", 3)  # 어휘 밖
    check("no-table", "표가 아닌 산문 텍스트\n", 3)
    check("header-only", H, 3)                              # 데이터 행 0
    # 발명된 구 어휘(보강완료·삭제완료·보강대기·삭제대기)는 이제 어휘 밖 → exit 3
    check("legacy-보강완료", H + "| x | 보강완료 | y |\n", 3)
    check("legacy-삭제대기", H + "| x | 삭제대기 | y |\n", 3)
    # 혼재: 잔여 + 스키마오류 동시 → 스키마(exit 3) 우선
    check("precedence", H + "| x | 미통과 | y |\n| z | 확인중 | w |\n", 3)

    # --- 치명#2 회귀 방지: 표 밖 산문은 무시 (원본 cand_B 동작 복원) ---
    # 표는 전항목 해소, 표 밖 정상 요약 문단에 '통과'·'미통과' 단어 포함 → exit 0 (차단 금지)
    check("summary-prose-ok",
          H + "| 지구는 둥글다 | 통과 | NASA |\n"
              "| 물은 H2O | 보강 | 화학편람 |\n\n"
              "요약: 11개 통과, 1개 보강. 잔여 미통과 없음.\n", 0)
    # 표 밖 헤딩/블록에 판정 어휘가 섞여도 무시 → exit 0
    check("heading-prose-ok",
          "# 팩트체크 보고서 — 미통과 0건\n" + H
          + "| 지구는 둥글다 | 통과 | NASA |\n", 0)
    check("bullet-prose-ok",
          H + "| 지구는 둥글다 | 통과 | NASA |\n"
              "\n- 검토 노트: 모든 문장 통과 처리 완료.\n", 0)
    # 판정 어휘가 표 셀(원문) 안에 있어도 오탐 없이 exit 0
    check("cell-text-not-flagged",
          H + "| 터널을 통과하는 열차는 빠르다 | 통과 | 물리편람 |\n", 0)

    print(json.dumps({"self_test": "ok" if not failures else "fail",
                      "cases": 18, "failures": failures}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def main():
    ap = argparse.ArgumentParser(description="대본 팩트체크 표 완비·미통과0 게이트")
    ap.add_argument("--self-test", action="store_true", help="밀폐 자기검증")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check", help="report 1건 게이트 (0=완비 2=잔여 3=불완결)")
    c.add_argument("file")
    c.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.cmd == "check":
        return cmd_check(args.file, args.json)
    ap.print_help()
    return 3


if __name__ == "__main__":
    sys.exit(main())
