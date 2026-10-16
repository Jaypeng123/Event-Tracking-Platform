# 素材、嵌入網站與單檔交付

## 1. 截圖與圖片

- **使用者提供的每一張圖都要用到**（除非內容重複，那就告訴使用者哪張沒用、為什麼）。
- 裁切：去掉瀏覽器網址列、分頁列、作業系統選單列、桌面背景與空白邊。裁完的空間拿來放標題或說明，不要留白框。
- 格式：轉成 webp（品質 82–88），長邊 ≤ 2400px；放在 `assets/`，檔名用語意（`figma-oauth-callback.webp`）。
  ```bash
  python3 -c "from PIL import Image; im=Image.open('in.png'); im.crop((0,88,im.width,im.height)).save('assets/x.webp','WEBP',quality=85)"
  ```
- 截圖框只用細邊框＋圓角＋淡陰影；不要補畫假的瀏覽器列或手機外框。
- 截圖太小或字看不清：改用 HTML 重做那一塊介面，或拆成局部特寫，不要硬塞。
- `alt` 寫內容是什麼；純裝飾用 `alt=""`。

## 2. 從 Figma 取素材（有 Figma MCP 時）

- URL 解析：`figma.com/design/:fileKey/...?node-id=1-2` → nodeId `1:2`。
- 先 `get_metadata` 拿頁面與 frame 清單，再對**單一 frame／區塊**截圖，不要整頁截。
- 網路被代理擋住、無法下載圖檔時，用 `get_screenshot` 的 base64 回應存檔。
- 需要真實資料（頁面名稱、元件文字）做 Demo 時，從 metadata 取，不要自己編。
- 截圖預設解析度偏低；簡報用要指定較高倍率，或只截需要的區塊。

## 3. 用 HTML 重建介面（取代模糊截圖）

從截圖或 Figma frame 抽取：文字原文 → 字級／字重／行數 → 間距（標題到內文、元件間距、內距）→ 按鈕尺寸與層級 → 色彩角色 → 圓角 → 圖片處理。不清楚時依序保留：可見的視覺語言 → 版面與間距邏輯 → 元件類型 → 氛圍。不要簡化成通用模板、不要壓縮間距。做完截圖和原圖逐區比對。

講設計故事時，重建的介面可以補上非理想狀態（空狀態、載入、錯誤、權限不足），這通常是作品集最有說服力的一頁。

## 4. 嵌入線上網站

- 用 `<iframe>` 全螢幕覆蓋在該頁上（不在 1600×900 舞台內縮放，避免網站被縮小變形），並提供：重新整理、新分頁開啟、載入中與「載入太慢」的提示（約 9 秒）。
- **只在前後一頁時才載入**（`Math.abs(cur - liveIdx) <= 1`），避免開場就吃頻寬。
- 已知限制，要事先告訴使用者：
  - 網站設 `X-Frame-Options`／CSP `frame-ancestors` 會拒絕嵌入。
  - 需要登入（例如 ChatGPT 登入、OAuth）的網站在 iframe 裡常常失敗或被擋第三方 cookie。
  - 現場網路不穩。
- 解法：做**離線 Demo**（下一節），線上網址放「新分頁開啟」當備案。

## 5. 離線 Demo（用真的前端程式＋假 API）

適用：產品需要登入、要呼叫付費 API、或現場可能沒網路。

1. 用 Vite 編譯產品的真實頁面元件（例如 Next.js 的 `app/page.tsx` + `globals.css`），Tailwind 用 `@tailwindcss/postcss`（Vite 新版與 `@tailwindcss/vite` 可能有 peer 衝突）。
2. 寫 `mock-api.js` 攔截 `fetch`：對每個 API 路徑回傳固定資料，並加 300–1200ms 延遲，讓載入狀態看得到。
3. 資料用真實來源（例如從 Figma metadata 取真的頁面名稱）；若是假資料，在 Demo 或講者備註標明。
4. 需要預填的欄位（例如貼好的 Figma 連結）用 Vite transform plugin 改初始 state，不要改產品原始碼。
5. `file://` 會擋 `type="module"` 的 script：建置後把 JS／CSS 內嵌進 HTML（inline 腳本）。
6. 用 Playwright 跑一次完整流程（進入專案 → 貼連結 → 分析 → 看結果），截圖確認。

## 6. 單一檔案交付

- `scripts/inline-icons.cjs deck.html`：把用到的 Lucide 圖示內嵌成 `<script id="icons">`，不依賴 CDN。
- `scripts/build_standalone.py deck.html standalone.html [--demo demo/index.html]`：圖片轉 base64 data URI；Demo 存成 `window.__DEMO_HTML__`，簡報端用 `iframe.srcdoc` 載入。
- 字體：系統字不需處理；自訂 Latin 字要 subset 並 base64 內嵌；中文字體太大，不要整包內嵌。
- 交付前斷網開一次 standalone 檔，確認圖示、圖片、Demo 都正常。
- 檔案大小：一般 5–15MB 可接受；超過 25MB 檢查是不是有未壓縮的 png 或影片。

## 7. 影片與生成素材（選用）

- 影片：`<video muted loop playsinline poster="...">`，5–8 秒、H.264／WebM 壓縮、無聲；要有暫停方法。
- AI 生成背景圖：同一份簡報用同一段風格前言（style preamble）；提示詞寫完整句子＋光線／鏡頭／構圖；要求在標題位置留空（例如「左上三分之一保持乾淨」）；**不要讓圖片裡出現文字**，字一律用 HTML。輸出 16:9，至少 3200×1800 給高解析螢幕。
- 動態圖解優先用 CSS／SVG；真的需要 Lottie 時，單檔交付要內嵌播放器，並確認第 0 格、中間、最後一格都正常。
- 所有素材下載到本機再內嵌，不要熱連結外部網址。

## 8. 作品集頁（同一份內容的長捲動版）

使用者要把簡報轉成作品集時，另做一頁長捲動案例研究，而不是把簡報拉長：
Hero → 00 Overview（TL;DR）→ 01 Context → 02 Positioning → 03 Solution（嵌入 Demo，延遲載入）→ 04 Key Decisions（每個：問題／決策／結果）→ 05 Process → 06 Outcome → 07 Reflection。
- 側邊目錄＋閱讀進度條＋捲動揭示（揭示前內容仍可見，不能讓內容依賴動畫才出現）。
- 沒有量化成果就只寫質性成果，明講尚無數據。
- 要檢查 390px 手機寬：`overflow-x: clip`、表格包一層可橫向捲動的容器、卡片可換行，沒有水平溢出。
