"""Inline assets/*.webp and the demo app into a single shareable HTML file."""
import base64, json, pathlib, re

here = pathlib.Path(__file__).parent
html = (here / "index.html").read_text(encoding="utf8")

def inline(match):
    data = base64.b64encode((here / match.group(1)).read_bytes()).decode()
    return "data:image/webp;base64," + data

out = re.sub(r"(assets/[\w-]+\.webp)", inline, html)

# Embed the demo app so slide 9 works from this single file (loaded via iframe srcdoc).
demo = (here / "demo" / "index.html").read_text(encoding="utf8")
demo_js = json.dumps(demo).replace("</", "<\\/")
out = out.replace("</body>", f"<script>window.__DEMO_HTML__ = {demo_js};</script>\n</body>", 1)
(here / "standalone.html").write_text(out, encoding="utf8")
print(f"standalone.html: {len(out) / 1e6:.1f} MB")
