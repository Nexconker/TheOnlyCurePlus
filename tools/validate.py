"""Validador estático de TOC+ (sin arrancar el juego):
- sintaxis de todos los .lua (lupa / Lua 5.1-ish como Kahlua)
- llaves balanceadas en los scripts .txt
- XML bien formados y modelos/texturas referenciados existentes
- claves getText usadas vs EN
- ítems TOC.* referenciados en Lua/scripts definidos
- modelos (StaticModel / WorldStaticModel / WeaponSprite) definidos en el mod o en vanilla
- iconos Item_<Icon>.png existentes (mod o vanilla)
"""
import os, re, sys, json, glob
from xml.etree import ElementTree as ET

MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
PZ = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media"
errors, warns = [], []

# ---------- Lua syntax
try:
    from lupa import LuaRuntime
    lua = LuaRuntime()
    for path in glob.glob(os.path.join(MOD, "lua", "**", "*.lua"), recursive=True) + glob.glob(os.path.join(MOD, "registries.lua")) + glob.glob(os.path.join(os.path.dirname(MOD), "..", "common", "media", "lua", "**", "*.lua"), recursive=True):
        src = open(path, encoding="utf-8", errors="replace").read()
        try:
            lua.compile(src)
        except Exception as e:
            errors.append("LUA %s: %s" % (os.path.relpath(path, MOD), str(e).splitlines()[0][:200]))
    print("lua files checked")
except ImportError:
    warns.append("lupa not installed: Lua syntax not checked")

# ---------- scripts braces + collect definitions
items, models, recipes, fixings, sounds = set(), set(), set(), set(), set()
script_refs = {"StaticModel": [], "WorldStaticModel": [], "WeaponSprite": [], "Icon": [], "ClothingItem": []}
for path in glob.glob(os.path.join(MOD, "scripts", "*.txt")):
    src = open(path, encoding="utf-8", errors="replace").read()
    src_nc = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    if src_nc.count("{") != src_nc.count("}"):
        errors.append("SCRIPT braces unbalanced in %s (%d vs %d)" % (os.path.basename(path), src_nc.count("{"), src_nc.count("}")))
    module = re.search(r"module\s+(\w+)", src_nc)
    modname = module.group(1) if module else "Base"
    for m in re.finditer(r"^\s*item\s+(\w+)\s*$", src_nc, re.M): items.add(modname + "." + m.group(1))
    for m in re.finditer(r"^\s*model\s+(\w+)\s*$", src_nc, re.M): models.add(m.group(1))
    for m in re.finditer(r"^\s*craftRecipe\s+(\w+)\s*$", src_nc, re.M): recipes.add(m.group(1))
    for m in re.finditer(r"^\s*sound\s+(\w+)\s*\{", src_nc, re.M): sounds.add(m.group(1))
    for key in script_refs:
        for m in re.finditer(r"^\s*%s\s*=\s*([^,]+)," % key, src_nc, re.M):
            script_refs[key].append((os.path.basename(path), m.group(1).strip()))
    # inputs/outputs references
    for m in re.finditer(r"\[([A-Za-z0-9_.;]+)\]", src_nc):
        for ref in m.group(1).split(";"):
            if ref.startswith("TOC."): script_refs.setdefault("recipeItem", []).append((os.path.basename(path), ref))
    for m in re.finditer(r"item\s+\d+\s+(TOC\.\w+)", src_nc):
        script_refs.setdefault("recipeItem", []).append((os.path.basename(path), m.group(1)))
    for m in re.finditer(r"Require\s*=\s*(TOC\.\w+)", src_nc):
        script_refs.setdefault("recipeItem", []).append((os.path.basename(path), m.group(1)))

# vanilla model names + icons
van_models = set()
for path in glob.glob(os.path.join(PZ, "scripts", "generated", "*.txt")) + glob.glob(os.path.join(PZ, "scripts", "generated", "**", "*.txt"), recursive=True):
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in re.finditer(r"^\s*model\s+(\w+)\s*$", src, re.M): van_models.add(m.group(1))
all_models = models | van_models
for key in ("StaticModel", "WorldStaticModel", "WeaponSprite"):
    for f, v in script_refs[key]:
        if v not in all_models: errors.append("MODEL %s=%s not defined (%s)" % (key, v, f))

mod_tex = {os.path.basename(p).lower() for p in glob.glob(os.path.join(MOD, "textures", "*.png"))}
van_tex_dirs = [os.path.join(PZ, "textures"), os.path.join(PZ, "textures", "Item")]
def icon_exists(icon):
    name = ("Item_" + icon + ".png").lower()
    if name in mod_tex: return True
    for d in van_tex_dirs:
        if os.path.exists(os.path.join(d, "Item_" + icon + ".png")): return True
    return None
for f, v in script_refs["Icon"]:
    r = icon_exists(v)
    if r is None: warns.append("ICON %s not found in mod textures (may be in a vanilla texture pack) (%s)" % (v, f))

for f, v in script_refs.get("recipeItem", []):
    if v not in items: errors.append("ITEM %s referenced in %s but not defined" % (v, f))

# model meshes/textures of our models
for path in glob.glob(os.path.join(MOD, "scripts", "TOC_models.txt")):
    src = open(path, encoding="utf-8").read()
    for m in re.finditer(r"model\s+(\w+)\s*\{(.*?)\n\s*\}", src, re.S):
        body = m.group(2)
        mesh = re.search(r"mesh\s*=\s*([^,]+),", body); tex = re.search(r"texture\s*=\s*([^,]+),", body)
        if mesh:
            p = os.path.join(MOD, "models_X", mesh.group(1).strip().replace("/", os.sep))
            if not (os.path.exists(p + ".X") or os.path.exists(p + ".x") or os.path.exists(p + ".fbx") or os.path.exists(p + ".FBX")):
                errors.append("MESH %s missing for model %s" % (mesh.group(1).strip(), m.group(1)))
        if tex:
            p = os.path.join(MOD, "textures", tex.group(1).strip().replace("/", os.sep).replace("\\", os.sep) + ".png")
            if not os.path.exists(p): errors.append("TEXTURE %s missing for model %s" % (tex.group(1).strip(), m.group(1)))

# ---------- clothing XML
ci_dir = os.path.join(MOD, "clothing", "clothingItems")
xml_names = set()
for path in glob.glob(os.path.join(ci_dir, "*.xml")):
    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        errors.append("XML %s: %s" % (os.path.basename(path), e)); continue
    xml_names.add(os.path.splitext(os.path.basename(path))[0])
    for tag in ("m_MaleModel", "m_FemaleModel"):
        el = root.find(tag)
        if el is not None and el.text:
            rel = el.text.strip().replace("\\", os.sep)
            p = os.path.join(MOD, "models_X", rel)
            if not any(os.path.exists(p + ext) for ext in (".X", ".x", ".fbx", ".FBX")):
                errors.append("XML %s: model %s missing" % (os.path.basename(path), el.text))
    for el in root.findall("textureChoices"):
        rel = el.text.strip().replace("\\", os.sep) + ".png"
        p = os.path.join(MOD, "textures", rel)
        pv = os.path.join(PZ, "textures", rel)
        if not os.path.exists(p) and not os.path.exists(pv):
            errors.append("XML %s: texture %s missing" % (os.path.basename(path), el.text))
for f, v in script_refs["ClothingItem"]:
    if v not in xml_names: errors.append("CLOTHING %s has no XML (%s)" % (v, f))
try:
    ET.parse(os.path.join(MOD, "fileGuidTable.xml"))
except Exception as e:
    errors.append("fileGuidTable.xml: %s" % e)

# ---------- translations
def load_json(path):
    txt = open(path, encoding="utf-8").read()
    return json.loads(txt)
en = {}
for f in glob.glob(os.path.join(MOD, "lua", "shared", "Translate", "EN", "*.json")):
    try:
        en.update(load_json(f))
    except Exception as e:
        errors.append("JSON %s: %s" % (os.path.basename(f), e))
for lang in ("ES",):
    for f in glob.glob(os.path.join(MOD, "lua", "shared", "Translate", lang, "*.json")):
        try: load_json(f)
        except Exception as e: errors.append("JSON %s/%s: %s" % (lang, os.path.basename(f), e))
used = set()
lua_src = ""
for path in glob.glob(os.path.join(MOD, "lua", "**", "*.lua"), recursive=True):
    lua_src += open(path, encoding="utf-8", errors="replace").read() + "\n"
for m in re.finditer(r'getText\("([A-Za-z0-9_]+)"\s*[,)]', lua_src): used.add(m.group(1))
for m in re.finditer(r'"((?:IGUI|ContextMenu|Tooltip|UI|Sandbox)_[A-Za-z0-9_]+)"', lua_src): used.add(m.group(1))
dynamic = {
    "ContextMenu_Limb_": ["Hand_L", "ForeArm_L", "UpperArm_L", "Hand_R", "ForeArm_R", "UpperArm_R", "Foot_L", "LowerLeg_L", "UpperLeg_L", "Foot_R", "LowerLeg_R", "UpperLeg_R"],
    "IGUI_TOC_SW_Step_": ["Tourniquet", "Disinfect", "Anesthesia", "Incision", "Bone", "Stitches", "Bandage"],
    "IGUI_TOC_SW_Missing_": ["Tourniquet", "Disinfect", "Anesthesia", "Incision", "Bone", "Stitches", "Bandage"],
    "IGUI_TOC_SW_Tier_": ["Surgical", "Fine", "Coarse", "Crude"],
    "IGUI_TOC_SW_Risk_": ["Low", "Medium", "High", "VeryHigh"],
    "IGUI_TOC_HP_Diag_": ["infected", "clean", "unsure"],
    "IGUI_TOC_Diag_": ["infected", "clean", "unsure", "infected_Maybe", "clean_Maybe", "unsure_Maybe"],
    "IGUI_TOC_Surgery_Result_": ["0", "1", "2"],
    "IGUI_TOC_Cure_": ["cured", "late", "doomed", "none"],
    "IGUI_TOC_Symptom_": ["1", "2", "3", "4"],
}
for pre, sufs in dynamic.items():
    for s in sufs: used.add(pre + s)
vanilla_keys = ("ContextMenu_Equip_Primary", "ContextMenu_Equip_Secondary", "ContextMenu_Equip_Two_Hands", "ContextMenu_RemoveBrokenGlass",
                "ContextMenu_Add_escape_rope_sheet", "ContextMenu_Add_escape_rope", "ContextMenu_Remove_escape_rope", "ContextMenu_Barricade",
                "ContextMenu_Unbarricade", "ContextMenu_MetalBarricade", "ContextMenu_MetalBarBarricade", "ContextMenu_Open_window",
                "ContextMenu_Close_window", "ContextMenu_PickupBrokenGlass", "ContextMenu_Open_door", "ContextMenu_Close_door")
for k in sorted(used):
    if k.endswith("_"): continue
    if k in vanilla_keys: continue
    if k not in en: errors.append("TRANSLATION key missing in EN: %s" % k)
# sandbox options translations
sb = open(os.path.join(MOD, "sandbox-options.txt"), encoding="utf-8").read()
for m in re.finditer(r"translation\s*=\s*(\w+)", sb):
    if "Sandbox_" + m.group(1) not in en: errors.append("SANDBOX translation missing: Sandbox_" + m.group(1))
for m in re.finditer(r"option\s+(\w+)\.(\w+)", sb):
    pass
# Lua references to TOC.* items
for m in re.finditer(r'"(TOC\.[A-Za-z_]+)"', lua_src):
    ref = m.group(1)
    if ref.endswith("_") or ref in ("TOC.Amputation_", "TOC.FieldSurgery"): continue
    if ref not in items: errors.append("LUA references undefined item %s" % ref)
# sounds used in lua
for m in re.finditer(r'playSound\("([A-Za-z_]+)"\)', lua_src):
    s = m.group(1)
    if s.startswith("TOC_") or s in ("Amputation", "Cauterization"):
        if s not in sounds: errors.append("SOUND %s not defined" % s)
# textures referenced by StaticData (ui)
for sex in ("Male", "Female"):
    for limb in dynamic["ContextMenu_Limb_"]:
        if not os.path.exists(os.path.join(MOD, "ui", sex, limb + ".png")): errors.append("UI overlay missing: %s/%s.png" % (sex, limb))
for p in ("ProstArm_L", "ProstArm_R", "ProstLeg_L", "ProstLeg_R"):
    if not os.path.exists(os.path.join(MOD, "ui", p + ".png")): errors.append("UI overlay missing: %s.png" % p)
# sound files
for m in re.finditer(r"file\s*=\s*([^,]+),", open(os.path.join(MOD, "scripts", "TOC_sounds.txt"), encoding="utf-8").read()):
    rel = m.group(1).strip()
    if not os.path.exists(os.path.join(os.path.dirname(MOD), rel.replace("/", os.sep))): errors.append("SOUND file missing: " + rel)

print("items:", len(items), "models:", len(models), "recipes:", sorted(recipes))
for w in warns: print("WARN", w)
for e in errors: print("ERROR", e)
print("errors:", len(errors), "warnings:", len(warns))
sys.exit(1 if errors else 0)
