"""Splice a loop from the CC0 rain recording (no compression, no reverb): keep the 1 s stretches without a loud single
drip (peak within 17 dB of their RMS), join them in recording order with 0.25 s equal-power crossfades, crossfade the
tail into the head, normalise peak to -1.4 dBFS (Vorbis headroom). Stdlib only."""
import wave, array, math, sys
src, dst = sys.argv[1], sys.argv[2]
w = wave.open(src); sr = w.getframerate(); x = [v / 32768 for v in array.array('h', w.readframes(w.getnframes()))]
L = sr; X = int(0.25 * sr)
chunks = []
for i in range(0, len(x) - L, L // 2):
    c = x[i:i + L]; pk = max(abs(v) for v in c); rms = math.sqrt(sum(v * v for v in c) / L)
    if 20 * math.log10(pk / rms) <= 17 and (not chunks or i >= chunks[-1][0] + L):
        chunks.append((i, c))
out = []
for _, c in chunks:
    if not out: out = list(c); continue
    for k in range(X):
        out[-X + k] = out[-X + k] * math.cos(0.5 * math.pi * k / X) + c[k] * math.sin(0.5 * math.pi * k / X)
    out += c[X:]
head = out[:X]; out = out[X:]
for k in range(X):
    out[-X + k] = out[-X + k] * math.cos(0.5 * math.pi * k / X) + head[k] * math.sin(0.5 * math.pi * k / X)
pk = max(abs(v) for v in out); g = 10 ** (-1.4 / 20) / pk; out = [v * g for v in out]
o = wave.open(dst, 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
o.writeframes(array.array('h', [int(round(v * 32767)) for v in out]).tobytes()); o.close()
print('chunks %d, len %.1f s, gain %+.1f dB, rms %.1f dBFS' % (len(chunks), len(out) / sr, 20 * math.log10(g), 20 * math.log10(math.sqrt(sum(v * v for v in out) / len(out)))))
