"""home-cinema: cut a seamless ambience loop from a CC0 recording (no compression, no reverb, no filtering).
Picks the calmest `secs`-long window (lowest crest factor in 1 s steps: no single loud crackle / horn / door),
crossfades its last 1.5 s into its head (equal power), scales so RMS = target dBFS unless that pushes the peak over
-1.0 dBFS (then peak-limited by scaling only). Mono 44.1 kHz. usage: in.wav out.wav secs target_rms_dbfs"""
import sys, wave, numpy as np
src, dst, secs, target = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
w = wave.open(src); sr = w.getframerate(); ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
if ch > 1: x = x.reshape(-1, ch).mean(axis=1)
N = int(secs * sr); X = int(1.5 * sr)
best = None
for start in range(int(2 * sr), len(x) - N - X - int(2 * sr), sr):
    seg = x[start:start + N + X]
    rms = np.sqrt((seg ** 2).mean()); crest = 20 * np.log10(np.abs(seg).max() / rms)
    if best is None or crest < best[0]: best = (crest, start)
crest, start = best
seg = x[start:start + N + X].copy()
t = np.arange(X) / X
loop = seg[:N].copy()
loop[:X] = seg[N:N + X] * np.cos(0.5 * np.pi * t) + seg[:X] * np.sin(0.5 * np.pi * t)
rms = np.sqrt((loop ** 2).mean()); pk = np.abs(loop).max()
g = min(10 ** (target / 20) / rms, 10 ** (-1.0 / 20) / pk)
loop *= g
r2 = 20 * np.log10(np.sqrt((loop ** 2).mean())); p2 = 20 * np.log10(np.abs(loop).max())
o = wave.open(dst, 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
o.writeframes((np.clip(loop, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
print(f"{src}: window {start / sr:.0f}-{(start + N) / sr:.0f} s crest {crest:.1f} dB -> {dst} {secs:.0f} s RMS {r2:.1f} dBFS peak {p2:.1f} dBFS")
