"""Cuánto del cuerpo de Tomb's Player Body atraviesa cada prótesis (ajustadas al cuerpo vanilla). Sólo cuenta las partes
del cuerpo que siguen VISIBLES con esa amputación (las que no ocultan las máscaras del muñón). Compara con el cuerpo
vanilla, que es la referencia (debería dar ~0). Necesita out/tomb/*.json (tomb_export.py). Uso: python tomb_clip.py"""
import os, sys, json, glob
sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh, pzx
from PIL import Image
from render_icons import find_mesh
import build_assets as BA, render_combos as RC
MX = os.environ.get("TOMB_PROST") or os.path.join(RC.MOD, "models_X", "Prosthesis")     # TOMB_PROST: prótesis del submod
HIDE = {"Wrist": {"R": (6,), "L": (4,)}, "": {"R": (5, 6), "L": (3, 4)}, "Upper": {"R": (5, 6), "L": (3, 4)},
        "Ankle": {"R": (10,), "L": (8,)}, "Leg": {"R": (9, 10), "L": (7, 8)}, "Thigh": {"R": (9, 10), "L": (7, 8)}}
def visible(uvs_per_vertex, masks):
    hid = np.zeros((256, 256), bool)
    for i in masks: hid |= RC.mask_alpha(i) > 0
    px = np.clip((uvs_per_vertex[:, 0] * 256).astype(int), 0, 255); py = np.clip((uvs_per_vertex[:, 1] * 256).astype(int), 0, 255)
    return ~hid[py, px]
def tomb_body(sex):
    T = json.load(open(os.path.join("out", "tomb", sex + ".json"))); m = T["meshes"][0]
    v = np.load(os.path.join("out", "tomb", sex + "_verts_pz.npy"))
    uv = np.zeros((len(v), 2))
    for tri, tu in zip(m["tris"], m["uvs"]):
        for vi, (u, w) in zip(tri, tu): uv[vi] = (u, 1 - w)
    from tomb_common import tomb_main_faces
    keep = sorted({i for k in tomb_main_faces(m["tris"], len(v)) for i in m["tris"][k]})     # sin la membrana invisible
    return v[keep], uv[keep]
def vanilla_body(sex):
    b = BA.load_body(sex); return np.asarray(b["verts"], float), np.asarray(b["uvs"], float)
def inside_depth(mesh, pts):
    """Profundidad (m) de los puntos que quedan DENTRO de alguna pieza cerrada de la prótesis."""
    depth = np.zeros(len(pts))
    for part in mesh.split(only_watertight=False):
        if not part.is_watertight or part.volume <= 0: continue
        inside = part.contains(pts)
        if inside.any():
            _, dist, _ = trimesh.proximity.closest_point(part, pts[inside])
            depth[inside] = np.maximum(depth[inside], dist)
    return depth
rows = []
for sex, sx in (("Male", "M"), ("Female", "F")):
    bodies = {"vanilla": vanilla_body(sex), "Tomb": tomb_body(sex)}
    for path in sorted(glob.glob(os.path.join(MX, "*_R_%s.X" % sx))):
        name = os.path.basename(path)[:-2]
        if "Under" in name: continue
        lvl = next((l for l in ("Wrist", "Upper", "Ankle", "Thigh") if l in name), "Leg" if "Leg" in name else "")
        m = pzx.read_mesh(find_mesh(pzx.parse(path)))
        mesh = trimesh.Trimesh(np.array(m["verts"], float), np.array([list(f) for f in m["faces"]]), process=True)
        res = []
        for bn, (bv, buv) in bodies.items():
            vis = visible(buv, HIDE[lvl]["R"])
            d = inside_depth(mesh, bv[vis])
            res.append((int((d > 0.001).sum()), 1000 * (d.max() if len(d) else 0)))
        rows.append((name, lvl or "ForeArm", res))
for name, lvl, res in rows:
    print("%-26s %-8s vanilla: %3d vért dentro (máx %4.1f mm) | Tomb: %3d vért dentro (máx %4.1f mm)" % (name, lvl, res[0][0], res[0][1], res[1][0], res[1][1]))
