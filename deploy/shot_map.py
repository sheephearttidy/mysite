#!/usr/bin/env python3
"""本地生成地图测试页(注入 mock 城市数据) + headless Chrome 截图
验证:星星是否钉在城市位置、城市列表是否渲染
"""
import os
import subprocess

ROOT = r"D:\Agent_Work_Base\my-portfolio"
OUT = r"D:\Agent_Work_Base\_shots"

# 读 map.html
with open(os.path.join(ROOT, "map.html"), encoding="utf-8") as f:
    html = f.read()

# 注入:拦截 fetch,返回 mock 城市数据
MOCK = """
<script>
  window.__fetch = window.fetch;
  window.fetch = function (url) {
    if (String(url).includes('/api/map')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ cities: [
          { city: '北京', count: 12 }, { city: '江苏 南京', count: 8 },
          { city: '上海', count: 6 }, { city: '广东 深圳', count: 5 },
          { city: '四川 成都', count: 3 }, { city: '浙江 杭州', count: 4 },
          { city: '湖南 长沙', count: 2 }, { city: '新疆 乌鲁木齐', count: 1 }
        ]})
      });
    }
    return window.__fetch.apply(this, arguments);
  };
</script>
"""
html = html.replace('<script src="js/theme.js"></script>', MOCK + '\n<script src="js/theme.js"></script>', 1)

out = os.path.join(ROOT, "_shot_map_mock.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

url = "http://127.0.0.1:8777/_shot_map_mock.html"
png = os.path.join(OUT, "map_mock.png")
cmd = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
       "--headless", "--disable-gpu", "--hide-scrollbars",
       "--virtual-time-budget=4000",
       "--window-size=1280,1000", f"--screenshot={png}", url]
r = subprocess.run(cmd, capture_output=True, timeout=60)
print(f"map_mock: {'OK' if os.path.exists(png) else 'FAIL'} ({os.path.getsize(png) if os.path.exists(png) else 0} bytes)")
print("done")
