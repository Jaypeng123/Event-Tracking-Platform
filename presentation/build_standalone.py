"""Inline assets/*.webp into a single shareable HTML file."""
import base64, pathlib, re

here = pathlib.Path(__file__).parent
html = (here / "index.html").read_text(encoding="utf8")

def inline(match):
    data = base64.b64encode((here / match.group(1)).read_bytes()).decode()
    return "data:image/webp;base64," + data

out = re.sub(r"(assets/[\w-]+\.webp)", inline, html)
(here / "standalone.html").write_text(out, encoding="utf8")
print(f"standalone.html: {len(out) / 1e6:.1f} MB")
