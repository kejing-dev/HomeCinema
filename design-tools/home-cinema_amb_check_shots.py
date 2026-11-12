import sys, json, numpy as np
from PIL import Image
R = sys.argv[1]; STY = sys.argv[2:] or ['walnut','beton','linen','slats','bronze']
def lab(rgb):
    c = rgb/255.0; c = np.where(c<=.04045, c/12.92, ((c+.055)/1.055)**2.4)
    M = np.array([[.4124,.3576,.1805],[.2126,.7152,.0722],[.0193,.1192,.9505]])
    xyz = c@M.T/np.array([.95047,1.0,1.08883]); f = np.where(xyz>.008856, np.cbrt(xyz), 7.787*xyz+16/116)
    L = 116*f[...,1]-16; a = 500*(f[...,0]-f[...,1]); b = 200*(f[...,1]-f[...,2]); return L, np.hypot(a,b)
box = {'default': ((160,768,2464,2096),(656,1088,1958,1818)), 'bronze': ((340,860,2280,2060),(656,1088,1958,1818))}
out = {}
for s in STY:
    (x0,y0,x1,y1),(ox0,oy0,ox1,oy1) = box.get(s, box['default'])
    r = {}
    for st in ['showing','lights-up']:
        img = np.asarray(Image.open(f'{R}/{st}-{s}.png').convert('RGB')).astype(float)
        m = np.zeros(img.shape[:2], bool); m[y0:y1, x0:x1] = True; m[oy0-25:oy1+25, ox0-25:ox1+25] = False
        L, C = lab(img[m]); Lo, Co = lab(img[oy0:oy1, ox0:ox1].reshape(-1,3))
        r[st] = dict(frameL=round(float(L.mean()),1), frameC=round(float(C.mean()),1), frameLp95=round(float(np.percentile(L,95)),1), openingL=round(float(Lo.mean()),1))
    sh, up = r['showing'], r['lights-up']
    r['pass'] = bool(sh['frameL'] <= sh['openingL']-15 and sh['frameC'] <= 12 and sh['frameLp95'] <= sh['openingL'] and up['frameC'] <= 15)
    out[s] = r
print(json.dumps(out, indent=1))
