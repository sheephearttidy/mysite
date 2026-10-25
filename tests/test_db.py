# -*- coding: utf-8 -*-
"""数据层行为基线(v3.2.0 CRUD 工厂化的安全网)。

在临时 SQLite 库上钉死每类内容 CRUD 的现有语义:
默认值 / 部分字段更新合并 / 枚举回退差异(honors/notes 有校验,其余直存)
/ 数字强转 / 删除返回值,以及导入导出、那年今日、提问涂鸦审核流。

重构工厂前后跑同一套,任何语义漂移立即红。
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


class TempDbMixin:
    """每类测试一个全新临时库;init_db 会灌 SEED 演示数据,清空内容表保证确定性"""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="mysite-test-")
        self.dbpath = os.path.join(self._tmp, "t.db")
        db.DB_PATH = self.dbpath
        db.init_db(self.dbpath)
        with db.get_db() as c:
            for t in ("skills", "timeline", "stats", "works", "profile", "honors",
                      "notes", "friendlinks", "songs", "questions", "doodles",
                      "messages", "message_threads", "photos", "notices",
                      "countdowns"):
                c.execute(f"DELETE FROM {t}")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)


class TestSkillsCrud(TempDbMixin, unittest.TestCase):
    KIND = "skills"

    def test_insert_defaults(self):
        row = db.insert_skill({})
        self.assertEqual(row["name"], "")
        self.assertEqual(row["percent"], 50)
        self.assertEqual(row["category"], "serious")
        self.assertEqual(row["color"], "teal")
        self.assertEqual(row["sort"], 99)

    def test_insert_explicit(self):
        row = db.insert_skill({"name": "Python", "percent": 75, "category": "passive",
                               "color": "blue", "sort": 3, "note": "n"})
        self.assertEqual(row["percent"], 75)
        self.assertEqual(row["category"], "passive")

    def test_insert_raw_enum_passthrough(self):
        # 语义差异钉死:skills 的 category/color 不做枚举校验,原样落库
        row = db.insert_skill({"category": "乱写的", "color": "啥"})
        self.assertEqual(row["category"], "乱写的")
        self.assertEqual(row["color"], "啥")

    def test_update_partial_merge(self):
        row = db.insert_skill({"name": "A", "percent": 10, "note": "old"})
        merged = db.update_skill(row["id"], {"note": "new"})
        self.assertEqual(merged["name"], "A")       # 未提供的字段保留
        self.assertEqual(merged["note"], "new")
        self.assertEqual(merged["percent"], 10)

    def test_update_missing_returns_none(self):
        self.assertIsNone(db.update_skill(99999, {"name": "x"}))

    def test_delete(self):
        row = db.insert_skill({})
        self.assertTrue(db.delete_skill(row["id"]))
        self.assertFalse(db.delete_skill(row["id"]))

    def test_get_order(self):
        db.insert_skill({"category": "passive", "sort": 1})
        db.insert_skill({"category": "serious", "sort": 9})
        db.insert_skill({"category": "serious", "sort": 2})
        cats = [s["category"] for s in db.get_skills()]
        # ORDER BY category,sort,id:category 按字典序(passive < serious)
        self.assertEqual(cats, ["passive", "serious", "serious"])


class TestTimelineCrud(TempDbMixin, unittest.TestCase):
    def test_insert_defaults(self):
        row = db.insert_timeline({})
        self.assertEqual(row["emoji"], "🚀")
        self.assertEqual(row["time_label"], "")
        self.assertEqual(row["sort"], 99)

    def test_update_and_delete(self):
        row = db.insert_timeline({"title": "开学"})
        self.assertEqual(db.update_timeline(row["id"], {"title": "军训"})["title"], "军训")
        self.assertIsNone(db.update_timeline(424242, {}))
        self.assertTrue(db.delete_timeline(row["id"]))


class TestStatsCrud(TempDbMixin, unittest.TestCase):
    def test_insert_defaults(self):
        row = db.insert_stat({})
        self.assertEqual(row["emoji"], "😄")
        self.assertEqual(row["number"], 0)
        self.assertEqual(row["unit"], "")

    def test_number_int_coercion(self):
        row = db.insert_stat({"number": "42"})     # 字符串数字被 int() 收敛
        self.assertEqual(row["number"], 42)


class TestWorksCrud(TempDbMixin, unittest.TestCase):
    def test_insert_defaults(self):
        row = db.insert_work({})
        self.assertEqual(row["emoji"], "🛠️")
        self.assertEqual(row["cover"], "pink")
        self.assertEqual(row["pill"], "进行中")
        self.assertEqual(row["link"], "")

    def test_update_partial(self):
        row = db.insert_work({"title": "站", "desc": "d"})
        merged = db.update_work(row["id"], {"pill": "完结"})
        self.assertEqual(merged["title"], "站")
        self.assertEqual(merged["pill"], "完结")


class TestProfileCrud(TempDbMixin, unittest.TestCase):
    def test_insert_defaults(self):
        row = db.insert_profile({})
        self.assertEqual(row["kind"], "info")
        self.assertEqual(row["emoji"], "")

    def test_get_order_kind_first(self):
        db.insert_profile({"kind": "info", "sort": 1})
        db.insert_profile({"kind": "about", "sort": 9})
        kinds = [p["kind"] for p in db.get_profile()]
        self.assertEqual(kinds, ["about", "info"])  # ORDER BY kind,sort,id


class TestHonorsCrud(TempDbMixin, unittest.TestCase):
    def test_insert_level_enum_fallback(self):
        # 语义差异钉死:honors.level 非法值回退 school(skills 可不回退!)
        row = db.insert_honor({"level": "宇宙级"})
        self.assertEqual(row["level"], "school")

    def test_update_level_enum(self):
        row = db.insert_honor({"level": "national"})
        self.assertEqual(db.update_honor(row["id"], {"level": "provincial"})["level"],
                         "provincial")
        # update 里非法枚举被忽略,保留原值(与 insert 的"回退默认"语义不同,钉死)
        self.assertEqual(db.update_honor(row["id"], {"level": "x"})["level"],
                         "provincial")

    def test_update_preserves_other_fields(self):
        row = db.insert_honor({"title": "一等奖", "year": "2026"})
        merged = db.update_honor(row["id"], {"year": "2025"})
        self.assertEqual(merged["title"], "一等奖")
        self.assertEqual(merged["year"], "2025")


class TestNotesCrud(TempDbMixin, unittest.TestCase):
    def test_insert_mood_enum_fallback(self):
        row = db.insert_note({"mood": "荧光绿"})
        self.assertEqual(row["mood"], "teal")

    def test_insert_ts_defaults_to_now(self):
        before = int(time.time())
        row = db.insert_note({})
        self.assertTrue(before <= row["ts"] <= int(time.time()) + 2)

    def test_get_order_newest_first(self):
        older = db.insert_note({"text": "旧", "ts": 1000})
        newer = db.insert_note({"text": "新", "ts": 2000})
        self.assertEqual(db.get_notes()[0]["id"], newer["id"])
        self.assertEqual(db.get_notes()[-1]["id"], older["id"])


class TestFriendlinksCrud(TempDbMixin, unittest.TestCase):
    def test_insert_defaults(self):
        row = db.insert_friendlink({})
        self.assertEqual(row["emoji"], "🔗")
        self.assertEqual(row["name"], "")
        self.assertEqual(row["url"], "")

    def test_update_delete(self):
        row = db.insert_friendlink({"name": "友站"})
        self.assertEqual(db.update_friendlink(row["id"], {"url": "https://x"})["url"],
                         "https://x")
        self.assertTrue(db.delete_friendlink(row["id"]))


class TestSongsCrud(TempDbMixin, unittest.TestCase):
    def test_crud(self):
        row = db.insert_song({"title": "歌", "song_id": "123"})
        self.assertEqual(row["song_id"], "123")
        merged = db.update_song(row["id"], {"artist": "人"})
        self.assertEqual(merged["artist"], "人")
        self.assertEqual(merged["title"], "歌")
        self.assertTrue(db.delete_song(row["id"]))


class TestHelpers(TempDbMixin, unittest.TestCase):
    def test_as_text(self):
        self.assertEqual(db._as_text("a"), "a")
        self.assertEqual(db._as_text(None, "d"), "d")
        self.assertEqual(db._as_text(12), "12")
        self.assertEqual(db._as_text(1.5), "1.5")
        self.assertEqual(db._as_text(True), "")            # bool 不当数字
        self.assertEqual(db._as_text({"x": 1}, "d"), "d")  # 对象回默认
        self.assertEqual(db._as_text([1], "d"), "d")

    def test_clean_import_value_num_range(self):
        self.assertEqual(db._clean_import_value("t", "percent", 99999), 100)
        self.assertEqual(db._clean_import_value("t", "percent", -5), 0)
        self.assertEqual(db._clean_import_value("t", "sort", "abc"), 0)

    def test_clean_import_value_enum(self):
        self.assertEqual(db._clean_import_value("t", "category", "hacker"), "serious")
        self.assertEqual(db._clean_import_value("t", "category", "passive"), "passive")

    def test_clean_import_value_text_limit(self):
        self.assertEqual(len(db._clean_import_value("t", "note", "x" * 999)), 200)

    def test_password_roundtrip(self):
        h = db.hash_password("s3cret-密码")
        self.assertTrue(db.verify_password("s3cret-密码", h))
        self.assertFalse(db.verify_password("wrong", h))
        self.assertFalse(db.verify_password("s3cret-密码", "garbage"))


class TestModerationFlows(TempDbMixin, unittest.TestCase):
    def test_questions_lifecycle(self):
        r = db.add_question("站用什么搭的?", ip="1.1.1.1")
        self.assertTrue(r["ok"])
        self.assertEqual(db.list_questions_public(), [])     # 未答不展示
        a = db.answer_question(r["id"], "Flask 手搓")
        self.assertTrue(a["ok"])
        self.assertEqual(db.list_questions_public()[0]["body"], "站用什么搭的?")
        self.assertEqual(db.question_counts()["shown"], 1)
        self.assertTrue(db.set_question_shown(r["id"], 2))
        self.assertEqual(db.list_questions_public(), [])
        self.assertTrue(db.delete_question(r["id"]))
        self.assertFalse(db.delete_question(r["id"]))

    def test_question_empty_body_rejected(self):
        self.assertFalse(db.add_question("   ").get("ok"))

    def test_doodles_lifecycle(self):
        r = db.add_doodle("doodle-20261025-abc.png", ip="1.1.1.1", width=640, height=400)
        self.assertTrue(r["ok"])
        self.assertEqual(db.list_doodles_public(), [])       # 待审不展示
        self.assertTrue(db.set_doodle_shown(r["id"], 1))
        self.assertEqual(db.list_doodles_public()[0]["width"], 640)
        d = db.delete_doodle(r["id"])
        self.assertTrue(d["ok"] and d["file"].endswith(".png"))

    def test_doodle_bad_filename_rejected(self):
        self.assertFalse(db.add_doodle("../evil.png").get("ok"))
        self.assertFalse(db.add_doodle("").get("ok"))

    def test_messages_and_threads(self):
        r = db.add_message("访客", "你好", "pink", ip="2.2.2.2")
        self.assertTrue(r["ok"]) and self.assertIn("token", r)
        self.assertEqual(db.list_messages_public(), [])      # 待审不展示
        self.assertTrue(db.set_message_shown(r["id"], 1))
        pub = db.list_messages_public()[0]
        self.assertEqual(pub["name"], "访客")
        self.assertIn("token", r)                            # 导出/追问凭证

    def test_alert_snapshot_counts(self):
        db.add_question("q1", ip="1.1.1.1")
        db.add_doodle("doodle-x.png", ip="1.1.1.1")
        snap = db.alert_snapshot()
        self.assertEqual(snap["pending_questions"], 1)
        self.assertEqual(snap["pending_doodles"], 1)
        self.assertEqual(snap["latest_question"]["body"], "q1")


class TestOnThisDay(TempDbMixin, unittest.TestCase):
    def test_empty_db(self):
        self.assertEqual(db.get_onthisday(), {"notes": [], "photos": []})

    def test_last_year_today_hit(self):
        now = time.localtime()
        last_year = int(time.mktime((now.tm_year - 1, now.tm_mon, now.tm_mday,
                                     12, 0, 0, 0, 0, -1)))
        db.insert_note({"text": "去年今日", "ts": last_year})
        hit = db.get_onthisday()["notes"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["text"], "去年今日")

    def test_this_year_excluded(self):
        db.insert_note({"text": "今天写的", "ts": int(time.time())})
        self.assertEqual(db.get_onthisday()["notes"], [])


class TestImportExport(TempDbMixin, unittest.TestCase):
    def test_roundtrip_merge(self):
        a = db.insert_honor({"title": "原奖项", "year": "2026"})
        exp_honors = db.get_honors()
        db.delete_honor(a["id"])
        counts = db.import_payload({"honors": exp_honors}, replace=False)
        self.assertEqual(counts.get("honors"), 1)
        self.assertEqual(db.get_honors()[0]["title"], "原奖项")

    def test_questions_in_backup(self):
        db.add_question("要备份的", ip="1.1.1.1")
        exp = db.get_questions_for_export()
        self.assertEqual(len(exp), 1)
        counts = db.import_payload(
            {"questions": [{"body": "导入问题", "ts": 1790000000, "shown": 1,
                            "answer": "答", "answered_ts": 1790000100}]},
            replace=False)
        self.assertEqual(counts.get("questions"), 1)
        self.assertEqual(db.question_counts()["total"], 2)


if __name__ == "__main__":
    unittest.main()
