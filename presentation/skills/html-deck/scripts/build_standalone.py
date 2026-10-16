"""把簡報的本機圖片（與可選的 demo 頁）內嵌成單一 HTML，可直接寄送、離線開啟。

用法：python3 build_standalone.py index.html [standalone.html] [--demo demo/index.html]
- 內嵌所有 src/href/data-zoom/url() 中引用的相對路徑圖片（webp/png/jpg/jpeg/gif/svg）
- --demo：把 demo 頁存成 window.__DEMO_HTML__，簡報端用 iframe.srcdoc 載入
"""
import base64, json, mimetypes, pathlib, re, sys

args = sys.argv[1:]
demo = None
if "--demo" in args:
    i = args.index("--demo"); demo = args[i + 1]; del args[i:i + 2]
src = pathlib.Path(args[0]); dst = pathlib.Path(args[1]) if len(args) > 1 else src.with_name("standalone.html")
root = src.parent
html = src.read_text(encoding="utf8")
cache = {}

def data_uri(rel):
    if rel not in cache:
        p = (root / rel)
        if not p.is_file():
            print("missing:", rel); return rel
        mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        cache[rel] = f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    return cache[rel]

pat = re.compile(r"""(?<![\w:/.-])((?:\./)?[\w./-]+\.(?:webp|png|jpe?g|gif|svg))(?=["')\s])""", re.I)
out = pat.sub(lambda m: data_uri(m.group(1)) if not m.group(1).startswith(("http", "//")) else m.group(1), html)
if demo:
    demo_js = json.dumps((root / demo).read_text(encoding="utf8")).replace("</", "<\\/")
    out = out.replace("</body>", f"<script>window.__DEMO_HTML__ = {demo_js};</script>\n</body>", 1)
dst.write_text(out, encoding="utf8")
print(f"{dst}: {len(out) / 1e6:.1f} MB, {len(cache)} images inlined")
