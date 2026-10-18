"""Arrastre en TODOS los estados de pie (giros, strafe, empujones) + andar con muleta cojeando.
Reescribe todos los nodos A_TOC_* (sustituye a patch_crawl2.py)."""
import os, sys, glob
MOD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")
LUA = os.path.join(MOD, "lua")
CRAWL = ["TOC_Crawl"] + ["TOC_Crawl%d" % i for i in range(2, 8)]
CRUTCH = ["TOC_Crutch%d" % i for i in range(1, 8)]
for f in glob.glob(os.path.join(MOD, "AnimSets", "player", "*", "A_TOC_*.xml")): os.remove(f)

def conds(vars_, extra=""):
    return "".join("""	<m_Conditions x_name="toc-%s">
		<m_Name>%s</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
""" % (v.lower(), v) for v in vars_) + extra

def node(name, anim, speed, vars_, looped=True, extra_conds="", transitions=(), deferred=False, blend="0.30"):
    trans = "".join("""	<m_Transitions>
		<m_Target>%s</m_Target>
		<m_blendInTime>0.3</m_blendInTime>
		<m_blendOutTime>0.3</m_blendOutTime>
	</m_Transitions>
""" % t for t in transitions)
    defer = """	<m_DeferredBoneName>Bip01</m_DeferredBoneName>
	<m_deferredBoneAxis>Z</m_deferredBoneAxis>
	<m_useDeferedRotation>true</m_useDeferedRotation>
""" if deferred else ""
    return """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>%s</m_Name>
	<m_Priority>10</m_Priority>
	<m_AnimName>%s</m_AnimName>
	<m_Looped>%s</m_Looped>
	<m_BlendTime>%s</m_BlendTime>
	<m_SpeedScale>%s</m_SpeedScale>
%s%s%s</animNode>
""" % (name, anim, "true" if looped else "false", blend, speed, defer, conds(vars_, extra_conds), trans)

def write(state, name, text):
    d = os.path.join(MOD, "AnimSets", "player", state); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".xml"), "w", encoding="utf-8", newline="\n").write(text)

TWIST = {"L": """	<m_Conditions x_name="toc-twist-l">
		<m_Name>targetTwist</m_Name>
		<m_Type>LESS</m_Type>
		<m_Value>0</m_Value>
	</m_Conditions>
""", "R": """	<m_Conditions x_name="toc-twist-r">
		<m_Name>targetTwist</m_Name>
		<m_Type>GTR</m_Type>
		<m_Value>0</m_Value>
	</m_Conditions>
"""}
LOOP = ("A_TOC_CrawlIdle", "A_TOC_Crawl")
# --- arrastre
write("idle", "A_TOC_CrawlIdle", node("A_TOC_CrawlIdle", "Zombie_CrawlIdle", "0.40", CRAWL, transitions=("A_TOC_Crawl",)))
write("movement", "A_TOC_Crawl", node("A_TOC_Crawl", "Zombie_Crawl", "0.64", CRAWL, transitions=("A_TOC_CrawlIdle",)))
write("run", "A_TOC_CrawlRun", node("A_TOC_CrawlRun", "Zombie_Crawl", "0.70", CRAWL, transitions=LOOP))
write("sprint", "A_TOC_CrawlSprint", node("A_TOC_CrawlSprint", "Zombie_Crawl", "0.70", CRAWL, transitions=LOOP))
write("strafe", "A_TOC_CrawlStrafe", node("A_TOC_CrawlStrafe", "Zombie_Crawl", "0.64", CRAWL, transitions=LOOP))
write("slowidleblend", "A_TOC_CrawlSlowIdle", node("A_TOC_CrawlSlowIdle", "Zombie_CrawlIdle", "0.40", CRAWL, transitions=LOOP))
write("bumped", "A_TOC_CrawlBumped", node("A_TOC_CrawlBumped", "Zombie_Crawler_HitReact", "0.80", CRAWL, looped=False, transitions=LOOP))
write("collide", "A_TOC_CrawlCollide", node("A_TOC_CrawlCollide", "Zombie_CrawlIdle", "0.40", CRAWL, looped=False, transitions=LOOP))
for side in ("L", "R"):
    write("turning", "A_TOC_CrawlTurn" + side, node("A_TOC_CrawlTurn" + side, "Zombie_CrawlTurn" + side, "0.80", CRAWL, looped=False, extra_conds=TWIST[side], transitions=LOOP, deferred=True, blend="0.10"))
    write("turningIdle180", "A_TOC_CrawlTurn180" + side, node("A_TOC_CrawlTurn180" + side, "Zombie_CrawlTurn" + side, "0.80", CRAWL, looped=False, extra_conds=TWIST[side], transitions=LOOP, deferred=True, blend="0.10"))
    write("turningMovement180", "A_TOC_CrawlTurnMove" + side, node("A_TOC_CrawlTurnMove" + side, "Zombie_CrawlTurn" + side, "0.80", CRAWL, looped=False, extra_conds=TWIST[side], transitions=LOOP, deferred=True, blend="0.10"))
# --- muleta: cojera fuerte del lado amputado, sosteniendo la muleta (variantes _Bat del juego)
for side in ("L", "R"):
    extra = """	<m_Conditions x_name="toc-crutchside-%s">
		<m_Name>TOC_CrutchSide</m_Name>
		<m_Type>STRING</m_Type>
		<m_Value>%s</m_Value>
	</m_Conditions>
""" % (side.lower(), side)
    write("movement", "A_TOC_CrutchWalk" + side, node("A_TOC_CrutchWalk" + side, "Bob_WalkHeavyLimp%s_Bat" % side, "0.80", CRUTCH, extra_conds=extra, transitions=("Idle",)))
print("nodos escritos:", len(glob.glob(os.path.join(MOD, "AnimSets", "player", "*", "A_TOC_*.xml"))))

# --- Lua
p = os.path.join(LUA, "client/TOC/Plus/LegMobility.lua"); s = open(p, encoding="utf-8").read()
rep = [
("""LegMobility.CRAWL_VARS = {""", """LegMobility.CRUTCH_VARS = { %s }
LegMobility.missingSide = "L"
LegMobility.CRAWL_VARS = {""" % ", ".join('"%s"' % v for v in CRUTCH)),
("""            if not dc:getIsProstEquippedGroup("Bottom_" .. side) then
                missing = missing + 1""",
"""            if not dc:getIsProstEquippedGroup("Bottom_" .. side) then
                missing = missing + 1
                LegMobility.missingSide = side"""),
("""local function setCrawl(player, crawl)""",
"""local function setCrutchAnim(player, on)
    if LegMobility.applied.crutch == on and (not on or LegMobility.applied.crutchSide == LegMobility.missingSide) then return end
    pcall(function()
        for _, v in ipairs(LegMobility.CRUTCH_VARS) do player:setVariable(v, on and "true" or "false") end
        player:setVariable("TOC_CrutchSide", LegMobility.missingSide)
    end)
    LegMobility.applied.crutch = on; LegMobility.applied.crutchSide = LegMobility.missingSide
end

local function setCrawl(player, crawl)"""),
("""    if m ~= StaticData.MOBILITY.CRAWL then setCrawl(player, false) end""",
"""    if m ~= StaticData.MOBILITY.CRAWL then setCrawl(player, false) end
    setCrutchAnim(player, m == StaticData.MOBILITY.CRUTCH and not inVehicle)"""),
("""        if LegMobility.applied.crawl then
            for _, v in ipairs(LegMobility.CRAWL_VARS) do player:setVariable(v, "false") end
        end""",
"""        if LegMobility.applied.crawl then
            for _, v in ipairs(LegMobility.CRAWL_VARS) do player:setVariable(v, "false") end
        end
        if LegMobility.applied.crutch then
            for _, v in ipairs(LegMobility.CRUTCH_VARS) do player:setVariable(v, "false") end
        end"""),
("""LegMobility.applied = { blocked = false, cantSprint = false, crawl = false }""",
 """LegMobility.applied = { blocked = false, cantSprint = false, crawl = false, crutch = false, crutchSide = nil }"""),
]
for a, b in rep:
    if b in s: continue
    assert a in s, a[:60]; s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s); print("LegMobility ok")

# --- muleta en la mano: punta hacia donde apunta un bate (abajo), almohadilla hacia la axila
p = os.path.join(MOD, "scripts", "TOC_models.txt"); s = open(p, encoding="utf-8").read()
old = """		attachment Bip01_Prop1
		{
			offset = 0.0 0.0 0.0,
			rotate = 0.0 0.0 0.0,
		}
		attachment Bip01_Prop2
		{
			offset = 0.0 0.0 0.0,
			rotate = 0.0 0.0 0.0,
		}"""
new = """		attachment Bip01_Prop1
		{
			offset = 0.0 0.0 0.0,
			rotate = 180.0 0.0 0.0,
		}
		attachment Bip01_Prop2
		{
			offset = 0.0 0.0 0.0,
			rotate = 180.0 0.0 0.0,
		}"""
if old in s:
    s = s.replace(old, new); open(p, "w", encoding="utf-8", newline="\n").write(s); print("crutch attachment ok")
print("crawl3 ok")
