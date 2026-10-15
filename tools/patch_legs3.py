"""Sección exacta de la pierna: intersección de los triángulos del cuerpo con el plano y (no franjas
de vértices), así la prótesis envuelve la superficie real con la holgura pedida."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "build_assets.py")
s = open(p, encoding="utf-8").read()
a = s.index("def _leg_points(body, side):")
b = s.index("def leg_profile(body, side, y, clearance=0.003, window=0.028):")

NEW = r'''
_leg_cache = {}
def _leg_mesh(body, side):
    """Vértices y caras visibles de la pierna (muslo, pantorrilla, pie) de un lado."""
    key = (id(body), side)
    if key not in _leg_cache:
        V = body["verts"]; W = body["weights"]
        bones = ("Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side)
        faces = []
        for f in body["faces"]:
            if face_is_hidden(body, f): continue
            if any(any(bn in W[vi] for bn in bones) for vi in f):
                # sólo caras del lado correcto (la cadera comparte vértices)
                if all((V[vi][0] > 0) == (side == "L") for vi in f):
                    faces.append(f)
        _leg_cache[key] = (V, faces)
    return _leg_cache[key]

def _leg_points(body, side):
    V, faces = _leg_mesh(body, side)
    idx = sorted({vi for f in faces for vi in f})
    return np.array([V[i] for i in idx])

def plane_section(body, side, y):
    """Puntos de la intersección de la superficie de la pierna con el plano y."""
    V, faces = _leg_mesh(body, side)
    pts = []
    for f in faces:
        for k in range(3):
            a_, b_ = V[f[k]], V[f[(k + 1) % 3]]
            ya, yb = a_[1], b_[1]
            if (ya - y) * (yb - y) <= 0 and ya != yb:
                t = (y - ya) / (yb - ya)
                pts.append(a_ + (b_ - a_) * t)
    return np.array(pts) if pts else np.zeros((0, 3))

def leg_section(pts_unused, y, clearance=0.003, segs=18, window=0.03, smooth=1, body=None, side=None):
    """Anillo (segs puntos) que envuelve la sección real de la pierna a la altura y + holgura."""
    sl = plane_section(body, side, y)
    if len(sl) < 4:
        P = _leg_points(body, side)
        sl = P[np.argsort(np.abs(P[:, 1] - y))[:10]]
    cx, cz = (sl[:, 0].min() + sl[:, 0].max()) / 2, (sl[:, 2].min() + sl[:, 2].max()) / 2
    ang = np.arctan2(sl[:, 2] - cz, sl[:, 0] - cx)
    dist = np.hypot(sl[:, 0] - cx, sl[:, 2] - cz)
    r = np.zeros(segs)
    for k in range(segs):
        t = -math.pi + 2 * math.pi * k / segs
        d = np.abs((ang - t + math.pi) % (2 * math.pi) - math.pi)
        sector = d <= math.pi / segs + 0.02
        if sector.any():
            r[k] = dist[sector].max()
        else:
            # sin puntos en el sector: interpolar entre los vecinos angulares más cercanos
            order = np.argsort(d)[:2]
            r[k] = dist[order].max()
    for _ in range(smooth):
        r = np.maximum(r, (np.roll(r, 1) + np.roll(r, -1)) / 2 * 0.98)
    r = r + clearance
    ring = [np.array([cx + r[k] * math.cos(-math.pi + 2 * math.pi * k / segs), y, cz + r[k] * math.sin(-math.pi + 2 * math.pi * k / segs)]) for k in range(segs)]
    return ring

'''
s = s[:a] + NEW.lstrip("\n") + s[b:]
# adaptar las llamadas: leg_section(pts, y, ...) -> pasar body y side
s = s.replace("    ring = leg_section(_leg_points(body, side), y, clearance)\n", "    ring = leg_section(None, y, clearance, body=body, side=side)\n")
s = s.replace("    pts = _leg_points(body, side)\n    rings = [leg_section(pts, y, clearance, segs) for y in ys]", "    rings = [leg_section(None, y, clearance, segs, body=body, side=side) for y in ys]")
s = s.replace("        r1 = leg_section(pts, y + 0.006, 0.0032 + 0.0025); r2 = leg_section(pts, y - 0.006, 0.0032 + 0.0025)",
              "        r1 = leg_section(None, y + 0.006, 0.0032 + 0.0025, body=body, side=side); r2 = leg_section(None, y - 0.006, 0.0032 + 0.0025, body=body, side=side)")
s = s.replace("    r_top = leg_section(pts, 0.07, 0.0); c = np.array(r_top).mean(0)", "    r_top = leg_section(None, 0.07, 0.0, body=body, side=side); c = np.array(r_top).mean(0)")
# el suavizado a lo largo de la pierna no debe reducir radios (max en vez de media)
s = s.replace("            R[k] = (R[k - 1] + 2 * R[k] + R[k + 1]) / 4\n            R[k][:, 1] = ys[k]",
              "            R[k] = np.maximum(R[k], (R[k - 1] + R[k + 1]) / 2 * 0.97)\n            R[k][:, 1] = ys[k]")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("legs3 applied")
