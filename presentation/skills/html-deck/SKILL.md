---
name: html-deck
description: 製作可直接在瀏覽器播放的 HTML 互動簡報：固定 16:9 舞台、鍵盤與觸控翻頁、講者備註、全螢幕、可列印成 PDF、可離線開啟的單一檔案。適用於任何主題與場合：設計分享、提案與募資簡報、產品發表、技術分享、教學與課程、工作坊、成果報告與週報、研究報告、作品集與案例研究。當使用者要「做簡報／投影片／deck／slides／pitch」、要把文件、筆記、PPTX、PDF、網頁或 Figma 內容轉成簡報、要在簡報中嵌入網站或可操作的 Demo、要審查或改善既有簡報、或要把簡報延伸成作品集長頁時使用。不適用：必須交付可在 PowerPoint 編輯的 .pptx（改用 PPTX 類 skill）、整頁由 AI 生成圖片組成的圖片式簡報。
---

# HTML 互動簡報

目標：任何主題、任何場合，都能做出一份**內容站得住、看起來是設計師做的、在現場不會出包**的簡報。

## 何時讀哪份 reference

| 階段 | 讀 |
| --- | --- |
| 開工、寫大綱 | `references/workflow.md`：需求表、簡報類型與骨架、六步驟、確認點、誠實規則 |
| 定風格、排版 | `references/visual-system.md`：design read、色彩策略、tokens、字級、版型輪替、元件、AI 味清單 |
| 圖表、流程圖、數據 | `references/diagrams-data.md`：先問要不要畫、圖表選型、複雜度上限、資料誠實 |
| 加動態與互動 | `references/motion.md`：用途關卡、參數、簡報專屬規則 |
| 素材、截圖、Figma、生成圖、嵌入網站、Demo、單檔交付 | `references/assets-embed-build.md` |
| 檢查、審查、交付 | `references/qa.md`：自動截圖、人工走查、審查格式、無障礙、技術陷阱 |
| 修改這份 skill 前 | `references/sources.md`：每條規則來自哪份 skill、衝突怎麼裁決 |

工具：`assets/template.html`（簡報骨架）、`scripts/inline-icons.cjs`（圖示離線內嵌）、`scripts/build_standalone.py`（單檔建置）、`scripts/shoot.cjs`（逐頁截圖＋出界／裁切／孤字／錯誤偵測）。

## 0. 選路線

| 需求 | 路線 |
| --- | --- |
| 現場或線上播放、需要互動、嵌入網站或 Demo、寄送單一檔案、轉作品集 | **本 skill** |
| 對方必須在 PowerPoint／Keynote 裡改字 | 可編輯 PPTX 類 skill（本 skill 的內容流程與視覺規則仍適用） |
| 海報感、整頁視覺、不需要改字 | 圖片式簡報類 skill |
| 要輸出成影片 | 影片合成類 skill；本 skill 的故事線與視覺規則可沿用 |

不確定就問一句：「需要在 PowerPoint 裡編輯嗎？」不需要就走 HTML。

## 1. 流程（細節見 workflow.md）

1. **讀素材、填需求表**：使用者給的檔案（文件、PPTX、PDF、截圖、網址、Figma）先完整讀過，從中自動填表。只問會改變方向的缺口：受眾、場景（暗場投影／會議室／線上／寄送閱讀）、時間、要不要 Demo。使用者說「直接做」就寫下推論並繼續。
2. **確認點 1 — 大綱**：選定簡報類型與骨架，給逐頁表（標題直接講結論／該頁目的／版型家族／講者重點）、一句話主張、情緒曲線與唯一高峰。
3. **確認點 2 — 風格樣張**：一段 design read＋封面、一頁內容、一頁特殊頁（圖表、Demo 或比較）。
4. **全量製作**：從 `assets/template.html` 開始，先改 tokens，再逐頁做。
5. **QA**：跑 `shoot.cjs`，**打開截圖看**，修到乾淨，再人工走查。
6. **交付**：開發版＋單檔版，附頁數、備註完整度、待補資料、已驗證／未驗證清單。

使用者提供的每一份素材都要被用到，或說明為什麼沒用。之後的修改通常是文案和局部版面：直接改、重跑 QA、回報改了哪幾頁。

## 2. 硬規則

**內容**
- 一頁一個概念。標題本身就是結論（「轉換率卡在第二步」，不是「數據分析」）。
- 細節放講者備註（`data-notes`），投影片只留看得懂的最少文字。
- 白話優先；專有名詞第一次出現時用一句話或比喻解釋。
- **不捏造**：數據、引言、客戶評語、成果、logo 沒有來源就標「待補資料」；沒有量化成果就寫質性成果；示意資料要標明。
- 結尾要收住：重述主張＋希望受眾採取的行動，不要只有「謝謝聆聽」。

**版面**
- 固定 16:9 舞台（預設 1600×900），不捲動、不出界。放不下就拆頁或刪字，不把字縮到投影看不清。
- 同一版型家族不連續超過 2 頁；整份至少 4 種家族；高峰前一頁安靜。
- 一個強調色只給 1–2 個重點元素；語意色最多 3 個。品牌或來源素材有主色就用它，不自己發明配色。
- 深色或淺色由播放場景決定，整份鎖定一種。
- 中文排版：不加負字距、處理孤字、行首標點懸掛、同排標題對齊。
- 截圖裁掉瀏覽器與系統外框，不手繪假瀏覽器外框；手機 App 畫面可用一致的簡潔裝置框。

**動態**
- 只有三個用途：引導閱讀順序、說明變化或因果、在高峰給一次驚喜。換頁轉場短而一致；不要每個標題、段落都淡入。
- 只動 transform／translate／opacity／clip-path；每頁狀態可直接跳到；處理 `prefers-reduced-motion`；不在畫面上的動畫要暫停。

**技術**
- 單一 HTML、免建置也能開；不依賴 CDN（圖示內嵌、字體系統字或 subset 內嵌）。
- 鍵盤：← → Space PageUp PageDown Home End、N 備註、F 全螢幕、Esc 關閉；觸控滑動；網址 `#頁碼`；列印時每頁一張。
- 需要登入、付費 API 或現場網路不穩的 Demo：做離線版（真前端＋假 API），線上網址當備案。

## 3. 可搭配的 skill（有安裝就在對應階段使用，沒安裝就用本 skill 的摘要規則）

| 階段 | Skill | 用途 |
| --- | --- | --- |
| 內容 | 簡報製作流程與提示詞 | 需求表、六步驟提示詞 |
| 內容 | design-critique、ai-native-product-designer | 設計分享的骨架（問題→選項→驗證→決策→成果）、要求回饋的方式 |
| 內容 | design-workshop-facilitation | 工作坊型簡報：議程、活動頁、時間緩衝 |
| 風格 | ppt-visual、pptx-presentations、theme-factory | 投影片版型、配色與字體組合起點 |
| 風格 | hallmark、impeccable、design-taste-frontend、frontend-design、minimalist-ui、high-end-visual-design | 方向宣告、色彩策略、AI 味清單、版型多樣性 |
| 排版 | better-typography、make-a-type-scale、better-layout、better-ui、make-interfaces-feel-better | 字級比例、行高、對齊、間距、圓角、圖示粗細 |
| 圖表 | diagram-design | 流程圖、架構圖、旅程圖、各類圖表 |
| 動態 | animate、design-motion-principles、find-animation-opportunities、review-animations、apple-design | 要不要動、怎麼動、AI 味動態 |
| 素材 | prompt-images、prompt-videos、ai-image-generation、ai-video-generation、imagegen-frontend-web | 生成背景、插圖、短影片、版面參考圖 |
| 素材 | figma-use、figma-generate-design、image-to-code、imagegen-frontend-mobile、ui-state-expander | 從 Figma 取素材、用 HTML 重建介面、手機畫面呈現、狀態頁 |
| 背景 | algorithmic-art | 固定 seed 的生成式背景 |
| QA | better-interface、superfuture-design-review、break-ui、web-interface-guidelines | 審查格式、最壞資料測試 |

完整對照、每份 skill 的簡報適用度與刻意不採用的部分見 `references/sources.md`。

## 4. 實作要點

- 每頁 `<section class="slide" data-notes="…">`；需要依序出現的元素才加 `data-a`（腳本自動編號），標題與一般內文不加。
- 互動元件在 `slide.addEventListener("enter", …)` 裡初始化或重設。
- 跨頁共用的資訊（章節導覽、進度條、步驟條）用 JS 從資料產生，不要每頁手抄。
- 圖片放 `assets/`，可放大的加 `data-zoom`。
- 元件 class 名稱要有辨識度，選擇器用 `>` 限定範圍，避免互相污染。
- 改完任何樣式都重跑 `shoot.cjs`。

## 5. 交付前檢查（完整版見 qa.md）

- [ ] `shoot.cjs` 沒有出界、裁切、孤字、JS 錯誤；看過縮圖總覽，節奏有變化
- [ ] 每頁有備註；總時間符合報告長度（含 Q&A 與 20–30% 緩衝）
- [ ] 斷網開單檔版：圖示、圖片、Demo、字體都正常
- [ ] 內文對比 ≥ 4.5:1；AI 味清單沒有命中
- [ ] 沒有捏造的數據或引言；待補資料已列給使用者
- [ ] 回報時分清楚「看過截圖確認」與「只改了程式碼、未驗證」
