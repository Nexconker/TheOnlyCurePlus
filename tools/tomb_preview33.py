"""Vista previa de la 3.3 sobre el cuerpo de Tomb's Player Body (2026-10-17): brazos modulares (base + cabezal) y las
piernas nuevas, hombre y mujer, con los modelos del submod de desarrollo (TheOnlyCurePlusTombBodyDev) y sus muñones.
Sólo para mirar en local. Uso: TOC_MEDIA=...Dev python tomb_preview33.py -> out/scene_tomb33 ;
blender -b -P blender_render.py -- out/scene_tomb33 out/preview/tomb33 520"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import tomb_preview as TP

MOD = TP.MOD
SUB = os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlusTombBodyDev", "42", "media", "models_X", "Prosthesis")
TP.SUB_AMP = os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlusTombBodyDev", "42", "media", "models_X", "Amputation")
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_tomb33"); os.makedirs(P.OUT, exist_ok=True)
TEX = {"baseMech": "normalArm", "headMechHand": "normalArm", "baseCyber": "cyberArm", "headCyberHand": "cyberArm", "baseMed": "medicalArm",
       "headMedHand": "medicalArm", "baseWood": "pegArm", "headKnob": "pegArm", "pegLeg": "pegLeg", "cyberLeg": "cyberArm", "medicalLeg": "medicalLeg",
       "mechLeg": "mechLeg"}
def piece(name, sex):
    key = next(k for k in TEX if name.startswith(k))
    return P.posed_x(os.path.join(SUB, "%s_%s.X" % (name, "M" if sex == "Male" else "F")), os.path.join(MOD, "textures", "Prosthesis", TEX[key] + ".png"), TP.W)
CASES = {  # nombre: (máscaras ocultas, (tipo, parte), piezas)
    "mechwrist": ((6,), ("arm", "Hand"), ["baseMechWrist_R", "headMechHand_R"]),
    "cyberfore": ((5, 6), ("arm", "ForeArm"), ["baseCyber_R", "headCyberHand_R"]),
    "medupper": ((5, 6), ("arm", "UpperArm"), ["baseMedUpper_R", "headMedHand_R"]),
    "pegcalf": ((9, 10), ("leg", "LowerLeg"), ["pegLeg_R"]),
    "cyberthigh": ((9, 10), ("leg", "UpperLeg"), ["cyberLegThigh_R"]),
    "medankle": ((10,), ("leg", "Foot"), ["medicalLegAnkle_R"]),
}
jobs = {}
for case, (masks, (kind, part), pieces) in CASES.items():
    for sex in ("Male", "Female"):
        prs = [piece(n, sex) for n in pieces]
        c = np.vstack([np.asarray(p["v"]) for p in prs]).mean(0); focus = [round(c[0] * 10, 2), round(-c[2] * 10, 2), round(c[1] * 10, 2)]
        nm = "t33_%s_%s" % (case, sex[0].lower())
        P.export(nm, [TP.tomb_body(sex, masks), TP.stump_tomb(kind, part, "R", sex)] + prs)
        jobs[nm] = [nm, 215, focus, 3.4 if kind == "arm" else 4.2, 8]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
