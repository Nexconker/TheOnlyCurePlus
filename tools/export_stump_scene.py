"""Escenas de los muñones de brazo hechos del cuerpo (make_arm_stumps.py), posados en reposo, con la máscara del
juego aplicada al cuerpo. Uso: python export_stump_scene.py -> out/scene/stump_*.json
Render: blender -b -P blender_render.py -- out/scene out/preview/stumps 700 stump_hand,stump_fa,stump_ua,stump_fa_mech"""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_x as P

MOD = P.RC.MOD
TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
clip = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X"))
W = P.worlds_at(clip, 0, False)
def stump(part, sex="Male"):
    return P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStump_Right_%s_%s.X" % (part, sex)), TEX, W)
P.export("stump_hand", [P.posed_body("Male", [6], W), stump("Hand")])
P.export("stump_fa", [P.posed_body("Male", [5, 6], W), stump("ForeArm")])
P.export("stump_ua", [P.posed_body("Male", [5, 6], W), stump("UpperArm")])
P.export("stump_fa_mech", [P.posed_body("Male", [5, 6], W), stump("ForeArm"),
                           P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "normalArm_R_M.X"), os.path.join(MOD, "textures", "Prosthesis", "normalArm.png"), W)])
P.export("stump_ua_f", [P.posed_body("Female", [5, 6], W), stump("UpperArm", "Female")])
# manos mecánica y médica (comentario de la ronda 2: "desentonan con las manos del juego")
for tier, tex in (("normalArm", "normalArm"), ("medicalArm", "medicalArm")):
    for lvl, part, masks in (("Wrist", "Hand", [6]), ("", "ForeArm", [5, 6])):
        P.export("hand_%s%s" % (tier, lvl), [P.posed_body("Male", masks, W), stump(part),
                 P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%s%s_R_M.X" % (tier, lvl)), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), W)])
# prótesis por encima del codo (nivel Upper, 3.1.0): reposo y golpe (codo doblado)
atk = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Attack1Hand01_Hit.X"))
Ta = max(k["R"][-1][0] for k in atk["keys"].values() if "R" in k)
Wa = P.worlds_at(atk, 0.35 * Ta, False)
for tier, tex in (("pegArm", "pegArm"), ("hookArm", "hookArm"), ("normalArm", "normalArm"), ("medicalArm", "medicalArm"), ("chainsawArm", "chainsawArm")):
    for nm, WW in (("upper_%s" % tier, W), ("upperatk_%s" % tier, Wa)):
        P.export(nm, [P.posed_body("Male", [5, 6], WW),
                      P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStump_Right_UpperArm_Male.X"), TEX, WW),
                      P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%sUpper_R_M.X" % tier), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), WW)])
