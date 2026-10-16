# 來源對照：這份 skill 從哪裡來

整理自 `AI_Skill.zip` 的全部 60 份 Markdown（58 份 skill＋2 份簡報流程筆記），加上「埋點規劃工具」HTML 簡報與作品集頁的實作經驗。這份檔案記錄**採用了什麼、刻意不採用什麼、衝突怎麼裁決**，之後調整 skill 時先看這裡。

## 採用對照

| 來源 | 採用到 | 內容 |
| --- | --- | --- |
| 簡報製作流程與提示詞 | workflow.md | 需求表、六步驟、每步檢查、不得捏造、交付前檢查 |
| Codex_PPT_Skills／codex-ppt SKILL | SKILL.md 路線選擇 | 三條路線（圖片式 PPTX、可編輯 PPTX、網頁互動 HTML）；確認點的概念。圖片生成與子代理流程**不採用**（HTML 路線不需要） |
| ppt-visual | visual-system.md §4 | 一頁一個概念、版型類型（封面、內容、比較、數據、結尾） |
| pptx-presentations | visual-system.md | 配色規格、圖表不要壓在文字下方 |
| high-end-visual-design | visual-system.md、motion.md | 大量留白、自訂 easing、避免制式 AI 網頁風格 |
| better-typography、make-a-type-scale | visual-system.md §3 | 依角色設定行高、balance／pretty、tabular-nums、字型 ≤ 3、大字行高收緊 |
| theme-factory、canvas-design | visual-system.md §1 | 先定設計理念再做視覺；主題 tokens 化 |
| diagram-design | visual-system.md、motion.md | 刪減優先、強調色只給 1–2 個元素、警告暗色＋青色光暈與三張相同卡片 |
| animate、animation-vocabulary、improve／review-animations、find-animation-opportunities、design-motion-principles | motion.md | 頻率關卡、easing 數值、只動 transform／opacity、不用 scale(0)、錯開 30–80ms、reduced motion 必要、AI 味動態清單、大量否決動畫候選 |
| scroll-craft | workflow.md §03、visual-system.md §4 | 情緒曲線、單一高峰、相鄰不重複手法、結尾要收住、不把字烘焙進圖、不捏造數據 |
| imagegen-frontend-web | visual-system.md §4–7 | 構圖錨點與背景模式輪替（同一種不連續 >2／>3）、至少一頁滿版與一頁安靜頁、唯一記憶點、調色盤紀律、允許／禁止的漸層、文案禁用詞 |
| prompt-images／prompt-videos／ai-image-generation／ai-video-generation | assets-embed-build.md §7 | 風格前言重複使用、完整句子提示詞、標題處留空、不生成文字、16:9 高解析、短靜音循環影片。廠商 CLI 只當選配 |
| algorithmic-art | visual-system.md §6 | 生成式背景固定 seed、非作用頁暫停 |
| hyperframes | motion.md §3 | 每個步驟狀態可直接到達（seek-safe）、簡報需要的功能清單（備註、跳頁、分段揭示） |
| text-to-lottie | assets-embed-build.md §7 | Lottie 檢查第 0／中／末格；簡單圖解優先 CSS／SVG |
| UI 視覺品質 11 份（hallmark、impeccable、design-taste-frontend、better-ui、better-layout、make-interfaces-feel-better、redesign-existing-projects、minimalist-ui、gpt-taste、frontend-design、industrial-brutalist-ui） | visual-system.md 全篇 | 一個強調色、不用純黑白、不預設 Inter、eyebrow 節制、不做相同卡片格、卡片不套卡片、組間距 ≥ 2×組內、同心圓角、陰影或邊框二擇一、圖示一套一粗細、不畫假瀏覽器外框、design read、場景決定深淺色、自我評分後再交付 |
| UI 審查 5 份（superfuture-design-review、better-interface、web-interface-guidelines、break-ui、design-critique） | qa.md | 審查順序與表格格式、HIGH／MEDIUM／LOW、具體數值修法、「考慮過但不改」、已驗證／未驗證、最壞資料測試、觀察→影響→建議 |
| Figma 交付 5 份（figma-use、figma-generate-design、image-to-code、design-handoff、agentation） | assets-embed-build.md §2–3 | URL 解析、先 metadata 再截區塊、HTML 重建介面的抽取順序與防走樣、重建後逐區比對 |
| 響應式／狀態 3 份（ui-state-expander、desktop-to-mobile、wireframe-prototyping） | assets-embed-build.md §3、§8 | 非理想狀態頁、作品集手機版檢查 |
| 設計探索 3 份（ai-native-product-designer、design-an-interface、design-workshop-facilitation） | workflow.md §03 | 設計分享的故事骨架（問題→選項→驗證→決策→成果）、Q&A 時間與 20–30% 緩衝 |
| iOS／Android 7 份 | assets-embed-build.md §3 | 只取手機介面重建的尺寸（390 寬、20px 邊距、44pt 觸控、字級表）；其餘平台規範不適用 |

## 來自實作經驗（zip 裡沒有，但這次簡報證明有用）

- 1600×900 固定舞台＋等比縮放、`data-notes` 講者備註、N／F 快捷鍵、網址 hash 頁碼
- 進場用 `translate` 不用 `transform`
- 提示詞做成對話框、截圖裁掉瀏覽器外框
- 問題頁與結果頁分開
- 步驟同步截圖檢視器、原生前端互動說明（模擬器、設定開關）
- 高卡片用圖示徽章填中段空白
- 比較表用白話＋比喻＋具體優點
- 嵌入網站只在前後頁載入；需要登入的產品改做離線 Demo（真程式＋fetch mock＋真實資料）
- 圖示離線內嵌、單一檔案建置、Playwright 逐頁截圖＋溢出偵測
- 中文孤字、標點懸掛、同排卡片標題對齊

## zip 裡缺的檔案

- 截圖列出但沒有 SKILL.md：**Better Colors**（OKLCH 色彩系統）、**Data Visualization**（圖表選擇與數據表達）。色彩部分以 impeccable／design-taste 的規則補；圖表規則目前只有 pptx-presentations 的「圖表不壓在文字下」與 workflow 的「真實資料、標來源」。如果之後拿到這兩份，補進 visual-system.md。
- 多份 skill 引用的子檔案不在 zip 內：hallmark／impeccable 的 references、figma-use 的 gotchas、break-ui 的 CATALOG 等。

## 衝突與裁決

| 衝突 | 裁決（簡報用） |
| --- | --- |
| Inter：多數禁用，brutalist 推薦 | 不預設。中文簡報以中文字體為主，Latin 選有個性的一款或用系統字。 |
| Lucide：minimalist／redesign／design-taste 不鼓勵 | 工具已有離線內嵌腳本所以保留可用，但整份只用一套、統一線條粗細；有品牌要求就換庫。 |
| 深色模式：design-taste 說必備，impeccable 說不能預設 | 依場景決定，整份鎖定一個主題。 |
| 米色／紙色背景：minimalist 推薦，impeccable／design-taste 禁 | 用中性或往主色偏的淡色；避免 `--paper`／`--cream` 式的暖米色預設。 |
| 動態量：gpt-taste 要求大量 GSAP，hallmark 要少於三種手法 | 簡報採克制：一種換頁、一種進場，加少數有用途的互動。 |
| 假外框：minimalist 允許 macOS 三點，hallmark／design-taste 禁 | 不畫假外框；裁乾淨的截圖＋細邊框。 |
| Eyebrow／章節編號：多份列為 AI 味 | 簡報有真實章節時允許（觀眾需要知道位置），但不做裝飾性編號、不每頁都放不同的小標。 |
| 頁碼計數器：scroll-craft 禁 | 簡報需要；放在角落低調的 HUD，不當作版面裝飾。 |
| 破折號：design-taste 全禁 | 中文「——」是正常標點可以用；但不要拿破折號當標題裝飾分隔。 |
| 卡片：impeccable 說卡片是偷懶 | 卡片數量依內容決定，能用列表／表格／流程就不用卡片，同排卡片不要三張一模一樣。 |
| 自己的「埋點規劃工具」簡報 | 它用了 Inter、JetBrains Mono、光球、格線背景、每頁 kicker。這些是使用者當時要求「更多互動與微互動」的結果，可接受；新簡報預設更克制，使用者要更多效果時再加。 |
