# 埋點規劃工具

這個專案是 Figma 埋點分析工具。使用者貼上 Figma 連結後，可以匯入 Page、選擇分析模型，並產出第一階段埋點建議與 Excel。

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
