# 埋點規劃工具

這個專案是 Figma 埋點分析工具。使用者貼上 Figma 連結後，可以匯入 Page、選擇分析模型，並產出第一階段埋點建議與 Excel。

## Phase 1 / Phase 2

- Phase 1 保存於 Git tag `phase-1`，指向 `de9c34a`，保留原本的整頁分析版本。
- Phase 2 在 `codex/phase-2-directed-analysis` 分支開發，新增「分析需求（選填）」欄位。
- 需求留白時執行原本的完整分析；輸入「幫我將逆向流程篩選出來」等需求後，會重新讀取選定 Page 的最新 Figma 內容，由 AI 判斷符合需求的行為與埋點。
- 指定需求分析不會自動補足整頁事件，也不會因為回傳零筆而產生備援事件；沒有設計依據時顯示「目前從此 Figma 稿件無法確認。」。
- 每次 request 只包含當前需求與最新選定範圍，不加入前次結果或對話歷史。切換專案、來源或 Page 時清空需求；一般瀏覽器重新整理回首頁並清空本次記錄。
- OAuth 授權跳轉期間只暫存原需求、Page 與模型，回到相同專案和連結後續接並刪除暫存；一般重新整理不保留此資料。
- AI 或 Figma 服務未完成時，指定需求分析顯示錯誤並保留輸入，供使用者重試。

執行 API 回歸測試：

```bash
npm test
```

測試使用合成 Figma 節點與模擬 AI 回應，驗證需求傳遞、資料隔離、重新讀取、零筆結果、取消流程與錯誤行為；不呼叫真實 Figma 或付費模型。

## Local Development

```bash
npm ci
cp .env.example .env.local
npm run dev
```

`.env.local` 需要設定：

- `FIGMA_OAUTH_CLIENT_ID`
- `FIGMA_OAUTH_CLIENT_SECRET`
- `FIGMA_OAUTH_COOKIE_SECRET`
- `FIGMA_OAUTH_REDIRECT_URI`
- `FIGMA_OAUTH_SCOPES`，預設 `file_content:read`
- `FIGMA_OAUTH_ENABLED=true`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`，預設 `gpt-5.6-luna`

若 Figma OAuth 尚未通過審核，管理者可暫時設定 `FIGMA_ACCESS_TOKEN` 作為平台備援；這不會出現在使用者介面，也不需要使用者理解 token。

## Cloudflare Workers Deployment

這個 repo 已包含 `wrangler.jsonc`。在 Cloudflare Workers & Pages 連接 GitHub repo 後，`main` 分支會自動 build 並部署到 Cloudflare Workers。

Cloudflare build settings 建議使用：

- Build command: `npm run build`
- Deploy command: `npx wrangler deploy`
- Root directory: `/`

Worker runtime 需要在 Cloudflare 的 Variables and Secrets 新增：

- `FIGMA_OAUTH_CLIENT_ID`
- `FIGMA_OAUTH_CLIENT_SECRET`
- `FIGMA_OAUTH_COOKIE_SECRET`
- `FIGMA_OAUTH_REDIRECT_URI`
- `FIGMA_OAUTH_SCOPES`
- `FIGMA_OAUTH_ENABLED`
- `OPENAI_API_KEY`

`FIGMA_ACCESS_TOKEN` 只作為管理者備援 secret，不是一般使用者授權流程。

若要在模型選單使用 Gemini，另外新增：

- `GEMINI_API_KEY`

若要本機手動部署，可先登入 Wrangler 後執行：

```bash
npm run deploy:cloudflare
```

## Notes

- 不要把 Figma token 或 OpenAI API key 寫進程式碼或 commit。
- `GEMINI_API_KEY` 是選用模型來源；沒有設定時，Gemini 選項會提示需要新增部署環境變數。
- 主要分析模型預設為 OpenAI 的 `gpt-5.6-luna`。
- 目前保留 `.openai/hosting.json`，因此原本的 Sites 測試站仍可繼續作為內部測試版使用。
