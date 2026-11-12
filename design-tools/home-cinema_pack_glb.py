"""home-cinema build: pack the design frame GLBs for the APK.
- bake KHR_materials_emissive_strength into emissiveFactor (the runtime scales emissive colour itself; the SDK may ignore the extension)
- re-encode PNG textures as JPEG (colour q86, normal q92); tiny maps (< 16 KB) stay PNG
- force alphaMode OPAQUE on every material (build.md 2026-10-29)
usage: python home-cinema_pack_glb.py <in.glb> <out.glb>
"""
import io, json, struct, sys
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
jl = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + jl])
off = 20 + jl
bl = struct.unpack('<I', b[off:off + 4])[0]
binc = b[off + 8: off + 8 + bl]

normal_imgs = set()
tex_img = {i: t['source'] for i, t in enumerate(j.get('textures', []))}
for m in j['materials']:
    m['alphaMode'] = 'OPAQUE'
    m.pop('alphaCutoff', None)
    ext = m.get('extensions', {})
    es = ext.pop('KHR_materials_emissive_strength', None)
    if es is not None:
        k = es.get('emissiveStrength', 1.0)
        m['emissiveFactor'] = [min(1.0, c * k) for c in m.get('emissiveFactor', [0, 0, 0])]
    if not ext:
        m.pop('extensions', None)
    if 'normalTexture' in m:
        normal_imgs.add(tex_img[m['normalTexture']['index']])
for key in ('extensionsUsed', 'extensionsRequired'):
    if key in j:
        j[key] = [e for e in j[key] if e != 'KHR_materials_emissive_strength']
        if not j[key]:
            del j[key]

views = j['bufferViews']
img_views = {}
# Linen: the dark 'backing' plane is a full 3.1 x 1.92 m quad that covers the opening (design R4 GLB bug, found on the
# emulator: the opening rendered black). Replace it with a ring that leaves the 1.64 x 0.94 m opening empty (A2 / A3).
for n in j['nodes']:
    if n.get('name') != 'backing':
        continue
    prim = j['meshes'][n['mesh']]['primitives'][0]
    acc = j['accessors']
    if acc[prim['attributes']['POSITION']]['count'] != 4:
        continue
    ty = n.get('matrix', [0]*16)[13] if 'matrix' in n else n.get('translation', [0, 0, 0])[1]
    X, Y0, Y1 = 1.55, -0.96, 0.96
    hx, hy0, hy1 = 0.82, -0.47 - ty, 0.47 - ty
    pts = [(-X, Y0), (X, Y0), (X, Y1), (-X, Y1), (-hx, hy0), (hx, hy0), (hx, hy1), (-hx, hy1)]
    tris = [0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]
    pos = b''.join(struct.pack('<3f', x, y, 0.0) for x, y in pts)
    nor = b''.join(struct.pack('<3f', 0.0, 0.0, 1.0) for _ in pts)
    uv = b''.join(struct.pack('<2f', (x + X) / (2 * X), (Y1 - y) / (Y1 - Y0)) for x, y in pts)
    idx = struct.pack('<%dH' % len(tris), *tris)
    for key, data, cnt in (('POSITION', pos, 8), ('NORMAL', nor, 8), ('TEXCOORD_0', uv, 8)):
        a = acc[prim['attributes'][key]]; img_views[a['bufferView']] = data; a['count'] = cnt; a.pop('byteOffset', None)
        views[a['bufferView']].pop('byteStride', None)
    acc[prim['attributes']['POSITION']]['min'] = [-X, Y0, 0.0]; acc[prim['attributes']['POSITION']]['max'] = [X, Y1, 0.0]
    a = acc[prim['indices']]; img_views[a['bufferView']] = idx; a['count'] = len(tris); a['max'] = [7]; a.pop('byteOffset', None)
    print('backing quad -> ring with the opening cut out (hole y %.2f..%.2f local)' % (hy0, hy1))
for i, im in enumerate(j.get('images', [])):
    v = views[im['bufferView']]
    data = binc[v.get('byteOffset', 0): v.get('byteOffset', 0) + v['byteLength']]
    if im.get('mimeType') == 'image/png' and len(data) > 16384:
        pil = Image.open(io.BytesIO(data)).convert('RGB')
        out = io.BytesIO()
        pil.save(out, 'JPEG', quality=92 if i in normal_imgs else 86, optimize=True)
        data = out.getvalue()
        im['mimeType'] = 'image/jpeg'
    img_views[im['bufferView']] = data

newbin = bytearray()
for vi, v in enumerate(views):
    data = img_views.get(vi)
    if data is None:
        data = binc[v.get('byteOffset', 0): v.get('byteOffset', 0) + v['byteLength']]
    while len(newbin) % 4:
        newbin.append(0)
    v['byteOffset'] = len(newbin)
    v['byteLength'] = len(data)
    newbin += data
while len(newbin) % 4:
    newbin.append(0)
j['buffers'] = [{'byteLength': len(newbin)}]
js = json.dumps(j, separators=(',', ':')).encode()
while len(js) % 4:
    js += b' '
total = 12 + 8 + len(js) + 8 + len(newbin)
out = struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(newbin), 0x004E4942) + bytes(newbin)
open(dst, 'wb').write(out)
print(f'{src} {len(b)} -> {dst} {len(out)} bytes')
