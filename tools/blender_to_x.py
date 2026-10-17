"""Convierte los JSON exportados por blender_build.py en los .X del mod (ropa con pesos por hueso y
modelos de suelo estáticos). Uso: python blender_to_x.py [out/blender] [mod/media]"""
import os, sys, json, glob
_args = sys.argv[1:]; sys.argv = sys.argv[:1]      # build_assets toma argv[1] como ruta del mod
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pzx
import build_assets as BA

SRC = _args[0] if len(_args) > 0 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "blender")
MOD = _args[1] if len(_args) > 1 else BA.MOD
TEX = {"pegLeg": "Prosthesis/pegLeg", "mechLeg": "Prosthesis/mechLeg", "medicalLeg": "Prosthesis/medicalLeg",
       "pegArm": "Prosthesis/pegArm", "hookArm": "Prosthesis/hookArm", "normalArm": "Prosthesis/normalArm", "medicalArm": "Prosthesis/medicalArm",
       "chainsawArm": "Prosthesis/chainsawArm", "knifeArm": "Prosthesis/knifeArm"}
bodies = {"Male": BA.load_body("Male"), "Female": BA.load_body("Female")}

def tier_of(name):
    for t in TEX:
        if name.startswith(t): return t
    raise ValueError(name)

def lay(verts, normals):
    """Tumba el modelo (eje largo Y -> X) y lo apoya en el suelo, como los modelos de suelo de build_assets."""
    V = np.array(verts, float); Nn = np.array(normals, float)
    c = V.mean(0)
    R = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float)
    V = (V - c) @ R.T; Nn = Nn @ R.T
    V[:, 1] -= V[:, 1].min() - 0.002
    return V, Nn

n = 0
for path in sorted(glob.glob(os.path.join(SRC, "*.json"))):
    name = os.path.splitext(os.path.basename(path))[0]
    d = json.load(open(path))
    tier = tier_of(name)
    sex = "Male" if name.endswith("_M") else "Female"
    body = bodies[sex]
    verts = [BA.v3(v) for v in d["verts"]]; normals = [BA.v3(v) for v in d["normals"]]
    uvs = [(float(u), float(v)) for u, v in d["uvs"]]; faces = [tuple(f) for f in d["faces"]]
    weights = [[(b, 1.0)] for b in d["bones"]]
    out = os.path.join(MOD, "models_X", "Prosthesis", name + ".X")
    pzx.write_skinned_x(BA.TEMPLATE[sex], out, name, TEX[tier], verts, normals, uvs, faces, weights, body["offsets"])
    n += 1
    # modelo de suelo: la pieza izquierda masculina del nivel base (la motosierra sólo existe a la derecha:
    # se deja tal cual, de lado sobre el suelo, que es como cae una motosierra)
    if name == tier + ("_R_M" if tier in ("chainsawArm", "knifeArm") else "_L_M"):      # motosierra y bayoneta: sólo derechas
        if tier == "chainsawArm":
            V = np.array(d["verts"], float); Nn = np.array(d["normals"], float)
            V = V - V.mean(0); V[:, 1] -= V[:, 1].min() - 0.002
        else:
            V, Nn = lay(d["verts"], d["normals"])
        gname = tier + "_Ground"
        pzx.write_static_x(os.path.join(MOD, "models_X", "Prosthesis", gname + ".X"), gname, TEX[tier], [BA.v3(v) for v in V], [BA.v3(v) for v in Nn], uvs, faces)
        n += 1
print("escritos", n, "archivos .X en", os.path.join(MOD, "models_X", "Prosthesis"))
