"""Tabla de patrones en todas las prótesis pintables (2026-10-18, "muéstrame el render en todas las prótesis"):
cada prótesis sola (sin cuerpo) en la pose de reposo, con cada patrón sobre su color de prueba.
Uso: python export_pattern_all.py -> out/scene_pattern_all ; blender -b -P blender_render.py -- out/scene_pattern_all out/renders_pattern_all 420"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(HERE, "export_workshop33.py"), encoding="utf-8").read().split("# ---- héroe")[0], "export_workshop33.py", "exec"))
from PIL import Image
from make_pattern_decals import PATTERNS
P.OUT = os.path.join(HERE, "out", "scene_pattern_all"); os.makedirs(P.OUT, exist_ok=True)
DEV = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media\textures\Prosthesis"
TMP = os.path.join(HERE, "out", "pattern_tex"); os.makedirs(TMP, exist_ok=True)
COL = {"camo": "green", "tiger": "orange", "hazard": "yellow", "carbon": "grey", "flames": "black", "digital": "grey", "urban": "grey",
       "splinter": "green", "racing": "red", "checker": "white", "dots": "blue", "chevron": "orange", "lightning": "black", "rust": "grey",
       "circuit": "black", "scales": "green", "hex": "purple"}
def tex(key, pat):
    t = TEX[key]; col = COL[pat] if pat else None
    base = ptex(key, col) if os.path.exists(ptex(key, col)) else ptex(key)
    dec = os.path.join(DEV, "Pattern", "%s_%s.png" % (t, pat)) if pat else None
    if not dec or not os.path.exists(dec): return base
    out = os.path.join(TMP, "%s_%s_%s.png" % (t, col, pat))
    if not os.path.exists(out): Image.alpha_composite(Image.open(base).convert("RGBA"), Image.open(dec).convert("RGBA")).save(out)
    return out
# fila -> piezas (modelo, clave de textura)
ROWS = [("Wood + Knob", [("baseWood_R_M", "Wood"), ("headKnob_R_M", "Knob")]),
        ("Scrap + Hook", [("baseScrap_R_M", "Scrap"), ("headHook_R_M", "Hook")]),
        ("Scrap + Bayonet", [("baseScrap_R_M", "Scrap"), ("headBayonet_R_M", "Bayonet")]),
        ("Mech + Mech hand", [("baseMech_R_M", "Mech"), ("headMechHand_R_M", "MechHand")]),
        ("Medical + Med hand", [("baseMed_R_M", "Med"), ("headMedHand_R_M", "MedHand")]),
        ("Cyber + Cyber hand", [("baseCyber_R_M", "Cyber"), ("headCyberHand_R_M", "CyberHand")]),
        ("Peg leg", [("pegLeg_L_M", "pegLeg")]), ("Mech leg", [("mechLeg_L_M", "mechLeg")]),
        ("Medical leg", [("medicalLeg_L_M", "medicalLeg")]), ("Cyber leg", [("cyberLeg_L_M", "cyberLeg")])]
jobs = {}
for ri, (label, parts) in enumerate(ROWS):
    for pat in [None] + list(PATTERNS):
        meshes = [P.posed_x(os.path.join(MX, "Prosthesis", m + ".X"), tex(k, pat), REST) for m, k in parts]
        name = "pa_%d_%s" % (ri, pat or "none")
        P.export(name, meshes)
        V = np.vstack([np.asarray(m["v"]) for m in meshes]); c = (V.min(0) + V.max(0)) / 2; ext = float((V.max(0) - V.min(0)).max()) * 10
        jobs[name] = [name, 215 if ri < 6 else 160, bl(c), ext * 1.45, 8, "nocull"]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
