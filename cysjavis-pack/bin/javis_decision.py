#!/usr/bin/env python3
"""javis_decision.py — VIBECODING CONSTITUTION §C11 DECISION block 파서·검증기.

계약(출처: _research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md §C11 L332-343):
  6조 = 결정권(인간) / 기록권(서기·에이전트) 분리. 서기는 전사(verbatim)만 한다 —
  해석·보완·추론으로 결정 내용을 생성하면 silent hijacking(6조 위반).
  이 도구는 그 규율의 기계화다: DECISION block 의 의무 필드가 하나라도 결손되면 exit 2 로
  차단하고 결손 필드를 보고한다. "빈 필드를 추론으로 채우기"를 코드가 거부한다(§C11.3).

의무 필드(§C11.2):
  decision_id  (DEC-YYYYMMDD-NNN)
  decider      (doctor | master — 위임 범위 내)
  scope        (반영 대상 문서·조문 지정 — 전사 대상 scope)
  decision     (결정문 원문 · verbatim — 서기 수정 금지, 여러 줄 허용)
  effective_date (YYYY-MM-DD)

입력 채널(§C11.2 3채널 모두 key: value 라인으로 환원):
  ①메시지 라벨 `[DECISION]` 접두   ②issue form   ③커밋 trailer `Decision:`
  → 본 파서는 header 구획(scalar 필드)과 body 구획(decision verbatim)을 명확히 경계짓는다.

  **필드/본문 경계(B-2 하이재킹 차단)**: 서기 도구의 존재 이유가 §C11 silent hijacking 차단이므로,
  도구 자신이 하이재킹을 자행해선 안 된다. 그러므로:
    - scalar 필드(decision_id·decider·scope·effective_date)는 **header 구획에서만** 파싱한다.
    - `decision:` 라인이 body 구획을 연다 — 그 이후는 **명시적 종결자 `[/DECISION]` 또는 EOF 까지**
      전부 결정문 원문(verbatim)으로 취급하고, **본문 내부의 field-like 줄(`scope: ...` 등)을
      필드로 재해석하지 않는다**(본문 보존·가짜 필드 무시). 따라서 `decision:` 은 header 필드 뒤,
      마지막 스칼라 필드다. 종결자 `[/DECISION]` 뒤에는 다시 header 필드가 올 수 있다(trailer 혼재 허용).

전사 대상 scope 기록: 검증 통과 시 정규화 레코드(JSON)를 stdout 으로 산출한다.
  --record 지정 시 $JAVIS_ROOT/.vibecoding/decisions.jsonl 에 append-only 로 영속.

exit codes: 0 valid · 2 의무 필드 결손·형식 위반(§C11.3 fail-closed) · 2 usage
"""
import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.environ.get("JAVIS_ROOT") or os.getcwd()
VIBE_DIR = os.path.join(ROOT, ".vibecoding")
DECISIONS = os.path.join(VIBE_DIR, "decisions.jsonl")

EXIT_OK, EXIT_INVALID = 0, 2

FIELDS = ("decision_id", "decider", "scope", "decision", "effective_date")
HEADER_KEYS = {"decision_id", "decider", "scope", "effective_date"}  # scalar 필드 — header 구획에서만 파싱
BODY_KEY = "decision"          # body 구획을 여는 키(verbatim — 이후 field-like 줄 재해석 금지)
BODY_END = "[/DECISION]"       # body 명시적 종결자(뒤에 header 필드 재개 허용)
DECIDERS = ("doctor", "master")
_ID_RE = re.compile(r"^DEC-\d{8}-\d{3}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")


def parse_block(text):
    """DECISION block 텍스트 → 필드 dict.

    header 구획: scalar 필드(HEADER_KEYS)만 `key: value` 로 파싱. 알 수 없는 key/비-kv 줄은 무시.
    body 구획: `decision:` 이 열고, 종결자 `[/DECISION]` 또는 EOF 까지 전부 원문(verbatim)으로
      수집한다 — **본문 내부의 field-like 줄(`scope: ...` 등)은 필드로 재해석하지 않는다**(B-2 차단).
      종결자를 만나면 header 로 복귀(커밋 trailer 혼재 허용).
    """
    fields = {}
    body_lines = None  # None=header 모드, list=body 수집 중
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()

        if body_lines is not None:
            # body 구획: 종결자만 특별 취급, 그 외 전부 verbatim(field-like 줄 무시).
            if stripped == BODY_END:
                fields[BODY_KEY] = "\n".join(body_lines).strip()
                body_lines = None
            else:
                body_lines.append(line)
            continue

        # header 구획.
        if stripped.startswith("[DECISION]"):
            rest = stripped[len("[DECISION]"):].strip()
            if not rest:
                continue
            stripped = rest
        m = _KV_RE.match(stripped)
        if not m:
            continue
        key = m.group(1).lower()
        if key in HEADER_KEYS:
            fields[key] = m.group(2).strip()
        elif key == BODY_KEY:
            # decision body 시작 — 인라인 값이 첫 줄(있으면).
            inline = m.group(2)
            body_lines = [inline] if inline else []
        # 그 외 알 수 없는 key: 무시(header 오염 차단).

    if body_lines is not None:  # EOF 로 body 종료(명시 종결자 없이).
        fields[BODY_KEY] = "\n".join(body_lines).strip()
    return fields


def validate(fields):
    """(missing, invalid) 리스트 반환. 둘 다 비면 유효."""
    missing = [f for f in FIELDS if not fields.get(f)]
    invalid = []
    if fields.get("decision_id") and not _ID_RE.match(fields["decision_id"]):
        invalid.append("decision_id(형식 DEC-YYYYMMDD-NNN 위반)")
    if fields.get("decider") and fields["decider"] not in DECIDERS:
        invalid.append(f"decider(허용: {DECIDERS})")
    if fields.get("effective_date") and not _DATE_RE.match(fields["effective_date"]):
        invalid.append("effective_date(형식 YYYY-MM-DD 위반)")
    return missing, invalid


def cmd_validate(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()

    fields = parse_block(text)
    missing, invalid = validate(fields)
    if missing or invalid:
        # §C11.3: 결손을 추론으로 채우지 않고 되묻는다(grill) — 여기선 결손·위반을 보고하고 차단.
        report = {"status": "blocked", "missing": missing, "invalid": invalid,
                  "note": "의무 필드 결손/형식 위반 — 추론으로 채우기 금지(§C11.3). 인가자에게 되물어야 함."}
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return EXIT_INVALID

    record = {f: fields[f] for f in FIELDS}
    record["recorded_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    if args.record:
        os.makedirs(VIBE_DIR, exist_ok=True)
        with open(DECISIONS, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    # 전사 대상 scope 를 포함한 정규화 레코드 산출.
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return EXIT_OK


def main(argv=None):
    p = argparse.ArgumentParser(description="§C11 DECISION block 검증·전사 레코드 산출")
    sub = p.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("validate", help="DECISION block 검증(의무 필드 결손=exit 2)")
    g = pv.add_mutually_exclusive_group()
    g.add_argument("--file", help="DECISION block 파일 경로")
    g.add_argument("--text", help="DECISION block 인라인 텍스트")
    pv.add_argument("--record", action="store_true", help="검증 통과 시 .vibecoding/decisions.jsonl 에 append")
    pv.set_defaults(func=cmd_validate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
