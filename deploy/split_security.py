#!/usr/bin/env python3
"""把 admin.html 的单一面板 security 拆成 6 个安全子面板 + 新增 fx 前台特效面板"""
import io
import re

PATH = r"D:\Agent_Work_Base\my-portfolio\admin\templates\admin.html"

with io.open(PATH, encoding="utf-8") as f:
    html = f.read()

start = html.find("      <!-- 安全设置 -->")
end_marker = "      </section>\n\n    </div>\n  </main>"
end = html.find(end_marker)
if start < 0 or end < 0:
    raise SystemExit(f"锚点未找到 start={start} end={end}")
end += len("      </section>")

OLD = html[start:end]

NEW = """      <!-- 前台特效 -->
      <section class="panel" id="panel-fx">
        <div class="sec-head">
          <h2>🎉 前台特效</h2>
          <span class="hint">节日装饰、粒子动效由这里控制,关掉就完全不出现</span>
        </div>

        <div class="item">
          <h3>🎊 节日装饰模式</h3>
          <p class="hint" style="margin-top:4px">
            「按日期自动」= 到了节日当天自动出现;「手动指定」= 只显示你选的那个节日(适合提前预览);
            「全部关闭」= 任何节日都不出现
          </p>
          <div class="secform" style="margin-top:12px">
            <div class="sf-row">
              <label class="sf-label">
                节日装饰
                <span class="sf-note">关掉后全站不显示任何节日特效</span>
              </label>
              <label class="switch">
                <input type="checkbox" id="fxHolidayOn" />
                <span class="slider"></span>
              </label>
            </div>
            <div class="sf-row">
              <label class="sf-label">
                模式
                <span class="sf-note">自动跟随日期 / 手动指定 / 关闭</span>
              </label>
              <select class="sf-input" id="fxMode">
                <option value="auto">按日期自动</option>
                <option value="manual">手动指定节日</option>
                <option value="off">全部关闭</option>
              </select>
            </div>
            <div class="sf-row">
              <label class="sf-label">
                指定节日
                <span class="sf-note">仅在「手动指定」模式下生效</span>
              </label>
              <select class="sf-input" id="fxKey">
                <option value="">— 不指定 —</option>
                <option value="national-day">🇨🇳 国庆节(红旗)</option>
                <option value="valentine">💗 情人节(爱心)</option>
                <option value="memorial">🕯️ 国家公祭日(全站黑白)</option>
                <option value="new-year">🎆 元旦(彩带)</option>
                <option value="christmas">🎄 圣诞节(雪花)</option>
                <option value="labor">🧹 劳动节(彩带)</option>
                <option value="children">✈️ 儿童节(纸飞机)</option>
                <option value="teacher">⭐ 教师节(星星)</option>
              </select>
            </div>
            <div class="sf-row">
              <label class="sf-label">
                前台动效总开关
                <span class="sf-note">关掉后所有粒子/飘落动效都不加载,页面更省电</span>
              </label>
              <label class="switch">
                <input type="checkbox" id="fxEffects" />
                <span class="slider"></span>
              </label>
            </div>
            <div class="ops" style="margin-top:14px">
              <button class="op add" onclick="saveFxSettings()">💾 保存特效设置</button>
              <button class="op edit" onclick="previewFx()">👀 当前生效预览</button>
            </div>
            <div id="fxPreview" style="margin-top:12px"></div>
          </div>
        </div>

        <div class="item" style="margin-top:16px">
          <h3>📖 说明</h3>
          <ul class="seclist">
            <li>前台每个页面在 <code>&lt;head&gt;</code> 里同步读一次 <code>/api/fx</code>(超时 1.2 秒)</li>
            <li>后台挂掉或响应慢 → 自动回退到「按日期自动」,不会白屏或卡顿</li>
            <li>「公祭日」一旦启用会强制全站黑白,优先级高于其他节日</li>
            <li>改完刷新前台页面即可看到效果(不需要重启服务)</li>
          </ul>
        </div>
      </section>

      <!-- 安全中心 · 后台密码 -->
      <section class="panel" id="panel-sec-pass">
        <div class="sec-head">
          <h2>🔑 后台密码</h2>
          <span class="hint">密码强度与更换</span>
        </div>
        <div class="sec-grid">
          <div class="sec-card ok" id="secCardCaptcha">
            <div class="sc-ic">🤖</div>
            <div class="sc-body"><div class="sc-t">登录验证码</div><div class="sc-v" id="scCaptchaVal">–</div></div>
          </div>
          <div class="sec-card" id="secCardFails">
            <div class="sc-ic">🚨</div>
            <div class="sc-body"><div class="sc-t">24 小时失败</div><div class="sc-v" id="scFailsVal">–</div></div>
          </div>
          <div class="sec-card" id="secCardBlocked">
            <div class="sc-ic">⛔</div>
            <div class="sc-body"><div class="sc-t">封锁中的 IP</div><div class="sc-v" id="scBlockedVal">–</div></div>
          </div>
          <div class="sec-card" id="secCardSessions">
            <div class="sc-ic">💻</div>
            <div class="sc-body"><div class="sc-t">活跃会话</div><div class="sc-v" id="scSessionsVal">–</div></div>
          </div>
        </div>
        <div class="item" style="margin-top:16px">
          <h3>🔑 修改密码</h3>
          <p class="hint" style="margin-top:6px">
            密码以 PBKDF2(120k 迭代)哈希存在数据库里,明文不落盘。建议定期更换。
          </p>
          <div class="ops">
            <button class="op edit" onclick="openPassModal()">🔑 修改密码</button>
            <button class="op del" onclick="revokeAllSessions()">🚪 踢掉其他所有会话</button>
          </div>
        </div>
      </section>

      <!-- 安全中心 · 登录防护 -->
      <section class="panel" id="panel-sec-login">
        <div class="sec-head">
          <h2>🛡️ 登录防护</h2>
          <span class="hint">验证码、失败封锁、会话时长,全部手动开关</span>
        </div>
        <div class="item">
          <div class="secform">
            <div class="sf-row">
              <label class="sf-label">
                登录验证码
                <span class="sf-note">开启后每次登录都要输图形验证码</span>
              </label>
              <label class="switch">
                <input type="checkbox" id="setCaptcha" />
                <span class="slider"></span>
              </label>
            </div>
            <div class="sf-row">
              <label class="sf-label">验证码位数<span class="sf-note">3~6 位,越长越难认</span></label>
              <input class="sf-input" type="number" id="setCaptchaLen" min="3" max="6" />
            </div>
            <div class="sf-row">
              <label class="sf-label">失败几次后封锁<span class="sf-note">超过这个次数就临时禁止登录</span></label>
              <input class="sf-input" type="number" id="setFailThreshold" min="1" max="50" />
            </div>
            <div class="sf-row">
              <label class="sf-label">封锁时长(分钟)<span class="sf-note">期间该 IP 无法登录</span></label>
              <input class="sf-input" type="number" id="setBlockMinutes" min="1" max="1440" />
            </div>
            <div class="sf-row">
              <label class="sf-label">空闲自动登出(分钟)<span class="sf-note">0 = 不自动登出</span></label>
              <input class="sf-input" type="number" id="setIdleMinutes" min="0" max="1440" />
            </div>
            <div class="sf-row">
              <label class="sf-label">会话有效期(小时)<span class="sf-note">超过后必须重新登录</span></label>
              <input class="sf-input" type="number" id="setSessionHours" min="1" max="720" />
            </div>
            <div class="sf-row">
              <label class="sf-label">审计日志保留条数<span class="sf-note">超出后只显示最新的</span></label>
              <input class="sf-input" type="number" id="setAuditKeep" min="50" max="5000" />
            </div>
            <div class="ops" style="margin-top:14px">
              <button class="op add" onclick="saveSecSettings()">💾 保存设置</button>
              <button class="op del" onclick="loadSecOverview()">↻ 重新读取</button>
            </div>
          </div>
        </div>
      </section>

      <!-- 安全中心 · 封锁名单 -->
      <section class="panel" id="panel-sec-blocked">
        <div class="sec-head">
          <h2>⛔ 封锁名单</h2>
          <span class="hint">失败次数超限被临时封锁的 IP</span>
        </div>
        <div class="item">
          <div id="secBlockedList"></div>
          <div class="ops" style="margin-top:12px">
            <button class="op edit" onclick="loadSecOverview()">↻ 刷新</button>
          </div>
        </div>
      </section>

      <!-- 安全中心 · 登录会话 -->
      <section class="panel" id="panel-sec-sessions">
        <div class="sec-head">
          <h2>💻 登录会话</h2>
          <span class="hint">发现陌生会话直接踢下线</span>
        </div>
        <div class="item">
          <p class="hint">改了密码后建议把其他会话全踢掉,强制所有设备重新登录。</p>
          <div id="secSessionList"></div>
          <div class="ops" style="margin-top:12px">
            <button class="op edit" onclick="loadSecOverview()">↻ 刷新</button>
            <button class="op del" onclick="revokeAllSessions()">🚪 踢掉其他所有会话</button>
          </div>
        </div>
      </section>

      <!-- 安全中心 · 审计日志 -->
      <section class="panel" id="panel-sec-audit">
        <div class="sec-head">
          <h2>📜 审计日志</h2>
          <span class="hint">登录、改密码、改设置、上传、备份等敏感操作留痕</span>
        </div>
        <div class="item">
          <div id="secAuditList"></div>
          <div class="ops" style="margin-top:12px">
            <button class="op edit" onclick="loadAudit()">↻ 刷新</button>
            <button class="op del" onclick="clearAudit()">🗑️ 清空日志</button>
          </div>
        </div>
      </section>

      <!-- 安全中心 · 防护状态 -->
      <section class="panel" id="panel-sec-status">
        <div class="sec-head">
          <h2>🛡️ 防护状态</h2>
          <span class="hint">当前全站安全措施一览</span>
        </div>
        <div class="item">
          <ul class="seclist">
            <li>✅ 全站 HTTPS + HSTS(强制跳转)</li>
            <li>✅ Session Cookie 带 Secure / HttpOnly / SameSite=Lax</li>
            <li>✅ 登录验证码(图形,3 分钟过期,一次性)</li>
            <li>✅ 登录限速:nginx 10 次/分钟 + 应用层失败封锁</li>
            <li>✅ 失败记录落库,重启不丢,支持手动解封</li>
            <li>✅ 登录成功重置 session(防会话固定)</li>
            <li>✅ 会话可远程踢下线 + 空闲自动登出</li>
            <li>✅ 敏感操作全程审计留痕</li>
            <li>✅ 后台以专用用户 <code>mysite</code> 运行(非 root)</li>
            <li>✅ 数据库与源码不在 webroot 可访问路径</li>
            <li>✅ SSH 仅公钥登录</li>
            <li>✅ 上传校验真实文件头,防改扩展名 webshell</li>
            <li>✅ JSON 请求体 64KB 上限,防内存放大</li>
          </ul>
        </div>
      </section>"""

html = html[:start] + NEW + html[end:]

with io.open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)

print("替换完成,新长度", len(html))
print("面板数:", html.count('class="panel"'))
