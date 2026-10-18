"""Genera TOC_prosthesis_items.txt con todas las variantes por nivel de amputación y añade sus nombres
a ItemName.json (EN/ES). Las variantes comparten nombre, icono, modelo de suelo y estadísticas: sólo
cambia el modelo vestido. El juego las intercambia solo al ponérselas (ProsthesisHandler.FitToStump)."""
import os, sys, json, re
MOD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")

ARM_LEVELS = ["", "Wrist", "Upper"]       # antebrazo (base), mano, brazo (por encima del codo, 3.1.0)
LEG_LEVELS = ["", "Ankle", "Thigh"]       # pantorrilla (base), pie, muslo

# tier: (icono, modelo de suelo, estadísticas)
ARMS = {
    "PegArm":     ("PegArm",     "prostheticArmPeg",     dict(Weight="1.0", CombatSpeedModifier="0.8",  ConditionMax=15, ConditionLowerChanceOneIn=20, BloodLocation="UpperArms;LowerArms")),
    "HookArm":    ("HookArm",    "prostheticArmHook",    dict(Weight="1.5", CombatSpeedModifier="0.9",  ConditionMax=20, ConditionLowerChanceOneIn=30, BloodLocation="UpperArms;UpperBody")),
    "NormalArm":  ("MechArm",    "prostheticArm",        dict(Weight="2",   CombatSpeedModifier="0.95", ConditionMax=30, ConditionLowerChanceOneIn=40, BloodLocation="UpperArms;UpperBody")),
    "MedicalArm": ("MedicalArm", "prostheticArmMedical", dict(Weight="1.2", CombatSpeedModifier="1.0",  ConditionMax=40, ConditionLowerChanceOneIn=60, BloodLocation="UpperArms;UpperBody")),
    # brazo motosierra (tipo Ash): sólo derecho (las animaciones de motosierra del juego son diestras)
    "ChainsawArm": ("ChainsawArm", "prostheticArmChainsaw", dict(Weight="4.5", CombatSpeedModifier="0.9", ConditionMax=30, ConditionLowerChanceOneIn=40, BloodLocation="UpperArms;UpperBody")),
    # brazo bayoneta (estilo Merle, 3.2.0): sólo derecho (el juego ataca con la mano principal), chatarra y una hoja
    "KnifeArm": ("KnifeArm", "prostheticArmKnife", dict(Weight="1.8", CombatSpeedModifier="0.95", ConditionMax=25, ConditionLowerChanceOneIn=35, BloodLocation="UpperArms;UpperBody")),
}
SIDES = {"ChainsawArm": ("R",), "KnifeArm": ("R",)}   # tiers que sólo existen de un lado (sin opción de cambiar de lado)
LEGS = {
    "PegLeg":     ("PegLeg",     "prostheticLegPeg",     dict(Weight="2.0", RunSpeedModifier="0.85", ConditionMax=15, ConditionLowerChanceOneIn=20, BloodLocation="LowerLegs")),
    "MechLeg":    ("MechLeg",    "prostheticLegMech",    dict(Weight="3.0", RunSpeedModifier="0.95", ConditionMax=30, ConditionLowerChanceOneIn=40, BloodLocation="LowerLegs")),
    "MedicalLeg": ("MedicalLeg", "prostheticLegMedical", dict(Weight="1.8", RunSpeedModifier="1.0",  ConditionMax=40, ConditionLowerChanceOneIn=60, BloodLocation="LowerLegs")),
}
# 3.3 gama cyber: sólo en el mod de desarrollo (MODULAR=1), como las piezas modulares
if os.environ.get("MODULAR") == "1":
    # corre un 10 % más que una pierna sana (2026-10-17, pedido): la única prótesis que mejora la velocidad
    LEGS["CyberLeg"] = ("CyberLeg", "prostheticLegCyber", dict(Weight="2.2", RunSpeedModifier="1.1", ConditionMax=60, ConditionLowerChanceOneIn=90, BloodLocation="LowerLegs"))
OTHER = {"L": "R", "R": "L"}

def block(name, side, group, icon, ground, st, one_side=False):
    bl = {"arm": "toc:armprost_", "leg": "toc:legprost_", "head": "toc:armhead_"}[group] + side.lower()
    L = ["\titem %s_%s" % (name, side), "\t{",
         "\t\tItemType = base:clothing,", "\t\tDisplayCategory = Prosthesis,",
         "\t\tClothingItem = %s_%s," % (name, side)]
    if not one_side:
        L += ["\t\tClothingItemExtra = %s_%s," % (name, OTHER[side]),
              "\t\tClothingItemExtraOption = InstallProst%s," % ("Right" if side == "L" else "Left"),
              "\t\tclothingExtraSubmenu = InstallProst%s," % ("Left" if side == "L" else "Right")]
    L += ["\t\tBodyLocation = %s," % bl, "\t\tWeight = %s," % st["Weight"]]
    if "CombatSpeedModifier" in st: L.append("\t\tCombatSpeedModifier = %s," % st["CombatSpeedModifier"])
    if "RunSpeedModifier" in st: L.append("\t\tRunSpeedModifier = %s," % st["RunSpeedModifier"])
    L += ["\t\tBloodLocation = %s," % st["BloodLocation"], "\t\tInsulation = 0.0,", "\t\tWindResistance = 0.0,", "\t\tWaterResistance = 0.0,",
          "\t\tCanHaveHoles = false,", "\t\tConditionMax = %d," % st["ConditionMax"], "\t\tConditionLowerChanceOneIn = %d," % st["ConditionLowerChanceOneIn"],
          "\t\tIcon = %s," % icon, "\t\tWorldStaticModel = %s," % ground, "\t}"]
    return "\n".join(L)

out = ["module TOC", "{", "\timports", "\t{", "\t\tBase", "\t}", "",
       "\t/* Prótesis (TOC+). Tiers: PegArm (Woodwork 2) < HookArm (MetalWelding 2) < NormalArm = mecánico (MetalWelding 4) < MedicalArm (botín).",
       "\t   Cada tier existe en variantes por nivel de amputación con el MISMO nombre y estadísticas:",
       "\t   brazos: <Tier>Arm (antebrazo) / <Tier>ArmWrist (mano); piernas: <Tier>Leg (pantorrilla) / <Tier>LegAnkle (pie) / <Tier>LegThigh (muslo).",
       "\t   Las recetas y el botín dan la variante base; al vestirla, ProsthesisHandler.FitToStump la cambia por la del muñón.",
       "\t   CombatSpeedModifier nunca > 1: una prótesis es como mucho tan buena como un brazo. RunSpeedModifier es vanilla: la pata de palo frena de verdad. */", ""]
names = []
for tier, (icon, ground, st) in ARMS.items():
    sides = SIDES.get(tier, ("L", "R"))
    for lvl in ARM_LEVELS:
        for side in sides:
            out.append(block("Prost_" + tier.replace("Arm", "Arm" + lvl), side, "arm", icon, ground, st, one_side=len(sides) == 1)); out.append("")
            names.append(("TOC.Prost_%s_%s" % (tier.replace("Arm", "Arm" + lvl), side), "TOC.Prost_%s_%s" % (tier, side)))
# 3.3 modular (DISENO_3.3_MODULAR.md): sólo con MODULAR=1 en el entorno (el mod de desarrollo); el mod base no los lleva.
# Bases: por nivel, como los brazos; cabezales: un ítem por lado en toc:armhead_X (motosierra y bayoneta sólo derechas).
MODULAR = os.environ.get("MODULAR") == "1"
BASES = {
    "BaseWood":  ("BaseWood",  "prostheticBaseWood",  dict(Weight="0.8", CombatSpeedModifier="0.85", ConditionMax=15, ConditionLowerChanceOneIn=20, BloodLocation="UpperArms;LowerArms")),
    "BaseScrap": ("BaseScrap", "prostheticBaseScrap", dict(Weight="1.3", CombatSpeedModifier="0.92", ConditionMax=22, ConditionLowerChanceOneIn=30, BloodLocation="UpperArms;UpperBody")),
    "BaseMech":  ("BaseMech",  "prostheticBaseMech",  dict(Weight="1.6", CombatSpeedModifier="0.97", ConditionMax=30, ConditionLowerChanceOneIn=40, BloodLocation="UpperArms;UpperBody")),
    "BaseMed":   ("BaseMed",   "prostheticBaseMed",   dict(Weight="1.0", CombatSpeedModifier="1.0",  ConditionMax=40, ConditionLowerChanceOneIn=60, BloodLocation="UpperArms;UpperBody")),
    "BaseCyber": ("BaseCyber", "prostheticBaseCyber", dict(Weight="1.2", CombatSpeedModifier="1.0",  ConditionMax=60, ConditionLowerChanceOneIn=90, BloodLocation="UpperArms;UpperBody")),
}
HEADS = {
    "HeadKnob":     ("HeadKnob",     "prostheticHeadKnob",     dict(Weight="0.3", ConditionMax=15, ConditionLowerChanceOneIn=20, BloodLocation="LowerArms")),
    "HeadHook":     ("HeadHook",     "prostheticHeadHook",     dict(Weight="0.4", ConditionMax=25, ConditionLowerChanceOneIn=30, BloodLocation="LowerArms")),
    "HeadMechHand": ("HeadMechHand", "prostheticHeadMechHand", dict(Weight="0.5", ConditionMax=30, ConditionLowerChanceOneIn=40, BloodLocation="LowerArms")),
    "HeadMedHand":  ("HeadMedHand",  "prostheticHeadMedHand",  dict(Weight="0.3", ConditionMax=40, ConditionLowerChanceOneIn=60, BloodLocation="LowerArms")),
    "HeadCyberHand": ("HeadCyberHand", "prostheticHeadCyberHand", dict(Weight="0.4", ConditionMax=60, ConditionLowerChanceOneIn=90, BloodLocation="LowerArms")),
    "HeadChainsaw": ("HeadChainsaw", "prostheticHeadChainsaw", dict(Weight="3.0", ConditionMax=30, ConditionLowerChanceOneIn=40, BloodLocation="LowerArms")),
    "HeadBayonet":  ("HeadBayonet",  "prostheticHeadBayonet",  dict(Weight="0.5", ConditionMax=25, ConditionLowerChanceOneIn=35, BloodLocation="LowerArms")),
}
HEAD_SIDES = {"HeadChainsaw": ("R",), "HeadBayonet": ("R",)}
if MODULAR:
    for tier, (icon, ground, st) in BASES.items():
        for lvl in ARM_LEVELS:
            for side in ("L", "R"):
                nm = "Prost_%s%s" % (tier, lvl)
                out.append(block(nm, side, "arm", icon, ground, st)); out.append("")
                names.append(("TOC.%s_%s" % (nm, side), "TOC.Prost_%s_%s" % (tier, side)))
    for tier, (icon, ground, st) in HEADS.items():
        sides = HEAD_SIDES.get(tier, ("L", "R"))
        for side in sides:
            out.append(block("Prost_" + tier, side, "head", icon, ground, st, one_side=len(sides) == 1)); out.append("")
            names.append(("TOC.Prost_%s_%s" % (tier, side), "TOC.Prost_%s_%s" % (tier, side)))
for tier, (icon, ground, st) in LEGS.items():
    for lvl in LEG_LEVELS:
        for side in ("L", "R"):
            out.append(block("Prost_" + tier.replace("Leg", "Leg" + lvl), side, "leg", icon, ground, st)); out.append("")
            names.append(("TOC.Prost_%s_%s" % (tier.replace("Leg", "Leg" + lvl), side), "TOC.Prost_%s_%s" % (tier, side)))
out.append("}")
open(os.path.join(MOD, "scripts", "TOC_prosthesis_items.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("items:", len(names))

# nombres: la variante hereda el nombre de la base
for lang in ("EN", "ES", "DE", "FR", "IT", "KO", "PL", "PTBR", "RU", "TR", "UA"):
    path = os.path.join(MOD, "lua", "shared", "Translate", lang, "ItemName.json")
    data = json.load(open(path, encoding="utf-8"))
    added = 0
    for full, base in names:
        if full not in data and base in data:
            data[full] = data[base]; added += 1
    json.dump(data, open(path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=4)
    print(lang, "nombres añadidos:", added)

# reparaciones: todas las variantes de un tier se reparan igual
FIX = {"PegArm": ["Base.Woodglue=2; Woodwork=2", "Base.DuctTape=2"], "PegLeg": ["Base.Woodglue=2; Woodwork=2", "Base.DuctTape=2"],
       "HookArm": ["Base.WeldingRods=2; MetalWelding=2", "Base.DuctTape=3"], "NormalArm": ["Base.WeldingRods=2; MetalWelding=3", "Base.DuctTape=3"],
       "MechLeg": ["Base.WeldingRods=2; MetalWelding=3", "Base.DuctTape=3"],
       "ChainsawArm": ["Base.EngineParts=2; Mechanics=3", "Base.WeldingRods=2; MetalWelding=4", "Base.DuctTape=4"],
       "KnifeArm": ["Base.WeldingRods=1; MetalWelding=2", "Base.DuctTape=2", "Base.LeatherStrips=2"],
       "MedicalArm": ["Base.DuctTape=3; Mechanics=3", "Base.Screws=4; Mechanics=2"], "MedicalLeg": ["Base.DuctTape=3; Mechanics=3", "Base.Screws=4; Mechanics=2"],
       # 3.3 modular
       "BaseWood": ["Base.Woodglue=2; Woodwork=2", "Base.DuctTape=2"], "BaseScrap": ["Base.WeldingRods=1; MetalWelding=2", "Base.DuctTape=2", "Base.LeatherStrips=2"],
       "BaseMech": ["Base.WeldingRods=2; MetalWelding=3", "Base.Screws=4; Mechanics=2"], "BaseMed": ["Base.DuctTape=3; Mechanics=3", "Base.Screws=4; Mechanics=2"],
       "HeadKnob": ["Base.Woodglue=1; Woodwork=1", "Base.DuctTape=1"], "HeadHook": ["Base.WeldingRods=1; MetalWelding=2", "Base.DuctTape=2"],
       "HeadMechHand": ["Base.Screws=4; Mechanics=3", "Base.DuctTape=3"], "HeadMedHand": ["Base.DuctTape=3; Mechanics=3", "Base.Screws=4; Mechanics=2"],
       "HeadChainsaw": ["Base.EngineParts=2; Mechanics=3", "Base.WeldingRods=2; MetalWelding=4", "Base.DuctTape=4"],
       "HeadBayonet": ["Base.WeldingRods=1; MetalWelding=2", "Base.DuctTape=2"],
       "BaseCyber": ["Base.ElectronicsScrap=3; Electricity=5", "Base.WeldingRods=2; MetalWelding=5"],
       "CyberLeg": ["Base.ElectronicsScrap=3; Electricity=5", "Base.WeldingRods=2; MetalWelding=5"],
       "HeadCyberHand": ["Base.ElectronicsScrap=3; Electricity=5", "Base.ElectricWire=2; Electricity=4"]}
fx = ["module TOC", "{", "	imports", "	{", "		Base", "	}", "	/* Reparación de prótesis (TOC+): madera con cola o cinta; metal con varillas de soldar o cinta; médicas con mecánica. Generado por tools/gen_prosthesis_items.py */"]
for full, base in names:
    tier = base.split("Prost_")[1].rsplit("_", 1)[0]
    item = full.split("TOC.")[1]
    fx += ["	fixing Fix TOC %s" % item, "	{", "		Require = %s," % full] + ["		Fixer = %s," % f for f in FIX[tier]] + ["	}"]
fx += ["	fixing Fix TOC Crutch", "	{", "		Require = TOC.Crutch,", "		Fixer = Base.Woodglue=2; Woodwork=1,", "		Fixer = Base.DuctTape=2,", "	}",
       "	fixing Fix TOC BoneSaw", "	{", "		Require = TOC.BoneSaw,", "		Fixer = Base.WeldingRods=1; MetalWelding=2,", "	}", "}"]
open(os.path.join(MOD, "scripts", "TOC_fixing.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(fx) + "\n")
print("fixing:", len(names) + 2)
