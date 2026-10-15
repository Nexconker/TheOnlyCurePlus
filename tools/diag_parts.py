"""Orientación REAL de las caras de un .X: separa la malla en piezas conexas (vértices unidos por posición) y calcula
el volumen con signo de cada una. Negativo = caras hacia dentro = el juego no las dibuja (culling). La prueba
cross·normal de diag_winding.py es circular cuando las normales salen de las propias caras.
Uso: python diag_parts.py [archivo.X ...]   (sin argumentos: todas las prótesis de brazo)"""
import os, sys, glob
_args = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pzx
from render_icons import find_mesh

MX = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\models_X"
files = _args or sorted(glob.glob(os.path.join(MX, "Prosthesis", "*Arm*_R_M.X")))

def parts(V, F):
    par = list(range(len(V)))
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    pos = {}
    for i, v in enumerate(V): pos.setdefault(tuple(np.round(v, 5)), []).append(i)
    for g in pos.values():
        for i in g[1:]: par[find(i)] = find(g[0])
    for a, b, c in F: par[find(b)] = find(a); par[find(c)] = find(a)
    comp = {}
    for fi, f in enumerate(F): comp.setdefault(find(f[0]), []).append(fi)
    return list(comp.values())

bad_total = 0
for path in files:
    m = pzx.read_mesh(find_mesh(pzx.parse(path)))
    V = np.array(m["verts"], float); F = np.array([list(f) for f in m["faces"]], int)
    res = []
    for fl in parts(V, F):
        a, b, c = V[F[fl, 0]], V[F[fl, 1]], V[F[fl, 2]]
        vol = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0
        res.append((vol, len(fl)))
    neg = [r for r in res if r[0] < -1e-9]
    bad_total += len(neg)
    print("%-40s piezas %3d  invertidas %3d %s" % (os.path.basename(path), len(res), len(neg),
          "  (caras: " + ", ".join(str(n) for _, n in neg[:8]) + ")" if neg else ""))
print("piezas invertidas en total:", bad_total)
