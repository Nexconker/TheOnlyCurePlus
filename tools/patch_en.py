"""Versión en inglés de las imágenes del Workshop: make_workshop.py acepta el idioma como argumento
(`python make_workshop.py en`) y traduce todo el texto dibujado mediante un diccionario; la salida va a
out/workshop/en/. make_workshop_folder.py usa la preview inglesa."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "make_workshop.py"); s = open(p, encoding="utf-8").read()

EN = '''
# ------------------------------------------------------------------ idioma
LANG = (sys.argv[1] if len(sys.argv) > 1 else "es").lower()
EN = {
    "FIELD SURGERY": "FIELD SURGERY", "THE ONLY CURE": "THE ONLY CURE",
    "Cirugía de campo por etapas · Infección y sepsis": "Staged field surgery · Infection and sepsis",
    "Prótesis por niveles que encajan de verdad": "Prostheses that fit the stump, level by level",
    "Piernas, muletas y arrastre · Zombis rastreros": "Legs, crutches and crawling · Crawler zombies",
    "Build 42 · Singleplayer y multijugador": "Build 42 · Singleplayer and multiplayer",
    "Fork de The Only Cure (ZioPao) · GPL-3.0": "Fork of The Only Cure (ZioPao) · GPL-3.0",
    "Prótesis · Cirugía · Sepsis · Rastreros": "Prostheses · Surgery · Sepsis · Crawlers",
    "Build 42 · SP y MP": "Build 42 · SP and MP",
    "PRÓTESIS DE PIERNA": "LEG PROSTHESES",
    "Pata de palo · Pierna mecánica · Pierna médica — por nivel de amputación: pie, pantorrilla o muslo": "Peg leg · Mechanical leg · Medical leg — per amputation level: foot, calf or thigh",
    "Encajes a la medida del muñón": "Sockets shaped to the stump", "Rodilla articulada en las de muslo": "Articulated knee on thigh models",
    "Caben bajo el pantalón": "They fit under trousers", "Se desgastan y se reparan": "They wear out and can be repaired",
    "PRÓTESIS DE BRAZO": "ARM PROSTHESES",
    "Brazo de madera · Gancho · Brazo mecánico · Brazo médico — por mano o por antebrazo": "Wooden arm · Hook · Mechanical arm · Medical arm — for a missing hand or forearm",
    "Cada tier con sus limitaciones": "Each tier has its limits", "Gancho: nada que exija dedos": "Hook: nothing that needs fingers",
    "Mecánico y médico: armas a dos manos": "Mechanical and medical: two-handed weapons", "Familiaridad con prótesis": "Prosthesis Familiarity skill",
    "CIRUGÍA DE CAMPO": "FIELD SURGERY",
    "Prepara, incide, sierra, sutura y venda — con riesgo real, gritos y desmayos": "Prep, incise, saw, stitch and bandage — with real risk, screams and fainting",
    "Ventana de cura e infección visible": "Cure window and visible infection", "Sepsis y convalecencia": "Sepsis and convalescence",
    "Sierra de hueso y kit quirúrgico": "Bone saw and surgical kit", "Muleta o arrastre sin piernas": "Crutch, or crawl without legs",
    "NUEVOS ÍTEMS": "NEW ITEMS", "Iconos 32x32 renderizados de los modelos · todos con modelo 3D en el suelo": "32x32 icons rendered from the models · every item has a 3D model on the floor",
    "En el suelo": "On the floor",
    "Sierra de hueso": "Bone Saw", "Kit quirúrgico": "Surgical Kit", "Guía de cirugía": "Field Surgery Guide", "Muleta": "Crutch", "Torniquete de pierna": "Leg Tourniquet",
    "Brazo de madera": "Wooden Arm", "Gancho": "Hook Arm", "Brazo mecánico": "Mechanical Arm", "Brazo médico": "Medical Arm",
    "Pata de palo": "Peg Leg", "Pierna mecánica": "Mechanical Leg", "Pierna médica": "Medical Leg",
    "Mano cercenada": "Severed Hand", "Antebrazo cercenado": "Severed Forearm", "Brazo cercenado": "Severed Upper Arm",
    "Pie cercenado": "Severed Foot", "Pantorrilla cercenada": "Severed Lower Leg", "Muslo cercenado": "Severed Thigh",
    "SIN PIERNAS": "NO LEGS?", "ARRÁSTRATE": "THEN CRAWL",
    "Sin las dos piernas y sin prótesis, el personaje se arrastra por el suelo.": "With both legs gone and no prosthesis, the character crawls on the ground.",
    "A los zombis les da igual que estés ahí abajo.": "Zombies do not care that you are down there.",
    "Animación del rastrero en todos los estados": "Crawler animation in every state", "Ni correr ni esprintar": "No running, no sprinting",
    "Con una pierna: muleta y cojera": "One leg: crutch and a limp", "Una prótesis te devuelve a pie": "A prosthesis puts you back on your feet",
}
def tr(text):
    return EN.get(text, text) if LANG == "en" else text
_orig_text = ImageDraw.ImageDraw.text
_orig_len = ImageDraw.ImageDraw.textlength
def _text(self, xy, text, *a, **k): return _orig_text(self, xy, tr(text), *a, **k)
def _len(self, text, *a, **k): return _orig_len(self, tr(text), *a, **k)
ImageDraw.ImageDraw.text = _text
ImageDraw.ImageDraw.textlength = _len
'''
if "LANG = (sys.argv" not in s:
    s = s.replace("import os, math\n", "import os, sys, math\n", 1)
    s = s.replace('OUT = os.path.join(HERE, "out", "workshop")', 'OUT = os.path.join(HERE, "out", "workshop")\n' + EN + '\nif LANG == "en": OUT = os.path.join(OUT, "en")', 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)

p = os.path.join(HERE, "make_workshop_folder.py"); s = open(p, encoding="utf-8").read()
old = 'Image.open(os.path.join(W, "preview.png"))'
new = 'Image.open(os.path.join(W, "en", "preview.png") if os.path.exists(os.path.join(W, "en", "preview.png")) else os.path.join(W, "preview.png"))'
if old in s and "en\", \"preview.png" not in s:
    s = s.replace(old, new); open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patch_en ok")
