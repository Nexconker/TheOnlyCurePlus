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
def stump(part, sex="Male", WW=None, prost=False):
    """prost: el modelo alternativo que el juego usa con una prótesis puesta (antebrazo y brazo: recortado bajo el encaje).
    Con el alfa de la textura (costura) y medio milímetro hacia dentro, como en seam_stump."""
    name = "ArmStumpProst" if prost and part != "Hand" else "ArmStump"
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "%s_Right_%s_%s.X" % (name, part, sex)), TEX, WW if WW is not None else W)
    return _inward(m)

def _inward(m):
    import numpy as np
    m["alpha"] = True
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * 0.0005
    return m

_posed_body = P.posed_body
P.posed_body = lambda sex, masks, WW: P.posed_body_texel(sex, masks, WW, shirt=False)   # el cuerpo enmascarado por texel
P.export("stump_hand", [P.posed_body("Male", [6], W), stump("Hand")])
P.export("stump_fa", [P.posed_body("Male", [5, 6], W), stump("ForeArm")])
P.export("stump_ua", [P.posed_body("Male", [5, 6], W), stump("UpperArm")])
P.export("stump_fa_mech", [P.posed_body("Male", [5, 6], W), stump("ForeArm"),
                           P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "normalArm_R_M.X"), os.path.join(MOD, "textures", "Prosthesis", "normalArm.png"), W)])
P.export("stump_ua_f", [P.posed_body("Female", [5, 6], W), stump("UpperArm", "Female")])
# manos mecánica y médica (comentario de la ronda 2: "desentonan con las manos del juego")
for tier, tex in (("normalArm", "normalArm"), ("medicalArm", "medicalArm")):
    for lvl, part, masks in (("Wrist", "Hand", [6]), ("", "ForeArm", [5, 6])):
        P.export("hand_%s%s" % (tier, lvl), [P.posed_body("Male", masks, W), stump(part, prost=True),
                 P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%s%s_R_M.X" % (tier, lvl)), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), W)])
# prótesis por encima del codo (nivel Upper, 3.1.0): reposo y golpe (codo doblado)
atk = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Attack1Hand01_Hit.X"))
Ta = max(k["R"][-1][0] for k in atk["keys"].values() if "R" in k)
Wa = P.worlds_at(atk, 0.35 * Ta, False)
for tier, tex in (("pegArm", "pegArm"), ("hookArm", "hookArm"), ("normalArm", "normalArm"), ("medicalArm", "medicalArm"), ("chainsawArm", "chainsawArm")):
    for nm, WW in (("upper_%s" % tier, W), ("upperatk_%s" % tier, Wa)):
        P.export(nm, [P.posed_body("Male", [5, 6], WW),
                      stump("UpperArm", WW=WW, prost=True),
                      P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%sUpper_R_M.X" % tier), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), WW)])
# comparación de grosor con el brazo sano (2026-10-14: "el brazo protésico se ve más grande que el normal")
for nm, part, masks, model, tex in (("cmp_wrist", "Hand", [6], "normalArmWrist_R_M", "normalArm"), ("cmp_fore", "ForeArm", [5, 6], "normalArm_R_M", "normalArm"),
                                    ("cmp_upper", "UpperArm", [5, 6], "normalArmUpper_R_M", "normalArm"), ("cmp_hook", "ForeArm", [5, 6], "hookArm_R_M", "hookArm"),
                                    ("cmp_peg_w", "Hand", [6], "pegArmWrist_R_M", "pegArm")):
    P.export(nm, [P.posed_body("Male", masks, W), stump(part, prost=True),
                  P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", model + ".X"), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), W)])
# costura del hombro como la dibuja el juego (2026-10-14: "se corta un poco"): cuerpo enmascarado texel a texel con una
# camiseta roja pintada, y el muñón con el alfa de su textura. Render: ... blender_render.py -- out/scene out/preview/seam 700 seam_fa_f,...
def seam_stump(part, sex, prost=False):
    tex = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skinF01_b.png" if sex == "Female" else "skin01_b.png")
    name = "ArmStumpProst" if prost else "ArmStump"
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "%s_Right_%s_%s.X" % (name, part, sex)), tex, W); m["alpha"] = True
    # medio milímetro hacia dentro: EEVEE no resuelve dos superficies con alfa en el mismo plano (pinta negro). En el
    # juego comparten profundidad y el cuerpo va primero: el resultado es el mismo salvo en la franja de 1 texel.
    import numpy as np
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * 0.0005
    return m
P.export("seam_fa_f", [P.posed_body_texel("Female", [5, 6], W), seam_stump("ForeArm", "Female")])
P.export("seam_fa_m", [P.posed_body_texel("Male", [5, 6], W), seam_stump("ForeArm", "Male")])
P.export("seam_ua_f", [P.posed_body_texel("Female", [5, 6], W), seam_stump("UpperArm", "Female")])
P.export("seam_hand_f", [P.posed_body_texel("Female", [6], W), seam_stump("Hand", "Female")])
P.export("seam_body_f", [P.posed_body_texel("Female", [5, 6], W)])
# tapa del muñón de pierna con la herida en la zona del pie (3.1.0)
_legtex = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skinF01_b.png")
_leg = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "Amputation_Left_LowerLeg_Female.X"), _legtex, W); _leg["alpha"] = True
P.export("seam_leg_f", [P.posed_body_texel("Female", [7, 8], W), _leg])
