#!/usr/bin/env python3
"""javis_evidence_manifest.py — 근거 manifest 게이트 (v3.2 §C9)

계약(출처: _research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md §C9):
- Phase 0 입력 게이트: 제안·설계 문서가 인용하는 근거 파일의 {경로, SHA-256, 존재} manifest 를
  결정론 스크립트로 검증한다. 불일치=입장 차단(fail-closed).
- generate: 파일 목록 → 각 파일의 절대경로·SHA-256·크기·줄수를 manifest.json 으로 봉인.
  존재하지 않는 입력 파일은 즉시 실패(exit 1) — 유령 근거 봉인 차단.
- check: manifest 의 각 항목을 실제 파일과 대조 — 존재 + SHA-256 일치. 하나라도 불일치=exit 1.

exit codes: 0 ok · 1 fail(존재/해시 불일치) · 2 usage · 3 manifest not found
"""
import argparse
import hashlib
import json
import os
import sys
import time

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_NOTFOUND = 0, 1, 2, 3


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _stat(path):
    """(sha256, size_bytes, line_count) — 존재하지 않으면 FileNotFoundError."""
    sha = _sha256_file(path)
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        lines = sum(1 for _ in f)
    return sha, size, lines


def cmd_generate(a):
    entries = []
    missing = []
    for raw in a.files:
        path = os.path.abspath(raw)
        if not os.path.isfile(path):
            missing.append(path)
            continue
        sha, size, lines = _stat(path)
        entries.append({"path": path, "sha256": sha,
                        "size_bytes": size, "line_count": lines})
    if missing:
        for m in missing:
            print(f"fail(1): 근거 파일 부재 — {m}", file=sys.stderr)
        return EXIT_FAIL
    manifest = {
        "kind": "evidence-manifest",
        "version": 1,
        "generated_at": _now(),
        "file_count": len(entries),
        "files": entries,
    }
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = f"{out}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, out)
    print(json.dumps({"generate": "ok", "out": out,
                      "file_count": len(entries)}, ensure_ascii=False))
    return EXIT_OK


def cmd_check(a):
    try:
        with open(a.manifest, encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"not found: {a.manifest}", file=sys.stderr)
        return EXIT_NOTFOUND
    except json.JSONDecodeError as e:
        print(f"error: manifest JSON 파싱 실패: {e}", file=sys.stderr)
        return EXIT_USAGE
    files = manifest.get("files", [])
    if not files:
        print("fail(1): manifest 에 files 항목 없음 — 빈 근거 게이트 거부", file=sys.stderr)
        return EXIT_FAIL
    failures = []
    for ent in files:
        path = ent.get("path")
        want = ent.get("sha256")
        if not path or not os.path.isfile(path):
            failures.append((path, "missing", None))
            continue
        got = _sha256_file(path)
        if got != want:
            failures.append((path, "sha256-mismatch", got))
    result = {"check": a.manifest, "file_count": len(files),
              "pass": not failures, "failures": len(failures)}
    print(json.dumps(result, ensure_ascii=False))
    if failures:
        for path, why, got in failures:
            detail = f" (got {got})" if got else ""
            print(f"fail(1): {why} — {path}{detail}", file=sys.stderr)
        return EXIT_FAIL
    return EXIT_OK


def main(argv=None):
    p = argparse.ArgumentParser(description="근거 manifest 게이트 (§C9 fail-closed)")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("generate", help="파일 목록 → manifest.json(경로·SHA-256·존재 봉인)")
    c.add_argument("--files", nargs="+", required=True, help="근거 파일 경로 목록")
    c.add_argument("--out", required=True, help="출력 manifest.json 경로")
    c.set_defaults(fn=cmd_generate)

    c = sub.add_parser("check", help="manifest 대조 — 존재·SHA-256 일치(불일치=exit 1)")
    c.add_argument("manifest")
    c.set_defaults(fn=cmd_check)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
