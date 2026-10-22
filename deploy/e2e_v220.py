#!/usr/bin/env python3
"""v2.2 E2E 造数端(跑在测试服务器上):
  create        → 后台新增带唯一标记的荣誉,打印 JSON {stamp,id}
  clean <id>    → 删除该荣誉
  check <stamp> → 检查 /api/page/about 是否含该标记
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import http.cookiejar

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:5102"

_cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def api(path, method="GET", form=None, body=None):
    data = None
    r = urllib.request.Request(BASE + path, method=method)
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
    elif body is not None:
        r.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        resp = OPENER.open(r, data, timeout=10)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def login():
    svg = api("/admin/captcha.svg")[1]
    code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
    api("/admin/login", "POST", form={"password": "admin", "captcha": code})
    return any(c.name == "session" for c in _cj)


act = sys.argv[1] if len(sys.argv) > 1 else "create"

if act == "create":
    assert login(), "登录失败"
    stamp = "E2E" + str(int(time.time()))
    st, body = api("/api/honors", "POST", body={
        "emoji": "🧪", "year": stamp, "title": "端到端荣誉" + stamp,
        "desc": "验证完就删", "level": "national", "sort": 1})
    hid = json.loads(body).get("id")
    print(json.dumps({"ok": st == 201, "stamp": stamp, "id": hid}))
elif act == "clean":
    assert login(), "登录失败"
    hid = int(sys.argv[2])
    st, _ = api(f"/api/honors/{hid}", "DELETE")
    print(json.dumps({"ok": st == 204}))
elif act == "check":
    stamp = sys.argv[2]
    body = urllib.request.urlopen(BASE + "/api/page/about", timeout=10).read().decode()
    print(json.dumps({"present": stamp in body}))
