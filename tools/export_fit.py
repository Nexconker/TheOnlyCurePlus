"""Exporta a JSON los datos de ajuste que Blender necesita para remodelar las prótesis:
secciones reales de piernas y antebrazos del cuerpo vanilla (holgura 0, con su centro), marcos de
huesos, medidas de pie y mano, alturas de corte y huesos. Unidades y ejes del juego (Y arriba, frente -Z).
Uso: python export_fit.py [salida.json]"""
import os, sys, json, math
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import build_assets as BA

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "fit.json")

def ring_with_center(ring):
    R = np.array(ring)
    c = [(R[:, 0].min() + R[:, 0].max()) / 2, float(R[0, 1]), (R[:, 2].min() + R[:, 2].max()) / 2]
    return {"c": [round(float(x), 5) for x in c], "pts": [[round(float(x), 5) for x in p] for p in R]}

spec = {"units": "PZ (0.57 u/m), Y arriba, frente -Z", "leg_cuts": BA.LEG_CUTS, "leg_levels": BA.LEG_LEVELS, "arm_levels": BA.ARM_LEVELS, "bodies": {}}
for sex in ("Male", "Female"):
    body = BA.load_body(sex)
    V = body["verts"]; W = body["weights"]
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
            ring = BA.axis_ring(body, bones, side, o, axis, down, front, t, 0.0)
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
                           "rings": arings, "hand": hand, "bones": {"upper": bones[0], "forearm": bones[1], "hand": bones[2]}}
    spec["bodies"][sex] = B
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(spec, open(OUT, "w", encoding="utf-8"), indent=0)
print("fit:", OUT, os.path.getsize(OUT) // 1024, "KB")
