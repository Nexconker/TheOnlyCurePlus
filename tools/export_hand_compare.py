"""Comparación de la orientación de las manos protésicas con la natural (2026-10-17, "veo la mano algo inclinada hacia
adentro en lugar de verse recta como la natural"): misma persona y pose (Bob_Idle), de frente y de lado, con la mano
derecha natural y con base de muñeca + cabezal de mano.
Uso: TOC_MEDIA=...Dev python export_hand_compare.py -> out/scene_hands ; blender_render.py -- out/scene_hands out/preview/hands 600"""
import os, sys, json
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_x as P
import outfits as O

MOD = P.RC.MOD
FEMALE = os.environ.get("TOC_SEX", "M").upper().startswith("F")
SEXN, BODY, SXL = ("Female", "FemaleBody02", "F") if FEMALE else ("Male", "MaleBody02", "M")
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_hands" + ("_F" if FEMALE else "")); os.makedirs(P.OUT, exist_ok=True)
MX = os.path.join(MOD, "models_X")
HX = os.path.join(_a[0] if _a else MOD, "models_X")   # cabezales de prueba
TEX = {"Mech": "normalArm", "Med": "medicalArm", "Cyber": "cyberArm", "MechHand": "normalArm", "MedHand": "medicalArm", "CyberHand": "cyberArm"}
c = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X")); W = P.worlds_at(c, 0.0, False)
shirt = O.grimy(O.clothes_tex("Shirt_Tshirt_Textures", "TShirt_Grey.png"), 0.2, seed=4)
pants = O.mesh(os.path.join("Clothes", "Kate_Trousers.x" if FEMALE else "Bob_Trousers.x"), O.clothes_tex("Trousers_Mesh", "TrousersMesh_Black.png"), W)
hair = O.female_hair("Bob", W, (60, 40, 28)) if FEMALE else O.hair("Short", W, (46, 34, 26))
stump_tex = O.stump_tex("LowerLeg", BODY)
def person(hide):
    return [O.body(W, O.body_texture(BODY, overlays=[shirt], hide=hide + ("LeftLeg", "RightLeg", "Crotch")), SEXN), pants, hair]
P.export("hand_natural", person(()))
for b, h in (("Cyber", "CyberHand"), ("Mech", "MechHand"), ("Med", "MedHand")):
    P.export("hand_%s" % h, person(("RightHand",)) + [
        O.inward(P.posed_x(os.path.join(MX, "Amputation", "ArmStumpProst_Right_Hand_%s.X" % SEXN), stump_tex, W)),
        P.posed_x(os.path.join(HX, "Prosthesis", "base%sWrist_R_%s.X" % (b, SXL)), os.path.join(MOD, "textures", "Prosthesis", TEX[b] + ".png"), W),
        P.posed_x(os.path.join(HX, "Prosthesis", "head%s_R_%s.X" % (h, SXL)), os.path.join(MOD, "textures", "Prosthesis", TEX[h] + ".png"), W)])
hd = W["Bip01_R_Hand"][3, :3]
focus = [float(hd[0] * 10), float(-hd[2] * 10), float(hd[1] * 10 - 0.4)]
jobs = {}
for nm in ("hand_natural", "hand_CyberHand", "hand_MechHand", "hand_MedHand"):
    for az in (0, 90, 180, 270):
        jobs["%s_%d" % (nm, az)] = [nm, az, focus, 2.2, 2]
# de frente, plano medio (del hombro a la punta de los dedos)
el = W["Bip01_R_Forearm"][3, :3]
fm = [float(el[0] * 10 - 0.6), float(-el[2] * 10), float(el[1] * 10 + 0.3)]
for nm in ("hand_natural", "hand_CyberHand", "hand_MechHand", "hand_MedHand"):
    jobs["front_%s" % nm] = [nm, 180, fm, 6.0, 4]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
