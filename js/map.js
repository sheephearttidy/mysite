/* ============================================================
   来访地图:拉 /api/map 城市数据,把星星钉在 SVG 世界地图上
   ============================================================ */

(function () {
  const SVG_W = 1000, SVG_H = 520;
  // v2.4.1 底图换成真实世界轮廓后,纬度范围裁到 84°N ~ 58°S,
  // 避免等距圆柱投影把南极洲拉成一条横带。星星必须用同一套公式,
  // 否则会和陆地错位。
  const LAT_TOP = 78, LAT_BOT = -58;

  // 等距圆柱投影:经纬度 -> SVG 坐标(与 map.html 底图完全一致)
  const project = (lon, lat) => [
    ((lon + 180) / 360) * SVG_W,
    ((LAT_TOP - lat) / (LAT_TOP - LAT_BOT)) * SVG_H
  ];

  // 五角星 path(中心在 0,0,半径 r)
  const starPath = r => {
    const pts = [];
    for (let i = 0; i < 10; i++) {
      const rad = i % 2 === 0 ? r : r * 0.42;
      const a = -Math.PI / 2 + i * Math.PI / 5;
      pts.push(`${(rad * Math.cos(a)).toFixed(1)},${(rad * Math.sin(a)).toFixed(1)}`);
    }
    return `M${pts.join(' L')} Z`;
  };

  // 城市名 -> 经纬度(容错:去后缀/别名)
  const lookup = name => {
    if (!name) return null;
    let n = String(name).trim();
    if (CITY_LL[n]) return CITY_LL[n];
    // "江苏 南京" -> "南京"
    const last = n.split(' ').pop();
    if (CITY_LL[last]) return CITY_LL[last];
    // 带"市/县/区"后缀
    const strip = last.replace(/市|县|区|州|盟|地区|自治州/g, '');
    if (CITY_LL[strip]) return CITY_LL[strip];
    return null;
  };

  const svg = document.getElementById('worldMap');
  const stars = document.getElementById('mapStars');
  const list = document.getElementById('cityList');
  const total = document.getElementById('mapTotal');
  if (!svg || !stars || !list) return;

  // 星星颜色轮换(莫兰迪可爱风)
  const COLORS = ['#ff6b9d', '#ffb84d', '#7ec8b8', '#9aa7ff', '#f2a0c8', '#8fd460', '#ffd93d'];

  const render = cities => {
    stars.innerHTML = '';
    list.innerHTML = '';
    let placed = 0;

    // v2.4.1 修:以前「查不到坐标的城市」会被重复列两次——
    // 先在正常循环里插一条,末尾又汇总插一条(用户看到「河北 承德」出现两遍)。
    // 现在只在一次循环里处理:查不到坐标的照样列出,但标 ❓ 并注明未定位。
    cities.forEach((c, i) => {
      const ll = lookup(c.city);
      const color = COLORS[i % COLORS.length];
      const li = document.createElement('li');
      li.className = 'city-item' + (ll ? '' : ' city-unknown');
      li.innerHTML = `<span class="city-star" style="color:${ll ? color : ''}">${ll ? '★' : '❓'}</span>
        <span class="city-name">${esc(c.city)}</span>
        <span class="city-count">${ll ? c.count + ' 次' : '没定位到,待补充'}</span>`;
      list.appendChild(li);

      if (ll) {
        placed++;
        const [x, y] = project(ll[0], ll[1]);
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('transform', `translate(${x},${y})`);
        g.innerHTML = `
          <path d="${starPath(11 + Math.min(c.count, 8) * 0.8)}" fill="${color}"
                stroke="#fff" stroke-width="1.5" stroke-linejoin="round"
                class="map-star" />
          <title>${esc(c.city)} · ${c.count} 次</title>`;
        stars.appendChild(g);
      }
    });

    total.textContent = placed;

    if (!cities.length) {
      list.innerHTML = '<li class="city-empty">还没有星星落地,快来做第一颗 ✨</li>';
      total.textContent = '0';
    }
  };

  fetch('/api/map')
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(d => render(Array.isArray(d.cities) ? d.cities : []))
    .catch(() => {
      list.innerHTML = '<li class="city-empty">地图暂时没连上,星星在打盹 😴</li>';
    });
})();
