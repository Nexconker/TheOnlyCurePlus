"""Arrastre también al apuntar, golpear, empujar, pisotear y disparar (estados aim*, melee, shove*, stomp, ranged)."""
import os, sys
MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
CRAWL = ["TOC_Crawl"] + ["TOC_Crawl%d" % i for i in range(2, 8)]

def conds():
    return "".join("""	<m_Conditions x_name="toc-%s">
		<m_Name>%s</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
""" % (v.lower(), v) for v in CRAWL)

ATTACK_EVENTS = """	<m_Events x_name="toc-ev-attackanim">
		<m_EventName>SetVariable</m_EventName>
		<m_Time>Start</m_Time>
		<m_ParameterValue>AttackAnim=FALSE</m_ParameterValue>
	</m_Events>
	<m_Events x_name="toc-ev-swing">
		<m_EventName>PlaySwingSound</m_EventName>
		<m_Time>Start</m_Time>
		<m_ParameterValue></m_ParameterValue>
	</m_Events>
"""

def node(name, anim, speed, looped, attack=False):
    early = "	<m_EarlyTransitionOut>true</m_EarlyTransitionOut>\n" if attack else ""
    return """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>%s</m_Name>
	<m_Priority>10</m_Priority>
	<m_AnimName>%s</m_AnimName>
	<m_Looped>%s</m_Looped>
	<m_BlendTime>0.20</m_BlendTime>
%s	<m_SpeedScale>%s</m_SpeedScale>
%s%s	<m_Transitions>
		<m_Target>A_TOC_CrawlIdle</m_Target>
		<m_blendInTime>0.3</m_blendInTime>
	</m_Transitions>
</animNode>
""" % (name, anim, "true" if looped else "false", early, speed, conds(), ATTACK_EVENTS if attack else "")

NODES = {
    "aim": ("A_TOC_CrawlAim", "Zombie_CrawlIdle", "0.40", True, False),
    "aim-strafe": ("A_TOC_CrawlAimStrafe", "Zombie_Crawl", "0.64", True, False),
    "aim-sneak": ("A_TOC_CrawlAimSneak", "Zombie_CrawlIdle", "0.40", True, False),
    "melee": ("A_TOC_CrawlMelee", "Zombie_CrawlLunge", "0.90", False, True),
    "shove": ("A_TOC_CrawlShove", "Zombie_CrawlLunge", "0.90", False, True),
    "shoveAim": ("A_TOC_CrawlShoveAim", "Zombie_CrawlLunge", "0.90", False, True),
    "stomp": ("A_TOC_CrawlStomp", "Zombie_CrawlLunge", "0.90", False, True),
    "ranged": ("A_TOC_CrawlRanged", "Zombie_CrawlIdle", "0.80", False, False),
}
for state, (name, anim, speed, looped, attack) in NODES.items():
    d = os.path.join(MOD, "AnimSets", "player", state); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".xml"), "w", encoding="utf-8", newline="\n").write(node(name, anim, speed, looped, attack))
print("nodos de ataque/apuntado:", len(NODES))
