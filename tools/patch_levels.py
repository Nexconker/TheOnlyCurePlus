"""Prótesis por nivel de amputación + gancho/brazo mecánico/médico propios + enrollado de caras correcto.

1. MeshB.tube y loft orientan cada cara hacia fuera (convención vanilla: cross(b-a, c-a) · normal > 0).
2. Secciones genéricas a lo largo de un eje (brazos) = misma técnica que las piernas.
3. peg_leg / mech_leg aceptan level: "Ankle" (pie), "" (pantorrilla), "Thigh" (muslo).
4. peg_arm / hook_arm / mech_arm aceptan level: "" (antebrazo), "Wrist" (mano).
5. build_models genera todas las variantes y los modelos de suelo; build_textures genera hookArm/normalArm/medicalArm.
"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "build_assets.py")
s = open(p, encoding="utf-8").read()

# ------------------------------------------------------------------ 1. enrollado en MeshB.tube
old_tube_caps = '''        for closing, ring, p, flip in ((close_start, rings[0], path_pts[0], True), (close_end, rings[-1], path_pts[-1], False)):
            if closing:
                axis = np.cross(ax, az); axis = axis / (np.linalg.norm(axis) or 1)
                if flip: axis = -axis
                ci = len(self.v); self.v.append(p); self.n.append(axis); self.uv.append(((uv_u[0] + uv_u[1]) / 2, (uv_v[0] + uv_v[1]) / 2)); self.w.append(bone)
                for s in range(segs):
                    s2 = (s + 1) % segs
                    tri = (ci, ring[s2], ring[s]) if flip else (ci, ring[s], ring[s2])
                    self.add_tri(*tri)'''
new_tube_caps = '''        first_face = len(self.f) - (len(rings) - 1) * segs * 2
        fwd_dir = np.array(path_pts[-1]) - np.array(path_pts[0])
        if np.linalg.norm(fwd_dir) < 1e-9: fwd_dir = np.cross(ax, az)
        fwd_dir = fwd_dir / (np.linalg.norm(fwd_dir) or 1)
        for closing, ring, p, flip in ((close_start, rings[0], path_pts[0], True), (close_end, rings[-1], path_pts[-1], False)):
            if closing:
                axis = -fwd_dir if flip else fwd_dir
                ci = len(self.v); self.v.append(np.array(p, float)); self.n.append(axis); self.uv.append(((uv_u[0] + uv_u[1]) / 2, (uv_v[0] + uv_v[1]) / 2)); self.w.append(bone)
                for s in range(segs):
                    s2 = (s + 1) % segs
                    self.add_tri(ci, ring[s], ring[s2])
        self.orient(first_face)
    def orient(self, first_face=0):
        """Da la vuelta a las caras (desde first_face) cuyo producto vectorial no apunta como la normal media de sus vértices."""
        for i in range(max(0, first_face), len(self.f)):
            a, b, c = self.f[i]
            fn = np.cross(self.v[b] - self.v[a], self.v[c] - self.v[a])
            ref = self.n[a] + self.n[b] + self.n[c]
            if np.dot(fn, ref) < 0: self.f[i] = (a, c, b)'''
assert old_tube_caps in s, "tube caps"
s = s.replace(old_tube_caps, new_tube_caps)

# ------------------------------------------------------------------ 1b. enrollado en loft
old_loft_a = '''    for k in range(len(rings) - 1):
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
    return ids'''
new_loft_a = '''    centers = [np.mean([m.v[i] for i in row], axis=0) for row in ids]
    first_face = len(m.f)
    refs = []            # dirección "hacia fuera" de referencia por cara nueva
    for k in range(len(rings) - 1):
        a_, b_ = ids[k], ids[k + 1]
        cmid = (centers[k] + centers[k + 1]) / 2
        for s_ in range(segs):
            s2 = (s_ + 1) % segs
            m.add_tri(a_[s_], b_[s_], b_[s2]); m.add_tri(a_[s_], b_[s2], a_[s2])
            refs.append(cmid); refs.append(cmid)
    for closing, row, first in ((close_start, ids[0], True), (close_end, ids[-1], False)):
        if closing:
            c = centers[0] if first else centers[-1]
            axis_dir = (centers[0] - centers[1]) if first else (centers[-1] - centers[-2])
            ci = len(m.v); m.v.append(c); m.n.append(np.array([0.0, 1.0, 0.0])); m.uv.append(((0.5), (uv_v[0] + uv_v[1]) / 2)); m.w.append(bone)
            for s_ in range(segs):
                s2 = (s_ + 1) % segs
                m.add_tri(ci, row[s_], row[s2]); refs.append(("cap", axis_dir))
    # orientar: caras laterales hacia fuera del eje; tapas en la dirección del eje
    for i, ref in zip(range(first_face, len(m.f)), refs):
        a, b, c = m.f[i]
        fn = np.cross(m.v[b] - m.v[a], m.v[c] - m.v[a])
        if isinstance(ref, tuple): outward = ref[1]
        else: outward = (m.v[a] + m.v[b] + m.v[c]) / 3 - ref
        if np.dot(fn, outward) < 0: m.f[i] = (a, c, b)
    # normales suaves reales (de las caras ya orientadas)
    V = np.array(m.v); F = np.array(m.f)
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3): np.add.at(N, F[:, k], fn)
    l = np.linalg.norm(N, axis=1); l[l == 0] = 1
    m.n = list(N / l[:, None])
    return ids'''
assert old_loft_a in s, "loft"
s = s.replace(old_loft_a, new_loft_a)

# ------------------------------------------------------------------ 2-4. prótesis
a = s.index("def peg_leg(body, side):")
b = s.index("def leg_tourniquet(body, side):")

NEW = r'''
# ------------------------------------------------------------------ secciones genéricas a lo largo de un eje

_limb_cache = {}
def _limb_mesh(body, bones, side):
    key = (id(body), tuple(bones), side)
    if key not in _limb_cache:
        V = body["verts"]; W = body["weights"]; faces = []
        for f in body["faces"]:
            if face_is_hidden(body, f): continue
            if any(any(bn in W[vi] for bn in bones) for vi in f):
                if (np.mean([V[vi][0] for vi in f]) > 0) == (side == "L"): faces.append(f)
        idx = sorted({vi for f in faces for vi in f})
        _limb_cache[key] = (V, faces, np.array([V[i] for i in idx]))
    return _limb_cache[key]

def axis_section(body, bones, side, o, axis, t):
    """Intersección de la superficie del miembro con el plano perpendicular a axis a distancia t de o."""
    V, faces, _ = _limb_mesh(body, bones, side)
    pts = []
    for f in faces:
        for k in range(3):
            a_, b_ = V[f[k]], V[f[(k + 1) % 3]]
            ta, tb = (a_ - o) @ axis - t, (b_ - o) @ axis - t
            if ta * tb <= 0 and ta != tb:
                s_ = ta / (ta - tb); pts.append(a_ + (b_ - a_) * s_)
    return np.array(pts) if pts else np.zeros((0, 3))

def axis_ring(body, bones, side, o, axis, u, v, t, clearance, segs=24, band=0.014, smooth=1):
    """Anillo que envuelve la sección real del miembro (más los vértices a ±band) con holgura."""
    V, faces, P = _limb_mesh(body, bones, side)
    sl = axis_section(body, bones, side, o, axis, t)
    tt = (P - o) @ axis
    bandp = P[np.abs(tt - t) <= band]
    if len(bandp): sl = np.vstack([sl, bandp]) if len(sl) else bandp
    if len(sl) < 4: sl = P[np.argsort(np.abs(tt - t))[:10]]
    pu, pv = (sl - o) @ u, (sl - o) @ v
    cu, cv = (pu.min() + pu.max()) / 2, (pv.min() + pv.max()) / 2
    ang = np.arctan2(pv - cv, pu - cu); dist = np.hypot(pu - cu, pv - cv)
    r = np.zeros(segs)
    for k in range(segs):
        th = -math.pi + 2 * math.pi * k / segs
        d = np.abs((ang - th + math.pi) % (2 * math.pi) - math.pi)
        sector = d <= 1.6 * math.pi / segs + 0.02
        r[k] = dist[sector].max() if sector.any() else dist[np.argsort(d)[:2]].max()
    for _ in range(smooth): r = np.maximum(r, (np.roll(r, 1) + np.roll(r, -1)) / 2 * 0.98)
    r = r + clearance
    c = o + axis * t
    return [c + u * (cu + r[k] * math.cos(-math.pi + 2 * math.pi * k / segs)) + v * (cv + r[k] * math.sin(-math.pi + 2 * math.pi * k / segs)) for k in range(segs)]

def axis_tube(m, body, bones, side, o, axis, u, v, ts, bone, clearance, uv_v, segs=24, close_start=False, close_end=False, scale=1.0):
    rings = [axis_ring(body, bones, side, o, axis, u, v, t, clearance, segs) for t in ts]
    R = np.array(rings)
    C = R.mean(1)
    rel = R - C[:, None, :]
    pu, pv = rel @ u, rel @ v
    rad = np.hypot(pu, pv); ang = np.arctan2(pv, pu)
    for _ in range(2):
        for k in range(1, len(R) - 1):
            rad[k] = np.maximum(rad[k], (rad[k - 1] + rad[k + 1]) / 2 * 0.97)
    rad = rad * scale
    R = C[:, None, :] + u[None, None, :] * (rad * np.cos(ang))[:, :, None] + v[None, None, :] * (rad * np.sin(ang))[:, :, None]
    rings = [list(r) for r in R]
    loft(m, rings, bone, uv_v, close_start, close_end)
    return [np.array(r).mean(0) for r in rings], rings

def path_tube(m, pts, radii, ref, segs, bone, uv_v, close_start=True, close_end=True):
    """Tubo cuyos anillos son perpendiculares a la tangente local del camino (para curvas: gancho, pulgar)."""
    rings = []
    for k, (p, r) in enumerate(zip(pts, radii)):
        tan = np.array(pts[min(k + 1, len(pts) - 1)]) - np.array(pts[max(k - 1, 0)])
        tan = tan / (np.linalg.norm(tan) or 1)
        u = np.array(ref, float) - tan * (np.array(ref, float) @ tan); u = u / (np.linalg.norm(u) or 1)
        v = np.cross(tan, u)
        rings.append([np.array(p) + u * (r[0] * math.cos(2 * math.pi * s_ / segs)) + v * (r[1] * math.sin(2 * math.pi * s_ / segs)) for s_ in range(segs)])
    loft(m, rings, bone, uv_v, close_start, close_end)

# ------------------------------------------------------------------ piernas (por nivel)

LEG_LEVELS = {"Ankle": "Foot", "": "LowerLeg", "Thigh": "UpperLeg"}      # sufijo del modelo -> parte amputada
ARM_LEVELS = {"Wrist": "Hand", "": "ForeArm"}

def peg_shaft(m, cx, cz, y_top, y_knee, thigh, calf, r_top=0.028):
    """Pata de madera torneada desde y_top hasta el suelo; si cruza la rodilla se parte en dos huesos."""
    def prof(y):
        t = (y_top - y) / max(1e-6, y_top)        # 0 arriba .. 1 abajo
        return r_top * (1 - t) + 0.016 * t + 0.004 * math.sin(math.pi * t) * (1 if t < 0.5 else 0.3)
    def seg(y0, y1, bone, uv):
        n = max(2, int((y0 - y1) / 0.035) + 2)
        ys = [y0 + (y1 - y0) * k / (n - 1) for k in range(n)]
        pts = [np.array([cx, y, cz]) for y in ys]; rr = [(prof(y), prof(y)) for y in ys]
        m.tube(pts, rr, (X, Z), 12, bone, (0, 1), uv, close_start=True, close_end=True)
    if y_top > y_knee + 0.02:
        seg(y_top, y_knee, thigh, (0.3, 0.6)); seg(y_knee, 0.012, calf, (0.6, 0.9))
    else:
        seg(y_top, 0.012, calf, (0.3, 0.9))
    m.tube([np.array([cx, 0.012, cz]), np.array([cx, 0.0, cz])], [(0.019, 0.019), (0.017, 0.017)], (X, Z), 12, calf, (0, 1), (0.92, 1.0), close_start=True, close_end=True)

def leg_straps(m, body, side, bone, ys, clearance):
    for y in ys:
        r1 = leg_section(None, y + 0.006, clearance + 0.0025, body=body, side=side); r2 = leg_section(None, y - 0.006, clearance + 0.0025, body=body, side=side)
        for q in r1: q[1] = y + 0.006
        for q in r2: q[1] = y - 0.006
        loft(m, [r1, r2], bone, (0.26, 0.29), close_start=True, close_end=True)

def peg_leg(body, side, level=""):
    """Pata de palo esbelta con encaje de cuero a la medida del muñón:
    Ankle: manguito en la pantorrilla baja + pata corta; "": encaje muslo bajo + pantorrilla + pata;
    Thigh: encaje en el muslo, cono de madera, rótula y pata larga."""
    thigh, calf = "Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side
    m = MeshB()
    if level == "Ankle":
        ys = [0.19, 0.17, 0.15, 0.13, 0.11, 0.095, 0.08, 0.068]
        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0042, (0.0, 0.25), close_start=True, close_end=True)
        leg_straps(m, body, side, calf, (0.183, 0.10), 0.0042)
        base = centers[-1]
        peg_shaft(m, base[0], base[2], 0.068, 0.25, thigh, calf, r_top=0.026)
    elif level == "Thigh":
        ys = [0.47, 0.45, 0.43, 0.41, 0.39]
        centers, rings = shaped_tube(m, body, side, ys, thigh, 0.0045, (0.0, 0.25), close_start=True, close_end=True)
        leg_straps(m, body, side, thigh, (0.462, 0.40), 0.0045)
        # cono de madera del muslo hasta la rodilla, rótula y pata
        R = np.array(rings[-1]); c = R.mean(0)
        rx, rz = (R[:, 0].max() - R[:, 0].min()) / 2 - 0.004, (R[:, 2].max() - R[:, 2].min()) / 2 - 0.004
        m.tube([np.array([c[0], 0.39, c[2]]), np.array([c[0], 0.33, c[2]]), np.array([c[0], 0.27, c[2]])], [(rx, rz), (rx * 0.8, rz * 0.8), (0.032, 0.032)], (X, Z), 16, thigh, (0, 1), (0.3, 0.6), close_start=True, close_end=True)
        m.tube([np.array([c[0], 0.27, c[2]]), np.array([c[0], 0.258, c[2]]), np.array([c[0], 0.242, c[2]]), np.array([c[0], 0.232, c[2]])], [(0.030, 0.030), (0.036, 0.036), (0.036, 0.036), (0.030, 0.030)], (X, Z), 16, calf, (0, 1), (0.3, 0.6), close_start=True, close_end=True)
        peg_shaft(m, c[0], c[2], 0.232, 0.25, thigh, calf, r_top=0.028)
    else:
        ys = [0.33, 0.30, 0.27, 0.24, 0.21, 0.18, 0.15, 0.12, 0.095, 0.075, 0.062]
        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0042, (0.0, 0.25), close_start=True, close_end=True)
        leg_straps(m, body, side, calf, (0.325, 0.20, 0.10), 0.0042)
        base = centers[-1]
        peg_shaft(m, base[0], base[2], 0.062, 0.25, thigh, calf, r_top=0.028)
    return m

def mech_shin(m, body, side, ys, calf, medical, uv=(0.2, 0.8)):
    """Caña con la forma de la pantorrilla; mecánica: chapa + barras laterales."""
    if medical:
        return shaped_tube(m, body, side, ys, calf, 0.0036, uv, close_start=True, close_end=True)
    centers, rings = shaped_tube(m, body, side, ys, calf, 0.0032, uv, close_start=True, close_end=True)
    for sgn in (-1, 1):
        path = []
        for k, r in enumerate(rings):
            R = np.array(r); c = R.mean(0)
            edge = R[:, 0].max() if sgn > 0 else R[:, 0].min()
            path.append(np.array([edge + sgn * 0.004, ys[k], c[2]]))
        m.tube(path, [(0.0045, 0.006)] * len(path), (X, Z), 8, calf, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
    return centers, rings

def mech_leg(body, side, medical=False, level=""):
    """Pierna mecánica (chapa + barras) o médica (carbono moldeado) por nivel: Ankle (manguito en la
    pantorrilla + tobillo + pie), "" (encaje bajo la rodilla + caña + pie), Thigh (encaje de muslo,
    muslo moldeado, rodilla articulada, caña y pie)."""
    thigh, calf, foot = "Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side
    m = MeshB()
    if level == "Ankle":
        shaped_tube(m, body, side, [0.19, 0.165, 0.14], calf, 0.0048, (0.0, 0.2), close_start=True, close_end=True)
        mech_shin(m, body, side, [0.14, 0.115, 0.09, 0.07], calf, medical)
    elif level == "Thigh":
        shaped_tube(m, body, side, [0.47, 0.45, 0.43, 0.41, 0.39], thigh, 0.0048, (0.0, 0.2), close_start=True, close_end=True)
        ys = [0.39, 0.36, 0.33, 0.30, 0.275]
        if medical:
            shaped_tube(m, body, side, ys, thigh, -0.003, (0.2, 0.8), close_start=True, close_end=True)
        else:
            centers, rings = shaped_tube(m, body, side, ys, thigh, -0.004, (0.2, 0.8), close_start=True, close_end=True)
            for sgn in (-1, 1):
                path = []
                for k, r in enumerate(rings):
                    R = np.array(r); c = R.mean(0)
                    edge = R[:, 0].max() if sgn > 0 else R[:, 0].min()
                    path.append(np.array([edge + sgn * 0.004, ys[k], c[2]]))
                m.tube(path, [(0.0045, 0.006)] * len(path), (X, Z), 8, thigh, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
        # rodilla: cilindro central (Calf) + discos de bisagra a los lados
        r_k = leg_section(None, 0.27, -0.004, body=body, side=side); Rk = np.array(r_k); ck = Rk.mean(0)
        m.tube([np.array([ck[0], 0.278, ck[2]]), np.array([ck[0], 0.236, ck[2]])], [(0.030, 0.034), (0.028, 0.032)], (X, Z), 14, calf, (0, 1), (0.8, 0.86), close_start=True, close_end=True)
        for sgn in (-1, 1):
            x0 = (Rk[:, 0].max() if sgn > 0 else Rk[:, 0].min()) + sgn * 0.002
            m.tube([np.array([x0, 0.255, ck[2]]), np.array([x0 + sgn * 0.012, 0.255, ck[2]])], [(0.016, 0.016), (0.016, 0.016)], (Y, Z), 12, calf, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
        mech_shin(m, body, side, [0.236, 0.21, 0.185, 0.16, 0.135, 0.105, 0.085, 0.07], calf, medical)
    else:
        shaped_tube(m, body, side, [0.33, 0.305, 0.28, 0.255], calf, 0.0048, (0.0, 0.2), close_start=True, close_end=True)
        mech_shin(m, body, side, [0.255, 0.225, 0.195, 0.165, 0.135, 0.105, 0.085, 0.07], calf, medical)
    # tobillo y pie
    r_top = leg_section(None, 0.07, 0.0, body=body, side=side); c = np.array(r_top).mean(0)
    m.tube([np.array([c[0], 0.072, c[2]]), np.array([c[0], 0.04, c[2]])], [(0.024, 0.028), (0.026, 0.03)], (X, Z), 12, foot, (0, 1), (0.8, 0.86), close_start=True, close_end=True)
    shaped_foot(m, body, side, foot, (0.86, 1.0), clearance=0.0035 if medical else 0.003)
    return m

# ------------------------------------------------------------------ brazos (por nivel)

def arm_frame(body, side):
    o, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Forearm" % side)
    ho, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Hand" % side)
    axis = ho - o; L = np.linalg.norm(axis); axis = axis / L
    down = np.array([0.0, -1.0, 0.0]); down = down - axis * (down @ axis); down = down / np.linalg.norm(down)   # palma (abajo)
    front = np.cross(down, axis); front = front / np.linalg.norm(front)                                           # hacia -Z aprox
    if front[2] > 0: front = -front
    return o, axis, down, front, L

def arm_socket(m, body, side, level, bone, uv_socket, uv_shell, clearance=0.0045):
    """Encaje: antebrazo (sobre el muñón junto al codo + caña con forma de antebrazo) o muñeca (manguito).
    Devuelve el punto donde arranca el dispositivo terminal y la base (u, v)."""
    o, axis, down, front, L = arm_frame(body, side)
    bones = ARM_BONES[side]
    if level == "Wrist":
        axis_tube(m, body, bones, side, o, axis, down, front, [0.07, 0.085, 0.10, 0.115, 0.13, 0.142], bone, clearance, uv_socket, close_start=True, close_end=True)
        axis_tube(m, body, bones, side, o, axis, down, front, [0.142, 0.152], bone, clearance - 0.004, uv_shell, close_start=True, close_end=True)
        return o + axis * 0.152
    axis_tube(m, body, bones, side, o, axis, down, front, [-0.015, 0.0, 0.015, 0.03, 0.045], bone, clearance, uv_socket, close_start=True, close_end=True)
    axis_tube(m, body, bones, side, o, axis, down, front, [0.045, 0.07, 0.095, 0.12], bone, -0.002, uv_shell, close_start=True, close_end=True)
    return o + axis * 0.12

def arm_straps(m, body, side, bone, ts, clearance):
    o, axis, down, front, L = arm_frame(body, side)
    bones = ARM_BONES[side]
    for t in ts:
        r1 = axis_ring(body, bones, side, o, axis, down, front, t - 0.005, clearance + 0.0025)
        r2 = axis_ring(body, bones, side, o, axis, down, front, t + 0.005, clearance + 0.0025)
        loft(m, [r1, r2], bone, (0.26, 0.29), close_start=True, close_end=True)

def peg_arm(body, side, level=""):
    """Brazo de madera: copa de cuero a medida + vástago y "mano" de madera."""
    bone = "Bip01_%s_Forearm" % side
    o, axis, down, front, L = arm_frame(body, side)
    m = MeshB()
    s = arm_socket(m, body, side, level, bone, (0.0, 0.25), (0.3, 0.6), clearance=0.0045)
    arm_straps(m, body, side, bone, (0.085, 0.13) if level == "Wrist" else (0.0, 0.035), 0.0045)
    rod = 0.02 if level == "Wrist" else 0.045
    m.tube([s, s + axis * rod], [(0.016, 0.016), (0.013, 0.013)], (down, front), 10, bone, (0, 1), (0.3, 0.7), close_start=True, close_end=True)
    e = s + axis * rod
    m.tube([e, e + axis * 0.015, e + axis * 0.05, e + axis * 0.065], [(0.014, 0.014), (0.026, 0.020), (0.026, 0.020), (0.012, 0.010)], (down, front), 12, bone, (0, 1), (0.72, 1.0), close_start=True, close_end=True)
    return m

def hook_arm(body, side, level=""):
    """Gancho: copa de cuero a medida, caña de acero y gancho partido (dos púas curvas) con goma."""
    bone = "Bip01_%s_Forearm" % side
    o, axis, down, front, L = arm_frame(body, side)
    m = MeshB()
    s = arm_socket(m, body, side, level, bone, (0.0, 0.25), (0.3, 0.6), clearance=0.0045)
    arm_straps(m, body, side, bone, (0.085, 0.13) if level == "Wrist" else (0.0, 0.035), 0.0045)
    # unidad de muñeca (acero oscuro) y caña
    m.tube([s, s + axis * 0.014], [(0.015, 0.015), (0.012, 0.012)], (down, front), 12, bone, (0, 1), (0.6, 0.84), close_start=True, close_end=True)
    sh = s + axis * 0.014
    m.tube([sh, sh + axis * 0.022], [(0.0065, 0.0065), (0.0065, 0.0065)], (down, front), 10, bone, (0, 1), (0.3, 0.6), close_start=True, close_end=True)
    base = sh + axis * 0.022
    # banda de goma en la base de las púas
    m.tube([base - axis * 0.004, base + axis * 0.004], [(0.0095, 0.0095), (0.0095, 0.0095)], (down, front), 10, bone, (0, 1), (0.86, 0.94), close_start=True, close_end=True)
    # dos púas: arco de radio R en el plano (axis, front) que se curva hacia delante (front)
    R = 0.024
    for off in (-0.0055, 0.0055):
        c = base + front * R + down * off
        pts, rr = [], []
        n = 9
        for k in range(n):
            th = math.radians(165.0) * k / (n - 1)
            pts.append(c + axis * (R * math.sin(th)) - front * (R * math.cos(th)))
            rr.append((0.0045 - 0.002 * k / (n - 1), 0.0045 - 0.002 * k / (n - 1)))
        path_tube(m, pts, rr, down, 8, bone, (0.94, 1.0))
    return m

def mech_hand(m, s, axis, down, front, bone, uv, medical):
    """Mano protésica estilizada: palma elíptica, cuatro dedos con ligera curva y pulgar."""
    pw = 0.0235 if medical else 0.022          # media anchura (front/back)
    pt = 0.010 if medical else 0.0085          # medio grosor (palma)
    m.tube([s, s + axis * 0.012, s + axis * 0.04, s + axis * 0.046], [(pt * 0.8, pw * 0.75), (pt, pw), (pt, pw), (pt * 0.9, pw * 0.95)], (down, front), 14, bone, (0, 1), uv, close_start=True, close_end=True)
    e = s + axis * 0.046
    fr = 0.0052 if medical else 0.0045
    for k, off in enumerate((-0.0165, -0.0055, 0.0055, 0.0165)):
        ln = 0.034 if k in (1, 2) else 0.028
        p0 = e + front * off
        pts = [p0, p0 + axis * (ln * 0.5), p0 + axis * (ln * 0.85) + down * 0.004, p0 + axis * ln + down * 0.009]
        rr = [(fr, fr), (fr, fr), (fr * 0.9, fr * 0.9), (fr * 0.75, fr * 0.75)]
        m.tube(pts, rr, (down, front), 8, bone, (0, 1), uv, close_start=True, close_end=True)
    # pulgar: sale del lado delantero de la palma, hacia delante y adelante
    t0 = s + axis * 0.012 + front * pw * 0.9 + down * (pt * 0.3)
    pts = [t0, t0 + front * 0.012 + axis * 0.008, t0 + front * 0.02 + axis * 0.022, t0 + front * 0.022 + axis * 0.036]
    path_tube(m, pts, [(fr * 1.15, fr * 1.15), (fr * 1.1, fr * 1.1), (fr, fr), (fr * 0.8, fr * 0.8)], down, 8, bone, uv)

def mech_arm(body, side, medical=False, level=""):
    """Brazo mecánico (chapa) o médico (carbono): encaje a medida, caña con forma de antebrazo y mano."""
    bone, hand = "Bip01_%s_Forearm" % side, "Bip01_%s_Hand" % side
    o, axis, down, front, L = arm_frame(body, side)
    m = MeshB()
    s = arm_socket(m, body, side, level, bone, (0.0, 0.2), (0.2, 0.8), clearance=0.0048 if medical else 0.0045)
    if not medical:
        # barras laterales en la caña (nivel antebrazo) o en el manguito (muñeca)
        bones = ARM_BONES[side]
        ts = [0.08, 0.10, 0.12, 0.14] if level == "Wrist" else [0.03, 0.06, 0.09, 0.12]
        for sgn in (-1, 1):
            path = []
            for t in ts:
                ring = np.array(axis_ring(body, bones, side, o, axis, down, front, t, 0.0045 if level == "Wrist" else -0.002))
                c = ring.mean(0); d = (ring - c) @ front
                edge = c + front * (d.max() if sgn > 0 else d.min())
                path.append(edge + front * sgn * 0.004)
            m.tube(path, [(0.0045, 0.0045)] * len(path), (down, axis), 8, bone, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
    # muñeca y mano (hueso de la mano: acompaña la animación de agarre)
    m.tube([s, s + axis * 0.01], [(0.011, 0.016), (0.010, 0.015)], (down, front), 12, hand, (0, 1), (0.8, 0.86), close_start=True, close_end=True)
    mech_hand(m, s + axis * 0.01, axis, down, front, hand, (0.86, 1.0), medical)
    return m

'''
s = s[:a] + NEW.lstrip("\n") + s[b:]

# ------------------------------------------------------------------ texturas: gancho + brazos
old_tex = "def tex_tourniquet_leg(path):"
new_tex = '''def tex_hook(path, seed=9):
    """v 0..0.25 cuero, 0.26..0.29 correa, 0.3..0.6 acero, 0.6..0.84 acero oscuro, 0.86..0.94 goma, 0.94..1 acero pulido."""
    img = noise_img((128, 128), (168, 170, 176), 6, seed)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 128, 32), fill=(78, 50, 32, 255))
    for i in range(0, 128, 9): d.line((i, 0, i + 4, 32), fill=(60, 38, 24, 255))
    d.rectangle((0, 33, 128, 37), fill=(45, 30, 20, 255))
    for i in range(38, 77, 5): d.line((0, i, 128, i), fill=(150, 152, 158, 255))
    d.rectangle((0, 77, 128, 108), fill=(70, 72, 78, 255))
    for i in range(0, 128, 6): d.line((i, 77, i, 108), fill=(58, 60, 66, 255))
    d.rectangle((0, 110, 128, 120), fill=(30, 30, 32, 255))
    d.rectangle((0, 121, 128, 128), fill=(205, 207, 212, 255))
    img.save(path)

def tex_tourniquet_leg(path):'''
assert old_tex in s; s = s.replace(old_tex, new_tex, 1)

old_bt = '''    tex_medical_arm(os.path.join(TOC_UP, "textures", "Prosthesis", "normalArm.png"), out("textures", "Prosthesis", "medicalArm.png"))'''
new_bt = '''    tex_hook(out("textures", "Prosthesis", "hookArm.png"))
    tex_metal(out("textures", "Prosthesis", "normalArm.png"), 4, False)
    tex_metal(out("textures", "Prosthesis", "medicalArm.png"), 5, True)'''
assert old_bt in s; s = s.replace(old_bt, new_bt)

# ------------------------------------------------------------------ build_models: variantes y suelo
old_loop = '''        for side in ("L", "R"):
            report["pegLeg_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Prosthesis", "pegLeg_%s_%s.X" % (side, sx)), "pegLeg_%s_%s" % (side, sx), "Prosthesis/pegLeg", sex, body, peg_leg(body, side))
            report["mechLeg_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Prosthesis", "mechLeg_%s_%s.X" % (side, sx)), "mechLeg_%s_%s" % (side, sx), "Prosthesis/mechLeg", sex, body, mech_leg(body, side))
            report["medicalLeg_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Prosthesis", "medicalLeg_%s_%s.X" % (side, sx)), "medicalLeg_%s_%s" % (side, sx), "Prosthesis/medicalLeg", sex, body, mech_leg(body, side, medical=True))
            report["pegArm_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Prosthesis", "pegArm_%s_%s.X" % (side, sx)), "pegArm_%s_%s" % (side, sx), "Prosthesis/pegArm", sex, body, peg_arm(body, side))
            report["tourniquetLeg_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Surgery", "TourniquetLeg_%s_%s.X" % (side, sx)), "TourniquetLeg_%s_%s" % (side, sx), "Surgery/tourniquetLeg", sex, body, leg_tourniquet(body, side))'''
new_loop = '''        for side in ("L", "R"):
            for lvl in LEG_LEVELS:
                for nm, fn in PROST_LEG_BUILDERS.items():
                    full = "%s%s_%s_%s" % (nm, lvl, side, sx)
                    report[full] = write_rigid(out("models_X", "Prosthesis", full + ".X"), full, "Prosthesis/" + nm, sex, body, fn(body, side, lvl))
            for lvl in ARM_LEVELS:
                for nm, fn in PROST_ARM_BUILDERS.items():
                    full = "%s%s_%s_%s" % (nm, lvl, side, sx)
                    report[full] = write_rigid(out("models_X", "Prosthesis", full + ".X"), full, "Prosthesis/" + nm, sex, body, fn(body, side, lvl))
            report["tourniquetLeg_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Surgery", "TourniquetLeg_%s_%s.X" % (side, sx)), "TourniquetLeg_%s_%s" % (side, sx), "Surgery/tourniquetLeg", sex, body, leg_tourniquet(body, side))'''
assert old_loop in s; s = s.replace(old_loop, new_loop)

old_ground = '''    for nm, mesh, tex in (("pegLeg_Ground", peg_leg(body, "L"), "Prosthesis/pegLeg"), ("mechLeg_Ground", mech_leg(body, "L"), "Prosthesis/mechLeg"),
                          ("medicalLeg_Ground", mech_leg(body, "L", True), "Prosthesis/medicalLeg"), ("pegArm_Ground", peg_arm(body, "L"), "Prosthesis/pegArm"),
                          ("TourniquetLeg_Ground", leg_tourniquet(body, "L"), "Surgery/tourniquetLeg")):'''
new_ground = '''    ground = [(nm + "_Ground", fn(body, "L", ""), "Prosthesis/" + nm) for nm, fn in list(PROST_LEG_BUILDERS.items()) + list(PROST_ARM_BUILDERS.items())]
    ground.append(("TourniquetLeg_Ground", leg_tourniquet(body, "L"), "Surgery/tourniquetLeg"))
    for nm, mesh, tex in ground:'''
assert old_ground in s; s = s.replace(old_ground, new_ground)

old_bm = "def build_models():"
new_bm = '''PROST_LEG_BUILDERS = {"pegLeg": lambda b, sd, lv: peg_leg(b, sd, lv), "mechLeg": lambda b, sd, lv: mech_leg(b, sd, False, lv), "medicalLeg": lambda b, sd, lv: mech_leg(b, sd, True, lv)}
PROST_ARM_BUILDERS = {"pegArm": lambda b, sd, lv: peg_arm(b, sd, lv), "hookArm": lambda b, sd, lv: hook_arm(b, sd, lv), "normalArm": lambda b, sd, lv: mech_arm(b, sd, False, lv), "medicalArm": lambda b, sd, lv: mech_arm(b, sd, True, lv)}

def build_models():'''
assert old_bm in s; s = s.replace(old_bm, new_bm, 1)

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("levels applied")
