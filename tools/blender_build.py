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
MODULAR = "--modular" in argv          # 3.3: sólo bases y cabezales (DISENO_3.3_MODULAR.md)
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
    # brazo motosierra: atlas 128x512, v 0..0.75 = chainsaw.png x3 (malla vanilla), v 0.75..1 = estas bandas
    # 3.3 gama cyber: carbono, placa principal, placa secundaria, juntas oscuras, acento y cables
    "cyber": {"socket": (0.0, 0.14), "plate": (0.14, 0.46), "plate2": (0.46, 0.60), "dark": (0.60, 0.80), "accent": (0.80, 0.90), "cable": (0.90, 1.0),
              "shell": (0.14, 0.46), "strap": (0.60, 0.80)},
    "saw": {"socket": (0.75, 0.80), "strap": (0.805, 0.815), "steel": (0.82, 0.89), "dark": (0.89, 0.95), "rubber": (0.95, 0.97), "polished": (0.97, 1.0)},
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
        self.raw = []       # mallas ya terminadas (coordenadas del juego) que se exportan tal cual: la motosierra vanilla
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
    def loft(self, name, rings, bone, band, subsurf=1, caps=(True, True), bevel=None, smooth=True, tight=False):
        verts, faces = [], []
        if subsurf and len(rings[0]) >= 24:
            step = 2 if subsurf == 1 else 4
            rings = [r[::step] for r in rings]
            # polígono circunscrito + margen: la superficie límite de la subdivisión queda FUERA del anillo original.
            # tight: sin margen (encajes de brazo con holgura propia: la subdivisión encoge menos que esa holgura)
            k = 1.0 if tight else 1.0 / math.cos(math.pi / len(rings[0])); pad = 0.0 if tight else 0.0015
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

# Ajuste a TombBody (export_fit --tomb): cada anillo trae "dc" = centro de la sección de Tomb - centro vanilla. Lo que va
# SOBRE el muñón sigue la forma de Tomb; lo que SUSTITUYE al miembro (carcasas del antebrazo y del brazo, bisagra) vuelve
# al centro vanilla con el grosor de Tomb, para que bisagra (en la articulación) y mano (en el eje) casen como en vanilla
# (2026-10-15, "la articulación del codo trae mínimos desfases y la mano también"). Sin "dc" (vanilla) no cambia nada.
ARM_LEVEL = ""

def _recenter_fore(t):
    if ARM_LEVEL == "Upper": return 1.0                       # todo el antebrazo es protésico
    if ARM_LEVEL == "": return min(1.0, max(0.0, (t - 0.045) / 0.03))   # encaje hasta t = 0.045, luego carcasa
    return 0.0                                                # muñeca: el brazal abraza el antebrazo real

def _shifted(out, ring, w):
    if not w or "dc" not in ring: return out
    dc = Vector(ring["dc"]) * w
    return [tuple(Vector(q) - dc) for q in out]

def arm_ring(arm, t, clearance):
    key = "%.3f" % (round(t / 0.005) * 0.005)
    ring = arm["rings"][key]
    out = _shifted(offset_ring(ring, clearance), ring, _recenter_fore(t))
    o, ax = Vector(arm["o"]), Vector(arm["axis"])
    # llevar al t exacto
    return [tuple(Vector(p) + ax * (t - (Vector(p) - o).dot(ax))) for p in out]

def upper_ring(arm, t, clearance):
    """Anillo del brazo superior a distancia t del hombro (3.1.0, prótesis por encima del codo)."""
    up = arm["upper"]
    t = max(0.0, min(t, up["len"]))
    key = "%.3f" % (round(t / 0.005) * 0.005)
    if key not in up["rings"]: key = max(up["rings"], key=lambda k: -abs(float(k) - t))
    w = min(1.0, max(0.0, (t - (up["t_cut"] + 0.012)) / 0.03))     # encaje del muñón -> carcasa hasta el codo
    out = _shifted(offset_ring(up["rings"][key], clearance), up["rings"][key], w)
    o, ax = Vector(up["o"]), Vector(up["axis"])
    return [tuple(Vector(q) + ax * (t - (Vector(q) - o).dot(ax))) for q in out]

UPPER_STYLE = {   # banda por textura: encaje, carcasa, correa (o None), pasador, tapas
    "peg": ("socket", "wood", "strap", "rubber", "rubber"),
    "hook": ("socket", "steel", "strap", "dark", "polished"),
    "metal": ("socket", "shell", None, "dark", "dark"),
    "saw": ("socket", "steel", "strap", "dark", "polished"),
    "cyber": ("socket", "plate", None, "dark", "accent"),
}

def build_upper_section(B, arm):
    """Encaje sobre el muñón del brazo, carcasa hasta el codo con la forma del brazo y bisagra de codo. Todo en el
    hueso del brazo; el antebrazo protésico (hueso del antebrazo) gira en la bisagra con las animaciones."""
    up = arm["upper"]; bone = up["bone"]
    uo, uax, udn, ufr = Vector(up["o"]), Vector(up["axis"]), Vector(up["down"]), Vector(up["front"])
    L, tc = up["len"], up["t_cut"]
    b_sock, b_shell, b_strap, b_pin, b_cap = UPPER_STYLE[B.tex]
    cl = ARM_CL
    t0 = max(0.012, tc - 0.035)
    tsu = sorted({round(t0 + 0.0075 * i, 4) for i in range(int((tc + 0.012 - t0) / 0.0075) + 1)} | {round(tc + 0.012, 4)})
    B.loft("usocket", smooth_rings([upper_ring(arm, t, cl) for t in tsu], 2), bone, B.band(b_sock), subsurf=1, tight=True)
    B.loft("urim", smooth_rings([upper_ring(arm, t0 - 0.004, cl + 0.0015), upper_ring(arm, t0, cl + 0.003), upper_ring(arm, t0 + 0.008, cl + 0.0025),
                                upper_ring(arm, t0 + 0.012, cl + 0.0005)]), bone, B.band(b_pin), subsurf=1)
    ts = [tc + 0.012, tc + 0.03, tc + 0.05, L - 0.03, L - 0.014]
    ts = sorted({round(t, 4) for t in ts if tc + 0.01 <= t <= L - 0.01})
    B.loft("ushell", smooth_rings([upper_ring(arm, t, ARM_SHELL) for t in ts]), bone, B.band(b_shell), subsurf=1)
    if b_strap:
        for i, t in enumerate((t0 + 0.012, tc - 0.004)):
            B.loft("ustrap%d" % i, [upper_ring(arm, t - 0.005, cl + 0.0018), upper_ring(arm, t + 0.005, cl + 0.0018)], bone, B.band(b_strap), subsurf=1)
    # bisagra: el codo flexiona alrededor del eje "abajo" del marco (vertical en la pose de reposo, palmas abajo)
    elbow = Vector(arm["o"])
    ring = [Vector(q) for q in upper_ring(arm, L - 0.006, cl)]
    c = sum(ring, Vector()) / len(ring)
    half = max(abs((q - c).dot(udn)) for q in ring) + 0.0015
    B.cyl("upin", tuple(elbow - udn * half), tuple(elbow + udn * half), 0.0085, 0.0085, bone, B.band(b_pin), segs=14, bevel=0.0012, ref=tuple(uax))
    for k, sg in enumerate((-1, 1)):
        cc = elbow + udn * sg * half
        B.cyl("ucap%d" % k, tuple(cc - udn * sg * 0.002), tuple(cc + udn * sg * 0.003), 0.0135, 0.0125, bone, B.band(b_cap), segs=14, bevel=0.0012, ref=tuple(uax))
        # pletina de la bisagra hacia el brazo
        q0 = cc - uax * 0.004; q1 = cc - uax * 0.032
        B.box("uplate%d" % k, (q0 + q1) / 2, (0.0022, 0.009, (q1 - q0).length / 2), (tuple(udn), tuple(ufr), tuple(uax)), bone, B.band(b_pin), bevel=0.0008)

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
def leg_socket(B, legs, ys, clearance, bone, band, rim=True, subsurf=1, thigh=None):
    """thigh: el encaje sube por encima de la rodilla (nivel pantorrilla); esa parte sigue al muslo (knee_blend)."""
    rings = smooth_rings([leg_ring(legs, y, clearance) for y in ys])
    ob = B.loft("socket", rings, bone, band, subsurf=subsurf)
    if thigh:
        c = sum((Vector(p) for p in rings[0]), Vector()) / len(rings[0])
        knee_blend(ob, c.x, c.z, thigh, bone)
    if rim:
        # ribete enrollado en el borde superior
        y0 = ys[0]
        rim = smooth_rings([leg_ring(legs, y0 + 0.004, clearance + 0.004), leg_ring(legs, y0, clearance + 0.006), leg_ring(legs, y0 - 0.012, clearance + 0.005), leg_ring(legs, y0 - 0.016, clearance + 0.001)])
        B.loft("rim", rim, thigh or bone, band, subsurf=1)
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

def leg_foot(B, legs, bone, band, medical, pylon=True):
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
    if not pylon: return
    r = leg_ring(legs, 0.07, 0.0); c = sum((Vector(p) for p in r), Vector()) / len(r)
    B.cyl("pylon", (c.x, 0.074, c.z), (c.x, 0.036, c.z), (0.022, 0.026), (0.024, 0.028), bone, band, segs=16, bevel=0.002)

def knee(B, legs, bone, band_dark, band_shell):
    r = leg_ring(legs, 0.27, -0.004); c = sum((Vector(p) for p in r), Vector()) / len(r)
    xmin, xmax = min(p[0] for p in r), max(p[0] for p in r)
    B.cyl("knee", (c.x, 0.28, c.z), (c.x, 0.234, c.z), (0.03, 0.035), (0.028, 0.032), bone, band_dark, segs=14, bevel=0.003)
    for sgn, nm in ((-1, "hingeL"), (1, "hingeR")):
        x0 = (xmax if sgn > 0 else xmin) + sgn * 0.001
        B.cyl(nm, (x0, 0.256, c.z), (x0 + sgn * 0.012, 0.256, c.z), 0.017, 0.017, bone, band_dark, segs=16, bevel=0.002)
        B.cyl(nm + "bolt", (x0 + sgn * 0.012, 0.256, c.z), (x0 + sgn * 0.016, 0.256, c.z), 0.006, 0.0055, bone, band_shell, segs=8)

# ------------------------------------------------------------------ piernas por tier y nivel
def knee_blend(ob, cx, cz, thigh, calf, y_knee=0.256, above=0.03, below=0.015):
    """Lo que sube por encima de la rodilla sigue al muslo y pasa suave a la pantorrilla (2026-10-17, "esta flexión me
    parece algo anormal": el cubo entero en la pantorrilla sacaba el borde por detrás del muslo al doblar la rodilla)."""
    ob["pz_blend"] = [cx, y_knee, cz, 0.0, -1.0, 0.0, -above, below]; ob["pz_blend_b0"] = thigh; ob["pz_blend_b1"] = calf

def peg_bucket(B, legs, y_top, y_follow, y_bot, r_bot, cl, bone, outward, thigh=None):
    """Cubo de madera tallado (2026-10-17, referencia: pata de palo de museo): sigue la pierna arriba y se estrecha en
    cono hasta una boca redonda abajo, con borde de cuero, una ventana lateral y un anillo torneado en la boca."""
    top = [Vector(p) for p in leg_ring(legs, y_follow, cl)]
    ct = sum(top, Vector()) / len(top)
    rb = leg_ring(legs, y_bot + 0.02, 0.0); cb = sum((Vector(p) for p in rb), Vector()) / len(rb)
    n = len(top); rings = []
    ys = [y_top + (y_follow - y_top) * k / 3 for k in range(3)]
    for y in ys:
        rings.append(leg_ring(legs, y, cl))
    for k in range(1, 7):
        f = k / 6; y = y_follow + (y_bot - y_follow) * f; e = f * f * (3 - 2 * f)
        c = ct * (1 - e) + Vector((cb.x, 0, cb.z)) * e; c.y = y
        ring = []
        for p in top:
            d = p - ct; d.y = 0
            th = math.atan2(d.z, d.x)
            rnd = Vector((math.cos(th), 0, math.sin(th))) * r_bot
            q = c + d * (1 - e) + rnd * e; q.y = y
            ring.append(tuple(q))
        rings.append(ring)
    ob = B.loft("bucket", smooth_rings(rings), bone, B.band("wood"), subsurf=1)
    if thigh: knee_blend(ob, ct.x, ct.z, thigh, bone)
    # borde de cuero enrollado arriba
    rim = B.loft("rim", smooth_rings([leg_ring(legs, y_top + 0.004, cl + 0.003), leg_ring(legs, y_top, cl + 0.005),
                                leg_ring(legs, y_top - 0.010, cl + 0.004), leg_ring(legs, y_top - 0.014, cl + 0.0005)]), thigh or bone, B.band("socket"), subsurf=1)
    # ventana lateral (hueco oscuro con marco) hacia fuera, a media altura del cono
    if y_follow - y_bot > 0.05:
        yw = y_follow + (y_bot - y_follow) * 0.35
        f = 0.35; e = f * f * (3 - 2 * f)
        c = ct * (1 - e) + Vector((cb.x, 0, cb.z)) * e
        p_out = max(top, key=lambda p: (p.x - ct.x) * outward)
        rx = abs(p_out.x - ct.x) * (1 - e) + r_bot * e
        hw = (y_follow - y_bot) * 0.16
    else:                                   # cono corto (sin pie): la ventana va en el tramo que sigue la pierna
        yw = (y_top + y_follow) / 2
        rw = [Vector(p) for p in leg_ring(legs, yw, cl)]; c = sum(rw, Vector()) / len(rw)
        rx = max((p.x - c.x) * outward for p in rw)
        hw = (y_top - y_follow) * 0.14
    pw = Vector((c.x + outward * (rx + 0.0008), yw, c.z))
    B.box("window", tuple(pw), (0.0016, hw, 0.010), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("rubber"), bevel=0.0012)
    # anillo torneado en la boca del cubo
    B.cyl("collar", (cb.x, y_bot + 0.006, cb.z), (cb.x, y_bot - 0.010, cb.z), r_bot + 0.003, r_bot - 0.002, bone, B.band("wood"), segs=18, bevel=0.002)
    B.cyl("collarband", (cb.x, y_bot + 0.002, cb.z), (cb.x, y_bot - 0.004, cb.z), r_bot + 0.0035, r_bot + 0.0025, bone, B.band("strap"), segs=18)
    return cb

def peg_pole(B, cx, cz, y0, bone):
    """Pata fina y recta con un pie redondo de madera y suela de goma."""
    prof = [(y0, 0.0125)] + [p for p in ((y0 - 0.02, 0.0118), (0.06, 0.0105)) if p[0] < y0 - 0.008 and p[0] > 0.045] + [(0.036, 0.0112), (0.028, 0.0135)]
    segs = 14
    rings = [[(cx + r * math.cos(2 * math.pi * s / segs), y, cz + r * math.sin(2 * math.pi * s / segs)) for s in range(segs)] for y, r in prof]
    B.loft("peg_pole", rings, bone, B.band("wood"), subsurf=1)
    B.cyl("peg_ring", (cx, 0.042, cz), (cx, 0.034, cz), 0.0135, 0.0135, bone, B.band("strap"), segs=14)
    B.cyl("foot", (cx, 0.030, cz), (cx, 0.008, cz), 0.017, 0.024, bone, B.band("wood"), segs=18, bevel=0.003)
    B.cyl("sole", (cx, 0.009, cz), (cx, 0.0, cz), 0.0245, 0.024, bone, B.band("rubber"), segs=18, bevel=0.002)

def build_peg_leg(B, legs, level):
    """Pata de palo (2026-10-17, "cambia la pata de palo a algo más o menos así" + foto de una pata de museo): cubo de
    madera cónico con ventana lateral y borde de cuero, anillo torneado en la boca, pata fina y recta y pie redondo."""
    thigh, calf = legs["bones"]["thigh"], legs["bones"]["calf"]
    r0 = leg_ring(legs, 0.30, 0.0); c0 = sum((Vector(p) for p in r0), Vector()) / len(r0)
    outward = 1 if c0.x > 0 else -1
    if level == "Ankle":
        # el muñón de pie baja hasta y ~ 0.071: el cubo sigue la pierna hasta ahí y se cierra justo debajo
        cb = peg_bucket(B, legs, 0.20, 0.08, 0.052, 0.022, 0.0042, calf, outward)
        leg_straps(B, legs, (0.185,), 0.0042, calf)
        peg_pole(B, cb.x, cb.z, 0.047, calf)
    elif level == "Thigh":
        cb = peg_bucket(B, legs, 0.47, 0.41, 0.30, 0.030, 0.0045, thigh, outward)
        leg_straps(B, legs, (0.455,), 0.0045, thigh)
        B.cyl("kneeknob", (cb.x, 0.292, cb.z), (cb.x, 0.236, cb.z), 0.030, 0.026, calf, B.band("wood"), segs=18, bevel=0.006)
        B.cyl("kneeband", (cb.x, 0.268, cb.z), (cb.x, 0.258, cb.z), 0.0312, 0.0312, calf, B.band("strap"), segs=18)
        peg_pole(B, cb.x, cb.z, 0.238, calf)
    else:
        cb = peg_bucket(B, legs, 0.31, 0.235, 0.12, 0.024, 0.0042, calf, outward, thigh=thigh)
        leg_straps(B, legs, (0.296,), 0.0042, thigh)
        peg_pole(B, cb.x, cb.z, 0.115, calf)

# ---- 3.3: piernas rehechas (2026-10-17, "haz la parte opcional"). La piel por debajo del muñón está oculta, así que lo
# que sustituye a la pierna ya no copia su forma: armazón hueco (mecánica), pilón de titanio (médica) o blindaje (cyber).
KNEE_Y, ANKLE_Y = 0.27, 0.066          # pivotes de Bip01_X_Calf y Bip01_X_Foot en bind

def lc(legs, y):
    r = leg_ring(legs, y, 0.0); c = sum((Vector(p) for p in r), Vector()) / len(r); c.y = y
    return c

def lell(legs, y, cl):
    """Elipse lisa que envuelve la sección de la pierna en y (como ring_radius_fn en el brazo)."""
    r = [Vector(p) for p in leg_ring(legs, y, 0.0)]; c = sum(r, Vector()) / len(r); c.y = y
    return c, max(abs(p.x - c.x) for p in r) * 1.03 + cl, max(abs(p.z - c.z) for p in r) * 1.03 + cl

def ell_ring(c, ax_, az_, n=20):
    return [(c.x + ax_ * math.cos(2 * math.pi * k / n), c.y, c.z + az_ * math.sin(2 * math.pi * k / n)) for k in range(n)]

def leg_panel(B, name, secs, th0, th1, thick, band, bone, facets=4):
    """Placa curva entre los ángulos th0..th1 (x = cos, z = sin; delante = -pi/2) sobre las secciones [(c, ax, az)]."""
    verts, faces, nA = [], [], facets + 1
    for c, ax_, az_ in secs:
        for k in range(nA):
            th = th0 + (th1 - th0) * k / facets
            d = Vector((math.cos(th), 0, math.sin(th)))
            o = Vector((c.x + ax_ * d.x, c.y, c.z + az_ * d.z))
            n = Vector((d.x / ax_, 0, d.z / az_)).normalized()
            verts.append(tuple(o)); verts.append(tuple(o - n * thick))
    rl = nA * 2
    for i in range(len(secs) - 1):
        for k in range(facets):
            o0 = i * rl + k * 2; o1 = o0 + 2; n0 = o0 + rl; n1 = o1 + rl
            faces += [(o0, o1, n1, n0), (o0 + 1, n0 + 1, n1 + 1, o1 + 1)]
        a_ = i * rl; b_ = a_ + rl; e = a_ + facets * 2; f_ = e + rl
        faces += [(a_, b_, b_ + 1, a_ + 1), (e, e + 1, f_ + 1, f_)]
    last = (len(secs) - 1) * rl
    for k in range(facets):
        p_ = k * 2; faces.append((p_, p_ + 1, p_ + 3, p_ + 2)); q_ = last + k * 2; faces.append((q_, q_ + 2, q_ + 3, q_ + 1))
    return B.mesh(name, verts, faces, bone, band, (Vector(verts[0]), Vector(verts[-1])), bevel=0.0006, smooth=False)

def bar_between(B, name, p, q, w, t, bone, band, side_ref=Vector((1, 0, 0))):
    p, q = Vector(p), Vector(q); a = norm(q - p)
    u = norm(side_ref - a * side_ref.dot(a)); v = a.cross(u)
    return B.box(name, tuple((p + q) / 2), (t, w, (q - p).length / 2), (tuple(u), tuple(v), tuple(a)), bone, band, bevel=0.0008)

def spring(B, name, p, q, r, turns, wire, bone, band):
    p, q = Vector(p), Vector(q); a = norm(q - p); u = norm(Vector((1, 0, 0)) - a * a.x); v = a.cross(u)
    n = int(turns * 10); pts = []
    for k in range(n + 1):
        f = k / n; th = 2 * math.pi * turns * f
        pts.append(tuple(p + (q - p) * f + (u * math.cos(th) + v * math.sin(th)) * r))
    return B.curve(name, pts, [wire] * len(pts), bone, band, res=1)

def foot_dims(legs):
    f = legs["foot"]
    return (f["xmin"] + f["xmax"]) / 2, (f["xmax"] - f["xmin"]) / 2, f["zheel"], f["ztoe"]

def mech_foot(B, legs, bone):
    """Pie de placas: suela de goma, quilla de acero, taco de talón, puntera inclinada y horquilla de tobillo."""
    cx, hw, zh, zt = foot_dims(legs); L = zh - zt
    B.box("sole", (cx, 0.0035, (zh + zt) / 2 - 0.002), (hw * 0.92, 0.0035, L / 2), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("dark"), bevel=0.003)
    B.box("footkeel", (cx, 0.011, (zh + zt) / 2 + 0.006), (hw * 0.62, 0.003, L * 0.42), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("shell"), bevel=0.0015)
    B.box("footheel", (cx, 0.016, zh - 0.022), (hw * 0.55, 0.009, 0.018), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("dark"), bevel=0.003)
    tz = zt + 0.035; ang = math.radians(12)
    B.box("foottoe", (cx, 0.0115, tz), (hw * 0.75, 0.0035, 0.032), ((1, 0, 0), (0, math.cos(ang), -math.sin(ang)), (0, math.sin(ang), math.cos(ang))), bone, B.band("shell"), bevel=0.0015)
    a = lc(legs, ANKLE_Y)
    for sg in (-1, 1):
        x = a.x + sg * 0.019
        bar_between(B, "footfork%d" % (sg > 0), (x, ANKLE_Y, a.z), (x, 0.013, a.z + 0.006), 0.009, 0.0022, bone, B.band("shell"))
    B.cyl("pylonhinge", (a.x - 0.024, ANKLE_Y, a.z), (a.x + 0.024, ANKLE_Y, a.z), 0.0085, 0.0085, bone, B.band("dark"), segs=14, ref=(0, 1, 0))

def build_mech_leg(B, legs, level, medical):
    """Pierna mecánica (3.3, hueca) o médica (moderna): encaje sobre el muñón; debajo, la mecánica es un armazón de pilón,
    amortiguador con muelle y dos pletinas, y la médica un adaptador piramidal con pilón de titanio y pie de carbono."""
    if medical: return build_med_leg(B, legs, level)
    thigh, calf, foot = legs["bones"]["thigh"], legs["bones"]["calf"], legs["bones"]["foot"]
    def shin_frame(y_top):
        top, bot = lc(legs, y_top), lc(legs, 0.088)
        B.loft("clamp", [ell_ring(*lell(legs, y_top + 0.004, 0.004), n=20), ell_ring(*lell(legs, y_top - 0.004, 0.003), n=20)], calf, B.band("dark"), subsurf=1)
        B.cyl("pylon", tuple(top), tuple(bot), 0.0105, 0.0105, calf, B.band("shell"), segs=14)
        d0 = top + (bot - top) * 0.12; d1 = top + (bot - top) * 0.45
        B.cyl("damper", tuple(d0), tuple(d1), 0.0165, 0.0165, calf, B.band("dark"), segs=16, bevel=0.0015)
        spring(B, "spring", d1, top + (bot - top) * 0.78, 0.0175, 6, 0.0019, calf, B.band("shell"))
        B.cyl("pylonclamp", tuple(top + (bot - top) * 0.8), tuple(top + (bot - top) * 0.87), 0.0148, 0.0148, calf, B.band("dark"), segs=14, bevel=0.001)
        c, ax_, az_ = lell(legs, y_top, 0.0)
        for sg in (-1, 1):
            p = Vector((c.x + sg * (ax_ * 0.85), y_top - 0.004, c.z)); q = Vector((bot.x + sg * 0.019, ANKLE_Y + 0.012, bot.z))
            bar_between(B, "strut%d" % (sg > 0), p, q, 0.0055, 0.0025, calf, B.band("shell"))
            for j, pp in enumerate((p, q)):
                B.sphere("strutbolt%d%d" % (sg > 0, j), tuple(pp + Vector((sg * 0.003, 0, 0))), 0.0032, calf, B.band("dark"), segs=8)
    if level == "Ankle":
        leg_socket(B, legs, [0.19, 0.165, 0.14, 0.115, 0.09, 0.075], 0.0048, calf, B.band("socket"))
        a = lc(legs, 0.075)
        B.loft("clamp", [ell_ring(*lell(legs, 0.079, 0.006), n=20), ell_ring(*lell(legs, 0.071, 0.005), n=20)], calf, B.band("dark"), subsurf=1)
        B.cyl("pylon", tuple(a), (a.x, ANKLE_Y + 0.004, a.z), 0.012, 0.012, calf, B.band("shell"), segs=14)
    elif level == "Thigh":
        leg_socket(B, legs, [0.47, 0.45, 0.43, 0.41, 0.395], 0.0048, thigh, B.band("socket"))
        k = lc(legs, KNEE_Y); c, ax_, az_ = lell(legs, 0.39, 0.0)
        B.loft("tclamp", [ell_ring(*lell(legs, 0.394, 0.005), n=20), ell_ring(*lell(legs, 0.386, 0.004), n=20)], thigh, B.band("dark"), subsurf=1)
        for sg in (-1, 1):
            p = Vector((c.x + sg * ax_ * 0.8, 0.388, c.z)); q = Vector((k.x + sg * 0.03, KNEE_Y + 0.008, k.z))
            bar_between(B, "tstrut%d" % (sg > 0), p, q, 0.007, 0.003, thigh, B.band("shell"))
            B.cyl("kneeplate%d" % (sg > 0), (k.x + sg * 0.027, KNEE_Y, k.z), (k.x + sg * 0.033, KNEE_Y, k.z), 0.02, 0.02, calf, B.band("shell"), segs=16, ref=(0, 1, 0))
        B.cyl("tpylon", (c.x, 0.386, c.z), (k.x, KNEE_Y + 0.022, k.z), 0.012, 0.012, thigh, B.band("shell"), segs=14)
        B.cyl("knee", (k.x - 0.027, KNEE_Y, k.z), (k.x + 0.027, KNEE_Y, k.z), 0.019, 0.019, calf, B.band("dark"), segs=18, bevel=0.002, ref=(0, 1, 0))
        B.cyl("kneeaxle", (k.x - 0.037, KNEE_Y, k.z), (k.x + 0.037, KNEE_Y, k.z), 0.006, 0.006, calf, B.band("shell"), segs=10, ref=(0, 1, 0))
        shin_frame(KNEE_Y - 0.02)
    else:
        leg_socket(B, legs, [0.31, 0.29, 0.27, 0.25, 0.24], 0.0048, calf, B.band("socket"), thigh=thigh)
        shin_frame(0.236)
    mech_foot(B, legs, foot)

def med_fairing(B, legs, y0, y1, prof, bone, ref_y=None, cl=-0.002):
    ys = [y0 + (y1 - y0) * k / (len(prof) - 1) for k in range(len(prof))]
    secs = []
    for y, f in zip(ys, prof):
        c, ax_, az_ = lell(legs, min(y, ref_y) if ref_y else y, cl)
        secs.append((lc(legs, y), ax_ * f, az_ * f))
    leg_panel(B, "fairing", secs, -3.55, 0.41, 0.0025, B.band("socket"), bone, facets=12)

def build_med_leg(B, legs, level):
    thigh, calf, foot = legs["bones"]["thigh"], legs["bones"]["calf"], legs["bones"]["foot"]
    def pylon(y_top):
        top, bot = lc(legs, y_top), lc(legs, ANKLE_Y + 0.016)
        B.cyl("adapter", tuple(top + Vector((0, 0.004, 0))), tuple(top - Vector((0, 0.012, 0))), 0.022, 0.012, calf, B.band("dark"), segs=16, bevel=0.0015)
        B.cyl("pylon", tuple(top - Vector((0, 0.01, 0))), tuple(bot), 0.0125, 0.0115, calf, B.band("shell"), segs=16)
        # carcasa cosmética de polímero (2026-10-17, "hiciste la médica muy delgada"): pantorrilla esbelta casi cerrada,
        # con una ranura por detrás donde se ve el pilón
        med_fairing(B, legs, y_top - 0.012, ANKLE_Y + 0.022, [0.95, 1.0, 0.97, 0.86, 0.72, 0.6], calf, ref_y=0.235)
        B.cyl("pylonclamp", tuple(bot + Vector((0, 0.022, 0))), tuple(bot + Vector((0, 0.008, 0))), 0.0118, 0.0118, calf, B.band("dark"), segs=14, bevel=0.001)
        B.cyl("pylonbase", tuple(bot + Vector((0, 0.004, 0))), (bot.x, 0.034, bot.z), 0.012, 0.017, foot, B.band("dark"), segs=14, bevel=0.0015)
    if level == "Ankle":
        leg_socket(B, legs, [0.19, 0.165, 0.14, 0.115, 0.09, 0.075], 0.0045, calf, B.band("socket"))
        a = lc(legs, 0.075)
        B.cyl("pylonbase", tuple(a), (a.x, 0.034, a.z), 0.02, 0.018, foot, B.band("dark"), segs=16, bevel=0.002)
    elif level == "Thigh":
        leg_socket(B, legs, [0.47, 0.45, 0.43, 0.41, 0.395], 0.0045, thigh, B.band("socket"))
        k = lc(legs, KNEE_Y); c = lc(legs, 0.39)
        B.cyl("tadapter", (c.x, 0.392, c.z), (c.x, 0.376, c.z), 0.024, 0.013, thigh, B.band("dark"), segs=16, bevel=0.0015)
        B.cyl("tpylon", (c.x, 0.378, c.z), (k.x, KNEE_Y + 0.03, k.z), 0.0125, 0.0125, thigh, B.band("shell"), segs=16)
        med_fairing(B, legs, 0.384, KNEE_Y + 0.036, [0.86, 0.8, 0.7, 0.58], thigh, cl=-0.004)
        # rodilla policéntrica: carcasa redondeada con tapas oscuras
        B.loft("knee", [ell_ring(Vector((k.x, KNEE_Y + 0.034, k.z)), 0.016, 0.018, 18), ell_ring(Vector((k.x, KNEE_Y + 0.01, k.z - 0.002)), 0.024, 0.027, 18),
                        ell_ring(Vector((k.x, KNEE_Y - 0.018, k.z - 0.001)), 0.022, 0.025, 18), ell_ring(Vector((k.x, KNEE_Y - 0.04, k.z)), 0.014, 0.016, 18)],
               calf, B.band("socket"), subsurf=1)
        for sg in (-1, 1):
            B.cyl("kneecap%d" % (sg > 0), (k.x + sg * 0.022, KNEE_Y, k.z), (k.x + sg * 0.027, KNEE_Y, k.z), 0.013, 0.012, calf, B.band("dark"), segs=16, ref=(0, 1, 0))
        pylon(KNEE_Y - 0.04)
    else:
        leg_socket(B, legs, [0.31, 0.29, 0.27, 0.25, 0.24], 0.0045, calf, B.band("socket"), thigh=thigh)
        pylon(0.236)
    leg_foot(B, legs, foot, B.band("socket"), True, pylon=False)

CYBER_LEG_PANELS = [(-2.30, -0.84, "plate"), (-0.68, 0.58, "plate2"), (0.78, 2.36, "plate"), (2.56, 3.82, "plate2")]

def cyber_leg_armor(B, legs, y0, y1, bone, cl, split=0.62):
    """Blindaje en franjas (como el antebrazo cyber): placa larga y anillo superpuesto abajo, núcleo y cables en los huecos."""
    def secs(ya, yb, extra, n=3):
        return [lell(legs, ya + (yb - ya) * k / (n - 1), cl + extra) for k in range(n)]
    ym = y0 + (y1 - y0) * split
    B.loft("core", [ell_ring(*lell(legs, y, cl - 0.007), n=20) for y in (y0 + 0.004, (y0 + y1) / 2, y1 - 0.004)], bone, B.band("dark"), subsurf=0)
    for k, (t0, t1, bk) in enumerate(CYBER_LEG_PANELS):
        leg_panel(B, "plateA%d" % k, secs(y0, ym + 0.004, 0.0), t0, t1, 0.003, B.band(bk), bone)
        leg_panel(B, "plateB%d" % k, secs(ym, y1, 0.0022), t0 - 0.06, t1 + 0.06, 0.003, B.band(bk), bone)
        g = t1 + 0.1
        pts = []
        for y, sink in ((y0 + 0.004, 0.0045), (y0 + (y1 - y0) * 0.35, 0.0026), (y0 + (y1 - y0) * 0.7, 0.0026), (y1 - 0.004, 0.0045)):
            c, ax_, az_ = lell(legs, y, cl)
            pts.append((c.x + (ax_ - sink) * math.cos(g), y, c.z + (az_ - sink) * math.sin(g)))
        B.curve("muscle%d" % k, pts, [0.0022, 0.003, 0.003, 0.0022], bone, B.band("cable"), res=2)
    c, ax_, az_ = lell(legs, y0 + (y1 - y0) * 0.3, cl)
    B.box("accent", (c.x, c.y, c.z - az_ - 0.0009), (0.003, abs(y1 - y0) * 0.1, 0.0007), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("accent"), bevel=0.0003)

def actuator(B, name, c, half, r, bone):
    """Disco actuador a los dos lados de una articulación (eje x), con anillo de acento."""
    B.cyl(name, (c.x - half, c.y, c.z), (c.x + half, c.y, c.z), r * 0.8, r * 0.8, bone, B.band("dark"), segs=18, ref=(0, 1, 0))
    for sg in (-1, 1):
        x = c.x + sg * half
        B.cyl(name + "disc%d" % (sg > 0), (x, c.y, c.z), (x + sg * 0.004, c.y, c.z), r, r, bone, B.band("dark"), segs=20, bevel=0.001, ref=(0, 1, 0))
        B.cyl(name + "ring%d" % (sg > 0), (x + sg * 0.004, c.y, c.z), (x + sg * 0.0055, c.y, c.z), r * 0.72, r * 0.72, bone, B.band("accent"), segs=20, ref=(0, 1, 0))

def cyber_foot(B, legs, bone):
    """Pie de placas: suela negra, tres placas superpuestas del tobillo a los dedos, talón grafito y actuador de tobillo."""
    cx, hw, zh, zt = foot_dims(legs); L = zh - zt
    prof = [(0.0, 0.55), (0.1, 0.85), (0.3, 1.0), (0.7, 0.98), (0.9, 0.86), (1.0, 0.6)]
    def wf_at(t):
        for (t0, w0), (t1, w1) in zip(prof, prof[1:]):
            if t0 <= t <= t1: return w0 + (w1 - w0) * (t - t0) / (t1 - t0)
        return prof[-1][1]
    rings = []
    for t, wf in prof:
        z = zh - L * t
        rings.append([(cx + hw * wf * math.cos(2 * math.pi * s / 14), 0.005 + 0.005 * math.sin(2 * math.pi * s / 14), z) for s in range(14)])
    B.loft("sole", rings, bone, B.band("dark"), subsurf=1)
    def top_plate(name, t0, t1, h0, h1, band, lift):
        rs = []
        for t, h in ((t0, h0), ((t0 + t1) / 2, (h0 + h1) / 2), (t1, h1)):
            z = zh - L * t; wf = wf_at(t)
            rs.append([(cx + hw * 0.95 * wf * math.cos(math.pi * s / 8), 0.009 + (h + lift) * math.sin(math.pi * s / 8), z) for s in range(9)])
        outer = [p for r in rs for p in r]
        inner = [(p[0] + (cx - p[0]) * 0.06, p[1] - 0.0025, p[2]) for p in outer]
        verts = outer + inner; n = len(outer)
        faces = []
        for i in range(2):
            for s_ in range(8):
                a_ = i * 9 + s_
                faces.append((a_, a_ + 1, a_ + 10, a_ + 9)); faces.append((n + a_, n + a_ + 9, n + a_ + 10, n + a_ + 1))
        for i in range(2):
            for s_ in (0, 8):
                a_ = i * 9 + s_; faces.append((a_, a_ + 9, n + a_ + 9, n + a_))
        for i in (0, 2):
            for s_ in range(8):
                a_ = i * 9 + s_; faces.append((a_, n + a_, n + a_ + 1, a_ + 1))
        B.mesh(name, verts, faces, bone, band, (Vector(verts[0]), Vector(verts[n - 1])), bevel=0.0005, smooth=False)
    top_plate("footplate0", 0.30, 0.55, 0.034, 0.024, B.band("plate"), 0.0)
    top_plate("footplate1", 0.50, 0.75, 0.024, 0.015, B.band("plate"), 0.0015)
    top_plate("footplate2", 0.71, 0.94, 0.015, 0.009, B.band("plate2"), 0.003)
    B.box("footheel", (cx, 0.02, zh - 0.018), (hw * 0.6, 0.016, 0.016), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), bone, B.band("plate2"), bevel=0.004)
    a = lc(legs, ANKLE_Y)
    B.loft("footankle", [ell_ring(Vector((a.x, ANKLE_Y + 0.02, a.z)), 0.019, 0.023, 16), ell_ring(Vector((a.x, ANKLE_Y - 0.02, a.z + 0.004)), 0.024, 0.032, 16),
                         ell_ring(Vector((a.x, 0.012, a.z + 0.006)), 0.03, 0.04, 16)], bone, B.band("plate"), subsurf=1)
    actuator(B, "pylonankle", Vector((a.x, ANKLE_Y, a.z)), 0.024, 0.012, bone)

def build_cyber_leg(B, legs, level):
    """Pierna cyber (tier 5): encaje de carbono, blindaje en franjas con cables, actuadores dorados en rodilla y tobillo y
    pie de placas."""
    thigh, calf, foot = legs["bones"]["thigh"], legs["bones"]["calf"], legs["bones"]["foot"]
    if level == "Ankle":
        leg_socket(B, legs, [0.19, 0.17, 0.15, 0.13, 0.11, 0.09, 0.075], 0.0045, calf, B.band("socket"))
        cyber_leg_armor(B, legs, 0.165, 0.08, calf, 0.008, split=0.55)
    elif level == "Thigh":
        leg_socket(B, legs, [0.47, 0.45, 0.43, 0.41, 0.395], 0.0045, thigh, B.band("socket"))
        cyber_leg_armor(B, legs, 0.392, 0.29, thigh, 0.002)
        k = lc(legs, KNEE_Y)
        actuator(B, "knee", k, 0.034, 0.02, calf)
        leg_panel(B, "kneecap", [lell(legs, y, 0.006) for y in (KNEE_Y + 0.02, KNEE_Y, KNEE_Y - 0.025)], -2.2, -0.94, 0.004, B.band("plate"), calf)
        cyber_leg_armor(B, legs, KNEE_Y - 0.03, 0.08, calf, 0.0)
    else:
        leg_socket(B, legs, [0.31, 0.29, 0.27, 0.25, 0.24], 0.0045, calf, B.band("socket"), thigh=thigh)
        cyber_leg_armor(B, legs, 0.24, 0.08, calf, 0.0)
    cyber_foot(B, legs, foot)

# ------------------------------------------------------------------ brazos
ARM_CL = 0.0025          # holgura de encajes/manguitos de brazo sobre la piel (3.1.0, antes 0.0045-0.0048)
ARM_SHELL = -0.006       # carcasas que sustituyen al miembro: del tamaño del brazo real tras el margen del loft

def arm_frame(arm):
    return Vector(arm["o"]), Vector(arm["axis"]), Vector(arm["down"]), Vector(arm["front"])

def end_shift(arm, t):
    """Desvío del centro del extremo del encaje respecto al cuerpo vanilla (sólo en el ajuste a TombBody, export_fit --tomb):
    lo que cuelga del encaje (mano, gancho, bola) se mueve igual que el encaje. En vanilla es cero."""
    v = arm.get("end_shift", {}).get("%.3f" % t)
    return Vector(v) if v else Vector((0.0, 0.0, 0.0))

def arm_socket(B, arm, level, bone, band_socket, band_shell, clearance=ARM_CL, subsurf=1):
    o, ax, dn, fr = arm_frame(arm)
    if level == "Wrist":
        ts = [0.07, 0.0775, 0.085, 0.0925, 0.10, 0.1075, 0.115, 0.1225, 0.13, 0.136, 0.142]   # anillos densos: sin subdivisión
        # sin subdivisión: el anillo de 24 lados ya abraza la sección real; la subdivisión añadía +3.5 % y 1.5 mm
        # +1.5 mm en el tramo final: ahí la piel de la muñeca, pesada en parte a la mano, se mueve al girar
        B.loft("cuff", smooth_rings([arm_ring(arm, t, clearance + (0.0015 if t >= 0.115 else 0.0)) for t in ts], 2), bone, band_socket, subsurf=1, tight=True)
        rim = smooth_rings([arm_ring(arm, 0.066, clearance + 0.0015), arm_ring(arm, 0.07, clearance + 0.003), arm_ring(arm, 0.082, clearance + 0.0025), arm_ring(arm, 0.086, clearance + 0.0005)])
        B.loft("rim", rim, bone, band_socket, subsurf=1)
        # anillo de cierre con la sección de la MUÑECA desplazada (en t = 0.154 el cuerpo ya es la palma, ancha y plana,
        # y el anillo salía como una falda puntiaguda)
        wr = arm_ring(arm, 0.142, clearance - 0.002)
        B.loft("collar", [wr, [tuple(Vector(q) + ax * 0.012) for q in wr]], bone, band_shell, subsurf=1)
        return o + ax * 0.154 + end_shift(arm, 0.14)
    if level == "Upper":
        # sin muñón en el antebrazo: carcasa del codo a la muñeca (algo más fina que el brazo) y anillo en el codo
        B.loft("ecuff", smooth_rings([arm_ring(arm, t, clearance - 0.001) for t in (-0.004, 0.004, 0.012)]), bone, band_socket, subsurf=1)
        B.loft("shell", smooth_rings([arm_ring(arm, t, ARM_SHELL) for t in (0.012, 0.035, 0.06, 0.085, 0.105, 0.12)]), bone, band_shell, subsurf=subsurf)
        return o + ax * 0.12
    # junto al codo un poco más de holgura: la piel del brazo se mueve al flexionar
    ts = [(-0.015, clearance + 0.001), (-0.0075, clearance + 0.001), (0.0, clearance + 0.001), (0.0075, clearance), (0.015, clearance),
          (0.0225, clearance), (0.03, clearance), (0.0375, clearance), (0.045, clearance)]
    B.loft("socket", smooth_rings([arm_ring(arm, t, c) for t, c in ts], 2), bone, band_socket, subsurf=1, tight=True)
    rim = smooth_rings([arm_ring(arm, -0.019, clearance + 0.0025), arm_ring(arm, -0.015, clearance + 0.004), arm_ring(arm, -0.003, clearance + 0.0035), arm_ring(arm, 0.001, clearance + 0.0015)])
    B.loft("rim", rim, bone, band_socket, subsurf=1)
    ts = [0.045, 0.065, 0.085, 0.105, 0.12]
    B.loft("shell", smooth_rings([arm_ring(arm, t, ARM_SHELL) for t in ts]), bone, band_shell, subsurf=subsurf)
    return o + ax * 0.12

def arm_straps(B, arm, ts, clearance, bone):
    o, ax, dn, fr = arm_frame(arm)
    for i, t in enumerate(ts):
        B.loft("strap%d" % i, [arm_ring(arm, t - 0.006, clearance + 0.0018), arm_ring(arm, t + 0.006, clearance + 0.0018)], bone, B.band("strap"), subsurf=1)
        r = arm_ring(arm, t, clearance + 0.0018)
        top = max(r, key=lambda p: -(Vector(p) - o).dot(dn))      # lado superior (-down)
        B.box("buckle%d" % i, Vector(top) - dn * 0.0025, (0.002, 0.005, 0.008), (tuple(dn), tuple(fr), tuple(ax)), bone, B.band("strap"), bevel=0.001)

def mech_bars_arm(B, arm, level, bone):
    o, ax, dn, fr = arm_frame(arm)
    ts = [0.08, 0.10, 0.12, 0.14] if level == "Wrist" else [0.03, 0.06, 0.09, 0.12]
    cl = ARM_CL if level == "Wrist" else ARM_SHELL
    for sgn, nm in ((-1, "barF"), (1, "barB")):
        pts = []
        for t in ts:
            r = [Vector(p) for p in arm_ring(arm, t, cl)]
            c = sum(r, Vector()) / len(r)
            d = [(p - c).dot(fr) for p in r]
            edge = c + fr * (max(d) if sgn > 0 else min(d))
            pts.append(tuple(edge + fr * sgn * 0.0032))
        B.curve(nm, pts, [0.0034] * len(pts), bone, B.band("dark"), res=2)
        for k in (0, len(pts) - 1):
            p = Vector(pts[k]); B.sphere("rivet%s%d" % (nm, k), tuple(p + fr * sgn * 0.003), 0.003, bone, B.band("dark"), segs=8)

WRIST_BALL = 0.0165      # radio de la rótula de muñeca (3.2.0)

def hand_scale(arm):
    """Ancho, grosor y largo de la mano del cuerpo frente a la del hombre vanilla (fit "hand": extensión de los vértices
    del hueso de la mano). 2026-10-17: con las proporciones del hombre, en la mujer la mano protésica salía un 37 % más
    gruesa que la natural."""
    ref = fit["bodies"]["Male"]["arms"]["R"]["hand"]; h = arm.get("hand") or ref
    r = lambda k: (h[k][1] - h[k][0]) / max(1e-6, ref[k][1] - ref[k][0])
    return r("front"), r("down"), r("t")

FINGER_LEN = 0.95          # dedos algo más cortos desde que son más rectos (7° + 24°): las puntas pasaban de la natural

def hand(B, q, arm, band, medical, joint_band=None, blend=False):
    """Mano de las prótesis mecánica y médica. Rehecha en 3.1.0 (comentario de la ronda 2: "desentonan con las manos
    del juego"): palma con perfil de mano (estrecha en la muñeca, ancha y plana en los nudillos), dedos gruesos, juntos
    y algo curvados como las manos "manopla" del juego, pulgar robusto y, en la mecánica, un eje en los nudillos.
    Tamaño = el de la mano vanilla con dedos (puntas en t ~ 0.26 del antebrazo). La palma mira a +dn.

    3.2.0, la mano se cierra al agarrar (petición del Workshop): ya no es rígida al antebrazo. La palma va al hueso de
    la mano y nace en la rótula de muñeca q; los dedos van a Bip01_X_Finger1 y el pulgar a Bip01_X_Finger0, como la mano
    vanilla. Medido en los clips del juego: Finger1 gira siempre alrededor de SU eje Y local (bisagra, 34-77° al
    agarrar), así que los nudillos se ponen justo sobre esa recta (fit.json "joints"): el dedo gira sobre su nudillo y
    no se separa de la palma. El pulgar nace en el pivote de Finger0, tapado por una bola centrada en él (gira sobre
    ejes variables, y una esfera centrada en el pivote es invariante a cualquier giro)."""
    o, ax, dn, fr = arm_frame(arm)
    q = Vector(q)
    hb, f0, f1 = arm["bones"]["hand"], arm["bones"]["finger0"], arm["bones"]["finger1"]
    J = arm["joints"]
    P0, P1, a1 = Vector(J["finger0"]), Vector(J["finger1"]), norm(Vector(J["finger1_axis"]))
    if a1.dot(fr) < 0: a1 = -a1
    hs_w, hs_t, hs_l = hand_scale(arm)
    SW, ST = 1.12 * hs_w, 1.35 * hs_t ** 2  # ancho y grueso (la mano del juego es una manopla gruesa), a la medida del cuerpo
    SR = (SW + ST) / 2                     # radios de dedos
    def rr(c, hw, ht, n=24, e=3.0):
        pts = []
        for k in range(n):
            th = 2 * math.pi * k / n; cx, sy = math.cos(th), math.sin(th)
            r = 1.0 / ((abs(cx) ** e + abs(sy) ** e) ** (1.0 / e))
            pts.append(tuple(c + fr * (hw * r * cx) + dn * (ht * r * sy)))
        return pts
    k = 1.03 if medical else 1.0
    # palma: de la rótula a la recta de los nudillos; el eje baja hacia la palma (+dn) hasta la altura de la bisagra
    Lp = (P1 - q).dot(ax); dK = (P1 - q).dot(dn)
    prof = [(0.0, 0.017, 0.0105), (0.24, 0.022, 0.0115), (0.52, 0.0275, 0.0118), (0.80, 0.030, 0.0112), (1.0, 0.029, 0.0100)]
    palm = B.loft("palm", [rr(q + ax * (u * Lp) + dn * (dK * u * u), hw * k * SW, ht * k * ST) for u, hw, ht in prof], hb, band, subsurf=1)
    if blend:
        # 3.3 (cabezales en la montura). 2026-10-17 ("las prótesis quedan supertorcidas... arregla las articulaciones y
        # animaciones"): las animaciones del juego giran la mano hasta 130° sobre el antebrazo (golpe fallado, comer,
        # saltar vallas, reacción al mordisco) y la franja de la palma repartida entre antebrazo y mano se retorcía como
        # un caramelo. Ahora la palma va entera a la mano (la montura ya está pegada a la muñeca) y un anillo de la
        # palma tapa la unión con la rótula: el giro se ve como el de un rotador de muñeca.
        hw0, ht0 = prof[0][1] * k * SW, prof[0][2] * k * ST
        B.cyl("palmcap", tuple(q - ax * 0.001), tuple(q + ax * 0.009), (hw0 + 0.0035, ht0 + 0.0035), (hw0 + 0.004, ht0 + 0.004), hb,
              joint_band if joint_band is not None else band, segs=20, bevel=0.0006, ref=tuple(fr))
    # nudillos sobre la bisagra, centrados en la palma
    H0 = P1 + a1 * ((q - P1).dot(fr) / a1.dot(fr))
    # dedos en curva relajada: salen a 15° hacia la palma y se curvan 40° más hasta la punta (puntas donde las de la mano
    # vanilla, t ~ 0.26 y dn ~ +0.04). Al agarrar, la bisagra gira 34-77° y las puntas vuelven hacia la palma (puño);
    # rectos quedaban en "L" (2026-10-16, primeros renders). 2026-10-17: 7° + 24° (antes 15° + 40°): de frente la mano
    # se veía "inclinada hacia adentro" frente a la natural, que en reposo tiene los dedos casi rectos.
    AL, PHI = math.radians(float(os.environ.get('TOC_AL', 7))), math.radians(float(os.environ.get('TOC_PHI', 24)))
    def finger_pts(K, ln):
        pts, p, n = [tuple(K)], Vector(K), 24
        marks = {round(0.42 * n), round(0.78 * n), n}
        for j in range(1, n + 1):
            th = AL + PHI * ((j - 0.5) / n) ** 1.3
            p = p + (ax * math.cos(th) + dn * math.sin(th)) * (ln / n)
            if j in marks: pts.append(tuple(p))
        return pts
    r0 = 0.0072 * k * SR
    for i, (off, ln) in enumerate(((-0.021, 0.037), (-0.007, 0.045), (0.007, 0.048), (0.021, 0.044))):
        K = H0 + a1 * (off * k * SW / a1.dot(fr))
        pts = finger_pts(K, ln * hs_l * FINGER_LEN * 0.95)       # las de la mecánica / médica pasaban un 6 %
        rr_ = [r0, 0.0068 * k * SR, 0.0062 * k * SR, 0.0055 * k * SR]
        B.curve("finger%d" % i, pts, rr_, f1, band, res=3)
        B.sphere("tip%d" % i, pts[-1], rr_[-1], f1, band, segs=10)
        B.sphere("knuckle%d" % i, tuple(K), r0 * 1.04, hb, band, segs=12)
    # pulgar: nace en el pivote de Finger0
    # algo más corto que el de 3.1.0: al agarrar (Finger0 gira hasta 75°) un pulgar largo asomaba por fuera del mango
    pts = [tuple(P0), tuple(P0 + fr * (0.010 * SW) + ax * 0.009 + dn * (0.004 * ST)),
           tuple(P0 + fr * (0.013 * SW) + ax * 0.019 + dn * (0.009 * ST)), tuple(P0 + fr * (0.012 * SW) + ax * 0.026 + dn * (0.014 * ST))]
    B.curve("thumb", pts, [0.0085 * k * SR, 0.0078 * k * SR, 0.007 * k * SR, 0.006 * k * SR], f0, band, res=3)
    B.sphere("thumbtip", pts[-1], 0.006 * k * SR, f0, band, segs=10)
    B.sphere("thumbball", tuple(P0), 0.0085 * k * SR * 1.06, hb, band, segs=12)
    if joint_band is not None:
        # eje de los nudillos de la mecánica: sobre la bisagra real, así no se mueve al cerrar los dedos
        w = 0.036 * SW / a1.dot(fr)
        B.cyl("axle", tuple(H0 - a1 * w), tuple(H0 + a1 * w), 0.0052, 0.0052, hb, joint_band, segs=12, bevel=0.001, ref=tuple(ax))

def build_peg_arm(B, arm, level):
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("wood"))
    arm_straps(B, arm, (0.09, 0.128) if level == "Wrist" else ((0.005, 0.038) if level == "" else ()), ARM_CL, bone)
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
    arm_straps(B, arm, (0.09, 0.128) if level == "Wrist" else ((0.005, 0.038) if level == "" else ()), ARM_CL, bone)
    B.cyl("wrist", tuple(s), tuple(s + ax * 0.016), 0.016, 0.0125, bone, B.band("dark"), segs=16, bevel=0.003)
    sh = s + ax * 0.016
    B.cyl("shaft", tuple(sh), tuple(sh + ax * 0.03), 0.0085, 0.008, bone, B.band("steel"), segs=12)
    base = sh + ax * 0.03
    B.cyl("band", tuple(base - ax * 0.005), tuple(base + ax * 0.005), 0.0125, 0.0125, bone, B.band("rubber"), segs=14, bevel=0.003)
    R = 0.031
    # el gancho se curva hacia +dn (lado de la palma): con el brazo colgando mira hacia dentro, hacia el cuerpo
    # (petición del usuario, 2026-10-14; antes se curvaba hacia delante). Las dos puntas, separadas delante/detrás.
    for i, off in enumerate((-0.0075, 0.0075)):
        c = base + dn * R + fr * off
        pts, rr = [], []
        n = 9
        for k in range(n):
            th = math.radians(165.0) * k / (n - 1)
            pts.append(tuple(c + ax * (R * math.sin(th)) - dn * (R * math.cos(th))))
            rr.append(0.0058 - 0.0028 * k / (n - 1))
        B.curve("prong%d" % i, pts, rr, bone, B.band("polished"), res=3)
        B.sphere("prongtip%d" % i, pts[-1], rr[-1], bone, B.band("polished"), segs=8)

def build_mech_arm(B, arm, level, medical):
    o, ax, dn, fr = arm_frame(arm); bone, hb = arm["bones"]["forearm"], arm["bones"]["hand"]
    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("shell"), clearance=ARM_CL, subsurf=1)
    if not medical: mech_bars_arm(B, arm, level, bone)
    # 3.2.0: la mano sigue al hueso de la mano (antes rígida al antebrazo: con la palma rígida y los dedos rectos el
    # objeto en la mano quedaba fuera de ella). Rótula de muñeca:
    #  - antebrazo / brazo: la articulación real (pivote del hueso de la mano) está libre -> unidad de muñeca redonda
    #    hasta el pivote y bola centrada en él: invariante a cualquier giro, no se abre ni al girar ni al flexionar.
    #  - muñeca: el pivote real queda dentro del brazal -> bola junto al collar, en el eje (el giro, que es lo que más
    #    hace la mano, la deja en su sitio; al flexionar resbala sobre la tapa del collar).
    hb = arm["bones"]["hand"]
    if level == "Wrist":
        q = s + ax * 0.006
    else:
        q = Vector(arm["joints"]["hand"])
        B.cyl("wristunit", tuple(s - ax * 0.002), tuple(q), 0.0145, 0.0145, bone, B.band("dark"), segs=16, bevel=0.0015, ref=tuple(dn))
    B.sphere("wristball", tuple(q), WRIST_BALL, hb, B.band("dark"), segs=16)
    # mecánica: mano de acero claro (banda shell) con nudillos y eje oscuros; médica: banda "dark" repintada de polímero claro
    if medical: hand(B, q, arm, B.band("dark"), True)
    else: hand(B, q, arm, B.band("shell"), False, joint_band=B.band("dark"))

def bracer_section(B, arm, level):
    """Parte del antebrazo de los brazos-arma (motosierra, bayoneta) según el nivel de amputación:
      - Wrist (falta la mano): brazal de cuero con dos férulas de acero y copa en la muñeca.
      - ForeArm: encaje de cuero en el muñón y carcasa de acero que sustituye lo que falta.
      - Upper: carcasa de acero del codo al acople (el brazo y la bisagra los pone build_upper_section).
    Devuelve (t_end, end_cl): dónde acaba y con qué holgura, para colgar el acople. Todo rígido al antebrazo."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    cl = ARM_CL
    def rivet(name, p, r=0.003): B.sphere(name, tuple(p), r, bone, B.band("polished"), segs=8)
    def surf(t, d, extra, clr=cl):
        r = [Vector(p) for p in arm_ring(arm, t, clr)]
        c = sum(r, Vector()) / len(r)
        return max(r, key=lambda p: (p - c).dot(d)) + d * extra
    if level == "Wrist":
        ts = [0.03, 0.045, 0.06, 0.075, 0.09, 0.105, 0.118]
        B.loft("bracer", smooth_rings([arm_ring(arm, t, cl) for t in ts], 2), bone, B.band("socket"), subsurf=1, tight=True)
        B.loft("rim", smooth_rings([arm_ring(arm, 0.026, cl + 0.0015), arm_ring(arm, 0.03, cl + 0.003), arm_ring(arm, 0.038, cl + 0.0025),
                                   arm_ring(arm, 0.042, cl + 0.0005)]), bone, B.band("dark"), subsurf=1)
        arm_straps(B, arm, (0.052, 0.09), cl, bone)
        for k, d in enumerate((fr, -fr)):        # férulas de acero delante y detrás del antebrazo
            pts = [tuple(surf(t, d, 0.004)) for t in (0.036, 0.075, 0.112)]
            B.curve("splint%d" % k, pts, [0.0032] * 3, bone, B.band("dark"), res=2)
            rivet("splintrivet%da" % k, Vector(pts[0]) + d * 0.002); rivet("splintrivet%db" % k, Vector(pts[-1]) + d * 0.002)
        cup = [arm_ring(arm, t, cl + e) for t, e in ((0.112, 0.0), (0.122, 0.001), (0.134, 0.002), (0.142, 0.0025))]
        B.loft("cup", smooth_rings(cup), bone, B.band("steel"), subsurf=1)
        t_end = 0.142; end_cl = cl + 0.0025
    elif level == "Upper":
        # antebrazo entero protésico: carcasa de acero del codo al acople, con nervios
        B.loft("ecuff", smooth_rings([arm_ring(arm, t, cl - 0.001) for t in (-0.004, 0.004, 0.012)]), bone, B.band("dark"), subsurf=1)
        shell = [arm_ring(arm, t, e) for t, e in ((0.012, ARM_SHELL + 0.002), (0.04, ARM_SHELL), (0.07, ARM_SHELL), (0.095, ARM_SHELL), (0.112, ARM_SHELL), (0.12, ARM_SHELL + 0.001))]
        B.loft("shell", smooth_rings(shell), bone, B.band("steel"), subsurf=1)
        for k, d in enumerate((fr, -fr)):
            pts = [tuple(surf(t, d, 0.0022, ARM_SHELL)) for t in (0.02, 0.06, 0.1, 0.116)]
            B.curve("rib%d" % k, pts, [0.003] * 4, bone, B.band("dark"), res=2)
        t_end = 0.12; end_cl = ARM_SHELL + 0.001
    else:
        ts = [-0.015, 0.0, 0.015, 0.03, 0.045]
        B.loft("socket", smooth_rings([arm_ring(arm, t, cl) for t in ts], 2), bone, B.band("socket"), subsurf=1, tight=True)
        B.loft("rim", smooth_rings([arm_ring(arm, -0.019, cl + 0.0025), arm_ring(arm, -0.015, cl + 0.004), arm_ring(arm, -0.003, cl + 0.0035),
                                   arm_ring(arm, 0.001, cl + 0.0015)]), bone, B.band("dark"), subsurf=1)
        arm_straps(B, arm, (0.005, 0.034), cl, bone)
        # carcasa de acero que sustituye la parte del antebrazo que falta (algo más fina que el brazo)
        shell = [arm_ring(arm, t, e) for t, e in ((0.043, cl + 0.001), (0.055, -0.002), (0.075, ARM_SHELL), (0.095, ARM_SHELL), (0.112, ARM_SHELL), (0.12, ARM_SHELL + 0.001))]
        B.loft("shell", smooth_rings(shell), bone, B.band("steel"), subsurf=1)
        B.loft("band", [arm_ring(arm, 0.043, cl + 0.002), arm_ring(arm, 0.05, cl + 0.002)], bone, B.band("dark"), subsurf=1)
        for k, d in enumerate((fr, -fr)):        # nervios con remaches a lo largo de la carcasa
            pts = [tuple(surf(t, d, 0.0022, ARM_SHELL)) for t in (0.056, 0.078, 0.1, 0.116)]
            B.curve("rib%d" % k, pts, [0.003] * 4, bone, B.band("dark"), res=2)
            for j, pp in enumerate(pts[::3]): rivet("ribrivet%d%d" % (k, j), Vector(pp) + d * 0.0022, 0.0026)
        t_end = 0.12; end_cl = ARM_SHELL + 0.001
    return t_end, end_cl

def build_saw_arm(B, arm, level, saw):
    """Brazo motosierra como el de Ash (Evil Dead 2): la motosierra vanilla sin asas con la espada como prolongación
    del antebrazo, unida por un acople mecánico (abrazadera con orejeta y perno, vástago, dos pletinas laterales
    atornilladas, piñón y placa de montaje). Todo rígido al hueso del antebrazo (como la mano mecánica).
    Por nivel de amputación:
      - Wrist (falta la mano): el antebrazo está entero -> brazal de cuero con dos férulas de acero y copa en la muñeca.
      - ForeArm (falta medio antebrazo): encaje de cuero en el muñón y carcasa de acero que sustituye lo que falta."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    cl = ARM_CL
    side = -dn                               # con el brazo colgando: -dn = hacia fuera, dn = hacia el cuerpo
    def rivet(name, p, r=0.003): B.sphere(name, tuple(p), r, bone, B.band("polished"), segs=8)
    def surf(t, d, extra, clr=cl):
        r = [Vector(p) for p in arm_ring(arm, t, clr)]
        c = sum(r, Vector()) / len(r)
        return max(r, key=lambda p: (p - c).dot(d)) + d * extra
    def hexbolt(name, p, axis, r=0.0042, hgt=0.003):
        axis = norm(Vector(axis))
        B.cyl(name, tuple(p), tuple(p + axis * hgt), r, r, bone, B.band("polished"), segs=6, bevel=0.0007,
              ref=tuple(ax if abs(axis.dot(ax)) < 0.9 else fr))
    t_end, end_cl = bracer_section(B, arm, level)
    # ---------------- acople
    end = [Vector(p) for p in arm_ring(arm, t_end, end_cl)]
    c_end = sum(end, Vector()) / len(end)
    e_dn = max(abs((p - c_end).dot(dn)) for p in end) + 0.004
    e_fr = max(abs((p - c_end).dot(fr)) for p in end) + 0.004
    ho, hn = saw["body_half"]
    L = 0.052                                # del extremo del antebrazo a la cara de la placa
    # abrazadera (collar elíptico ajustado al extremo) con orejeta delante y perno pasante
    B.cyl("collar", tuple(c_end - ax * 0.004), tuple(c_end + ax * 0.012), (e_dn, e_fr), (e_dn, e_fr), bone, B.band("dark"), segs=20, bevel=0.0018, ref=tuple(dn))
    lug_c = c_end + ax * 0.004 + fr * (e_fr + 0.005)
    for k, sg in enumerate((-1, 1)):
        B.box("lug%d" % k, lug_c + dn * (sg * 0.0048), (0.0065, 0.0016, 0.0062), (tuple(ax), tuple(dn), tuple(fr)), bone, B.band("dark"), bevel=0.0008)
    B.cyl("clampbolt", tuple(lug_c - dn * 0.011), tuple(lug_c + dn * 0.011), 0.0022, 0.0022, bone, B.band("polished"), segs=8, ref=tuple(ax))
    hexbolt("nut0", lug_c + dn * 0.0064, dn, 0.0040, 0.0032); hexbolt("nut1", lug_c - dn * 0.0064, -dn, 0.0040, 0.0032)
    # placa de montaje: rectángulo redondeado del tamaño del motor, biselada
    def rr(center, a_, b_, e=4.0, n=24):
        pts = []
        for k in range(n):
            th = 2 * math.pi * k / n; c_, s_ = math.cos(th), math.sin(th)
            r = 1.0 / ((abs(c_) ** e + abs(s_) ** e) ** (1.0 / e))
            pts.append(tuple(center + dn * (a_ * r * c_) + fr * (b_ * r * s_)))
        return pts
    P_top, P_bot = c_end + ax * (L - 0.009), c_end + ax * L
    # la placa se hunde en la cara superior biselada del motor (sin holgura entre ambos)
    B.loft("plate", [rr(P_top, ho * 0.96, hn * 0.96), rr(P_bot, ho * 0.96, hn * 0.96)], bone, B.band("dark"), subsurf=0, bevel=0.0025)
    # vástago central
    B.cyl("stem", tuple(c_end + ax * 0.011), tuple(P_top + ax * 0.001), 0.0125, 0.0155, bone, B.band("steel"), segs=16, bevel=0.0015, ref=tuple(dn))
    B.cyl("stemring", tuple(P_top - ax * 0.008), tuple(P_top), 0.0185, 0.021, bone, B.band("dark"), segs=16, bevel=0.0015, ref=tuple(dn))
    # pletinas laterales: del collar a la placa, abiertas hacia fuera, con tornillos hexagonales en los extremos
    for k, sg in enumerate((1, -1)):
        A = c_end + ax * 0.003 + dn * sg * (e_dn + 0.0032)
        Bp = P_top + dn * sg * (ho * 0.78)
        w = norm(Bp - A); u = fr; v = norm(w.cross(u))
        if v.dot(dn * sg) < 0: v = -v
        B.box("bar%d" % k, (A + Bp) / 2, (0.0115, 0.0026, (Bp - A).length / 2 + 0.003), (tuple(u), tuple(v), tuple(w)), bone, B.band("steel"), bevel=0.0012)
        hexbolt("hexA%d" % k, A + v * 0.0024, v); hexbolt("hexB%d" % k, Bp + v * 0.0024 - w * 0.004, v)
        if sg < 0:
            # piñón sobre la pletina exterior, como el de la figura
            gc = (A + Bp) / 2 + v * 0.0026
            B.cyl("gear", tuple(gc), tuple(gc + v * 0.0045), 0.0125, 0.0125, bone, B.band("dark"), segs=12, ref=tuple(w))
            for j in range(10):
                an = 2 * math.pi * j / 10; rd = w * math.cos(an) + u * math.sin(an)
                B.box("tooth%d" % j, gc + v * 0.00225 + rd * 0.0145, (0.0026, 0.002, 0.00225), (tuple(rd), tuple(v.cross(rd)), tuple(v)), bone, B.band("dark"))
            B.sphere("hub", tuple(gc + v * 0.005), 0.0042, bone, B.band("polished"), segs=8)
    # manguera de gasolina: del antebrazo, por delante, hasta el borde de la placa
    h = norm(side * 0.45 + fr * 0.9)
    t_h = 0.07 if level == "Wrist" else (0.03 if level == "Upper" else 0.025)
    h_cl = ARM_SHELL if level == "Upper" else cl           # nivel Upper: la manguera sale de la carcasa, más fina
    p_plate = P_top + h * (max(ho, hn) * 0.92) - ax * 0.002
    B.curve("hose", [tuple(surf(t_h, h, 0.0045, h_cl)), tuple(surf(t_end - 0.012, h, 0.006, end_cl)),
                     tuple(c_end + ax * (L * 0.45) + h * (max(e_dn, e_fr) + 0.012)), tuple(p_plate)], [0.0042] * 4, bone, B.band("rubber"), res=3)
    # motosierra: base del motor sobre la placa, espada (b) por el eje del antebrazo, o -> dn, n -> +-fr
    sb, so, sn, base = Vector(saw["b"]), Vector(saw["o"]), Vector(saw["n"]), Vector(saw["base"])
    det_l = sb.dot(so.cross(sn)); det_w = ax.dot(dn.cross(fr))
    fr_s = fr if (det_l > 0) == (det_w > 0) else -fr
    S0 = P_bot - ax * 0.012
    def place(p):
        d = Vector(p) - base
        return S0 + ax * d.dot(sb) + dn * d.dot(so) + fr_s * d.dot(sn)
    def turn(nv):
        nv = Vector(nv)
        return norm(ax * nv.dot(sb) + dn * nv.dot(so) + fr_s * nv.dot(sn))
    B.raw.append({"verts": [tuple(place(p)) for p in saw["verts"]], "normals": [tuple(turn(n)) for n in saw["normals"]],
                  "uvs": saw["uvs"], "faces": saw["faces"], "bone": bone, "name": "saw"})

def build_knife_arm(B, arm, level):
    """Brazo bayoneta (3.2.0), como el de Merle en The Walking Dead: sobre el muñón el mismo brazal / carcasa que el
    brazo motosierra (bracer_section) y en la punta una copa de acero cerrada, una virola, una guarda y una hoja de
    bayoneta en línea con el antebrazo, el filo hacia la palma. Sólo derecho (el juego ataca con la mano principal).
    Todo rígido al antebrazo; el arma (TOC.MountedBlade) es invisible y usa las animaciones de cuchillo (estocada),
    que empujan el antebrazo hacia delante: la hoja en línea con él apuñala."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    t_end, end_cl = bracer_section(B, arm, level)
    end = [Vector(p) for p in arm_ring(arm, t_end, end_cl)]
    c = sum(end, Vector()) / len(end)
    e_dn = max(abs((p - c).dot(dn)) for p in end) + 0.002
    e_fr = max(abs((p - c).dot(fr)) for p in end) + 0.002
    # casquete que cierra la copa
    caps = []
    for d, f in ((0.0, 1.0), (0.007, 0.93), (0.014, 0.74), (0.019, 0.44)):
        cc = c + ax * d
        caps.append([tuple(cc + dn * (e_dn * f * math.cos(2 * math.pi * j / 20)) + fr * (e_fr * f * math.sin(2 * math.pi * j / 20))) for j in range(20)])
    B.loft("endcap", caps, bone, B.band("dark"), subsurf=1)
    for j in range(6):                       # remaches en el borde del casquete
        an = 2 * math.pi * (j + 0.5) / 6
        p = c + ax * 0.004 + dn * ((e_dn + 0.0006) * math.cos(an)) + fr * ((e_fr + 0.0006) * math.sin(an))
        B.sphere("caprivet%d" % j, tuple(p), 0.0025, bone, B.band("polished"), segs=8)
    # virola y guarda
    f0 = c + ax * 0.015
    B.cyl("ferrule", tuple(f0), tuple(f0 + ax * 0.026), 0.0105, 0.0085, bone, B.band("steel"), segs=14, bevel=0.0012, ref=tuple(dn))
    g = f0 + ax * 0.027
    B.box("guard", tuple(g), (0.0035, 0.020, 0.0072), (tuple(ax), tuple(dn), tuple(fr)), bone, B.band("dark"), bevel=0.0012)
    # apaño casero: cinta americana enrollada en la virola y sobre la junta de la carcasa con el casquete
    def wrap(name, centers, radii):
        rings = []
        for k, (cc, r) in enumerate(zip(centers, radii)):
            j = 0.0005 * math.sin(k * 2.3)
            rings.append([tuple(cc + dn * ((r + j) * math.cos(2 * math.pi * i / 16)) + fr * ((r - j) * math.sin(2 * math.pi * i / 16))) for i in range(16)])
        B.loft(name, rings, bone, B.band("rubber"), subsurf=1)
    wrap("wrap0", [f0 + ax * d for d in (0.002, 0.007, 0.012, 0.017)], [0.0116, 0.0119, 0.0113, 0.0108])
    jr = [Vector(q) for q in arm_ring(arm, t_end - 0.004, end_cl + 0.0014)]
    wrap("wrap1", [c + ax * d for d in (-0.008, -0.003, 0.002, 0.006)],
         [max((q - c).length for q in jr) * f for f in (1.0, 1.02, 1.01, 0.97)])
    # hoja: sección hexagonal (lomo hacia -dn, filo hacia +dn), punta recortada en el lomo
    L, n, rings = 0.15, 16, []
    for k in range(n + 1):
        u = k / n
        we = 0.0125 * (1.0 if u < 0.6 else max(0.03, 1 - ((u - 0.6) / 0.4) ** 1.5))      # del eje al filo
        ws = 0.0072 * (1.0 if u < 0.7 else max(0.03, 1 - ((u - 0.7) / 0.3) ** 0.8))      # del eje al lomo
        th = max(0.0004, 0.0023 * (1 - 0.65 * u))                                          # medio grueso
        cc = g + ax * (0.0035 + L * u)
        pts = [(-ws, th), (we * 0.3, th), (we, 0.0), (we * 0.3, -th), (-ws, -th), (-ws - th * 0.6, 0.0)]
        rings.append([tuple(cc + dn * a + fr * b) for a, b in pts])
    B.loft("blade", rings, bone, B.band("polished"), subsurf=0, smooth=False)

# ------------------------------------------------------------------ 3.3 modular: bases y cabezales (DISENO_3.3_MODULAR.md)
# Todas las bases acaban en la MONTURA ESTÁNDAR: una brida redonda en el eje del antebrazo, en t = largo del antebrazo +
# MOUNT_GAP (justo pasada la muñeca). Los cabezales empiezan ahí: un solo modelo por lado y sexo vale para los tres
# niveles de amputación.
# 2026-10-17 ("las manos están desfasadas en posición y tamaño... que se compacte en la muñeca"): antes 0.019 y la palma
# empezaba 2.5 cm pasada la muñeca real. El muñón de mano acaba en t ~ 0.1405 (forearm_len 0.137): la montura queda
# justo al final del encaje (t ~ 0.146) y la rótula pegada a la brida (WRIST_OFF)
MOUNT_GAP = 0.009
WRIST_OFF = 0.003
MOUNT_R = 0.0175

def mount_point(arm):
    o, ax, dn, fr = arm_frame(arm)
    return o + ax * (arm["forearm_len"] + MOUNT_GAP)

def mount_flange(B, arm, band_key="dark"):
    """Brida de la montura: disco con cuatro tornillos (rígida al antebrazo)."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    m = mount_point(arm)
    B.cyl("mountflange", tuple(m - ax * 0.006), tuple(m), MOUNT_R, MOUNT_R, bone, B.band(band_key), segs=20, bevel=0.0012, ref=tuple(dn))
    for k in range(4):
        an = 2 * math.pi * (k + 0.5) / 4
        p = m - ax * 0.001 + (dn * math.cos(an) + fr * math.sin(an)) * (MOUNT_R - 0.003)
        B.sphere("mountbolt%d" % k, tuple(p), 0.0022, bone, B.band(band_key), segs=8)
    return m

def socket_only(B, arm, level, band_socket, band_rim):
    """Encaje sobre el muñón sin la carcasa que sustituía el resto del antebrazo. Devuelve dónde acaba el encaje (t)."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]; cl = ARM_CL
    if level == "Wrist":
        ts = [0.07, 0.0775, 0.085, 0.0925, 0.10, 0.1075, 0.115, 0.1225, 0.13, 0.136, 0.142]
        B.loft("cuff", smooth_rings([arm_ring(arm, t, cl + (0.0015 if t >= 0.115 else 0.0)) for t in ts], 2), bone, band_socket, subsurf=1, tight=True)
        B.loft("rim", smooth_rings([arm_ring(arm, 0.066, cl + 0.0015), arm_ring(arm, 0.07, cl + 0.003), arm_ring(arm, 0.082, cl + 0.0025),
                                   arm_ring(arm, 0.086, cl + 0.0005)]), bone, band_rim, subsurf=1)
        wr = arm_ring(arm, 0.142, cl - 0.002)
        B.loft("collar", [wr, [tuple(Vector(q) + ax * 0.004) for q in wr]], bone, band_rim, subsurf=1)
        return 0.146
    if level == "Upper":
        B.loft("ecuff", smooth_rings([arm_ring(arm, t, cl - 0.001) for t in (-0.004, 0.004, 0.012)]), bone, band_rim, subsurf=1)
        return 0.012
    ts = [(-0.015, cl + 0.001), (-0.0075, cl + 0.001), (0.0, cl + 0.001), (0.0075, cl), (0.015, cl), (0.0225, cl), (0.03, cl), (0.0375, cl), (0.045, cl)]
    B.loft("socket", smooth_rings([arm_ring(arm, t, c) for t, c in ts], 2), bone, band_socket, subsurf=1, tight=True)
    B.loft("rim", smooth_rings([arm_ring(arm, -0.019, cl + 0.0025), arm_ring(arm, -0.015, cl + 0.004), arm_ring(arm, -0.003, cl + 0.0035),
                               arm_ring(arm, 0.001, cl + 0.0015)]), bone, band_rim, subsurf=1)
    return 0.045

def band_ring(B, name, c, ax_, dn_, fr_, a_out, b_out, length, thick, bone, band, n=24):
    """Anillo hueco (banda) elíptico alrededor de ax_: semiejes a_out (dn) y b_out (fr), largo y grueso de pared."""
    def ring(t, k):
        return [tuple(c + ax_ * t + dn_ * ((a_out - k) * math.cos(2 * math.pi * i / n)) + fr_ * ((b_out - k) * math.sin(2 * math.pi * i / n))) for i in range(n)]
    rings = [ring(-length / 2, 0), ring(length / 2, 0), ring(length / 2, thick), ring(-length / 2, thick), ring(-length / 2, 0)]
    return B.loft(name, rings, bone, band, subsurf=0, caps=(False, False), bevel=0.0006)

def build_mech_frame(B, arm, level):
    """Base mecánica hueca (3.3): ya no copia la forma del brazo (la piel de debajo está oculta). Encaje en el muñón, anillo
    de acero, dos pletinas acodadas (radio y cúbito) con anillo intermedio, arriostrado en X por el dorso, pistón
    hidráulico por la palma, motor de giro de muñeca, dos cables, anillo de muñeca y la brida de la montura.
    A nivel mano el antebrazo es real: brazal con pletinas laterales y la brida."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    t0 = socket_only(B, arm, level, B.band("socket"), B.band("dark"))
    m = mount_point(arm); tm = (m - o).dot(ax)
    if level == "Wrist":
        mech_bars_arm(B, arm, level, bone)
        mount_flange(B, arm)
        return
    pr = [arm_ring(arm, t0 + d, ARM_CL + 0.0015 + e) for d, e in ((0.0, 0.0), (0.004, 0.001), (0.010, 0.001), (0.014, 0.0))]
    B.loft("proxring", smooth_rings(pr), bone, B.band("dark"), subsurf=1)
    ring = [Vector(q) for q in arm_ring(arm, t0 + 0.008, ARM_CL + 0.0025)]
    c0 = sum(ring, Vector()) / len(ring)
    hf = max(abs((q - c0).dot(fr)) for q in ring); hd = max(abs((q - c0).dot(dn)) for q in ring)
    # eje del armazón: del centro del encaje a la montura; anillo intermedio y anillo de muñeca huecos
    rd = MOUNT_R
    cd = o + ax * (tm - 0.014)
    tmid = t0 + (tm - 0.014 - t0) * 0.55
    cm = c0 + (cd - c0) * ((tmid - t0) / (tm - 0.014 - t0))
    hf_m, hd_m = hf * 0.78, hd * 0.85
    band_ring(B, "midring", cm, ax, dn, fr, hd_m + 0.002, hf_m + 0.002, 0.007, 0.0028, bone, B.band("dark"))
    band_ring(B, "distring", cd, ax, dn, fr, rd + 0.0015, rd + 0.0015, 0.010, 0.003, bone, B.band("dark"))
    def bar(name, p, q, wdt=0.0044, th=0.0027):
        p, q = Vector(p), Vector(q); w = norm(q - p)
        u = norm(w.cross(dn)) if abs(w.dot(dn)) < 0.9 else fr; v = w.cross(u)
        B.box(name, tuple((p + q) / 2), (th, wdt, (q - p).length / 2 + 0.0015), (tuple(u), tuple(v), tuple(w)), bone, B.band("shell"), bevel=0.0008)
    # pletinas acodadas delante y detrás: casi paralelas hasta el anillo intermedio y convergen hacia la muñeca
    for k, sg in enumerate((1, -1)):
        p = c0 + fr * sg * (hf + 0.0015); q = cm + fr * sg * (hf_m + 0.0045); r = cd + fr * sg * (rd + 0.0045)
        bar("strut%da" % k, p, q); bar("strut%db" % k, q, r)
        for j, pp in enumerate((p, q, r)):
            B.cyl("strutpin%d%d" % (k, j), tuple(Vector(pp) + fr * sg * 0.0016), tuple(Vector(pp) + fr * sg * 0.0046), 0.0026, 0.0026, bone, B.band("dark"), segs=10, ref=tuple(ax))
    # arriostrado en X por el dorso (-dn), entre encaje y anillo intermedio
    for k, sg in enumerate((1, -1)):
        p = c0 + ax * 0.008 + fr * sg * hf * 0.62 - dn * (hd * 0.72); q = cm - fr * sg * hf_m * 0.7 - dn * (hd_m * 0.85)
        bar("brace%d" % k, p, q, wdt=0.0022, th=0.0014)
    # pistón hidráulico por la palma (+dn)
    pa = c0 + dn * (hd + 0.003); pb = cd + dn * (rd + 0.004)
    mid = pa + (pb - pa) * 0.55
    B.cyl("pistonbody", tuple(pa), tuple(mid), 0.0062, 0.0062, bone, B.band("dark"), segs=14, bevel=0.0008, ref=tuple(ax))
    B.cyl("pistoncap", tuple(mid - (pb - pa) * 0.04), tuple(mid + (pb - pa) * 0.02), 0.0068, 0.0068, bone, B.band("shell"), segs=14, ref=tuple(ax))
    B.cyl("pistonrod", tuple(mid), tuple(pb), 0.0029, 0.0029, bone, B.band("shell"), segs=10, ref=tuple(ax))
    for j, pp in enumerate((pa, pb)):
        B.cyl("pistoneye%d" % j, tuple(Vector(pp) - fr * 0.0045), tuple(Vector(pp) + fr * 0.0045), 0.0042, 0.0042, bone, B.band("dark"), segs=12, ref=tuple(ax))
    # motor de giro de muñeca por el dorso, sobre el anillo de muñeca
    mc = cd - dn * (rd + 0.006) - ax * 0.004
    B.box("wristmotor", tuple(mc), (0.0055, 0.010, 0.0085), (tuple(dn), tuple(fr), tuple(ax)), bone, B.band("dark"), bevel=0.0015)
    B.cyl("motorcap", tuple(mc - dn * 0.0055), tuple(mc - dn * 0.0075), 0.0055, 0.0055, bone, B.band("shell"), segs=14, ref=tuple(ax))
    # cables: del anillo proximal a la montura, por los lados del dorso
    for k, sg in enumerate((1, -1)):
        a0 = c0 - dn * hd * 0.45 + fr * sg * (hf + 0.002)
        a3 = m - ax * 0.004 - dn * rd * 0.45 + fr * sg * (rd + 0.002)
        a1 = a0 + (a3 - a0) * 0.33 + fr * sg * 0.004 - dn * 0.005
        a2 = a0 + (a3 - a0) * 0.66 + fr * sg * 0.004 - dn * 0.004
        B.curve("cable%d" % k, [tuple(a0), tuple(a1), tuple(a2), tuple(a3)], [0.0016] * 4, bone, B.band("socket"), res=2)
    mount_flange(B, arm)

def taper_to_mount(B, arm, t_end, end_cl, band, name="taper"):
    """Transición de la sección del armazón en t_end a la sección redonda de la montura."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    m = mount_point(arm)
    end = [Vector(q) for q in arm_ring(arm, t_end, end_cl)]
    c = sum(end, Vector()) / len(end); n = len(end)
    rings = []
    for f in (0.0, 0.35, 0.7, 1.0):
        cc = c * (1 - f) + (m - ax * 0.005) * f
        ring = []
        for i in range(n):
            th = math.atan2((end[i] - c).dot(fr), (end[i] - c).dot(dn))
            rnd = cc + (dn * math.cos(th) + fr * math.sin(th)) * (MOUNT_R - 0.001)
            ring.append(tuple((end[i] - c + cc) * (1 - f) + rnd * f))
        rings.append(ring)
    B.loft(name, rings, bone, band, subsurf=1)

def build_wood_base(B, arm, level):
    """Base de madera (antes brazo de madera): encaje de cuero, correas, carcasa de madera hasta la montura."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    t0 = socket_only(B, arm, level, B.band("socket"), B.band("socket"))
    arm_straps(B, arm, (0.09, 0.128) if level == "Wrist" else ((0.005, 0.038) if level == "" else ()), ARM_CL, bone)
    if level != "Wrist":
        ts = [t0, t0 + 0.02, 0.07, 0.095, 0.115]
        B.loft("shell", smooth_rings([arm_ring(arm, t, ARM_SHELL) for t in ts]), bone, B.band("wood"), subsurf=1)
        taper_to_mount(B, arm, 0.115, ARM_SHELL, B.band("wood"))
    mount_flange(B, arm, "rubber")

def build_scrap_base(B, arm, level):
    """Base de chatarra (gancho, motosierra, bayoneta): el brazal / carcasa de acero de los brazos-arma hasta la montura."""
    t_end, end_cl = bracer_section(B, arm, level)
    taper_to_mount(B, arm, t_end, end_cl, B.band("steel"))
    mount_flange(B, arm, "dark")

def build_med_base(B, arm, level):
    """Base médica: encaje y carcasa lisa de polímero hasta la montura."""
    t0 = socket_only(B, arm, level, B.band("socket"), B.band("dark"))
    if level != "Wrist":
        ts = [t0, t0 + 0.02, 0.07, 0.095, 0.115]
        B.loft("shell", smooth_rings([arm_ring(arm, t, ARM_SHELL) for t in ts]), arm["bones"]["forearm"], B.band("dark"), subsurf=1)
        taper_to_mount(B, arm, 0.115, ARM_SHELL, B.band("dark"))
    mount_flange(B, arm, "shell")

def head_knob(B, arm):
    """Pomo de madera torneada (antes brazo de madera)."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    s = mount_point(arm)
    B.cyl("rod", tuple(s), tuple(s + ax * 0.02), 0.014, 0.012, bone, B.band("wood"), segs=14, subsurf=1)
    e = s + ax * 0.02
    rings = []
    for d, r in ((0.0, 0.012), (0.012, 0.024), (0.03, 0.027), (0.05, 0.024), (0.062, 0.015), (0.068, 0.009)):
        c = e + ax * d
        rings.append([tuple(c + dn * (r * math.cos(2 * math.pi * k / 16)) + fr * (r * 0.85 * math.sin(2 * math.pi * k / 16))) for k in range(16)])
    B.loft("knob", rings, bone, B.band("wood"), subsurf=1)

def head_hook(B, arm):
    """Gancho de dos puntas (curvado hacia la palma), sobre la montura."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    s = mount_point(arm)
    B.cyl("wrist", tuple(s), tuple(s + ax * 0.012), 0.015, 0.0125, bone, B.band("dark"), segs=16, bevel=0.003)
    sh = s + ax * 0.012
    B.cyl("shaft", tuple(sh), tuple(sh + ax * 0.03), 0.0085, 0.008, bone, B.band("steel"), segs=12)
    base = sh + ax * 0.03
    B.cyl("band", tuple(base - ax * 0.005), tuple(base + ax * 0.005), 0.0125, 0.0125, bone, B.band("rubber"), segs=14, bevel=0.003)
    R = 0.031
    for i, off in enumerate((-0.0075, 0.0075)):
        c = base + dn * R + fr * off
        pts, rr = [], []
        for k in range(9):
            th = math.radians(165.0) * k / 8
            pts.append(tuple(c + ax * (R * math.sin(th)) - dn * (R * math.cos(th))))
            rr.append(0.0058 - 0.0028 * k / 8)
        B.curve("prong%d" % i, pts, rr, bone, B.band("polished"), res=3)
        B.sphere("prongtip%d" % i, pts[-1], rr[-1], bone, B.band("polished"), segs=8)

def head_bayonet(B, arm):
    """Bayoneta estilo Merle sobre la montura: virola con cinta, guarda y hoja en línea con el antebrazo."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    f0 = mount_point(arm) + ax * 0.002
    B.cyl("ferrule", tuple(f0), tuple(f0 + ax * 0.026), 0.0115, 0.0085, bone, B.band("steel"), segs=14, bevel=0.0012, ref=tuple(dn))
    g = f0 + ax * 0.027
    B.box("guard", tuple(g), (0.0035, 0.020, 0.0072), (tuple(ax), tuple(dn), tuple(fr)), bone, B.band("dark"), bevel=0.0012)
    rings = []
    for k, (d, r) in enumerate(((0.002, 0.0122), (0.007, 0.0125), (0.012, 0.0119), (0.017, 0.0112))):
        cc = f0 + ax * d; j = 0.0005 * math.sin(k * 2.3)
        rings.append([tuple(cc + dn * ((r + j) * math.cos(2 * math.pi * i / 16)) + fr * ((r - j) * math.sin(2 * math.pi * i / 16))) for i in range(16)])
    B.loft("wrap0", rings, bone, B.band("rubber"), subsurf=1)
    L, n, rings = 0.15, 16, []
    for k in range(n + 1):
        u = k / n
        we = 0.0125 * (1.0 if u < 0.6 else max(0.03, 1 - ((u - 0.6) / 0.4) ** 1.5))
        ws = 0.0072 * (1.0 if u < 0.7 else max(0.03, 1 - ((u - 0.7) / 0.3) ** 0.8))
        th = max(0.0004, 0.0023 * (1 - 0.65 * u))
        cc = g + ax * (0.0035 + L * u)
        pts = [(-ws, th), (we * 0.3, th), (we, 0.0), (we * 0.3, -th), (-ws, -th), (-ws - th * 0.6, 0.0)]
        rings.append([tuple(cc + dn * a + fr * b) for a, b in pts])
    B.loft("blade", rings, bone, B.band("polished"), subsurf=0, smooth=False)

def head_chainsaw(B, arm, saw):
    """Motosierra estilo Ash sobre la montura: abrazadera, vástago, pletinas, piñón, placa y la motosierra vanilla."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    c_end = mount_point(arm)
    e_dn = e_fr = MOUNT_R + 0.003
    side = -dn
    def hexbolt(name, p, axis, r=0.0042, hgt=0.003):
        axis = norm(Vector(axis))
        B.cyl(name, tuple(p), tuple(p + axis * hgt), r, r, bone, B.band("polished"), segs=6, bevel=0.0007, ref=tuple(ax if abs(axis.dot(ax)) < 0.9 else fr))
    ho, hn = saw["body_half"]
    L = 0.052
    B.cyl("collar", tuple(c_end - ax * 0.004), tuple(c_end + ax * 0.012), (e_dn, e_fr), (e_dn, e_fr), bone, B.band("dark"), segs=20, bevel=0.0018, ref=tuple(dn))
    lug_c = c_end + ax * 0.004 + fr * (e_fr + 0.005)
    for k, sg in enumerate((-1, 1)):
        B.box("lug%d" % k, lug_c + dn * (sg * 0.0048), (0.0065, 0.0016, 0.0062), (tuple(ax), tuple(dn), tuple(fr)), bone, B.band("dark"), bevel=0.0008)
    B.cyl("clampbolt", tuple(lug_c - dn * 0.011), tuple(lug_c + dn * 0.011), 0.0022, 0.0022, bone, B.band("polished"), segs=8, ref=tuple(ax))
    hexbolt("nut0", lug_c + dn * 0.0064, dn, 0.0040, 0.0032); hexbolt("nut1", lug_c - dn * 0.0064, -dn, 0.0040, 0.0032)
    def rr(center, a_, b_, e=4.0, n=24):
        pts = []
        for k in range(n):
            th = 2 * math.pi * k / n; c_, s_ = math.cos(th), math.sin(th)
            r = 1.0 / ((abs(c_) ** e + abs(s_) ** e) ** (1.0 / e))
            pts.append(tuple(center + dn * (a_ * r * c_) + fr * (b_ * r * s_)))
        return pts
    P_top, P_bot = c_end + ax * (L - 0.009), c_end + ax * L
    B.loft("plate", [rr(P_top, ho * 0.96, hn * 0.96), rr(P_bot, ho * 0.96, hn * 0.96)], bone, B.band("dark"), subsurf=0, bevel=0.0025)
    B.cyl("stem", tuple(c_end + ax * 0.011), tuple(P_top + ax * 0.001), 0.0125, 0.0155, bone, B.band("steel"), segs=16, bevel=0.0015, ref=tuple(dn))
    B.cyl("stemring", tuple(P_top - ax * 0.008), tuple(P_top), 0.0185, 0.021, bone, B.band("dark"), segs=16, bevel=0.0015, ref=tuple(dn))
    for k, sg in enumerate((1, -1)):
        A = c_end + ax * 0.003 + dn * sg * (e_dn + 0.0032)
        Bp = P_top + dn * sg * (ho * 0.78)
        w = norm(Bp - A); u = fr; v = norm(w.cross(u))
        if v.dot(dn * sg) < 0: v = -v
        B.box("bar%d" % k, (A + Bp) / 2, (0.0115, 0.0026, (Bp - A).length / 2 + 0.003), (tuple(u), tuple(v), tuple(w)), bone, B.band("steel"), bevel=0.0012)
        hexbolt("hexA%d" % k, A + v * 0.0024, v); hexbolt("hexB%d" % k, Bp + v * 0.0024 - w * 0.004, v)
        if sg < 0:
            gc = (A + Bp) / 2 + v * 0.0026
            B.cyl("gear", tuple(gc), tuple(gc + v * 0.0045), 0.0125, 0.0125, bone, B.band("dark"), segs=12, ref=tuple(w))
            for j in range(10):
                an = 2 * math.pi * j / 10; rd_ = w * math.cos(an) + u * math.sin(an)
                B.box("tooth%d" % j, gc + v * 0.00225 + rd_ * 0.0145, (0.0026, 0.002, 0.00225), (tuple(rd_), tuple(v.cross(rd_)), tuple(v)), bone, B.band("dark"))
            B.sphere("hub", tuple(gc + v * 0.005), 0.0042, bone, B.band("polished"), segs=8)
    h = norm(side * 0.45 + fr * 0.9)
    p_plate = P_top + h * (max(ho, hn) * 0.92) - ax * 0.002
    B.curve("hose", [tuple(c_end + h * (e_fr + 0.004)), tuple(c_end + ax * (L * 0.45) + h * (max(e_dn, e_fr) + 0.012)), tuple(p_plate)], [0.0042] * 3, bone, B.band("rubber"), res=3)
    sb, so, sn, base = Vector(saw["b"]), Vector(saw["o"]), Vector(saw["n"]), Vector(saw["base"])
    det_l = sb.dot(so.cross(sn)); det_w = ax.dot(dn.cross(fr))
    fr_s = fr if (det_l > 0) == (det_w > 0) else -fr
    S0 = P_bot - ax * 0.012
    def place(p):
        d = Vector(p) - base
        return S0 + ax * d.dot(sb) + dn * d.dot(so) + fr_s * d.dot(sn)
    def turn(nv):
        nv = Vector(nv)
        return norm(ax * nv.dot(sb) + dn * nv.dot(so) + fr_s * nv.dot(sn))
    B.raw.append({"verts": [tuple(place(p)) for p in saw["verts"]], "normals": [tuple(turn(n)) for n in saw["normals"]],
                  "uvs": saw["uvs"], "faces": saw["faces"], "bone": bone, "name": "saw"})

# ---- 3.3 gama CYBER (pedida 2026-10-17 con referencias: brazos de placas blindadas facetadas en dos tonos, con
# músculos de cable a la vista entre placas y dedos articulados por segmentos). Atlas propio cyberArm.png (BANDS["cyber"]).
def ring_radius_fn(arm, t, clearance):
    """Sección lisa para el blindaje: la elipse que envuelve la sección del brazo en t (ejes dn/fr) más la holgura. La
    piel de debajo está oculta, así que las placas no copian los bultos del brazo (con los anillos crudos se arrugaban)."""
    o, ax, dn, fr = arm_frame(arm)
    pts = [Vector(q) for q in arm_ring(arm, t, 0.0)]
    c = sum(pts, Vector()) / len(pts)
    a = max(abs((q - c).dot(dn)) for q in pts) * 1.03 + clearance
    b = max(abs((q - c).dot(fr)) for q in pts) * 1.03 + clearance
    def R(th): return 1.0 / math.sqrt((math.cos(th) / a) ** 2 + (math.sin(th) / b) ** 2)
    return c, R

def ellipse_ring(arm, t, clearance, n=24):
    o, ax, dn, fr = arm_frame(arm)
    c, R = ring_radius_fn(arm, t, clearance)
    return [tuple(c + (dn * math.cos(th) + fr * math.sin(th)) * R(th)) for th in (2 * math.pi * k / n for k in range(n))]

def armor_panel(B, arm, name, ts, a0, a1, clearance, thick, band, facets=3, bone=None):
    """Placa blindada facetada: cubre del ángulo a0 al a1 (radianes, desde +dn hacia +fr) entre los t de ts."""
    o, ax, dn, fr = arm_frame(arm); bone = bone or arm["bones"]["forearm"]
    verts, faces = [], []
    nA = facets + 1
    for t in ts:
        c, R = ring_radius_fn(arm, t, clearance)
        for k in range(nA):
            th = a0 + (a1 - a0) * k / facets
            d = dn * math.cos(th) + fr * math.sin(th)
            r = R(th)
            verts.append(tuple(c + d * r)); verts.append(tuple(c + d * (r - thick)))
    rowlen = nA * 2
    for i in range(len(ts) - 1):
        for k in range(facets):
            o0 = i * rowlen + k * 2; o1 = o0 + 2; n0 = o0 + rowlen; n1 = o1 + rowlen
            faces.append((o0, o1, n1, n0)); faces.append((o0 + 1, n0 + 1, n1 + 1, o1 + 1))
        a = i * rowlen; b = a + rowlen
        faces.append((a, b, b + 1, a + 1)); e = a + facets * 2; f = e + rowlen
        faces.append((e, e + 1, f + 1, f))
    last = (len(ts) - 1) * rowlen
    for k in range(facets):
        p = k * 2; faces.append((p, p + 1, p + 3, p + 2))
        q = last + k * 2; faces.append((q, q + 2, q + 3, q + 1))
    return B.mesh(name, verts, faces, bone, band, (Vector(verts[0]), Vector(verts[-1])), bevel=0.0006, smooth=False)

CYBER_PANELS = [(-0.62, 0.62), (0.80, 2.05), (2.35, 3.93), (4.23, 5.48)]   # dorso, lados y palma, con huecos entre placas

def cyber_plating(B, arm, t0, t1, clearance, rows=2, accent=True):
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    # (2026-10-17: "de lejos parece mesa de ajedrez") antes dos filas alternando blanco y grafito; ahora franjas a lo
    # largo: dorso y palma en blanco, laterales en grafito, una placa larga y un anillo de placas más corto superpuesto
    # junto a la muñeca (mismo color por columna, así no sale el tablero)
    tr = t1 - (t1 - t0) * 0.28
    for k, (p0, p1) in enumerate(CYBER_PANELS):
        band = B.band("plate" if k % 2 == 0 else "plate2")
        armor_panel(B, arm, "plate0%d" % k, [t0, (t0 + tr) / 2, tr + 0.004], p0 + math.pi, p1 + math.pi, clearance, 0.003, band, facets=4)
        armor_panel(B, arm, "plate1%d" % k, [tr, (tr + t1) / 2, t1], p0 + math.pi - 0.06, p1 + math.pi + 0.06, clearance + 0.0022, 0.003, band, facets=4)
    if accent:
        tc = t0 + (tr - t0) * 0.5
        c, R = ring_radius_fn(arm, tc, clearance)
        d = -dn
        p = c + d * (R(math.pi) + 0.0009)
        B.box("accent", tuple(p), (0.0007, 0.0032, (t1 - t0) * 0.12), (tuple(d), tuple(fr), tuple(ax)), bone, B.band("accent"), bevel=0.0003)
    # núcleo oscuro (tapa lo que hay detrás: la piel de debajo está oculta) y músculos de cable entre las placas
    core = [ellipse_ring(arm, t, clearance - 0.006) for t in (t0 - 0.004, (t0 + t1) / 2, t1 + 0.004)]
    B.loft("core", core, bone, B.band("dark"), subsurf=0)
    for k, (p0, p1) in enumerate(CYBER_PANELS):
        g0 = p1 + math.pi; g1 = CYBER_PANELS[(k + 1) % len(CYBER_PANELS)][0] + math.pi + (2 * math.pi if k == len(CYBER_PANELS) - 1 else 0)
        for j, f in enumerate((0.3, 0.7)):
            th = g0 + (g1 - g0) * f
            pts = []
            for t, sink in ((t0 + 0.003, 0.0045), (t0 + (t1 - t0) * 0.33, 0.0026), (t0 + (t1 - t0) * 0.66, 0.0026), (t1 - 0.003, 0.0045)):
                c, R = ring_radius_fn(arm, t, clearance)
                dd = dn * math.cos(th) + fr * math.sin(th)
                pts.append(tuple(c + dd * (R(th) - sink)))
            B.curve("muscle%d%d" % (k, j), pts, [0.0018, 0.0025, 0.0025, 0.0018], bone, B.band("cable"), res=2)

def build_cyber_base(B, arm, level):
    """Base cyber: encaje de carbono, placas blindadas facetadas en dos filas con músculos de cable entre ellas, la
    transición a la montura y una brida con anillo de acento."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    t0 = socket_only(B, arm, level, B.band("socket"), B.band("dark"))
    if level == "Wrist":
        cyber_plating(B, arm, 0.078, 0.14, ARM_CL + 0.0055, rows=2)
    else:
        start = t0 + 0.006
        B.loft("proxring", smooth_rings([arm_ring(arm, t0 + d, ARM_CL + e) for d, e in ((-0.003, 0.001), (0.001, 0.0015), (0.004, 0.001), (0.0055, -0.002))]),
               bone, B.band("dark"), subsurf=1)
        cyber_plating(B, arm, start, 0.118, ARM_SHELL + 0.0075, rows=2)
        taper_to_mount(B, arm, 0.118, ARM_SHELL + 0.004, B.band("dark"))
    m = mount_flange(B, arm, "dark")
    B.cyl("mountaccent", tuple(m - ax * 0.008), tuple(m - ax * 0.006), MOUNT_R + 0.0012, MOUNT_R + 0.0012, bone, B.band("accent"), segs=20, ref=tuple(dn))

def head_cyber_hand(B, arm):
    """Mano cyber: palma de placas (pasa de la montura al hueso de la mano), placa en el dorso, dedos de tres segmentos
    con articulaciones oscuras y puntas de acento, pulgar de dos segmentos. Se cierra al agarrar como las otras."""
    o, ax, dn, fr = arm_frame(arm)
    hb, f0b, f1b, fab = arm["bones"]["hand"], arm["bones"]["finger0"], arm["bones"]["finger1"], arm["bones"]["forearm"]
    J = arm["joints"]
    P0, P1, a1 = Vector(J["finger0"]), Vector(J["finger1"]), norm(Vector(J["finger1_axis"]))
    if a1.dot(fr) < 0: a1 = -a1
    q = mount_point(arm) + ax * WRIST_OFF
    B.sphere("wristball", tuple(q), WRIST_BALL * 0.95, fab, B.band("dark"), segs=24)
    B.cyl("wristaccent", tuple(q - ax * 0.002), tuple(q + ax * 0.002), WRIST_BALL * 1.02, WRIST_BALL * 1.02, fab, B.band("accent"), segs=16, ref=tuple(dn))
    Lp = (P1 - q).dot(ax); dK = (P1 - q).dot(dn)
    def rr(c, hw, ht, n=12):
        return [tuple(c + fr * (hw * math.cos(2 * math.pi * k / n)) + dn * (ht * math.sin(2 * math.pi * k / n))) for k in range(n)]
    hs_w, hs_t, hs_l = hand_scale(arm)
    prof = [(u, w * hs_w, t * hs_t ** 2) for u, w, t in ((0.0, 0.0135, 0.0105), (0.3, 0.025, 0.0138), (0.65, 0.031, 0.0135), (1.0, 0.030, 0.0115))]   # base dentro de la rótula
    palm = B.loft("palm", [rr(q + ax * (u * Lp) + dn * (dK * u * u), hw * 1.08, ht * 1.2) for u, hw, ht in prof], hb, B.band("plate"), subsurf=0, smooth=False)
    # palma entera al hueso de la mano: con pocos anillos (sin subdivisión) la mezcla dejaba el primero en el antebrazo y
    # al doblar la muñeca el tramo se estiraba en dientes. El anillo de la palma tapa el cruce con la rótula.
    B.cyl("palmcap", tuple(q - ax * 0.001), tuple(q + ax * 0.008), (0.0200, 0.0170), (0.0205, 0.0175), hb, B.band("dark"), segs=20, bevel=0.0006, ref=tuple(fr))
    # placa curva del dorso (-dn), pegada a la palma: arco de 130 grados de la sección, de u=0.32 a u=0.9
    def prof_at(u):
        for (u0, w0, h0), (u1, w1, h1) in zip(prof, prof[1:]):
            if u0 <= u <= u1:
                f = (u - u0) / (u1 - u0); return w0 + (w1 - w0) * f, h0 + (h1 - h0) * f
        return prof[-1][1], prof[-1][2]
    # (2026-10-17: "la placa de la mano se ve rara y muy plana") tres escamas que se solapan como en las referencias:
    # cada una con cresta central facetada, el borde distal levantado y montada un poco sobre la anterior
    def scale_plate(name, u0, u1, lift, band, span=62, nA=9):
        verts, faces, us = [], [], (u0, (u0 + u1) / 2, u1)
        for iu, u in enumerate(us):
            hw, ht = prof_at(u); c = q + ax * (u * Lp) + dn * (dK * u * u)
            rise = lift + 0.0012 * iu                                         # borde distal levantado
            for k in range(nA):
                f = k / (nA - 1); th = math.radians(-span + 2 * span * f)
                d2 = -dn * math.cos(th) * ht * 1.2 + fr * math.sin(th) * hw * 1.08
                ridge = 0.0022 * (1 - abs(2 * f - 1)) ** 1.5                  # cresta en el centro, en punta
                out = c + d2 + norm(d2) * (0.0012 + rise + ridge)
                verts.append(tuple(out)); verts.append(tuple(out - norm(d2) * 0.0024))
        rl = nA * 2
        for i in range(len(us) - 1):
            for k in range(nA - 1):
                o0 = i * rl + k * 2; o1 = o0 + 2; n0 = o0 + rl; n1 = o1 + rl
                faces += [(o0, o1, n1, n0), (o0 + 1, n0 + 1, n1 + 1, o1 + 1)]
            a_ = i * rl; b_ = a_ + rl; e = a_ + (nA - 1) * 2; f_ = e + rl
            faces += [(a_, b_, b_ + 1, a_ + 1), (e, e + 1, f_ + 1, f_)]
        last = (len(us) - 1) * rl
        for k in range(nA - 1):
            p_ = k * 2; faces.append((p_, p_ + 1, p_ + 3, p_ + 2)); q_ = last + k * 2; faces.append((q_, q_ + 2, q_ + 3, q_ + 1))
        B.mesh(name, verts, faces, hb, band, (Vector(verts[0]), Vector(verts[-1])), bevel=0.0005, smooth=False)
    scale_plate("backplate0", 0.22, 0.48, 0.0000, B.band("plate2"), span=48)
    scale_plate("backplate1", 0.44, 0.70, 0.0010, B.band("plate2"), span=51)
    scale_plate("backplate2", 0.66, 0.92, 0.0020, B.band("plate"), span=54)
    H0 = P1 + a1 * ((q - P1).dot(fr) / a1.dot(fr))
    AL, PHI = math.radians(float(os.environ.get('TOC_AL', 7))), math.radians(float(os.environ.get('TOC_PHI', 24)))
    for i, (off, ln) in enumerate(((-0.021, 0.037), (-0.007, 0.045), (0.007, 0.048), (0.021, 0.044))):
        K = H0 + a1 * (off * 1.08 * hs_w / a1.dot(fr))
        ln = ln * hs_l * FINGER_LEN
        pts, p = [K], Vector(K)
        for j in range(1, 4):
            th = AL + PHI * ((j - 0.5) / 3) ** 1.3
            p = p + (ax * math.cos(th) + dn * math.sin(th)) * (ln / 3); pts.append(p)
        B.sphere("knuckle%d" % i, tuple(K), 0.0062, hb, B.band("accent"), segs=10)
        for j in range(3):
            a_, b_ = pts[j], pts[j + 1]
            w = norm(b_ - a_); u = norm(w.cross(dn)) if abs(w.dot(dn)) < 0.9 else fr; v = w.cross(u)
            r = (0.0053 - 0.0006 * j) * (hs_w + hs_t) / 2
            B.box("seg%d%d" % (i, j), tuple((a_ + b_) / 2), (r, r * 0.92, (b_ - a_).length / 2 - 0.0012), (tuple(u), tuple(v), tuple(w)),
                  f1b, B.band("plate2" if j == 2 else "plate"), bevel=0.0012)
            if j < 2: B.sphere("joint%d%d" % (i, j), tuple(b_), r * 0.85, f1b, B.band("dark"), segs=8)
    tpts = [P0, P0 + fr * 0.011 + ax * 0.010 + dn * 0.005, P0 + fr * 0.0145 + ax * 0.021 + dn * 0.012, P0 + fr * 0.0135 + ax * 0.029 + dn * 0.018]
    B.sphere("thumbball", tuple(P0), 0.0078, hb, B.band("accent"), segs=10)
    for j in range(3):
        a_, b_ = tpts[j], tpts[j + 1]
        w = norm(b_ - a_); u = norm(w.cross(dn)) if abs(w.dot(dn)) < 0.9 else fr; v = w.cross(u)
        r = (0.0064 - 0.0008 * j) * (hs_w + hs_t) / 2
        B.box("thumbseg%d" % j, tuple((a_ + b_) / 2), (r, r * 0.92, (b_ - a_).length / 2 - 0.0012), (tuple(u), tuple(v), tuple(w)),
              f0b, B.band("plate2" if j == 2 else "plate"), bevel=0.0012)
        if j < 2: B.sphere("thumbjoint%d" % j, tuple(b_), r * 0.85, f0b, B.band("dark"), segs=8)

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
                UV.append([round(x, 4) for x in uv_of(verts[vi], proj[vi])])
                if "pz_blend" in ob:
                    # 3.3: peso repartido entre dos huesos a lo largo de un eje (la palma de los cabezales: unida a la
                    # montura en su base y del hueso de la mano hacia los nudillos, como la piel vanilla en la muñeca)
                    bl_ = list(ob["pz_blend"]); b0, b1 = ob["pz_blend_b0"], ob["pz_blend_b1"]
                    org, axb, t0, t1 = Vector(bl_[0:3]), Vector(bl_[3:6]), bl_[6], bl_[7]
                    u = max(0.0, min(1.0, ((verts[vi] - org).dot(axb) - t0) / max(1e-6, t1 - t0)))
                    w = u * u * (3 - 2 * u)
                    W.append([[b0, round(1 - w, 4)], [b1, round(w, 4)]] if 0.001 < w < 0.999 else (b1 if w >= 0.999 else b0))
                else:
                    W.append(bone)
        for fi, f in enumerate(faces):
            F.append([remap[(f[0], fi)], remap[(f[1], fi)], remap[(f[2], fi)]])
        bm.free(); ev.to_mesh_clear()
    for r in B.raw:
        base = len(V)
        V += [[round(x, 5) for x in v] for v in r["verts"]]; N += [[round(x, 4) for x in n] for n in r["normals"]]
        UV += [[round(x, 5) for x in t] for t in r["uvs"]]; W += [r["bone"]] * len(r["verts"])
        F += [[base + i for i in f] for f in r["faces"]]
    json.dump({"verts": V, "normals": N, "uvs": UV, "faces": F, "bones": W}, open(path, "w"))
    return len(V), len(F)

# ------------------------------------------------------------------ catálogo
LEG_TIERS = {"pegLeg": ("peg", lambda B, legs, lv: build_peg_leg(B, legs, lv)),
             "mechLeg": ("metal", lambda B, legs, lv: build_mech_leg(B, legs, lv, False)),
             "medicalLeg": ("metal", lambda B, legs, lv: build_mech_leg(B, legs, lv, True)),
             "cyberLeg": ("cyber", lambda B, legs, lv: build_cyber_leg(B, legs, lv))}
ARM_TIERS = {"pegArm": ("peg", lambda B, arm, lv: build_peg_arm(B, arm, lv)),
             "hookArm": ("hook", lambda B, arm, lv: build_hook_arm(B, arm, lv)),
             "normalArm": ("metal", lambda B, arm, lv: build_mech_arm(B, arm, lv, False)),
             "medicalArm": ("metal", lambda B, arm, lv: build_mech_arm(B, arm, lv, True))}
# sólo brazo derecho: las animaciones de motosierra del juego son diestras (Bip01_Prop1 = mano derecha)
SAW_TIERS = {"chainsawArm": ("saw", lambda B, arm, lv, saw: build_saw_arm(B, arm, lv, saw))}
# brazo bayoneta (estilo Merle, 3.2.0): sólo derecho, como la motosierra; atlas del gancho (cuero, correa, acero, pulido)
KNIFE_TIERS = {"knifeArm": ("hook", lambda B, arm, lv: build_knife_arm(B, arm, lv))}

LEG_UNDER = ("foot", "sole", "pylon", "ferrule", "peg_")      # peg_pole / peg_ring: lo que asoma bajo el pantalón
ARM_UNDER = ("wrist", "shaft", "band", "prong", "wristunit", "palm", "finger", "tip", "knuckle", "joint", "thumb", "rod", "knob", "axle",
             "cup", "collar", "lug", "clampbolt", "nut", "plate", "stem", "bar", "hex", "gear", "tooth", "hub",
             "endcap", "caprivet", "ferrule", "guard", "blade", "wrap")
report = []
col_x = 0.0

# ---- 3.3 modular: catálogo de bases (por nivel) y cabezales (uno por lado y sexo, empiezan en la montura)
def head_hand(B, arm, medical):
    o, ax, dn, fr = arm_frame(arm)
    q = mount_point(arm) + ax * WRIST_OFF
    B.sphere("wristball", tuple(q), WRIST_BALL, arm["bones"]["forearm"], B.band("dark"), segs=16)
    if medical: hand(B, q, arm, B.band("dark"), True, blend=True)
    else: hand(B, q, arm, B.band("shell"), False, joint_band=B.band("dark"), blend=True)

MOD_BASES = {"baseWood": ("peg", build_wood_base), "baseScrap": ("hook", build_scrap_base),
             "baseMech": ("metal", build_mech_frame), "baseMed": ("metal", build_med_base), "baseCyber": ("cyber", build_cyber_base)}
MOD_HEADS = {"headKnob": ("peg", head_knob), "headHook": ("hook", head_hook),
             "headMechHand": ("metal", lambda B, arm: head_hand(B, arm, False)),
             "headMedHand": ("metal", lambda B, arm: head_hand(B, arm, True)),
             "headChainsaw": ("saw", lambda B, arm: head_chainsaw(B, arm, fit["saw"])), "headBayonet": ("hook", head_bayonet),
             "headCyberHand": ("cyber", head_cyber_hand)}
MOD_ONE_SIDE = {"headChainsaw": "R", "headBayonet": "R"}     # el juego ataca con la mano principal
BASE_UNDER = ("mountflange", "mountbolt")

if MODULAR:
    for sex, body in fit["bodies"].items():
        sx = "M" if sex == "Male" else "F"
        for side in ("L", "R"):
            arm = body["arms"][side]
            jobs = [(n, lv, tex, fn) for n, (tex, fn) in MOD_BASES.items() for lv in fit["arm_levels"]]
            jobs += [(n, None, tex, fn) for n, (tex, fn) in MOD_HEADS.items() if MOD_ONE_SIDE.get(n, side) == side]
            for tier, lv, tex, fn in jobs:
                name = "%s%s_%s_%s" % (tier, lv or "", side, sx)
                if FILTER and FILTER not in name: continue
                B = Builder(name, tex)
                ARM_LEVEL = lv or ""
                if lv is None: fn(B, arm)
                else:
                    fn(B, arm, lv)
                    if lv == "Upper": build_upper_section(B, arm)
                nv, nf = export_builder(B, os.path.join(OUTDIR, name + ".json"))
                if lv is not None:                         # bajo la manga sólo asoma la brida de la montura
                    full = B.parts
                    B.parts = [ob for ob in full if ob.name.split(".", 1)[1].startswith(BASE_UNDER)]
                    if B.parts: export_builder(B, os.path.join(OUTDIR, "%s%sUnder_%s_%s.json" % (tier, lv, side, sx)))
                    B.parts = full
                for ob in list(B.parts): bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.collections.remove(B.coll)
                report.append((name, nv, nf)); print("built", name, nv, "verts", nf, "tris")
    print("DONE", len(report), "models")
    raise SystemExit(0)

for sex, body in fit["bodies"].items():
    sx = "M" if sex == "Male" else "F"
    for side in ("L", "R"):
        jobs = []
        for tier, (tex, fn) in LEG_TIERS.items():
            for lv in fit["leg_levels"]: jobs.append((tier, lv, tex, fn, body["legs"][side]))
        for tier, (tex, fn) in ARM_TIERS.items():
            for lv in fit["arm_levels"]: jobs.append((tier, lv, tex, fn, body["arms"][side]))
        if side == "R":
            for tier, (tex, fn) in SAW_TIERS.items():
                for lv in fit["arm_levels"]:
                    jobs.append((tier, lv, tex, (lambda f, sw: (lambda B, arm, l: f(B, arm, l, sw)))(fn, fit["saw"]), body["arms"][side]))
            for tier, (tex, fn) in KNIFE_TIERS.items():
                for lv in fit["arm_levels"]: jobs.append((tier, lv, tex, fn, body["arms"][side]))
        for tier, lv, tex, fn, data in jobs:
            name = "%s%s_%s_%s" % (tier, lv, side, sx)
            if FILTER and FILTER not in name: continue
            B = Builder(name, tex)
            ARM_LEVEL = lv if tier in ARM_TIERS or tier in SAW_TIERS or tier in KNIFE_TIERS else ""
            fn(B, data, lv)
            if lv == "Upper": build_upper_section(B, data)
            nv, nf = export_builder(B, os.path.join(OUTDIR, name + ".json"))
            report.append((name, nv, nf))
            # variante bajo la ropa (modelo alternativo del juego): sólo lo que asoma por el bajo del
            # pantalón (pie, pilón, contera, pata) o por el puño de la manga (dispositivo terminal)
            keep = LEG_UNDER if tier in LEG_TIERS else ARM_UNDER
            full_parts = B.parts      # B.raw (la motosierra) asoma siempre: va también en la variante bajo la ropa
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
