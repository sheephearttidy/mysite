/* 回归测试:同步 XHR 不能设 timeout(浏览器会抛 InvalidAccessError)
   用真实 Node 环境模拟浏览器规范行为,确认 holiday.js 不再设 timeout。
   这是「手动指定未生效」的真正根因。
*/
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'js', 'holiday.js');
const code = fs.readFileSync(SRC, 'utf8');

let P = 0, F = 0;
function ck(name, cond, extra) {
  if (cond) { console.log(`PASS  ${name}`); P++; }
  else { console.log(`FAIL  ${name}  ${extra || ''}`); F++; }
}

console.log('=== 静态检查:源码不应给同步 XHR 设 timeout ===');

// 找到 readConfig 函数体
const i = code.indexOf('function readConfig');
const j = code.indexOf('\n  }', i);
const body = code.slice(i, j);

ck('readConfig 里 xhr.open 是同步(false)',
   /xhr\.open\([^)]*,\s*false\s*\)/.test(body));
ck('readConfig 里没有 xhr.timeout 赋值',
   !/xhr\.timeout\s*=/.test(body),
   '发现 xhr.timeout 赋值 -> 浏览器会抛 InvalidAccessError');

console.log('\n=== 行为检查:模拟浏览器的同步 XHR 规范 ===');

// 严格模拟 Chrome:同步请求设 timeout 就抛异常
function makeStrictXHR(responseJson, throwOnTimeout) {
  function XHR() { this._timeoutSet = false; this._sync = false; }
  XHR.prototype.open = function (method, url, async) {
    this._sync = async === false;
  };
  Object.defineProperty(XHR.prototype, 'timeout', {
    set(v) {
      if (throwOnTimeout && this._sync) {
        const e = new Error("Failed to set the 'timeout' property on 'XMLHttpRequest': Timeouts cannot be set for synchronous requests made from a document.");
        e.name = 'InvalidAccessError';
        throw e;
      }
      this._timeoutSet = true;
    },
    get() { return 0; },
  });
  XHR.prototype.send = function () {
    this.status = 200;
    this.responseText = JSON.stringify(responseJson);
  };
  return XHR;
}

function run(apiResponse, strict) {
  const attrs = {};
  const document = {
    documentElement: {
      setAttribute(k, v) { attrs[k] = v; },
      getAttribute(k) { return attrs[k] || null; },
    },
  };
  const XHR = makeStrictXHR(apiResponse, strict);
  const fn = new Function('document', 'XMLHttpRequest', 'Date', code);
  // 固定日期到 6/15(无节日),这样只有后台配置能产生特效
  const RealDate = Date;
  const D = class extends RealDate {
    constructor(...a) { if (a.length === 0) super(2026, 5, 15, 12, 0, 0); else super(...a); }
  };
  fn(document, XHR, D);
  return attrs['data-holiday'] || '';
}

const CFG = { mode: 'manual', key: 'memorial', effects: '1' };

const strictResult = run(CFG, true);
ck('严格浏览器环境下 manual 仍生效', strictResult === 'memorial', `实际 ${JSON.stringify(strictResult)}`);

const laxResult = run(CFG, false);
ck('宽松环境下 manual 生效', laxResult === 'memorial', `实际 ${JSON.stringify(laxResult)}`);

console.log('\n=== 对照组:如果设了 timeout 会怎样 ===');
// 把代码强行加上 timeout,验证会失败(证明测试有效)
const brokenCode = code.replace(
  "xhr.open('GET', '/api/fx', false);",
  "xhr.open('GET', '/api/fx', false);\n      xhr.timeout = 1200;"
);
function runBroken(apiResponse) {
  const attrs = {};
  const document = {
    documentElement: {
      setAttribute(k, v) { attrs[k] = v; },
      getAttribute(k) { return attrs[k] || null; },
    },
  };
  const XHR = makeStrictXHR(apiResponse, true);
  const fn = new Function('document', 'XMLHttpRequest', 'Date', brokenCode);
  const RealDate = Date;
  const D = class extends RealDate {
    constructor(...a) { if (a.length === 0) super(2026, 5, 15, 12, 0, 0); else super(...a); }
  };
  fn(document, XHR, D);
  return attrs['data-holiday'] || '';
}
const brokenResult = runBroken(CFG);
ck('加回 timeout 后确实失效(证明测试能抓到)', brokenResult === '',
   `实际 ${JSON.stringify(brokenResult)}`);

console.log(`\n通过 ${P} 项,失败 ${F} 项`);
process.exit(F ? 1 : 0);
