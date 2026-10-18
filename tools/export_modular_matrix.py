"""Matriz de combinaciones 3.3 (todas las bases x todos los cabezales) sobre el cuerpo, en reposo, nivel antebrazo.
Uso: python export_modular_matrix.py <carpeta_media con models_X/Prosthesis> [nivel: Wrist|Fore|Upper] [pose: rest|swing]
  -> out/scene_matrix ; render: blender -b -P blender_render.py -- out/scene_matrix out/preview/matrix 400"""
import os, sys, json
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_x as P
import outfits as O

SRC = _a[0]
LVL = _a[1] if len(_a) > 1 else "Fore"
POSE = _a[2] if len(_a) > 2 else "rest"
MOD = P.RC.MOD
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_matrix")
os.makedirs(P.OUT, exist_ok=True)
TEX = {"Mech": "normalArm", "Med": "medicalArm", "Wood": "pegArm", "Scrap": "knifeArm", "MechHand": "normalArm", "MedHand": "medicalArm",
       "Knob": "pegArm", "Hook": "hookArm", "Chainsaw": "chainsawArm", "Bayonet": "knifeArm", "Cyber": "cyberArm", "CyberHand": "cyberArm"}
def ptex(k): return os.path.join(MOD, "textures", "Prosthesis", TEX[k] + ".png")
BASES = ["Wood", "Scrap", "Mech", "Med"]
HEADS = ["Knob", "Hook", "MechHand", "MedHand", "Chainsaw", "Bayonet"]
LV = {"Wrist": ("Wrist", "Hand", [6]), "Fore": ("", "ForeArm", [5, 6]), "Upper": ("Upper", "UpperArm", [5, 6])}[LVL]
clip, frac = {"rest": ("Bob_Idle.X", 0.0), "swing": ("Bob_Attack1Hand01_Hit.X", 0.35)}[POSE]
c = P.load_clip(os.path.join(P.ANIMS, "Bob", clip)); T = max(k[-1][0] for kk in c["keys"].values() for k in kk.values())
W = P.worlds_at(c, frac * T, False)
STUMP = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
body = P.posed_body_texel("Male", LV[2], W, shirt=False)
stump = O.inward(P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStumpProst_Right_%s_Male.X" % LV[1]), STUMP, W))
f = (W["Bip01_R_Forearm"][3, :3] + W["Bip01_R_Hand"][3, :3]) / 2
focus = [float(f[0] * 10), float(-f[2] * 10), float(f[1] * 10 - 0.6)]
jobs = {}
for b in BASES:
    base = P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "base%s%s_R_M.X" % (b, LV[0])), ptex(b), W)
    for h in HEADS:
        nm = "mx_%s_%s" % (b, h)
        P.export(nm, [body, stump, base, P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "head%s_R_M.X" % h), ptex(h), W)])
        jobs[nm] = [nm, 210, focus, 3.8, 10]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
