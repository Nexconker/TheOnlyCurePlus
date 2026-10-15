"""Remodelado de las prótesis en Blender a partir de los datos de ajuste de Python (out/fit.json).

Uso (sin interfaz):
  blender -b -P blender_build.py -- out/fit.json out/blender [filtro] [--blend out/prosthesis.blend]

Para cada modelo (tier x nivel x lado x sexo) construye las piezas con primitivas de Blender
(lofts con subdivisión, curvas con bisel, cajas biseladas, esferas), cada pieza etiquetada con su
hueso y su franja de textura, y exporta un JSON {verts, normals, uvs, faces, weights} en unidades
del juego. blender_to_x.py lo convierte en .X. Las secciones de encaje son las del cuerpo vanilla
(fit.json) más holgura: el ajuste viene de Python, el acabado de Blender.

Convenciones: coordenadas del juego (Y arriba, frente -Z) en todo el script; sólo al crear datos
de Blender se convierten (bl = (x, -z, y) * S) y al exportar se deshace.
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector

S = 10.0
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FIT = argv[0] if len(argv) > 0 else "out/fit.json"
OUTDIR = argv[1] if len(argv) > 1 else "out/blender"
FILTER = None
BLEND = None
for i, a in enumerate(argv[2:]):
    if a == "--blend": BLEND = argv[2:][i + 1]
    elif not a.startswith("--") and (i == 0 or argv[2:][i - 1] != "--blend"): FILTER = a
os.makedirs(OUTDIR, exist_ok=True)
fit = json.load(open(FIT, encoding="utf-8"))

def bl(p): return (p[0] * S, -p[2] * S, p[1] * S)
def pz(p): return (p[0] / S, p[2] / S, -p[1] / S)
def v3(p): return Vector((p[0], p[1], p[2]))
def norm(v): return v / (v.length or 1.0)

# ------------------------------------------------------------------ bandas UV por textura
BANDS = {
    "peg":  {"socket": (0.0, 0.25), "strap": (0.26, 0.29), "wood": (0.3, 0.9), "rubber": (0.92, 1.0)},
    "metal": {"socket": (0.0, 0.2), "shell": (0.2, 0.86), "dark": (0.86, 1.0)},
    "hook": {"socket": (0.0, 0.25), "strap": (0.26, 0.29), "steel": (0.3, 0.6), "dark": (0.6, 0.84), "rubber": (0.86, 0.94), "polished": (0.94, 1.0)},
}

# ------------------------------------------------------------------ escena
scene = bpy.context.scene
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
ROOT = bpy.data.collections.new("TOCPlus")
scene.collection.children.link(ROOT)

class Builder:
    """Acumula las piezas de un modelo."""
    def __init__(self, name, tex):
        self.name, self.tex, self.parts = name, tex, []
        self.coll = bpy.data.collections.new(name); ROOT.children.link(self.coll)
    def band(self, key): return BANDS[self.tex][key]
    def _obj(self, name, data, bone, band, axis):
        ob = bpy.data.objects.new(self.name + "." + name, data)
        self.coll.objects.link(ob)
        ob["pz_bone"] = bone; ob["pz_band"] = list(band); ob["pz_axis"] = [float(x) for p in axis for x in p]
        self.parts.append(ob)
        return ob
    def mesh(self, name, verts, faces, bone, band, axis, subsurf=0, bevel=None, smooth=True):
        me = bpy.data.meshes.new(name)
        me.from_pydata([bl(v) for v in verts], [], faces); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = smooth
        ob = self._obj(name, me, bone, band, axis)
        if bevel:
            m = ob.modifiers.new("bev", "BEVEL"); m.width = bevel * S; m.segments = 3; m.limit_method = "ANGLE"; m.angle_limit = math.radians(40)
        if subsurf:
            m = ob.modifiers.new("sub", "SUBSURF"); m.levels = subsurf; m.render_levels = subsurf
        return ob
    # ---- primitivas (coordenadas del juego)
    def loft(self, name, rings, bone, band, subsurf=1, caps=(True, True), bevel=None, smooth=True):
        verts, faces = [], []
        if subsurf and len(rings[0]) >= 24:
            step = 2 if subsurf == 1 else 4
            rings = [r[::step] for r in rings]
            # polígono circunscrito + margen: la superficie límite de la subdivisión queda FUERA del anillo original
            k = 1.0 / math.cos(math.pi / len(rings[0])); pad = 0.0015
            out = []
            for r in rings:
                c = sum((Vector(p) for p in r), Vector()) / len(r); rr = []
                for p in r:
                    d = Vector(p) - c; l = d.length or 1e-6
                    rr.append(tuple(c + d * (k + pad / l)))
                out.append(rr)
            rings = out
        if subsurf and len(rings) >= 2:
            # anillos extremos duplicados muy cerca: la subdivisión no redondea (ni encoge) las tapas
            def near(a, b, f):
                return [tuple(Vector(p) + (Vector(q) - Vector(p)) * f) for p, q in zip(a, b)]
            rings = [rings[0], near(rings[0], rings[1], 0.04)] + list(rings[1:-1]) + [near(rings[-1], rings[-2], 0.04), rings[-1]]
        n = len(rings[0])
        for r in rings: verts += [tuple(p) for p in r]
        for k in range(len(rings) - 1):
            a, b = k * n, (k + 1) * n
            for s in range(n):
                s2 = (s + 1) % n
                faces.append((a + s, a + s2, b + s2, b + s))
        if caps[0]: faces.append(tuple(range(n - 1, -1, -1)))
        if caps[1]: faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
        c0 = Vector(sum((Vector(p) for p in rings[0]), Vector()) / n); c1 = Vector(sum((Vector(p) for p in rings[-1]), Vector()) / n)
        return self.mesh(name, verts, faces, bone, band, (c0, c1), subsurf=subsurf, bevel=bevel, smooth=smooth)
    def cyl(self, name, p0, p1, r0, r1, bone, band, segs=16, subsurf=0, bevel=None, ref=None):
        p0, p1 = Vector(p0), Vector(p1)
        ax = norm(p1 - p0)
        ref = Vector(ref) if ref is not None else (Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0)))
        u = norm(ref - ax * ref.dot(ax)); v = ax.cross(u)
        rings = []
        for p, r in ((p0, r0), (p1, r1)):
            rx, rz = (r if isinstance(r, (int, float)) else r[0]), (r if isinstance(r, (int, float)) else r[1])
            rings.append([tuple(p + u * (rx * math.cos(2 * math.pi * s / segs)) + v * (rz * math.sin(2 * math.pi * s / segs))) for s in range(segs)])
        return self.loft(name, rings, bone, band, subsurf=subsurf, bevel=bevel, smooth=True)
    def sphere(self, name, c, r, bone, band, segs=8):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r * S)
        bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(bl(c)))
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        c = Vector(c)
        return self._obj(name, me, bone, band, (c - Vector((0, r, 0)), c + Vector((0, r, 0))))
    def box(self, name, center, size, basis, bone, band, bevel=None, subsurf=0):
        """Caja con ejes basis=(u,v,w) y semiejes size (en esa base)."""
        c = Vector(center); u, v, w = (Vector(b) for b in basis)
        verts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    verts.append(tuple(c + u * (sx * size[0]) + v * (sy * size[1]) + w * (sz * size[2])))
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        return self.mesh(name, verts, faces, bone, band, (c - w * size[2], c + w * size[2]), subsurf=subsurf, bevel=bevel, smooth=bool(bevel or subsurf))
    def curve(self, name, pts, radii, bone, band, res=3, caps=True):
        cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
        base = max(radii)
        cu.bevel_depth = base * S; cu.bevel_resolution = min(res, 1); cu.use_fill_caps = caps; cu.resolution_u = 4
        sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = min(3, len(pts))
        for k, (p, r) in enumerate(zip(pts, radii)):
            x, y, z = bl(p); sp.points[k].co = (x, y, z, 1.0); sp.points[k].radius = r / base
        return self._obj(name, cu, bone, band, (Vector(pts[0]), Vector(pts[-1])))

# ------------------------------------------------------------------ anillos de ajuste
def offset_ring(ring, clearance, y=None):
    c = Vector(ring["c"]); out = []
    for p in ring["pts"]:
        p = Vector(p); d = p - c; l = d.length or 1e-6
        q = c + d * (1.0 + clearance / l)
        if y is not None: q.y = y
        out.append(tuple(q))
    return out

def leg_ring(legs, y, clearance):
    key = "%.3f" % (round(y / 0.005) * 0.005)
    return offset_ring(legs["rings"][key], clearance, y=y)

def arm_ring(arm, t, clearance):
    key = "%.3f" % (round(t / 0.005) * 0.005)
    ring = arm["rings"][key]
    out = offset_ring(ring, clearance)
    o, ax = Vector(arm["o"]), Vector(arm["axis"])
    # llevar al t exacto
    return [tuple(Vector(p) + ax * (t - (Vector(p) - o).dot(ax))) for p in out]

def smooth_rings(rings, passes=1):
    """Evita escalones entre anillos consecutivos (radio por sector, nunca reduce)."""
    R = [[Vector(p) for p in r] for r in rings]
    for _ in range(passes):
        for k in range(1, len(R) - 1):
            c0 = sum(R[k], Vector()) / len(R[k])
            for s in range(len(R[k])):
                d = R[k][s] - c0; l = d.length
                la = (R[k - 1][s] - (sum(R[k - 1], Vector()) / len(R[k - 1]))).length
                lb = (R[k + 1][s] - (sum(R[k + 1], Vector()) / len(R[k + 1]))).length
                target = max(l, (la + lb) / 2 * 0.97)
                if l > 1e-9: R[k][s] = c0 + d * (target / l)
    return [[tuple(p) for p in r] for r in R]

# ------------------------------------------------------------------ piezas de pierna
def leg_socket(B, legs, ys, clearance, bone, band, rim=True, subsurf=1):
    rings = smooth_rings([leg_ring(legs, y, clearance) for y in ys])
    ob = B.loft("socket", rings, bone, band, subsurf=subsurf)
    if rim:
        # ribete enrollado en el borde superior
        y0 = ys[0]
        rim = smooth_rings([leg_ring(legs, y0 + 0.004, clearance + 0.004), leg_ring(legs, y0, clearance + 0.006), leg_ring(legs, y0 - 0.012, clearance + 0.005), leg_ring(legs, y0 - 0.016, clearance + 0.001)])
        B.loft("rim", rim, bone, band, subsurf=1)
    return ob

def leg_straps(B, legs, ys, clearance, bone):
    for i, y in enumerate(ys):
        rings = [leg_ring(legs, y + 0.007, clearance + 0.003), leg_ring(legs, y - 0.007, clearance + 0.003)]
        B.loft("strap%d" % i, rings, bone, B.band("strap"), subsurf=1)
        # hebilla al frente (-Z)
        r = leg_ring(legs, y, clearance + 0.003)
        front = min(r, key=lambda p: p[2])
        B.box("buckle%d" % i, (front[0], y, front[2] - 0.004), (0.009, 0.006, 0.003), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("strap") if B.tex != "metal" else B.band("dark"), bevel=0.0015)

def leg_shell(B, legs, ys, clearance, bone, band, mech_bars=False, subsurf=1):
    rings = smooth_rings([leg_ring(legs, y, clearance) for y in ys])
    ob = B.loft("shell", rings, bone, band, subsurf=subsurf)
    if mech_bars:
        for sgn, nm in ((-1, "barL"), (1, "barR")):
            pts = []
            for k, r in enumerate(rings):
                c = sum((Vector(p) for p in r), Vector()) / len(r)
                edge = max(r, key=lambda p: p[0]) if sgn > 0 else min(r, key=lambda p: p[0])
                pts.append((edge[0] + sgn * 0.003, ys[k], c.z))
            B.curve(nm, pts, [0.0062] * len(pts), bone, B.band("dark"), res=2)
            for k in (0, len(pts) // 2, len(pts) - 1):
                p = pts[k]; B.sphere("rivet%s%d" % (nm, k), (p[0] + sgn * 0.003, p[1], p[2]), 0.0032, bone, B.band("dark"), segs=8)
    return ob, rings

def leg_foot(B, legs, bone, band, medical):
    f = legs["foot"]
    cx = (f["xmin"] + f["xmax"]) / 2; hw = (f["xmax"] - f["xmin"]) / 2 + (0.004 if medical else 0.003)
    zh, zt = f["zheel"], f["ztoe"]; L = zh - zt
    rings = []
    prof = [(0.0, 0.55, 0.040), (0.08, 0.80, 0.048), (0.22, 1.0, 0.044), (0.45, 1.0, 0.034), (0.65, 0.98, 0.027), (0.85, 0.90, 0.019), (1.0, 0.62, 0.012)]
    segs = 12
    for t, wf, h in prof:
        z = zh - L * t
        rings.append([(cx + hw * wf * math.cos(2 * math.pi * s / segs), 0.004 + h / 2 + (h / 2) * math.sin(2 * math.pi * s / segs), z) for s in range(segs)])
    B.loft("foot", rings, bone, band, subsurf=1)
    # suela plana ligeramente mayor
    B.box("sole", (cx, 0.004, (zh + zt) / 2), (hw + 0.002, 0.004, L / 2 + 0.003), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, band, bevel=0.003)
    # tobillo (pilón)
    r = leg_ring(legs, 0.07, 0.0); c = sum((Vector(p) for p in r), Vector()) / len(r)
    B.cyl("pylon", (c.x, 0.074, c.z), (c.x, 0.036, c.z), (0.022, 0.026), (0.024, 0.028), bone, band, segs=16, bevel=0.002)

def peg_shaft(B, legs, cx, cz, y_top, r_top, bones):
    """Pata torneada: anillos circulares con perfil con cuentas; dos huesos si cruza la rodilla."""
    def prof(y):
        t = (y_top - y) / max(1e-6, y_top)
        r = r_top * (1 - t) + 0.016 * t
        r += 0.004 * math.sin(math.pi * t) * (1 if t < 0.5 else 0.3)
        # cuentas torneadas
        r += 0.0025 * max(0.0, math.sin(y * 2 * math.pi / 0.045)) ** 3 if y > 0.03 else 0
        return r
    segs = 16
    def seg(y0, y1, bone, uvband):
        n = max(3, int((y0 - y1) / 0.012) + 2)
        ys = [y0 + (y1 - y0) * k / (n - 1) for k in range(n)]
        rings = [[(cx + prof(y) * math.cos(2 * math.pi * s / segs), y, cz + prof(y) * math.sin(2 * math.pi * s / segs)) for s in range(segs)] for y in ys]
        B.loft("peg_%s" % bone[-5:], rings, bone, uvband, subsurf=1)
    thigh, calf = bones
    if y_top > 0.27:
        seg(y_top, 0.25, thigh, B.band("wood")); seg(0.25, 0.014, calf, B.band("wood"))
    else:
        seg(y_top, 0.014, calf, B.band("wood"))
    B.cyl("ferrule", (cx, 0.016, cz), (cx, 0.0, cz), 0.019, 0.017, calf, B.band("rubber"), segs=14, bevel=0.002)

def knee(B, legs, bone, band_dark, band_shell):
    r = leg_ring(legs, 0.27, -0.004); c = sum((Vector(p) for p in r), Vector()) / len(r)
    xmin, xmax = min(p[0] for p in r), max(p[0] for p in r)
    B.cyl("knee", (c.x, 0.28, c.z), (c.x, 0.234, c.z), (0.03, 0.035), (0.028, 0.032), bone, band_dark, segs=14, bevel=0.003)
    for sgn, nm in ((-1, "hingeL"), (1, "hingeR")):
        x0 = (xmax if sgn > 0 else xmin) + sgn * 0.001
        B.cyl(nm, (x0, 0.256, c.z), (x0 + sgn * 0.012, 0.256, c.z), 0.017, 0.017, bone, band_dark, segs=16, bevel=0.002)
        B.cyl(nm + "bolt", (x0 + sgn * 0.012, 0.256, c.z), (x0 + sgn * 0.016, 0.256, c.z), 0.006, 0.0055, bone, band_shell, segs=8)

# ------------------------------------------------------------------ piernas por tier y nivel
def build_peg_leg(B, legs, level):
    thigh, calf = legs["bones"]["thigh"], legs["bones"]["calf"]
    if level == "Ankle":
        ys = [0.19, 0.17, 0.15, 0.13, 0.11, 0.095, 0.08, 0.068]
        leg_socket(B, legs, ys, 0.0042, calf, B.band("socket"))
        leg_straps(B, legs, (0.175, 0.10), 0.0042, calf)
        r = leg_ring(legs, 0.068, 0.0042); c = sum((Vector(p) for p in r), Vector()) / len(r)
        peg_shaft(B, legs, c.x, c.z, 0.068, 0.026, (thigh, calf))
    elif level == "Thigh":
        ys = [0.47, 0.45, 0.43, 0.41, 0.39]
        leg_socket(B, legs, ys, 0.0045, thigh, B.band("socket"))
        leg_straps(B, legs, (0.455, 0.40), 0.0045, thigh)
        r = leg_ring(legs, 0.39, 0.0045); c = sum((Vector(p) for p in r), Vector()) / len(r)
        rx = (max(p[0] for p in r) - min(p[0] for p in r)) / 2 - 0.004; rz = (max(p[2] for p in r) - min(p[2] for p in r)) / 2 - 0.004
        B.cyl("cone", (c.x, 0.39, c.z), (c.x, 0.272, c.z), (rx, rz), (0.031, 0.031), thigh, B.band("wood"), segs=18)
        B.cyl("kneeknob", (c.x, 0.274, c.z), (c.x, 0.232, c.z), 0.031, 0.029, calf, B.band("wood"), segs=18, bevel=0.005)
        peg_shaft(B, legs, c.x, c.z, 0.232, 0.028, (thigh, calf))
    else:
        ys = [0.33, 0.30, 0.27, 0.24, 0.21, 0.18, 0.15, 0.12, 0.095, 0.075, 0.062]
        leg_socket(B, legs, ys, 0.0042, calf, B.band("socket"))
        leg_straps(B, legs, (0.315, 0.20, 0.10), 0.0042, calf)
        r = leg_ring(legs, 0.062, 0.0042); c = sum((Vector(p) for p in r), Vector()) / len(r)
        peg_shaft(B, legs, c.x, c.z, 0.062, 0.028, (thigh, calf))

def build_mech_leg(B, legs, level, medical):
    thigh, calf, foot = legs["bones"]["thigh"], legs["bones"]["calf"], legs["bones"]["foot"]
    sub = 1
    shell_cl = 0.0036 if medical else 0.0032
    if level == "Ankle":
        leg_socket(B, legs, [0.19, 0.165, 0.14], 0.0048, calf, B.band("socket"), subsurf=sub)
        leg_shell(B, legs, [0.14, 0.115, 0.09, 0.07], shell_cl, calf, B.band("shell"), mech_bars=not medical, subsurf=sub)
    elif level == "Thigh":
        leg_socket(B, legs, [0.47, 0.45, 0.43, 0.41, 0.39], 0.0048, thigh, B.band("socket"), subsurf=sub)
        leg_shell(B, legs, [0.39, 0.36, 0.33, 0.30, 0.275], -0.003 if medical else -0.004, thigh, B.band("shell"), mech_bars=not medical, subsurf=sub)
        knee(B, legs, calf, B.band("dark"), B.band("shell"))
        leg_shell(B, legs, [0.234, 0.21, 0.185, 0.16, 0.135, 0.105, 0.085, 0.07], shell_cl, calf, B.band("shell"), mech_bars=not medical, subsurf=sub)
    else:
        leg_socket(B, legs, [0.33, 0.305, 0.28, 0.255], 0.0048, calf, B.band("socket"), subsurf=sub)
        leg_shell(B, legs, [0.255, 0.225, 0.195, 0.165, 0.135, 0.105, 0.085, 0.07], shell_cl, calf, B.band("shell"), mech_bars=not medical, subsurf=sub)
    leg_foot(B, legs, foot, B.band("dark"), medical)

# ------------------------------------------------------------------ brazos
def arm_frame(arm):
    return Vector(arm["o"]), Vector(arm["axis"]), Vector(arm["down"]), Vector(arm["front"])

def arm_socket(B, arm, level, bone, band_socket, band_shell, clearance=0.0045, subsurf=1):
    o, ax, dn, fr = arm_frame(arm)
    if level == "Wrist":
        ts = [0.07, 0.085, 0.10, 0.115, 0.13, 0.142]
        B.loft("cuff", smooth_rings([arm_ring(arm, t, clearance) for t in ts]), bone, band_socket, subsurf=subsurf)
        rim = smooth_rings([arm_ring(arm, 0.066, clearance + 0.004), arm_ring(arm, 0.07, clearance + 0.006), arm_ring(arm, 0.082, clearance + 0.005), arm_ring(arm, 0.086, clearance + 0.001)])
        B.loft("rim", rim, bone, band_socket, subsurf=1)
        B.loft("collar", [arm_ring(arm, 0.142, clearance - 0.004), arm_ring(arm, 0.154, clearance - 0.004)], bone, band_shell, subsurf=1)
        return o + ax * 0.154
    ts = [-0.015, 0.0, 0.015, 0.03, 0.045]
    B.loft("socket", smooth_rings([arm_ring(arm, t, clearance) for t in ts]), bone, band_socket, subsurf=subsurf)
    rim = smooth_rings([arm_ring(arm, -0.019, clearance + 0.004), arm_ring(arm, -0.015, clearance + 0.006), arm_ring(arm, -0.003, clearance + 0.005), arm_ring(arm, 0.001, clearance + 0.001)])
    B.loft("rim", rim, bone, band_socket, subsurf=1)
    ts = [0.045, 0.065, 0.085, 0.105, 0.12]
    B.loft("shell", smooth_rings([arm_ring(arm, t, -0.002) for t in ts]), bone, band_shell, subsurf=subsurf)
    return o + ax * 0.12

def arm_straps(B, arm, ts, clearance, bone):
    o, ax, dn, fr = arm_frame(arm)
    for i, t in enumerate(ts):
        B.loft("strap%d" % i, [arm_ring(arm, t - 0.006, clearance + 0.003), arm_ring(arm, t + 0.006, clearance + 0.003)], bone, B.band("strap"), subsurf=1)
        r = arm_ring(arm, t, clearance + 0.003)
        top = max(r, key=lambda p: -(Vector(p) - o).dot(dn))      # lado superior (-down)
        B.box("buckle%d" % i, Vector(top) - dn * 0.004, (0.003, 0.006, 0.009), (tuple(dn), tuple(fr), tuple(ax)), bone, B.band("strap"), bevel=0.0015)

def mech_bars_arm(B, arm, level, bone):
    o, ax, dn, fr = arm_frame(arm)
    ts = [0.08, 0.10, 0.12, 0.14] if level == "Wrist" else [0.03, 0.06, 0.09, 0.12]
    cl = 0.0045 if level == "Wrist" else -0.002
    for sgn, nm in ((-1, "barF"), (1, "barB")):
        pts = []
        for t in ts:
            r = [Vector(p) for p in arm_ring(arm, t, cl)]
            c = sum(r, Vector()) / len(r)
            d = [(p - c).dot(fr) for p in r]
            edge = c + fr * (max(d) if sgn > 0 else min(d))
            pts.append(tuple(edge + fr * sgn * 0.0045))
        B.curve(nm, pts, [0.0045] * len(pts), bone, B.band("dark"), res=2)
        for k in (0, len(pts) - 1):
            p = Vector(pts[k]); B.sphere("rivet%s%d" % (nm, k), tuple(p + fr * sgn * 0.003), 0.003, bone, B.band("dark"), segs=8)

def hand(B, s, arm, bone, band, medical):
    o, ax, dn, fr = arm_frame(arm)
    s = Vector(s)
    pw = 0.032 if medical else 0.031; pt = 0.013 if medical else 0.0115
    # palma: caja redondeada
    B.box("palm", s + ax * 0.028, (pt, pw, 0.028), (tuple(dn), tuple(fr), tuple(ax)), bone, band, bevel=0.006 if medical else 0.005, subsurf=1)
    e = s + ax * 0.054
    fr_r = 0.0066 if medical else 0.0062
    for k, off in enumerate((-0.0225, -0.0075, 0.0075, 0.0225)):
        ln = 0.044 if k in (1, 2) else 0.037
        p0 = e + fr * off - ax * 0.004
        pts = [tuple(p0), tuple(p0 + ax * (ln * 0.45)), tuple(p0 + ax * (ln * 0.8) + dn * 0.005), tuple(p0 + ax * ln + dn * 0.012)]
        B.curve("finger%d" % k, pts, [fr_r, fr_r, fr_r * 0.92, fr_r * 0.8], bone, band, res=3)
        B.sphere("tip%d" % k, pts[-1], fr_r * 0.8, bone, band, segs=8)
        if not medical:
            B.sphere("knuckle%d" % k, tuple(p0 + ax * (ln * 0.45)), fr_r * 1.15, bone, band, segs=8)
            B.sphere("joint%d" % k, tuple(p0 + ax * (ln * 0.8) + dn * 0.005), fr_r * 1.05, bone, band, segs=8)
    t0 = s + ax * 0.014 + fr * pw * 0.9 + dn * (pt * 0.3)
    pts = [tuple(t0), tuple(t0 + fr * 0.014 + ax * 0.009), tuple(t0 + fr * 0.024 + ax * 0.026), tuple(t0 + fr * 0.027 + ax * 0.042)]
    B.curve("thumb", pts, [fr_r * 1.2, fr_r * 1.1, fr_r, fr_r * 0.85], bone, band, res=3)
    B.sphere("thumbtip", pts[-1], fr_r * 0.85, bone, band, segs=8)
    if not medical: B.sphere("thumbjoint", pts[2], fr_r * 1.1, bone, band, segs=8)

def build_peg_arm(B, arm, level):
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("wood"))
    arm_straps(B, arm, (0.09, 0.128) if level == "Wrist" else (0.005, 0.038), 0.0045, bone)
    rod = 0.02 if level == "Wrist" else 0.045
    B.cyl("rod", tuple(s), tuple(s + ax * rod), 0.016, 0.013, bone, B.band("wood"), segs=14, subsurf=1)
    e = s + ax * rod
    # "mano" de madera torneada
    rings = []
    for d, r in ((0.0, 0.013), (0.012, 0.024), (0.03, 0.027), (0.05, 0.024), (0.062, 0.015), (0.068, 0.009)):
        c = e + ax * d
        rings.append([tuple(c + dn * (r * math.cos(2 * math.pi * k / 16)) + fr * (r * 0.85 * math.sin(2 * math.pi * k / 16))) for k in range(16)])
    B.loft("knob", rings, bone, B.band("wood"), subsurf=1)

def build_hook_arm(B, arm, level):
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("steel"))
    arm_straps(B, arm, (0.09, 0.128) if level == "Wrist" else (0.005, 0.038), 0.0045, bone)
    B.cyl("wrist", tuple(s), tuple(s + ax * 0.016), 0.016, 0.0125, bone, B.band("dark"), segs=16, bevel=0.003)
    sh = s + ax * 0.016
    B.cyl("shaft", tuple(sh), tuple(sh + ax * 0.03), 0.0085, 0.008, bone, B.band("steel"), segs=12)
    base = sh + ax * 0.03
    B.cyl("band", tuple(base - ax * 0.005), tuple(base + ax * 0.005), 0.0125, 0.0125, bone, B.band("rubber"), segs=14, bevel=0.003)
    R = 0.031
    for i, off in enumerate((-0.0075, 0.0075)):
        c = base + fr * R + dn * off
        pts, rr = [], []
        n = 9
        for k in range(n):
            th = math.radians(165.0) * k / (n - 1)
            pts.append(tuple(c + ax * (R * math.sin(th)) - fr * (R * math.cos(th))))
            rr.append(0.0058 - 0.0028 * k / (n - 1))
        B.curve("prong%d" % i, pts, rr, bone, B.band("polished"), res=3)
        B.sphere("prongtip%d" % i, pts[-1], rr[-1], bone, B.band("polished"), segs=8)

def build_mech_arm(B, arm, level, medical):
    o, ax, dn, fr = arm_frame(arm); bone, hb = arm["bones"]["forearm"], arm["bones"]["hand"]
    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("shell"), clearance=0.0048 if medical else 0.0045, subsurf=1)
    if not medical: mech_bars_arm(B, arm, level, bone)
    # muñeca y mano RÍGIDAS (hueso del antebrazo): pesadas al hueso de la mano giraban con el agarre
    # (muleta, armas) y chocaban con la caña; una prótesis mecánica no articula
    B.cyl("wristunit", tuple(s), tuple(s + ax * 0.012), (0.012, 0.018), (0.012, 0.019), bone, B.band("dark"), segs=16, bevel=0.002, ref=tuple(dn))
    hand(B, s + ax * 0.012, arm, bone, B.band("dark"), medical)

# ------------------------------------------------------------------ exportación
def export_builder(B, path):
    dg = bpy.context.evaluated_depsgraph_get()
    V, N, UV, F, W = [], [], [], [], []
    for ob in B.parts:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        if me is None or len(me.polygons) == 0:
            ev.to_mesh_clear(); continue
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        mw = ev.matrix_world
        verts = [Vector(pz(mw @ v.co)) for v in bm.verts]
        faces = [[v.index for v in f.verts] for f in bm.faces]
        # orientación definitiva: volumen con signo de la pieza (cerrada); negativo = caras hacia dentro
        vol = 0.0
        for f in faces:
            a, b, c = verts[f[0]], verts[f[1]], verts[f[2]]
            vol += a.dot(b.cross(c)) / 6.0
        if vol < 0:
            faces = [[f[0], f[2], f[1]] for f in faces]
        if abs(vol) < 1e-9:
            print("AVISO pieza sin volumen (abierta):", ob.name)
        # normales de cara en coordenadas del juego
        fn = []
        for f in faces:
            a, b, c = verts[f[0]], verts[f[1]], verts[f[2]]
            n = (b - a).cross(c - a); fn.append(norm(n))
        adj = [[] for _ in verts]
        for i, f in enumerate(faces):
            for vi in f: adj[vi].append(i)
        # agrupar normales por vértice (aristas vivas = vértices partidos)
        cosT = math.cos(math.radians(52))
        base = len(V)
        remap = {}      # (vi, cluster) -> índice exportado
        bone = ob["pz_bone"]; v0, v1 = ob["pz_band"]; axv = list(ob["pz_axis"]); p0, p1 = Vector(axv[:3]), Vector(axv[3:])
        axis = norm(p1 - p0) if (p1 - p0).length > 1e-6 else Vector((0, 1, 0))
        ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
        u_ax = norm(ref - axis * ref.dot(axis)); w_ax = axis.cross(u_ax)
        proj = [(p - p0).dot(axis) for p in verts]
        pmin, pmax = min(proj), max(proj)
        def uv_of(p, pr):
            d = p - p0; ang = math.atan2(d.dot(w_ax), d.dot(u_ax))
            u = (ang / (2 * math.pi)) % 1.0
            vv = v0 + (v1 - v0) * ((pr - pmin) / (pmax - pmin) if pmax > pmin else 0.5)
            return (u, vv)
        for vi in range(len(verts)):
            clusters = []
            for fi in adj[vi]:
                n = fn[fi]
                for cl in clusters:
                    if cl["n"].dot(n) >= cosT * (cl["n"].length or 1):
                        cl["n"] = cl["n"] + n; cl["faces"].append(fi); break
                else:
                    clusters.append({"n": Vector(n), "faces": [fi]})
            for ci, cl in enumerate(clusters):
                idx = len(V)
                for fi in cl["faces"]: remap[(vi, fi)] = idx
                V.append([round(x, 5) for x in verts[vi]]); nn = norm(cl["n"]); N.append([round(x, 4) for x in nn])
                UV.append([round(x, 4) for x in uv_of(verts[vi], proj[vi])]); W.append(bone)
        for fi, f in enumerate(faces):
            F.append([remap[(f[0], fi)], remap[(f[1], fi)], remap[(f[2], fi)]])
        bm.free(); ev.to_mesh_clear()
    json.dump({"verts": V, "normals": N, "uvs": UV, "faces": F, "bones": W}, open(path, "w"))
    return len(V), len(F)

# ------------------------------------------------------------------ catálogo
LEG_TIERS = {"pegLeg": ("peg", lambda B, legs, lv: build_peg_leg(B, legs, lv)),
             "mechLeg": ("metal", lambda B, legs, lv: build_mech_leg(B, legs, lv, False)),
             "medicalLeg": ("metal", lambda B, legs, lv: build_mech_leg(B, legs, lv, True))}
ARM_TIERS = {"pegArm": ("peg", lambda B, arm, lv: build_peg_arm(B, arm, lv)),
             "hookArm": ("hook", lambda B, arm, lv: build_hook_arm(B, arm, lv)),
             "normalArm": ("metal", lambda B, arm, lv: build_mech_arm(B, arm, lv, False)),
             "medicalArm": ("metal", lambda B, arm, lv: build_mech_arm(B, arm, lv, True))}

LEG_UNDER = ("foot", "sole", "pylon", "ferrule", "peg_")
ARM_UNDER = ("wrist", "shaft", "band", "prong", "wristunit", "palm", "finger", "tip", "knuckle", "joint", "thumb", "rod", "knob")
report = []
col_x = 0.0
for sex, body in fit["bodies"].items():
    sx = "M" if sex == "Male" else "F"
    for side in ("L", "R"):
        jobs = []
        for tier, (tex, fn) in LEG_TIERS.items():
            for lv in fit["leg_levels"]: jobs.append((tier, lv, tex, fn, body["legs"][side]))
        for tier, (tex, fn) in ARM_TIERS.items():
            for lv in fit["arm_levels"]: jobs.append((tier, lv, tex, fn, body["arms"][side]))
        for tier, lv, tex, fn, data in jobs:
            name = "%s%s_%s_%s" % (tier, lv, side, sx)
            if FILTER and FILTER not in name: continue
            B = Builder(name, tex)
            fn(B, data, lv)
            nv, nf = export_builder(B, os.path.join(OUTDIR, name + ".json"))
            report.append((name, nv, nf))
            # variante bajo la ropa (modelo alternativo del juego): sólo lo que asoma por el bajo del
            # pantalón (pie, pilón, contera, pata) o por el puño de la manga (dispositivo terminal)
            keep = LEG_UNDER if tier in LEG_TIERS else ARM_UNDER
            full_parts = B.parts
            B.parts = [ob for ob in full_parts if any(ob.name.split(".", 1)[1].startswith(k) for k in keep)]
            uname = "%s%sUnder_%s_%s" % (tier, lv, side, sx)
            if B.parts:
                unv, unf = export_builder(B, os.path.join(OUTDIR, uname + ".json"))
                print("built", uname, unv, "verts", unf, "tris")
            B.parts = full_parts
            keep = BLEND and side == "L" and sex == "Male"
            if keep:
                # muestrario: cada modelo desplazado en X para verlos juntos
                for ob in B.parts: ob.location.x += col_x
                col_x += 2.5
            else:
                for ob in list(B.parts): bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.collections.remove(B.coll)
            print("built", name, nv, "verts", nf, "tris")
if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(BLEND))
    print("blend", BLEND)
print("DONE", len(report), "models")
