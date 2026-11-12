"""home-cinema: masks for design-tools/ambient_check.py from emulator screenshots.
frame = pixels that differ from the same view without the app (left of the controls window);
player = the opening (16:9 box at the frame bbox centre, 1.64/3.1 x 0.94/1.85 of the wall; bronze 1.66/2.57 x 0.96/1.62);
the emulator has no video in the opening, so 'player' is the room seen through it (a bright wall), a stand-in."""
import sys, numpy as np
from PIL import Image
ev, out = sys.argv[1], sys.argv[2]
bg = np.asarray(Image.open(f'{ev}/bg-no-app.png').convert('RGB')).astype(int)
ratio = {'bronze': (1.66/2.57, 0.96/1.62)}
for s in ['walnut','beton','linen','slats','bronze']:
    up = np.asarray(Image.open(f'{ev}/lights-up-{s}.png').convert('RGB')).astype(int)
    sh = np.asarray(Image.open(f'{ev}/showing-{s}.png').convert('RGB')).astype(int)
    d = (np.abs(up - bg).sum(2) > 40) | (np.abs(sh - bg).sum(2) > 40)
    d[:, 1450:] = False
    ys, xs = np.where(d)
    # wall bbox from robust percentiles (props/shadows stick out a little)
    x0, x1 = np.percentile(xs, [1, 99]).astype(int); y0, y1 = np.percentile(ys, [1, 99]).astype(int)
    rw, rh = ratio.get(s, (1.64/3.1, 0.94/1.85))
    cx, cy = (x0+x1)/2, (y0+y1)/2; hw, hh = (x1-x0)*rw/2, (y1-y0)*rh/2
    m = np.zeros(d.shape, np.uint8)
    m[d] = 255
    m[int(cy-hh):int(cy+hh), int(cx-hw):int(cx+hw)] = 128
    Image.fromarray(m).save(f'{out}/{s}-peripheral-mask.png')
    Image.open(f'{ev}/showing-{s}.png').convert('RGB').save(f'{out}/{s}-peripheral.png')
    Image.open(f'{ev}/lights-up-{s}.png').convert('RGB').save(f'{out}/{s}-peripheral-up.png')
    print(s, 'wall bbox', x0, y0, x1, y1)
