"""Renders de las tarjetas del Workshop para la 3.3 (2026-10-17, "actualiza todos los renders para las imágenes de la
Workshop y añade nuevos"): personajes vestidos con ropa real del juego, muñones del tono de su piel y las prótesis de la
3.3 (bases + cabezales modulares, gama cyber, piernas nuevas). Mismos nombres de render que usaba make_workshop.py
(hero_m, hero_f, arms_*, legs_*) más los nuevos (arms_cyber, legs_cyber, cyber_*, mod_*, prop_*).
Uso: python export_workshop33.py -> out/scene_ws33 ; blender -b -P blender_render.py -- out/scene_ws33 out/workshop/renders 1600"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import outfits as O
from render_icons import load_x

MOD = P.RC.MOD
MX = os.path.join(MOD, "models_X")
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_ws33"); os.makedirs(P.OUT, exist_ok=True)
TEX = {"Wood": "pegArm", "Scrap": "knifeArm", "Mech": "normalArm", "Med": "medicalArm", "Cyber": "cyberArm",
       "Knob": "pegArm", "Hook": "hookArm", "MechHand": "normalArm", "MedHand": "medicalArm", "CyberHand": "cyberArm",
       "Chainsaw": "chainsawArm", "Bayonet": "knifeArm", "pegLeg": "pegLeg", "mechLeg": "mechLeg", "medicalLeg": "medicalLeg", "cyberLeg": "cyberArm"}
SIDE = {"L": "Left", "R": "Right"}
ARM_PART = {"Wrist": "Hand", "": "ForeArm", "Upper": "UpperArm"}
LEG_PART = {"Ankle": "Foot", "": "LowerLeg", "Thigh": "UpperLeg"}
ARM_HIDE = {"Wrist": ("Hand",), "": ("Arm", "Hand"), "Upper": ("Arm", "Hand")}
LEG_HIDE = {"Ankle": ("Foot",), "": ("Leg", "Foot"), "Thigh": ("Leg", "Foot")}

def ptex(key, paint=None):
    if paint: return os.path.join(MOD, "textures", "Prosthesis", "Paint", "%s_%s.png" % (TEX[key], paint))
    return os.path.join(MOD, "textures", "Prosthesis", TEX[key] + ".png")

def clip_w(name, frac=0.0):
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", name)); T = max(k[-1][0] for kk in c["keys"].values() for k in kk.values())
    return P.worlds_at(c, frac * T, False)

def person(W, sex, arm=None, leg=None, shirt="TShirt_Grey.png", lower="shorts", hair=None, beard=None, skin=2, paint=None, blood=0):
    """arm = (lado, nivel, base, cabezal); leg = (lado, nivel, tier). Devuelve las mallas del personaje."""
    F = sex == "Female"; SX = "Female" if F else "Male"; sx = "F" if F else "M"
    body_name = ("FemaleBody%02d" if F else "MaleBody%02d") % skin
    hide = []
    if arm: hide += [SIDE[arm[0]] + h for h in ARM_HIDE[arm[1]]]
    if leg: hide += [SIDE[leg[0]] + h for h in LEG_HIDE[leg[1]]]
    over = [O.grimy(O.clothes_tex("Shirt_Tshirt_Textures", shirt), 0.25, blood=blood, seed=3)]
    meshes = []
    if lower == "shorts": over.append(O.clothes_tex("Shorts_Textures", "LongShorts_Denim.png"))
    over.append(O.clothes_tex("Shoes_Socks_Textres", "ArmyBoots.png"))
    if lower == "trousers": hide += ["LeftLeg", "RightLeg", "Crotch"]
    meshes.append(O.body(W, O.body_texture(body_name, overlays=over, hide=tuple(hide)), SX))
    if lower == "trousers":
        meshes.append(O.mesh(os.path.join("Clothes", ("Kate_Trousers.x" if F else "Bob_Trousers.x")), O.grimy(O.clothes_tex("Trousers_Mesh", "TrousersMesh_Black.png"), 0.3, seed=6), W))
    if hair: meshes.append(O.female_hair(hair[0], W, hair[1]) if F else O.hair(hair[0], W, hair[1]))
    if beard and not F: meshes.append(O.beard(beard[0], W, beard[1]))
    if arm:
        side, lvl, base, head = arm
        meshes.append(O.inward(P.posed_x(os.path.join(MX, "Amputation", "ArmStumpProst_%s_%s_%s.X" % (SIDE[side], ARM_PART[lvl], SX)), O.stump_tex("LowerLeg", body_name), W)))
        meshes.append(P.posed_x(os.path.join(MX, "Prosthesis", "base%s%s_%s_%s.X" % (base, lvl, side, sx)), ptex(base, paint), W))
        meshes.append(P.posed_x(os.path.join(MX, "Prosthesis", "head%s_%s_%s.X" % (head, side, sx)), ptex(head, paint), W))
    if leg:
        side, lvl, tier = leg
        meshes.append(O.inward(P.posed_x(os.path.join(MX, "Amputation", "Amputation_%s_%s_%s.X" % (SIDE[side], LEG_PART[lvl], SX)), O.stump_tex(LEG_PART[lvl], body_name), W)))
        meshes.append(P.posed_x(os.path.join(MX, "Prosthesis", "%s%s_%s_%s.X" % (tier, lvl, side, sx)), ptex(tier, paint), W))
    return meshes

def bl(p, dz=0.0): return [float(p[0] * 10), float(-p[2] * 10), float(p[1] * 10 + dz)]
jobs = {}
REST = clip_w("Bob_Idle.X")
WALK = clip_w("Bob_Walk.X", 0.25)
MID = bl(REST["Bip01_Pelvis"][3, :3] * 0.75 + REST["Bip01_Head"][3, :3] * 0.25)

def scene(name, meshes, job_name=None, az=150, focus=None, zoom=None, elev=6):
    P.export(name, meshes)
    jobs[job_name or name] = [name, az, focus or MID, zoom or 10.0, elev, "nocull"]

# ---- héroe: cyber contra chatarra
scene("ws_hero_m", person(REST, "Male", arm=("R", "", "Cyber", "CyberHand"), leg=("L", "", "mechLeg"), shirt="TShirt_Grey.png",
                          hair=("Short", (40, 30, 24)), beard=("Full", (40, 30, 24))), "hero_m", az=150)
scene("ws_hero_f", person(REST, "Female", arm=("L", "Wrist", "Scrap", "Hook"), leg=("R", "Thigh", "medicalLeg"), shirt="TShirt_White.png",
                          hair=("Bob", (70, 44, 28)), blood=6), "hero_f", az=150)
# ---- brazos (cuerpo de cintura para arriba, el brazo protésico de frente)
def arm_job(name, sex, arm, az, hair, beard=None, shirt="TShirt_Grey.png", paint=None):
    W = REST
    s = "Right" if arm[0] == "R" else "Left"
    f = bl(W["Bip01_%s_Forearm" % ("R" if arm[0] == "R" else "L")][3, :3] * 0.6 + W["Bip01_Spine1"][3, :3] * 0.4, 0.2)
    scene("ws_" + name, person(W, sex, arm=arm, lower="trousers", hair=hair, beard=beard, shirt=shirt, paint=paint), name, az=az, focus=f, zoom=6.2, elev=10)
arm_job("arms_peg", "Male", ("R", "", "Wood", "Knob"), 210, ("Messy", (54, 46, 38)), ("Chin", (54, 46, 38)), "Shirt_LumberjackRed.png" if False else "TShirt_Grey.png")
arm_job("arms_hook", "Female", ("L", "Wrist", "Scrap", "Hook"), 150, ("Bob", (70, 44, 28)), shirt="TShirt_White.png")
arm_job("arms_mech", "Male", ("R", "Upper", "Mech", "MechHand"), 210, ("Short", (40, 30, 24)), ("Full", (40, 30, 24)))
arm_job("arms_medical", "Female", ("L", "", "Med", "MedHand"), 150, ("Bob", (34, 26, 22)), shirt="TShirt_Grey.png")
arm_job("arms_cyber", "Male", ("R", "", "Cyber", "CyberHand"), 210, ("Short", (40, 30, 24)), shirt="TShirt_White.png")
# ---- piernas (de cintura para abajo, de lado a media zancada)
def leg_job(name, sex, leg, hair):
    W = WALK
    k = bl(W["Bip01_%s_Calf" % leg[0]][3, :3], -0.4)
    scene("ws_" + name, person(W, sex, leg=leg, hair=hair), name, az=235, focus=k, zoom=7.0, elev=4)
leg_job("legs_peg", "Male", ("R", "", "pegLeg"), ("Short", (40, 30, 24)))
leg_job("legs_mech", "Male", ("L", "Thigh", "mechLeg"), ("Short", (40, 30, 24)))
leg_job("legs_medical", "Female", ("R", "", "medicalLeg"), ("Bob", (70, 44, 28)))
leg_job("legs_cyber", "Female", ("R", "Thigh", "cyberLeg"), ("Bob", (70, 44, 28)))
# ---- tarjeta cyber: brazo + pierna cyber (pintados de rojo uno, otro original) y primer plano de la mano
cy = person(REST, "Male", arm=("R", "", "Cyber", "CyberHand"), leg=("R", "Thigh", "cyberLeg"), shirt="TShirt_Grey.png", hair=("Short", (40, 30, 24)))
scene("ws_cyber_full", cy, "cyber_full", az=200)
h = bl(REST["Bip01_R_Hand"][3, :3] * 0.7 + REST["Bip01_R_Forearm"][3, :3] * 0.3)
jobs["cyber_hand"] = None
GRIP = clip_w("Bob_AimToIdle_Handgun.X")
scene("ws_cyber_grip", person(GRIP, "Female", arm=("R", "", "Cyber", "CyberHand"), shirt="TShirt_White.png", hair=("Bob", (34, 26, 22)), lower="trousers"),
      "cyber_grip", az=215, focus=bl(GRIP["Bip01_R_Hand"][3, :3] * 0.6 + GRIP["Bip01_Spine1"][3, :3] * 0.4), zoom=6.0, elev=8)
# ---- tarjeta modular: el mismo armazón mecánico con cinco cabezales (primer plano del brazo)
fm = bl(REST["Bip01_R_Hand"][3, :3] * 0.6 + REST["Bip01_R_Forearm"][3, :3] * 0.4, -0.3)
for head in ("Knob", "Hook", "MechHand", "Chainsaw", "Bayonet"):
    base = "Mech"
    scene("ws_mod_" + head, person(REST, "Male", arm=("R", "", base, head), lower="trousers", hair=("Short", (40, 30, 24))),
          "mod_" + head, az=215, focus=[fm[0], fm[1], fm[2] - (0.6 if head == "Chainsaw" else 0.2 if head == "Bayonet" else 0.0)],
          zoom=4.6 if head == "Chainsaw" else 3.8, elev=8)
# ---- pintura: tres personas con la misma combinación en distintos colores
for col in ("red", "yellow", "blue"):
    scene("ws_paint_" + col, person(REST, "Male", arm=("R", "", "Mech", "MechHand"), leg=("L", "", "mechLeg"), paint=col, hair=("Short", (40, 30, 24))),
          "paint_" + col, az=160)
# ---- objetos en el suelo (tarjeta de ítems)
for nm, rel, tx in (("prop_cyberhand", "headCyberHand_Ground", "cyberArm"), ("prop_cyberleg", "cyberLeg_Ground", "cyberArm"),
                    ("prop_basemech", "baseMech_Ground", "normalArm")):
    v, f, uv = load_x(os.path.join(MX, "Prosthesis", rel + ".X"))
    P.export("ws_" + nm, [{"v": v, "f": f, "uv": uv, "tex": os.path.join(MOD, "textures", "Prosthesis", tx + ".png")}])
    vv = np.asarray(v); c = (vv.min(0) + vv.max(0)) / 2
    jobs[nm] = ["ws_" + nm, 150, bl(c), None, 40]
hg = bl(GRIP["Bip01_R_Hand"][3, :3] * 0.8 + GRIP["Bip01_R_Forearm"][3, :3] * 0.2)
jobs["cyber_hand"] = ["ws_cyber_grip", 250, hg, 2.2, 10, "nocull"]       # primer plano de la mano agarrando
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
