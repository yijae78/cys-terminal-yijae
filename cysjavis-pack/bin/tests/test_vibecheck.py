#!/usr/bin/env python3
"""test_vibecheck.py — javis_vibecheck.py 3게이트 positive + negative(fail-closed) 회귀.

설계 §C10.2 negative test 의무: 각 게이트는 "막아야 할 입력을 실제로 막는지"의 적대 케이스를
최소 1개 동반한다(막을 대상이 없는 게이트=미완). 여기서는 subprocess로 실제 CLI를 구동해
exit code(0 pass / 1 soft / 2 hard-fail)가 계약대로 나오는지 핀한다 — fixture는 tmp에 동적 생성.

핀 대상:
  docs      positive: L3 필수문서+front-matter+CLAUDE.md → exit 0
            negative: spec 결손 → exit 2 / front-matter 필드 결손 → exit 1
  security  positive: 클린 트리 → exit 0
            negative: 심어둔 private key → exit 2 / RLS 누락 → exit 2 / supabase 부재 → skip(0)
                      / .env 미ignore → exit 1
  integrity positive: pre-run 후 무변동 gate → exit 0
            negative: assertion 감소 → exit 2 / skip 증가 → exit 2 / self-mock 삽입 → exit 2
                      / pre-run 없는 gate → exit 2(순서 강제)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # cysjavis-pack/bin
VIBECHECK = os.path.join(BIN, "javis_vibecheck.py")


def _run(*args, cwd=None):
    """CLI 실행 → CompletedProcess. --json 강제해 파싱 가능하게."""
    p = subprocess.run([sys.executable, VIBECHECK, *args, "--json"],
                       capture_output=True, text=True, cwd=cwd)
    return p


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# NLC 정본 계약 골격(templates/*.md 실측): sot·context·layer·inheritance 완비.
_FM = ("---\nsot:\n  - /docs/_root-sot.md\ncontext:\n  - /docs/spec.md\n"
       "layer: 7\ninheritance:\n  - additive-only\n---\n")


def _doc(project, name, front_matter=True, subdir="docs"):
    body = (_FM if front_matter else "") + f"# {name}\n\ncontent\n"
    _write(os.path.join(project, subdir, f"{name}.md"), body)


class DocsGate(unittest.TestCase):
    def _scaffold_l3(self, project, front_matter=True):
        _doc(project, "requirement", front_matter)
        _doc(project, "spec", front_matter)
        _doc(project, "test", front_matter)
        _write(os.path.join(project, "CLAUDE.md"), "# bridge\n")

    def test_positive_l3_passes(self):
        with tempfile.TemporaryDirectory() as t:
            self._scaffold_l3(t)
            p = _run("docs", "--project", t, "--level", "L3")
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertEqual(json.loads(p.stdout)["verdict"], "pass")

    def test_negative_missing_spec_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            _doc(t, "requirement")
            _doc(t, "test")  # spec 없음
            _write(os.path.join(t, "CLAUDE.md"), "# bridge\n")
            p = _run("docs", "--project", t, "--level", "L3")
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "doc-chain" and it["severity"] == 2
                                and "spec" in it["message"] for it in out["findings"]))

    def test_negative_missing_frontmatter_soft(self):
        with tempfile.TemporaryDirectory() as t:
            self._scaffold_l3(t, front_matter=False)
            p = _run("docs", "--project", t, "--level", "L3")
            self.assertEqual(p.returncode, 1, p.stdout)  # 문서는 있으나 계약 골격 결손 → soft

    def test_negative_missing_context_field_soft(self):
        # context(SCDP 상속 목록)만 빠진 front-matter — layer 등은 존재 → context 결손 SOFT.
        fm_no_ctx = ("---\nsot:\n  - /docs/_root-sot.md\nlayer: 7\n"
                     "inheritance:\n  - additive-only\n---\n")
        with tempfile.TemporaryDirectory() as t:
            for k in ("requirement", "spec", "test"):
                _write(os.path.join(t, "docs", f"{k}.md"), fm_no_ctx + f"# {k}\n")
            _write(os.path.join(t, "CLAUDE.md"), "# bridge\n")
            p = _run("docs", "--project", t, "--level", "L3")
            self.assertEqual(p.returncode, 1, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "frontmatter" and it["severity"] == 1
                                and "context" in it["message"] for it in out["findings"]))

    def test_l1_no_required_docs_passes(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "CLAUDE.md"), "# bridge\n")
            p = _run("docs", "--project", t, "--level", "L1")
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_l1_2_alias_normalizes_to_l1(self):
        # M-2: viberoute 어휘 "L1-2"를 --level로 받아도 usage 에러 없이 L1으로 정규화.
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "CLAUDE.md"), "# bridge\n")
            p = _run("docs", "--project", t, "--level", "L1-2")
            self.assertEqual(p.returncode, 0, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "level" and "L1-2 → L1" in it["message"]
                                for it in out["findings"]), p.stdout)

    # ── NLC 정본 경로 정렬 회귀 (SOT: skills/vibecoding-docs/assets/README.md 대응표) ──
    def _canon(self, project, relpath):
        _write(os.path.join(project, relpath), _FM + "# doc\n\ncontent\n")

    def _scaffold_canon_l4(self, project):
        # 정본 경로: state-management(8)·database(6)·external/<서비스>(3, 경계)까지.
        for rp in ("docs/requirement.md", "docs/spec.md", "docs/test.md",
                   "docs/state-management.md", "docs/database.md", "docs/external/stripe.md"):
            self._canon(project, rp)
        _write(os.path.join(project, "CLAUDE.md"), "# bridge\n")

    def test_positive_nlc_canonical_l4_passes(self):
        with tempfile.TemporaryDirectory() as t:
            self._scaffold_canon_l4(t)
            p = _run("docs", "--project", t, "--level", "L4")
            self.assertEqual(p.returncode, 0, p.stdout)  # state-management·external 별칭/경로 인식

    def test_positive_nlc_canonical_l5_passes(self):
        with tempfile.TemporaryDirectory() as t:
            self._scaffold_canon_l4(t)
            for rp in ("docs/prd.md", "docs/userflow.md", "docs/plan.md",
                       "docs/design/visual.md", "docs/design/ui.md"):
                self._canon(t, rp)
            p = _run("docs", "--project", t, "--level", "L5")
            self.assertEqual(p.returncode, 0, p.stdout)  # design=ui.md·visual 별칭 인식·security 미요구

    def test_negative_state_management_removed_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            self._scaffold_canon_l4(t)
            os.remove(os.path.join(t, "docs", "state-management.md"))
            p = _run("docs", "--project", t, "--level", "L4")
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "doc-chain" and it["severity"] == 2
                                and "state" in it["message"] for it in out["findings"]))

    def test_negative_external_boundary_removed_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            self._scaffold_canon_l4(t)
            os.remove(os.path.join(t, "docs", "external", "stripe.md"))
            p = _run("docs", "--project", t, "--level", "L4")
            self.assertEqual(p.returncode, 2, p.stdout)  # docs/external/ 경로 규칙(.md ≥1) 위반
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "doc-chain" and it["severity"] == 2
                                and "boundary" in it["message"] for it in out["findings"]))


class SecurityGate(unittest.TestCase):
    def test_positive_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "app.py"), "x = 1\n")
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_negative_planted_private_key_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "leak.pem"),
                   "-----BEGIN RSA PRIVATE KEY-----\nMIIEabc123\n-----END RSA PRIVATE KEY-----\n")
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "secrets" and it["severity"] == 2
                                for it in out["findings"]))

    def test_negative_planted_aws_key_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "config.py"), 'AWS = "AKIA1234567890ABCDEF"\n')
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 2, p.stdout)

    def test_placeholder_secret_not_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "config.py"),
                   'api_key = "your_api_key_example_here_xxxx"\n'
                   'token = os.environ["TOKEN"]\n')
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            # placeholder는 secret으로 계상되지 않아야 함 → hard 없음
            out = json.loads(p.stdout)
            self.assertFalse(any(it["check"] == "secrets" and it["severity"] == 2
                                 for it in out["findings"]), p.stdout)

    def test_negative_rls_missing_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "supabase", "migrations", "001_init.sql"),
                   "create table public.profiles (id uuid primary key);\n"
                   "create table public.secrets_tbl (id uuid);\n"
                   "alter table public.profiles enable row level security;\n")
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "rls" and it["severity"] == 2
                                and "secrets_tbl" in it["message"] for it in out["findings"]))

    def test_rls_all_enabled_passes(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "supabase", "migrations", "001_init.sql"),
                   "create table public.profiles (id uuid primary key);\n"
                   "alter table public.profiles enable row level security;\n")
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_supabase_absent_skips(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "app.py"), "x = 1\n")
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 0, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "rls" and "skip" in it["message"]
                                for it in out["findings"]))

    def test_negative_env_not_ignored_soft(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "app.py"), "x = 1\n")
            _write(os.path.join(t, ".gitignore"), "node_modules\n")  # .env 없음
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 1, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "env-gitignore" and it["severity"] == 1
                                for it in out["findings"]))

    def test_negative_admin_route_no_guard_soft(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "server.js"),
                   "app.get('/admin/users', (req, res) => { res.json(users); });\n")
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 1, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "admin-exposure" and it["severity"] == 1
                                for it in out["findings"]))

    def test_negative_large_file_secret_hard_fail(self):
        """M-5: >1MB 파일에 숨긴 AWS 키도 스트리밍 스캔으로 검출(조용한 skip 제거)."""
        with tempfile.TemporaryDirectory() as t:
            filler = ("# harmless log line padding\n" * 60000)  # ≈1.6MB > 1MB 구 skip 임계
            _write(os.path.join(t, "big.log"),
                   filler + "\nAWS_KEY=AKIA1234567890ABCDEF\n" + filler)
            self.assertGreater(os.path.getsize(os.path.join(t, "big.log")), 1_000_000)
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t, "--no-history")
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "secrets" and it["severity"] == 2
                                and "big.log" in (it.get("evidence") or "")
                                for it in out["findings"]), p.stdout)

    def test_secrets_git_history_hard_fail(self):
        """이력에만 존재하고 작업트리엔 없는 secret도 검출(git log -p 경로)."""
        with tempfile.TemporaryDirectory() as t:
            env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
            subprocess.run(["git", "init", "-q"], cwd=t, env=env)
            _write(os.path.join(t, "secret.txt"),
                   "-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----\n")
            subprocess.run(["git", "add", "-A"], cwd=t, env=env)
            subprocess.run(["git", "commit", "-qm", "add"], cwd=t, env=env)
            os.remove(os.path.join(t, "secret.txt"))  # 작업트리에서 제거
            subprocess.run(["git", "add", "-A"], cwd=t, env=env)
            subprocess.run(["git", "commit", "-qm", "rm"], cwd=t, env=env)
            _write(os.path.join(t, ".gitignore"), ".env\n")
            p = _run("security", "--project", t)  # 이력 스캔 on
            self.assertEqual(p.returncode, 2, p.stdout)


_TESTFILE = (
    "import unittest\n\n"
    "class T(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        assert 1 == 1\n"
    "        assert 2 == 2\n"
    "        assert 3 == 3\n"
)


class IntegrityGate(unittest.TestCase):
    def _prerun(self, project):
        _write(os.path.join(project, "tests", "test_thing.py"), _TESTFILE)
        p = _run("integrity", "pre-run", "--project", project)
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_positive_unchanged_gate_passes(self):
        with tempfile.TemporaryDirectory() as t:
            self._prerun(t)
            p = _run("integrity", "gate", "--project", t)
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_negative_gate_without_prerun_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            _write(os.path.join(t, "tests", "test_thing.py"), _TESTFILE)
            p = _run("integrity", "gate", "--project", t)  # pre-run 없이
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any(it["check"] == "order" for it in out["findings"]))

    def test_negative_assertion_reduced_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            self._prerun(t)
            _write(os.path.join(t, "tests", "test_thing.py"),  # assert 3 → 1
                   "import unittest\n\nclass T(unittest.TestCase):\n"
                   "    def test_a(self):\n        assert 1 == 1\n")
            p = _run("integrity", "gate", "--project", t)
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any("assertion 감소" in it["message"] for it in out["findings"]))

    def test_negative_skip_increased_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            self._prerun(t)
            _write(os.path.join(t, "tests", "test_thing.py"),
                   "import unittest\n\nclass T(unittest.TestCase):\n"
                   "    @unittest.skip('x')\n    def test_a(self):\n"
                   "        assert 1 == 1\n        assert 2 == 2\n        assert 3 == 3\n")
            p = _run("integrity", "gate", "--project", t)
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any("skip 마커 증가" in it["message"] for it in out["findings"]))

    def test_negative_selfmock_inserted_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            self._prerun(t)
            _write(os.path.join(t, "tests", "test_thing.py"),
                   "import unittest\nfrom unittest.mock import MagicMock\n\n"
                   "class T(unittest.TestCase):\n"
                   "    def test_a(self):\n"
                   "        dep = MagicMock()\n"
                   "        assert 1 == 1\n        assert 2 == 2\n        assert 3 == 3\n")
            p = _run("integrity", "gate", "--project", t)
            self.assertEqual(p.returncode, 2, p.stdout)
            out = json.loads(p.stdout)
            self.assertTrue(any("self-mock 삽입" in it["message"] for it in out["findings"]))

    def test_negative_test_file_deleted_hard_fail(self):
        with tempfile.TemporaryDirectory() as t:
            self._prerun(t)
            os.remove(os.path.join(t, "tests", "test_thing.py"))
            p = _run("integrity", "gate", "--project", t)
            self.assertEqual(p.returncode, 2, p.stdout)


if __name__ == "__main__":
    unittest.main()
