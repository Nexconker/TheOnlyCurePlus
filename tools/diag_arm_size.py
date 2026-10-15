"""Compara el grosor de las prótesis de brazo con el brazo real del cuerpo vanilla, sección a sección (pose de reposo).
Para cada t a lo largo del brazo superior (hombro -> codo) y del antebrazo (codo -> muñeca): radio medio de la prótesis
respecto al centro del anillo del cuerpo y radio medio del cuerpo. Uso: python diag_arm_size.py [modelo ...]"""
import os, sys, json
_args = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pzx
from render_icons import find_mesh

HERE = os.path.dirname(os.path.abspath(__file__))
MX = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\models_X\Prosthesis"
fit = json.load(open(os.path.join(HERE, "out", "fit.json"), encoding="utf-8"))
models = _args or ["normalArmUpper_R_M", "medicalArmUpper_R_M", "hookArmUpper_R_M", "pegArmUpper_R_M", "chainsawArmUpper_R_M",
                   "normalArm_R_M", "normalArmWrist_R_M", "hookArm_R_M"]

def section(V, o, ax, t, band=0.004):
    tt = (V - o) @ ax
    return V[np.abs(tt - t) <= band]

def report(name):
    sex = "Male" if name.endswith("_M") else "Female"; side = name.split("_")[-2]
    arm = fit["bodies"][sex]["arms"][side]; up = arm["upper"]
    V = np.array(pzx.read_mesh(find_mesh(pzx.parse(os.path.join(MX, name + ".X"))))["verts"], float)
    rows = []
    for label, frame, rings, ts in (("brazo", up, up["rings"], [0.03, 0.05, 0.07, 0.09, 0.11, 0.125]),
                                    ("antebrazo", arm, arm["rings"], [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12])):
        o, ax = np.array(frame["o"]), np.array(frame["axis"])
        for t in ts:
            key = "%.3f" % (round(t / 0.005) * 0.005)
            if key not in rings: continue
            ring = np.array(rings[key]["pts"]); c = np.array(rings[key]["c"])
            rb = np.linalg.norm(ring - c, axis=1).mean()
            sec = section(V, o, ax, t)
            if len(sec) < 6: continue
            # sólo lo que rodea el eje (descarta mano, bisagra, tornillos lejos del centro)
            d = sec - c; d -= np.outer(d @ ax, ax); r = np.linalg.norm(d, axis=1)
            r = r[r < rb * 1.8]
            if len(r) < 6: continue
            rows.append((label, t, rb, np.percentile(r, 90), np.median(r)))
    print("== %s" % name)
    for label, t, rb, rp, rm in rows:
        print("  %-9s t=%.3f  cuerpo %.4f  prótesis p90 %.4f (%+.0f%%)  mediana %.4f (%+.0f%%)" % (label, t, rb, rp, (rp / rb - 1) * 100, rm, (rm / rb - 1) * 100))

for m in models: report(m)
