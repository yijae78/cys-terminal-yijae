#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""javis_gate_check.py — 게이트 shadow 대조용 독립 검사기 (DESIGN P1·시뮬 S3-2)

게이트의 diff로 게이트의 diff를 채점하는 순환을 금지한다(producer≠evaluator). 이 검사기는
게이트와 **다른 로직** — 구조적 diff가 아니라 **단순 경고 키워드 문자열 규칙**만 쓴다.

판정: "게이트가 억제(NOCHG|QUIET)로 판정한 시점의 실제 push 본문에 경고 키워드가 존재"하는
건수. 0건이어야 정상(오억제 0). 1건 이상이면 게이트가 경고를 삼킨 것 = shadow 실패.

입력:
  --ledger <path>     게이트 대장(ledger.jsonl) — 억제 판정 시점(ts_epoch) 추출
  --push-dir <dir>    보관된 실제 push 본문 파일들(각 파일 mtime = 발화 시각)
  --window <sec>      억제 판정과 push를 짝짓는 시간 창(기본 300 = 1주기)

종료 코드: 0 = 오억제 0건 · 1 = 오억제 발견(목록 출력) · 2 = usage.
의존성: 파이썬 표준 라이브러리만.
"""

import argparse
import json
import os
import sys
import time

EXIT_OK, EXIT_FOUND, EXIT_USAGE = 0, 1, 2

SUPPRESS_VERDICTS = ("NOCHG", "QUIET")

# 경고 키워드 규칙(게이트 diff 로직과 무관한 문자열 매칭). javis_report.render_text가 실제
# push 본문에 찍는 경고 마커에서 도출: "⚠ idle 5분+", "⚠ 컨텍스트 60%+", "⚠ 미처리 승인(feed)",
# "cys status 수집 실패". 대소문자 무시.
WARNING_KEYWORDS = ["idle", "컨텍스트", "60%", "feed", "승인", "실패", "⚠", "stall"]


def _ledger_suppressed(ledger_path):
    """대장에서 억제 판정(ts_epoch) 목록 추출."""
    out = []
    try:
        with open(ledger_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print("대장 읽기 실패: %s" % e, file=sys.stderr)
        return None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("verdict") in SUPPRESS_VERDICTS:
            ep = e.get("ts_epoch")
            if isinstance(ep, (int, float)):
                out.append((ep, e))
    return out


def _push_bodies(push_dir):
    """(mtime_epoch, path, text) 목록 — 보관된 push 본문 파일."""
    out = []
    try:
        names = os.listdir(push_dir)
    except OSError as e:
        print("push-dir 읽기 실패: %s" % e, file=sys.stderr)
        return None
    for name in sorted(names):
        p = os.path.join(push_dir, name)
        if not os.path.isfile(p):
            continue
        try:
            mt = os.path.getmtime(p)
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read(65536)
        except OSError:
            continue
        out.append((mt, p, text))
    return out


def _has_warning(text):
    low = text.lower()
    return [kw for kw in WARNING_KEYWORDS if kw.lower() in low]


def check(ledger_path, push_dir, window):
    suppressed = _ledger_suppressed(ledger_path)
    if suppressed is None:
        return EXIT_USAGE
    bodies = _push_bodies(push_dir)
    if bodies is None:
        return EXIT_USAGE

    violations = []
    for ep, entry in suppressed:
        for mt, path, text in bodies:
            if abs(mt - ep) <= window:
                hits = _has_warning(text)
                if hits:
                    violations.append((entry.get("ts", "?"), entry.get("verdict"),
                                       os.path.basename(path), hits))

    if violations:
        print("오억제 발견 %d건 — 게이트가 경고를 삼켰다(producer≠evaluator 검증 실패):"
              % len(violations))
        for ts, verdict, fname, hits in violations:
            print("  %s  판정=%s  push=%s  키워드=%s" % (ts, verdict, fname, ",".join(hits)))
        return EXIT_FOUND

    print("오억제 0건 — 억제 판정 %d건 중 경고 포함 push 없음(shadow OK)." % len(suppressed))
    return EXIT_OK


def main(argv=None):
    p = argparse.ArgumentParser(description="게이트 shadow 독립 검사기(경고 키워드 규칙·producer≠evaluator)")
    p.add_argument("--ledger", required=True, help="게이트 대장 ledger.jsonl 경로")
    p.add_argument("--push-dir", required=True, help="보관된 실제 push 본문 파일 디렉터리")
    p.add_argument("--window", type=float, default=300.0, help="억제↔push 시간 창(초, 기본 300)")
    a = p.parse_args(argv)
    return check(a.ledger, a.push_dir, a.window)


if __name__ == "__main__":
    sys.exit(main())
