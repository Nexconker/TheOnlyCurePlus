"""Vistas de las prótesis modulares 3.3 (base + cabezal) sobre el cuerpo, en reposo y agarrando una pistola.
Uso: python export_modular_scene.py <carpeta_media con models_X/Prosthesis> <base> <cabezal> [lado]
  -> out/scene_mod ; render: blender -b -P blender_render.py -- out/scene_mod out/preview/mod 600"""
import os, sys, json
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import outfits as O

SRC, BASE, HEAD = _a[0], _a[1], _a[2]
SIDE = _a[3] if len(_a) > 3 else "R"
SW = "Left" if SIDE == "L" else "Right"
MOD = P.RC.MOD
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_mod")
os.makedirs(P.OUT, exist_ok=True)
TEX = {"Mech": "normalArm", "Med": "medicalArm", "Wood": "pegArm", "Scrap": "knifeArm", "MechHand": "normalArm", "MedHand": "medicalArm",
       "Knob": "pegArm", "Hook": "hookArm", "Chainsaw": "chainsawArm", "Bayonet": "knifeArm", "Cyber": "cyberArm", "CyberHand": "cyberArm"}
def ptex(k): return os.path.join(MOD, "textures", "Prosthesis", TEX[k] + ".png")
STUMP = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
S = 10.0
def bl(p): return [float(p[0] * S), float(-p[2] * S), float(p[1] * S)]
MH, MA = (4, 3) if SIDE == "L" else (6, 5)
LEVELS = [("Wrist", "Hand", [MH]), ("", "ForeArm", [MA, MH]), ("Upper", "UpperArm", [MA, MH])]
def clip_w(name, frac):
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", name)); T = max(k[-1][0] for kk in c["keys"].values() for k in kk.values())
    return P.worlds_at(c, frac * T, False)
POSES = {"rest": clip_w("Bob_Idle.X", 0.0), "grip": clip_w("Bob_AimToIdle_Handgun.X", 0.0), "swing": clip_w("Bob_Attack1Hand01_Hit.X", 0.35)}
jobs = {}
for pose, W in POSES.items():
    focus = bl((W["Bip01_%s_Forearm" % SIDE][3, :3] + W["Bip01_%s_Hand" % SIDE][3, :3]) / 2)
    for lvl, part, masks in LEVELS:
        nm = "mod_%s%s_%s" % (BASE, lvl or "Fore", pose)
        st = O.inward(P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStumpProst_%s_%s_Male.X" % (SW, part)), STUMP, W))
        P.export(nm, [P.posed_body_texel("Male", masks, W, shirt=False), st,
                      P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "base%s%s_%s_M.X" % (BASE, lvl, SIDE)), ptex(BASE), W),
                      P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "head%s_%s_M.X" % (HEAD, SIDE)), ptex(HEAD), W)])
        for az in (200, 290):
            jobs["%s_%d" % (nm, az)] = [nm, az, focus, 3.0, 12]
        if lvl == "":       # primer plano de la mano (cabezal)
            hf = bl(W["Bip01_%s_Hand" % SIDE][3, :3] * 1.25 - W["Bip01_%s_Forearm" % SIDE][3, :3] * 0.25)
            for az in (150, 250, 330):
                jobs["hand_%s_%s_%d" % (BASE, pose, az)] = [nm, az, hf, 1.1, 15]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
