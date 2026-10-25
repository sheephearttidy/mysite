# -*- coding: utf-8 -*-
"""Web 层冒烟:Flask test_client(不起端口)。

覆盖:前台页面渲染、公开接口、未登录 401、登录态 CRUD 路由全链路
(201/204/404)、公开写接口限频。登录态用 session_transaction 直接注入,
不碰真实密码。
"""
import os
import shutil
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "admin"))

import db  # noqa: E402
import app as appmod  # noqa: E402  (导入时会对开发库执行幂等建表,无害)

# 注意:DB_PATH 不能在模块级设置——discover 会先导入全部测试模块,
# 之后 test_db 的 setUp/tearDown 会反复改写并删掉自己的临时库,
# 到 test_web 真正运行时模块级指向的目录早已不存在。
# 所以在 setUpClass 里再指向本类专属的临时库。


class WebTestBase(unittest.TestCase):
    DB_PATH = None

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="mysite-web-")
        cls.DB_PATH = os.path.join(cls._tmp, "t.db")
        db.DB_PATH = cls.DB_PATH
        db.init_db(cls.DB_PATH)
        with db.get_db() as c:
            for t in ("skills", "timeline", "stats", "works", "profile", "honors",
                      "notes", "friendlinks", "songs", "questions", "doodles",
                      "messages", "message_threads", "photos", "notices",
                      "countdowns"):
                c.execute(f"DELETE FROM {t}")

    @classmethod
    def tearDownClass(cls):
        db.DB_PATH = os.path.join(ROOT, "admin", "data", "mysite.db")
        shutil.rmtree(cls._tmp, ignore_errors=True)


def login(client):
    """注入登录 session,绕过密码/验证码(它们有自己的手测);
    login_required 会查 sessions 表,所以要先建一条真实会话"""
    sid = "test-sid-0001"
    db.add_session(sid, "127.0.0.1", "unittest")
    with client.session_transaction() as s:
        s["user"] = appmod.ADMIN_USER
        s["sid"] = sid
        s["last_seen"] = int(time.time())


class TestPages(WebTestBase):
    def setUp(self):
        self.c = appmod.app.test_client()

    def test_front_pages_render(self):
        for p in ["/", "/about.html", "/skills.html", "/works.html",
                  "/campus.html", "/map.html", "/contact.html", "/gallery.html"]:
            r = self.c.get(p)
            self.assertEqual(r.status_code, 200, p)

    def test_unknown_page_404(self):
        self.assertEqual(self.c.get("/nonexist.html").status_code, 404)

    def test_public_apis(self):
        self.assertEqual(self.c.get("/api/health").status_code, 200)
        self.assertIn("questions", self.c.get("/api/questions").get_json())
        self.assertIn("doodles", self.c.get("/api/doodles").get_json())
        d = self.c.get("/api/page/index").get_json()
        self.assertIn("site", d)
        self.assertIn("onthisday", d)
        fx = self.c.get("/api/fx").get_json()
        self.assertIn("pet", fx)


class TestCrudRoutes(WebTestBase):
    def setUp(self):
        self.c = appmod.app.test_client()
        login(self.c)

    def test_unauthorized_401(self):
        anon = appmod.app.test_client()
        for m, p in [("post", "/api/skills"), ("put", "/api/skills/1"),
                     ("delete", "/api/skills/1")]:
            r = getattr(anon, m)(p, json={})
            self.assertEqual(r.status_code, 401, f"{m} {p}")

    def test_crud_full_cycle(self):
        # POST 201 返回整行
        r = self.c.post("/api/skills", json={"name": "测试技能", "percent": 88})
        self.assertEqual(r.status_code, 201)
        row = r.get_json()
        self.assertEqual(row["percent"], 88)
        # PUT 部分更新
        r = self.c.put(f"/api/skills/{row['id']}", json={"note": "改过"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["note"], "改过")
        self.assertEqual(r.get_json()["percent"], 88)
        # DELETE 204 / 再删 404
        self.assertEqual(self.c.delete(f"/api/skills/{row['id']}").status_code, 204)
        self.assertEqual(self.c.delete(f"/api/skills/{row['id']}").status_code, 404)

    def test_all_kinds_roundtrip(self):
        """8 类内容各走一遍 POST→DELETE,验证路由工厂(或手写路由)全通"""
        samples = {
            "timeline": {"title": "t"},
            "stats": {"label": "s"},
            "works": {"title": "w"},
            "profile": {"label": "p"},
            "honors": {"title": "h"},
            "notes": {"text": "n"},
            "friendlinks": {"name": "f", "url": "https://x.dev"},  # 路由层必填校验
            "skills": {"name": "k"},
        }
        for kind, body in samples.items():
            r = self.c.post(f"/api/{kind}", json=body)
            self.assertEqual(r.status_code, 201, kind)
            rid = r.get_json()["id"]
            r = self.c.put(f"/api/{kind}/{rid}", json={"sort": 5})
            self.assertEqual(r.status_code, 200, kind)
            self.assertEqual(self.c.delete(f"/api/{kind}/{rid}").status_code, 204, kind)

    def test_friendlink_requires_name_and_url(self):
        # 路由层特有校验:名称和链接都要填(其余 7 类无此校验)
        r = self.c.post("/api/friendlinks", json={"name": "只有名字"})
        self.assertEqual(r.status_code, 400)

    def test_songs_route_still_special(self):
        # songs 需要 QQ 链接解析:没认出歌曲应 400
        r = self.c.post("/api/songs", json={"title": "无链接"})
        self.assertEqual(r.status_code, 400)

    def test_questions_admin_flow(self):
        r = self.c.post("/api/questions", json={"body": "路由层问题"})
        self.assertEqual(r.status_code, 200)
        qid = r.get_json()["id"]
        r = self.c.post(f"/api/questions/{qid}/mod",
                        json={"action": "answer", "answer": "路由层回答"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("路由层问题", self.c.get("/api/questions").get_json()["questions"][0]["body"])


class TestRateLimits(WebTestBase):
    def test_question_throttle(self):
        c = appmod.app.test_client()
        appmod._Q_LAST.clear()
        r1 = c.post("/api/questions", json={"body": "第一条"})
        r2 = c.post("/api/questions", json={"body": "第二条"})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 429)
        appmod._Q_LAST.clear()

    def test_doodle_rejects_non_png(self):
        c = appmod.app.test_client()
        appmod._DOODLE_LAST.clear()
        r = c.post("/api/doodles", data={"file": (__import__("io").BytesIO(b"GIF89axxxx"),
                                                  "evil.gif")},
                   content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)
        appmod._DOODLE_LAST.clear()


if __name__ == "__main__":
    unittest.main()
