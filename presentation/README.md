# 埋點規劃工具 · 簡報與作品集（HTML）

## 作品集（案例研究長頁）
- `portfolio.html`：作品集版本，長頁捲動的案例研究（摘要 → 背景 → 定位 → 解決方案＋互動 Demo → 五個關鍵決策 → 開發過程 → 成果 → 反思）
- `portfolio-standalone.html`：單一檔案版，圖片與 Demo 都已內嵌

## 設計分享簡報

- `index.html`：簡報本體（圖片在 `assets/`）
- `standalone.html`：單一檔案版（圖片已內嵌），方便直接分享
- 修改 `index.html` 或 `portfolio.html` 後，執行 `python3 build_standalone.py` 會重新產生兩個單一檔案版

## 操作
- `←` / `→`、空白鍵、滑動：換頁　`F`：全螢幕　`N`：講者備註（取自原 PPT）
- 點擊截圖可放大檢視
- 第 9 頁是產品 Demo（全螢幕）：使用真實的 `app/page.tsx` 介面，但所有 API 都換成假資料，離線也能操作
  - 流程：前往埋點規劃 → 輸入專案名稱 → Figma 連結已預先帶入 → 匯入 → 選擇 Page → 分析頁面內容（約 3 秒後出現結果）
  - 下方浮動列可換頁、「重新開始 Demo」（清空資料回到首頁）或開啟正式網站

## Demo 重新產生
App 介面或假資料（`demo-src/mock-data.js`）改動後：

```bash
cd demo-src && npm install && npm run build   # 產生 ../demo/index.html
cd .. && python3 build_standalone.py          # 更新 standalone.html
```

## HTML 簡報 Skill（`skills/html-deck/`）
把這份簡報的做法與 `AI_Skill.zip` 裡 60 份設計 skill 的規則，整理成可重複使用的簡報製作 skill。
- `SKILL.md`：主流程與硬規則；`references/` 放細節（內容流程、視覺系統、動態、素材與嵌入、QA、來源對照）
- `assets/template.html`：簡報骨架；`scripts/`：圖示內嵌、單檔建置、逐頁截圖 QA
- 安裝：把整個 `html-deck` 資料夾放到 `~/.claude/skills/`（Claude Code）或對應工具的 skills 目錄；`html-deck.zip` 是同內容的壓縮檔
