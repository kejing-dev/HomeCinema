import sys
from PIL import Image
D, out, styles, shots = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4].split(',')
w, h = 480, 300
sheet = Image.new('RGB', (w * len(shots), h * len(styles)))
for j, s in enumerate(styles):
    for i, k in enumerate(shots):
        sheet.paste(Image.open(f'{D}/{s}-{k}.png').convert('RGB').resize((w, h)), (i * w, j * h))
sheet.save(out, quality=82)
