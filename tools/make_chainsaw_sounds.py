"""Sonidos sintetizados del brazo motosierra (motor de dos tiempos, sin audio descargado).
Modelo: tren de explosiones a la frecuencia de encendido (ralentí ~48 Hz, a fondo ~190 Hz), cada explosión un
pulso corto de ruido + resonancia; silenciador = filtros resonantes; cadena = ruido agudo que crece con las
revoluciones; saturación suave. Escribe en media/sound:
  TOC_ChainsawIdle (bucle sin costura), TOC_ChainsawRev (golpe al aire), TOC_ChainsawCut (al dar),
  TOC_ChainsawStart (tirón + arranca), TOC_ChainsawPull (tirón fallido), TOC_ChainsawStop (se apaga).
Uso: python make_chainsaw_sounds.py [carpeta_salida]"""
import os, sys, wave
import numpy as np
from scipy.signal import butter, lfilter, iirpeak

OUT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\sound"
SR = 22050
rng = np.random.default_rng(42)

def write(name, sig, gain=0.92):
    sig = np.asarray(sig, float)
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * gain
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(sig, -1, 1) * 32000).astype("<i2").tobytes())
    print("%-24s %.2f s" % (name, len(sig) / SR))

def smooth_noise(n, cutoff_hz, seed):
    r = np.random.default_rng(seed).standard_normal(n)
    b, a = butter(2, cutoff_hz / (SR / 2))
    x = lfilter(b, a, r)
    return x / (np.max(np.abs(x)) + 1e-9)

def bp(x, f, q):
    b, a = iirpeak(f / (SR / 2), q)
    return lfilter(b, a, x)

def band(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)

PULSES = []
for k in range(6):
    L = int(0.012 * SR); t = np.arange(L) / SR
    nz = rng.standard_normal(L)
    p = np.exp(-t / 0.0022) * (0.7 * nz + np.sin(2 * np.pi * (560 + 60 * k) * t)) + 0.6 * np.exp(-t / 0.006) * np.sin(2 * np.pi * 170 * t)
    PULSES.append(p)

def engine(freq, misfire=0.0, seed=1, chain=1.0, amp=None):
    """freq: frecuencia de encendido por muestra. Devuelve la señal del motor."""
    n = len(freq); r = np.random.default_rng(seed)
    f = freq * (1 + 0.035 * smooth_noise(n, 25, seed + 1))
    ph = np.cumsum(f / SR)
    fires = np.nonzero(np.diff(np.floor(ph)))[0]
    L = len(PULSES[0]); sig = np.zeros(n + L)
    for i in fires:
        mf = misfire[i] if isinstance(misfire, np.ndarray) else misfire
        if r.random() < mf: continue
        sig[i:i + L] += (0.75 + 0.5 * r.random()) * PULSES[r.integers(len(PULSES))]
    sig = sig[:n]
    # silenciador: resonancias + cuerpo grave
    body = lfilter(*butter(2, 900 / (SR / 2)), sig)
    muff = 0.8 * bp(sig, 340, 2.5) + 0.55 * bp(sig, 1150, 3.0) + 0.3 * bp(sig, 2700, 2.0) + 0.9 * body
    # zumbido: armónicos de la frecuencia de encendido (tono "motosierra")
    phase = 2 * np.pi * np.cumsum(f) / SR
    buzz = sum((1.0 / h) * np.sin(h * phase) for h in range(1, 9))
    rpm = np.clip((freq - 45) / 145, 0, 1)
    out = muff + 0.12 * buzz * (0.3 + 0.7 * rpm)
    # cadena y espada: ruido agudo modulado por las revoluciones
    ch = band(rng.standard_normal(n), 2800, 7000) * (0.15 + 0.85 * rpm ** 1.5) * chain
    out = out + 0.35 * ch * (np.max(np.abs(out)) / (np.max(np.abs(ch)) + 1e-9)) * 0.5
    if amp is not None: out = out * amp
    return np.tanh(1.8 * out / (np.max(np.abs(out)) + 1e-9))

def curve(points, dur):
    """[(t, valor)] -> curva por muestra (interpolación suavizada)."""
    n = int(dur * SR); t = np.arange(n) / SR
    ts, vs = zip(*points)
    c = np.interp(t, ts, vs)
    return lfilter(*butter(1, 12 / (SR / 2)), c) if len(points) > 2 else c

def env(n, a, r):
    e = np.ones(n); A, R = int(a * SR), int(r * SR)
    if A: e[:A] = np.linspace(0, 1, A)
    if R: e[-R:] = np.linspace(1, 0, R)
    return e

def pull_cord(dur=0.42, seed=7):
    """Tirón del arrancador: zumbido de cuerda que sube de tono y un chasquido."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 300 + 2200 * (t / dur) ** 0.7
    ph = 2 * np.pi * np.cumsum(f) / SR
    z = (np.sin(ph) * 0.4 + band(np.random.default_rng(seed).standard_normal(n), 900, 4000)) * np.sin(np.pi * t / dur) ** 0.6
    z[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    click = np.zeros(n); k = int(0.03 * SR); click[:k] = np.random.default_rng(seed + 1).standard_normal(k) * np.exp(-np.arange(k) / (0.004 * SR))
    return z / np.max(np.abs(z)) * 0.7 + click * 0.5

os.makedirs(OUT, exist_ok=True)

# --- ralentí: 2 s en bucle sin costura (fundido cruzado del final sobre el principio)
D, X = 2.0, 0.25
fr = 48 * (1 + 0.05 * smooth_noise(int((D + X) * SR), 1.5, 3))
idle = engine(fr, misfire=0.03, seed=11, chain=0.25)
N, F = int(D * SR), int(X * SR)
loop = idle[:N].copy()
w = np.linspace(0, 1, F)
loop[:F] = idle[:F] * w + idle[N:N + F] * (1 - w)
write("TOC_ChainsawIdle.wav", loop, 0.6)

# --- golpe al aire: acelera a fondo y vuelve
fr = curve([(0, 50), (0.18, 185), (0.6, 192), (0.85, 120), (1.15, 60)], 1.15)
write("TOC_ChainsawRev.wav", engine(fr, misfire=0.01, seed=21) * env(len(fr), 0.02, 0.15))

# --- al dar: a fondo, se ahoga al morder y rechina
fr = curve([(0, 185), (0.12, 175), (0.3, 118), (0.5, 140), (0.75, 175), (0.95, 120)], 0.95)
e = engine(fr, misfire=0.0, seed=31, chain=1.6)
n = len(fr); t = np.arange(n) / SR
grind = band(rng.standard_normal(n), 1300, 4200) * (0.6 + 0.4 * np.abs(smooth_noise(n, 30, 33)))
grind *= np.clip(np.sin(np.pi * np.clip((t - 0.08) / 0.75, 0, 1)), 0, 1)
wet = band(rng.standard_normal(n), 150, 700) * np.exp(-np.maximum(t - 0.1, 0) / 0.08) * (t > 0.1)
cut = e + 0.55 * grind / np.max(np.abs(grind)) + 0.4 * wet / (np.max(np.abs(wet)) + 1e-9)
write("TOC_ChainsawCut.wav", np.tanh(1.4 * cut) * env(n, 0.005, 0.12))

# --- arranque: tirón, petardeo, arranca, acelerón y queda al ralentí
p = pull_cord(0.42, 5)
fr = curve([(0, 18), (0.15, 30), (0.35, 70), (0.55, 175), (0.95, 180), (1.3, 70), (1.9, 50)], 1.9)
mis = np.clip(1.0 - np.arange(len(fr)) / (0.4 * SR), 0.03, 0.85)
run = engine(fr, misfire=mis, seed=41) * env(len(fr), 0.05, 0.25)
start = np.concatenate([p, np.zeros(int(0.03 * SR)), run * 0.95])
write("TOC_ChainsawStart.wav", start)

# --- tirón fallido: tirón + un par de toses
p = pull_cord(0.4, 9)
fr = curve([(0, 22), (0.5, 14)], 0.6)
cough = engine(fr, misfire=0.55, seed=51) * env(len(fr), 0.01, 0.4) * 0.6
write("TOC_ChainsawPull.wav", np.concatenate([p, cough]), 0.8)

# --- apagado: cae de vueltas con fallos hasta pararse
fr = curve([(0, 55), (0.5, 32), (1.0, 12)], 1.1)
mis = np.linspace(0.05, 0.7, len(fr))
stop = engine(fr, misfire=mis, seed=61, chain=0.3) * env(len(fr), 0.0, 0.5)
write("TOC_ChainsawStop.wav", stop, 0.7)
