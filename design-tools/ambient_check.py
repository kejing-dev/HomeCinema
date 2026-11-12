"""Ambient check: how much does the frame pull the eye in the peripheral (headset-FOV) view?
For each style reads out4/<style>-peripheral.png (Showing state), -peripheral-up.png (Lights up) and -peripheral-mask.png
(white = frame, grey = other app's player, black = room). Reports CIELAB mean L* and chroma C* per region, and the
frame's 95th-percentile L* (hot spots). Pass rule (design rule from B30, written before rendering):
  showing: frame mean L* <= player mean L* - 15, frame mean C* <= 12, frame p95 L* <= player mean L*
  up:      frame mean C* <= 15 (no saturated colour even with lights up)
Usage: python3 ambient_check.py <out-dir> <style> [<style> ...]  -> JSON to stdout"""
import json, sys, os
import numpy as np
from PIL import Image


def lab(rgb):
    c = rgb / 255.0
    c = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
    M = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]])
    xyz = c @ M.T / np.array([.95047, 1.0, 1.08883])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16; a = 500 * (f[..., 0] - f[..., 1]); b = 200 * (f[..., 1] - f[..., 2])
    return L, np.hypot(a, b)


def region_stats(img, sel):
    L, C = lab(img[sel].astype(float))
    return {"L": round(float(L.mean()), 1), "C": round(float(C.mean()), 1), "Lp95": round(float(np.percentile(L, 95)), 1), "px": int(sel.sum())}


out = {}
D = sys.argv[1]
for s in sys.argv[2:]:
    m = np.asarray(Image.open(os.path.join(D, f"{s}-peripheral-mask.png")).convert("L")).astype(int)
    regions = {"frame": m > 200, "player": (m > 90) & (m < 170), "room": m < 30}
    r = {}
    for state, f in (("showing", f"{s}-peripheral.png"), ("up", f"{s}-peripheral-up.png")):
        img = np.asarray(Image.open(os.path.join(D, f)).convert("RGB"))
        r[state] = {k: region_stats(img, v) for k, v in regions.items()}
    sh, up = r["showing"], r["up"]
    r["pass"] = bool(sh["frame"]["L"] <= sh["player"]["L"] - 15 and sh["frame"]["C"] <= 12 and sh["frame"]["Lp95"] <= sh["player"]["L"] and up["frame"]["C"] <= 15)
    r["frameShareOfView"] = round(regions["frame"].mean(), 3)
    out[s] = r
print(json.dumps(out, indent=1))
