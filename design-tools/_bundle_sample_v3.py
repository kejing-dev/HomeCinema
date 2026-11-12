"""Bundle .scratch/preview.html into one self-contained sample.html (runtime, script, assets inlined),
with a bilingual screen gallery (still screenshots of every required state) above the live preview.
Usage: python3 bundle_sample.py <scratch-dir> <out.html>"""
import base64, io, os, re, sys, json
from PIL import Image
S, OUT = sys.argv[1], sys.argv[2]
G = os.path.join(S, "review", "gallery")
h = open(os.path.join(S, "preview.html")).read()
css = open(os.path.join(S, "runtime/tokens.css")).read()
js = open(os.path.join(S, "runtime/components.js")).read()
pj = open(os.path.join(S, "preview.js")).read()
MIME = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg"}
def datauri(rel):
    return "data:" + MIME[rel.rsplit(".", 1)[1]] + ";base64," + base64.b64encode(open(os.path.join(S, rel), "rb").read()).decode()
h = re.sub(r'"(assets/[\w-]+\.(?:svg|png|jpg))"', lambda m: '"' + datauri(m.group(1)) + '"', h)
assert "assets/" not in pj
h = h.replace('<link rel="stylesheet" href="runtime/tokens.css">', "<style>" + css + "</style>")
h = h.replace('<script src="runtime/components.js" defer></script>', "<script>" + js.replace("</script>", "<\\/script>") + "</script>")
h = h.replace('<script src="preview.js" defer></script>', "<script>" + pj + "</script>")


def jpg(name, box=None, width=1400):
    im = Image.open(os.path.join(G, name)).convert("RGB")
    if box: im = im.crop(box)
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


ROOM = (60, 170, 2490, 1520)
fig = lambda src, zh, en, cls="": f'<figure class="{cls}"><img src="{src}" alt=""><figcaption><b>{zh}</b><br>{en}</figcaption></figure>'
R = os.path.join(S, "review", "renders")
STY = [("gallery", "白廊", "Gallery"), ("neon", "霓虹夜", "Neon Night"), ("wa", "和纸木格", "Washi & Wood"),
       ("portal", "全息光环", "Holo Portal"), ("moss", "苔石", "Moss & Stone"), ("cosmos", "星海", "Cosmos")]
I18N = json.loads(re.search(r'<script id="i18n-data" type="application/json">(.*?)</script>', open(os.path.join(S, "preview.html")).read(), re.S).group(1))
def rjpg(path, width=760):
    im = Image.open(path).convert("RGB"); im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=80, optimize=True); return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
gal = ['<section id="pv-gallery"><h1>私人影院 · 影院框 v3 <span>Home Cinema · Cinema Frame</span></h1>',
       '<p>门 B 改（第二轮）：六种当代风格的<b>真 3D 框</b>（GLB 模型，有纵深、材质和自发光灯光），每种风格自带灯光颜色和环境声。框中间是空的，套在你正在别的应用里看的播放器外面；不播放、不调暗房间、不控制别的应用。下面每种风格三张真渲染（正面 / 斜侧 / 近景），再往下是交互预览的状态截图和可点的预览。<br>'
       '<span class="en">Gate B rework, round 2: six contemporary real-3D frames (GLB with depth, materials and emissive theme lights), each with its own light colour and ambience. The hollow opening frames the player you already use in another app. Three real renders per style (front / angled / close-up), then preview state screens and the clickable preview.</span></p>']
for sid, zh, en in STY:
    meta = json.load(open(os.path.join(R, sid + ".json")))
    tex = ("，贴图 " + "、".join(meta["textures"])) if meta["textures"] else "，无贴图"
    gal.append(f'<h2>{zh} · {en}</h2><p class="meta">{I18N["zh"]["sd." + sid]} · <span class="en">{I18N["en"]["sd." + sid]}</span><br>'
               f'<span class="en">{meta["tris"]:,} 三角形 triangles{tex} · 材质 {len(meta["materials"])} 个 · GLB assets/frames/{sid}.glb</span></p><div class="g3">')
    for shot, czh, cen in (("front", "正面", "front"), ("angled", "斜侧", "angled"), ("detail", "近景", "close-up")):
        gal.append(fig(rjpg(os.path.join(R, f"{sid}-{shot}.jpg")), czh, cen))
    gal.append('</div>')
SC = [("a1-align.png", "对齐模式（白廊）", "Align mode (Gallery)"), ("a2-align-zh.png", "对齐模式（和纸木格，中文）", "Align mode (Washi & Wood, Chinese)"),
      ("b1-up.png", "1 · 灯亮着（霓虹夜）", "Lights up (Neon Night)"), ("b2-opening.png", "2 · 开场 4 秒：框灯渐暗", "Opening, 4 s: frame lights fade"),
      ("b3-showing.png", "3 · 放映中：框灯 12 %", "Showing: frame lights 12 %"), ("b4-closing.png", "4 · 散场 6 秒：框灯回来", "Closing, 6 s: frame lights return"),
      ("b5-portal-showing.png", "放映中（全息光环）", "Showing (Holo Portal)"), ("b6-cosmos-showing.png", "放映中（星海，中文）", "Showing (Cosmos, Chinese)")]
PN = [("crop-p1-show.png", "控制面板 · 选风格", "Controls · pick a style"), ("crop-p2-settings.png", "设置：睡眠计时、环境声、语言、退出", "Settings: sleep timer, ambience, language, exit"),
      ("crop-p3-settings-zh.png", "设置（中文）", "Settings (Chinese)")]
gal += ['<h2>对齐与开场 / 散场 · Alignment &amp; show states</h2><p class="en">房间（透视）亮度不变，变的只是框自己的灯。The room is unchanged; only the frame’s own lights change.</p><div class="g2">']
gal += [fig(jpg(f, ROOM, 1100), zh, en) for f, zh, en in SC]
gal += ['</div><h2>控制面板与设置 · Controls &amp; settings</h2><div class="g3">']
gal += [fig(jpg(f, None, 600), zh, en, "pn") for f, zh, en in PN]
gal += ['</div><h2>交互预览 · Live preview</h2></section>']
style = ("<style>#pv-gallery{max-width:1480px;margin:0 auto;padding:24px 32px;font:15px/1.6 system-ui,-apple-system,'PingFang SC',sans-serif;color:#1d1d1f}"
         "#pv-gallery h1{font-size:26px}#pv-gallery h1 span{font-size:16px;color:#777;font-weight:400;margin-left:8px}"
         "#pv-gallery h2{font-size:18px;margin:28px 0 10px;border-bottom:1px solid #ddd;padding-bottom:4px}.en{color:#666;font-size:13px}"
         "#pv-gallery .g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}#pv-gallery .g3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}"
         "#pv-gallery figure{margin:0}#pv-gallery img{width:100%;border-radius:10px;display:block;box-shadow:0 1px 4px rgba(0,0,0,.15)}"
         "#pv-gallery figcaption{font-size:13px;color:#444;margin-top:6px}#pv-gallery .meta{margin:0 0 8px;font-size:14px}</style>")
h = h.replace("<body>", "<body>" + style + "".join(gal), 1)
open(OUT, "w").write(h)
print(OUT, len(h) // 1024, "KB")
