import{r as u,j as a,H as st,V as ct,B as lt,K as ut,a as dt,i as mt,D as ht,h as ft,Q as pt,t as xt,v as gt,w as vt,y as wt,s as bt,R as Et}from"./BranchedMenu-Dgbp7iZ1.js";const ze=[{id:"index",path:"/",label:"首页"},{id:"about",path:"/about.html",label:"关于我"},{id:"skills",path:"/skills.html",label:"技能树"},{id:"works",path:"/works.html",label:"小破项目"},{id:"campus",path:"/campus.html",label:"校园日常"},{id:"gallery",path:"/gallery.html",label:"相册"},{id:"map",path:"/map.html",label:"来访地图"},{id:"contact",path:"/contact.html",label:"来找我玩"}];function Fe(){const t=window.location.pathname.replace(/\/+$/,"")||"/";if(t==="/")return"index";const i=ze.find(l=>l.path===t);if(i)return i.id;const n=/^\/([a-z-]+)\.html$/.exec(t);return n?n[1]:"404"}function yt(t){t!==window.location.pathname&&(window.history.pushState({},"",t),window.dispatchEvent(new PopStateEvent("popstate")))}const k={index:ut,about:ft,skills:pt,works:dt,campus:ht,gallery:mt,map:xt,contact:gt},Tt=[{label:"浏览",children:[{value:"index",label:"首页",icon:k.index},{value:"works",label:"小破项目",icon:k.works},{value:"gallery",label:"相册",icon:k.gallery},{value:"campus",label:"校园日常",icon:k.campus}]},{label:"了解我",children:[{value:"about",label:"关于我",icon:k.about},{value:"skills",label:"技能树",icon:k.skills},{value:"map",label:"来访地图",icon:k.map},{value:"contact",label:"来找我玩",icon:k.contact}]},{label:"更多",children:[{value:"docs",label:"API 文档",icon:vt},{value:"admin",label:"后台管理",icon:wt}]}],Ie={docs:"/docs/api.html",admin:"/admin/"};function jt({pageId:t}){const[i,n]=u.useState(!1),[l,c]=u.useState(()=>document.documentElement.getAttribute("data-theme")||"light");u.useEffect(()=>(document.body.style.overflow=i?"hidden":"",()=>{document.body.style.overflow=""}),[i]),u.useEffect(()=>{if(!i)return;const h=j=>{j.key==="Escape"&&n(!1)};return window.addEventListener("keydown",h),()=>window.removeEventListener("keydown",h)},[i]);const v=()=>{const h=l==="dark"?"light":"dark";c(h),document.documentElement.setAttribute("data-theme",h),document.documentElement.setAttribute("data-theme-source","manual");try{localStorage.setItem("theme",h)}catch{}},E=h=>{if(n(!1),Ie[h]){window.location.href=Ie[h];return}const j=ze.find(S=>S.id===h);j&&yt(j.path)},T={items:Tt,defaultOpen:[0,1],defaultActive:t,onSelect:E,width:210,rowHeight:36,indent:38,trunk:12,radius:9,lineWidth:1.5,fontSize:13.5,drawDuration:380,foldDuration:280};return a.jsxs(a.Fragment,{children:[a.jsx("header",{className:"nav",children:a.jsxs("div",{className:"container nav-inner",children:[a.jsxs("a",{href:"/",className:"logo",onClick:h=>{h.preventDefault(),E("index")},children:[a.jsx("span",{className:"dot"}),a.jsx("span",{"data-site":"site_name",children:"至尊杰的小窝"})]}),a.jsxs("div",{className:"nav-actions",children:[a.jsxs("button",{className:"nav-menu-btn","aria-label":"打开导航菜单","aria-expanded":i,onClick:()=>n(!0),children:[a.jsx(st,{icon:ct,size:20,strokeWidth:2.4}),a.jsx("span",{children:"菜单"})]}),a.jsxs("button",{className:"theme-toggle",onClick:v,"aria-label":"切换深色模式",title:"切换深色模式",children:[a.jsx("span",{className:"ti-sun",children:"☀️"}),a.jsx("span",{className:"ti-moon",children:"🌙"})]})]})]})}),i&&a.jsx("div",{className:"drawer-scrim",onClick:()=>n(!1),"aria-hidden":"true"}),a.jsxs("aside",{className:`drawer${i?" open":""}`,"aria-hidden":!i,"aria-label":"站点导航",children:[a.jsxs("div",{className:"drawer-head",children:[a.jsx("span",{className:"drawer-title",children:"导航"}),a.jsx("button",{className:"drawer-close",onClick:()=>n(!1),"aria-label":"关闭菜单",children:"✕"})]}),a.jsx("div",{className:"drawer-body",children:u.createElement(lt,{...T,key:t,color:"var(--ink, #2d2a32)",accentColor:"var(--pink, #ff6b9d)",lineColor:"rgba(0,0,0,.22)"})})]})]})}function Ct(){const[t,i]=u.useState(!1),[n,l]=u.useState(!1);return u.useEffect(()=>{const c=()=>i(window.scrollY>400);return window.addEventListener("scroll",c,{passive:!0}),c(),()=>window.removeEventListener("scroll",c)},[]),a.jsxs(a.Fragment,{children:[a.jsx("footer",{children:a.jsx("div",{className:"container",children:a.jsxs("p",{children:[a.jsx("span",{className:"sprout",children:"🌱"})," ","© 2026 至尊杰 · 燕京理工学院 · 纯手搓 + AI 协作 · learning and building"]})})}),a.jsx("button",{className:`back-top${t?" show":""}`,onClick:()=>window.scrollTo({top:0,behavior:"smooth"}),"aria-label":"返回顶部",children:"🚀"}),a.jsx("button",{className:"qr-fab",onClick:()=>l(!0),"aria-label":"微信二维码",children:"💬"}),n&&a.jsx("div",{className:"qr-modal",onClick:()=>l(!1),children:a.jsxs("div",{className:"qr-box",onClick:c=>c.stopPropagation(),children:[a.jsx("button",{className:"qr-close",onClick:()=>l(!1),"aria-label":"关闭",children:"✕"}),a.jsx("img",{src:"/assets/wechat-qr.jpg",alt:"微信二维码"}),a.jsx("p",{className:"hint",children:"微信扫一扫,加个好友吧 🎉"})]})})]})}const me=8,Xe=4,At=`#version 300 es
in vec2 aPosition;
void main() {
  gl_Position = vec4(aPosition, 0.0, 1.0);
}`,kt=`#version 300 es
precision highp float;
uniform vec2 uView;
uniform float uZoom;
uniform float uPhase;
uniform float uTwinkleClock;
uniform float uRings;
uniform vec3 uColors[8];
uniform int uColorCount;
uniform int uStreakCount;
uniform int uColumns;
uniform float uWidth;
uniform float uTail;
uniform float uTwinkle;
uniform float uHead;
uniform float uDepth;
uniform vec4 uMouse;
uniform vec3 uLens;
uniform float uLightMode;
uniform float uEncode;
out vec4 outColor;

const vec3 CAMERA = vec3(0.0, -0.8888889, -0.2222222);
const float TAU = 6.28318530718;
const float SPACING = 0.005;
const float REACH = 0.32;

uint scramble(uint x) {
  x ^= x >> 16;
  x *= 0x7feb352du;
  x ^= x >> 15;
  x *= 0x846ca68bu;
  x ^= x >> 16;
  return x;
}

float unit(uint x) {
  return float(x & 0xffffu) / 65535.0;
}

float stroke(float d, float w) {
  float s = max(0.75 * w, 0.55);
  return 0.75 * w / s * exp(-0.5 * d * d / (s * s));
}

float orb(float d, float r) {
  float s = max(0.6 * r, 0.7);
  float e = 0.6 * r / s;
  return e * e * exp(-0.5 * d * d / (s * s));
}

void main() {
  vec2 frag = gl_FragCoord.xy;
  vec2 screen = (2.0 * frag - uView) / uView.x;
  vec2 p = screen;
  mat2 warp = mat2(1.0);
  if (uLens.z > 0.0) {
    vec2 o = p - uLens.xy;
    float e = uLens.z * exp(-dot(o, o) / (REACH * REACH));
    p -= o * e;
    warp = mat2(1.0 - e) + outerProduct(o, o) * (2.0 * e / (REACH * REACH));
  }

  vec3 dir = vec3(p, uZoom);
  vec3 exits = (1.0 - CAMERA * sign(dir)) / max(abs(dir), vec3(1e-6));
  float u = min(exits.x, min(exits.y, exits.z));
  for (int i = 0; i < 5; i++) {
    vec3 h = CAMERA + u * dir;
    vec3 h2 = h * h;
    u -= (dot(h2, h2) - 1.0) / (4.0 * dot(dir, h2 * h));
  }
  vec3 hit = CAMERA + u * dir;
  vec3 normal = hit * hit * hit;
  float facing = dot(normal, dir);
  vec3 stepX = u * (vec3(1.0, 0.0, 0.0) - dir * (normal.x / facing));
  vec3 stepY = u * (vec3(0.0, 1.0, 0.0) - dir * (normal.y / facing));
  float ring = hit.y * hit.y + hit.z * hit.z;
  float theta = atan(hit.z, hit.y);
  mat2 jacobian = mat2(
    stepX.x,
    (hit.y * stepX.z - hit.z * stepX.y) / ring,
    stepY.x,
    (hit.y * stepY.z - hit.z * stepY.y) / ring
  ) * warp * (2.0 / uView.x);

  vec2 gradX = vec2(jacobian[0][0], jacobian[1][0]);
  vec2 gradTheta = vec2(jacobian[0][1], jacobian[1][1]);
  float scale = max(length(gradX), 1e-8);
  float det = max(abs(gradX.x * gradTheta.y - gradX.y * gradTheta.x), 1e-12);
  float along = scale / det;
  float skew = dot(gradX, gradTheta) / det;
  float spacing = SPACING / scale;
  float detail = smoothstep(1.6, 3.2, spacing);
  if (detail <= 0.0) {
    outColor = vec4(0.0, 0.0, 0.0, 1.0);
    return;
  }
  float halfWidth = min(uWidth / scale, 0.2 * spacing);
  float headRadius = min(2.0 * uWidth / scale, 0.35 * spacing);
  float headReach = 4.0 * max(0.6 * headRadius, 0.7);
  float edge = uColumns > 1 ? 1.0 : 0.5;
  float period = TAU / uRings;
  float fog = exp(-max(u * length(dir) - 0.6, 0.0) * 1.6 * uDepth);

  float boost = 1.0;
  if (uMouse.z > 0.0) {
    vec2 m = screen - uMouse.xy;
    boost += 2.0 * uMouse.z * exp(-dot(m, m) / max(uMouse.w * uMouse.w, 1e-4));
  }

  int count = max(uColorCount, 1);
  vec3 total = vec3(0.0);
  for (int layer = 0; layer < 16; layer++) {
    if (layer >= uStreakCount) break;
    float x = hit.x + float(layer) * SPACING / 8.0;
    float nearest = floor(x / SPACING + 0.5);
    float side = x >= nearest * SPACING ? 1.0 : -1.0;
    for (int k = 0; k < 2; k++) {
      if (k >= uColumns) break;
      float column = nearest + side * float(k);
      float across = (x - column * SPACING) / scale;
      uint seed = scramble(uint(int(column) + 65536) + uint(layer) * 0x9e3779b9u);
      uint next = scramble(seed);
      float hue = unit(seed >> 16);
      float delta = theta - uPhase * (1.0 + floor(unit(seed) * 16.0) / 16.0) - unit(next) * period;
      delta -= period * floor(delta / period + 0.5);
      float ahead = delta * along - across * skew;
      if (abs(ahead) > headReach && (delta > 0.0 || -delta * uTail > 3.2)) continue;
      float behind = max(-delta, 0.0);
      float fall = exp(-uTail * behind) * (1.0 - smoothstep(0.5, 0.95, behind / (0.5 * period)));
      fall *= 1.0 - smoothstep(1.2, 3.2, uTail * behind);
      float reach = length(vec2(across, ahead));
      float trail = stroke(ahead > 0.0 ? reach : abs(across), halfWidth * mix(0.4, 1.0, fall)) * fall;
      float glint = orb(reach, headRadius) * mix(3.0, 1.8, uLightMode);
      float weight = mix(1.5, 1.0 + sin(uTwinkleClock + 7.0 * hue + 4.0), uTwinkle);
      weight *= 1.0 - smoothstep(0.72 * edge, edge, abs(across) / spacing);
      vec3 color = uColors[min(int(hue * float(count)), count - 1)];
      vec3 hot = mix(color, vec3(1.0), uHead * (1.0 - uLightMode));
      total += (trail * color + glint * hot) * weight;
    }
  }

  outColor = vec4(total * fog * boost * detail * uEncode, 1.0);
}`,Mt=`#version 300 es
precision highp float;
uniform sampler2D uSource;
uniform vec2 uTarget;
uniform vec2 uTexel;
uniform float uLimit;
out vec4 outColor;

void main() {
  vec2 uv = gl_FragCoord.xy / uTarget;
  vec3 color = texture(uSource, uv - uTexel).rgb;
  color += texture(uSource, uv + uTexel).rgb;
  color += texture(uSource, uv + vec2(uTexel.x, -uTexel.y)).rgb;
  color += texture(uSource, uv + vec2(-uTexel.x, uTexel.y)).rgb;
  outColor = vec4(min(color * 0.25, vec3(uLimit)), 1.0);
}`,Nt=`#version 300 es
precision highp float;
uniform sampler2D uSource;
uniform vec2 uTarget;
uniform vec2 uStep;
out vec4 outColor;

void main() {
  vec2 uv = gl_FragCoord.xy / uTarget;
  vec3 color = texture(uSource, uv).rgb * 0.181862;
  color += (texture(uSource, uv + uStep * 1.423135).rgb + texture(uSource, uv - uStep * 1.423135).rgb) * 0.284316;
  color += (texture(uSource, uv + uStep * 3.326702).rgb + texture(uSource, uv - uStep * 3.326702).rgb) * 0.106598;
  color += (texture(uSource, uv + uStep * 5.242989).rgb + texture(uSource, uv - uStep * 5.242989).rgb) * 0.018156;
  outColor = vec4(color, 1.0);
}`,Rt=`#version 300 es
precision highp float;
uniform sampler2D uScene;
uniform sampler2D uBloom0;
uniform sampler2D uBloom1;
uniform sampler2D uBloom2;
uniform sampler2D uBloom3;
uniform vec2 uView;
uniform float uDecode;
uniform float uGlow;
uniform float uBloom;
uniform float uPresence;
uniform float uOpacity;
uniform float uFade;
uniform float uLightMode;
uniform vec3 uTopColor;
uniform float uTopGlow;
out vec4 outColor;

float smootherstep01(float t) {
  t = clamp(t, 0.0, 1.0);
  return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

void main() {
  vec2 uv = gl_FragCoord.xy / uView;
  vec3 light = texelFetch(uScene, ivec2(gl_FragCoord.xy), 0).rgb;
  if (uBloom > 0.0) {
    vec3 halo = texture(uBloom0, uv).rgb * 0.42;
    halo += texture(uBloom1, uv).rgb * 0.3;
    halo += texture(uBloom2, uv).rgb * 0.18;
    halo += texture(uBloom3, uv).rgb * 0.1;
    light += halo * uBloom * (uLightMode > 0.5 ? 0.2 : 1.0);
  }
  light *= uDecode * uGlow * uPresence;

  if (uLightMode < 0.5 && uTopGlow > 0.0) {
    float aspect = uView.x / uView.y;
    vec2 q = vec2((uv.x - 0.5) * aspect, 1.04 - uv.y);
    float spread = 0.34 * max(aspect, 0.75);
    float core = exp(-q.x * q.x / (spread * spread) - q.y * q.y / 0.06);
    float halo = exp(-q.x * q.x / (3.6 * spread * spread) - q.y * q.y / 0.18);
    light += uTopColor * uTopGlow * (core * 0.85 + halo * 0.3) * uPresence;
  }

  vec3 lit = max(light, 0.0);
  vec3 mapped = sqrt(1.0 - exp(-1.3 * lit * lit / (lit + 0.025)));
  float peak = max(mapped.r, max(mapped.g, mapped.b));

  float mask = uOpacity;
  float edge = uFade * 0.5;
  if (edge > 0.0) {
    mask *= smootherstep01(uv.x / edge) * smootherstep01((1.0 - uv.x) / edge);
    mask *= smootherstep01(uv.y / edge) * smootherstep01((1.0 - uv.y) / edge);
  }
  float grain = (fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715)))) - 0.5) / 255.0;

  if (uLightMode > 0.5) {
    float coverage = clamp(smoothstep(0.0, 0.5, peak) * mask * 0.94 + grain, 0.0, 1.0);
    vec3 chroma = sqrt(clamp(lit / max(max(lit.r, max(lit.g, lit.b)), 1e-6), 0.0, 1.0));
    chroma = pow(chroma, vec3(1.35));
    chroma /= max(max(chroma.r, max(chroma.g, chroma.b)), 1e-4);
    float saturation = 1.0 - min(chroma.r, min(chroma.g, chroma.b));
    chroma = mix(vec3(0.3), chroma, smoothstep(0.08, 0.35, saturation));
    outColor = vec4(chroma * coverage, coverage);
  } else {
    vec3 color = clamp(mapped + grain, 0.0, 1.0) * mask;
    outColor = vec4(color, max(color.r, max(color.g, color.b)));
  }
}`,Lt=2.6,Pt=9,he=Math.PI*2,z=(t,i,n)=>Math.min(n,Math.max(i,t)),Ge=(t,i,n)=>{const l=t.createShader(i);return l?(t.shaderSource(l,n),t.compileShader(l),t.getShaderParameter(l,t.COMPILE_STATUS)?l:(t.deleteShader(l),null)):null},ee=(t,i)=>{const n=Ge(t,t.VERTEX_SHADER,At),l=Ge(t,t.FRAGMENT_SHADER,i),c=t.createProgram();if(!n||!l||!c)return null;if(t.attachShader(c,n),t.attachShader(c,l),t.bindAttribLocation(c,0,"aPosition"),t.linkProgram(c),t.deleteShader(n),t.deleteShader(l),!t.getProgramParameter(c,t.LINK_STATUS))return t.deleteProgram(c),null;const v={},E=t.getProgramParameter(c,t.ACTIVE_UNIFORMS);for(let T=0;T<E;T++){const h=t.getActiveUniform(c,T);h&&(v[h.name.replace(/\[0\]$/,"")]=t.getUniformLocation(c,h.name))}return{program:c,uniforms:v}},St=({colors:t=["#ffffff"],backgroundColor:i="#94a3b8",speed:n=.3,streakCount:l=2,streakWidth:c=.8,streakLength:v=1,glow:E=1,density:T=.6,twinkle:h=.3,zoom:j=3,backgroundGlow:S=.1,headGlow:Oe=.6,depth:Ue=.5,bloom:Be=.35,opacity:We=1,mouseInteraction:Ve=!0,mouseStrength:He=.4,mouseRadius:Ye=.45,mouseDampening:qe=.15,lens:$e=.5,holdToWarp:Ke=!0,intro:Qe=!0,fade:Ze=0,lightMode:Je=!1,mixBlendMode:xe,paused:et=!1,dpr:tt,className:ge="",style:at})=>{const ve=u.useRef(null),we=u.useRef(null),O=u.useRef(null),M=u.useRef(null),[ot,rt]=u.useState(0);return M.current={colors:(Array.isArray(t)&&t.length?t:["#ffffff"]).slice(0,me).map(String),backgroundColor:String(i),speed:n,streakCount:Math.round(z(l,1,16)),streakWidth:Math.max(.05,c),streakLength:Math.max(.05,v),glow:Math.max(0,E),density:T,twinkle:z(h,0,1),zoom:Math.max(.1,j),backgroundGlow:Math.max(0,S),headGlow:z(Oe,0,1),depth:Math.max(0,Ue),bloom:Math.max(0,Be),opacity:z(We,0,1),mouseInteraction:Ve,mouseStrength:Math.max(0,He),mouseRadius:Math.max(.01,Ye),mouseDampening:Math.max(0,qe),lens:z($e,0,1),holdToWarp:Ke,intro:Qe,fade:z(Ze,0,1),lightMode:Je,paused:et,dpr:tt},u.useEffect(()=>{var _e;const w=ve.current,x=we.current,e=x==null?void 0:x.getContext("webgl2",{alpha:!0,premultipliedAlpha:!0,antialias:!1,depth:!1,stencil:!1,powerPreference:"high-performance"});if(!w||!x||!e)return;const be=!!e.getExtension("EXT_color_buffer_float"),te=ee(e,kt),ae=ee(e,Mt),q=ee(e,Nt),oe=ee(e,Rt);if(!te||!ae||!q||!oe)return;const Ee=o=>{o.preventDefault()},ye=()=>rt(o=>o+1);x.addEventListener("webglcontextlost",Ee),x.addEventListener("webglcontextrestored",ye);const Te=e.createBuffer(),re=e.createVertexArray();e.bindVertexArray(re),e.bindBuffer(e.ARRAY_BUFFER,Te),e.bufferData(e.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),e.STATIC_DRAW),e.enableVertexAttribArray(0),e.vertexAttribPointer(0,2,e.FLOAT,!1,0,0);const nt=be?e.RGBA16F:e.RGBA8,ne=be?1:.25,ie=()=>({texture:null,framebuffer:e.createFramebuffer(),width:0,height:0}),U=ie(),$=Array.from({length:Xe},()=>[ie(),ie()]),se=(o,r,d)=>{o.texture&&o.width===r&&o.height===d||(o.texture&&e.deleteTexture(o.texture),o.texture=e.createTexture(),o.width=r,o.height=d,e.bindTexture(e.TEXTURE_2D,o.texture),e.texStorage2D(e.TEXTURE_2D,1,nt,r,d),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MIN_FILTER,e.LINEAR),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MAG_FILTER,e.LINEAR),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_S,e.CLAMP_TO_EDGE),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_T,e.CLAMP_TO_EDGE),e.bindFramebuffer(e.FRAMEBUFFER,o.framebuffer),e.framebufferTexture2D(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,o.texture,0))},B=(o,r)=>(e.bindFramebuffer(e.FRAMEBUFFER,o?o.framebuffer:null),e.viewport(0,0,o?o.width:x.width,o?o.height:x.height),e.useProgram(r.program),r.uniforms),_=(o,r)=>{e.activeTexture(e.TEXTURE0+o),e.bindTexture(e.TEXTURE_2D,r)},D=document.createElement("canvas").getContext("2d",{willReadFrequently:!0}),ce=new Map,it=o=>{if(ce.has(o))return ce.get(o);let r=[1,1,1];if(D){D.clearRect(0,0,1,1),D.fillStyle="#ffffff",D.fillStyle=o,D.fillRect(0,0,1,1);const[d,b,V]=D.getImageData(0,0,1,1).data;r=[d/255,b/255,V/255]}return ce.set(o,r),r},je=o=>it(o).map(r=>r*r),W=((_e=window.matchMedia)==null?void 0:_e.call(window,"(prefers-reduced-motion: reduce)").matches)??!1,le=new Float32Array(me*3),g={x:0,y:0,inside:!1,held:!1},s={travel:0,intro:M.current.intro&&!W?0:1,mouseX:0,mouseY:0,lensX:0,lensY:0,touch:0,warp:0};let N=0,F=0,K=!0;const ue=()=>{const o=M.current,r=x.width,d=x.height,b=Math.max(1,w.clientWidth),V=Math.max(1,w.clientHeight);e.bindVertexArray(re),se(U,r,d),$.forEach((m,p)=>{const A=Math.max(1,Math.round(b/2**(p+1))),L=Math.max(1,Math.round(V/2**(p+1)));se(m[0],A,L),se(m[1],A,L)});const H=s.intro,Z=Math.min(1,H*2.2),I=1+5*Math.pow(1-H,2)+2.5*s.warp,R=Math.max(1,Math.floor(he*Math.max(o.density,.05)+.5)),X=he/R,Y=9+s.travel,G=o.colors.map(je);le.fill(0);for(let m=0;m<me;m++)le.set(G[Math.min(m,G.length-1)],m*3);const J=m=>(2*m-r)/r,De=m=>(2*m-d)/r,f=B(U,te);if(e.uniform2f(f.uView,r,d),e.uniform1f(f.uZoom,o.zoom),e.uniform1f(f.uPhase,Y%(16*X)),e.uniform1f(f.uTwinkleClock,Y%he),e.uniform1f(f.uRings,R),e.uniform3fv(f.uColors,le),e.uniform1i(f.uColorCount,G.length),e.uniform1i(f.uStreakCount,o.streakCount),e.uniform1i(f.uColumns,o.streakWidth>1?2:1),e.uniform1f(f.uWidth,5e-4*o.streakWidth),e.uniform1f(f.uTail,19/(o.streakLength*I)),e.uniform1f(f.uTwinkle,o.twinkle),e.uniform1f(f.uHead,o.headGlow),e.uniform1f(f.uDepth,o.depth),e.uniform4f(f.uMouse,J(s.mouseX),De(s.mouseY),o.mouseInteraction?o.mouseStrength*s.touch:0,o.mouseRadius),e.uniform3f(f.uLens,J(s.lensX),De(s.lensY),o.mouseInteraction?.5*o.lens*s.touch:0),e.uniform1f(f.uLightMode,o.lightMode?1:0),e.uniform1f(f.uEncode,ne),e.drawArrays(e.TRIANGLES,0,3),o.bloom>0){let m=U;$.forEach(([p,A])=>{const L=B(p,ae);_(0,m.texture),e.uniform1i(L.uSource,0),e.uniform2f(L.uTarget,p.width,p.height),e.uniform2f(L.uTexel,1/m.width,1/m.height),e.uniform1f(L.uLimit,4*ne),e.drawArrays(e.TRIANGLES,0,3);let P=B(A,q);_(0,p.texture),e.uniform1i(P.uSource,0),e.uniform2f(P.uTarget,A.width,A.height),e.uniform2f(P.uStep,1/p.width,0),e.drawArrays(e.TRIANGLES,0,3),P=B(p,q),_(0,A.texture),e.uniform1i(P.uSource,0),e.uniform2f(P.uTarget,p.width,p.height),e.uniform2f(P.uStep,0,1/A.height),e.drawArrays(e.TRIANGLES,0,3),m=p})}const y=B(null,oe);_(0,U.texture),e.uniform1i(y.uScene,0),$.forEach(([m],p)=>{_(p+1,m.texture),e.uniform1i(y[`uBloom${p}`],p+1)}),e.uniform2f(y.uView,r,d),e.uniform1f(y.uDecode,1/ne),e.uniform1f(y.uGlow,o.glow),e.uniform1f(y.uBloom,o.bloom),e.uniform1f(y.uPresence,Z),e.uniform1f(y.uOpacity,o.opacity),e.uniform1f(y.uFade,o.fade),e.uniform1f(y.uLightMode,o.lightMode?1:0),e.uniform3fv(y.uTopColor,je(o.backgroundColor)),e.uniform1f(y.uTopGlow,o.backgroundGlow),e.drawArrays(e.TRIANGLES,0,3);for(let m=Xe;m>=0;m--)_(m,null)},Ce=o=>{if(N=0,!K||document.hidden)return;const r=M.current,d=F?Math.min(.05,(o-F)/1e3):1/60;F=o,!r.intro||W?s.intro=1:s.intro<1&&(s.intro=Math.min(1,s.intro+d/Lt));const b=r.holdToWarp&&g.held&&g.inside&&!W;s.warp+=((b?1:0)-s.warp)*(1-Math.exp(-d*(b?2.2:1.6)));const V=Pt*Math.pow(1-s.intro,2)+6*s.warp,H=!r.paused&&!W;H&&(s.travel+=d*.1*r.speed*(1+V));const Z=x.width/Math.max(1,w.clientWidth),I=g.x*Z,R=(w.clientHeight-g.y)*Z,X=r.mouseInteraction&&g.inside&&!W;X&&s.touch<.01&&(s.mouseX=I,s.mouseY=R,s.lensX=I,s.lensY=R);const Y=r.mouseDampening>0?1-Math.exp(-d/r.mouseDampening):1;s.mouseX+=(I-s.mouseX)*Y,s.mouseY+=(R-s.mouseY)*Y;const G=1-Math.exp(-d*6);s.lensX+=(I-s.lensX)*G,s.lensY+=(R-s.lensY)*G,s.touch+=((X?1:0)-s.touch)*(1-Math.exp(-d*(X?4:2))),ue();const J=s.intro<1||s.warp>.001||Math.abs((X?1:0)-s.touch)>.002;H&&r.speed!==0||J?N=requestAnimationFrame(Ce):F=0},C=()=>{!N&&K&&!document.hidden&&(N=requestAnimationFrame(Ce))},de=()=>{const o=M.current,r=Math.max(1,w.clientWidth),d=Math.max(1,w.clientHeight),b=Math.min(o.dpr||window.devicePixelRatio||1,2);x.width=Math.max(1,Math.round(r*b)),x.height=Math.max(1,Math.round(d*b)),N||ue(),C()},Ae=o=>{const r=w.getBoundingClientRect(),d=o.clientX-r.left,b=o.clientY-r.top;return{x:d,y:b,inside:d>=0&&b>=0&&d<=r.width&&b<=r.height}},ke=o=>{const r=Ae(o);g.x=r.x,g.y=r.y,g.inside=r.inside,C()},Me=o=>{const r=Ae(o);r.inside&&(g.x=r.x,g.y=r.y,g.inside=!0,g.held=!0,C())},Q=()=>{g.held=!1,C()},Ne=()=>{g.inside=!1,g.held=!1,C()},Re=()=>{F=0,C()},Le=new ResizeObserver(de);Le.observe(w);const Pe=new IntersectionObserver(o=>{K=o.some(r=>r.isIntersecting),K&&(F=0,C())});Pe.observe(w),window.addEventListener("pointermove",ke,{passive:!0}),window.addEventListener("pointerdown",Me,{passive:!0}),window.addEventListener("pointerup",Q,{passive:!0}),window.addEventListener("pointercancel",Q,{passive:!0}),document.documentElement.addEventListener("pointerleave",Ne),document.addEventListener("visibilitychange",Re),de();let Se=M.current.dpr;return O.current=()=>{const o=M.current;if(o.dpr!==Se){Se=o.dpr,de();return}N||ue(),C()},()=>{var o;cancelAnimationFrame(N),O.current=null,x.removeEventListener("webglcontextlost",Ee),x.removeEventListener("webglcontextrestored",ye),Le.disconnect(),Pe.disconnect(),window.removeEventListener("pointermove",ke),window.removeEventListener("pointerdown",Me),window.removeEventListener("pointerup",Q),window.removeEventListener("pointercancel",Q),document.documentElement.removeEventListener("pointerleave",Ne),document.removeEventListener("visibilitychange",Re),[U,...$.flat()].forEach(r=>{r.texture&&e.deleteTexture(r.texture),e.deleteFramebuffer(r.framebuffer)}),[te,ae,q,oe].forEach(r=>e.deleteProgram(r.program)),e.deleteBuffer(Te),e.deleteVertexArray(re),e.isContextLost()||(o=e.getExtension("WEBGL_lose_context"))==null||o.loseContext()}},[ot]),u.useEffect(()=>{var w;(w=O.current)==null||w.call(O)}),a.jsx("div",{ref:ve,className:`lightfall-container${ge?` ${ge}`:""}`,style:{...xe?{mixBlendMode:xe}:null,...at},children:a.jsx("canvas",{ref:we,className:"lightfall-canvas","aria-hidden":"true"})})};function fe(t,i,n){if(!n)return;let l=document.head.querySelector(`meta[${t}="${i}"]`);l||(l=document.createElement("meta"),l.setAttribute(t,i),document.head.appendChild(l)),l.setAttribute("content",n)}function _t(t,i){if(!i)return;let n=document.head.querySelector(`link[rel="${t}"]`);n||(n=document.createElement("link"),n.setAttribute("rel",t),document.head.appendChild(n)),n.setAttribute("href",i)}function Dt({title:t,description:i,canonical:n,ogTitle:l,ogDescription:c}){t&&(document.title=t),fe("name","description",i),fe("property","og:title",l||t),fe("property","og:description",c||i),_t("canonical",n)}function Ft({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"首页 · 至尊杰的小窝",description:"首页",canonical:"https://imyxj.xyz/"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"首页"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function It({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"关于我 · 至尊杰的小窝",description:"关于我",canonical:"https://imyxj.xyz/about.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"关于我"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function Xt({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"技能树 · 至尊杰的小窝",description:"技能树",canonical:"https://imyxj.xyz/skills.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"技能树"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function Gt({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"小破项目 · 至尊杰的小窝",description:"小破项目",canonical:"https://imyxj.xyz/works.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"小破项目"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function zt({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"校园日常 · 至尊杰的小窝",description:"校园日常",canonical:"https://imyxj.xyz/campus.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"校园日常"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function Ot({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"相册 · 至尊杰的小窝",description:"相册",canonical:"https://imyxj.xyz/gallery.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"相册"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function Ut({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"来访地图 · 至尊杰的小窝",description:"来访地图",canonical:"https://imyxj.xyz/map.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"来访地图"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function Bt({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"来找我玩 · 至尊杰的小窝",description:"来找我玩",canonical:"https://imyxj.xyz/contact.html"})},[t]),a.jsx("section",{className:"sec-cream page-head",children:a.jsxs("div",{className:"container",children:[a.jsx("h2",{children:"来找我玩"}),a.jsx("p",{className:"hint",children:"内容迁移中…"})]})})}function Wt({onSeo:t}){return u.useEffect(()=>{t==null||t({title:"页面走丢了 · 至尊杰的小窝",description:"这个页面走丢了。"})},[t]),a.jsx("section",{className:"sec-cream page-head err-page",children:a.jsx("div",{className:"container",children:a.jsxs("div",{className:"err-card",children:[a.jsxs("div",{className:"err-code","aria-hidden":"true",children:[a.jsx("span",{className:"err-digit",children:"4"}),a.jsx("span",{className:"err-zero",children:"🍩"}),a.jsx("span",{className:"err-digit",children:"4"})]}),a.jsxs("h2",{children:["这个页面走丢了",a.jsx("span",{className:"wave-hand",children:" 🧭"})]}),a.jsxs("p",{className:"err-text",children:["你要找的页面好像不在这儿 —— 可能是链接打错了,",a.jsx("br",{}),"也可能它被我搬走或者删掉了。"]}),a.jsxs("div",{className:"err-actions",children:[a.jsx("a",{className:"btn",href:"/",children:"🏠 回首页"}),a.jsx("a",{className:"btn btn-teal",href:"/works.html",children:"🛠️ 看项目"}),a.jsx("a",{className:"btn btn-yellow",href:"/contact.html",children:"📬 来找我"})]})]})})})}const Vt={index:Ft,about:It,skills:Xt,works:Gt,campus:zt,gallery:Ot,map:Ut,contact:Bt};function Ht(){const[t,i]=u.useState(!1),[n,l]=u.useState(!1);return u.useEffect(()=>{var T,h;const c=window.matchMedia("(prefers-reduced-motion: reduce)"),v=window.matchMedia("(max-width: 720px)"),E=()=>{i(c.matches),l(v.matches)};return E(),(T=c.addEventListener)==null||T.call(c,"change",E),(h=v.addEventListener)==null||h.call(v,"change",E),()=>{var j,S;(j=c.removeEventListener)==null||j.call(c,"change",E),(S=v.removeEventListener)==null||S.call(v,"change",E)}},[]),a.jsx("div",{className:"site-backdrop","aria-hidden":"true",children:a.jsx(St,{colors:["#ffd93d","#ff6b9d","#7ec8b8","#ffffff"],backgroundColor:"#1b1922",speed:t?.12:.3,streakCount:n?6:12,streakWidth:.8,streakLength:1.1,density:.6,twinkle:.3,glow:.9,backgroundGlow:.14,headGlow:.6,depth:.55,bloom:n?.25:.4,zoom:3,opacity:.55,mouseInteraction:!t&&!n,mouseStrength:.35,mouseRadius:.45,lens:.45,holdToWarp:!t,intro:!0,fade:.35,paused:t})})}function Yt({initialPage:t}){const[i,n]=u.useState(t||Fe());u.useEffect(()=>{const c=()=>n(Fe());return window.addEventListener("popstate",c),()=>window.removeEventListener("popstate",c)},[]),u.useEffect(()=>{window.scrollTo(0,0)},[i]);const l=Vt[i]||Wt;return a.jsxs(a.Fragment,{children:[a.jsx(Ht,{}),a.jsxs("div",{className:"site-content",children:[a.jsx(jt,{pageId:i}),a.jsx("main",{id:"page-main",children:a.jsx(l,{onSeo:Dt})}),a.jsx(Ct,{})]})]})}const pe=document.getElementById("react-root");pe&&bt(pe).render(a.jsx(Et.StrictMode,{children:a.jsx(Yt,{initialPage:pe.dataset.page||"index"})}));
