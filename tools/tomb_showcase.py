"""Renders de las prótesis puestas sobre el cuerpo de Tomb's Player Body con los muñones del submod TombBody fit
(make_tomb_stumps.py). Cuerpo de Tomb con su textura y las máscaras por texel, muñón con la misma textura (como en el
juego con TombBody activo) y la prótesis del mod. Sólo para mirar en local.
Uso: python tomb_showcase.py  ->  out/scene/tshow_*.json + entradas en out/scene/tomb_jobs.json"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import tomb_preview as TP          # cuerpo de Tomb posado y enmascarado (tomb_body), máscaras por texel

MOD = TP.MOD
SUBX = os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlusTombBody", "42", "media", "models_X", "Amputation")
SUBP = os.path.join(os.path.dirname(SUBX), "Prosthesis")          # prótesis ajustadas al cuerpo de Tomb (export_fit --tomb)
MAINP = TP.PROST

def prost_sub(model, sex):
    TP.PROST = SUBP; m = TP.prost(model, sex); TP.PROST = MAINP; return m
W = TP.W

def tomb_stump(name, sex):
    tex = os.path.join(TP.TT, ("MaleBody01" if sex == "Male" else "FemaleBody01") + ".png")
    return P.posed_x(os.path.join(SUBX, name + ".X"), tex, W)

def vanilla_stump(name, sex):
    """El muñón del mod principal (cuerpo vanilla, su textura con alfa), para el antes/después."""
    tex = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg" if name.startswith("Arm") else name.split("_")[2],
                       "skin01_b.png" if sex == "Male" else "skinF01_b.png")
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", name + ".X"), tex, W)
    return TP.inward(m)

ARM_TIERS = ["pegArm", "hookArm", "normalArm", "medicalArm", "chainsawArm"]
LEG_TIERS = ["pegLeg", "mechLeg", "medicalLeg"]
ARM_LEVELS = [("Wrist", "Hand", (6,)), ("", "ForeArm", (5, 6)), ("Upper", "UpperArm", (5, 6))]
LEG_LEVELS = [("Ankle", "Foot", (10,)), ("", "LowerLeg", (9, 10)), ("Thigh", "UpperLeg", (9, 10))]

jobs = json.load(open(os.path.join("out", "scene", "tomb_jobs.json"))) if os.path.exists(os.path.join("out", "scene", "tomb_jobs.json")) else {}
jobs = {k: v for k, v in jobs.items() if not k.startswith("tshow_")}
for sex in ("Male", "Female"):
    sx = sex[0].lower()
    for kind, tiers, levels in (("arm", ARM_TIERS, ARM_LEVELS), ("leg", LEG_TIERS, LEG_LEVELS)):
        for lvl, part, masks in levels:
            if kind == "arm":
                stump = "ArmStump%s_Right_%s_%s" % ("" if part == "Hand" else "Prost", part, sex)
            else:
                stump = "Amputation_Right_%s_%s" % (part, sex)
            body = TP.tomb_body(sex, masks)
            st = tomb_stump(stump, sex)
            for tier in tiers:
                pr = prost_sub("%s%s_R" % (tier, lvl), sex)
                name = "tshow_%s_%s_%s" % (sx, kind, tier + (lvl or "Mid"))
                P.export(name, [body, st, pr])
                c = np.asarray(pr["v"]).mean(0)
                focus = [round(c[0] * 10, 2), round(-c[2] * 10, 2), round(c[1] * 10 + (1.2 if kind == "arm" else 1.0), 2)]
                jobs[name] = [name, 205, focus, 4.2, 10]
                jobs[name + "_b"] = [name, 25, focus, 4.2, 10]
    # antes / después en la cadera y el hombro (muñón vanilla del mod principal frente al de Tomb)
    for kind, stump, masks, model in (("hip", "Amputation_Right_UpperLeg_%s" % sex, (9, 10), "mechLegThigh_R"),
                                     ("shoulder", "ArmStumpProst_Right_UpperArm_%s" % sex, (5, 6), "normalArmUpper_R")):
        body = TP.tomb_body(sex, masks)
        for tag, st, pr in (("antes", vanilla_stump(stump, sex), TP.prost(model, sex)), ("despues", tomb_stump(stump, sex), prost_sub(model, sex))):
            name = "tshow_%s_%s_%s" % (sx, kind, tag)
            P.export(name, [body, st, pr])
            top = np.asarray(pr["v"]); top = top[top[:, 1] > top[:, 1].max() - 0.05].mean(0)
            focus = [round(top[0] * 10, 2), round(-top[2] * 10, 2), round(top[1] * 10, 2)]
            jobs[name] = [name, 205, focus, 2.6, 12]
            jobs[name + "_b"] = [name, 25, focus, 2.6, 12]
json.dump(jobs, open(os.path.join("out", "scene", "tomb_jobs.json"), "w"))
print(sum(1 for k in jobs if k.startswith("tshow_")), "vistas tshow")
