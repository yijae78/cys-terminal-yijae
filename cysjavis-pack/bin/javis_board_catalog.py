#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""javis_board_catalog.py — 스킬보드 카탈로그(board-catalog.json) 제안·무결성 도구.

★기계 제안·사람 승인(acl 부여는 오너 몫) — 카탈로그 미포함=암묵 차단은 보안 경계다.
  propose는 후보 JSON을 stdout으로만 내보내고 파일을 절대 쓰지 않는다. 카탈로그에 없는
  스킬이 보드에서 실행 불가한 것은 결함이 아니라 deny-by-default 보안 경계이므로, 병합
  (실제 등재·acl 부여)은 반드시 사람이 승인해 수행한다.

서브커맨드:
  propose  설치 스킬(pack/skills + ~/.claude*/skills — skill_roots) 중 카탈로그 미등재만 후보 제안.
           출력 {"candidates":[{name, label, scope, acl:2, gate:"hitl"}]} — 파일 쓰기 없음.
  check    board-catalog.json의 모든 name이 설치 스킬(skill_roots 중 한 곳)로 존재하는지 검사.
           전부 존재=exit 0 · 불일치=exit 1(불일치 목록 stderr). (preflight C66과 동일 로직의
           단독 실행 표면.)

의존성: 파이썬 표준 라이브러리만. 네트워크·LLM 호출 없음.
"""
import argparse
import json
import os
import sys


def pack_dir():
    """pack 위치 — CYS_PACK_DIR env 폴백 ~/.cys/pack (다른 pack bin 도구와 동일 관례)."""
    return os.environ.get("CYS_PACK_DIR") or os.path.join(os.path.expanduser("~"), ".cys", "pack")


def _referenced_names(catalog_path):
    """board-catalog.json이 참조하는 스킬명 목록(domains[].skills[].name + actions[].name).
    중복 제거·순서 보존. 읽기/파싱 실패는 예외를 그대로 올린다(호출자가 처리)."""
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)
    names = []
    if isinstance(data, dict):
        for dom in data.get("domains", []):
            if isinstance(dom, dict):
                for s in dom.get("skills", []):
                    if isinstance(s, dict) and s.get("name"):
                        names.append(s["name"])
        for act in data.get("actions", []):
            if isinstance(act, dict) and act.get("name"):
                names.append(act["name"])
    return list(dict.fromkeys(names))


def skill_roots():
    """스킬 설치 루트 전체 — pack/skills + ~/.claude*/skills (실측 2026-07-16: 보드 카탈로그
    스킬은 claude 프로필 skills에 설치돼 있고 일회용 워커도 프로필 스킬을 로드한다.
    pack 단일 루트는 설치된 스킬을 미설치로 오탐)."""
    roots = [os.path.join(pack_dir(), "skills")]
    home = os.path.expanduser("~")
    try:
        for name in sorted(os.listdir(home)):
            if name == ".claude" or name.startswith(".claude-"):
                d = os.path.join(home, name, "skills")
                if os.path.isdir(d):
                    roots.append(d)
    except OSError:
        pass
    return roots


def _skill_installed(name, roots):
    """스킬 설치 여부 — 루트 중 한 곳에 <name>/ 디렉터리가 있으면 설치."""
    return any(os.path.isdir(os.path.join(r, name)) for r in roots)


def _installed_skills(skills_root):
    """지정 루트 하위에서 SKILL.md를 가진 디렉터리명 목록(정렬)."""
    out = []
    try:
        entries = sorted(os.listdir(skills_root))
    except OSError:
        return out
    for name in entries:
        if os.path.isfile(os.path.join(skills_root, name, "SKILL.md")):
            out.append(name)
    return out


def _skill_desc(skill_dir):
    """SKILL.md에서 description 추출 — frontmatter 'description:' 첫 줄 우선, 없으면 본문 첫 문단 80자."""
    try:
        with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return ""
    body_start = 0
    if lines and lines[0].strip() == "---":
        body_start = len(lines)
        for i in range(1, len(lines)):
            s = lines[i].strip()
            if s == "---":
                body_start = i + 1
                break
            if s.lower().startswith("description:"):
                desc = s.split(":", 1)[1].strip()
                if desc:
                    return desc
    for ln in lines[body_start:]:
        s = ln.strip()
        if s and not s.startswith("#"):
            return s[:80]
    return ""


def cmd_propose(a):
    pack = pack_dir()
    try:
        registered = set(_referenced_names(os.path.join(pack, "board-catalog.json")))
    except (OSError, ValueError):
        registered = set()   # 카탈로그 부재/파손 = 전부 후보(제안만·병합은 사람)
    candidates = []
    seen = set()
    for root in skill_roots():
        for name in _installed_skills(root):
            if name in registered or name in seen:
                continue
            seen.add(name)
            candidates.append({"name": name, "label": name,
                               "scope": _skill_desc(os.path.join(root, name)),
                               "acl": 2, "gate": "hitl"})
    print(json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2))
    return 0


def cmd_check(a):
    pack = pack_dir()
    try:
        names = _referenced_names(os.path.join(pack, "board-catalog.json"))
    except (OSError, ValueError) as e:
        print("board-catalog.json 읽기/파싱 실패: %s" % e, file=sys.stderr)
        return 1
    roots = skill_roots()
    missing = [n for n in names if not _skill_installed(n, roots)]
    if missing:
        print("카탈로그 참조 스킬 미설치(전 루트 부재): %s" % ", ".join(missing), file=sys.stderr)
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description="스킬보드 카탈로그 제안·무결성 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("propose").set_defaults(fn=cmd_propose)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
