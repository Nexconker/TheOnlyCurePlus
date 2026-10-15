"""Arrastrarse sin piernas: nodos de animación del rastrero (Zombie_Crawl / Zombie_CrawlIdle) en los
estados del jugador, activados por la variable de animación TOC_Crawl, y la movilidad CRAWL en Lua."""
import os, sys
MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
LUA = os.path.join(MOD, "lua")

def node(name, anim, speed, blend="0.30"):
    return """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>%s</m_Name>
	<m_Priority>10</m_Priority>
	<m_AnimName>%s</m_AnimName>
	<m_Looped>true</m_Looped>
	<m_BlendTime>%s</m_BlendTime>
	<m_SpeedScale>%s</m_SpeedScale>
	<m_Conditions x_name="toc-crawl-%s">
		<m_Name>TOC_Crawl</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
</animNode>
""" % (name, anim, blend, speed, name.lower())

# estados del jugador donde puede estar mientras se arrastra: quieto, moviéndose (andar/sigilo),
# correr y esprintar (por si el juego entra en esos estados antes de que Lua lo corte)
for state, name, anim, speed in (("idle", "TOC_CrawlIdle", "Zombie_CrawlIdle", "0.40"),
                                 ("movement", "TOC_Crawl", "Zombie_Crawl", "0.64"),
                                 ("run", "TOC_CrawlRun", "Zombie_Crawl", "0.70"),
                                 ("sprint", "TOC_CrawlSprint", "Zombie_Crawl", "0.70"),
                                 ("turningMovement180", "TOC_CrawlTurn", "Zombie_Crawl", "0.64")):
    d = os.path.join(MOD, "AnimSets", "player", state)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".xml"), "w", encoding="utf-8", newline="\n").write(node(name, anim, speed))
    print("anim node", state, name)

def patch(rel, pairs):
    p = os.path.join(LUA, rel); s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        if b in s: continue          # ya aplicado
        assert a in s, (rel, a[:60]); s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched", rel)

patch("shared/TOC/StaticData.lua", [
("""    NONE = "NONE",          -- can't walk: needs crutch or prosthesis
    CRUTCH = "CRUTCH",      -- walking with a crutch: no running""",
"""    NONE = "NONE",          -- one leg missing, no crutch: can't walk
    CRAWL = "CRAWL",        -- both legs missing, no prostheses: crawling only (zombie crawler animation)
    CRUTCH = "CRUTCH",      -- walking with a crutch: no running"""),
])

patch("client/TOC/Plus/LegMobility.lua", [
("""--  NONE   -> a leg is missing and there is no crutch / prosthesis: cannot move""",
"""--  NONE   -> a leg is missing and there is no crutch / prosthesis: cannot move
--  CRAWL  -> both legs missing and no prosthesis: crawls on the ground (animation variable TOC_Crawl
--            selects the zombie crawler clips added in media/AnimSets/player/*/TOC_Crawl*.xml)"""),
("""LegMobility.applied = { blocked = false, cantSprint = false }
LegMobility.tick""",
"""LegMobility.applied = { blocked = false, cantSprint = false, crawl = false }
LegMobility.tick"""),
("""    if missing >= 2 then return StaticData.MOBILITY.NONE end""",
"""    if missing >= 2 then return StaticData.MOBILITY.CRAWL end"""),
("""local function setCantSprint(player, cant)
    if LegMobility.applied.cantSprint == cant then return end
    pcall(function() player:setMoodleCantSprint(cant) end)
    LegMobility.applied.cantSprint = cant
end""",
"""local function setCantSprint(player, cant)
    if LegMobility.applied.cantSprint == cant then return end
    pcall(function() player:setMoodleCantSprint(cant) end)
    LegMobility.applied.cantSprint = cant
end

local function setCrawl(player, crawl)
    if LegMobility.applied.crawl == crawl then return end
    pcall(function()
        player:setVariable("TOC_Crawl", crawl and "true" or "false")
        if crawl then
            if player:isSneaking() then player:setSneaking(false) end
        end
    end)
    LegMobility.applied.crawl = crawl
end"""),
("""    if m == StaticData.MOBILITY.NONE then
        setBlocked(player, not inVehicle)
        setCantSprint(player, true)""",
"""    if m ~= StaticData.MOBILITY.CRAWL then setCrawl(player, false) end
    if m == StaticData.MOBILITY.CRAWL then
        -- se arrastra: libre de moverse pero a ras de suelo, sin correr ni sigilo, gastando resistencia
        setBlocked(player, false)
        setCantSprint(player, true)
        setCrawl(player, not inVehicle)
        pcall(function()
            if player:isRunning() then player:setRunning(false) end
            if player:isSprinting() then player:setSprinting(false) end
            if player:isSneaking() then player:setSneaking(false) end
            if player:isPlayerMoving() and not inVehicle then
                local stats = player:getStats()
                stats:set(CharacterStat.ENDURANCE, math.max(0, (stats:get(CharacterStat.ENDURANCE) or 1) - 0.004))
            end
        end)
        local now = getTimestampMs and getTimestampMs() or 0
        if not inVehicle and now - LegMobility.lastHint > 20000 then
            LegMobility.lastHint = now
            Messages.Say(player, getText("IGUI_TOC_Crawling"), true)
        end
    elseif m == StaticData.MOBILITY.NONE then
        setBlocked(player, not inVehicle)
        setCantSprint(player, true)"""),
("""        if LegMobility.applied.blocked then player:setBlockMovement(false) end
        if LegMobility.applied.cantSprint then player:setMoodleCantSprint(false) end
    end)
    LegMobility.applied = { blocked = false, cantSprint = false }""",
"""        if LegMobility.applied.blocked then player:setBlockMovement(false) end
        if LegMobility.applied.cantSprint then player:setMoodleCantSprint(false) end
        if LegMobility.applied.crawl then player:setVariable("TOC_Crawl", "false") end
    end)
    LegMobility.applied = { blocked = false, cantSprint = false, crawl = false }"""),
])

for lang, txt in (("EN", "No legs. All I can do is crawl."), ("ES", "Sin piernas. Lo único que puedo hacer es arrastrarme.")):
    p = os.path.join(LUA, "shared", "Translate", lang, "IG_UI.json"); s = open(p, encoding="utf-8").read()
    if "IGUI_TOC_Crawling" not in s:
        key = '"IGUI_TOC_NeedCrutch":'
        i = s.index(key); j = s.index("\n", i)
        s = s[:j + 1] + '    "IGUI_TOC_Crawling": "%s",\n' % txt + s[j + 1:]
        open(p, "w", encoding="utf-8", newline="\n").write(s); print("string", lang)
print("crawl ok")
