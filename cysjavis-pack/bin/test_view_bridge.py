#!/usr/bin/env python3
"""test_view_bridge.py — javis_view_bridge.py 사이드카 단위 테스트 (W-PBa).

검증: 화이트리스트 통과/차단(../ traversal·심볼릭 링크 이탈), 토큰 없는 요청 404,
state 파일 생성·권한 0600, diff argv 고정성.

실행:  python3 cysjavis-pack/bin/test_view_bridge.py
"""
import importlib.util
import json
import os
import shutil
import stat
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import HTTPError

HERE = os.path.dirname(os.path.abspath(__file__))
MODPATH = os.path.join(HERE, "javis_view_bridge.py")


def load_module():
    spec = importlib.util.spec_from_file_location("javis_view_bridge", MODPATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bridge = load_module()


class ViewBridgeTest(unittest.TestCase):
    def setUp(self):
        # 임시 허용 루트 + 그 밖의 비밀 디렉토리.
        self.tmp = tempfile.mkdtemp(prefix="viewbridge-test-")
        self.root = os.path.join(self.tmp, "root")
        self.outside = os.path.join(self.tmp, "outside")
        os.makedirs(self.root)
        os.makedirs(self.outside)
        os.makedirs(os.path.join(self.root, "sub"))
        with open(os.path.join(self.root, "a.md"), "w") as f:
            f.write("# 제목\n\n본문")
        with open(os.path.join(self.outside, "secret.txt"), "w") as f:
            f.write("SECRET")
        # 루트 안에서 밖을 가리키는 심볼릭 링크(이탈 시도용).
        self.link = os.path.join(self.root, "escape")
        try:
            os.symlink(self.outside, self.link)
            self.have_symlink = True
        except OSError:
            self.have_symlink = False

        # 모듈 전역 화이트리스트·state 경로를 테스트 격리.
        bridge.ALLOWED_ROOTS = [os.path.realpath(self.root)]
        bridge.STATE_DIR = os.path.join(self.tmp, "viewer")
        bridge.STATE_PATH = os.path.join(bridge.STATE_DIR, "state.json")

        # 서버 기동(0-bind).
        self.token = "TESTTOKEN_abc123"
        bridge.Handler.token = self.token
        self.srv = ThreadingHTTPServer((bridge.BIND, 0), bridge.Handler)
        self.port = self.srv.server_address[1]
        self.th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.th.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --------------------------------------------------------------- helper
    def _url(self, path, tok=None):
        t = self.token if tok is None else tok
        base = "http://%s:%d" % (bridge.BIND, self.port)
        if tok == "":   # 토큰 없는 raw 경로
            return base + path
        return base + "/" + t + path

    def _get(self, path, tok=None):
        try:
            r = urlopen(self._url(path, tok), timeout=5)
            return r.status, r.read().decode()
        except HTTPError as e:
            return e.code, e.read().decode()

    # --------------------------------------------------------------- 토큰
    def test_missing_token_404(self):
        code, _ = self._get("/api/list?path=" + self.root, tok="")
        self.assertEqual(code, 404)

    def test_wrong_token_404(self):
        code, _ = self._get("/api/list?path=" + self.root, tok="WRONG")
        self.assertEqual(code, 404)

    def test_app_served_with_token(self):
        code, body = self._get("/app/")
        self.assertEqual(code, 200)
        self.assertIn("자비스 뷰어", body)

    # --------------------------------------------------------------- 화이트리스트
    def test_file_whitelist_pass(self):
        code, body = self._get("/api/file?path=" +
                               os.path.join(self.root, "a.md"))
        self.assertEqual(code, 200)
        j = json.loads(body)
        self.assertTrue(j["ok"])
        self.assertIn("본문", j["content"])

    def test_traversal_blocked(self):
        # <root>/../outside/secret.txt → realpath 정규화 후 루트 밖 → 403.
        p = os.path.join(self.root, "..", "outside", "secret.txt")
        code, body = self._get("/api/file?path=" + p)
        self.assertEqual(code, 403)
        self.assertEqual(json.loads(body)["error"], "path_denied")

    def test_absolute_outside_blocked(self):
        code, body = self._get("/api/file?path=" +
                               os.path.join(self.outside, "secret.txt"))
        self.assertEqual(code, 403)

    def test_symlink_escape_blocked(self):
        if not self.have_symlink:
            self.skipTest("symlink unsupported")
        # <root>/escape → outside/. 심볼릭 링크로 루트 이탈 시도.
        p = os.path.join(self.link, "secret.txt")
        code, body = self._get("/api/file?path=" + p)
        self.assertEqual(code, 403)
        self.assertEqual(json.loads(body)["error"], "path_denied")

    def test_within_roots_helper(self):
        self.assertIsNotNone(bridge.within_roots(
            os.path.join(self.root, "a.md")))
        self.assertIsNone(bridge.within_roots(
            os.path.join(self.outside, "secret.txt")))
        # 형제 prefix 오판 방지: root + "_sibling" 은 루트로 오인되면 안 됨.
        sib = os.path.realpath(self.root) + "_sibling"
        self.assertIsNone(bridge.within_roots(sib + "/x"))

    def test_list_within_roots(self):
        code, body = self._get("/api/list?path=" + self.root)
        self.assertEqual(code, 200)
        names = [e["name"] for e in json.loads(body)["entries"]]
        self.assertIn("a.md", names)
        self.assertIn("sub", names)

    # --------------------------------------------------------------- diff
    def test_diff_repo_denied(self):
        code, _ = self._get("/api/diff?repo=" + self.outside + "&base=HEAD")
        self.assertEqual(code, 403)

    def test_diff_bad_ref_option_injection(self):
        # 선두 '-' = git 옵션 주입 시도 → 400 bad_ref.
        code, body = self._get("/api/diff?repo=" + self.root +
                               "&base=--output%3Dfoo")
        self.assertEqual(code, 400)
        self.assertEqual(json.loads(body)["error"], "bad_ref")

    def test_diff_bad_ref_shell_meta(self):
        code, body = self._get("/api/diff?repo=" + self.root +
                               "&base=HEAD%3Brm%20-rf")   # 'HEAD;rm -rf'
        self.assertEqual(code, 400)

    def test_diff_argv_fixed(self):
        # subprocess.run 을 가로채 argv 가 고정 형태인지 검증(임의 인자 주입 차단).
        captured = {}

        class FakeResult:
            returncode = 0
            stdout = "diff --git a/x b/x\n"
            stderr = ""

        def fake_run(argv, **kw):
            captured["argv"] = argv
            return FakeResult()

        orig = bridge.subprocess.run
        bridge.subprocess.run = fake_run
        try:
            code, body = self._get("/api/diff?repo=" + self.root + "&base=HEAD")
        finally:
            bridge.subprocess.run = orig
        self.assertEqual(code, 200)
        self.assertEqual(
            captured["argv"],
            ["git", "-C", os.path.realpath(self.root), "diff", "HEAD"])

    # --------------------------------------------------------------- state
    def test_state_file_perms_0600(self):
        bridge.write_state(4321, "tok-xyz")
        self.assertTrue(os.path.isfile(bridge.STATE_PATH))
        mode = stat.S_IMODE(os.stat(bridge.STATE_PATH).st_mode)
        self.assertEqual(mode, 0o600, "state.json 권한은 0600 이어야 함")
        j = json.load(open(bridge.STATE_PATH))
        self.assertEqual(j["port"], 4321)
        self.assertEqual(j["token"], "tok-xyz")
        self.assertEqual(j["pid"], os.getpid())

    # --------------------------------------------------------------- 읽기전용
    def test_post_rejected(self):
        import urllib.request
        req = urllib.request.Request(
            self._url("/api/file?path=" + os.path.join(self.root, "a.md")),
            data=b"x", method="POST")
        try:
            urlopen(req, timeout=5)
            self.fail("POST 는 거부되어야 함")
        except HTTPError as e:
            self.assertEqual(e.code, 405)


if __name__ == "__main__":
    unittest.main(verbosity=2)
