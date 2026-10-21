import sys, os
sys.path.insert(0, "/tmp/testapp")
import app as A
A.DB_PATH = "/tmp/testapp/data/test.db"
A.db.DB_PATH = A.DB_PATH
A.db.init_db(A.DB_PATH)
A.UPLOAD_DIR = "/tmp/testapp/uploads"
A.UPLOAD_URL = "/assets/uploads"
os.makedirs(A.UPLOAD_DIR, exist_ok=True)
A.app.config["SESSION_COOKIE_SECURE"] = False
A.app.config["TESTING"] = True

import captcha as CAP
_last = {"text": None}
_orig = CAP.make_captcha
def _patched(length=4):
    r = _orig(length)
    _last["text"] = r["text"]
    return r
CAP.make_captcha = _patched

@A.app.get("/__test/cap")
def _test_cap():
    return {"text": _last["text"]}

# 前台页面 + CSS + JS(测试用)
from flask import send_from_directory
@A.app.get("/")
def _home():
    return send_from_directory("/tmp/testapp/frontend", "index.html")

@A.app.get("/<name>.html")
def _page(name):
    return send_from_directory("/tmp/testapp/frontend", f"{name}.html")

@A.app.get("/css/<path:fn>")
def _css(fn):
    return send_from_directory("/tmp/testapp/frontend/css", fn)

@A.app.get("/js/<path:fn>")
def _js(fn):
    return send_from_directory("/tmp/testapp/frontend/js", fn)

A.app.run(host="127.0.0.1", port=5102, debug=False)
