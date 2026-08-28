# 埋點規劃工具

這個專案是 Figma 埋點分析工具。使用者貼上 Figma 連結後，可以匯入 Page、選擇分析模型，並產出第一階段埋點建議與 Excel。

## Local Development

```bash
npm ci
cp .env.example .env.local
npm run dev
```

`.env.local` 需要設定：

- `FIGMA_ACCESS_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`，預設 `gpt-5.6-luna`

## Cloudflare Workers Deployment

這個 repo 已包含 `wrangler.deploy.jsonc` 與 GitHub Actions。推到 GitHub 後，`main` 分支會自動 build 並部署到 Cloudflare Workers。

GitHub repo 需要新增以下 Secrets：

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `FIGMA_ACCESS_TOKEN`
- `OPENAI_API_KEY`

Cloudflare API token 需要能部署 Workers。若要手動部署，可先登入 Wrangler 後執行：

```bash
npm run deploy:cloudflare
```

## Notes

- 不要把 Figma token 或 OpenAI API key 寫進程式碼或 commit。
- `GEMINI_API_KEY` 是選用 fallback，主要分析模型預設為 OpenAI 的 `gpt-5.6-luna`。
- 目前保留 `.openai/hosting.json`，因此原本的 Sites 測試站仍可繼續作為內部測試版使用。
