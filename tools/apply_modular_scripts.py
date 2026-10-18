"""3.3 modular, en el mod de DESARROLLO (TOC_MEDIA): recetas por pieza (bases y cabezales) en lugar de las de brazo
completo, modelos de suelo de las piezas y botín de hospital con bases y cabezales médicos. Idempotente.
Uso: TOC_MEDIA=...TheOnlyCurePlusDev\\42\\media python apply_modular_scripts.py"""
import os, re
MEDIA = os.environ.get("TOC_MEDIA")
assert MEDIA and "Dev" in MEDIA, "sólo para el mod de desarrollo (TOC_MEDIA=...TheOnlyCurePlusDev...)"

# ---- recetas
p = os.path.join(MEDIA, "scripts", "TOC_recipes.txt")
s = open(p, encoding="utf-8").read()
OLD = ["Craft_Prosthetic_PegArm", "Craft_Prosthetic_Hook", "Craft_Prosthetic_Arm", "Craft_Prosthetic_ChainsawArm", "Craft_Prosthetic_KnifeArm"]
for name in OLD:
    m = re.search(r"\n\tcraftRecipe %s\n\t\{.*?\n\t\}\n" % re.escape(name), s, re.S)
    if m: s = s[:m.start()] + "\n" + s[m.end():]

def recipe(name, action, time, cat, skills, xp, inputs, outputs, comment):
    L = ["\t/* %s */" % comment, "\tcraftRecipe %s" % name, "\t{", "\t\ttimedAction = %s," % action, "\t\tTime = %d," % time,
         "\t\tTags = InHandCraft,", "\t\tcategory = %s," % cat, "\t\tNeedToBeLearn = false,"]
    if skills: L.append("\t\tSkillRequired = %s," % skills)
    if xp: L.append("\t\txpAward = %s," % xp)
    L += ["\t\tinputs", "\t\t{"] + ["\t\t\t%s," % i for i in inputs] + ["\t\t}", "\t\toutputs", "\t\t{"] + ["\t\t\titem 1 %s," % o for o in outputs] + ["\t\t}", "\t}", ""]
    return "\n".join(L)

R = []
R.append(recipe("Craft_Prosthetic_BaseWood", "Making", 160, "Carpentry", "Woodwork:2", "Woodwork:15",
    ["item 2 [Base.Plank]", "item 1 [Base.LeatherStrips;Base.LeatherStripsDirty]", "item 4 [Base.Nails]",
     "item 1 tags[base:hammer] mode:keep flags[MayDegradeVeryLight]", "item 1 tags[base:saw] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_BaseWood_L"], "3.3 modular: base de madera (encaje de cuero y carcasa de madera)"))
R.append(recipe("Craft_Prosthetic_HeadKnob", "Making", 60, "Carpentry", "Woodwork:1", "Woodwork:5",
    ["item 1 [Base.Plank]", "item 1 tags[base:saw] mode:keep flags[MayDegradeLight]"], ["TOC.Prost_HeadKnob_L"], "cabezal: pomo de madera"))
R.append(recipe("Craft_Prosthetic_BaseScrap", "BuildMetalStructureSmall", 140, "Metalworking", "MetalWelding:2", "MetalWelding:20",
    ["item 1 [Base.SmallSheetMetal;Base.ScrapMetal;Base.SheetMetal]", "item 3 [Base.LeatherStrips;Base.LeatherStripsDirty]", "item 2 [Base.DuctTape]",
     "item 2 [Base.BlowTorch] flags[DontRecordInput]", "item 1 [Base.WeldingRods] flags[DontRecordInput]", "item 1 tags[base:hammer] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_BaseScrap_L"], "base de chatarra (brazal de cuero y carcasa de chapa)"))
R.append(recipe("Craft_Prosthetic_HeadHook", "BuildMetalStructureSmall", 80, "Metalworking", "MetalWelding:2", "MetalWelding:15",
    ["item 1 [Base.MetalPipe]", "item 2 [Base.BlowTorch] flags[DontRecordInput]", "item 1 [Base.WeldingRods] flags[DontRecordInput]"],
    ["TOC.Prost_HeadHook_L"], "cabezal: gancho"))
R.append(recipe("Craft_Prosthetic_BaseMech", "BuildMetalStructureSmall", 200, "Metalworking", "MetalWelding:4", "MetalWelding:40",
    ["item 3 [Base.MetalPipe]", "item 1 [Base.SmallSheetMetal;Base.SheetMetal]", "item 4 [Base.Screws]",
     "item 3 [Base.BlowTorch] flags[DontRecordInput]", "item 3 [Base.WeldingRods] flags[DontRecordInput]", "item 1 tags[base:screwdriver] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_BaseMech_L"], "base mecánica: armazón hueco con pistón"))
R.append(recipe("Craft_Prosthetic_HeadMechHand", "BuildMetalStructureSmall", 160, "Metalworking", "MetalWelding:4;Mechanics:2", "MetalWelding:25;Mechanics:15",
    ["item 1 [Base.MetalPipe]", "item 1 [Base.SmallSheetMetal;Base.SheetMetal]", "item 6 [Base.Screws]",
     "item 1 [Base.BlowTorch] flags[DontRecordInput]", "item 1 [Base.WeldingRods] flags[DontRecordInput]", "item 1 tags[base:screwdriver] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_HeadMechHand_L"], "cabezal: mano mecánica (se cierra al agarrar)"))
R.append(recipe("Craft_Prosthetic_HeadChainsaw", "Welding", 360, "Metalworking", "MetalWelding:5;Mechanics:4", "MetalWelding:50;Mechanics:40",
    ["item 4 [Base.EngineParts]", "item 2 [Base.SmallSheetMetal]", "item 1 [Base.MetalPipe]", "item 6 [Base.Screws]",
     "item 1 [Base.Saw;Base.GardenSaw;Base.SmallSaw;Base.CrudeSaw]", "item 4 [Base.BlowTorch] flags[DontRecordInput]", "item 3 [Base.WeldingRods] flags[DontRecordInput]",
     "item 1 tags[base:weldingmask] mode:keep", "item 1 tags[base:screwdriver] mode:keep flags[MayDegradeLight]", "item 1 tags[base:wrench] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_HeadChainsaw_R"], "cabezal: motosierra estilo Ash (sólo derecho, pide base de metal; sale con el depósito vacío)"))
R.append(recipe("Craft_Prosthetic_HeadBayonet", "BuildMetalStructureSmall", 90, "Metalworking", "MetalWelding:2", "MetalWelding:15",
    ["item 1 [Base.HuntingKnife;Base.KitchenKnife;Base.FlintKnife;Base.KnifeButterfly;Base.LargeKnife]", "item 1 [Base.ScrapMetal;Base.SmallSheetMetal]",
     "item 1 [Base.DuctTape]", "item 1 [Base.BlowTorch] flags[DontRecordInput]", "item 1 tags[base:hammer] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_HeadBayonet_R"], "cabezal: bayoneta estilo Merle (sólo derecho)"))
# gama cyber (2026-10-17: "más futurista y difícil de craftear"): mucha habilidad en tres ramas y electrónica rara
R.append(recipe("Craft_Prosthetic_BaseCyber", "Welding", 600, "Metalworking", "MetalWelding:7;Electricity:6;Mechanics:5",
    "MetalWelding:60;Electricity:60;Mechanics:40",
    ["item 2 [Base.SheetMetal]", "item 2 [Base.Aluminum]", "item 1 [Base.CarBatteryCharger]", "item 1 [Base.Amplifier]",
     "item 6 [Base.ElectronicsScrap]", "item 4 [Base.ElectricWire]", "item 10 [Base.Screws]",
     "item 5 [Base.BlowTorch] flags[DontRecordInput]", "item 4 [Base.WeldingRods] flags[DontRecordInput]",
     "item 1 tags[base:weldingmask] mode:keep", "item 1 tags[base:screwdriver] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_BaseCyber_L"], "gama cyber: base de placas blindadas con músculos de cable (tier 5)"))
R.append(recipe("Craft_Prosthetic_HeadCyberHand", "MakingElectrical", 480, "Electrical", "Electricity:7;Mechanics:6;MetalWelding:4",
    "Electricity:60;Mechanics:50",
    ["item 1 [Base.MotionSensor]", "item 1 [Base.Pager;Base.Calculator;Base.Remote;Base.RemoteCraftedV3]", "item 1 [Base.Aluminum]",
     "item 5 [Base.ElectronicsScrap]", "item 3 [Base.ElectricWire]", "item 12 [Base.Screws]",
     "item 2 [Base.BlowTorch] flags[DontRecordInput]", "item 1 tags[base:screwdriver] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_HeadCyberHand_L"], "gama cyber: mano de dedos articulados por segmentos"))
R.append(recipe("Craft_Prosthetic_CyberLeg", "Welding", 660, "Metalworking", "MetalWelding:7;Electricity:6;Mechanics:6",
    "MetalWelding:60;Electricity:60;Mechanics:50",
    ["item 3 [Base.SheetMetal]", "item 2 [Base.Aluminum]", "item 1 [Base.CarBatteryCharger]", "item 1 [Base.MotionSensor]",
     "item 8 [Base.ElectronicsScrap]", "item 5 [Base.ElectricWire]", "item 14 [Base.Screws]",
     "item 6 [Base.BlowTorch] flags[DontRecordInput]", "item 5 [Base.WeldingRods] flags[DontRecordInput]",
     "item 1 tags[base:weldingmask] mode:keep", "item 1 tags[base:screwdriver] mode:keep flags[MayDegradeLight]",
     "item 1 tags[base:wrench] mode:keep flags[MayDegradeLight]"],
    ["TOC.Prost_CyberLeg_L"], "gama cyber: pierna blindada con actuadores en rodilla y tobillo (tier 5, no modular)"))
HEADER = "\n\t/************* 3.3: prótesis de brazo modulares (base + cabezal) *******************/\n"
block = HEADER + "\n".join(R)
# idempotente: quitar el bloque anterior (cabecera y cada receta con su comentario) y volver a ponerlo entero
s = s.replace(HEADER, "\n")
for r in R:
    name = re.search(r"craftRecipe (\S+)", r).group(1)
    m = re.search(r"\n\t/\*[^\n]*\*/\n\tcraftRecipe %s\n\t\{.*?\n\t\}\n" % re.escape(name), s, re.S)
    if m: s = s[:m.start()] + "\n" + s[m.end():]
s = re.sub(r"\n{3,}", "\n\n", s)
i = s.index("\t/************* Prosthetic legs (TOC+) *******************/")
s = s[:i] + block.lstrip("\n") + "\n" + s[i:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("recetas:", len(R), "nuevas; antiguas quitadas:", ", ".join(OLD))

# ---- modelos de suelo
p = os.path.join(MEDIA, "scripts", "TOC_models.txt")
s = open(p, encoding="utf-8").read()
GROUND = {"BaseWood": ("baseWood", "pegArm"), "BaseScrap": ("baseScrap", "knifeArm"), "BaseMech": ("baseMech", "normalArm"), "BaseMed": ("baseMed", "medicalArm"),
          "HeadKnob": ("headKnob", "pegArm"), "HeadHook": ("headHook", "hookArm"), "HeadMechHand": ("headMechHand", "normalArm"),
          "HeadMedHand": ("headMedHand", "medicalArm"), "HeadChainsaw": ("headChainsaw", "chainsawArm"), "HeadBayonet": ("headBayonet", "knifeArm"),
          "BaseCyber": ("baseCyber", "cyberArm"), "HeadCyberHand": ("headCyberHand", "cyberArm"), "LegCyber": ("cyberLeg", "cyberArm")}
add = ""
for nm, (mesh, tex) in GROUND.items():
    if "model prosthetic%s\n" % nm in s: continue
    add += "    model prosthetic%s\n\t{\n\t\tmesh = Prosthesis/%s_Ground,\n\t\ttexture = Prosthesis/%s,\n\t}\n" % (nm, mesh, tex)
if add:
    i = s.index("    model TOC_Invisible")
    s = s[:i] + "    /* 3.3 modular: piezas en el suelo */\n" + add + s[i:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("modelos de suelo añadidos:", add.count("model "))

# ---- botín
p = os.path.join(MEDIA, "lua", "server", "TOC", "Distributions.lua")
s = open(p, encoding="utf-8").read()
s = s.replace('"TOC.Prost_HookArm_L", 3, "TOC.Prost_NormalArm_L", 2, "TOC.Prost_MedicalArm_L", 1,',
              '"TOC.Prost_BaseScrap_L", 2, "TOC.Prost_HeadHook_L", 3, "TOC.Prost_BaseMech_L", 2, "TOC.Prost_HeadMechHand_L", 2, "TOC.Prost_BaseMed_L", 1, "TOC.Prost_HeadMedHand_L", 1,')
s = s.replace('"TOC.Prost_MedicalArm_L", 2, "TOC.Prost_MedicalLeg_L", 2,', '"TOC.Prost_BaseMed_L", 2, "TOC.Prost_HeadMedHand_L", 2, "TOC.Prost_MedicalLeg_L", 2,')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("botín:", "Prost_MedicalArm" not in s and "ok" or "QUEDAN REFERENCIAS ANTIGUAS")
