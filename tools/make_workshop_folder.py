"""Prepara la carpeta que lee el subidor del Workshop del juego:
  %USERPROFILE%\\Zomboid\\Workshop\\TheOnlyCurePlus\\
      workshop.txt      (título, descripción, tags, visibilidad)
      preview.png       (imagen principal)
      Contents\\mods\\TheOnlyCurePlus\\...   (copia del mod sin basura de desarrollo)
También copia poster.png / icon.png nuevos al mod y actualiza la descripción de mod.info.
Uso: python make_workshop_folder.py"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "out", "workshop")
MOD = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus"
WS = r"C:\Users\nexco\Zomboid\Workshop\TheOnlyCurePlus"
# submod opcional para Tomb's Player Body (tools/make_tomb_stumps.py), con permiso de Tomb (2026-10-15): va en el mismo ítem
SUBMODS = [r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusTombBody"]

DESC_EN = open(os.path.join(HERE, "workshop_description_EN.txt"), encoding="utf-8").read()

# 1. póster e icono del mod (versión en inglés: el Workshop va sólo en inglés)
WI = os.path.join(W, "en") if os.path.exists(os.path.join(W, "en", "poster.png")) else W
shutil.copy(os.path.join(WI, "poster.png"), os.path.join(MOD, "42", "poster.png"))
shutil.copy(os.path.join(WI, "icon.png"), os.path.join(MOD, "42", "icon.png"))
shutil.copy(os.path.join(WI, "poster.png"), os.path.join(MOD, "poster.png"))
shutil.copy(os.path.join(WI, "icon.png"), os.path.join(MOD, "icon.png"))

# 2. mod.info (42 y raíz si existe)
INFO = """name=The Only Cure+ (Field Surgery)
poster=poster.png
icon=icon.png
description=Fork of ZioPao's The Only Cure for Build 42. Staged field surgery with real risk, visible infection window and diagnosis, sepsis and convalescence, prosthesis tiers that wear out and fit the stump (foot, calf or thigh; hand, forearm or upper arm), leg amputations with crutches, crawling and above-knee prostheses, an Ash-style chainsaw arm, crawler zombies, severed limbs as items. Enable only one of The Only Cure / The Only Cure+.
id=TheOnlyCurePlus
url=https://github.com/Nexconker/TheOnlyCurePlus
modversion=3.1.1
versionMin=42.20
loadModAfter=\\FancyHandwork,\\BrutalHandwork,\\TwoWeaponsOnBackRework
incompatible=\\TheOnlyCure,\\BB_FirstAidOverhaul
"""
for p in (os.path.join(MOD, "42", "mod.info"), os.path.join(MOD, "mod.info")):
    if os.path.exists(os.path.dirname(p)):
        open(p, "w", encoding="utf-8", newline="\n").write(INFO)

# 3. carpeta del Workshop
dst = os.path.join(WS, "Contents", "mods", "TheOnlyCurePlus")
# El ID del ítem publicado vive en workshop.txt (id=...). Sin él, el juego publica un ítem NUEVO en vez de
# actualizar: se conserva del workshop.txt anterior y se guarda también en tools/workshop_id.txt.
ID_FILE = os.path.join(HERE, "workshop_id.txt")
item_id = None
old_txt = os.path.join(WS, "workshop.txt")
if os.path.exists(old_txt):
    for ln in open(old_txt, encoding="utf-8", errors="ignore"):
        if ln.startswith("id="): item_id = ln.strip()[3:]
if not item_id and os.path.exists(ID_FILE):
    item_id = open(ID_FILE, encoding="utf-8").read().strip() or None
if item_id: open(ID_FILE, "w", encoding="utf-8").write(item_id)
if os.path.exists(WS): shutil.rmtree(WS)
os.makedirs(os.path.join(WS, "Contents", "mods"), exist_ok=True)
IGNORE = shutil.ignore_patterns("*.pyc", "__pycache__", "*.bak*", "Thumbs.db", ".git", "*.blend", "*.json.tmp")
shutil.copytree(MOD, dst, ignore=IGNORE)
for sub in SUBMODS:
    if os.path.exists(sub): shutil.copytree(sub, os.path.join(WS, "Contents", "mods", os.path.basename(sub)), ignore=IGNORE)
from PIL import Image
Image.open(os.path.join(W, "en", "preview.png") if os.path.exists(os.path.join(W, "en", "preview.png")) else os.path.join(W, "preview.png")).convert("RGB").resize((256, 256), Image.LANCZOS).save(os.path.join(WS, "preview.png"))   # el juego exige 256x256
lines = ["version=1"] + (["id=" + item_id] if item_id else []) + ["title=The Only Cure+ (Field Surgery)"]
# Descripción CORTA y sólo ASCII: el subidor del juego la reenvía a Steam en cada actualización y la
# descripción larga con cirílico/coreano devolvió result=2. La completa se pega a mano en la web de Steam
# (tools/workshop_description_EN.txt).
# SIN enlaces: con "github.com/..." aquí Steam devolvió result=2 al confirmar la 3.1.0 (el contenido ya se había subido
# entero). El enlace va en la descripción larga, que se pega en la web.
SHORT = ["The Only Cure+ (Field Surgery) for Build 42: staged field surgery, infection and sepsis,",
         "prostheses that fit the stump (now above the elbow too), an Ash-style chainsaw arm,",
         "legs, crutches and crawling, crawler zombies. SP and MP.",
         "Includes an optional add-on for Tomb's Player Body.",
         "Full description, changelog and languages on the Steam page."]
for ln in SHORT:
    assert all(ord(c) < 128 for c in ln)
    lines.append("description=" + ln)
lines += ["tags=Build 42;Items;Models;Clothing/Armor;Multiplayer;Realistic;Hardmode", "visibility=public"]
open(os.path.join(WS, "workshop.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
n = sum(len(f) for _, _, f in os.walk(os.path.join(WS, "Contents", "mods")))
print("Workshop listo:", WS, "-", n, "archivos copiados", "- id:", item_id or "NINGUNO (se publicaría como ítem nuevo)")
