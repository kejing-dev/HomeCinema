"""Generate original demo artwork (poster / backdrop / logo layers) for Home Cinema demo titles.
All shapes are procedural; no third-party imagery."""
import math, os, random, sys
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

TITLES = [
  ("harbor", "Harbor Lights", "港湾灯火", ("#0b2a3a", "#1f5e6e", "#f2a65a"), "harbor"),
  ("moon", "Paper Moon Express", "纸月亮快车", ("#1d1438", "#5b3f8c", "#f4e3b2"), "train"),
  ("orchard", "The Quiet Orchard", "静谧果园", ("#16331f", "#4f8a4b", "#f0d36b"), "hills"),
  ("vega", "Signal from Vega", "织女星信号", ("#050a1f", "#1d3b78", "#9fd3ff"), "dish"),
  ("relay", "Desert Relay", "沙漠接力", ("#3a1606", "#c4602a", "#ffd27a"), "dunes"),
  ("rain", "Rain on Glass", "雨窗", ("#1b2430", "#4b6178", "#cfe3f2"), "rain"),
  ("kite", "Kite Season", "风筝季", ("#0f3a66", "#4fa3d9", "#ffcf4d"), "kites"),
  ("keepers", "Lighthouse Keepers", "守塔人", ("#101a2a", "#2e5172", "#ffe08a"), "lighthouse"),
]

def scene(kind, w, h, c, rnd):
    bg, mid, acc = c
    s = []
    if kind == "harbor":
        for i in range(14):
            x = rnd.uniform(0, w); y = h*0.62 + rnd.uniform(-h*0.04, h*0.03)
            s.append(f'<rect x="{x:.0f}" y="{y-h*0.05:.0f}" width="{w*0.03:.0f}" height="{h*0.05:.0f}" fill="{mid}"/>')
            s.append(f'<circle cx="{x+w*0.015:.0f}" cy="{y-h*0.03:.0f}" r="{w*0.006:.1f}" fill="{acc}"/>')
            s.append(f'<rect x="{x+w*0.012:.0f}" y="{y+h*0.02:.0f}" width="{w*0.006:.1f}" height="{h*0.12:.0f}" fill="{acc}" opacity="0.35"/>')
        s.append(f'<rect x="0" y="{h*0.62:.0f}" width="{w}" height="{h*0.38:.0f}" fill="{bg}" opacity="0.55"/>')
    elif kind == "train":
        s.append(f'<circle cx="{w*0.68:.0f}" cy="{h*0.3:.0f}" r="{min(w,h)*0.17:.0f}" fill="{acc}"/>')
        s.append(f'<path d="M0 {h*0.72:.0f} Q {w*0.5:.0f} {h*0.6:.0f} {w} {h*0.7:.0f} L {w} {h} L 0 {h} Z" fill="{bg}"/>')
        for i in range(6):
            x = w*0.08 + i*w*0.13
            s.append(f'<rect x="{x:.0f}" y="{h*0.6:.0f}" width="{w*0.11:.0f}" height="{h*0.07:.0f}" rx="6" fill="{mid}"/>')
            s.append(f'<rect x="{x+w*0.02:.0f}" y="{h*0.615:.0f}" width="{w*0.07:.0f}" height="{h*0.025:.0f}" fill="{acc}" opacity="0.8"/>')
    elif kind == "hills":
        s.append(f'<circle cx="{w*0.25:.0f}" cy="{h*0.25:.0f}" r="{min(w,h)*0.1:.0f}" fill="{acc}" opacity="0.9"/>')
        for k, (yy, col) in enumerate([(0.55, mid), (0.68, bg)]):
            s.append(f'<path d="M0 {h*yy:.0f} Q {w*0.3:.0f} {h*(yy-0.12):.0f} {w*0.6:.0f} {h*yy:.0f} T {w} {h*(yy-0.04):.0f} L {w} {h} L 0 {h} Z" fill="{col}"/>')
        for i in range(9):
            x = w*0.1 + i*w*0.1; y = h*0.7 + (i % 2)*h*0.04
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{w*0.035:.0f}" fill="{mid}"/><rect x="{x-2:.0f}" y="{y:.0f}" width="4" height="{h*0.05:.0f}" fill="{bg}"/>')
    elif kind == "dish":
        for i in range(70):
            s.append(f'<circle cx="{rnd.uniform(0,w):.0f}" cy="{rnd.uniform(0,h*0.7):.0f}" r="{rnd.uniform(0.6,2.2):.1f}" fill="#ffffff" opacity="{rnd.uniform(.3,.9):.2f}"/>')
        s.append(f'<circle cx="{w*0.75:.0f}" cy="{h*0.2:.0f}" r="{min(w,h)*0.03:.0f}" fill="{acc}"/>')
        s.append(f'<path d="M{w*0.2:.0f} {h*0.7:.0f} A {w*0.22:.0f} {w*0.22:.0f} 0 0 1 {w*0.55:.0f} {h*0.48:.0f} Z" fill="{mid}"/>')
        s.append(f'<line x1="{w*0.37:.0f}" y1="{h*0.6:.0f}" x2="{w*0.75:.0f}" y2="{h*0.2:.0f}" stroke="{acc}" stroke-width="2" stroke-dasharray="6 8" opacity="0.8"/>')
        s.append(f'<rect x="0" y="{h*0.7:.0f}" width="{w}" height="{h*0.3:.0f}" fill="{bg}"/>')
    elif kind == "dunes":
        s.append(f'<circle cx="{w*0.5:.0f}" cy="{h*0.38:.0f}" r="{min(w,h)*0.16:.0f}" fill="{acc}"/>')
        for k, (yy, col, op) in enumerate([(0.55, mid, .8), (0.66, mid, 1), (0.78, bg, 1)]):
            s.append(f'<path d="M0 {h*yy:.0f} C {w*0.25:.0f} {h*(yy-0.1):.0f} {w*0.55:.0f} {h*(yy+0.06):.0f} {w} {h*(yy-0.05):.0f} L {w} {h} L 0 {h} Z" fill="{col}" opacity="{op}"/>')
        for i in range(4):
            s.append(f'<circle cx="{w*(0.3+i*0.08):.0f}" cy="{h*(0.62-i*0.015):.0f}" r="{w*0.008:.1f}" fill="{bg}"/>')
    elif kind == "rain":
        s.append(f'<rect x="{w*0.15:.0f}" y="{h*0.12:.0f}" width="{w*0.7:.0f}" height="{h*0.6:.0f}" rx="8" fill="{mid}" opacity="0.6"/>')
        s.append(f'<line x1="{w*0.5:.0f}" y1="{h*0.12:.0f}" x2="{w*0.5:.0f}" y2="{h*0.72:.0f}" stroke="{bg}" stroke-width="6"/>')
        for i in range(60):
            x = rnd.uniform(w*0.16, w*0.84); y = rnd.uniform(h*0.13, h*0.7)
            s.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x-2:.0f}" y2="{y+rnd.uniform(6,18):.0f}" stroke="{acc}" stroke-width="1.6" opacity="0.7"/>')
        s.append(f'<circle cx="{w*0.68:.0f}" cy="{h*0.4:.0f}" r="{w*0.05:.0f}" fill="#ffcf7a" opacity="0.5"/>')
    elif kind == "kites":
        for i in range(5):
            x = rnd.uniform(w*0.15, w*0.85); y = rnd.uniform(h*0.12, h*0.5); r = w*rnd.uniform(.04, .07)
            col = [acc, "#ff7a6b", "#ffffff", acc, "#7be0b5"][i]
            s.append(f'<path d="M{x:.0f} {y-r:.0f} L {x+r*0.7:.0f} {y:.0f} L {x:.0f} {y+r*1.3:.0f} L {x-r*0.7:.0f} {y:.0f} Z" fill="{col}"/>')
            s.append(f'<path d="M{x:.0f} {y+r*1.3:.0f} q 10 30 -6 60 q -10 30 6 50" stroke="{col}" fill="none" stroke-width="1.5"/>')
        s.append(f'<path d="M0 {h*0.8:.0f} Q {w*0.5:.0f} {h*0.72:.0f} {w} {h*0.8:.0f} L {w} {h} L 0 {h} Z" fill="{bg}"/>')
    elif kind == "lighthouse":
        s.append(f'<path d="M{w*0.55:.0f} {h*0.28:.0f} L {w*1.1:.0f} {h*0.12:.0f} L {w*1.1:.0f} {h*0.36:.0f} Z" fill="{acc}" opacity="0.35"/>')
        s.append(f'<path d="M{w*0.47:.0f} {h*0.72:.0f} L {w*0.5:.0f} {h*0.3:.0f} L {w*0.6:.0f} {h*0.3:.0f} L {w*0.63:.0f} {h*0.72:.0f} Z" fill="#e9eef4"/>')
        s.append(f'<rect x="{w*0.505:.0f}" y="{h*0.24:.0f}" width="{w*0.09:.0f}" height="{h*0.06:.0f}" fill="{acc}"/>')
        for i in range(3):
            s.append(f'<rect x="{w*0.48+i*0.004*w:.0f}" y="{h*(0.42+i*0.1):.0f}" width="{w*(0.14-i*0.008):.0f}" height="{h*0.03:.0f}" fill="#c84b3c"/>')
        s.append(f'<path d="M0 {h*0.72:.0f} Q {w*0.5:.0f} {h*0.68:.0f} {w} {h*0.74:.0f} L {w} {h} L 0 {h} Z" fill="{bg}"/>')
    return "\n".join(s)

def svg(w, h, body, defs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{defs}{body}</svg>\n'

for i, (key, en, zh, c, kind) in enumerate(TITLES):
    bg, mid, acc = c
    grad = f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{mid}"/></linearGradient></defs>'
    # poster 2:3 (Primary) - scene only, title lives on the separate logo layer
    rnd = random.Random(i)
    body = f'<rect width="400" height="600" fill="url(#g)"/>' + scene(kind, 400, 600, c, rnd)
    open(f"{OUT}/poster-{key}.svg", "w").write(svg(400, 600, body, grad))
    # backdrop 16:9
    rnd = random.Random(i + 100)
    body = f'<rect width="960" height="540" fill="url(#g)"/>' + scene(kind, 960, 540, c, rnd)
    open(f"{OUT}/backdrop-{key}.svg", "w").write(svg(960, 540, body, grad))
    # logo layer: transparent title art (front depth layer)
    size = 64 if len(en) < 14 else 50
    body = (f'<text x="300" y="100" text-anchor="middle" font-family="Georgia, \'Times New Roman\', serif" font-weight="700" '
            f'font-size="{size}" fill="{acc}" stroke="{bg}" stroke-width="2" paint-order="stroke">{en}</text>'
            f'<text x="300" y="160" text-anchor="middle" font-family="\'PingFang SC\', \'Noto Sans CJK SC\', sans-serif" font-size="34" fill="#ffffff" opacity="0.92">{zh}</text>')
    open(f"{OUT}/logo-{key}.svg", "w").write(svg(600, 200, body))
# app icon (original): stylised screen + depth layers
icon = ('<defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b1f3a"/><stop offset="1" stop-color="#3a1f4f"/></linearGradient></defs>'
        '<rect width="512" height="512" rx="112" fill="url(#b)"/>'
        '<rect x="150" y="120" width="212" height="300" rx="18" fill="#f2a65a" opacity="0.35" transform="translate(-26 18)"/>'
        '<rect x="150" y="120" width="212" height="300" rx="18" fill="#f2a65a" opacity="0.6" transform="translate(-13 9)"/>'
        '<rect x="150" y="120" width="212" height="300" rx="18" fill="#ffd27a"/>'
        '<path d="M228 220 L 304 270 L 228 320 Z" fill="#1b1f3a"/>')
open(f"{OUT}/app-icon.svg", "w").write(svg(512, 512, icon))
print("ok", len(os.listdir(OUT)))
