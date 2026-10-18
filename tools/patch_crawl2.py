"""El juego elige, entre los nodos cuyas condiciones se cumplen, el que MÁS condiciones tiene (sneakidle
con 3 gana a Idle con 2; los nodos vanilla llegan a 5). Los nodos de arrastre llevan 7 condiciones sobre
variables TOC_Crawl1..7 que Lua pone a la vez."""
import os, sys, glob
MOD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")
LUA = os.path.join(MOD, "lua")
VARS = ["TOC_Crawl"] + ["TOC_Crawl%d" % i for i in range(2, 8)]

NODES = {"idle": ("A_TOC_CrawlIdle", "Zombie_CrawlIdle", "0.40"), "movement": ("A_TOC_Crawl", "Zombie_Crawl", "0.64"),
         "run": ("A_TOC_CrawlRun", "Zombie_Crawl", "0.70"), "sprint": ("A_TOC_CrawlSprint", "Zombie_Crawl", "0.70"),
         "turningMovement180": ("A_TOC_CrawlTurn", "Zombie_Crawl", "0.64")}
def node(name, anim, speed):
    conds = "".join("""	<m_Conditions x_name="toc-crawl-%s-%d">
		<m_Name>%s</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
""" % (name.lower(), i, v) for i, v in enumerate(VARS))
    trans = "".join("""	<m_Transitions>
		<m_Target>%s</m_Target>
		<m_blendInTime>0.3</m_blendInTime>
		<m_blendOutTime>0.3</m_blendOutTime>
	</m_Transitions>
""" % o for o, _, _ in NODES.values() if o != name)
    return """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>%s</m_Name>
	<m_Priority>10</m_Priority>
	<m_AnimName>%s</m_AnimName>
	<m_Looped>true</m_Looped>
	<m_BlendTime>0.30</m_BlendTime>
	<m_SpeedScale>%s</m_SpeedScale>
%s%s</animNode>
""" % (name, anim, speed, conds, trans)
for state, (name, anim, speed) in NODES.items():
    d = os.path.join(MOD, "AnimSets", "player", state)
    open(os.path.join(d, name + ".xml"), "w", encoding="utf-8", newline="\n").write(node(name, anim, speed))
print("nodes rewritten with", len(VARS), "conditions")

p = os.path.join(LUA, "client/TOC/Plus/LegMobility.lua"); s = open(p, encoding="utf-8").read()
old = """        player:setVariable("TOC_Crawl", crawl and "true" or "false")"""
new = """        -- 7 variables iguales: el juego prefiere el nodo con más condiciones cumplidas (ver patch_crawl2.py)
        for _, v in ipairs(LegMobility.CRAWL_VARS) do player:setVariable(v, crawl and "true" or "false") end"""
assert old in s; s = s.replace(old, new)
old2 = """        if LegMobility.applied.crawl then player:setVariable("TOC_Crawl", "false") end"""
new2 = """        if LegMobility.applied.crawl then
            for _, v in ipairs(LegMobility.CRAWL_VARS) do player:setVariable(v, "false") end
        end"""
assert old2 in s; s = s.replace(old2, new2)
old3 = """LegMobility.applied = { blocked = false, cantSprint = false, crawl = false }
LegMobility.tick"""
new3 = """LegMobility.applied = { blocked = false, cantSprint = false, crawl = false }
LegMobility.CRAWL_VARS = { %s }
LegMobility.tick""" % ", ".join('"%s"' % v for v in VARS)
assert old3 in s; s = s.replace(old3, new3)
open(p, "w", encoding="utf-8", newline="\n").write(s); print("LegMobility ok")
