// Inline the built JS/CSS into demo/index.html so it also works over file://.
import fs from "node:fs";
import path from "node:path";

const out = path.resolve("../demo");
let html = fs.readFileSync(path.join(out, "index.html"), "utf8");
html = html.replace(/<link rel="stylesheet"[^>]*href="\.\/(assets\/[^"]+)"[^>]*>/, (_, f) =>
  `<style>${fs.readFileSync(path.join(out, f), "utf8")}</style>`);
html = html.replace(/<script type="module"[^>]*src="\.\/(assets\/[^"]+)"[^>]*><\/script>/, (_, f) =>
  `<script type="module">${fs.readFileSync(path.join(out, f), "utf8").replaceAll("</script", "<\\/script")}</script>`);
fs.writeFileSync(path.join(out, "index.html"), html);
fs.rmSync(path.join(out, "assets"), { recursive: true, force: true });
console.log(`demo/index.html: ${(html.length / 1024).toFixed(0)} KB`);
