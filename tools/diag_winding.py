"""Comprueba que todas las mallas .X del mod tienen las caras orientadas como las vanilla:
cross(b-a, c-a) · normal_media > 0 (caras a la vista desde fuera). Imprime la fracción por archivo."""
import os, sys, glob
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
import numpy as np, pzx
from render_icons import find_mesh

MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\models_X"
bad = 0
for path in sorted(glob.glob(os.path.join(MOD, "**", "*.X"), recursive=True)):
    m = pzx.read_mesh(find_mesh(pzx.parse(path)))
    v = np.array(m["verts"], float); f = np.array([list(x) for x in m["faces"]], int)
    n = np.array(m["normals"], float) if m.get("normals") else None
    if n is None or len(n) != len(v):
        print("%-45s sin normales" % os.path.relpath(path, MOD)); continue
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    vn = n[f[:, 0]] + n[f[:, 1]] + n[f[:, 2]]
    ok = (np.einsum("ij,ij->i", fn, vn) > 0).mean()
    flag = "" if ok >= 0.97 else "   <-- REVISAR"
    if flag: bad += 1
    print("%-45s %5.1f%% (%d caras)%s" % (os.path.relpath(path, MOD), ok * 100, len(f), flag))
print("archivos con problemas:", bad)
