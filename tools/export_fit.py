"""Exporta a JSON los datos de ajuste que Blender necesita para remodelar las prótesis:
secciones reales de piernas y antebrazos del cuerpo vanilla (holgura 0, con su centro), marcos de
huesos, medidas de pie y mano, alturas de corte y huesos. Unidades y ejes del juego (Y arriba, frente -Z).
Uso: python export_fit.py [salida.json]"""
import os, sys, json, math
_ARGV = sys.argv[1:]; sys.argv = sys.argv[:1]      # build_assets / render_icons leen argv[1] como ruta del mod
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import build_assets as BA

# --tomb: ajuste para el submod "TombBody fit": los anillos se miden sobre el cuerpo de Tomb's Player Body (out/tomb/*.json de
# tomb_export.py; sólo se mide, no se copia nada suyo). Es 2-8 mm más delgado que el vanilla: con los encajes vanilla quedaba
# hueco y se veía el interior del encaje. Mano y pie siguen siendo los vanilla.
TOMB = "--tomb" in _ARGV
_pos = [a for a in _ARGV if not a.startswith("--")]
OUT = _pos[0] if _pos else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "fit_tomb.json" if TOMB else "fit.json")

from tomb_common import tomb_main_faces

def tomb_only(vb):
    """El cuerpo de Tomb como dict de cuerpo (mismo esqueleto y pose de reposo que el vanilla, comprobado en tomb_export),
    sin su membrana transparente. Sus caras llevan una UV opaca de la textura vanilla para que face_is_hidden no las descarte."""
    import json as _json
    here = os.path.dirname(os.path.abspath(__file__))
    T = _json.load(open(os.path.join(here, "out", "tomb", vb["sex"] + ".json")))["meshes"][0]
    tv = np.load(os.path.join(here, "out", "tomb", vb["sex"] + "_verts_pz.npy"))
    alpha = BA.hidden_alpha(vb["sex"])
    ys, xs = np.nonzero(alpha >= 250); opaque_uv = (xs[len(xs) // 2] / 255.0, ys[len(ys) // 2] / 255.0)
    return {"verts": tv, "faces": [tuple(int(i) for i in T["tris"][k]) for k in tomb_main_faces(T["tris"], len(tv))],
            "uvs": np.tile(opaque_uv, (len(tv), 1)), "weights": [dict(w) for w in T["weights"]], "offsets": vb["offsets"], "sex": vb["sex"]}

def ring_with_center(ring):
    R = np.array(ring)
    c = [(R[:, 0].min() + R[:, 0].max()) / 2, float(R[0, 1]), (R[:, 2].min() + R[:, 2].max()) / 2]
    return {"c": [round(float(x), 5) for x in c], "pts": [[round(float(x), 5) for x in p] for p in R]}

# ------------------------------------------------------------------ motosierra (brazo tipo Ash)
# Como la de Ash (Evil Dead 2): el motor pegado al muñón y la espada como prolongación del antebrazo. Se usa la
# malla vanilla Chainsaw.X (sin ítem en 42.21) SIN sus asas: de sus 4 piezas se quedan el cuerpo y la espada.
# Aquí sólo se mide en sus coordenadas; blender_build.py la coloca en cada brazo (rígida al antebrazo).
# Textura: atlas 128x512 = chainsaw.png x3 (sus UV llegan a v=2.12, la hoja repite) en v 0..0.75 y las bandas
# de la prótesis en v 0.75..1 (BANDS["saw"] de blender_build).
SAW_X = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media\models_X\Chainsaw.X"
SAW_TILES = 3
SAW_VSCALE = 0.75 / SAW_TILES

def chainsaw_local():
    import pzx
    from render_icons import find_mesh
    m = pzx.read_mesh(find_mesh(pzx.parse(SAW_X)))
    V = np.array(m["verts"], float); Nn = np.array(m["normals"], float); F = np.array([list(f) for f in m["faces"]], int)
    uv = np.array(m["uvs"], float)
    # piezas conexas (vértices partidos unidos por posición)
    par = list(range(len(V)))
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    pos = {}
    for i, v in enumerate(V): pos.setdefault(tuple(np.round(v, 4)), []).append(i)
    for g in pos.values():
        for i in g[1:]: par[find(i)] = find(g[0])
    for t in F: par[find(t[1])] = find(t[0]); par[find(t[2])] = find(t[0])
    comps = {}
    for fi, t in enumerate(F): comps.setdefault(find(t[0]), []).append(fi)
    parts = {}
    for fl in comps.values():
        p = V[np.unique(F[fl])]; ext = p.max(0) - p.min(0)
        if ext[1] > 0.25: parts["bar"] = fl                          # espada: la más larga en Y
        elif ext[0] < 0.03 and p[:, 1].min() < 0.0: parts["rear"] = fl  # asa trasera (fuera)
        elif len(fl) == max(len(x) for x in comps.values()): parts["loop"] = fl  # arco delantero (fuera)
        else: parts["body"] = fl
    assert set(parts) == {"bar", "rear", "loop", "body"}, parts.keys()
    keep = sorted(parts["body"] + parts["bar"])
    used = np.unique(F[keep]); remap = {int(o): i for i, o in enumerate(used)}
    Fk = [[remap[int(i)] for i in F[fi]] for fi in keep]
    # ejes de la sierra: b = espada (hacia la punta), n = normal de la espada (su eje fino), o = b x n
    pb = V[np.unique(F[parts["bar"]])]
    c = pb.mean(0); _, _, vt = np.linalg.svd(pb - c); b = vt[0] * np.sign(vt[0][1])
    n = vt[2] - b * vt[2].dot(b); n /= np.linalg.norm(n)
    o = np.cross(b, n)
    body = V[np.unique(F[parts["body"]])]; cb = body.mean(0)
    if (c - cb).dot(o) < 0: o, n = -o, -n                              # o: del cuerpo hacia la espada
    base = cb + b * ((body - cb) @ b).min()                             # base del motor, centrada
    uv = uv[used]
    uv[:, 0] = np.clip(uv[:, 0], 0.0, 1.0)
    uv[:, 1] = np.clip(uv[:, 1], 0.0, SAW_TILES) * SAW_VSCALE
    return {"verts": V[used].round(5).tolist(), "normals": Nn[used].round(4).tolist(), "uvs": uv.round(5).tolist(), "faces": Fk,
            "b": b.round(5).tolist(), "o": o.round(5).tolist(), "n": n.round(5).tolist(), "base": base.round(5).tolist(),
            "body_half": [float(((body - cb) @ o).max()), float(((body - cb) @ n).max())], "bar_offset": float((c - cb).dot(o)),
            "length": float(((V[used] - base) @ b).max())}

# ------------------------------------------------------------------ brazo superior (prótesis por encima del codo, 3.1.0)
ARM_RING_BAND = 0.007        # franja a lo largo del brazo que entra en cada anillo de ajuste (ver comentario abajo)
UPPER_STUMP_CUT = 0.155      # |x| del corte del muñón de brazo (make_arm_stumps.ARM_CUTS["UpperArm"])

def upper_arm(body, side):
    """Marco hombro -> codo y anillos reales del brazo superior cada 5 mm (t = distancia desde el hombro)."""
    so, _, _, _ = BA.bone_frame(body["offsets"], "Bip01_%s_UpperArm" % side)
    eo, _, _, _ = BA.bone_frame(body["offsets"], "Bip01_%s_Forearm" % side)
    axis = eo - so; L = float(np.linalg.norm(axis)); axis = axis / L
    down = np.array([0.0, -1.0, 0.0]); down = down - axis * (down @ axis); down = down / np.linalg.norm(down)
    front = np.cross(down, axis); front = front / np.linalg.norm(front)
    if front[2] > 0: front = -front
    bones = ["Bip01_%s_UpperArm" % side]
    rings = {}
    t = 0.0
    while t <= L + 1e-6:
        ring = BA.axis_ring(body, bones, side, so, axis, down, front, t, 0.0, band=ARM_RING_BAND)
        R = np.array(ring)
        du, dv = (R - so) @ down, (R - so) @ front
        c = so + axis * t + down * ((du.min() + du.max()) / 2) + front * ((dv.min() + dv.max()) / 2)
        rings["%.3f" % t] = {"c": [round(float(x), 5) for x in c], "pts": [[round(float(x), 5) for x in p] for p in R]}
        t += 0.005
    # t del corte del muñón a lo largo del eje (el corte es un plano |x| = UPPER_STUMP_CUT)
    t_cut = (UPPER_STUMP_CUT - abs(so[0])) / max(abs(axis[0]), 1e-6)
    return {"o": [float(x) for x in so], "axis": [float(x) for x in axis], "down": [float(x) for x in down], "front": [float(x) for x in front],
            "len": L, "t_cut": float(t_cut), "rings": rings, "bone": bones[0]}

spec = {"units": "PZ (0.57 u/m), Y arriba, frente -Z", "leg_cuts": BA.LEG_CUTS, "leg_levels": BA.LEG_LEVELS, "arm_levels": dict(BA.ARM_LEVELS, Upper="UpperArm"), "bodies": {}}
for sex in ("Male", "Female"):
    vbody = BA.load_body(sex)
    body = tomb_only(vbody) if TOMB else vbody
    V = vbody["verts"]; W = vbody["weights"]          # pie y mano: los vanilla (no cambian con Tomb)
    B = {"legs": {}, "arms": {}}
    for side in ("L", "R"):
        # ---- pierna: anillos cada 5 mm de 0.06 a 0.49 (holgura 0)
        rings = {}
        y = 0.06
        while y <= 0.4901:
            rings["%.3f" % y] = ring_with_center(BA.leg_section(None, y, 0.0, body=body, side=side))
            y += 0.005
        bn = "Bip01_%s_Foot" % side
        pts = np.array([V[i] for i in range(len(V)) if bn in W[i]])
        foot = {"xmin": float(pts[:, 0].min()), "xmax": float(pts[:, 0].max()), "zheel": float(pts[:, 2].max()), "ztoe": float(pts[:, 2].min()), "ymax": float(pts[:, 1].max())}
        B["legs"][side] = {"rings": rings, "foot": foot, "bones": {"thigh": "Bip01_%s_Thigh" % side, "calf": "Bip01_%s_Calf" % side, "foot": "Bip01_%s_Foot" % side}}
        # ---- brazo: marco del antebrazo y anillos cada 5 mm de t=-0.02 a 0.16
        o, axis, down, front, L = BA.arm_frame(body, side)
        bones = BA.ARM_BONES[side]
        arings = {}
        t = -0.02
        while t <= 0.1601:
            # franja ±7 mm (no los ±14 mm por defecto): junto a codo y muñeca la franja ancha inflaba el anillo y los
            # encajes se abrían como un cubo (2026-10-14, "el brazo protésico se ve más grande que el normal")
            ring = BA.axis_ring(body, bones, side, o, axis, down, front, t, 0.0, band=ARM_RING_BAND)
            R = np.array(ring)
            # centro en coordenadas (t, down, front)
            du, dv = (R - o) @ down, (R - o) @ front
            c = o + axis * t + down * ((du.min() + du.max()) / 2) + front * ((dv.min() + dv.max()) / 2)
            arings["%.3f" % t] = {"c": [round(float(x), 5) for x in c], "pts": [[round(float(x), 5) for x in p] for p in R]}
            t += 0.005
        hb = "Bip01_%s_Hand" % side
        hp = np.array([V[i] for i in range(len(V)) if hb in W[i]])
        ht, hd, hf = (hp - o) @ axis, (hp - o) @ down, (hp - o) @ front
        hand = {"t": [float(ht.min()), float(ht.max())], "down": [float(hd.min()), float(hd.max())], "front": [float(hf.min()), float(hf.max())]}
        B["arms"][side] = {"o": [float(x) for x in o], "axis": [float(x) for x in axis], "down": [float(x) for x in down], "front": [float(x) for x in front], "forearm_len": float(L),
                           "rings": arings, "hand": hand, "bones": {"upper": bones[0], "forearm": bones[1], "hand": bones[2]},
                           "upper": upper_arm(body, side)}
    spec["bodies"][sex] = B
spec["saw"] = chainsaw_local()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(spec, open(OUT, "w", encoding="utf-8"), indent=0)
print("fit:", OUT, os.path.getsize(OUT) // 1024, "KB")
