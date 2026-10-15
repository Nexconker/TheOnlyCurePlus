"""Reemplaza peg_leg / mech_leg en build_assets.py por versiones que siguen la forma real de la pierna
(secciones elípticas muestreadas del cuerpo vanilla + holgura de pocos milímetros)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "build_assets.py")
s = open(p, encoding="utf-8").read()
a = s.index("def peg_leg(body, side):")
b = s.index("def peg_arm(body, side):")

NEW = r'''
def leg_profile(body, side, y, clearance=0.003, window=0.028):
    """Sección elíptica (centro, rx, rz) de la pierna del cuerpo a la altura y, a partir de los
    vértices visibles del muslo/pantorrilla/pie en una franja alrededor de y."""
    V = body["verts"]; W = body["weights"]
    bones = ("Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side)
    idx = [i for i in range(len(V)) if any(bn in W[i] for bn in bones) and not any("Dress" in bn for bn in W[i])]
    pts = np.array([V[i] for i in idx if abs(V[i][1] - y) <= window])
    if len(pts) < 4:
        # franja vacía: tomar los 8 vértices más cercanos en altura
        near = sorted(idx, key=lambda i: abs(V[i][1] - y))[:8]
        pts = np.array([V[i] for i in near])
    cx, cz = (pts[:, 0].min() + pts[:, 0].max()) / 2, (pts[:, 2].min() + pts[:, 2].max()) / 2
    rx = (pts[:, 0].max() - pts[:, 0].min()) / 2 + clearance
    rz = (pts[:, 2].max() - pts[:, 2].min()) / 2 + clearance
    return np.array([cx, y, cz]), rx, rz

def shaped_tube(m, body, side, ys, bone, clearance, uv_v, segs=18, close_start=False, close_end=False, scale=1.0):
    pts, radii = [], []
    for y in ys:
        c, rx, rz = leg_profile(body, side, y, clearance)
        pts.append(c); radii.append((rx * scale, rz * scale))
    m.tube(pts, radii, (X, Z), segs, bone, (0, 1), uv_v, close_start=close_start, close_end=close_end)
    return pts, radii

def shaped_foot(m, body, side, bone, uv_v, clearance=0.003, lift=0.0):
    """Pie con la forma del pie del cuerpo: secciones (x,y) a lo largo de Z (talón -> punta)."""
    V = body["verts"]; W = body["weights"]
    bn = "Bip01_%s_Foot" % side
    pts = np.array([V[i] for i in range(len(V)) if bn in W[i] and not any("Dress" in b for b in W[i])])
    z0, z1 = pts[:, 2].max(), pts[:, 2].min()          # talón (+z) -> punta (-z)
    path, radii = [], []
    n = 7
    for k in range(n):
        z = z0 + (z1 - z0) * k / (n - 1)
        sl = pts[np.abs(pts[:, 2] - z) < 0.03]
        if len(sl) < 3: sl = pts[np.argsort(np.abs(pts[:, 2] - z))[:6]]
        cx = (sl[:, 0].min() + sl[:, 0].max()) / 2
        rx = (sl[:, 0].max() - sl[:, 0].min()) / 2 + clearance
        ry = (sl[:, 1].max() - sl[:, 1].min()) / 2 + clearance
        cy = (sl[:, 1].min() + sl[:, 1].max()) / 2 + lift
        path.append(np.array([cx, cy, z])); radii.append((rx, max(ry, 0.008)))
    m.tube(path, radii, (X, Y), 14, bone, (0, 1), uv_v, close_start=True, close_end=True)

def peg_leg(body, side):
    """Pata de palo esbelta: encaje de cuero con la forma del muslo bajo y de la pantorrilla
    (holgura 3-4 mm, cabe bajo el pantalón) y pata de madera torneada bajo el tobillo."""
    bone = "Bip01_%s_Calf" % side
    m = MeshB()
    # encaje: del muslo bajo (sobre la tapa del muñón) al tobillo, siguiendo la pierna
    ys = [0.33, 0.30, 0.27, 0.24, 0.20, 0.16, 0.12, 0.085, 0.065]
    pts, radii = shaped_tube(m, body, side, ys, bone, 0.0035, (0.0, 0.25), close_start=True, close_end=True)
    # ribete superior y dos correas finas (anillos cerrados apenas más anchos)
    for y, uv in ((0.325, (0.26, 0.29)), (0.21, (0.26, 0.29)), (0.10, (0.26, 0.29))):
        c, rx, rz = leg_profile(body, side, y, 0.0035)
        m.tube([c + Y * 0.006, c - Y * 0.006], [(rx + 0.0025, rz + 0.0025)] * 2, (X, Z), 18, bone, (0, 1), uv, close_start=True, close_end=True)
    # pata de madera torneada desde el tobillo al suelo
    base = pts[-1]
    peg = [np.array([base[0], 0.065, base[2]]), np.array([base[0], 0.05, base[2]]), np.array([base[0], 0.03, base[2]]), np.array([base[0], 0.012, base[2]])]
    m.tube(peg, [(0.030, 0.030), (0.022, 0.022), (0.019, 0.019), (0.016, 0.016)], (X, Z), 12, bone, (0, 1), (0.3, 0.9), close_start=True)
    tip = np.array([base[0], 0.012, base[2]])
    m.tube([tip, np.array([base[0], 0.0, base[2]])], [(0.019, 0.019), (0.017, 0.017)], (X, Z), 12, bone, (0, 1), (0.92, 1.0), close_end=True)
    return m

def mech_leg(body, side, medical=False):
    """Pierna mecánica (chapa + barras) o médica (carbono moldeado): encaje y caña con la forma
    de la pierna, tobillo y pie con la forma del pie del cuerpo."""
    calf, foot = "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side
    m = MeshB()
    # encaje (sobre el muñón, forma del muslo bajo)
    shaped_tube(m, body, side, [0.33, 0.30, 0.27, 0.245], calf, 0.004, (0.0, 0.2), close_start=True)
    if medical:
        # caña de carbono con la forma de la pantorrilla hasta el tobillo
        shaped_tube(m, body, side, [0.245, 0.21, 0.17, 0.13, 0.10, 0.075], calf, 0.003, (0.2, 0.8), close_end=True)
    else:
        # caña de chapa (un poco más ceñida) + dos barras de acero a los lados
        pts, radii = shaped_tube(m, body, side, [0.245, 0.21, 0.17, 0.13, 0.10, 0.075], calf, 0.0025, (0.2, 0.8), close_end=True)
        for k in range(len(pts) - 1):
            for sgn in (-1, 1):
                a_, b_ = pts[k], pts[k + 1]
                ra, rb = radii[k][0] + 0.004, radii[k + 1][0] + 0.004
                m.tube([a_ + X * sgn * ra, b_ + X * sgn * rb], [(0.005, 0.006), (0.005, 0.006)], (X, Z), 8, calf, (0, 1), (0.85, 0.95), close_start=(k == 0), close_end=(k == len(pts) - 2))
    # tobillo: pequeño cilindro entre la caña y el pie
    c, rx, rz = leg_profile(body, side, 0.075, 0.0)
    m.tube([np.array([c[0], 0.078, c[2]]), np.array([c[0], 0.045, c[2]])], [(rx * 0.75, rz * 0.7), (rx * 0.8, rz * 0.75)], (X, Z), 12, foot, (0, 1), (0.8, 0.86), close_start=True)
    # pie con la forma del pie del cuerpo
    shaped_foot(m, body, side, foot, (0.0, 0.86, 1.0, 1.0) if False else (0.86, 1.0), clearance=0.0035 if medical else 0.003)
    return m

'''
s = s[:a] + NEW.lstrip("\n") + s[b:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("legs replaced")
