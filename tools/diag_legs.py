"""Diagnóstico: qué vértices del muñón (Amputation_Left_LowerLeg) quedan FUERA de la prótesis.
Para cada vértice del muñón entre y0..y1 se calcula la sección de la prótesis a esa altura y se compara
el radio polar del vértice con el de la prótesis en la misma dirección."""
import os, sys, math
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from render_icons import load_x

MOD = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\models_X"

def section(v, f, y):
    pts = []
    for tri in f:
        for k in range(3):
            a, b = v[tri[k]], v[tri[(k + 1) % 3]]
            if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
                t = (y - a[1]) / (b[1] - a[1]); pts.append(a + (b - a) * t)
    return np.array(pts) if pts else np.zeros((0, 3))

def check(sex, stump, pros, y0, y1):
    sv, sf, _ = load_x(os.path.join(MOD, "Amputation", stump))
    pv, pf, _ = load_x(os.path.join(MOD, "Prosthesis", pros))
    sv = np.array(sv); pv = np.array(pv)
    worst = []
    # vértices del muñón y puntos de sección del muñón (cada 5 mm)
    cand = [tuple(p) for p in sv if y0 <= p[1] <= y1 and p[0] > 0.02]
    for y in np.arange(y0, y1, 0.005):
        cand += [tuple(p) for p in section(sv, sf, y) if p[0] > 0.02]
    for p in cand:
        p = np.array(p)
        ps = section(pv, pf, p[1])
        if len(ps) < 6: continue
        # sólo la parte de la prótesis cerca de la pierna (x del mismo lado)
        cx, cz = (ps[:, 0].min() + ps[:, 0].max()) / 2, (ps[:, 2].min() + ps[:, 2].max()) / 2
        ang = math.atan2(p[2] - cz, p[0] - cx); rp = math.hypot(p[2] - cz, p[0] - cx)
        pa = np.arctan2(ps[:, 2] - cz, ps[:, 0] - cx); pr = np.hypot(ps[:, 2] - cz, ps[:, 0] - cx)
        d = np.abs((pa - ang + math.pi) % (2 * math.pi) - math.pi)
        near = d <= 0.25
        rr = pr[near].max() if near.any() else pr[np.argsort(d)[:2]].max()
        if rp > rr - 0.0005:
            worst.append((rp - rr, p[0], p[1], p[2], math.degrees(ang)))
    worst.sort(reverse=True)
    print(sex, stump, pros, "fuera:", len(worst), "de", len(cand))
    for w in worst[:12]:
        print("  +%.4f  x=%.3f y=%.3f z=%.3f ang=%.0f" % w)

for sex, sx in (("Male", "M"), ("Female", "F")):
    for tier in ("pegLeg", "mechLeg", "medicalLeg"):
        check(sex, "Amputation_Left_Foot_%s.X" % sex, "%sAnkle_L_%s.X" % (tier, sx), 0.078, 0.19)
        check(sex, "Amputation_Left_LowerLeg_%s.X" % sex, "%s_L_%s.X" % (tier, sx), 0.252, 0.335)
        check(sex, "Amputation_Left_UpperLeg_%s.X" % sex, "%sThigh_L_%s.X" % (tier, sx), 0.402, 0.468)
