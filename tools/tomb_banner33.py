"""Renders del banner de Tomb's Player Body con la 3.3 (2026-10-17): su cuerpo con su textura, los muñones del submod y
prótesis de la 3.3 de cuerpo entero. Uso: python tomb_banner33.py -> out/scene_tban ;
blender -b -P blender_render.py -- out/scene_tban out/workshop/renders 1600 tbanner_m,tbanner_f,tbanner_f2"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import tomb_preview as TP

MOD = TP.MOD
SUB = os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlusTombBody", "42", "media", "models_X")
TP.SUB_AMP = os.path.join(SUB, "Amputation")
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_tban"); os.makedirs(P.OUT, exist_ok=True)
def tex(n): return os.path.join(MOD, "textures", "Prosthesis", n + ".png")
def piece(name, sex, t): return P.posed_x(os.path.join(SUB, "Prosthesis", "%s_%s.X" % (name, "M" if sex == "Male" else "F")), tex(t), TP.W)
CASTS = {  # nombre: (sexo, máscaras, muñones [(tipo, parte, lado)], piezas [(modelo, atlas)], acimut)
    "tbanner_m": ("Male", (5, 6, 7, 8), [("arm", "ForeArm", "R"), ("leg", "LowerLeg", "L")],
                  [("baseCyber_R", "cyberArm"), ("headCyberHand_R", "cyberArm"), ("mechLeg_L", "mechLeg")], 160),
    "tbanner_f": ("Female", (9, 10), [("leg", "UpperLeg", "R")], [("medicalLegThigh_R", "medicalLeg")], 200),
    "tbanner_f2": ("Female", (4, 9, 10), [("arm", "Hand", "L"), ("leg", "LowerLeg", "R")],
                   [("baseScrapWrist_L", "knifeArm"), ("headHook_L", "hookArm"), ("pegLeg_R", "pegLeg")], 150),
}
jobs = {}
for nm, (sex, masks, stumps, pieces, az) in CASTS.items():
    meshes = [TP.tomb_body(sex, masks)] + [TP.stump_tomb(k, p, s, sex) for k, p, s in stumps] + [piece(m, sex, t) for m, t in pieces]
    P.export("tb_" + nm, meshes)
    pel = TP.W["Bip01_Pelvis"][3, :3] * 0.75 + TP.W["Bip01_Head"][3, :3] * 0.25
    jobs[nm] = ["tb_" + nm, az, [float(pel[0] * 10), float(-pel[2] * 10), float(pel[1] * 10)], 10.0, 6]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
