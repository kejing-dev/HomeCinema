"""Revision 4 (ambient): bundle .scratch/preview.html into one self-contained sample.html (runtime, script, assets inlined),
with the round-4 gallery above the live preview: one-line intro, "only look at these" list, the 5 ambient styles
(3 renders + peripheral view + ambient numbers each), before/after peripheral comparison, state screens, panels, gate-B questions.
Usage: python3 bundle_sample.py <scratch-dir> <out.html>"""
import base64, io, os, re, sys, json
from PIL import Image
S, OUT = sys.argv[1], sys.argv[2]
G = os.path.join(S, "review", "gallery"); R = os.path.join(S, "review", "renders")
h = open(os.path.join(S, "preview.html")).read()
css = open(os.path.join(S, "runtime/tokens.css")).read()
js = open(os.path.join(S, "runtime/components.js")).read()
pj = open(os.path.join(S, "preview.js")).read()
MIME = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
def datauri(rel):
    return "data:" + MIME[rel.rsplit(".", 1)[1]] + ";base64," + base64.b64encode(open(os.path.join(S, rel), "rb").read()).decode()
h = re.sub(r'"(assets/[\w-]+\.(?:svg|png|jpg|webp))"', lambda m: '"' + datauri(m.group(1)) + '"', h)
assert "assets/" not in pj
h = h.replace('<link rel="stylesheet" href="runtime/tokens.css">', "<style>" + css + "</style>")
h = h.replace('<script src="runtime/components.js" defer></script>', "<script>" + js.replace("</script>", "<\\/script>") + "</script>")
h = h.replace('<script src="preview.js" defer></script>', "<script>" + pj + "</script>")


def jpg(path, box=None, width=1400, q=80):
    im = Image.open(path).convert("RGB")
    if box: im = im.crop(box)
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


fig = lambda src, zh, en, cls="": f'<figure class="{cls}"><img src="{src}" alt=""><figcaption><b>{zh}</b><br><span class="en">{en}</span></figcaption></figure>'
I18N = json.loads(re.search(r'<script id="i18n-data" type="application/json">(.*?)</script>', open(os.path.join(S, "preview.html")).read(), re.S).group(1))
AC = json.load(open(os.path.join(R, "ambient-check.json")))
STY = [("walnut", "胡桃画廊", "Walnut Gallery", "画廊式的深框：胡桃木四边、暗亚麻衬边、一道 6 mm 黄铜细线，炭灰石灰墙；下沿一条胡桃搁板，放陶瓶和几本画册。",
        "Gallery shadow-box: walnut frame, dark linen slip, a 6 mm brass hairline on a charcoal limewash wall; a walnut ledge with a stoneware vase and art books."),
       ("beton", "清水混凝土", "Béton", "像在一面木模清水混凝土墙上开了一扇深窗：14 cm 斜角窗口、对拉螺栓孔；右下一块混凝土小台，放一块石灰华叠石。",
        "A deep window cut into board-formed concrete: 14 cm chamfered reveal, tie holes; a concrete stub shelf with a travertine pebble stack."),
       ("linen", "亚麻软包", "Linen Room", "精品酒店影音室的做法：深灰米色织物吸音板、胡桃收边，收边下藏一条暖色灯线；两侧小搁板放亚麻罩台灯和书。",
        "Boutique-hotel media room: dark greige fabric acoustic panels, walnut trim with a hidden warm LED line; small ledges with a linen-shade lamp and books."),
       ("slats", "烟熏橡木格栅", "Smoked Oak", "最像家庭影院的一款：黑毡上的竖向烟熏橡木格栅、哑光黑钢窗框，开口四周一层很淡的中性屏后光（bias light）。",
        "The most home-theatre one: vertical smoked-oak slats on black felt, a matte black steel sight frame and a faint neutral bias light around the opening."),
       ("bronze", "青铜细框", "Bronze Line", "几乎看不见的一款：黑亚麻博物馆卡纸加 3 cm 做旧青铜细框，没有摆件、不配声音。",
        "Almost not there: a black linen museum mat and a 3 cm darkened-bronze frame. No props, no sound.")]
OLD = [("neon", "霓虹夜（上一轮）", "Neon Night (round 3)"), ("portal", "全息光环（上一轮）", "Holo Portal (round 3)"), ("gallery", "白廊（上一轮）", "Gallery (round 3)")]

def ac_line(s):
    a = AC[s]; sh, up = a["showing"], a["up"]
    return (f'放映时框的平均明度 L* {sh["frame"]["L"]}（画面 {sh["player"]["L"]}，房间 {sh["room"]["L"]}），平均彩度 C* {sh["frame"]["C"]}，最亮 5% 的 L* {sh["frame"]["Lp95"]}；'
            f'灯亮时 C* {up["frame"]["C"]} · {"不抢眼 ✓" if a["pass"] else "抢眼 ✗"}')

gal = ['<section id="pv-gallery">',
       '<h1>私人影院 · 影院框 第 4 版 <span>Home Cinema · Cinema Frame · round 4 (ambient)</span></h1>',
       '<p class="lead"><b>一句话：</b>你照常在 PICO Video、浏览器或系统播放器里看片，私人影院在那个窗口四周补一面安静的「墙」——胡桃、混凝土、亚麻、橡木格栅或青铜细框——让画面周围暗下来、有质感，但不抢画面。<br>'
       '<b>怎么用：</b>① 选一种墙面；② 把播放器拖进框中间（第一次会提示）；③ 开始播放，框上的微光自己暗下去，停了再亮回来。<br>'
       '<span class="en">You keep watching in your usual player; Home Cinema adds a quiet wall treatment around that window. Pick a style, drag your player into the opening once, press play: the frame’s soft light fades on its own and returns when you stop.</span></p>',
       '<div class="changed"><h2>本次只看这几处 · What changed this round</h2><ol>'
       '<li><b>六种风格全换成五种「退后」的墙面</b>：胡桃画廊、清水混凝土、亚麻软包、烟熏橡木格栅、青铜细框。去掉了霓虹、全息、星海这类发光高饱和的，也去掉了圆胖的卡通造型。</li>'
       '<li><b>写实材质</b>：每种都是真 3D（有厚度、倒角、木纹走向沿每根木条），512 px 颜色 + 法线贴图；摆件（陶瓶、画册、亚麻台灯、石灰华叠石）用 Tripo 生成后减面、降饱和。</li>'
       '<li><b>不再发光</b>：每种只有一处很弱的光（墙面上的一层暖色洗墙或藏起来的灯线），放映时降到 12 %，没有泛光。</li>'
       '<li><b>每种加了一张「余光视角」</b>：坐在 1.45 m 外、眼睛看着画面、按头显约 100° 视场渲染，框落在视野外圈；下面给了明度 / 彩度的量化，上一轮的霓虹、光环、白廊放在一起对比。</li>'
       '<li><b>面板的风格卡、应用图标跟着换成低饱和</b>；其他（对齐、开场散场、睡眠计时、设置、退出）和上一版一样，折叠在下面。</li></ol>'
       '<p class="en">Five ambient wall treatments replace the six bright styles; real materials (Tripo props, PBR wood / concrete / linen / bronze); only one faint light per style, no bloom; a peripheral-view render and measured brightness / colourfulness for each, compared with round 3. Controls are unchanged apart from the style cards and icon.</p></div>',
       '<h2>「不抢眼」怎么量的 · How “not eye-catching” was checked</h2>'
       '<p>余光视角图里，用遮罩分出「框」「播放器画面」「房间」三块，算 CIELAB 明度 L* 和彩度 C*。规则先写好再渲染：放映时框的平均 L* 比画面低 15 以上、平均 C* ≤ 12、最亮 5 % 不超过画面平均亮度；灯亮时 C* ≤ 15。五种新风格全过，上一轮三种全不过。'
       '<br><span class="en">In the peripheral view a mask splits frame / player / room; the rule (frame mean L* ≥ 15 below the picture, mean C* ≤ 12, brightest 5 % no brighter than the picture; C* ≤ 15 with lights up) was set before rendering. All five new styles pass; the three round-3 styles tested all fail.</span></p>']
for sid, zh, en, dzh, den in STY:
    meta = json.load(open(os.path.join(R, sid + ".json")))
    gal.append(f'<h2>{zh} · {en}</h2><p class="meta">{dzh}<br><span class="en">{den}</span><br>'
               f'<span class="en">{I18N["zh"]["sd." + sid]} · {I18N["en"]["sd." + sid]} · {meta["tris"]:,} 三角形 triangles · 材质 {len(meta["materials"])} 个 · GLB assets/frames/{sid}.glb</span><br>'
               f'<span class="ac">{ac_line(sid)}</span></p><div class="g4">')
    for shot, czh, cen in (("front", "正面（灯亮）", "front, lights up"), ("angled", "斜侧", "angled"), ("detail", "近景：材质和摆件", "close-up: materials and props"), ("peripheral", "余光视角（放映中）", "peripheral view, showing")):
        gal.append(fig(jpg(os.path.join(R, f"{sid}-{shot}.jpg"), width=760), czh, cen))
    gal.append('</div>')
gal.append('<h2>余光对比：上一轮 vs 这一轮 · Peripheral view, round 3 vs round 4</h2><p class="en">同一机位、同一画面、都在「放映中」。Same eye position and picture, all in the Showing state.</p><div class="g4">')
for sid, zh, en in OLD:
    a = AC[sid]["showing"]["frame"]
    gal.append(fig(jpg(os.path.join(R, f"legacy-{sid}-peripheral.jpg"), width=760), f'{zh} · C* {a["C"]} · 最亮 L* {a["Lp95"]} ✗', en))
a = AC["slats"]["showing"]["frame"]
gal.append(fig(jpg(os.path.join(R, "slats-peripheral.jpg"), width=760), f'烟熏橡木格栅（这一轮）· C* {a["C"]} · 最亮 L* {a["Lp95"]} ✓', "Smoked Oak (round 4)"))
gal.append('</div>')
ROOM = (60, 170, 2490, 1520)
SC = [("a1-align.png", "对齐模式（胡桃画廊）", "Align mode (Walnut Gallery)"), ("a2-align-zh.png", "对齐模式（亚麻软包，中文）", "Align mode (Linen Room, Chinese)"),
      ("b1-up.png", "1 · 灯亮着（烟熏橡木格栅）", "Lights up (Smoked Oak)"), ("b2-opening.png", "2 · 开场 4 秒：微光渐暗", "Opening, 4 s: soft light fades"),
      ("b3-showing.png", "3 · 放映中：微光 12 %", "Showing: soft light at 12 %"), ("b4-closing.png", "4 · 散场 6 秒：微光回来", "Closing, 6 s: soft light returns"),
      ("b5-beton-showing.png", "放映中（清水混凝土）", "Showing (Béton)"), ("b6-bronze-showing-zh.png", "放映中（青铜细框，中文）", "Showing (Bronze Line, Chinese)")]
PN = [("crop-p1-show.png", "控制面板 · 选风格", "Controls · pick a style"), ("crop-p2-settings.png", "设置：睡眠计时、环境声、语言、退出", "Settings: sleep timer, ambience, language, exit"),
      ("crop-p3-settings-zh.png", "设置（中文）", "Settings (Chinese)")]
gal += ['<details><summary>没变的部分（点开看）：对齐、开场 / 散场、控制面板 · Unchanged: alignment, show states, controls</summary>',
        '<p class="en">房间（透视）亮度不变，变的只是框自己的微光。预览里房间和播放器是示意。The room is unchanged; only the frame’s own soft light changes.</p><div class="g2">']
gal += [fig(jpg(os.path.join(G, f), ROOM, 1100), zh, en) for f, zh, en in SC]
gal += ['</div><div class="g3">']
gal += [fig(jpg(os.path.join(G, f), None, 600), zh, en, "pn") for f, zh, en in PN]
gal += ['</div></details>',
        '<h2>门 B：需要你定的 4 件事 · Gate B: four decisions</h2><ol class="qs">'
        '<li><b>风格</b>：这五种（胡桃画廊、清水混凝土、亚麻软包、烟熏橡木格栅、青铜细框）要删哪个、换哪个？默认五个都留。<span class="en">Keep all five, or drop / swap any?</span></li>'
        '<li><b>环境声默认关</b>，在设置里打开，可以吗？<span class="en">Ambience sound off by default (turn on in Settings)?</span></li>'
        '<li><b>睡眠计时到点</b>：只让框上的微光亮回来（默认），还是顺便把私人影院也关掉？<span class="en">When the sleep timer ends: only bring the soft light back (default), or also close Home Cinema?</span></li>'
        '<li><b>「有声自动开场」默认开</b>，可以吗？静音看片时不会触发，要手动按「开场」。<span class="en">“Start with the sound” on by default? Muted playback won’t trigger it.</span></li></ol>'
        '<p>看完在面板上点 [继续]，或点 [改…] 写意见（可以直接回「1 删亚麻；2 可以；3 也关掉；4 可以」这样）。PRD：<a href="prd.html">prd.html</a> · 风格对比页：<a href="options.html">options.html</a></p>',
        '<h2>交互预览 · Live preview</h2></section>']
style = ("<style>#pv-gallery{max-width:1480px;margin:0 auto;padding:24px 32px;font:15px/1.6 system-ui,-apple-system,'PingFang SC',sans-serif;color:#1d1d1f}"
         "#pv-gallery h1{font-size:26px}#pv-gallery h1 span{font-size:16px;color:#777;font-weight:400;margin-left:8px}"
         "#pv-gallery h2{font-size:18px;margin:28px 0 10px;border-bottom:1px solid #ddd;padding-bottom:4px}.en{color:#666;font-size:13px}"
         "#pv-gallery .lead{font-size:16px;background:#f4f1ec;border-radius:12px;padding:14px 18px}"
         "#pv-gallery .changed{border:3px solid #c98a2b;border-radius:12px;padding:4px 18px 10px;margin:18px 0;background:#fffaf2}#pv-gallery .changed h2{border:0}"
         "#pv-gallery .g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}#pv-gallery .g3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}"
         "#pv-gallery .g4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}"
         "#pv-gallery figure{margin:0}#pv-gallery img{width:100%;border-radius:10px;display:block;box-shadow:0 1px 4px rgba(0,0,0,.15)}"
         "#pv-gallery figcaption{font-size:13px;color:#444;margin-top:6px}#pv-gallery .meta{margin:0 0 8px;font-size:14px}#pv-gallery .ac{font-size:13px;color:#4a5a3a}"
         "#pv-gallery details{margin:24px 0}#pv-gallery summary{cursor:pointer;font-weight:600;font-size:16px}#pv-gallery .qs li{margin:6px 0}#pv-gallery .qs .en{display:block}</style>")
h = h.replace("<body>", "<body>" + style + "".join(gal), 1)
open(OUT, "w").write(h)
print(OUT, len(h) // 1024, "KB")
