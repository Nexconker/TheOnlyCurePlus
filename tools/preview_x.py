"""Vista rápida de modelos .X sin Blender: dibuja el cuerpo vanilla en gris y la(s) pieza(s) en color,
de frente y de lado. Uso: python preview_x.py salida.png pieza1.X [pieza2.X ...] [--sex Male|Female] [--nobody]"""
import sys, os
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
import pzx, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

PZ = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media"

def find_mesh(n):
    for c in n.children:
        if c.type == "Mesh": return c
        r = find_mesh(c)
        if r: return r

def load(path):
    m = pzx.read_mesh(find_mesh(pzx.parse(path)))
    return np.array(m["verts"], float), [tuple(f) for f in m["faces"]]

def draw(ax, verts, faces, proj, color, alpha=1.0, zorder=1):
    # proj: ("x","y") frente ; ("z","y") lado ; ("x","z") arriba
    ix = {"x": 0, "y": 1, "z": 2}
    a, b = ix[proj[0]], ix[proj[1]]
    depth_axis = ({0, 1, 2} - {a, b}).pop()
    polys, depths = [], []
    for f in faces:
        p = verts[list(f)]
        polys.append(p[:, [a, b]])
        depths.append(p[:, depth_axis].mean())
    order = np.argsort(depths)
    polys = [polys[i] for i in order]
    shade = (np.array(depths)[order] - min(depths)) / (max(depths) - min(depths) + 1e-6)
    cols = [(color[0] * (0.55 + 0.45 * s), color[1] * (0.55 + 0.45 * s), color[2] * (0.55 + 0.45 * s), alpha) for s in shade]
    pc = PolyCollection(polys, facecolors=cols, edgecolors=(0, 0, 0, 0.15), linewidths=0.2, zorder=zorder)
    ax.add_collection(pc)

def main():
    args = sys.argv[1:]
    out = args.pop(0)
    sex = "Male"; body = True
    if "--sex" in args:
        i = args.index("--sex"); sex = args[i + 1]; del args[i:i + 2]
    if "--nobody" in args:
        args.remove("--nobody"); body = False
    pieces = [(p, load(p)) for p in args]
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    projs = [("x", "y", "frente"), ("z", "y", "lado"), ("x", "z", "arriba")]
    colors = [(0.85, 0.3, 0.3), (0.3, 0.6, 0.9), (0.3, 0.8, 0.4), (0.9, 0.7, 0.2)]
    allv = []
    if body:
        bv, bf = load(os.path.join(PZ, "models_X", "Skinned", "%sBody.X" % sex))
        allv.append(bv)
    for ax, (pa, pb, title) in zip(axes, projs):
        if body: draw(ax, bv, bf, (pa, pb), (0.75, 0.75, 0.75), 0.9, 1)
        for k, (p, (v, f)) in enumerate(pieces):
            draw(ax, v, f, (pa, pb), colors[k % len(colors)], 1.0, 2)
        ax.set_title(title); ax.set_aspect("equal"); ax.grid(True, alpha=0.3)
    for _, (v, _) in pieces: allv.append(v)
    V = np.vstack(allv)
    pad = 0.05
    for ax, (pa, pb, _) in zip(axes, projs):
        ix = {"x": 0, "y": 1, "z": 2}
        ax.set_xlim(V[:, ix[pa]].min() - pad, V[:, ix[pa]].max() + pad)
        ax.set_ylim(V[:, ix[pb]].min() - pad, V[:, ix[pb]].max() + pad)
    fig.suptitle(", ".join(os.path.basename(p) for p, _ in pieces))
    fig.tight_layout(); fig.savefig(out, dpi=110); print("saved", out)

main()
