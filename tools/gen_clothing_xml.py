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

def write(name, male, female, textures, masks=(), static=False, alt=None):
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
    for m in masks: L.append("    <m_Masks>%d</m_Masks>" % m)
    for t in textures: L.append("    <textureChoices>%s</textureChoices>" % t)
    L.append("</clothingItem>")
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    return guid

def P(*parts): return BS.join(parts)

SIDE = {"L": "Left", "R": "Right"}
MASKS = {"Foot": {"L": (8,), "R": (10,)}, "LowerLeg": {"L": (7, 8), "R": (9, 10)}, "UpperLeg": {"L": (7, 8), "R": (9, 10)}}
for part in ("Foot", "LowerLeg", "UpperLeg"):
    for side in ("L", "R"):
        tex = []
        for suf in ("_b", "_hairy_b", "_c", "_hairy_c"):
            for i in range(1, 6): tex.append(P("Amputations", "Human", part, "skin%02d%s" % (i, suf)))
        for suf in ("_b", "_c"):
            for i in range(1, 6): tex.append(P("Amputations", "Human", part, "skinF%02d%s" % (i, suf)))
        for z in range(1, 5):
            for l in range(1, 4): tex.append(P("Amputations", "Zombie", part, "z_skin%02d_l%d" % (z, l)))
        write("Amputation_%s_%s" % (part, side), P("Amputation", "Amputation_%s_%s_Male" % (SIDE[side], part)),
              P("Amputation", "Amputation_%s_%s_Female" % (SIDE[side], part)), tex, MASKS[part][side])

# prótesis: tier x nivel de amputación (mismo nombre de ítem con sufijo Wrist / Ankle / Thigh)
PROST = {"PegArm": ("pegArm", ["", "Wrist"]), "HookArm": ("hookArm", ["", "Wrist"]), "NormalArm": ("normalArm", ["", "Wrist"]), "MedicalArm": ("medicalArm", ["", "Wrist"]),
         "PegLeg": ("pegLeg", ["", "Ankle", "Thigh"]), "MechLeg": ("mechLeg", ["", "Ankle", "Thigh"]), "MedicalLeg": ("medicalLeg", ["", "Ankle", "Thigh"]),
         "ChainsawArm": ("chainsawArm", ["", "Wrist"])}
ONE_SIDE = {"ChainsawArm": "R"}      # brazo motosierra: sólo derecho
for side in ("L", "R"):
    for tier, (model, levels) in PROST.items():
        if ONE_SIDE.get(tier, side) != side: continue
        for lvl in levels:
            item = "Prost_%s%s_%s" % (tier, lvl, side)
            write(item, P("Prosthesis", "%s%s_%s_M" % (model, lvl, side)), P("Prosthesis", "%s%s_%s_F" % (model, lvl, side)), [P("Prosthesis", model)],
                  alt=(P("Prosthesis", "%s%sUnder_%s_M" % (model, lvl, side)), P("Prosthesis", "%s%sUnder_%s_F" % (model, lvl, side))))
    write("Surg_Leg_Tourniquet_%s" % side, P("Surgery", "TourniquetLeg_%s_M" % side), P("Surgery", "TourniquetLeg_%s_F" % side), [P("Surgery", "tourniquetLeg")])

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
