// 逐頁截圖 + 溢出偵測 + 頁面錯誤。用法：
//   node shoot.cjs <deck.html> <輸出資料夾> [--exe /path/to/chromium] [--wait 1500]
// 需要 playwright-core（npm i playwright-core）。輸出 slide-01.png… 與 report.txt。
const { chromium } = require("playwright-core");
const fs = require("fs"), path = require("path");
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i > -1 ? args.splice(i, 2)[1] : null; };
const exe = opt("--exe") || process.env.CHROMIUM_PATH || undefined;
const wait = +(opt("--wait") || 1500);
const [file, out = "shots"] = args;
if (!file) { console.error("usage: node shoot.cjs deck.html outDir [--exe chromium] [--wait ms]"); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch({ executablePath: exe });
  const p = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const log = [];
  p.on("pageerror", e => log.push("PAGEERROR " + e.message));
  p.on("console", m => { if (m.type() === "error") log.push("CONSOLE " + m.text()); });
  p.on("requestfailed", r => log.push("REQFAIL " + r.url().slice(0, 120)));
  await p.goto("file://" + path.resolve(file));
  await p.waitForTimeout(600);
  const n = await p.evaluate(() => document.querySelectorAll(".slide").length);
  for (let i = 0; i < n; i++) {
    if (i) await p.keyboard.press("ArrowRight");
    await p.waitForTimeout(wait);
    const issues = await p.evaluate(() => {
      const s = document.querySelector(".slide.active"), st = document.getElementById("stage").getBoundingClientRect(), out = [];
      s.querySelectorAll("*").forEach(el => {
        if (el.closest("[data-allow-overflow]")) return;
        const r = el.getBoundingClientRect(); if (!r.width) return;
        if (r.right > st.right + 1 || r.bottom > st.bottom + 1 || r.left < st.left - 1) out.push("出界 " + el.tagName + "." + el.className);
        if (el.scrollHeight > el.clientHeight + 2 && getComputedStyle(el).overflowY === "hidden" && el.clientHeight > 0) out.push("內容被裁切 " + el.tagName + "." + el.className);
      });
      // 孤字：段落最後一行只有 1 個 CJK 字
      s.querySelectorAll(".p,.sub,.h3,.title,.hero,.bubble,td").forEach(el => {
        const rg = document.createRange(); rg.selectNodeContents(el); const rects = [...rg.getClientRects()];
        if (rects.length > 1) { const last = rects[rects.length - 1]; if (last.width < 40) out.push("疑似孤字 " + el.textContent.trim().slice(-6)); }
      });
      return [...new Set(out)].slice(0, 6);
    });
    if (issues.length) log.push(`slide ${i + 1}: ` + issues.join(" | "));
    await p.screenshot({ path: path.join(out, `slide-${String(i + 1).padStart(2, "0")}.png`) });
  }
  // 縮圖總覽（contact sheet），一次看整份節奏
  const imgs = fs.readdirSync(out).filter(f => /^slide-\d+\.png$/.test(f)).sort();
  const html = `<body style="margin:0;background:#111;display:grid;grid-template-columns:repeat(4,1fr);align-items:start;align-content:start;gap:8px;padding:8px">${imgs.map((f, i) => `<figure style="margin:0;color:#aaa;font:12px sans-serif"><img style="width:100%;display:block" src="data:image/png;base64,${fs.readFileSync(path.join(out, f)).toString("base64")}">${i + 1}</figure>`).join("")}</body>`;
  const sheet = await b.newPage({ viewport: { width: 1600, height: 900 } });
  await sheet.setContent(html); await sheet.waitForTimeout(500);
  await sheet.screenshot({ path: path.join(out, "contact-sheet.png"), fullPage: true });
  fs.writeFileSync(path.join(out, "report.txt"), log.join("\n") || "OK：沒有偵測到問題");
  console.log(log.join("\n") || "OK"); console.log(`${n} slides → ${out}`);
  await b.close();
})();
