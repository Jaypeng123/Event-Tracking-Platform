// 只內嵌簡報實際用到的 Lucide 圖示，取代 CDN。用法：npm i lucide && node inline-icons.cjs deck.html
// 會取代 <script src="https://unpkg.com/lucide…"> 或既有的 <script id="icons">（不要把這兩種寫在 HTML 註解裡）。
const fs = require("fs");
const lucide = require("lucide");
const file = process.argv[2];
let html = fs.readFileSync(file, "utf8");
const names = [...new Set([...html.matchAll(/data-lucide="([a-z0-9-]+)"/g)].map(m => m[1]))].sort();
const pascal = n => n.replace(/(^|-)([a-z0-9])/g, (_, __, c) => c.toUpperCase());
const map = {}, missing = [];
for (const n of names) {
  const node = lucide.icons[pascal(n)];
  if (!node) { missing.push(n); continue; }
  map[n] = node[2].map(([tag, attrs]) => `<${tag} ${Object.entries(attrs).map(([k, v]) => `${k}="${v}"`).join(" ")}/>`).join("");
}
if (missing.length) { console.error("missing icons:", missing.join(", ")); process.exit(1); }
const block = `<script id="icons">window.lucide={icons:${JSON.stringify(map)},createIcons(){document.querySelectorAll("i[data-lucide]").forEach(el=>{const d=this.icons[el.dataset.lucide];if(!d)return;const s=document.createElementNS("http://www.w3.org/2000/svg","svg");["width","height"].forEach(a=>s.setAttribute(a,"24"));s.setAttribute("viewBox","0 0 24 24");s.setAttribute("fill","none");s.setAttribute("stroke","currentColor");s.setAttribute("stroke-width","2");s.setAttribute("stroke-linecap","round");s.setAttribute("stroke-linejoin","round");s.setAttribute("class","lucide "+(el.getAttribute("class")||""));if(el.getAttribute("style"))s.setAttribute("style",el.getAttribute("style"));s.innerHTML=d;el.replaceWith(s);});}};</script>`;
const re = /<script src="https:\/\/unpkg\.com\/lucide[^"]*"><\/script>|<script id="icons">[\s\S]*?<\/script>/;
if (!re.test(html)) { console.error("找不到 lucide <script>，請先放一個 <script id=\"icons\"></script>"); process.exit(1); }
html = html.replace(re, () => block);
fs.writeFileSync(file, html);
console.log(names.length, "icons inlined");
