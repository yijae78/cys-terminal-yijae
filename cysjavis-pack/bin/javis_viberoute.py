#!/usr/bin/env python3
"""javis_viberoute.py — §C4 Route-Contract (Level 판정의 결정론 계약)

설계 SOT: _research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md §C4 (L164-225).
층위: _route.py(fast/deliberate/slow = 응답 모드)와 직교하는 **구현 절차 강도** 라우터.
     합성(§C4.7): _route.py가 slow로 판정한 구현 작업에만 본 계약이 발동한다. Level 판정의
     단일 SOT — Level은 오직 여기서만 산출·기록된다.

핵심 계약:
- C4.1 입력 스키마: 6신호(true|false|unknown) + evidence + input_hash(sha256(signals 직렬화)).
- C4.2 순수 함수 판정표(first-match-wins 4행) — 0단계 정규화(unknown→true) 후 2^6=64조합 전칭.
       스키마 위반(신호 누락·enum 밖 값·직렬화 불일치)은 fail-closed: Level 미산출·exit 비0.
- C4.3 needs-grill: unknown≥2면 플래그(의도 합의 요구). 폴백은 "격상된 Level로 진행"(격하 아님).
- C4.4 critic은 advisory 한정 — {suspected_direction, evidence, confidence}. Level 변경 불가.
- C4.5 재분류: critic finding/인간 이의 → master|doctor 명시 승인(APR)+reason code(RC-01~04)
       → 새 Level 재판정. 격하(RC-02)는 실행 경로 무변경 기계 증거 필수.
- silent 변경 차단: 판정·critic·재분류를 각각 append-only ledger 레코드로 기록. 기록 없는
       Level 변동은 게이트 위반(verify가 탐지).

ledger: $JAVIS_ROOT/_round/vibecoding-ledger/route-log.jsonl (개인경로 하드코딩 금지 — pack scan
       gate 준수, javis_task 관례). 배포 시 JAVIS_ROOT=워크스페이스 루트면 정본 경로로 해소된다.
       CYS_VIBEROUTE_LEDGER 또는 --ledger로 override(테스트).

exit codes: 0 ok · 2 usage · 3 JSON 파싱 실패 · 4 fail-closed(스키마/enum/hash — Level 미산출) ·
            5 재분류 무효(승인/사유/증거 결여) · 6 verify 게이트 위반(silent 변경/변조)

사용법:
    python3 javis_viberoute.py judge --input task.json      # 또는 stdin(--input -)
    python3 javis_viberoute.py hash --input signals.json    # input_hash 산출(테스트 보조)
    python3 javis_viberoute.py critic --task-id T1 --input-hash <h> \\
        --direction down --evidence "주석뿐" --confidence low
    python3 javis_viberoute.py reclassify --task-id T1 --from-level L4 --to-level L1-2 \\
        --approval-id APR-20260718-001 --reason-code RC-02 \\
        --machine-evidence "AST diff → 실행경로 무변경"
    python3 javis_viberoute.py verify --task-id T1        # 유효 Level + 게이트 위반 검사
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import uuid

ROOT = os.environ.get("JAVIS_ROOT") or os.getcwd()  # 개인경로 하드코딩 금지(pack scan gate) — env 또는 CWD

# ── §C4.1 신호·enum·레벨 정의 ──────────────────────────────────────────────
# 신호 순서는 표기 안정성용(직렬화 해시는 sort_keys라 순서 무관).
SIGNAL_KEYS = (
    "persistent_data",
    "external_integration",
    "deploy_exposure",
    "scale_modules",
    "brownfield",
    "new_service",
)
VALUE_ENUM = ("true", "false", "unknown")
LEVELS = ("L1-2", "L3", "L4", "L5")
LEVEL_ORDER = {"L1-2": 0, "L3": 1, "L4": 2, "L5": 3}  # 격상/격하 방향 계산용

# M-2 어휘 통일: viberoute Level 토큰(L1-2 유지) → javis_vibecheck.py --level(L1|L3|L4|L5) 매핑.
# vibecheck의 "L1"은 LEVEL_DOCS 주석상 "L1~L2 스크립트·데모"를 포괄하므로 L1-2→L1. 나머지는 항등.
# (vibecheck 코드는 w-vibecheck 소유 — 여기선 viberoute 출력을 정합시키는 단방향 매핑만 제공.)
VIBECHECK_LEVEL_MAP = {"L1-2": "L1", "L3": "L3", "L4": "L4", "L5": "L5"}


def to_vibecheck_level(level):
    """viberoute Level → vibecheck --level 인자. 매핑 밖 값은 None(합성 파이프라인이 판별·차단)."""
    return VIBECHECK_LEVEL_MAP.get(level)

# ── §C4.5 재분류 계약 상수 ─────────────────────────────────────────────────
APR_RE = re.compile(r"^APR-\d{8}-\d{3}$")             # C1.3 approval_id 형식
REASON_CODES = ("RC-01", "RC-02", "RC-03", "RC-04")
# RC-01 은폐된 연동 발견(격상) / RC-02 주석·포맷뿐인 델타(격하) /
# RC-03 승인된 scope 변경 / RC-04 pilot 롤백. RC-01=up·RC-02=down 방향 고정.
UP_ONLY_CODES = ("RC-01",)
DOWN_ONLY_CODES = ("RC-02",)

EXIT_OK, EXIT_USAGE, EXIT_PARSE = 0, 2, 3
EXIT_FAILCLOSED, EXIT_RECLASS, EXIT_GATE = 4, 5, 6


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


# ── 순수 함수 계층 (import 대상 — 테스트가 직접 호출) ───────────────────────
def compute_input_hash(signals) -> str:
    """C4.1 input_hash = sha256(signals 직렬화). 정규 직렬화: sort_keys·tight separators.
    같은 signals(키 순서 무관)면 항상 같은 해시 — 결정론."""
    canon = json.dumps(signals, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def validate_schema(payload) -> list:
    """C4.2 fail-closed 검증 — 문제 목록 반환(빈 리스트=통과). Level을 '낮게 추정'하지 않는다.
    검사: 루트 dict / signals dict / 6신호 정확 존재(누락·잉여 모두 위반) / 각 신호 dict +
    value enum / input_hash 제공 시 직렬화 일치."""
    if not isinstance(payload, dict):
        return ["루트가 JSON 객체가 아님"]
    signals = payload.get("signals")
    if not isinstance(signals, dict):
        return ["signals 누락 또는 객체 아님"]
    problems = []
    keys = set(signals.keys())
    missing = [k for k in SIGNAL_KEYS if k not in keys]
    extra = [k for k in keys if k not in SIGNAL_KEYS]
    if missing:
        problems.append("신호 누락: %s" % missing)
    if extra:
        problems.append("미지 신호(스키마 밖): %s" % extra)  # 미지 신호=모호 → fail-closed
    for k in SIGNAL_KEYS:
        s = signals.get(k)
        if not isinstance(s, dict):
            problems.append("신호 %s가 객체 아님" % k)
            continue
        v = s.get("value")
        if v not in VALUE_ENUM:
            problems.append("신호 %s value가 enum 밖: %r" % (k, v))
    ih = payload.get("input_hash")
    if ih is not None:
        want = compute_input_hash(signals)
        if ih != want:
            problems.append("input_hash 불일치: got %s want %s" % (ih, want))
    return problems


def normalize(signals) -> dict:
    """C4.2 0단계 정규화 — unknown은 true로 간주(보수적 격상). value=='false'만 false.
    (validate_schema 통과 신호 전제 — value는 enum 3치.)"""
    return {k: signals[k]["value"] in ("true", "unknown") for k in SIGNAL_KEYS}


def unknown_count(signals) -> int:
    return sum(1 for k in SIGNAL_KEYS if signals[k]["value"] == "unknown")


def decide_level(n) -> str:
    """C4.2 판정표 — first-match-wins. 입력 n = 정규화된 6신호 bool dict. 순수 함수.
    전칭성: true 신호가 하나라도 있으면 행1~3 중 하나에 반드시 걸리고, 전부 false면 행4 —
    64조합 전체가 정확히 한 행에 떨어진다(미산출 0)."""
    pd = n["persistent_data"]
    ei = n["external_integration"]
    de = n["deploy_exposure"]
    sm = n["scale_modules"]
    bf = n["brownfield"]
    ns = n["new_service"]
    if de and (ns or (pd and ei)):                 # 행1
        return "L5"
    if pd or ei or ns or de:                        # 행2
        return "L4"
    if sm or bf:                                    # 행3
        return "L3"
    return "L1-2"                                   # 행4 (전 신호 false)


def _direction(from_level, to_level) -> str:
    """레벨 격상/격하/동일 방향. LEVEL_ORDER 밖 값은 'invalid'."""
    if from_level not in LEVEL_ORDER or to_level not in LEVEL_ORDER:
        return "invalid"
    a, b = LEVEL_ORDER[from_level], LEVEL_ORDER[to_level]
    return "up" if b > a else ("down" if b < a else "same")


def validate_reclass(from_level, to_level, approval_id, reason_code, machine_evidence) -> list:
    """C4.5 재분류 유효성 — 문제 목록 반환(빈=유효). 승인 부재·enum 밖 사유·방향 불일치·
    격하 기계증거 결여를 전부 차단(fail-closed). verify와 reclassify 양쪽이 공유하는 단일 판정."""
    problems = []
    if from_level not in LEVEL_ORDER:
        problems.append("from_level 무효: %r" % (from_level,))
    if to_level not in LEVEL_ORDER:
        problems.append("to_level 무효: %r" % (to_level,))
    if not approval_id or not APR_RE.match(approval_id):
        problems.append("approval_id 부재/형식오류(APR-YYYYMMDD-NNN): %r" % (approval_id,))
    if reason_code not in REASON_CODES:
        problems.append("reason_code enum 밖(RC-01~04): %r" % (reason_code,))
    d = _direction(from_level, to_level)
    if d != "invalid":
        if reason_code in UP_ONLY_CODES and d != "up":
            problems.append("%s는 격상 전용인데 방향=%s" % (reason_code, d))
        if reason_code in DOWN_ONLY_CODES and d != "down":
            problems.append("%s는 격하 전용인데 방향=%s" % (reason_code, d))
        if d == "down" and not (machine_evidence and str(machine_evidence).strip()):
            problems.append("격하는 실행경로 무변경 기계증거(--machine-evidence) 필수")
    return problems


# ── ledger 계층 (append-only) ──────────────────────────────────────────────
def _ledger_path(a=None) -> str:
    if a is not None and getattr(a, "ledger", None):
        return a.ledger
    env = os.environ.get("CYS_VIBEROUTE_LEDGER")
    if env:
        return env
    return os.path.join(ROOT, "_round", "vibecoding-ledger", "route-log.jsonl")


def _append(ledger, rec):
    """append-only 기록 — 기존 줄은 절대 재작성하지 않는다. 원자적 append(O_APPEND)."""
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def _read_records(ledger, task_id=None):
    """ledger 전 레코드(또는 task_id 필터). 비-JSON/빈 줄은 skip(귀속 불가)."""
    out = []
    if not os.path.isfile(ledger):
        return out
    with open(ledger, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if task_id is None or rec.get("task_id") == task_id:
                out.append(rec)
    return out


# ── CLI 명령 ───────────────────────────────────────────────────────────────
def _load_input(a):
    """--input FILE 또는 stdin(--input -). 반환 (payload|None, err|None)."""
    src = a.input
    try:
        if src in (None, "-"):
            raw = sys.stdin.read()
        else:
            with open(src, encoding="utf-8") as f:
                raw = f.read()
    except OSError as e:
        return None, "입력 읽기 실패: %s" % e
    try:
        return json.loads(raw), None
    except ValueError as e:
        return None, "JSON 파싱 실패: %s" % e


def cmd_judge(a):
    payload, err = _load_input(a)
    if err:
        print(json.dumps({"error": err}, ensure_ascii=False), file=sys.stderr)
        return EXIT_PARSE
    problems = validate_schema(payload)
    if problems:
        # fail-closed: Level 미산출·차단·보고 (C4.2). 통과가 아니라 차단이 기본값.
        print(json.dumps({"gate": "fail-closed", "level": None, "problems": problems},
                         ensure_ascii=False), file=sys.stderr)
        return EXIT_FAILCLOSED
    signals = payload["signals"]
    norm = normalize(signals)
    uc = unknown_count(signals)
    level = decide_level(norm)
    needs_grill = uc >= 2                                   # C4.3
    ih = payload.get("input_hash") or compute_input_hash(signals)
    rec = {
        "type": "judgment",
        "id": "RT-%s-%s" % (time.strftime("%Y%m%d%H%M%S"), uuid.uuid4().hex[:6]),
        "task_id": payload.get("task_id"),
        "input_hash": ih,
        "signals": signals,
        "normalized": norm,
        "unknown_count": uc,
        "needs_grill": needs_grill,
        "level": level,
        "at": _now(),
    }
    _append(_ledger_path(a), rec)
    print(json.dumps({
        "task_id": rec["task_id"], "level": level,
        "vibecheck_level": to_vibecheck_level(level),  # M-2: vibecheck --level 인자로 넘길 매핑값
        "normalized": norm, "unknown_count": uc, "needs_grill": needs_grill,
        "input_hash": ih, "route_id": rec["id"], "recorded": True,
    }, ensure_ascii=False))
    return EXIT_OK


def cmd_hash(a):
    payload, err = _load_input(a)
    if err:
        print(json.dumps({"error": err}, ensure_ascii=False), file=sys.stderr)
        return EXIT_PARSE
    signals = payload.get("signals") if isinstance(payload, dict) else None
    if not isinstance(signals, dict):
        print(json.dumps({"error": "signals 없음"}, ensure_ascii=False), file=sys.stderr)
        return EXIT_FAILCLOSED
    print(compute_input_hash(signals))
    return EXIT_OK


def cmd_critic(a):
    """C4.4 critic advisory 기록 — Level 불변. 어떤 경우에도 Level을 바꾸지 않는다."""
    if a.direction not in ("up", "down"):
        print("error: --direction은 up|down", file=sys.stderr)
        return EXIT_USAGE
    if a.confidence not in ("high", "medium", "low"):
        print("error: --confidence는 high|medium|low", file=sys.stderr)
        return EXIT_USAGE
    rec = {
        "type": "critic",
        "task_id": a.task_id,
        "input_hash": a.input_hash,           # 어느 판정에 대한 finding인지 참조
        "suspected_direction": a.direction,
        "evidence": a.evidence or "",
        "confidence": a.confidence,
        "advisory": True,                     # advisory finding만 — Level 변경 권한 없음
        "level_unchanged": True,
        "at": _now(),
    }
    _append(_ledger_path(a), rec)
    print(json.dumps({"critic": "recorded", "task_id": a.task_id,
                      "suspected_direction": a.direction, "level_unchanged": True},
                     ensure_ascii=False))
    return EXIT_OK


def cmd_reclassify(a):
    """C4.5 재분류 기록 — 명시 승인자(APR)+reason code 필수. 무효는 fail-closed(기록 거부)."""
    problems = validate_reclass(a.from_level, a.to_level, a.approval_id,
                                a.reason_code, a.machine_evidence)
    if problems:
        print(json.dumps({"reclassify": "denied", "problems": problems},
                         ensure_ascii=False), file=sys.stderr)
        return EXIT_RECLASS
    rec = {
        "type": "reclassification",
        "task_id": a.task_id,
        "from_level": a.from_level,
        "to_level": a.to_level,
        "direction": _direction(a.from_level, a.to_level),
        "approval_id": a.approval_id,
        "reason_code": a.reason_code,
        "machine_evidence": (a.machine_evidence or ""),
        "at": _now(),
    }
    _append(_ledger_path(a), rec)
    print(json.dumps({"reclassify": "recorded", "task_id": a.task_id,
                      "from_level": a.from_level, "to_level": a.to_level,
                      "reason_code": a.reason_code, "approval_id": a.approval_id},
                     ensure_ascii=False))
    return EXIT_OK


def replay(records) -> tuple:
    """ledger 레코드(단일 task, 시간순)를 재생해 (effective_level, violations) 산출.
    silent 변경 차단의 결정론 판정: 판정 base에서 유효 재분류만 적용, 무효/미지 레코드는 위반.
    - judgment: signals로 decide_level·input_hash를 **재계산해 기록값과 대조**(B-1/M-6).
      기록된 level을 신뢰하지 않는다 — 위조된 signals↔level·input_hash 불일치를 게이트 fail로 잡는다.
    - critic: advisory·무시(Level 불변)
    - reclassification: validate_reclass 통과 + from_level==현 effective(사슬 무결성) 시에만 적용
      (재분류 to_level은 승인된 human/master 오버라이드라 signals 재계산 대상 아님)
    - 그 외 type: 미지 레코드 = silent 변경 의심 → 위반"""
    violations = []
    effective = None
    for r in records:
        t = r.get("type")
        if t == "judgment":
            signals = r.get("signals")
            rec_level = r.get("level")
            rec_hash = r.get("input_hash")
            # M-6: input_hash를 signals 직렬화로 재검증(validate_schema가 rec_hash 대조 포함).
            probs = validate_schema({"signals": signals, "input_hash": rec_hash})
            if rec_hash is None:
                probs = probs + ["판정 레코드 input_hash 부재 — 재검증 불가"]
            if probs:
                violations.append("판정 레코드 무결성 위반: %s" % probs)
                effective = None            # 신뢰 불가 — 이 판정을 base로 쓰지 않는다
                continue
            # B-1: 기록된 level을 재계산과 대조. 위조(signals↔level 불일치)면 게이트 fail.
            recomputed = decide_level(normalize(signals))
            if recomputed != rec_level:
                violations.append("판정 위조 의심: 기록 level=%s ≠ signals 재계산=%s"
                                  % (rec_level, recomputed))
                effective = recomputed      # 위조 level 신뢰 금지 — 진짜 재계산값 노출
                continue
            effective = rec_level
        elif t == "critic":
            continue
        elif t == "reclassification":
            if effective is None:
                violations.append("판정 전 재분류 — 근거 판정 부재")
                continue
            probs = validate_reclass(r.get("from_level"), r.get("to_level"),
                                     r.get("approval_id"), r.get("reason_code"),
                                     r.get("machine_evidence"))
            if probs:
                violations.append("무효 재분류(승인/사유/증거 결여): %s" % probs)
                continue
            if r.get("from_level") != effective:
                violations.append("사슬 단절: from_level %s ≠ 현 effective %s"
                                  % (r.get("from_level"), effective))
                continue
            effective = r.get("to_level")
        else:
            violations.append("미지 레코드 type %r — silent 변경 의심" % (t,))
    if effective is None:
        violations.append("판정(judgment) 레코드 부재")
    return effective, violations


def cmd_verify(a):
    records = _read_records(_ledger_path(a), a.task_id)
    effective, violations = replay(records)
    out = {"task_id": a.task_id, "effective_level": effective,
           "gate": "pass" if not violations else "fail", "violations": violations}
    stream = sys.stdout if not violations else sys.stderr
    print(json.dumps(out, ensure_ascii=False), file=stream)
    return EXIT_OK if not violations else EXIT_GATE


def main(argv=None):
    p = argparse.ArgumentParser(
        description="§C4 Route-Contract — Level 판정의 결정론 계약",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def _add_ledger(c):
        c.add_argument("--ledger", default=None,
                       help="ledger 경로 override(기본: $JAVIS_ROOT/_round/vibecoding-ledger/route-log.jsonl)")

    c = sub.add_parser("judge", help="입력 JSON→Level 판정·기록")
    c.add_argument("--input", default="-", help="입력 JSON 파일(기본 stdin '-')")
    _add_ledger(c)
    c.set_defaults(fn=cmd_judge)

    c = sub.add_parser("hash", help="signals의 input_hash 산출(테스트 보조)")
    c.add_argument("--input", default="-")
    c.set_defaults(fn=cmd_hash)

    c = sub.add_parser("critic", help="C4.4 advisory finding 기록(Level 불변)")
    c.add_argument("--task-id", dest="task_id", required=True)
    c.add_argument("--input-hash", dest="input_hash", default=None)
    c.add_argument("--direction", required=True, help="up|down(의심 방향)")
    c.add_argument("--evidence", default=None)
    c.add_argument("--confidence", required=True, help="high|medium|low")
    _add_ledger(c)
    c.set_defaults(fn=cmd_critic)

    c = sub.add_parser("reclassify", help="C4.5 재분류 기록(APR+reason code 필수)")
    c.add_argument("--task-id", dest="task_id", required=True)
    c.add_argument("--from-level", dest="from_level", required=True)
    c.add_argument("--to-level", dest="to_level", required=True)
    c.add_argument("--approval-id", dest="approval_id", required=True)
    c.add_argument("--reason-code", dest="reason_code", required=True)
    c.add_argument("--machine-evidence", dest="machine_evidence", default=None,
                   help="격하(RC-02) 시 실행경로 무변경 기계증거 필수")
    _add_ledger(c)
    c.set_defaults(fn=cmd_reclassify)

    c = sub.add_parser("verify", help="유효 Level 재생 + silent 변경 게이트 검사")
    c.add_argument("--task-id", dest="task_id", required=True)
    _add_ledger(c)
    c.set_defaults(fn=cmd_verify)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
