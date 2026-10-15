"""Sonidos sintetizados para TOC+ (sin descargar nada): grito de dolor, desmayo, hueso que cede."""
import numpy as np, wave, struct, os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
SR = 22050

def write(name, sig):
    sig = np.clip(sig, -1, 1)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((sig * 32000).astype("<i2").tobytes())

def env(n, a, r):
    e = np.ones(n); A = int(a * SR); R = int(r * SR)
    e[:A] = np.linspace(0, 1, A); e[-R:] = np.linspace(1, 0, R); return e

def scream(seed, pitch, dur, female):
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    f0 = pitch * (1 + 0.25 * np.exp(-t * 3)) * (1 + 0.03 * np.sin(2 * np.pi * 6.5 * t))  # vibrato y caída
    f0 *= (1 - 0.15 * t / dur)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = np.zeros(n)
    for h in range(1, 14):                      # armónicos con formante
        amp = (1.0 / h) * (1.6 if 3 <= h <= 6 else 1.0)
        sig += amp * np.sin(h * phase + rng.uniform(0, 6.28))
    sig *= 1 + 0.4 * (rng.standard_normal(n) * 0.5)  # ronquera
    sig += 0.25 * rng.standard_normal(n) * np.exp(-t * 2)  # aire inicial
    sig *= env(n, 0.05, 0.3)
    return sig / np.max(np.abs(sig))

write("TOC_ScreamMale1.wav", scream(1, 190, 1.4, False))
write("TOC_ScreamMale2.wav", scream(2, 215, 1.1, False))
write("TOC_ScreamFemale1.wav", scream(3, 330, 1.3, True))
write("TOC_ScreamFemale2.wav", scream(4, 370, 1.0, True))

# gemido ahogado (anestesiado): grave, corto, cerrado
rng = np.random.default_rng(9); n = int(0.9 * SR); t = np.arange(n) / SR
f0 = 120 * (1 + 0.1 * np.sin(2 * np.pi * 5 * t)); ph = 2 * np.pi * np.cumsum(f0) / SR
g = sum((1 / h) * np.sin(h * ph) for h in range(1, 6)) * env(n, 0.1, 0.4)
write("TOC_Groan.wav", g / np.max(np.abs(g)) * 0.7)

# crujido de hueso: ráfaga de clicks + ruido filtrado
rng = np.random.default_rng(5); n = int(0.6 * SR); t = np.arange(n) / SR
noise = rng.standard_normal(n)
lp = np.convolve(noise, np.ones(12) / 12, mode="same")
clicks = np.zeros(n)
for c in rng.uniform(0.05, 0.5, 9):
    i = int(c * SR); clicks[i:i + 60] += np.hanning(60) * rng.uniform(0.6, 1.0)
crack = (lp * 0.6 + clicks) * env(n, 0.01, 0.25)
write("TOC_BoneCrack.wav", crack / np.max(np.abs(crack)))

# caída al suelo (desmayo): golpe sordo
n = int(0.5 * SR); t = np.arange(n) / SR
thud = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 14) + 0.3 * rng.standard_normal(n) * np.exp(-t * 30)
write("TOC_Thud.wav", thud / np.max(np.abs(thud)))
print("ok", os.listdir(OUT))
