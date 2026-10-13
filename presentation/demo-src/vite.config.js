// Builds a self-contained demo of the real app (app/page.tsx + app/globals.css)
// with every /api call answered by mock-api.js, for offline presentation demos.
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/postcss";
import { defineConfig } from "vite";
import { DEMO_FIGMA_URL } from "./mock-data.js";

const here = path.dirname(fileURLToPath(import.meta.url));

// Pre-fill the Figma link field so the presenter only has to click.
const prefillFigmaUrl = {
  name: "demo-prefill-figma-url",
  transform(code, id) {
    if (!id.endsWith(path.join("app", "page.tsx"))) return null;
    const literal = JSON.stringify(DEMO_FIGMA_URL);
    return code
      .replace('const [draftFigmaUrl, setDraftFigmaUrl] = useState("");', `const [draftFigmaUrl, setDraftFigmaUrl] = useState(${literal});`)
      .replaceAll('setDraftFigmaUrl("")', `setDraftFigmaUrl(${literal})`);
  },
};

export default defineConfig({
  root: here,
  base: "./",
  plugins: [prefillFigmaUrl, react()],
  css: { postcss: { plugins: [tailwindcss({ base: path.join(here, "../../app") })] } },
  resolve: {
    alias: {
      tailwindcss: path.join(here, "node_modules/tailwindcss/index.css"),
      react: path.join(here, "node_modules/react"),
      "react-dom": path.join(here, "node_modules/react-dom"),
    },
  },
  server: { fs: { allow: [path.join(here, "../..")] } },
  build: { outDir: path.join(here, "../demo"), emptyOutDir: true, assetsInlineLimit: 100000000, cssCodeSplit: false },
});
