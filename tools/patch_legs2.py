"""Secciones de pierna por casco radial (no elipse) + suavizado, y pie en cuña. Sustituye
leg_profile/shaped_tube/shaped_foot/peg_leg/mech_leg en build_assets.py."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "build_assets.py")
s = open(p, encoding="utf-8").read()
a = s.index("def leg_profile(")
b = s.index("def peg_arm(body, side):")

NEW = r'''
def _leg_points(body, side):
    V = body["verts"]; W = body["weights"]
    bones = ("Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side)
    return np.array([V[i] for i in range(len(V)) if any(bn in W[i] for bn in bones) and not any("Dress" in bn for bn in W[i])])

def leg_section(pts, y, clearance=0.003, segs=18, window=0.03, smooth=1):
    """Anillo 3D (segs puntos) que envuelve la pierna a la altura y: radio máximo por sector angular
    de los vértices de la franja [y-window, y+window], más holgura, suavizado circularmente."""
    sl = pts[np.abs(pts[:, 1] - y) <= window]
    if len(sl) < 6:
        sl = pts[np.argsort(np.abs(pts[:, 1] - y))[:10]]
    cx, cz = (sl[:, 0].min() + sl[:, 0].max()) / 2, (sl[:, 2].min() + sl[:, 2].max()) / 2
    ang = np.arctan2(sl[:, 2] - cz, sl[:, 0] - cx)
    dist = np.hypot(sl[:, 0] - cx, sl[:, 2] - cz)
    r = np.zeros(segs)
    for k in range(segs):
        t = 2 * math.pi * k / segs
        d = np.abs((ang - t + math.pi) % (2 * math.pi) - math.pi)
        w = np.exp(-(d / 0.45) ** 2)                         # ventana angular suave
        r[k] = (dist * w).max() if w.max() > 0.2 else np.median(dist)
        # garantizar que ningún vértice del sector quede fuera
        inside = d < math.pi / segs * 1.5
        if inside.any(): r[k] = max(r[k], dist[inside].max())
    for _ in range(smooth):
        r = (np.roll(r, 1) + 2 * r + np.roll(r, -1)) / 4
    r = r + clearance
    ring = [np.array([cx + r[k] * math.cos(2 * math.pi * k / segs), y, cz + r[k] * math.sin(2 * math.pi * k / segs)]) for k in range(segs)]
    return ring

def leg_profile(body, side, y, clearance=0.003, window=0.028):
    """Compatibilidad: centro y radios medios de la sección."""
    ring = leg_section(_leg_points(body, side), y, clearance)
    R = np.array(ring); c = R.mean(0)
    return np.array([c[0], y, c[2]]), (R[:, 0].max() - R[:, 0].min()) / 2, (R[:, 2].max() - R[:, 2].min()) / 2

def loft(m, rings, bone, uv_v=(0.0, 1.0), close_start=False, close_end=False, flip=False):
    """Une anillos consecutivos (misma cantidad de puntos) con triángulos; tapas en abanico opcionales."""
    segs = len(rings[0]); ids = []
    for k, ring in enumerate(rings):
        row = []
        for s_, q in enumerate(ring):
            row.append(len(m.v)); m.v.append(np.array(q)); m.n.append(np.array([0.0, 1.0, 0.0]))
            m.uv.append((s_ / segs, uv_v[0] + (uv_v[1] - uv_v[0]) * k / max(1, len(rings) - 1))); m.w.append(bone)
        ids.append(row)
    for k in range(len(rings) - 1):
        a_, b_ = ids[k], ids[k + 1]
        for s_ in range(segs):
            s2 = (s_ + 1) % segs
            if flip:
                m.add_tri(a_[s_], b_[s2], b_[s_]); m.add_tri(a_[s_], a_[s2], b_[s2])
            else:
                m.add_tri(a_[s_], b_[s_], b_[s2]); m.add_tri(a_[s_], b_[s2], a_[s2])
    for closing, row, first in ((close_start, ids[0], True), (close_end, ids[-1], False)):
        if closing:
            c = np.mean([m.v[i] for i in row], axis=0)
            ci = len(m.v); m.v.append(c); m.n.append(np.array([0.0, 1.0, 0.0])); m.uv.append(((0.5), (uv_v[0] + uv_v[1]) / 2)); m.w.append(bone)
            for s_ in range(segs):
                s2 = (s_ + 1) % segs
                if first != flip: m.add_tri(ci, row[s2], row[s_])
                else: m.add_tri(ci, row[s_], row[s2])
    # normales suaves reales
    V = np.array(m.v); F = np.array(m.f)
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3): np.add.at(N, F[:, k], fn)
    l = np.linalg.norm(N, axis=1); l[l == 0] = 1
    m.n = list(N / l[:, None])
    return ids

def shaped_tube(m, body, side, ys, bone, clearance, uv_v, segs=18, close_start=False, close_end=False, scale=1.0):
    pts = _leg_points(body, side)
    rings = [leg_section(pts, y, clearance, segs) for y in ys]
    # suavizado a lo largo de la pierna (evita escalones entre franjas)
    R = np.array(rings)
    for _ in range(2):
        for k in range(1, len(R) - 1):
            R[k] = (R[k - 1] + 2 * R[k] + R[k + 1]) / 4
            R[k][:, 1] = ys[k]
    rings = [list(r) for r in R]
    loft(m, rings, bone, uv_v, close_start, close_end)
    centers = [np.array(r).mean(0) for r in rings]
    return centers, rings

def shaped_foot(m, body, side, bone, uv_v, clearance=0.003, lift=0.0):
    """Pie protésico en cuña con las medidas del pie del cuerpo: talón alto y redondo, punta baja.
    Anillos (x,y) a lo largo de Z desde el talón (+z) a la punta (-z)."""
    V = body["verts"]; W = body["weights"]
    bn = "Bip01_%s_Foot" % side
    pts = np.array([V[i] for i in range(len(V)) if bn in W[i] and not any("Dress" in b for b in W[i])])
    zh, zt = pts[:, 2].max(), pts[:, 2].min()
    cx = (pts[:, 0].min() + pts[:, 0].max()) / 2
    half_w = (pts[:, 0].max() - pts[:, 0].min()) / 2 + clearance
    L = zh - zt
    rings = []
    segs = 14
    prof = [(0.00, 0.60, 0.040), (0.10, 0.80, 0.046), (0.25, 1.00, 0.040), (0.45, 1.00, 0.032), (0.65, 0.98, 0.026), (0.85, 0.90, 0.018), (1.00, 0.65, 0.012)]
    for t, wf, h in prof:
        z = zh - L * t
        for_ring = []
        for k in range(segs):
            ang = 2 * math.pi * k / segs
            x = cx + half_w * wf * math.cos(ang)
            y = 0.002 + lift + h / 2 + (h / 2) * math.sin(ang)
            for_ring.append(np.array([x, y, z]))
        rings.append(for_ring)
    loft(m, rings, bone, uv_v, close_start=True, close_end=True, flip=True)

def peg_leg(body, side):
    """Pata de palo esbelta: encaje de cuero con la forma del muslo bajo y de la pantorrilla
    (holgura ~3 mm: cabe bajo el pantalón) y pata de madera torneada bajo el tobillo."""
    bone = "Bip01_%s_Calf" % side
    m = MeshB()
    ys = [0.33, 0.30, 0.27, 0.24, 0.21, 0.18, 0.15, 0.12, 0.095, 0.075, 0.062]
    centers, rings = shaped_tube(m, body, side, ys, bone, 0.0032, (0.0, 0.25), close_start=True, close_end=True)
    # ribete superior y dos correas finas (anillos cerrados apenas más anchos)
    pts = _leg_points(body, side)
    for y in (0.325, 0.20, 0.10):
        r1 = leg_section(pts, y + 0.006, 0.0032 + 0.0025); r2 = leg_section(pts, y - 0.006, 0.0032 + 0.0025)
        for q in r1: q[1] = y + 0.006
        for q in r2: q[1] = y - 0.006
        loft(m, [r1, r2], bone, (0.26, 0.29), close_start=True, close_end=True)
    # pata de madera torneada desde el tobillo al suelo
    base = centers[-1]
    peg = [np.array([base[0], 0.062, base[2]]), np.array([base[0], 0.048, base[2]]), np.array([base[0], 0.03, base[2]]), np.array([base[0], 0.012, base[2]])]
    m.tube(peg, [(0.028, 0.028), (0.021, 0.021), (0.018, 0.018), (0.016, 0.016)], (X, Z), 12, bone, (0, 1), (0.3, 0.9), close_start=True)
    tip = np.array([base[0], 0.012, base[2]])
    m.tube([tip, np.array([base[0], 0.0, base[2]])], [(0.019, 0.019), (0.017, 0.017)], (X, Z), 12, bone, (0, 1), (0.92, 1.0), close_end=True)
    return m

def mech_leg(body, side, medical=False):
    """Pierna mecánica (chapa + barras) o médica (carbono moldeado): encaje y caña con la forma
    de la pierna, tobillo y pie en cuña con las medidas del pie del cuerpo."""
    calf, foot = "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side
    m = MeshB()
    # encaje sobre el muñón: muslo bajo
    shaped_tube(m, body, side, [0.33, 0.305, 0.28, 0.255], calf, 0.004, (0.0, 0.2), close_start=True, close_end=True)
    ys = [0.255, 0.225, 0.195, 0.165, 0.135, 0.105, 0.085, 0.07]
    if medical:
        shaped_tube(m, body, side, ys, calf, 0.003, (0.2, 0.8), close_start=True, close_end=True)
    else:
        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0025, (0.2, 0.8), close_start=True, close_end=True)
        # dos barras de acero a los lados, pegadas a la chapa
        for sgn in (-1, 1):
            path = []
            for k, r in enumerate(rings):
                R = np.array(r); c = R.mean(0)
                edge = R[:, 0].max() if sgn > 0 else R[:, 0].min()
                path.append(np.array([edge + sgn * 0.004, ys[k], c[2]]))
            m.tube(path, [(0.0045, 0.006)] * len(path), (X, Z), 8, calf, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
    # tobillo
    pts = _leg_points(body, side)
    r_top = leg_section(pts, 0.07, 0.0); c = np.array(r_top).mean(0)
    m.tube([np.array([c[0], 0.072, c[2]]), np.array([c[0], 0.04, c[2]])], [(0.024, 0.028), (0.026, 0.03)], (X, Z), 12, foot, (0, 1), (0.8, 0.86), close_start=True)
    shaped_foot(m, body, side, foot, (0.86, 1.0), clearance=0.0035 if medical else 0.003)
    return m

'''
s = s[:a] + NEW.lstrip("\n") + s[b:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("legs2 applied")
