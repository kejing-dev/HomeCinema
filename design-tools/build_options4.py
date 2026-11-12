"""Round 4: options.html = side-by-side comparison of the five ambient styles (front + peripheral view + numbers),
with round 3 styles for reference. Usage: python3 build_options4.py <scratch-dir> <out.html>"""
import base64, io, json, os, sys
from PIL import Image
S, OUT = sys.argv[1], sys.argv[2]; R = os.path.join(S, "review", "renders")
AC = json.load(open(os.path.join(R, "ambient-check.json")))
def jpg(name, w=640):
    im = Image.open(os.path.join(R, name)).convert("RGB"); im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=80, optimize=True); return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
STY = [("walnut", "胡桃画廊 Walnut Gallery", "胡桃木深框 + 暗亚麻衬边 + 黄铜细线，炭灰石灰墙，陶瓶和画册", "最像「家里挂了一幅好画」；暖、稳", "室内底噪"),
       ("beton", "清水混凝土 Béton", "木模清水混凝土墙上的 14 cm 深窗口，石灰华叠石", "最冷静、最建筑感；灰、无彩", "天窗细雨"),
       ("linen", "亚麻软包 Linen Room", "深灰米色织物吸音板 + 胡桃收边，亚麻台灯和书", "最柔、最像酒店影音室", "很轻的壁炉声"),
       ("slats", "烟熏橡木格栅 Smoked Oak", "黑毡上的竖向烟熏橡木格栅 + 黑钢窗框，屏后一点中性光", "最像家庭影院；最暗", "闷闷的城市夜"),
       ("bronze", "青铜细框 Bronze Line", "黑亚麻卡纸 + 3 cm 做旧青铜细框，什么都不放", "几乎看不见；最退后", "不配声音")]
rows = []
for k, name, look, feel, snd in STY:
    a = AC[k]; sh = a["showing"]["frame"]
    rows.append(f'<tr><td><b>{name}</b><br>{look}<br><span class="en">感觉：{feel} · 环境声：{snd}</span><br><span class="ok">放映时 L* {sh["L"]} · C* {sh["C"]} · 最亮 {sh["Lp95"]} · {"不抢眼 ✓" if a["pass"] else "✗"}</span></td>'
                f'<td><img src="{jpg(k + "-front.jpg")}"></td><td><img src="{jpg(k + "-peripheral.jpg")}"></td></tr>')
old = "".join(f'<figure><img src="{jpg("legacy-" + k + "-peripheral.jpg", 480)}"><figcaption>{n} · C* {AC[k]["showing"]["frame"]["C"]} · 最亮 {AC[k]["showing"]["frame"]["Lp95"]} ✗</figcaption></figure>'
              for k, n in (("neon", "霓虹夜"), ("portal", "全息光环"), ("gallery", "白廊")))
html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>Home Cinema · 风格对比（第 4 轮 ambient）</title>
<style>body{{font:15px/1.6 -apple-system,'PingFang SC',sans-serif;max-width:1400px;margin:24px auto;padding:0 24px;color:#1d1d1f}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #e3e3e3;padding:10px;vertical-align:top}}th{{text-align:left;background:#f4f4f6}}
td:first-child{{width:30%}}img{{width:100%;border-radius:8px;display:block}}.en{{color:#666;font-size:13px}}.ok{{color:#3d5a2a;font-size:13px}}
.old{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}figure{{margin:0}}figcaption{{font-size:13px;color:#555}}.note{{background:#f4f1ec;border-radius:10px;padding:12px 16px}}</style></head><body>
<h1>私人影院 · 风格对比 <span class="en">Home Cinema · ambient styles, round 4</span></h1>
<p class="note">方向已定：方案 A「影院框」（只在 Shared Space 里装饰别的应用的播放器四周，见 <code>feasibility.md</code>）。这一页只比较第 4 轮的五种风格。左边一句话，中间是正面渲染（灯亮），右边是<b>余光视角</b>（眼在 1.45 m、看着画面、约 100° 视场、放映中）。数字：L* 明度、C* 彩度，规则是放映时框比画面暗 15 以上、C* ≤ 12、最亮 5 % 不超过画面。<br>
<span class="en">Direction A is settled. This page compares only the five round-4 styles: description, front render (lights up), and the peripheral view (eye at 1.45 m, looking at the picture, ~100° FOV, showing).</span></p>
<table><tr><th>风格</th><th>正面</th><th>余光视角（放映中）</th></tr>{''.join(rows)}</table>
<h2>上一轮为什么被打回（同一机位）</h2><div class="old">{old}</div>
<p>完整样稿：<a href="sample.html">sample.html</a> · PRD：<a href="prd.html">prd.html</a></p></body></html>"""
open(OUT, "w").write(html); print(OUT, len(html) // 1024, "KB")
