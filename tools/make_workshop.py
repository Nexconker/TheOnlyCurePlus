"""Compone las imágenes del Workshop a partir de los renders de Blender:
  out/workshop/preview.png  (1024x1024, imagen principal del Workshop)
  out/workshop/hero.png     (1920x1080, cabecera)
  out/workshop/card_*.png   (1600x900, tarjetas de características)
  out/workshop/poster.png   (512x512 para el menú de mods) + icon.png (64x64)
Uso: python make_workshop.py"""
import os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "out", "workshop", "renders")
OUT = os.path.join(HERE, "out", "workshop")

# ------------------------------------------------------------------ idioma
LANG = (sys.argv[1] if len(sys.argv) > 1 else "es").lower()
EN = {
    "FIELD SURGERY": "FIELD SURGERY", "THE ONLY CURE": "THE ONLY CURE",
    "Cirugía de campo por etapas · Infección y sepsis": "Staged field surgery · Infection and sepsis",
    "Prótesis por niveles que encajan de verdad": "Prostheses that fit the stump, level by level",
    "Piernas, muletas y arrastre · Zombis rastreros": "Legs, crutches and crawling · Crawler zombies",
    "Piernas, muletas y arrastre · Brazo motosierra": "Legs, crutches and crawling · Chainsaw arm",
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
    "Madera · Gancho · Mecánico · Médico — sin mano, sin antebrazo o sin brazo entero": "Wood · Hook · Mechanical · Medical — for a missing hand, forearm or whole arm",
    "Por encima del codo: bisagra de codo": "Above the elbow: elbow hinge",
    "Brazo motosierra": "Chainsaw Arm",
    "Brazo motosierra estilo Ash: el motor al muñón, la espada en línea con el antebrazo": "Ash-style chainsaw arm: motor bolted to the stump, bar in line with the forearm",
    "Tirón de arranque (la Mecánica ayuda)": "Pull-start (Mechanics helps)", "Depósito de 0,5 L: échale gasolina": "0.5 L tank: refuel with petrol",
    "En marcha corta zombis y extremidades": "Running, it cuts zombies and limbs", "Ruido: lo oyen desde lejos": "Loud: they hear it from afar",
    "Mano izquierda libre": "Left hand stays free", "Sólo brazo derecho": "Right arm only", "Mano, antebrazo o brazo entero": "Hand, forearm or whole arm",
    "EL BRAZO DE MERLE.": "MERLE'S ARM.", "Brazo bayoneta estilo Merle: chatarra, cuero, cinta americana y una bayoneta": "Merle-style bayonet arm: scrap metal, leather, duct tape and a bayonet",
    "Soldadura 2: un cuchillo, chatarra, cuero y cinta": "Welding 2: a knife, scrap metal, leather and tape", "Apuñala como un cuchillo de caza": "Stabs like a hunting knife",
    "Se desgasta con el uso": "Wears out with use", "Brazo bayoneta": "Bayonet Arm",
    "TUMBADO": "ON THE GROUND", "NO ESTÁS A SALVO": "YOU ARE NOT SAFE",
    "Arrastrarte no te esconde: los zombis te ven, te oyen y te alcanzan.": "Crawling does not hide you: zombies see you, hear you and catch up.",
    "Los zombis no te ignoran en el suelo": "Zombies do not ignore you on the ground", "Te mueves a paso de rastrero": "You move at a crawler's pace",
    "Busca una muleta o una prótesis": "Find a crutch or a prosthesis", "Opera en un sitio cerrado": "Operate somewhere closed",
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
    "EL RUIDO DE OPERAR": "SURGERY IS LOUD", "Cada grito se oye lejos. Los zombis van hacia él.": "Every scream carries. Zombies come to it.",
    "SERRAR EL HUESO": "SAWING THE BONE", "¡grito!": "scream!", "3 gritos durante el serrado · la sierra se oye a 5 casillas": "3 screams while sawing · the saw itself carries 5 tiles",
    "QUÉ LO REDUCE": "WHAT KEEPS IT DOWN", "Sin nada": "Nothing", "grito a 25 casillas": "scream, 25 tiles", "Analgésicos": "Painkillers",
    "grito a 10 casillas": "scream, 10 tiles", "Analgésicos + alcohol": "Painkillers + alcohol", "solo un gemido, 3 casillas": "just a groan, 3 tiles",
    "Somníferos": "Sleeping pills", "también cuentan como anestesia": "also count as anaesthesia",
    "Menos dolor también = menos riesgo de desmayo.": "Less pain also means less chance of fainting.",
    "Radio de los gritos ajustable en sandbox (0-80)": "Scream radius is a sandbox option (0-80)", "Anillos no a escala": "Rings not to scale",
    "Opera en un sitio cerrado y despejado": "Operate somewhere closed and cleared",
    "Sin anestesia": "No anaesthesia", "Sierra": "Saw", "Gemido (muy anestesiado)": "Groan (heavily sedated)", "casillas": "tiles",
    "ALCANCE EN CASILLAS": "REACH IN TILES",
    "SIN PIERNAS": "NO LEGS?", "ARRÁSTRATE": "THEN CRAWL",
    "Sin las dos piernas y sin prótesis, el personaje se arrastra por el suelo.": "With both legs gone and no prosthesis, the character crawls on the ground.",
    "Los zombis te encontrarán igual ahí abajo.": "Zombies will still find you down there.",
    "Animación del rastrero en todos los estados": "Crawler animation in every state", "Ni correr ni esprintar": "No running, no sprinting",
    "Con una pierna: muleta o arrastrarse": "One leg: crutch, or crawl", "Una prótesis te devuelve a pie": "A prosthesis puts you back on your feet",
}
EN.update({'Prótesis modulares · Gama cibernética · Pintura': 'Modular prostheses · Cybernetic tier · Paint', 'Pata de palo · Mecánica · Médica · Cibernética — pie, pantorrilla o muslo': 'Peg leg · Mechanical · Medical · Cybernetic — foot, calf or thigh', 'Se pintan en el banco': 'Paint them at the workbench', 'Madera · Chatarra · Mecánica · Médica · Cibernética — sin mano, sin antebrazo o sin brazo entero': 'Wood · Scrap · Mechanical · Medical · Cybernetic — for a missing hand, forearm or whole arm', 'Base + cabezal intercambiable': 'Base + swappable attachment', 'Manos: armas a dos manos': 'Hands: two-handed weapons', 'Cabezal de motosierra estilo Ash: se monta en cualquier base de metal': 'Ash-style chainsaw attachment: mounts on any metal base', 'Cabezal de bayoneta estilo Merle: chatarra, cuero, cinta americana y una bayoneta': 'Merle-style bayonet attachment: scrap metal, leather, duct tape and a bayonet', 'PRÓTESIS MODULARES': 'MODULAR PROSTHESES', 'Una base en el muñón y el cabezal que quieras: cámbialo sin quitarte la base': 'A base on the stump and any attachment you like: swap it without taking the base off', 'Pomo': 'Knob', 'Motosierra': 'Chainsaw', 'Bayoneta': 'Bayonet', 'Mano mecánica': 'Mechanical Hand', '5 bases · 7 cabezales': '5 bases · 7 attachments', 'Estadísticas de la combinación': 'Stats come from the combination', 'Cada base por nivel: mano, antebrazo o brazo': 'Every base per level: hand, forearm or arm', 'Tus brazos viejos se convierten solos': 'Your old arms convert automatically', 'API para cabezales de otros mods': 'API for attachments from other mods', 'GAMA CIBERNÉTICA': 'CYBERNETIC TIER', 'Tier 5: placas blindadas, músculos de cable y dedos articulados — brazo y pierna': 'Tier 5: armour plates, cable muscles and segmented fingers — arm and leg', 'Mano cibernética: se cierra al agarrar': 'Cybernetic hand: closes when gripping', 'Sólo en bases de tier 3 o más': 'Only on tier 3+ bases', 'Soldadura 7 · Electricidad 6 · Mecánica 5': 'Welding 7 · Electrical 6 · Mechanics 5', 'Electrónica rara: cargador, amplificador, sensor': 'Rare electronics: charger, amplifier, sensor', 'Mejor bonificación y menor desgaste': 'Best bonus, lowest wear', 'Brazo, mano y pierna': 'Arm, hand and leg', 'PINTA TU PRÓTESIS': 'PAINT YOUR PROSTHESIS', 'Cualquier bote de pintura del juego y un pincel, en el banco de prótesis': 'Any vanilla paint can and a paintbrush, at the prosthesis workbench', '10 colores': '10 colours', 'Rasca la pintura para volver': 'Scrape the paint off to get', 'al acabado original': 'the original finish back', 'Bases, cabezales y piernas': 'Bases, attachments and legs', 'Gasta un uso del bote': 'Uses one dose of the can', 'La pintura gastada muestra el desgaste': 'Worn paint shows the wear', 'Se ve en multijugador': 'Visible in multiplayer', 'BANCO DE PRÓTESIS': 'PROSTHESIS WORKBENCH', 'Un mueble que fabricas y colocas: monta, combina y pinta tus prótesis a su lado': 'Furniture you build and place: fit, combine and paint your prostheses next to it', 'Carpintería 3: tablones, clavos, chapa y tornillos': 'Carpentry 3: planks, nails, sheet metal and screws', 'Modelo 3D de verdad': 'A real 3D model', 'Vista 3D de tu personaje': '3D view of your character', 'Estadísticas y comparación': 'Stats and comparison', 'Botón para pintar': 'Paint button', 'Banco de prótesis': 'Prosthesis Workbench', 'Base de madera': 'Wooden Base', 'Base de chatarra': 'Scrap Base', 'Armazón mecánico': 'Mechanical Frame', 'Base médica': 'Medical Base', 'Armazón cibernético': 'Cybernetic Frame', 'Mano médica': 'Medical Hand', 'Mano cibernética': 'Cybernetic Hand', 'Pierna cibernética': 'Cybernetic Leg'})

def tr(text):
    return EN.get(text, text) if LANG == "en" else text
_orig_text = ImageDraw.ImageDraw.text
_orig_len = ImageDraw.ImageDraw.textlength
def _text(self, xy, text, *a, **k): return _orig_text(self, xy, tr(text), *a, **k)
def _len(self, text, *a, **k): return _orig_len(self, tr(text), *a, **k)
ImageDraw.ImageDraw.text = _text
ImageDraw.ImageDraw.textlength = _len

if LANG == "en": OUT = os.path.join(OUT, "en")
F_TITLE = r"C:\Windows\Fonts\impact.ttf"
F_BODY = r"C:\Windows\Fonts\bahnschrift.ttf"
F_BOLD = r"C:\Windows\Fonts\ariblk.ttf"
RED = (196, 32, 38); RED2 = (120, 14, 20); BONE = (236, 226, 206); GREY = (150, 150, 155); DARK = (14, 13, 15)

def font(path, size):
    return ImageFont.truetype(path, size)

def background(w, h, seed=1):
    """Fondo oscuro con viñeta, grano y una banda roja diagonal tipo cinta de hospital."""
    img = Image.new("RGB", (w, h), DARK)
    # gradiente radial
    grad = Image.new("L", (w, h), 0); gd = ImageDraw.Draw(grad)
    for i in range(40, 0, -1):
        r = int(max(w, h) * 0.75 * i / 40)
        gd.ellipse((w * 0.55 - r, h * 0.45 - r * 0.8, w * 0.55 + r, h * 0.45 + r * 0.8), fill=int(70 * (1 - i / 40)))
    img = Image.composite(Image.new("RGB", (w, h), (40, 38, 44)), img, grad.filter(ImageFilter.GaussianBlur(w // 12)))
    # grano
    import random
    rnd = random.Random(seed)
    noise = Image.effect_noise((w, h), 18).convert("L")
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.06)
    # líneas de rejilla sutiles (plano quirúrgico)
    d = ImageDraw.Draw(img, "RGBA")
    step = 64
    for x in range(0, w, step): d.line((x, 0, x, h), fill=(255, 255, 255, 7))
    for y in range(0, h, step): d.line((0, y, w, y), fill=(255, 255, 255, 7))
    return img

import random
def blood_layer(w, h, splats, seed=7):
    """Capa RGBA de sangre: salpicaduras (manchas irregulares con gotas) y regueros que caen."""
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    for (cx, cy, r, drips) in splats:
        for k in range(26):
            a = rnd.uniform(0, 2 * math.pi); dist = abs(rnd.gauss(0, r * 0.45))
            rr = max(2, rnd.gauss(r * 0.28, r * 0.12) * (1 - dist / (r * 1.6)))
            x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.75
            col = (rnd.randint(95, 150), rnd.randint(4, 14), rnd.randint(8, 18), rnd.randint(190, 240))
            d.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), fill=col)
        for k in range(40):
            a = rnd.uniform(0, 2 * math.pi); dist = rnd.uniform(r * 0.6, r * 1.9)
            rr = rnd.uniform(1.5, r * 0.06)
            x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.7
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(120, 8, 12, rnd.randint(150, 230)))
        for k in range(drips):
            x = cx + rnd.uniform(-r * 0.6, r * 0.6); ln = rnd.uniform(r * 0.5, r * 2.2); wd = rnd.uniform(2, r * 0.07)
            d.line((x, cy, x + rnd.uniform(-4, 4), cy + ln), fill=(110, 6, 10, 225), width=int(wd))
            d.ellipse((x - wd, cy + ln - wd * 1.4, x + wd, cy + ln + wd * 1.4), fill=(120, 8, 12, 230))
    glow = layer.filter(ImageFilter.GaussianBlur(1.2))
    hi = Image.new("RGBA", (w, h), (0, 0, 0, 0)); hd = ImageDraw.Draw(hi)
    for (cx, cy, r, _) in splats:
        hd.ellipse((cx - r * 0.25, cy - r * 0.3, cx + r * 0.05, cy - r * 0.05), fill=(200, 60, 70, 60))
    glow.alpha_composite(hi.filter(ImageFilter.GaussianBlur(6)))
    return glow

def add_blood(img, splats, seed=7):
    img.alpha_composite(blood_layer(img.width, img.height, splats, seed))

def red_vignette(img, strength=70):
    w, h = img.size
    v = Image.new("L", (w, h), 0); d = ImageDraw.Draw(v)
    d.rectangle((0, 0, w, h), fill=strength)
    d.ellipse((-w * 0.15, -h * 0.25, w * 1.15, h * 1.25), fill=0)
    v = v.filter(ImageFilter.GaussianBlur(w // 8))
    red = Image.new("RGBA", (w, h), (90, 0, 6, 255)); red.putalpha(v)
    img.alpha_composite(red)

def shadowed(img, blur=18, alpha=170):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: min(255, v) * alpha // 255)
    sh.putalpha(a); sh = sh.filter(ImageFilter.GaussianBlur(blur))
    return sh

def feather(im, edge=90):
    """Desvanece los bordes del render (para primeros planos recortados por el encuadre)."""
    w, h = im.size
    m = Image.new("L", (w, h), 255); d = ImageDraw.Draw(m)
    for i in range(edge):
        v = int(255 * i / edge)
        d.rectangle((i, i, w - 1 - i, h - 1 - i), outline=v)
    m = m.filter(ImageFilter.GaussianBlur(edge // 4))
    a = im.split()[3]; a = Image.fromarray((__import__("numpy").array(a, float) * __import__("numpy").array(m, float) / 255).astype("uint8"))
    im = im.copy(); im.putalpha(a); return im

def paste_render(base, name, box, fit="contain", soft=False, shadow=True, mirror=False, rotate=0):
    """Pega un render RGBA (recortado a su contenido) dentro de box=(x0,y0,x1,y1) con sombra."""
    im = Image.open(os.path.join(R, name + ".png")).convert("RGBA")
    if mirror: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if rotate: im = im.rotate(rotate, resample=Image.BICUBIC, expand=True)
    if soft: im = feather(im, 230)
    bbox = im.split()[3].getbbox(); im = im.crop(bbox)
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / im.width, bh / im.height) if fit == "contain" else max(bw / im.width, bh / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    x = box[0] + (bw - im.width) // 2; y = box[1] + (bh - im.height) // 2
    if shadow and not soft: base.alpha_composite(shadowed(im), (x + 10, y + 18))
    base.alpha_composite(im, (x, y))
    return (x, y, x + im.width, y + im.height)

def title_block(d, x, y, title, sub, size=150, subsize=44, color=BONE):
    ft = font(F_TITLE, size); fs = font(F_BODY, subsize)
    # sombra del título
    d.text((x + 6, y + 6), title, font=ft, fill=(0, 0, 0))
    d.text((x, y), title, font=ft, fill=color)
    tw = d.textlength(title, font=ft)
    d.rectangle((x, y + size * 0.98, x + tw, y + size * 0.98 + 10), fill=RED)
    d.text((x, y + size * 1.02 + 24), sub, font=fs, fill=GREY)
    return y + size * 1.02 + 24 + subsize + 10

def tape(d, w, h, y, text, angle_h=28):
    """Banda roja con texto repetido (cinta de precinto)."""
    f = font(F_BOLD, angle_h)
    d.rectangle((0, y, w, y + angle_h + 18), fill=RED2)
    s = ("  " + text + "   ✚  ") * 8
    d.text((-40, y + 8), s, font=f, fill=(255, 220, 220))

def make_hero(w=1920, h=1080):
    img = background(w, h).convert("RGBA")
    red_vignette(img, 80)
    add_blood(img, [(1500, 985, 150, 0), (1120, 960, 110, 0), (1760, 1010, 80, 0)], seed=3)
    paste_render(img, "hero_m", (1180, -30, 1950, 1090))
    paste_render(img, "hero_f", (820, 40, 1460, 1090))
    add_blood(img, [(1860, 120, 70, 3), (60, 1000, 90, 0)], seed=11)
    d = ImageDraw.Draw(img)
    d.text((90, 150), "THE ONLY CURE", font=font(F_TITLE, 150), fill=(0, 0, 0))
    d.text((84, 144), "THE ONLY CURE", font=font(F_TITLE, 150), fill=BONE)
    d.text((88, 300), "+", font=font(F_TITLE, 190), fill=RED)
    d.text((200, 330), "FIELD SURGERY", font=font(F_TITLE, 120), fill=BONE)
    d.rectangle((84, 470, 820, 480), fill=RED)
    lines = ["Cirugía de campo por etapas · Infección y sepsis", "Prótesis por niveles que encajan de verdad",
             "Prótesis modulares · Gama cibernética · Pintura", "Build 42 · Singleplayer y multijugador"]
    fy = 505
    for ln in lines:
        d.text((90, fy), ln, font=font(F_BODY, 40), fill=(215, 210, 200)); fy += 56
    d.text((90, h - 70), "Fork de The Only Cure (ZioPao) · GPL-3.0", font=font(F_BODY, 30), fill=GREY)
    paste_render(img, "bonesaw", (470, 730, 960, 1000), rotate=-62)
    img.convert("RGB").save(os.path.join(OUT, "hero.png")); print("hero.png")

def make_preview(size=1024):
    img = background(size, size, 2).convert("RGBA")
    red_vignette(img, 70)
    add_blood(img, [(700, 905, 120, 0), (300, 890, 90, 0)], seed=5)
    paste_render(img, "hero_m", (330, 200, 1010, 940))
    paste_render(img, "hero_f", (10, 250, 620, 940))
    add_blood(img, [(960, 60, 60, 4)], seed=9)
    d = ImageDraw.Draw(img)
    d.text((44, 34), "THE ONLY CURE", font=font(F_TITLE, 108), fill=(0, 0, 0))
    d.text((40, 30), "THE ONLY CURE", font=font(F_TITLE, 108), fill=BONE)
    tw = d.textlength("THE ONLY CURE", font=font(F_TITLE, 108))
    d.text((40 + tw + 14, 10), "+", font=font(F_TITLE, 150), fill=RED)
    d.text((42, 142), "FIELD SURGERY", font=font(F_TITLE, 60), fill=RED)
    d.rectangle((40, 212, 540, 218), fill=RED)
    # etiqueta inferior
    d.rectangle((0, size - 110, size, size), fill=(0, 0, 0, 160))
    d.text((40, size - 92), "Prótesis · Cirugía · Sepsis · Rastreros", font=font(F_BODY, 44), fill=BONE)
    d.text((40, size - 44), "Build 42 · SP y MP", font=font(F_BODY, 28), fill=GREY)
    img.convert("RGB").save(os.path.join(OUT, "preview.png")); print("preview.png")

def make_card(name, renders, title, sub, bullets, w=1600, h=900, blood_before=(), blood_after=(), vignette=0):
    img = background(w, h, hash(name) % 1000).convert("RGBA")
    if vignette: red_vignette(img, vignette)
    if blood_before: add_blood(img, blood_before, seed=len(name))
    n = len(renders); cw = (w - 80) // n
    for i, rn in enumerate(renders):
        rot = {"bonesaw": -35, "crutch": 18}.get(rn, 0)
        paste_render(img, rn, (40 + i * cw, 190, 40 + (i + 1) * cw - 20, h - 100), soft=rn.startswith(("legs", "arms")), rotate=rot)
    if blood_after: add_blood(img, blood_after, seed=len(name) + 1)
    d = ImageDraw.Draw(img)
    d.text((44, 34), title, font=font(F_TITLE, 84), fill=(0, 0, 0)); d.text((40, 30), title, font=font(F_TITLE, 84), fill=BONE)
    d.rectangle((40, 122, 40 + d.textlength(title, font=font(F_TITLE, 84)), 128), fill=RED)
    d.text((40, 140), sub, font=font(F_BODY, 34), fill=GREY)
    # pie con viñetas
    d.rectangle((0, h - 100, w, h), fill=(0, 0, 0, 170))
    fb = font(F_BODY, 26); x = 40; yy = h - 86
    for i, b in enumerate(bullets):
        tw = d.textlength(b, font=fb)
        if x + tw + 30 > w - 40: x = 40; yy += 34
        d.rectangle((x, yy + 8, x + 10, yy + 18), fill=RED)
        d.text((x + 20, yy), b, font=fb, fill=(220, 215, 205)); x += tw + 60
    img.convert("RGB").save(os.path.join(OUT, "card_%s.png" % name)); print("card_%s.png" % name)

ITEMS = [("BoneSaw", "Sierra de hueso"), ("SurgicalKit", "Kit quirúrgico"), ("FieldSurgeryGuide", "Guía de cirugía"), ("Crutch", "Muleta"), ("LegTourniquet", "Torniquete de pierna"),
         ("ProsthesisWorkbench", "Banco de prótesis"), ("BaseWood", "Base de madera"),
         ("BaseScrap", "Base de chatarra"), ("BaseMech", "Armazón mecánico"), ("BaseMed", "Base médica"), ("BaseCyber", "Armazón cibernético"),
         ("HeadKnob", "Pomo"), ("HeadHook", "Gancho"), ("HeadMechHand", "Mano mecánica"), ("HeadMedHand", "Mano médica"), ("HeadCyberHand", "Mano cibernética"),
         ("HeadChainsaw", "Motosierra"), ("HeadBayonet", "Bayoneta"),
         ("PegLeg", "Pata de palo"), ("MechLeg", "Pierna mecánica"), ("MedicalLeg", "Pierna médica"), ("CyberLeg", "Pierna cibernética"),
         ("SeveredHand", "Mano cercenada"), ("SeveredForeArm", "Antebrazo cercenado"), ("SeveredUpperArm", "Brazo cercenado"),
         ("SeveredFoot", "Pie cercenado"), ("SeveredLowerLeg", "Pantorrilla cercenada"), ("SeveredUpperLeg", "Muslo cercenado")]
TEXD = os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlus", "42", "media", "textures")

def make_items_card(w=1600, h=900):
    img = background(w, h, 42).convert("RGBA")
    red_vignette(img, 60)
    add_blood(img, [(1500, 860, 100, 0), (80, 120, 50, 3)], seed=21)
    d = ImageDraw.Draw(img)
    d.text((44, 34), "NUEVOS ÍTEMS", font=font(F_TITLE, 84), fill=(0, 0, 0)); d.text((40, 30), "NUEVOS ÍTEMS", font=font(F_TITLE, 84), fill=BONE)
    d.rectangle((40, 122, 40 + d.textlength("NUEVOS ÍTEMS", font=font(F_TITLE, 84)), 128), fill=RED)
    d.text((40, 140), "Iconos 32x32 renderizados de los modelos · todos con modelo 3D en el suelo", font=font(F_BODY, 32), fill=GREY)
    cols, cell, x0, y0 = 8, 124, 40, 196
    fl = font(F_BODY, 20)
    for i, (nm, label) in enumerate(ITEMS):
        cx = x0 + (i % cols) * (cell + 12); cy = y0 + (i // cols) * (cell + 12)
        d.rounded_rectangle((cx, cy, cx + cell, cy + cell), radius=10, fill=(0, 0, 0, 110), outline=(255, 255, 255, 25))
        ic = Image.open(os.path.join(TEXD, "Item_%s.png" % nm)).convert("RGBA").resize((80, 80), Image.NEAREST)
        img.alpha_composite(ic, (cx + (cell - 80) // 2, cy + 8))
        fsz = 18; fl2 = font(F_BODY, fsz)
        while d.textlength(label, font=fl2) > cell - 8 and fsz > 12:
            fsz -= 1; fl2 = font(F_BODY, fsz)
        tw = d.textlength(label, font=fl2)
        d.text((cx + (cell - tw) / 2, cy + cell - 28), label, font=fl2, fill=(225, 220, 210))
    d.text((1180, 200), "En el suelo", font=font(F_BOLD, 26), fill=GREY)
    paste_render(img, "prop_bench", (1180, 240, 1560, 500))
    paste_render(img, "prop_cyberhand", (1180, 510, 1560, 680))
    paste_render(img, "prop_cyberleg", (1180, 690, 1560, 860))
    img.convert("RGB").save(os.path.join(OUT, "card_items.png")); print("card_items.png")

def blood_smear(img, p0, p1, width, seed=4):
    """Reguero arrastrado: elipses solapadas de p0 a p1 que se afinan, con salpicaduras laterales."""
    rnd = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    n = 60
    for i in range(n):
        t = i / (n - 1); x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
        wd = width * (0.35 + 0.65 * (1 - t)) * rnd.uniform(0.75, 1.1); hh = wd * 0.32
        a = int(200 * (1 - t * 0.6))
        d.ellipse((x - wd, y - hh, x + wd, y + hh), fill=(rnd.randint(90, 130), 6, 10, a))
    for i in range(70):
        t = rnd.random(); x = p0[0] + (p1[0] - p0[0]) * t + rnd.gauss(0, width * 0.8); y = p0[1] + (p1[1] - p0[1]) * t + rnd.gauss(0, width * 0.35)
        r = rnd.uniform(2, width * 0.08); d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=(110, 6, 10, rnd.randint(120, 220)))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))

def make_crawl_card(w=1600, h=900):
    img = background(w, h, 77).convert("RGBA")
    red_vignette(img, 110)
    # suelo: perspectiva sugerida con una franja más clara
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(0, 560), (w, 520), (w, h), (0, h)], fill=(30, 28, 30, 255))
    for y in range(540, h, 28): d.line((0, y + 20, w, y), fill=(255, 255, 255, 6))
    blood_smear(img, (1500, 660), (520, 760), 70, seed=4)
    add_blood(img, [(1480, 640, 90, 0), (1180, 700, 60, 0)], seed=13)
    box = paste_render(img, "crawl2", (300, 330, 1500, 900))
    add_blood(img, [(box[0] + 760, box[3] - 150, 55, 0), (box[0] + 820, box[3] - 120, 45, 0)], seed=17)
    d = ImageDraw.Draw(img)
    d.text((44, 34), "SIN PIERNAS", font=font(F_TITLE, 96), fill=(0, 0, 0)); d.text((40, 30), "SIN PIERNAS", font=font(F_TITLE, 96), fill=BONE)
    d.text((40, 130), "ARRÁSTRATE", font=font(F_TITLE, 96), fill=RED)
    d.rectangle((40, 236, 560, 243), fill=RED)
    d.text((40, 262), "Sin las dos piernas y sin prótesis, el personaje se arrastra por el suelo.", font=font(F_BODY, 32), fill=(215, 210, 200))
    d.text((40, 304), "Los zombis te encontrarán igual ahí abajo.", font=font(F_BODY, 32), fill=GREY)
    d.rectangle((0, h - 100, w, h), fill=(0, 0, 0, 170))
    fb = font(F_BODY, 26); x = 40; yy = h - 86
    for b in ("Animación del rastrero en todos los estados", "Ni correr ni esprintar", "Con una pierna: muleta o arrastrarse", "Una prótesis te devuelve a pie"):
        tw = d.textlength(b, font=fb)
        if x + tw + 30 > w - 40: x = 40; yy += 34
        d.rectangle((x, yy + 8, x + 10, yy + 18), fill=RED); d.text((x + 20, yy), b, font=fb, fill=(220, 215, 205)); x += tw + 60
    img.convert("RGB").save(os.path.join(OUT, "card_crawl.png")); print("card_crawl.png")


def arrow(d, p0, p1, color, width=5, head=18):
    d.line((p0, p1), fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (2.6, -2.6):
        d.line((p1, (p1[0] + head * math.cos(ang + da), p1[1] + head * math.sin(ang + da))), fill=color, width=width)

def make_noise_card(w=1600, h=900):
    img = background(w, h, 91).convert("RGBA")
    red_vignette(img, 70)
    cx, cy, k = 1120, 440, 70                      # radio en px = k * sqrt(casillas)
    R = lambda tiles: k * math.sqrt(tiles)
    rings = [(25, (196, 32, 38), "Sin anestesia", "25"), (10, (230, 120, 40), "Analgésicos", "10"),
             (5, (230, 200, 70), "Sierra", "5"), (3, (170, 170, 175), "Gemido (muy anestesiado)", "3")]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for tiles, col, _, _ in rings:           # relleno suave + borde
        r = R(tiles); ld.ellipse((cx - r, cy - r * 0.62, cx + r, cy + r * 0.62), fill=col + (28,), outline=col + (230,), width=4)
    img.alpha_composite(layer)
    add_blood(img, [(cx - 10, cy + 40, 60, 0)], seed=33)
    d = ImageDraw.Draw(img)
    fn = font(F_BOLD, 24)
    for (tiles, col, label, num), ang in zip(rings, (-62, 15, 35, 62)):
        r = R(tiles); x = cx + r * math.cos(math.radians(ang)); y = cy + r * 0.62 * math.sin(math.radians(ang))
        tw = d.textlength(num, font=fn)
        d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(0, 0, 0, 220), outline=col, width=3)
        d.text((x - tw / 2, y - 15), num, font=fn, fill=col)
    # leyenda bajo el diagrama
    ly = cy + R(25) * 0.62 + 26
    d.text((cx - R(25), ly), "ALCANCE EN CASILLAS", font=font(F_BOLD, 20), fill=GREY)
    ly += 32; fs = font(F_BODY, 22)
    for i, (tiles, col, label, num) in enumerate(rings):
        lx = cx - R(25) + (i % 2) * 330; yy2 = ly + (i // 2) * 32
        d.ellipse((lx, yy2 + 4, lx + 18, yy2 + 22), outline=col, width=4)
        t = "%s  %s" % (num, tr(label)); d.text((lx + 26, yy2), t, font=fs, fill=(220, 215, 205))
    # zombis acudiendo desde fuera del anillo de 25
    zs = [("noise_zombie0", -140, 1.14, 150), ("noise_zombie1", 160, 1.10, 140), ("noise_zombie2", 10, 1.12, 140)]
    for name, ang, f, size in zs:
        a = math.radians(ang); r = R(25) * f
        zx, zy = cx + r * math.cos(a), cy + r * 0.62 * math.sin(a)
        paste_render(img, name, (int(zx - size / 2), int(zy - size), int(zx + size / 2), int(zy)))
        r2 = R(25) * 0.78
        arrow(ImageDraw.Draw(img), (zx - (zx - cx) * 0.12, zy - 30 - (zy - cy) * 0.12), (cx + r2 * math.cos(a), cy + r2 * 0.62 * math.sin(a)), (196, 32, 38, 255))
    paste_render(img, "noise_patient", (cx - 95, cy - 150, cx + 95, cy + 40))
    d = ImageDraw.Draw(img)
    # título
    d.text((44, 34), "EL RUIDO DE OPERAR", font=font(F_TITLE, 84), fill=(0, 0, 0)); d.text((40, 30), "EL RUIDO DE OPERAR", font=font(F_TITLE, 84), fill=BONE)
    d.rectangle((40, 122, 40 + d.textlength("EL RUIDO DE OPERAR", font=font(F_TITLE, 84)), 128), fill=RED)
    d.text((40, 140), "Cada grito se oye lejos. Los zombis van hacia él.", font=font(F_BODY, 32), fill=GREY)
    # línea de tiempo del serrado
    y0 = 240; d.text((40, y0), "SERRAR EL HUESO", font=font(F_BOLD, 24), fill=BONE)
    bx0, bx1, by = 40, 600, y0 + 58
    d.rounded_rectangle((bx0, by - 7, bx1, by + 7), radius=7, fill=(70, 68, 72, 255))
    for pc in (0.04, 0.38, 0.72):
        x = bx0 + (bx1 - bx0) * pc
        d.ellipse((x - 13, by - 13, x + 13, by + 13), fill=RED)
        d.text((x - 24, by + 18), "¡grito!", font=font(F_BODY, 20), fill=(240, 150, 150))
    d.text((bx0, by + 50), "3 gritos durante el serrado · la sierra se oye a 5 casillas", font=font(F_BODY, 22), fill=(205, 200, 190))
    # qué lo reduce
    y1 = by + 110; d.text((40, y1), "QUÉ LO REDUCE", font=font(F_BOLD, 24), fill=BONE)
    rows = [("Sin nada", "grito a 25 casillas", (196, 32, 38)),
            ("Analgésicos", "grito a 10 casillas", (230, 120, 40)),
            ("Analgésicos + alcohol", "solo un gemido, 3 casillas", (170, 170, 175)),
            ("Somníferos", "también cuentan como anestesia", (170, 170, 175))]
    yy = y1 + 42
    for a, b, col in rows:
        d.rectangle((40, yy + 7, 52, yy + 19), fill=col)
        d.text((64, yy), a, font=font(F_BOLD, 22), fill=(230, 225, 215))
        d.text((64 + d.textlength(a, font=font(F_BOLD, 22)) + 12, yy + 1), "- " + tr(b), font=font(F_BODY, 22), fill=(205, 200, 190)); yy += 38
    d.text((40, yy + 14), "Menos dolor también = menos riesgo de desmayo.", font=font(F_BODY, 22), fill=GREY)
    # pie
    d.rectangle((0, h - 70, w, h), fill=(0, 0, 0, 170))
    fb = font(F_BODY, 24); x = 40
    for b in ("Radio de los gritos ajustable en sandbox (0-80)", "Anillos no a escala", "Opera en un sitio cerrado y despejado"):
        d.rectangle((x, h - 44, x + 10, h - 34), fill=RED); d.text((x + 20, h - 52), b, font=fb, fill=(220, 215, 205)); x += d.textlength(b, font=fb) + 60
    img.convert("RGB").save(os.path.join(OUT, "card_noise.png")); print("card_noise.png")


def footer(img, d, bullets, w, h):
    d.rectangle((0, h - 100, w, h), fill=(0, 0, 0, 170))
    fb = font(F_BODY, 26); x = 40; yy = h - 86
    for b in bullets:
        tw = d.textlength(b, font=fb)
        if x + tw + 30 > w - 40: x = 40; yy += 34
        d.rectangle((x, yy + 8, x + 10, yy + 18), fill=RED); d.text((x + 20, yy), b, font=fb, fill=(220, 215, 205)); x += tw + 60

def make_chainsaw_card(w=1600, h=900):
    """Brazo motosierra: el golpe en grande, el brazo en reposo y el acople de cerca."""
    img = background(w, h, 314).convert("RGBA")
    red_vignette(img, 120)
    add_blood(img, [(300, 640, 130, 0), (560, 420, 70, 2), (170, 760, 90, 1), (1460, 820, 80, 0)], seed=66)
    # 3.2.0: con ropa del juego al estilo Ash Williams (export_ash_scene.py): camisa vaquera, escopeta recortada en la izquierda
    paste_render(img, "ash_attack", (-20, 215, 840, 900))
    paste_render(img, "ash_idle", (830, 225, 1220, 885))
    box = (1235, 235, 1580, 580)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=14, fill=(0, 0, 0, 150), outline=(196, 32, 38, 200), width=3)
    paste_render(img, "ash_close", box, shadow=False)
    add_blood(img, [(560, 430, 50, 3), (600, 470, 30, 4)], seed=77)
    d = ImageDraw.Draw(img)
    d.text((44, 34), "GROOVY.", font=font(F_TITLE, 96), fill=(0, 0, 0)); d.text((40, 30), "GROOVY.", font=font(F_TITLE, 96), fill=RED)
    d.rectangle((40, 136, 40 + d.textlength("GROOVY.", font=font(F_TITLE, 96)), 143), fill=BONE)
    d.text((40, 156), "Cabezal de motosierra estilo Ash: se monta en cualquier base de metal", font=font(F_BODY, 30), fill=(215, 210, 200))
    d.text((box[0], box[3] + 14), "Mano, antebrazo o brazo entero", font=font(F_BODY, 22), fill=GREY)
    footer(img, d, ["Tirón de arranque (la Mecánica ayuda)", "Depósito de 0,5 L: échale gasolina", "En marcha corta zombis y extremidades",
                    "Ruido: lo oyen desde lejos", "Mano izquierda libre", "Sólo brazo derecho"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_chainsaw.png")); print("card_chainsaw.png")

def make_bayonet_card(w=1600, h=900):
    """Brazo bayoneta (3.2.0), mismo esquema que la motosierra: la estocada en grande, en reposo y el brazo de cerca.
    Renders de export_merle_scene.py (chaqueta de cuero con la manga derecha cortada, vaqueros, botas)."""
    img = background(w, h, 271).convert("RGBA")
    red_vignette(img, 110)
    add_blood(img, [(260, 700, 120, 0), (620, 380, 60, 2), (140, 800, 80, 1), (1480, 830, 70, 0)], seed=91)
    paste_render(img, "knife_attack", (0, 215, 820, 900))
    paste_render(img, "knife_idle", (830, 225, 1220, 885))
    box = (1235, 235, 1580, 580)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=14, fill=(0, 0, 0, 150), outline=(196, 32, 38, 200), width=3)
    paste_render(img, "knife_close", box, shadow=False)
    add_blood(img, [(470, 330, 40, 3), (505, 300, 26, 4)], seed=93)
    d = ImageDraw.Draw(img)
    t = "EL BRAZO DE MERLE."
    d.text((44, 34), t, font=font(F_TITLE, 96), fill=(0, 0, 0)); d.text((40, 30), t, font=font(F_TITLE, 96), fill=RED)
    d.rectangle((40, 136, 40 + d.textlength(t, font=font(F_TITLE, 96)), 143), fill=BONE)
    d.text((40, 156), "Cabezal de bayoneta estilo Merle: chatarra, cuero, cinta americana y una bayoneta", font=font(F_BODY, 30), fill=(215, 210, 200))
    d.text((box[0], box[3] + 14), "Mano, antebrazo o brazo entero", font=font(F_BODY, 22), fill=GREY)
    footer(img, d, ["Soldadura 2: un cuchillo, chatarra, cuero y cinta", "Apuñala como un cuchillo de caza", "Se desgasta con el uso",
                    "Mano izquierda libre", "Sólo brazo derecho"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_bayonet.png")); print("card_bayonet.png")

def make_findyou_card(w=1600, h=900):
    """Aclara lo que la frase vieja del arrastre daba a entender: en el suelo los zombis NO te ignoran."""
    img = background(w, h, 271).convert("RGBA")
    red_vignette(img, 140)
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(0, 600), (w, 560), (w, h), (0, h)], fill=(30, 28, 30, 255))
    for y in range(580, h, 28): d.line((0, y + 20, w, y), fill=(255, 255, 255, 6))
    blood_smear(img, (1180, 720), (720, 780), 60, seed=9)
    # zombis acercándose desde los lados y desde el fondo
    zs = [("noise_zombie0", (40, 330, 400, 880)), ("noise_zombie1", (1190, 300, 1560, 880)), ("noise_zombie2", (990, 300, 1240, 700))]
    for name, b in zs: paste_render(img, name, b, mirror=(name == "noise_zombie0"))
    pbox = paste_render(img, "crawl2", (360, 470, 1160, 880))
    add_blood(img, [(pbox[0] + 470, pbox[3] - 90, 55, 0)], seed=19)
    d = ImageDraw.Draw(img)
    cx, cy = (pbox[0] + pbox[2]) // 2, (pbox[1] + pbox[3]) // 2 + 20
    for (x0, y0) in ((320, 580), (1270, 560), (1100, 520)):
        arrow(d, (x0, y0), (cx + (x0 - cx) * 0.35, cy + (y0 - cy) * 0.35), (196, 32, 38, 255), width=6, head=22)
    d.text((44, 34), "TUMBADO", font=font(F_TITLE, 96), fill=(0, 0, 0)); d.text((40, 30), "TUMBADO", font=font(F_TITLE, 96), fill=BONE)
    d.text((40, 130), "NO ESTÁS A SALVO", font=font(F_TITLE, 96), fill=RED)
    d.rectangle((40, 236, 40 + d.textlength("NO ESTÁS A SALVO", font=font(F_TITLE, 96)), 243), fill=RED)
    d.text((40, 262), "Arrastrarte no te esconde: los zombis te ven, te oyen y te alcanzan.", font=font(F_BODY, 32), fill=(215, 210, 200))
    footer(img, d, ["Los zombis no te ignoran en el suelo", "Te mueves a paso de rastrero", "Ni correr ni esprintar", "Busca una muleta o una prótesis"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_findyou.png")); print("card_findyou.png")

# ------------------------------------------------------------------ 3.3: tarjetas nuevas (2026-10-17)
def card_header(img, title, sub, color=BONE):
    d = ImageDraw.Draw(img)
    d.text((44, 34), title, font=font(F_TITLE, 84), fill=(0, 0, 0)); d.text((40, 30), title, font=font(F_TITLE, 84), fill=color)
    d.rectangle((40, 122, 40 + d.textlength(title, font=font(F_TITLE, 84)), 128), fill=RED)
    d.text((40, 140), sub, font=font(F_BODY, 32), fill=GREY)
    return d

def label_under(d, box, text, size=24, color=(225, 220, 210)):
    f = font(F_BODY, size); tw = d.textlength(text, font=f)
    d.text(((box[0] + box[2]) / 2 - tw / 2, box[3] + 6), text, font=f, fill=color)

def make_modular_card(w=1600, h=900):
    """Un armazón, cinco cabezales: el mismo brazo con pomo, gancho, mano, motosierra y bayoneta."""
    img = background(w, h, 333).convert("RGBA")
    add_blood(img, [(1460, 830, 80, 0), (120, 820, 70, 1)], seed=33)
    d = card_header(img, "PRÓTESIS MODULARES", "Una base en el muñón y el cabezal que quieras: cámbialo sin quitarte la base")
    heads = [("mod_Knob", "Pomo"), ("mod_Hook", "Gancho"), ("mod_MechHand", "Mano mecánica"), ("mod_Chainsaw", "Motosierra"), ("mod_Bayonet", "Bayoneta")]
    cw = (w - 80) // len(heads)
    for i, (rn, lab) in enumerate(heads):
        box = (40 + i * cw + 10, 200, 40 + (i + 1) * cw - 10, h - 150)
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle(box, radius=14, fill=(0, 0, 0, 90), outline=(255, 255, 255, 28))
        img.alpha_composite(ov)
        paste_render(img, rn, (box[0] + 10, box[1] + 10, box[2] - 10, box[3] - 10), shadow=False)
        label_under(ImageDraw.Draw(img), box, lab)
    d = ImageDraw.Draw(img)
    footer(img, d, ["5 bases · 7 cabezales", "Estadísticas de la combinación", "Cada base por nivel: mano, antebrazo o brazo",
                    "Tus brazos viejos se convierten solos", "API para cabezales de otros mods"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_modular.png")); print("card_modular.png")

def make_cyber_card(w=1600, h=900):
    img = background(w, h, 515).convert("RGBA")
    d = card_header(img, "GAMA CIBERNÉTICA", "Tier 5: placas blindadas, músculos de cable y dedos articulados — brazo y pierna", color=(232, 196, 120))
    paste_render(img, "cyber_full", (20, 180, 620, h - 100))
    paste_render(img, "cyber_grip", (600, 200, 1120, h - 100))
    box = (1160, 220, 1560, 620)
    dd = ImageDraw.Draw(img, "RGBA")
    dd.rounded_rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=14, fill=(0, 0, 0, 150), outline=(200, 152, 58, 220), width=3)
    paste_render(img, "cyber_hand", box, shadow=False)
    d = ImageDraw.Draw(img)
    d.text((box[0], box[3] + 16), "Mano cibernética: se cierra al agarrar", font=font(F_BODY, 22), fill=GREY)
    d.text((box[0], box[3] + 46), "Sólo en bases de tier 3 o más", font=font(F_BODY, 22), fill=GREY)
    footer(img, d, ["Soldadura 7 · Electricidad 6 · Mecánica 5", "Electrónica rara: cargador, amplificador, sensor", "Mejor bonificación y menor desgaste",
                    "Brazo, mano y pierna"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_cyber.png")); print("card_cyber.png")

def make_paint_card(w=1600, h=900):
    img = background(w, h, 727).convert("RGBA")
    d = card_header(img, "PINTA TU PRÓTESIS", "Cualquier bote de pintura del juego y un pincel, en el banco de prótesis")
    for i, rn in enumerate(("paint_red", "paint_yellow", "paint_blue")):
        paste_render(img, rn, (60 + i * 330, 190, 60 + (i + 1) * 330 - 20, h - 110))
    # muestras de color
    cols = [(38, 38, 42), (232, 232, 228), (128, 130, 134), (168, 34, 30), (214, 104, 28), (222, 184, 40), (78, 102, 52), (40, 72, 150), (98, 52, 130), (214, 116, 150)]
    d = ImageDraw.Draw(img)
    x0, y0 = 1080, 230
    d.text((x0, y0 - 46), "10 colores", font=font(F_BOLD, 30), fill=BONE)
    for k, c in enumerate(cols):
        r, cc = divmod(k, 2)
        d.rounded_rectangle((x0 + cc * 220, y0 + r * 92, x0 + cc * 220 + 200, y0 + r * 92 + 76), radius=10, fill=c + (255,), outline=(220, 220, 220, 120))
    d.text((x0, y0 + 5 * 92 + 10), "Rasca la pintura para volver", font=font(F_BODY, 24), fill=GREY)
    d.text((x0, y0 + 5 * 92 + 40), "al acabado original", font=font(F_BODY, 24), fill=GREY)
    footer(img, d, ["Bases, cabezales y piernas", "Gasta un uso del bote", "La pintura gastada muestra el desgaste", "Se ve en multijugador"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_paint.png")); print("card_paint.png")

def make_workbench_card(w=1600, h=900):
    img = background(w, h, 919).convert("RGBA")
    d = card_header(img, "BANCO DE PRÓTESIS", "Un mueble que fabricas y colocas: monta, combina y pinta tus prótesis a su lado")
    paste_render(img, "prop_bench", (30, 190, 560, h - 110))
    ui = Image.open(os.path.join(HERE, "out", "preview", "workbench_mockup%s.png" % ("_en" if LANG == "en" else ""))).convert("RGBA")
    ui = ui.crop((50, 50, ui.width - 50, ui.height - 50))
    s = min(980 / ui.width, 600 / ui.height); ui = ui.resize((int(ui.width * s), int(ui.height * s)), Image.LANCZOS)
    img.alpha_composite(shadowed(ui), (580 + 10, 200 + 18)); img.alpha_composite(ui, (580, 200))
    d = ImageDraw.Draw(img)
    footer(img, d, ["Carpintería 3: tablones, clavos, chapa y tornillos", "Modelo 3D de verdad", "Vista 3D de tu personaje",
                    "Estadísticas y comparación", "Botón para pintar"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_workbench.png")); print("card_workbench.png")

def make_poster(size=512):
    img = Image.open(os.path.join(OUT, "preview.png")).convert("RGB").resize((size, size), Image.LANCZOS)
    img.save(os.path.join(OUT, "poster.png")); print("poster.png")
    ic = background(256, 256, 5).convert("RGBA"); paste_render(ic, "bonesaw", (10, 10, 246, 246))
    d = ImageDraw.Draw(ic); d.text((16, 196), "TOC+", font=font(F_TITLE, 52), fill=BONE)
    ic.convert("RGB").resize((64, 64), Image.LANCZOS).save(os.path.join(OUT, "icon.png")); print("icon.png")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_hero(); make_preview()
    make_card("legs", ["legs_peg", "legs_mech", "legs_medical", "legs_cyber"], "PRÓTESIS DE PIERNA", "Pata de palo · Mecánica · Médica · Cibernética — pie, pantorrilla o muslo",
              ["Encajes a la medida del muñón", "Rodilla articulada en las de muslo", "Caben bajo el pantalón", "Se desgastan y se reparan", "Se pintan en el banco"],
              blood_before=[(120, 800, 90, 0), (1380, 780, 70, 0)], vignette=50)
    make_card("arms", ["arms_peg", "arms_hook", "arms_mech", "arms_medical", "arms_cyber"], "PRÓTESIS DE BRAZO", "Madera · Chatarra · Mecánica · Médica · Cibernética — sin mano, sin antebrazo o sin brazo entero",
              ["Base + cabezal intercambiable", "Gancho: nada que exija dedos", "Manos: armas a dos manos", "Por encima del codo: bisagra de codo"])
    make_modular_card(); make_cyber_card(); make_paint_card(); make_workbench_card()
    make_chainsaw_card()
    make_bayonet_card()
    make_findyou_card()
    make_card("surgery", ["stumps", "bonesaw", "crutch"], "CIRUGÍA DE CAMPO", "Prepara, incide, sierra, sutura y venda — con riesgo real, gritos y desmayos",
              ["Ventana de cura e infección visible", "Sepsis y convalecencia", "Sierra de hueso y kit quirúrgico", "Muleta o arrastre sin piernas"],
              blood_before=[(300, 790, 170, 0), (1020, 760, 120, 0)], blood_after=[(210, 650, 40, 5), (300, 640, 30, 3), (1420, 140, 50, 4)], vignette=90)
    make_items_card()
    make_crawl_card()
    make_noise_card()
    make_poster()
