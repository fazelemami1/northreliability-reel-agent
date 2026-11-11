"""Original instrumental bed for NR reels (no lyrics, no samples): warm pad, plucked arpeggio, soft kick and shaker.
Usage: python3 make_music.py out.wav seconds"""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
dur = float(sys.argv[2]); N = int(SR * (dur + 1))
bpm = 96; beat = 60 / bpm; bar = 4 * beat
rng = np.random.default_rng(7)
t = np.arange(N) / SR
def hz(m): return 440 * 2 ** ((m - 69) / 12)
# Am - F - C - G (i - VI - III - VII), calm and steady
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
bass = [45, 41, 48, 43]
L = np.zeros(N); R = np.zeros(N)

def env(n, a, r):
    e = np.ones(n); a = min(int(a * SR), n); r = min(int(r * SR), n)
    e[:a] = np.linspace(0, 1, a); e[n - r:] *= np.linspace(1, 0, r); return e

def lp(x, fc):
    b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, x)

nbars = int(np.ceil(dur / bar)) + 1
for i in range(nbars):
    s = int(i * bar * SR); n = int(bar * SR * 1.15); n = min(n, N - s)
    if n <= 0: break
    tt = np.arange(n) / SR; ch = chords[i % 4]
    pad = sum(np.sin(2 * np.pi * hz(m) * tt * (1 + d)) for m in ch for d in (-0.002, 0.002)) / 6
    pad = lp(pad, 1800) * env(n, 0.8, 0.9) * 0.16
    L[s:s + n] += pad; R[s:s + n] += pad
    bs = np.sin(2 * np.pi * hz(bass[i % 4]) * tt) * env(n, 0.05, 0.6) * 0.14
    L[s:s + n] += bs; R[s:s + n] += bs
    arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]
    for k in range(8):  # eighth-note pluck
        ps = s + int(k * beat / 2 * SR); pn = int(0.6 * SR)
        if ps + pn > N: continue
        pt = np.arange(pn) / SR; f = hz(arp[k % 4])
        pl = (np.sin(2 * np.pi * f * pt) + 0.3 * np.sin(4 * np.pi * f * pt)) * np.exp(-pt * 6) * 0.07
        pan = 0.35 if k % 2 else 0.65
        L[ps:ps + pn] += pl * (1 - pan) * 2; R[ps:ps + pn] += pl * pan * 2
    for k in range(4):  # soft kick on each beat, shaker off-beat
        ks = s + int(k * beat * SR); kn = int(0.25 * SR)
        if ks + kn <= N:
            kt = np.arange(kn) / SR
            kick = np.sin(2 * np.pi * (50 + 60 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 14) * 0.22
            L[ks:ks + kn] += kick; R[ks:ks + kn] += kick
        hs = ks + int(beat / 2 * SR); hn = int(0.06 * SR)
        if hs + hn <= N and i > 0:
            nz = rng.standard_normal(hn); nz = nz - lp(nz, 6000)
            sh = nz * np.exp(-np.arange(hn) / SR * 60) * 0.03
            L[hs:hs + hn] += sh; R[hs:hs + hn] += sh

L, R = L[:int(SR * dur)], R[:int(SR * dur)]
fade = np.ones(len(L)); fi, fo = int(0.5 * SR), int(2.0 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
st = np.stack([L * fade, R * fade], 1)
st = st / np.max(np.abs(st)) * 0.5   # about -6 dBFS peak, sits under speech or text
wavfile.write(sys.argv[1], SR, (st * 32767).astype(np.int16))
print("ok", dur)
