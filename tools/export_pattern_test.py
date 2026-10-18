"""Prueba de patrones (2026-10-18): personajes con prótesis pintadas + patrón, componiendo la textura como hace el juego
(la calcomanía encima del color con alfa). Reusa las definiciones de export_workshop33.py sin ejecutar sus escenas.
Uso: python export_pattern_test.py -> out/scene_pattern ; blender -b -P blender_render.py -- out/scene_pattern out/renders_pattern 1200"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "export_workshop33.py"), encoding="utf-8").read().split("# ---- héroe")[0]
exec(compile(src, "export_workshop33.py", "exec"))
from PIL import Image
P.OUT = os.path.join(HERE, "out", "scene_pattern"); os.makedirs(P.OUT, exist_ok=True)
DEV = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media\textures\Prosthesis"
TMP = os.path.join(HERE, "out", "pattern_tex"); os.makedirs(TMP, exist_ok=True)
PATTERN = [None]
_ptex = ptex
def ptex(key, paint=None):
    base = _ptex(key, paint)
    if not PATTERN[0]: return base
    dec = os.path.join(DEV, "Pattern", "%s_%s.png" % (TEX[key], PATTERN[0]))
    if not os.path.exists(dec): return base
    out = os.path.join(TMP, "%s_%s_%s.png" % (TEX[key], paint or "orig", PATTERN[0]))
    Image.alpha_composite(Image.open(base).convert("RGBA"), Image.open(dec).convert("RGBA")).save(out)
    return out
jobs = {}
COL = {"camo": "green", "tiger": "orange", "hazard": "yellow", "carbon": "grey", "flames": "black", "digital": "grey", "urban": "grey",
       "splinter": "green", "racing": "red", "checker": "white", "dots": "blue", "chevron": "orange", "lightning": "black", "rust": "grey",
       "circuit": "black", "scales": "green", "hex": "purple"}
for i, (pat, col) in enumerate(COL.items()):
    PATTERN[0] = pat; sex = "Female" if i % 2 else "Male"
    hair = ("Bob", (34, 26, 22)) if sex == "Female" else ("Short", (40, 30, 24))
    scene("pt_" + pat, person(REST, sex, arm=("R", "", "Mech", "MechHand"), leg=("L", "", "mechLeg"), paint=col, hair=hair, shirt="TShirt_White.png"), "pt_" + pat, az=160)
PATTERN[0] = "hazard"
scene("pt_cyber", person(REST, "Female", arm=("R", "", "Cyber", "CyberHand"), leg=("L", "Thigh", "cyberLeg"), paint="red", hair=("Bob", (70, 44, 28))), "pt_cyber", az=160)
f = bl(REST["Bip01_R_Hand"][3, :3] * 0.5 + REST["Bip01_R_Forearm"][3, :3] * 0.5)
for pat in ("hazard", "camo", "flames"):
    jobs["pt_close_" + pat] = ["pt_" + pat, 215, f, 3.8, 8, "nocull"]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas")
