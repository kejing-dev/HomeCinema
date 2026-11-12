# mute.py in.glb out.glb sat val : scale texture saturation and value (ambient look)
import sys, trimesh
from PIL import ImageEnhance
src, dst, sat, val = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
m = trimesh.load(src, force='mesh', process=False)
mat = m.visual.material
im = getattr(mat, 'baseColorTexture', None)
im = ImageEnhance.Brightness(ImageEnhance.Color(im.convert('RGB')).enhance(sat)).enhance(val)
mat.baseColorTexture = im
m.export(dst); print(dst, len(m.faces))
