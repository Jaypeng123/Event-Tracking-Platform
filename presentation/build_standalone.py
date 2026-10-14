"""Inline assets/*.webp and the demo app into single shareable HTML files.

index.html     -> standalone.html            (presentation deck)
portfolio.html -> portfolio-standalone.html  (case study page)
"""
import base64, json, pathlib, re

here = pathlib.Path(__file__).parent
demo = (here / "demo" / "index.html").read_text(encoding="utf8")
demo_js = json.dumps(demo).replace("</", "<\\/")

def inline(match):
    data = base64.b64encode((here / match.group(1)).read_bytes()).decode()
    return "data:image/webp;base64," + data

for src, dst in [("index.html", "standalone.html"), ("portfolio.html", "portfolio-standalone.html")]:
    html = (here / src).read_text(encoding="utf8")
    out = re.sub(r"(assets/[\w-]+\.webp)", inline, html)
    # Embed the demo app so it works from this single file (loaded via iframe srcdoc).
    out = out.replace("</body>", f"<script>window.__DEMO_HTML__ = {demo_js};</script>\n</body>", 1)
    (here / dst).write_text(out, encoding="utf8")
    print(f"{dst}: {len(out) / 1e6:.1f} MB")
