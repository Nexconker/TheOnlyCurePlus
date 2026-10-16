"""Genera los clothingItems XML nuevos de TOC+ y regenera fileGuidTable.xml con TODOS los XML del mod."""
import os, re, uuid, sys
MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
CI = os.path.join(MOD, "clothing", "clothingItems")
os.makedirs(CI, exist_ok=True)
BS = "\\"   # separador de rutas de modelo/textura dentro del XML (como en los XML vanilla)

def existing_guid(path):
    if os.path.exists(path):
        m = re.search(r"<m_GUID>([^<]+)</m_GUID>", open(path, encoding="utf-8", errors="ignore").read())
        if m: return m.group(1)
    return str(uuid.uuid4())

def write(name, male, female, textures, masks=(), static=False, alt=None, own_atlas=False):
    path = os.path.join(CI, name + ".xml")
    guid = existing_guid(path)
    L = ['<?xml version="1.0" encoding="utf-8"?>', "<clothingItem>",
         "    <m_MaleModel>%s</m_MaleModel>" % male, "    <m_FemaleModel>%s</m_FemaleModel>" % female]
    if alt:
        # modelo alternativo: el juego lo usa cuando hay una prenda en una ubicación marcada con setAltModel
        L += ["    <m_AltMaleModel>%s</m_AltMaleModel>" % alt[0], "    <m_AltFemaleModel>%s</m_AltFemaleModel>" % alt[1]]
    L += [
         "    <m_GUID>%s</m_GUID>" % guid, "    <m_Static>%s</m_Static>" % ("true" if static else "false"),
         "    <m_AllowRandomHue>false</m_AllowRandomHue>", "    <m_AllowRandomTint>false</m_AllowRandomTint>"]
    if own_atlas:
        # el juego aplica a cada prenda las máscaras de las que van por encima (ModelInstanceTextureCreator), pensadas
        # para texturas con el UV del cuerpo. En un atlas propio recortan trozos al azar: con los muñones de pierna
        # puestos (sus máscaras de pierna) la prótesis de brazo perdía el encaje. "none" = como mochilas y cinturones.
        L.append("    <m_MasksFolder>none</m_MasksFolder>")
    for m in masks: L.append("    <m_Masks>%d</m_Masks>" % m)
    for t in textures: L.append("    <textureChoices>%s</textureChoices>" % t)
    L.append("</clothingItem>")
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    return guid

def P(*parts): return BS.join(parts)

SIDE = {"L": "Left", "R": "Right"}
MASKS = {"Foot": {"L": (8,), "R": (10,)}, "LowerLeg": {"L": (7, 8), "R": (9, 10)}, "UpperLeg": {"L": (7, 8), "R": (9, 10)}}

def stump_textures(folder):
    """42 entradas, el orden que esperan ItemsController.GetAmputationTexturesIndex y ZombieStumps.GetTextureIndex:
    20 masculinas (tono x vello x sangrante/cicatrizada), 10 femeninas, 12 de zombi."""
    tex = []
    for suf in ("_b", "_hairy_b", "_c", "_hairy_c"):
        for i in range(1, 6): tex.append(P("Amputations", "Human", folder, "skin%02d%s" % (i, suf)))
    for suf in ("_b", "_c"):
        for i in range(1, 6): tex.append(P("Amputations", "Human", folder, "skinF%02d%s" % (i, suf)))
    for z in range(1, 5):
        for l in range(1, 4): tex.append(P("Amputations", "Zombie", folder, "z_skin%02d_l%d" % (z, l)))
    return tex

for part in ("Foot", "LowerLeg", "UpperLeg"):
    for side in ("L", "R"):
        write("Amputation_%s_%s" % (part, side), P("Amputation", "Amputation_%s_%s_Male" % (SIDE[side], part)),
              P("Amputation", "Amputation_%s_%s_Female" % (SIDE[side], part)), stump_textures(part), MASKS[part][side])

# brazos (3.1.0): muñones hechos del propio cuerpo (tools/make_arm_stumps.py) en lugar de los FBX del TOC original, que
# rehacían el hombro entero y dejaban una raya oscura en la costura. Son copias del cuerpo con la herida en la misma
# zona libre del UV que las piernas, así que usan las MISMAS texturas (carpeta LowerLeg) y el mismo orden de 42.
ARM_MASKS = {"Hand": {"L": (4,), "R": (6,)}, "ForeArm": {"L": (3, 4), "R": (5, 6)}, "UpperArm": {"L": (3, 4), "R": (5, 6)}}
for part in ("Hand", "ForeArm", "UpperArm"):
    for side in ("L", "R"):
        # alternativo = con prótesis puesta (BodyLocations: setAltModel(ArmProst, Arm)): el brazo cortado bajo el borde
        # del encaje, sin piel dentro que pueda asomar (tools/make_arm_stumps.py: build_prost_variants)
        # (sólo antebrazo y brazo: ahí la amputación ya oculta el brazo entero. En la mano el antebrazo es el del cuerpo y
        # tiene que seguir visible: las camisas de manga larga son textura pintada sobre él)
        # (mano desde 2026-10-15: su alternativo es el muñón cortado dentro del brazal; antes asomaba una pestaña de piel)
        alt = (P("Amputation", "ArmStumpProst_%s_%s_Male" % (SIDE[side], part)), P("Amputation", "ArmStumpProst_%s_%s_Female" % (SIDE[side], part)))
        write("Amputation_%s_%s" % (part, side), P("Amputation", "ArmStump_%s_%s_Male" % (SIDE[side], part)),
              P("Amputation", "ArmStump_%s_%s_Female" % (SIDE[side], part)), stump_textures("LowerLeg"), ARM_MASKS[part][side], alt=alt)

# prótesis: tier x nivel de amputación (mismo nombre de ítem con sufijo Wrist / Ankle / Thigh)
PROST = {"PegArm": ("pegArm", ["", "Wrist", "Upper"]), "HookArm": ("hookArm", ["", "Wrist", "Upper"]), "NormalArm": ("normalArm", ["", "Wrist", "Upper"]), "MedicalArm": ("medicalArm", ["", "Wrist", "Upper"]),
         "PegLeg": ("pegLeg", ["", "Ankle", "Thigh"]), "MechLeg": ("mechLeg", ["", "Ankle", "Thigh"]), "MedicalLeg": ("medicalLeg", ["", "Ankle", "Thigh"]),
         "ChainsawArm": ("chainsawArm", ["", "Wrist", "Upper"])}
ONE_SIDE = {"ChainsawArm": "R"}      # brazo motosierra: sólo derecho
for side in ("L", "R"):
    for tier, (model, levels) in PROST.items():
        if ONE_SIDE.get(tier, side) != side: continue
        for lvl in levels:
            item = "Prost_%s%s_%s" % (tier, lvl, side)
            write(item, P("Prosthesis", "%s%s_%s_M" % (model, lvl, side)), P("Prosthesis", "%s%s_%s_F" % (model, lvl, side)), [P("Prosthesis", model)],
                  alt=(P("Prosthesis", "%s%sUnder_%s_M" % (model, lvl, side)), P("Prosthesis", "%s%sUnder_%s_F" % (model, lvl, side))), own_atlas=True)
    write("Surg_Leg_Tourniquet_%s" % side, P("Surgery", "TourniquetLeg_%s_M" % side), P("Surgery", "TourniquetLeg_%s_F" % side), [P("Surgery", "tourniquetLeg")], own_atlas=True)
    # torniquete de brazo: el del TOC original (también atlas propio), sólo se le añade la carpeta de máscaras
    tq = os.path.join(CI, "Surg_Arm_Tourniquet_%s.xml" % side)
    if os.path.exists(tq):
        t = open(tq, encoding="utf-8").read()
        if "<m_MasksFolder>" not in t:
            t = t.replace("    <textureChoices>", "    <m_MasksFolder>none</m_MasksFolder>\n    <textureChoices>", 1)
            open(tq, "w", encoding="utf-8", newline="\n").write(t)

rows = []
for f in sorted(os.listdir(CI)):
    if f.lower().endswith(".xml"):
        rows.append((f, existing_guid(os.path.join(CI, f))))
L = ['<?xml version="1.0" encoding="utf-8"?>', "<fileGuidTable>"]
for f, g in rows:
    L += ["    <files>", "        <path>media/clothing/clothingItems/%s</path>" % f, "        <guid>%s</guid>" % g, "    </files>"]
L.append("</fileGuidTable>")
open(os.path.join(MOD, "fileGuidTable.xml"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("xml:", len(rows))
