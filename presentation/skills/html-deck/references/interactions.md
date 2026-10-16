# 微互動模式庫

這份是從實際做過的互動簡報中整理出來、可重複使用的微互動配方。每個配方都寫了：**它在敘事上的用途**、**怎麼依主題改編**、**核心程式碼**（全部用 template 的 tokens：`--accent`、`--accent-rgb`、`--line`、`--line-2`、`--surface`、`--bg-1`、`--text`、`--text-2`、`--muted`、`--ease-out`）。

使用原則：配方是素材庫，不是清單。依互動強度挑選，並把每個效果「換成這份簡報的主題」。

## 1. 互動強度刻度

開工時和 design read 一起決定強度；使用者要求「更多互動」「更有設計感」就往上調。

| 強度 | 背景層 | 封面／章節 | 內容頁 | 適合 |
| --- | --- | --- | --- | --- |
| 1 靜態 | 無 | 無動畫 | 只有換頁淡入 | 書面寄送、正式報告 |
| 2 克制 | 游標聚光 | 標題底線畫出 | 卡片依序出現、截圖可放大 | 多數商務、研究、教學 |
| 3 互動 | 聚光 | 章節頁數字環 | 每段落 1–2 個可操作元件（切換、步驟檢視器、模擬器） | 技術分享、設計分享、提案 |
| 4 沉浸 | 主題隱喻粒子層 | 封面 3D 傾斜＋漂浮籌碼、章節鏤空大字＋軌道 | 每個關鍵頁都有一個互動，結論連鎖亮起 | 設計分享、作品集、發表 |
| 5 展演 | 粒子＋游標連線＋事件脈衝 | 全部 | 加上內嵌 Demo 全螢幕層 | 發表會、Demo Day、展場循環播放 |

**選擇規則（任何強度都適用）**
- 整份簡報只有**一套**背景系統，所有頁面共用，不要每頁換一種特效。
- 每頁最多**一個主要互動**（要觀眾或講者操作的那個）；其他動態只能是陪襯。
- 互動要能**由講者操作**：點擊、方向鍵或自動播放；不能依賴觀眾自己滑鼠移過去才看得到重點。
- 所有互動在 `prefers-reduced-motion` 下有靜態版本；所有持續動畫在非作用頁暫停。
- 強度 4–5 的裝飾（光球、持續旋轉、脈動）要更淡、更慢，並確認瞇眼看時焦點仍是內容。

## 2. 主題隱喻：讓特效「屬於」這份簡報

背景與裝飾互動要從主題找隱喻，而不是套通用特效：

| 主題 | 背景隱喻 | 章節／封面裝飾 |
| --- | --- | --- |
| 數據、追蹤、分析、網路 | 節點網路，偶爾有節點發出脈衝（事件被記錄） | 數字外圍的資料環 |
| 成長、轉換、行銷 | 由下往上緩慢上升的粒子 | 上升曲線畫出 |
| 流程、物流、工作流 | 沿路徑流動的光點 | 軌道上的步驟圖示 |
| 時間、歷史、路線圖 | 緩慢橫移的時間刻度 | 時間軸線畫出 |
| 自然、永續、健康 | 緩慢漂移的有機形狀 | 柔和的同心波紋 |
| 安全、基礎設施 | 靜態網格＋偶爾掃描線 | 層層外框 |
| 創意、品牌、設計 | 游標附近的色彩聚光、可拖曳的形狀 | 大字鏤空填色 |
| 教育、知識 | 連結起來的概念點 | 書頁或卡片翻開 |

找不到合理隱喻就退回強度 2（只用聚光），不要硬加。

## 3. 背景層

### 3.1 游標聚光（強度 2+）
用途：讓畫面有生命感但不干擾。改編：顏色用強調色、半徑依舞台大小。
```css
.spot{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(520px 420px at var(--sx,70%) var(--sy,30%),rgba(var(--accent-rgb),.08),transparent 70%)}
```
```js
stage.addEventListener("mousemove", e => {
  const r = stage.getBoundingClientRect();
  stage.style.setProperty("--sx", ((e.clientX - r.left) / r.width * 100) + "%");
  stage.style.setProperty("--sy", ((e.clientY - r.top) / r.height * 100) + "%");
});
```

### 3.2 主題粒子網路（強度 4–5）
用途：把主題隱喻變成背景（例如「事件在網路中被記錄」）。改編：粒子數 40–70、連線距離、顏色、脈衝頻率、游標行為（排斥或吸引）都依主題調整；換成上升粒子、流動光點時只改更新規則。
```js
const cv = document.getElementById("bgfx"), ctx = cv.getContext("2d");
const DPR = Math.min(2, devicePixelRatio || 1); cv.width = 1600 * DPR; cv.height = 900 * DPR; ctx.scale(DPR, DPR);
const ACC = getComputedStyle(document.documentElement).getPropertyValue("--accent-rgb").trim();
const mouse = { x: -999, y: -999 };
const P = Array.from({ length: 58 }, () => ({ x: Math.random()*1600, y: Math.random()*900, vx: (Math.random()-.5)*.25, vy: (Math.random()-.5)*.25, r: Math.random()*1.6+.6 }));
const pings = [];
function tick(){
  ctx.clearRect(0, 0, 1600, 900);
  for (const p of P){                                   // 移動＋邊界反彈＋游標排斥
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0 || p.x > 1600) p.vx *= -1; if (p.y < 0 || p.y > 900) p.vy *= -1;
    const dx = p.x - mouse.x, dy = p.y - mouse.y, d = Math.hypot(dx, dy);
    if (d < 140){ p.x += dx/d*.8; p.y += dy/d*.8; }
  }
  for (let i = 0; i < P.length; i++) for (let j = i+1; j < P.length; j++){   // 鄰近連線
    const a = P[i], b = P[j], d = Math.hypot(a.x-b.x, a.y-b.y);
    if (d < 150){ ctx.strokeStyle = `rgba(${ACC},${(1-d/150)*.13})`; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke(); }
  }
  for (const p of P){                                   // 游標連線（強度 5）＋節點
    const d = Math.hypot(p.x-mouse.x, p.y-mouse.y);
    if (d < 200){ ctx.strokeStyle = `rgba(${ACC},${(1-d/200)*.35})`; ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(mouse.x,mouse.y); ctx.stroke(); }
    ctx.fillStyle = `rgba(${ACC},.5)`; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill();
  }
  if (Math.random() < .02){ const p = P[Math.random()*P.length|0]; pings.push({ x:p.x, y:p.y, t:0 }); }   // 事件脈衝
  for (let k = pings.length-1; k >= 0; k--){ const g = pings[k]; g.t += .012; if (g.t >= 1){ pings.splice(k,1); continue; }
    ctx.strokeStyle = `rgba(${ACC},${(1-g.t)*.6})`; ctx.beginPath(); ctx.arc(g.x, g.y, 4+g.t*30, 0, 7); ctx.stroke(); }
  if (!document.hidden) requestAnimationFrame(tick); else setTimeout(() => requestAnimationFrame(tick), 500);
}
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) tick();
```
注意：`<canvas id="bgfx">` 放在舞台最底層、`pointer-events:none`；Demo 全螢幕時暫停；淺色主題把透明度再降一半。

### 3.3 遮罩格線（只在主題是藍圖、量測、工程時）
用途：工程感的底紋，只在游標附近浮現，避免整頁格子。
```css
.grid-bg{position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(var(--accent-rgb),.05) 1px,transparent 1px),linear-gradient(90deg,rgba(var(--accent-rgb),.05) 1px,transparent 1px);
  background-size:56px 56px;
  mask-image:radial-gradient(900px 600px at var(--sx,70%) var(--sy,30%),#000,transparent 75%);
  -webkit-mask-image:radial-gradient(900px 600px at var(--sx,70%) var(--sy,30%),#000,transparent 75%)}
```

### 3.4 漂移光暈（強度 4+，慎用）
用途：深色封面的空氣感。只放 1–2 顆、極淡、18–22 秒一個來回；被批評為 AI 味的常見來源，焦點不清時第一個刪。
```css
.orb{position:absolute;border-radius:50%;filter:blur(60px);pointer-events:none;opacity:.35;animation:drift 20s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate(-60px,50px) scale(1.15)}}
```

## 4. 封面

### 4.1 3D 傾斜主視覺＋同心環＋漂浮籌碼（強度 4）
用途：封面就讓觀眾看到「成品」。改編：主視覺換成產品畫面、照片或代表物；籌碼放 2–3 個真實資訊（技術、數字、角色），不要假數據。
```css
.hero{position:absolute;right:70px;top:50%;width:720px;height:720px;transform:translateY(-50%);perspective:1400px}
.hero .tilt{position:absolute;left:50%;top:50%;width:600px;transform:translate(-50%,-50%) rotateX(var(--rx,4deg)) rotateY(var(--ry,-8deg));
  transform-style:preserve-3d;transition:transform .25s ease-out}
.hero .tilt img{width:100%;border-radius:20px;box-shadow:0 60px 120px rgba(0,0,0,.45)}
.hero .rings{position:absolute;inset:-120px;pointer-events:none}
.hero .rings circle{fill:none;stroke:var(--line)}
.hero .rings .spin{transform-origin:50% 50%;animation:spin 60s linear infinite}
.chip{position:absolute;display:flex;gap:10px;align-items:center;padding:12px 16px;border-radius:14px;font-size:14px;
  background:var(--bg-1);border:1px solid var(--line-2);box-shadow:0 18px 40px rgba(0,0,0,.25);animation:float 6s ease-in-out infinite}
.chip:nth-of-type(2){animation-delay:-2s}.chip:nth-of-type(3){animation-delay:-4s}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes float{50%{translate:0 -12px}}
```
```js
stage.addEventListener("mousemove", e => {           // 只在封面頁傾斜，游標離開回正
  if (cur !== 0) return;
  const r = stage.getBoundingClientRect(), x = (e.clientX-r.left)/r.width, y = (e.clientY-r.top)/r.height;
  tilt.style.setProperty("--ry", ((x-.5)*16-6) + "deg"); tilt.style.setProperty("--rx", ((.5-y)*12+3) + "deg");
});
```
SVG 環：`<svg class="rings" viewBox="0 0 960 960"><circle class="spin" cx="480" cy="480" r="420" stroke-dasharray="4 12"/><circle cx="480" cy="480" r="340"/></svg>`。

### 4.2 關鍵詞強調
用途：標題中最重要的詞。建議實心強調色＋進場時底線畫出；漸層文字是常見 AI 味，只在品牌本身就是漸層時使用。
```css
.hl{color:var(--accent);background:linear-gradient(var(--accent),var(--accent)) no-repeat 0 100%/0 .08em;transition:background-size .8s var(--ease-out) .4s}
.slide.active .hl{background-size:100% .08em}
```

## 5. 章節與尋路

### 5.1 鏤空大字＋數字軌道（強度 3–4）
用途：章節頁一眼看出「進入新段落」與「第幾段」。改編：大字可用章節英文、關鍵字或年份；軌道上的圖示換成該章節的代表圖示。
```css
.sec .big{font-size:220px;font-weight:900;line-height:.9;color:transparent;-webkit-text-stroke:2px rgba(var(--accent-rgb),.7);transition:color .6s}
.sec .big:hover{color:rgba(var(--accent-rgb),.15)}
.sec .n{position:absolute;right:150px;top:50%;transform:translateY(-50%);width:420px;height:420px;display:grid;place-items:center}
.sec .n > svg{position:absolute;inset:0}
.sec .n .r1{fill:none;stroke:var(--line-2);stroke-dasharray:4 10;transform-origin:center;animation:spin 40s linear infinite}
.sec .n .r2{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:120 900;stroke-linecap:round;transform-origin:center;animation:spin 8s linear infinite}
.sec .n .digit{font:800 150px/1 var(--sans);color:var(--accent)}
.sec .n .orbit{position:absolute;inset:0;animation:spin 14s linear infinite}
.sec .n .orbit span{position:absolute;top:-22px;left:50%;translate:-50% 0;width:44px;height:44px;border-radius:14px;display:grid;place-items:center;
  background:var(--bg-1);border:1px solid var(--line-2);color:var(--accent)}
.sec .n .orbit span svg{animation:spin 14s linear infinite reverse}   /* 圖示反轉，保持正立 */
```
注意：`.sec .n > svg` 要用 `>` 限定，否則會抓到軌道裡的圖示 SVG。

### 5.2 章節導覽膠囊（強度 2+）
用途：在章節頁顯示全部章節、目前章節反白，點擊直接跳過去（Q&A 時很好用）。由 JS 依章節資料產生：
```js
const SECS = [["part1","01 背景"],["part2","02 做法"],["part3","03 成果"]];
slides.forEach(s => { const nav = s.querySelector(".secnav"); if (!nav) return;
  nav.innerHTML = SECS.map(([id,l],i) => `<button data-goto="${id}" class="${+s.dataset.sec===i?"on":""}">${l}</button>`).join(""); });
```

### 5.3 步驟條（強度 2+）
用途：一個長段落（例如五個關卡）中，每頁右上角顯示目前在第幾步、已完成幾步。只標 `data-stage="3"`，JS 自動產生：
```js
const STAGES = ["定義","設計","開發","上線","優化"];
slides.forEach(s => { const k = +s.dataset.stage; if (!k) return;
  const el = document.createElement("div"); el.className = "stepper";
  el.innerHTML = STAGES.map((t,i) => `<div class="st ${i+1<k?"done":""} ${i+1===k?"cur":""}"><span class="dot"></span>${i<STAGES.length-1?'<span class="bar"></span>':""}<span class="lbl">${t}</span></div>`).join("");
  s.appendChild(el); });
```
```css
.stepper{position:absolute;top:58px;right:92px;display:flex;align-items:center}
.stepper .st{position:relative;display:flex;align-items:center}
.stepper .dot{width:14px;height:14px;border-radius:50%;border:2px solid var(--line-2);background:var(--bg-1)}
.stepper .bar{width:46px;height:2px;background:var(--line)}
.stepper .done .dot,.stepper .done .bar{background:rgba(var(--accent-rgb),.5);border-color:transparent}
.stepper .cur .dot{width:18px;height:18px;background:var(--accent);border-color:var(--accent);box-shadow:0 0 0 6px rgba(var(--accent-rgb),.15)}
.stepper .lbl{position:absolute;top:28px;left:50%;translate:-50% 0;white-space:nowrap;font-size:13px;color:var(--text-2);display:none}
.stepper .cur .lbl{display:block}
```

### 5.4 總覽軌道＋流動光點（強度 3+）
用途：議程頁，一條細線串起各章節卡片，一顆光點沿線緩慢移動暗示「我們要走這條路」。
```css
.ov-track{position:relative;display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-top:30px}
.ov-track .line{position:absolute;left:30px;right:30px;top:-34px;height:2px;background:linear-gradient(90deg,rgba(var(--accent-rgb),.6),rgba(var(--accent-rgb),.1))}
.ov-track .line::after{content:"";position:absolute;top:-4px;width:10px;height:10px;border-radius:50%;background:var(--accent);animation:travel 5s ease-in-out infinite}
@keyframes travel{from{left:0}to{left:calc(100% - 10px)}}
```
卡片加 `data-goto="章節id"` 就能點擊跳轉；卡片 hover 時「前往」字樣與箭頭間距拉開。

### 5.5 HUD：進度條、頁碼、閒置淡出
用途：講者知道位置、觀眾不被干擾。導覽列平時 35–40% 不透明，滑鼠移過去才完整顯示；Demo 全螢幕時隱藏。

## 6. 內容卡

### 6.1 卡片浮起＋圖示徽章（強度 2+）
用途：卡片內容少、被拉高時，用大型圖示徽章填滿中段，文字壓到底部；hover 時卡片輕微浮起、徽章放大。改編：徽章顏色用語意色區分類型（正向、警示、負向）。
```js
document.querySelectorAll(".fill>.card").forEach(c => {
  const ic = c.querySelector(":scope>.ic"), h = c.querySelector(":scope>.h3"); if (!ic || !h) return;
  const m = document.createElement("span"); m.className = "medal " + [...ic.classList].filter(k => k !== "ic").join(" ");
  const ring = document.createElement("i"); ring.appendChild(ic.querySelector("svg").cloneNode(true)); m.appendChild(ring);
  c.insertBefore(m, h); c.classList.add("has-medal");
});
```
```css
.fill>.card .h3{margin-top:auto}
.medal{flex:1;display:grid;place-items:center;pointer-events:none;--mr:var(--accent-rgb)}
.medal.warn{--mr:161,98,7}.medal.bad{--mr:185,28,28}            /* 依語意色調整 */
.medal i{position:relative;width:104px;height:104px;border-radius:50%;display:grid;place-items:center;color:rgb(var(--mr));
  background:radial-gradient(circle at 35% 30%,rgba(var(--mr),.24),rgba(var(--mr),.04) 70%);border:1px solid rgba(var(--mr),.35);transition:scale .5s var(--ease-out)}
.medal i::before{content:"";position:absolute;inset:-16px;border-radius:50%;border:1px dashed rgba(var(--mr),.25);animation:spin 24s linear infinite}
.medal svg{width:46px;height:46px;stroke-width:1.6}
@media (hover:hover){.fill>.card:hover{translate:0 -6px}.fill>.card:hover .medal i{scale:1.07}}
.card.has-medal>.ic{display:none}
```

## 7. 流程與因果

### 7.1 流動連接線（強度 3+）
用途：垂直流程中，連接線上有光點往下流，表示資料或請求的方向。
```css
.fconn{height:36px;position:relative;margin-left:34px}
.fconn::before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:rgba(var(--accent-rgb),.3)}
.fconn::after{content:"";position:absolute;left:-4px;width:10px;height:10px;border-radius:50%;background:var(--accent);animation:down 1.6s linear infinite}
@keyframes down{from{top:-4px;opacity:0}20%{opacity:1}to{top:calc(100% - 6px);opacity:0}}
```

### 7.2 掃光軌道（強度 3+）
用途：橫向階段卡片上方一條軌道，一道光從左掃到右，表示「依序推進」。
```css
.track{position:absolute;left:0;right:0;top:-26px;height:3px;border-radius:3px;background:rgba(var(--accent-rgb),.15);overflow:hidden}
.track::after{content:"";position:absolute;inset:0;width:30%;background:linear-gradient(90deg,transparent,var(--accent),transparent);animation:sweep 3.5s ease-in-out infinite}
@keyframes sweep{from{translate:-100% 0}to{translate:340% 0}}
```

### 7.3 Before → After（強度 2+）
用途：前後對照。Before 卡降低不透明度，After 卡強調色外框；中間圓鈕的箭頭輕推，暗示方向。
```css
.ba{display:grid;grid-template-columns:1fr 90px 1fr;align-items:stretch}
.ba .before{opacity:.75}
.ba .after{border-color:rgba(var(--accent-rgb),.45);background:rgba(var(--accent-rgb),.06)}
.ba .mid span{width:62px;height:62px;border-radius:50%;display:grid;place-items:center;color:var(--accent);border:1px solid var(--line-2);animation:nudge 2s ease-in-out infinite}
@keyframes nudge{50%{translate:8px 0}}
```
也可改成拖曳滑桿：兩張圖疊在一起，用 `clip-path: inset(0 0 0 var(--x))` 揭示 After。

### 7.4 機制模擬器（強度 3+，講者操作）
用途：把抽象機制（快取、排隊、重試、額度、權限）變成可按的示範：按「執行」後節點依序亮起、計數器跳動，對照兩種做法的差異。改編：節點與計數器的意義依主題重寫；結果必須和真實行為一致。
```js
const wait = ms => new Promise(r => setTimeout(r, ms));
let busy = false;
runBtn.addEventListener("click", async () => {
  if (busy) return; busy = true; counterA.textContent = 0; counterB.textContent = 0;
  for (let round = 0; round < 5; round++){
    for (let k = 0; k < nodesA.length; k++){
      nodesA[k].classList.add("lit"); nodesB[k].classList.add("lit");
      if (k === HOT_INDEX) counterA.textContent = +counterA.textContent + 1;   // 只有 A 方案每次都打到昂貴節點
      if (k === HOT_INDEX && round === 0) counterB.textContent = 1;          // B 方案只有第一次
      await wait(260); nodesA[k].classList.remove("lit"); nodesB[k].classList.remove("lit");
    }
    await wait(120);
  }
  busy = false;
});
```
```css
.fnode{display:flex;gap:14px;align-items:center;padding:16px 18px;border-radius:14px;background:var(--surface-2);border:1px solid var(--line);transition:background .25s,border-color .25s}
.fnode.lit{background:rgba(var(--accent-rgb),.18);border-color:var(--accent)}
.fnode.hot.lit{background:rgba(185,28,28,.15);border-color:var(--bad)}
.counter .v{font:800 40px/1 var(--sans);font-variant-numeric:tabular-nums}
```
跳頁進來時重設計數器；reduced motion 下直接顯示最終數字。

### 7.5 步驟同步畫面檢視器（強度 3+，最常用）
用途：一個流程有 3–6 張畫面時，左邊步驟、右邊畫面同步；自動輪播並在目前步驟下方顯示倒數進度條，講者點任何一步就停止自動播放並跳到該步。
```js
const steps = [...box.querySelectorAll(".vstep")], imgs = [...viewer.querySelectorAll("img")];
let k = 0, timer, paused = false;
function show(i){ k = i; steps.forEach((s,j) => s.classList.toggle("on", j===i)); imgs.forEach((im,j) => im.classList.toggle("on", j===i)); }
function auto(){ clearInterval(timer); if (!paused) timer = setInterval(() => { if (slides[cur] === mySlide) show((k+1) % steps.length); }, 4500); }
steps.forEach((s,i) => s.addEventListener("click", () => { paused = true; clearInterval(timer); box.classList.add("paused"); show(i); }));
mySlide.addEventListener("enter", () => { show(0); auto(); });
```
```css
.viewer{position:relative;border-radius:16px;overflow:hidden;aspect-ratio:2/1;box-shadow:var(--shadow)}
.viewer img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top;opacity:0;scale:1.02;transition:opacity .6s,scale .8s var(--ease-out)}
.viewer img.on{opacity:1;scale:1;z-index:1}
.vstep{cursor:pointer;opacity:.5;transition:opacity .3s}
.vstep.on{opacity:1}.vstep.on .h3{color:var(--accent)}
.vstep .tm{height:2px;margin-top:10px;background:var(--line);overflow:hidden;display:none}
.vstep.on .tm{display:block}
.vstep.on .tm i{display:block;height:100%;width:0;background:var(--accent);animation:tm 4.5s linear forwards}
.paused .vstep.on .tm i{animation:none;width:100%}
@keyframes tm{to{width:100%}}
```
`.tm` 的動畫時長要和 `setInterval` 一致。

## 8. 截圖與證據

### 8.1 截圖框：浮起＋放大提示＋燈箱（強度 2+）
用途：截圖是證據，要能放大給觀眾看細節。
```css
.shot{position:relative;border-radius:14px;overflow:hidden;box-shadow:var(--shadow);cursor:zoom-in;transition:translate .4s var(--ease-out),box-shadow .4s}
@media (hover:hover){.shot:hover{translate:0 -4px}}
.shot .zoomhint{position:absolute;right:12px;bottom:12px;width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:rgba(0,0,0,.6);color:#fff;opacity:0;transition:opacity .3s}
.shot:hover .zoomhint{opacity:1}
```
燈箱用 `data-zoom` 開啟、點擊或 Esc 關閉（template 已內建）。

### 8.2 疊放截圖切換（強度 3）
用途：兩個相關畫面（前後版本、兩個步驟）前後錯位疊放，點後面那張或按鈕就交換。
```css
.stack{position:relative}
.stack .shot{position:absolute;width:86%;transition:transform .6s var(--ease-out),opacity .6s,z-index 0s .3s}
.stack .shot.back{transform:translate(14%,22%) scale(.94);opacity:.6;z-index:1;filter:saturate(.6)}
.stack .shot.front{transform:none;z-index:2}
```
```js
document.querySelectorAll(".stack").forEach(st => {
  const swap = () => st.querySelectorAll(".shot").forEach(s => { s.classList.toggle("front"); s.classList.toggle("back"); });
  st.querySelector(".swap").addEventListener("click", e => { e.stopPropagation(); swap(); });
  st.addEventListener("click", e => { if (e.target.closest(".shot.back")) swap(); });
});
```
這裡用 `transform` 是因為 `.shot` 的 hover 用的是 `translate`，兩者不衝突。

### 8.3 重點框標註
用途：在截圖上框出問題或重點區域（百分比定位）＋短標籤。框只在進場時脈動一兩次就停，不要無限脈動。
```css
.hl-box{position:absolute;border:3px solid var(--bad);border-radius:8px;box-shadow:0 0 0 4px rgba(185,28,28,.15);animation:pulse 1.6s ease-in-out 2}
.hl-tag{position:absolute;background:var(--bad);color:#fff;font-size:14px;font-weight:700;padding:6px 10px;border-radius:8px}
@keyframes pulse{50%{box-shadow:0 0 0 10px rgba(185,28,28,.05)}}
```

### 8.4 蓋章
用途：標示「示意資料」「已淘汰」「通過」這類判定；進場時從放大縮回、只出現一次。
```css
.stamp{position:absolute;right:26px;top:42%;rotate:-12deg;border:3px solid var(--bad);color:var(--bad);font:800 22px/1 var(--sans);letter-spacing:.08em;
  padding:10px 16px;border-radius:10px;background:rgba(255,255,255,.85);animation:stampIn 1.2s var(--ease-out) both .9s}
@keyframes stampIn{from{opacity:0;scale:1.6}to{opacity:1;scale:1}}
```

### 8.5 思考泡泡
用途：在畫面旁加一句「當時的心聲／觀眾會想的問題」，緩慢漂浮引起注意。一頁最多一個。

## 9. 對話與文件

### 9.1 對話視窗
用途：呈現提問與回覆、訪談、客服對話；比純文字更像「現場」。標題列放對象名稱與狀態；氣泡左右區分角色；需要指出問題時，在氣泡內把那段字用警示色底標記。
```css
.chat{border-radius:20px;border:1px solid var(--line-2);background:var(--bg-1);box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column}
.chat-hd{display:flex;align-items:center;gap:12px;padding:14px 20px;border-bottom:1px solid var(--line);font-size:14px;color:var(--text-2)}
.msg{display:flex;gap:14px;align-items:flex-start}.msg.me{flex-direction:row-reverse}
.av{width:38px;height:38px;border-radius:12px;flex:none;display:grid;place-items:center;font-weight:700}
.msg.me .bubble{background:rgba(var(--accent-rgb),.14);border:1px solid rgba(var(--accent-rgb),.3);border-top-right-radius:6px}
.msg.ai .bubble{background:var(--surface-2);border:1px solid var(--line);border-top-left-radius:6px}
.bubble .warn{background:rgba(185,28,28,.12);color:var(--bad);border-radius:4px;padding:0 4px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.typing span{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);animation:bounce 1.2s infinite}
.typing span:nth-child(2){animation-delay:.15s}.typing span:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,80%,100%{translate:0 0;opacity:.4}40%{translate:0 -6px;opacity:1}}
```
「輸入中」動畫只在要表演「回覆正在產生」時使用，不要常駐。

### 9.2 文件卡
用途：展示產出的文件（規格、報告、提案書）的結構：標題列＋分段標籤＋內容；新增或有問題的部分用不同底色標記。

## 10. 狀態切換

### 10.1 點擊切換卡（強度 3）
用途：示範「設定前／設定後」「未完成／完成」「關閉／開啟」：講者點卡片，狀態標籤、文字、外框一起切換。
```js
document.querySelectorAll(".toggle-card").forEach(c => c.addEventListener("click", () => {
  const on = c.classList.toggle("ok");
  c.querySelectorAll("[data-on]").forEach(el => el.textContent = on ? el.dataset.on : el.dataset.off);
}));
```
```html
<div class="card toggle-card"><span class="st" data-off="尚未設定" data-on="已設定">尚未設定</span> …</div>
```
```css
.toggle-card{cursor:pointer;transition:border-color .35s,background .35s,translate .35s var(--ease-out)}
.toggle-card .st{color:var(--warn);background:rgba(161,98,7,.1);border-radius:999px;padding:6px 11px;font-size:13px;font-weight:600}
.toggle-card.ok{border-color:rgba(var(--accent-rgb),.5);background:rgba(var(--accent-rgb),.08)}
.toggle-card.ok .st{color:var(--accent);background:rgba(var(--accent-rgb),.12)}
```

### 10.2 比較表互動
用途：講者講到哪一列，滑鼠移過去該列就淡淡高亮；推薦欄用淡強調色底、結論列加粗。
```css
table.cmp td{transition:background .25s}
@media (hover:hover){table.cmp tr:hover td{background:rgba(var(--accent-rgb),.06)}}
table.cmp .pickcol{background:rgba(var(--accent-rgb),.07)}
table.cmp tr.pick td{font-weight:600}
```

## 11. 結論

### 11.1 關鍵詞連鎖亮起（強度 3+）
用途：結論頁底部 3–5 個關鍵詞，依序亮起再循環，串成一句話（例如「問題 → 原型 → 驗證 → 上線」）。進入該頁才開始，離開就停。
```js
let chainT;
function runChain(){
  clearInterval(chainT); const items = [...document.querySelectorAll("#chain span")]; let k = 0;
  chainT = setInterval(() => { if (slides[cur] !== chainSlide){ clearInterval(chainT); return; }
    items.forEach((s,i) => s.classList.toggle("on", i===k)); k = (k+1) % items.length; }, 1100);
}
chainSlide.addEventListener("enter", runChain);
```
```css
.chain{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.chain span{padding:14px 22px;border-radius:14px;border:1px solid var(--line);font-size:20px;color:var(--text-2);transition:background .4s,color .4s}
.chain span.on{color:var(--bg-1);background:var(--accent);border-color:var(--accent)}
```

## 12. 內嵌 Demo 全螢幕層（強度 5）

用途：講到成品時，整個畫面切成可操作的網站或 App。
- 結構：`#live`（全螢幕 iframe＋載入畫面）＋`#livebar`（底部浮動控制列：上一頁、Demo 標籤、重新開始、新分頁開啟、下一頁）。
- 只在前後一頁時才載入 iframe；載入完成淡出載入畫面；超過約 9 秒顯示「改開新分頁」。
- 進入 Demo 頁時隱藏 HUD 與背景粒子；滑鼠閒置 2.5 秒後控制列淡到 30%。
- 方向鍵在 iframe 取得焦點時會被網站吃掉，控制列一定要有上一頁、下一頁按鈕。
```css
#live{position:fixed;inset:0;z-index:40;opacity:0;visibility:hidden;transition:opacity .45s,visibility .45s}
body.live-on #live{opacity:1;visibility:visible}
#live.loaded .loading{opacity:0;visibility:hidden}
#live.slow .loading .fallback{opacity:1}
#livebar{position:fixed;left:50%;bottom:18px;translate:-50% 0;z-index:45;display:flex;gap:4px;padding:6px;border-radius:999px;
  background:var(--bg-1);border:1px solid var(--line-2);box-shadow:var(--shadow);opacity:0;visibility:hidden;transition:opacity .35s,visibility .35s}
body.live-on #livebar{opacity:1;visibility:visible}
body.live-on.idle #livebar{opacity:.3}
```
```js
let idleT; addEventListener("mousemove", () => { document.body.classList.remove("idle"); clearTimeout(idleT); idleT = setTimeout(() => document.body.classList.add("idle"), 2500); });
```
離線 Demo 的做法見 `assets-embed-build.md` §7。

## 13. 用 HTML 重建產品畫面

用途：沒有好截圖、或要示範「改之前」的版本時，用 HTML 重建一小塊產品介面，保留產品自己的配色與字體（放在 `.pf` 這類命名空間下，避免和簡報 tokens 混在一起）。示意的假資料用醒目底色標出，並可加 §8.4 的蓋章說明是示意。

## 14. 高強度效果的取捨

以下效果在實作中很吸睛，但也是 UI 品質類 skill 常點名的 AI 味來源。強度 4–5 時可用，但照右欄處理：

| 效果 | 風險 | 使用方式 |
| --- | --- | --- |
| 漸層文字 | 廉價感、可讀性差 | 改實心強調色＋底線；品牌本身是漸層才用 |
| 持續脈動的狀態點 | 分散注意力 | 只放在真的「即時」的元素，或只脈動 2 次 |
| 漂浮光球 | 典型 AI 背景 | 最多 1–2 顆、極淡、慢 |
| 整頁格線 | 裝飾性背景 | 只在藍圖、工程主題，並用游標遮罩 |
| 假視窗三色點 | 手繪假外框 | 對話視窗可以用簡化標題列，不要假瀏覽器網址列 |
| 所有卡片 hover 浮起 | 每個元素都在動 | 只給可點擊或要強調的卡片 |
| 持續旋轉的環 | 搶焦點、暈 | 40 秒以上一圈、低對比，reduced motion 停止 |

## 15. 整合到 template

1. 把要用的 CSS 加進 template 的「5. 元件」區塊，顏色一律走 tokens。
2. JS 加進主腳本：初始化放在 `fit()` 之前；需要「進入頁面才開始」的互動，在該頁 `slide.addEventListener("enter", …)` 啟動，在離開時（`cur` 不等於該頁）自行停止。
3. 新增的持續動畫都要加進 `@media (prefers-reduced-motion: reduce)` 的停用清單。
4. 跑 `shoot.cjs`；互動頁要另外截「互動後」的狀態確認（例如模擬器跑完、切換後、步驟 3）。
