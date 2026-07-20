#!/usr/bin/env python3
"""javis_prereg.py — 사전등록(pre-registration) ledger 도구 (v3.2 Phase 0)

계약(출처: _research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md
§C6.2·C6.6 pilot · §C7.3 A/B eval 사전등록 · §C10.2 mutation operator 셋):
- ledger 는 append-only 다: seal 은 record 를 SHA-256 봉인과 함께 한 줄 추가할 뿐, 기존 줄을
  절대 재작성하지 않는다(회계 감사 가능).
- freeze: 이미 봉인된 record_id 를 다시 seal 하려는 시도는 거부한다(exit 9). "사후 변경 금지"
  (§C6.2 "Phase 0 마감에서 오너 재가 후 ledger 동결·사후 변경 금지")의 결정론 집행.
- 봉인 무결성: 각 줄은 payload 의 정규화(canonical) JSON SHA-256 을 함께 저장한다. verify 는
  저장된 payload 로부터 해시를 재계산해 봉인 해시와 대조 — 줄이 변조되면 불일치(exit 1).
- 체인: 각 줄은 직전 줄의 SHA-256(prev_sha256)을 담아 append-only 사슬을 이룬다. verify-chain 이
  이 사슬을 전수 순회해 중간 줄 삭제·삽입·변조를 탐지한다(per-record verify 는 삭제를 못 잡는다).

저장:  $JAVIS_ROOT/_round/vibecoding-ledger/ledger.jsonl (JSONL · 한 줄 = 봉인 record 1건)

exit codes: 0 ok · 1 verify 불일치(변조) · 2 usage · 3 not found · 9 frozen(재봉인 거부)
"""
import argparse
import hashlib
import json
import os
import sys
import time

ROOT = os.environ.get("JAVIS_ROOT") or os.getcwd()  # 개인경로 하드코딩 금지(pack scan gate)
LEDGER_DIR = os.path.join(ROOT, "_round", "vibecoding-ledger")
LEDGER_PATH = os.path.join(LEDGER_DIR, "ledger.jsonl")

EXIT_OK, EXIT_VERIFY_FAIL, EXIT_USAGE, EXIT_NOTFOUND, EXIT_FROZEN = 0, 1, 2, 3, 9


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _canon_hash(obj):
    """payload 의 정규화 JSON(sort_keys·UTF-8) SHA-256 — 키 순서·공백 무관 결정론 해시."""
    canon = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _line_sha(line):
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def _read_ledger_raw():
    """ledger.jsonl 의 raw 줄 목록(빈 줄 제외·개행 제거). seal 의 prev_sha256 계산과 동일한
    바이트 기준(rstrip("\\n"))으로 읽어야 체인 해시 재계산이 일치한다."""
    out = []
    try:
        with open(LEDGER_PATH, encoding="utf-8") as f:
            for raw in f:
                ln = raw.rstrip("\n")
                if ln:
                    out.append(ln)
    except FileNotFoundError:
        pass
    return out


def _read_ledger():
    """ledger.jsonl 의 봉인 entry 목록(파싱된 dict). 부재 시 빈 목록."""
    return [json.loads(ln) for ln in _read_ledger_raw()]


def _find_sealed(record_id):
    for entry in _read_ledger():
        if entry.get("record_id") == record_id:
            return entry
    return None


def cmd_seal(a):
    try:
        with open(a.record, encoding="utf-8") as f:
            rec = json.load(f)
    except FileNotFoundError:
        print(f"not found: {a.record}", file=sys.stderr)
        return EXIT_NOTFOUND
    except json.JSONDecodeError as e:
        print(f"error: record JSON 파싱 실패: {e}", file=sys.stderr)
        return EXIT_USAGE
    rid = rec.get("record_id")
    if not rid:
        print("error: record 에 record_id 필드 필수", file=sys.stderr)
        return EXIT_USAGE
    if _find_sealed(rid):
        print(f"frozen(9): record_id {rid} 이미 봉인됨 — 재봉인 거부(사후 변경 금지)",
              file=sys.stderr)
        return EXIT_FROZEN
    os.makedirs(LEDGER_DIR, exist_ok=True)
    # append-only 사슬: 직전 줄(있으면)의 raw SHA-256 을 prev 로 고정
    prev_sha = None
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, encoding="utf-8") as f:
            lines = [ln for ln in (x.rstrip("\n") for x in f) if ln]
        if lines:
            prev_sha = _line_sha(lines[-1])
    entry = {
        "record_id": rid,
        "sealed_at": _now(),
        "payload_sha256": _canon_hash(rec),
        "prev_sha256": prev_sha,
        "payload": rec,
    }
    line = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(json.dumps({"seal": "ok", "record_id": rid,
                      "payload_sha256": entry["payload_sha256"]}, ensure_ascii=False))
    return EXIT_OK


def cmd_verify(a):
    entry = _find_sealed(a.record_id)
    if entry is None:
        print(f"not found: {a.record_id} — ledger 에 봉인 기록 없음", file=sys.stderr)
        return EXIT_NOTFOUND
    recomputed = _canon_hash(entry.get("payload"))
    sealed = entry.get("payload_sha256")
    ok = recomputed == sealed
    print(json.dumps({"verify": a.record_id, "match": ok,
                      "sealed_sha256": sealed, "recomputed_sha256": recomputed},
                     ensure_ascii=False))
    return EXIT_OK if ok else EXIT_VERIFY_FAIL


def cmd_verify_chain(a):
    """append-only 체인 무결성 검증 — 각 줄의 prev_sha256 이 직전 줄의 실제 raw SHA-256 과
    일치하는지 전수 순회한다. 중간 줄 삭제·삽입·변조 시 그 지점에서 사슬이 끊겨 exit 1.
    (per-record verify 는 삭제를 못 잡는다 — 남은 줄 각각은 여전히 자기 payload 해시와
    일치하기 때문. 삭제 탐지는 이 줄-간 사슬 검증만이 한다.)"""
    raw = _read_ledger_raw()
    if not raw:
        print(json.dumps({"verify_chain": "empty", "count": 0, "ok": True}, ensure_ascii=False))
        return EXIT_OK
    prev_line_sha = None
    for i, ln in enumerate(raw):
        try:
            entry = json.loads(ln)
        except json.JSONDecodeError as e:
            print(f"chain break(1): index {i} JSON 파싱 실패 — {e}", file=sys.stderr)
            return EXIT_VERIFY_FAIL
        declared = entry.get("prev_sha256")
        rid = entry.get("record_id", "?")
        if declared != prev_line_sha:
            print(json.dumps({"verify_chain": "broken", "break_index": i, "record_id": rid,
                              "declared_prev": declared, "actual_prev": prev_line_sha,
                              "hint": "중간 삭제·삽입·변조 지점"}, ensure_ascii=False),
                  file=sys.stderr)
            return EXIT_VERIFY_FAIL
        prev_line_sha = _line_sha(ln)
    print(json.dumps({"verify_chain": "ok", "count": len(raw)}, ensure_ascii=False))
    return EXIT_OK


def cmd_show(a):
    entry = _find_sealed(a.record_id)
    if entry is None:
        print(f"not found: {a.record_id}", file=sys.stderr)
        return EXIT_NOTFOUND
    print(json.dumps(entry, ensure_ascii=False, indent=1))
    return EXIT_OK


def main(argv=None):
    p = argparse.ArgumentParser(description="사전등록 ledger (append-only SHA-256 봉인·freeze)")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("seal", help="record.json 을 ledger 에 SHA-256 봉인 추가(재봉인 거부)")
    c.add_argument("record", help="봉인할 record JSON 경로(record_id 필드 필수)")
    c.set_defaults(fn=cmd_seal)

    c = sub.add_parser("verify", help="봉인 해시 재계산 대조(exit 0 일치 / 1 불일치)")
    c.add_argument("record_id")
    c.set_defaults(fn=cmd_verify)

    c = sub.add_parser("verify-chain", help="append-only 체인 무결성 전수 검증(중간 삭제·삽입 탐지)")
    c.set_defaults(fn=cmd_verify_chain)

    c = sub.add_parser("show", help="봉인 entry 출력")
    c.add_argument("record_id")
    c.set_defaults(fn=cmd_show)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
