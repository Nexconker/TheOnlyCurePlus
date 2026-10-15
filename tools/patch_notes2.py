"""Segunda tanda de anotaciones del usuario:
A. Arrastre también quieto: los nodos de animación se nombran para que ordenen antes que los vanilla
   (A_TOC_*), con transiciones entre ellos, y al entrar en arrastre el personaje cae al suelo.
B. Gritos: voces vanilla del jugador (PainFromBite / PainFromScratch / PainFromLacerate) en vez de wav sintético.
C. Texturas de muñón de pierna para el cuerpo femenino (FemaleBody01-05) + índice por sexo.
D. Al amputar con el kit quirúrgico se muestra la sierra de hueso en la mano, no el botiquín.
"""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
LUA = os.path.join(MOD, "lua")

def patch(path, pairs, must=True):
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        if b in s: continue
        if a not in s:
            if must: raise AssertionError((path, a[:70]))
            continue
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="\n").write(s); print("patched", os.path.relpath(path, MOD) if path.startswith(MOD) else path)

# ---------------------------------------------------------------- A. nodos de arrastre
for f in glob.glob(os.path.join(MOD, "AnimSets", "player", "*", "TOC_Crawl*.xml")): os.remove(f)
NODES = {"idle": ("A_TOC_CrawlIdle", "Zombie_CrawlIdle", "0.40"), "movement": ("A_TOC_Crawl", "Zombie_Crawl", "0.64"),
         "run": ("A_TOC_CrawlRun", "Zombie_Crawl", "0.70"), "sprint": ("A_TOC_CrawlSprint", "Zombie_Crawl", "0.70"),
         "turningMovement180": ("A_TOC_CrawlTurn", "Zombie_Crawl", "0.64")}
def node(name, anim, speed):
    others = [n for n, _, _ in NODES.values() if n != name]
    trans = "".join("""	<m_Transitions>
		<m_Target>%s</m_Target>
		<m_blendInTime>0.3</m_blendInTime>
		<m_blendOutTime>0.3</m_blendOutTime>
	</m_Transitions>
""" % o for o in others)
    return """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>%s</m_Name>
	<m_Priority>10</m_Priority>
	<m_AnimName>%s</m_AnimName>
	<m_Looped>true</m_Looped>
	<m_BlendTime>0.30</m_BlendTime>
	<m_SpeedScale>%s</m_SpeedScale>
	<m_Conditions x_name="toc-crawl-%s">
		<m_Name>TOC_Crawl</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
%s</animNode>
""" % (name, anim, speed, name.lower(), trans)
for state, (name, anim, speed) in NODES.items():
    d = os.path.join(MOD, "AnimSets", "player", state); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".xml"), "w", encoding="utf-8", newline="\n").write(node(name, anim, speed))
print("anim nodes:", ", ".join(n for n, _, _ in NODES.values()))

patch(os.path.join(LUA, "client/TOC/Plus/LegMobility.lua"), [
("""        player:setVariable("TOC_Crawl", crawl and "true" or "false")
        if crawl then
            if player:isSneaking() then player:setSneaking(false) end
        end""",
"""        player:setVariable("TOC_Crawl", crawl and "true" or "false")
        if crawl then
            if player:isSneaking() then player:setSneaking(false) end
            -- cae al suelo: tras la caída vanilla el estado idle ya elige el nodo de arrastre
            if not player:isKnockedDown() then player:setKnockedDown(true) end
        end"""),
])

# ---------------------------------------------------------------- B. gritos vanilla
VOICE = """
---Voz vanilla del jugador (los mismos gritos que al ser mordido); si falla, el wav propio.
local function Voice(char, voiceName, fallback)
    local ok = pcall(function() char:playerVoiceSound(voiceName) end)
    if not ok and fallback then pcall(function() char:getEmitter():playSound(fallback) end) end
end
"""
p = os.path.join(LUA, "client/TOC/TimedActions/CutLimbAction.lua")
patch(p, [
("local CutLimbAction = ISBaseTimedAction:derive(\"CutLimbAction\")", "local CutLimbAction = ISBaseTimedAction:derive(\"CutLimbAction\")\n" + VOICE),
("""        local snd = self.patient:isFemale() and "TOC_ScreamFemale" or "TOC_ScreamMale"
        pcall(function() emitter:playSound(snd) end)""",
"""        Voice(self.patient, "PainFromBite", self.patient:isFemale() and "TOC_ScreamFemale" or "TOC_ScreamMale")"""),
("""        pcall(function() emitter:playSound("TOC_Groan") end)
        addSound(self.patient, self.patient:getX(), self.patient:getY(), self.patient:getZ(), 3, 3)""",
"""        Voice(self.patient, "PainFromScratch", "TOC_Groan")
        addSound(self.patient, self.patient:getX(), self.patient:getY(), self.patient:getZ(), 3, 3)"""),
# D. sierra en la mano aunque la herramienta sea el kit quirúrgico
("""    pcall(function() self:setOverrideHandModels(self.item:getStaticModel()) end)

    self.sound = self.character:getEmitter():playSound("Amputation")""",
"""    pcall(function()
        -- el kit quirúrgico lleva la sierra dentro: en la mano se ve la sierra, no el botiquín
        local model = self.item:getFullType() == "TOC.SurgicalKit" and "BoneSaw" or self.item:getStaticModel()
        self:setOverrideHandModels(model)
    end)

    self.sound = self.character:getEmitter():playSound("Amputation")"""),
])
p = os.path.join(LUA, "client/TOC/TimedActions/SurgeryIncisionAction.lua")
patch(p, [
("""    pcall(function() self.patient:getEmitter():playSound("TOC_Groan") end)""",
"""    if not pcall(function() self.patient:playerVoiceSound("PainFromLacerate") end) then
        pcall(function() self.patient:getEmitter():playSound("TOC_Groan") end)
    end"""),
])
p = os.path.join(LUA, "client/TOC/TimedActions/CauterizeAction.lua")
s = open(p, encoding="utf-8").read()
import re
m = re.search(r'    local snd = self\.character:isFemale\(\) and "TOC_ScreamFemale" or "TOC_ScreamMale"\n(\s*)pcall\(function\(\) ([a-zA-Z_.:()]+):playSound\(snd\) end\)', s)
if m:
    s = s.replace(m.group(0), '    local snd = self.character:isFemale() and "TOC_ScreamFemale" or "TOC_ScreamMale"\n%sif not pcall(function() self.character:playerVoiceSound("PainFromBite") end) then pcall(function() %s:playSound(snd) end) end' % (m.group(1), m.group(2)))
    open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched CauterizeAction")
else:
    print("CauterizeAction: patrón no encontrado, revisar a mano")

# ---------------------------------------------------------------- C. texturas femeninas de muñón
patch(os.path.join(LUA, "server/TOC/Controllers/ItemsController.lua"), [
("""    local textureString = playerObj:getHumanVisual():getSkinTexture() or "MaleBody01"
    local isHairy = textureString:sub(-1) == "a"
    local matchedIndex = tonumber(textureString:match("%d%d")) or 1
    if matchedIndex < 1 or matchedIndex > 5 then matchedIndex = 1 end
    if isHairy then matchedIndex = matchedIndex + 5 end
    if isCicatrized then matchedIndex = matchedIndex + 10 end
    return matchedIndex - 1""",
"""    local textureString = playerObj:getHumanVisual():getSkinTexture() or "MaleBody01"
    local isHairy = textureString:sub(-1) == "a"
    local matchedIndex = tonumber(textureString:match("%d%d")) or 1
    if matchedIndex < 1 or matchedIndex > 5 then matchedIndex = 1 end
    -- piernas (TOC+): el cuerpo femenino tiene su propio mapeado, así que sus texturas van aparte
    -- (índices 20..29: 5 sangrantes + 5 cicatrizadas); los brazos del TOC original siguen con las masculinas
    local isFemaleBody = string.find(textureString, "Female") ~= nil
    if isFemaleBody and StaticData.IsLegLimb(limbName or "") then
        return 20 + (matchedIndex - 1) + (isCicatrized and 5 or 0)
    end
    if isHairy then matchedIndex = matchedIndex + 5 end
    if isCicatrized then matchedIndex = matchedIndex + 10 end
    return matchedIndex - 1"""),
("function ItemsController.Player.GetAmputationTexturesIndex(playerObj, isCicatrized)",
 "function ItemsController.Player.GetAmputationTexturesIndex(playerObj, isCicatrized, limbName)"),
("            local texId = ItemsController.Player.GetAmputationTexturesIndex(playerObj, isCicatrized)",
 "            local texId = ItemsController.Player.GetAmputationTexturesIndex(playerObj, isCicatrized, limbName)"),
])
patch(os.path.join(LUA, "shared/TOC/Handlers/ZombieStumps.lua"), [
("    return 20 + matchedIndex * 3 + level", "    return 30 + matchedIndex * 3 + level      -- tras 20 masculinas + 10 femeninas (piernas)"),
])
# generador de XML: femeninas entre las humanas y las zombi (sólo piernas)
patch(os.path.join(HERE, "gen_clothing_xml.py"), [
("""        for suf in ("_b", "_hairy_b", "_c", "_hairy_c"):
            for i in range(1, 6): tex.append(P("Amputations", "Human", part, "skin%02d%s" % (i, suf)))
        for z in range(1, 5):""",
"""        for suf in ("_b", "_hairy_b", "_c", "_hairy_c"):
            for i in range(1, 6): tex.append(P("Amputations", "Human", part, "skin%02d%s" % (i, suf)))
        for suf in ("_b", "_c"):
            for i in range(1, 6): tex.append(P("Amputations", "Human", part, "skinF%02d%s" % (i, suf)))
        for z in range(1, 5):"""),
])
# build_assets: texturas femeninas
patch(os.path.join(HERE, "build_assets.py"), [
("""        for z in range(1, 5):
            for lvl in range(1, 4):
                src = Image.open(os.path.join(bodydir, "M_ZedBody%02d_level%d.png" % (z, lvl))).convert("RGBA")""",
"""        for i in range(1, 6):
            src = Image.open(os.path.join(bodydir, "FemaleBody%02d.png" % i)).convert("RGBA")
            paint_disc(src.copy(), "blood", 50 + i).save(out("textures", "Amputations", "Human", part, "skinF%02d_b.png" % i))
            paint_disc(src.copy(), "scar", 50 + i).save(out("textures", "Amputations", "Human", part, "skinF%02d_c.png" % i))
        for z in range(1, 5):
            for lvl in range(1, 4):
                src = Image.open(os.path.join(bodydir, "M_ZedBody%02d_level%d.png" % (z, lvl))).convert("RGBA")"""),
])
print("notes2 ok")
