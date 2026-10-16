# 來源對照：每份 skill 對簡報的價值、採用了什麼、刻意不採用什麼

整理自 `AI_Skill.zip` 全部 60 份 Markdown（58 份 skill＋2 份簡報流程筆記），以及一份實際 HTML 簡報與作品集頁的製作經驗。調整這份 skill 前先讀這裡。

適用度：**高**＝核心規則來源；**中**＝部分規則可用；**低**＝只取一兩個觀念；**不適用**＝領域不同。

## 簡報設計（5）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| 簡報製作流程與提示詞 | 高 | workflow.md | 需求表、六步驟與每步檢查、不得捏造、交付前檢查 | — |
| Codex_PPT_Skills | 高 | SKILL.md §0 | 三條路線；HTML 路線要有講者模式、16:9 鎖定、鍵盤翻頁、計時器 | 指定 Reveal.js／Tailwind |
| codex-ppt（SKILL.md） | 中 | workflow.md 確認點 | 大綱與樣張確認點、可見進度、交付時說明限制 | 整頁生成圖片、子代理分派流程（HTML 路線不需要） |
| ppt-visual | 高 | visual-system.md §4、§5 | 版型類型（封面、大字、三欄、分割、數據、時間軸、比較、流程、引言）、一頁一個概念、視覺層級、三分法、對比與對齊、深色背景適合暗場、投影前實測 | 固定配色模板與字體配對（例如 Inter）作為預設 |
| pptx-presentations | 高 | diagrams-data.md §5、visual-system.md §1 | 先依主題與品牌選色並說明理由、圖表與文字並排、不把圖表壓在文字下方、極端字級對比 | 只能用 web-safe 字體（HTML 可內嵌） |

## 視覺設計與排版（6）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| better-typography | 高 | visual-system.md §3 | 依角色設定行高、≥3 行至少 1.4、字型 ≤ 3、配對要有對比、balance／pretty、tabular-nums、行長上限、字重下限、`lang` 屬性 | 表單 16px 防縮放等網頁專用規則 |
| make-a-type-scale | 高 | visual-system.md §3 | 模數比例選擇、行高遞減公式、>120px 收到 1.05、字級要算不要猜 | Figma 變數與規格表建置流程 |
| diagram-design | 高 | diagrams-data.md | 先刪減、密度 4/10、節點 ≤ 9、連線 ≤ 12、強調色 ≤ 2、正交連線與標籤規則、圖表類型選擇、無障礙 SVG、匯入時只取內容 | 指定字體組合（Instrument Serif／Geist） |
| high-end-visual-design | 中 | visual-system.md、motion.md | 大量留白、自訂 easing、只動 transform／opacity、模糊只用在固定層 | 雙層外框卡片、按鈕內嵌圓形圖示、每個元素都要進場動畫、禁用所有 Lucide |
| theme-factory | 中 | visual-system.md §2 | 主題以配色＋字體組合呈現、讓使用者選或自訂 | 10 套固定主題 |
| canvas-design | 低 | visual-system.md §1 | 先命名設計理念再做視覺 | 輸出 PNG／PDF 海報 |

## 動態效果與互動（8）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| animate | 高 | motion.md | 先判斷要不要動、六種用途、工具選擇、easing 數值、時長表、不用 scale(0)、可中斷、reduced motion 與 hover 限制 | Motion 函式庫細節 |
| design-motion-principles | 高 | motion.md §1、§6 | 依專案類型權衡（Emil 克制／Jakub 精緻／Jhey 玩心）、進場與離場、fill-mode、AI 味動態清單 | 稽核報告輸出格式 |
| find-animation-opportunities | 高 | motion.md §2 | 大量否決候選、頻率關卡、資料不為裝飾而動 | 程式碼掃描流程 |
| review-animations | 中 | qa.md | 審查用的十項標準與補救優先順序 | — |
| improve-animations | 低 | qa.md | 先偵查再審查、計畫要自足 | 寫計畫檔流程 |
| animation-vocabulary | 中 | motion.md §5 | 動態名詞（方向感轉場、前後滑桿、線條繪製、數字跳動、交叉淡入） | — |
| scroll-craft | 高 | workflow.md §1、§2、visual-system.md §6 | 先寫情緒曲線再選手法、唯一高峰與前面的安靜、相鄰不重複、結尾要收住、不把字烘焙進圖、不捏造數據、遮罩只放在文字下方、通用節拍法 | 捲動驅動引擎、影片編碼、指紋登記 |
| imagegen-frontend-web | 高 | visual-system.md §1、§4、§7 | 構圖錨點與背景模式輪替、至少一頁滿版與一頁安靜頁、唯一記憶點、敘事主軸、調色紀律、允許與禁止的漸層、文案與假品牌禁用、數據圖表節制 | 每區一張生成圖的輸出規定、轉換漏斗 |

## AI 圖片與影片生成（4）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| prompt-images | 中 | assets-embed-build.md §5 | 完整句子提示、攝影語彙、說清楚要保留什麼、一致性、長寬比與解析度 | 圖內文字技巧（簡報字一律用 HTML） |
| prompt-videos | 中 | assets-embed-build.md §5 | 鏡頭語言、「沒有其他動作」、無字幕、首尾影格內插 | 對白與音效生成 |
| ai-image-generation | 低 | assets-embed-build.md §5 | 可選的生成後端、去背、放大 | 綁定特定 CLI 與模型清單 |
| ai-video-generation | 低 | assets-embed-build.md §5 | 產品旋轉、靜止鏡頭的短循環 | 綁定特定 CLI 與模型清單 |

## 動態視覺素材與創意程式（3）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| algorithmic-art | 中 | visual-system.md §6 | 固定 seed、配色取自系統、可重現 | 另寫設計哲學檔 |
| hyperframes | 中 | motion.md §4 | 每個步驟狀態可直接跳到、簡報需要的功能清單（備註、分段揭示、跳頁）、預設 16:9 | 依賴其執行環境與 CLI |
| text-to-lottie | 低 | assets-embed-build.md §5 | 第 0／中／末格檢查、非線性 easing | 指定播放器專案與開發伺服器 |

## UI 視覺品質與設計優化（11）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| hallmark | 高 | workflow.md §0、visual-system.md | 開工前問受眾／用途／語氣、使用者說「直接做」時寫出推論、結構多樣性、不捏造數據、tokens 鎖定、不手繪假外框、標題不用斜體、自我評分後再交付、豐富度階梯（文字→CSS→SVG→生成圖→函式庫→Lottie） | 21 套主題與專案記錄檔 |
| impeccable | 高 | visual-system.md §1、§2、§7、motion.md §4 | 場景決定深淺色、色彩策略四種、反射檢查、對比數值、有色背景不用灰字、標題字距下限、卡片是偷懶的答案、絕對禁止清單、揭示不能是內容唯一出現方式 | 腳本與子指令系統 |
| design-taste-frontend | 高 | visual-system.md §4、§7 | 先寫一行設計判讀、三個刻度、eyebrow 節制、版型家族不重複、zigzag 上限、bento 格數＝內容數、長列表換元件、配色與形狀鎖定、引言 ≤ 3 行、文案自我檢查 | React／Next 技術棧規定、破折號全面禁用（見衝突） |
| frontend-design | 中 | visual-system.md §1 | 選一個明確語氣、說得出記憶點、強勢主色勝過平均分配 | — |
| better-layout | 高 | visual-system.md §2 | 用空間分組、組間距 ≥ 2 倍、對齊共用邊、依重要性排序 | RTL、斷點規則 |
| better-ui | 高 | visual-system.md §2、§5 | 同心圓角、光學對齊、陰影與邊框分工、圖示線條配字重、圖片外框數值 | — |
| make-interfaces-feel-better | 高 | qa.md §3 | 快速／完整審查模式、考慮過但不改、未驗證項目要列出 | — |
| redesign-existing-projects | 中 | qa.md、visual-system.md | 先掃描再診斷再修、修正優先順序（字體→配色→互動→版面→元件→狀態）、文案禁用詞 | 網站專用項目（SEO、404、cookie） |
| minimalist-ui | 中 | visual-system.md | 極簡方向的配色與間距參考 | 允許 macOS 假視窗外框、指定字體清單 |
| gpt-taste | 低 | visual-system.md §7 | 標題 ≤ 2–3 行、禁用假中繼標籤 | 強制 GSAP 與隨機化流程 |
| industrial-brutalist-ui | 低 | visual-system.md §1 | 選定一種風格就整份貫徹 | 掃描線、ASCII 框、假型號字串 |

## UI 審查、測試與品質驗證（5）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| better-interface | 高 | qa.md §3、§5 | 審查順序、證據要求、單一嚴重度量表、焦點框與觸控目標、圖示與動畫細節 | Figma 卡片標註 |
| superfuture-design-review | 高 | qa.md §3 | 量測而不是憑感覺、阻擋／重要／打磨三級、每項附具體修法、先講少數關鍵問題、最後列優點 | — |
| break-ui | 中 | qa.md §2 | 最壞但真實的資料、0／1／大量、單複數 | 開發用切換器 |
| design-critique | 中 | qa.md §4、workflow.md §2 | 依階段給回饋、我喜歡／我希望／如果、觀察→影響→建議、簡報者先說明想要的回饋 | 會議主持細節 |
| web-interface-guidelines | 低 | qa.md | 可選的線上檢查清單 | 需連網抓規則 |

## Figma 設計與開發交付（5）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| figma-use | 中 | assets-embed-build.md §3 | 網址判斷檔案類型、小步執行、截圖倍率、Slides 的限制 | 元件與變數建置細節 |
| figma-generate-design | 低 | assets-embed-build.md §3 | 先找既有元件與變數、逐區截圖驗證 | 設計系統組裝流程 |
| image-to-code | 高 | assets-embed-build.md §4 | 從圖抽取的清單與順序、防走樣、不清楚就取得新圖而不是裁小圖 | 一律先生成圖片 |
| design-handoff | 低 | assets-embed-build.md | 狀態與動態規格表（可作為技術分享的附錄頁） | — |
| agentation | 不適用 | — | — | 開發工具列 |

## 響應式、介面狀態與原型（3）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| ui-state-expander | 中 | visual-system.md §5、assets-embed-build.md §4 | 非理想狀態清單（空、載入、錯誤、權限、極長內容） | — |
| desktop-to-mobile | 中 | assets-embed-build.md §4、§9 | 390px 基準、邊距、字級換算、觸控目標 | Figma frame 產生流程 |
| wireframe-prototyping | 低 | workflow.md | 依階段選擬真度 | 測試計畫範本 |

## 設計探索、產品策略與協作（3）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| design-workshop-facilitation | 中 | workflow.md §1 | 工作坊簡報骨架、時間 20–30% 緩衝、每 60–90 分鐘休息、議程與產出 | 場地與物資 |
| ai-native-product-designer | 中 | workflow.md §1 | 設計案例的敘事（問題→選項→驗證→決策→以行為改變衡量的成果） | 職級評分表 |
| design-an-interface | 低 | workflow.md | 先產出多個差異大的方向再比較（可用在風格樣張） | API 設計流程 |

## iOS／Android 原生介面（7）

| 檔案 | 適用度 | 採用到 | 內容 | 不採用 |
| --- | --- | --- | --- | --- |
| apple-design | 中 | motion.md、qa.md | 可中斷、進出同路徑、避免滿版移動背景與約 0.2Hz 慢速循環、reduced transparency、字距隨字級、尋路（我在哪、能去哪、怎麼離開）→ 進度與章節導覽 | 手勢物理細節 |
| imagegen-frontend-mobile | 中 | visual-system.md §5、assets-embed-build.md §4 | 手機畫面用一致裝置框、四周留白均等、內容為主、圖上文字加遮罩、畫面字不能太小 | 只生成圖片 |
| apple-hig-designer | 低 | assets-embed-build.md §4 | iOS 字級、對比 7:1 目標 | SwiftUI 元件 |
| android-design-guidelines | 低 | assets-embed-build.md §4 | Material 字級、觸控 48dp | Compose 實作 |
| apple-ui-designer | 低 | visual-system.md | 有疑慮就刪除、分隔線或間距擇一 | — |
| ios-design | 不適用 | — | — | SwiftUI 架構規則 |
| mobile-android-design | 不適用 | — | — | Compose 範例 |

## zip 裡缺的檔案

- 分類表列出但沒有附檔：**Better Colors**（OKLCH 色彩系統）、**Data Visualization**（圖表選擇）。色彩以 impeccable／design-taste-frontend／imagegen-frontend-web 補；圖表以 diagram-design／pptx-presentations 補（見 diagrams-data.md）。拿到原檔後再補強。
- 多份 skill 引用的子檔案不在 zip 內（hallmark、impeccable、figma-use、break-ui 等的 references）。

## 來自實作經驗（zip 沒有，但實際做過一次證明有用）

- 固定 16:9 舞台＋等比縮放、`data-notes` 講者備註、N／F 快捷鍵、網址 hash 頁碼、列印每頁一張
- 進場用 `translate` 不用 `transform`
- 對話氣泡呈現原文、截圖裁掉瀏覽器外框
- 結果頁與問題頁分開
- 步驟同步畫面檢視器、原生前端互動說明元件
- 卡片拉高時用圖示徽章填中段空白
- 比較表用白話＋比喻＋具體差異
- 嵌入網站只在前後頁載入；需要登入的產品改做離線 Demo
- 圖示離線內嵌、單一檔案建置、Playwright 逐頁截圖＋溢出偵測
- 中文孤字、標點懸掛、同排標題對齊

## 衝突與裁決

| 衝突 | 裁決（簡報用） |
| --- | --- |
| Inter：多數禁用，少數允許 | 不預設；中文簡報以中文字體為主，Latin 選有個性的一款或用系統字。 |
| Lucide：多份不鼓勵 | 工具附離線內嵌腳本所以可用；整份只用一套、統一線條粗細，有品牌規範就換。 |
| 深色模式：有的說必備，有的說不能預設 | 由播放場景決定，整份鎖定。 |
| 米色背景：minimalist 推薦，impeccable／design-taste 禁 | 不當預設；品牌是暖色時用強調色與圖片帶出。 |
| 動態量：gpt-taste 要大量 GSAP，hallmark 要少於三種手法 | 依簡報類型決定（motion.md §1），預設克制。 |
| 假外框：minimalist 允許，hallmark／design-taste 禁；imagegen-frontend-mobile 要求手機框 | 網頁畫面不畫假瀏覽器列；手機 App 畫面可用一致的簡潔裝置框。 |
| Eyebrow／章節編號：多份列為 AI 味 | 簡報有真實章節時可用（觀眾需要知道位置），統一一種寫法；不做裝飾性編號。 |
| 頁碼：scroll-craft 禁計數器 | 簡報需要頁碼與進度，放在角落低調的 HUD，不當版面裝飾。 |
| 破折號：design-taste 全禁 | 中文「——」是正常標點可用；不拿破折號當標題裝飾分隔。 |
| 卡片：impeccable 說是偷懶的答案 | 依內容決定；能用列表、表格、流程就不用卡片；並排卡片不要長得一模一樣。 |
| 每個元素都要進場動畫（high-end、minimalist）vs 靜態文字不該動（design-motion-principles） | 簡報採後者：只有依序揭示有意義時才動，標題與內文不動。 |
| 襯線：design-taste 不鼓勵，minimalist／redesign 用於編輯風 | 預設無襯線；方向明確是編輯、人文、典藏時才用（含中文明體）。 |
| 一律先生成圖片再做（image-to-code） | 有真實素材時以真實素材為準；生成圖只用在探索方向或氛圍素材。 |
