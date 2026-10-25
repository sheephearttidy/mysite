#!/usr/bin/env python3
"""v2.2.0 功能自测:三新类型 API CRUD + 前台 page 接口 + admin 数据注入"""
import json
import http.cookiejar
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:5102"
PWD = "admin"
PASS = FAIL = 0


def ck(name, cond):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def req(path, method="GET", body=None):
    r = urllib.request.Request(BASE + path, method=method)
    data = None
    if body is not None:
        r.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        resp = OPENER.open(r, data, timeout=10)
        return resp.status, resp.read().decode(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), e.headers


# 带 cookie jar 的 opener:302 重定向也不丢登录态
_cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def get_captcha():
    """取一张验证码并解析答案;答案摘要绑定在 session 里,必须走同一 CookieJar"""
    st, svg, _ = req("/admin/captcha.svg")
    code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
    return code


def login_cookie():
    """登录一次(表单提交),CookieJar 自动持有 session;返回登录是否成功"""
    code = get_captcha()
    data = urllib.parse.urlencode(
        {"password": PWD, "captcha": code}).encode()
    r = urllib.request.Request(BASE + "/admin/login", data=data, method="POST")
    try:
        resp = OPENER.open(r, timeout=10)
        # 成功 → 302 跟进后落在 /admin 页
        return resp.url.rstrip("/").endswith("/admin") and \
            any(c.name == "session" for c in _cj)
    except urllib.error.HTTPError:
        return False


# ---------- 登录 ----------
ck("后台登录成功", login_cookie())

# ---------- admin 页注入新数据 ----------
st, html, _ = req("/admin")
ck("admin 页 200", st == 200)
ck("admin 注入 honors", '"honors":' in html)
ck("admin 注入 notes", '"notes":' in html)
ck("admin 注入 friendlinks", '"friendlinks":' in html)
ck("admin 侧边栏有荣誉墙", 'data-panel="honors"' in html)
ck("admin 侧边栏有随手记", 'data-panel="notes"' in html)
ck("admin 侧边栏有友情链接", 'data-panel="friendlinks"' in html)
ck("admin 面板 HTML honors", 'id="panel-honors"' in html)
ck("admin 面板 HTML notes", 'id="panel-notes"' in html)
ck("admin 面板 HTML friendlinks", 'id="panel-friendlinks"' in html)

# ---------- 前台 page 接口 ----------
st, body, _ = req("/api/page/about")
d = json.loads(body)
ck("page/about 带 honors", st == 200 and isinstance(d.get("honors"), list)
   and len(d["honors"]) >= 1)
st, body, _ = req("/api/page/campus")
d = json.loads(body)
ck("page/campus 带 notes", st == 200 and isinstance(d.get("notes"), list)
   and len(d["notes"]) >= 1)
st, body, _ = req("/api/page/contact")
d = json.loads(body)
ck("page/contact 带 friendlinks", st == 200 and isinstance(d.get("friendlinks"), list)
   and len(d["friendlinks"]) >= 1)
ck("旧 page/map 已移除", req("/api/page/map")[0] == 404)

# ---------- CRUD:荣誉 ----------
st, body, _ = req("/api/honors", "POST",
                  {"emoji": "🥇", "year": "2026", "title": "测试奖项",
                   "desc": "自测用", "level": "national", "sort": 99})
h = json.loads(body)
hid = h.get("id")
ck("新增荣誉 201", st == 201 and hid)
st, body, _ = req(f"/api/honors/{hid}", "PUT",
                  {"title": "测试奖项改", "level": "school"})
ck("改荣誉 OK", st == 200 and json.loads(body)["title"] == "测试奖项改"
   and json.loads(body)["level"] == "school")
ck("非法 level 拒绝", json.loads(req(f"/api/honors/{hid}", "PUT",
   {"level": "hacker"})[1])["level"] == "school")
st, body, _ = req(f"/api/honors/{hid}", "DELETE", None)
ck("删荣誉 204", st == 204)

# ---------- CRUD:随手记 ----------
st, body, _ = req("/api/notes", "POST",
                  {"emoji": "🧪", "text": "自测随手记"})
n = json.loads(body)
nid = n.get("id")
ck("新增随手记 201(自动 ts)", st == 201 and nid and n.get("ts", 0) > 0)
st, body, _ = req(f"/api/notes/{nid}", "PUT", {"mood": "pink"})
ck("改随手记颜色", st == 200 and json.loads(body)["mood"] == "pink")
st, body, _ = req(f"/api/notes/{nid}", "DELETE", None)
ck("删随手记 204", st == 204)

# ---------- CRUD:友链 ----------
st, body, _ = req("/api/friendlinks", "POST",
                  {"name": "测试站", "url": "https://example.com"})
f = json.loads(body)
fid = f.get("id")
ck("新增友链 201", st == 201 and fid)
ck("友链缺 url 400", req("/api/friendlinks", "POST",
   {"name": "坏数据"})[0] == 400)
st, body, _ = req(f"/api/friendlinks/{fid}", "PUT", {"desc": "测试简介"})
ck("改友链 OK", st == 200 and json.loads(body)["desc"] == "测试简介")
st, body, _ = req(f"/api/friendlinks/{fid}", "DELETE", None)
ck("删友链 204", st == 204)

# ---------- 未登录防护(用干净 opener,不带 session) ----------
_anon = urllib.request.build_opener()
try:
    _anon.open(urllib.request.Request(
        BASE + "/api/honors", method="POST",
        data=json.dumps({"title": "x"}).encode(),
        headers={"Content-Type": "application/json"}), timeout=10)
    st_anon = 200
except urllib.error.HTTPError as e:
    st_anon = e.code
ck("未登录 CRUD 拒绝", st_anon in (302, 401, 403))

# ---------- 导出含新表 ----------
st, body, _ = req("/api/export")
d = json.loads(body)
ck("export 含 honors/notes/friendlinks",
   all(k in d for k in ("honors", "notes", "friendlinks")) and d.get("version") == 2)

print(f"\n通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
