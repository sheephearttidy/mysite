/* 用 Node 模拟浏览器,直接执行真实的 js/holiday.js
   验证「后台配置 -> data-holiday」的完整映射。
   不联网:mock XMLHttpRequest 返回指定 JSON。
*/
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'js', 'holiday.js');
const code = fs.readFileSync(SRC, 'utf8');

let P = 0, F = 0;
function ck(name, got, want) {
  if (got === want) { console.log(`PASS  ${name} -> ${JSON.stringify(got)}`); P++; }
  else { console.log(`FAIL  ${name}: got ${JSON.stringify(got)} want ${JSON.stringify(want)}`); F++; }
}

// 造一个假浏览器环境,跑 holiday.js,返回 html 上的属性
function run(apiResponse, fixedDate) {
  const attrs = {};
  const document = {
    documentElement: {
      setAttribute(k, v) { attrs[k] = v; },
      getAttribute(k) { return attrs[k] || null; },
    },
  };

  // mock XMLHttpRequest:按 apiResponse 返回(传 null 表示网络失败)
  function XMLHttpRequest() {}
  XMLHttpRequest.prototype.open = function () {};
  XMLHttpRequest.prototype.send = function () {
    if (apiResponse === null) { this.status = 0; this.responseText = ''; return; }
    this.status = 200;
    this.responseText = JSON.stringify(apiResponse);
  };

  // 固定「今天」,便于测日期自动检测
  const RealDate = Date;
  let DateMock = RealDate;
  if (fixedDate) {
    const [y, m, d] = fixedDate;
    DateMock = class extends RealDate {
      constructor(...a) { if (a.length === 0) super(y, m - 1, d, 12, 0, 0); else super(...a); }
      static now() { return new RealDate(y, m - 1, d, 12, 0, 0).getTime(); }
    };
  }

  const fn = new Function('document', 'XMLHttpRequest', 'Date', code);
  fn(document, XMLHttpRequest, DateMock);
  return attrs['data-holiday'] || '';
}

console.log('=== 手动指定(mode=manual) ===');
const KEYS = ['national-day', 'valentine', 'memorial', 'new-year',
              'christmas', 'labor', 'children', 'teacher'];
for (const k of KEYS) {
  ck(`manual/${k}`, run({ mode: 'manual', key: k, effects: '1' }, [2026, 6, 15]), k);
}

console.log('\n=== 全关 ===');
ck('mode=off', run({ mode: 'off', key: '', effects: '1' }, [2026, 6, 15]), '');
ck('effects=0(manual 也应全关)',
   run({ mode: 'manual', key: 'christmas', effects: '0' }, [2026, 6, 15]), '');
ck('effects=0(auto 也应全关)',
   run({ mode: 'auto', key: '', effects: '0' }, [2026, 10, 1]), '');

console.log('\n=== 自动检测(mode=auto) ===');
const AUTOCASES = [
  [[2026, 10, 1], 'national-day', '10-01 国庆'],
  [[2026, 10, 7], 'national-day', '10-07 国庆末'],
  [[2026, 10, 8], '', '10-08 无节'],
  [[2026, 2, 14], 'valentine', '02-14 情人节'],
  [[2026, 12, 13], 'memorial', '12-13 公祭日'],
  [[2026, 12, 24], 'christmas', '12-24 平安夜'],
  [[2026, 12, 25], 'christmas', '12-25 圣诞'],
  [[2026, 1, 1], 'new-year', '01-01 元旦'],
  [[2026, 5, 1], 'labor', '05-01 劳动节'],
  [[2026, 6, 1], 'children', '06-01 儿童节'],
  [[2026, 9, 10], 'teacher', '09-10 教师节'],
  [[2026, 6, 15], '', '06-15 无节'],
];
for (const [dt, want, label] of AUTOCASES) {
  ck(`auto ${label}`, run({ mode: 'auto', key: '', effects: '1' }, dt), want);
}

console.log('\n=== 后台读不到(网络失败)-> 回退自动 ===');
ck('网络失败 + 10-01 应国庆',
   run(null, [2026, 10, 1]), 'national-day');
ck('网络失败 + 06-15 应无',
   run(null, [2026, 6, 15]), '');

console.log('\n=== 非法 key 应视为无 ===');
ck('manual/不存在的节日',
   run({ mode: 'manual', key: 'not-exist', effects: '1' }, [2026, 6, 15]), '');

console.log('\n=== 手动优先于日期 ===');
ck('10-01 手动指定圣诞',
   run({ mode: 'manual', key: 'christmas', effects: '1' }, [2026, 10, 1]), 'christmas');

console.log(`\n通过 ${P} 项,失败 ${F} 项`);
process.exit(F ? 1 : 0);
