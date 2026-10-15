"""Añade make_noise_card() a make_workshop.py: anillos de alcance del ruido de la cirugía (datos reales del
mod: SurgeryPlan.Risk y CutLimbAction), zombis acudiendo, línea de tiempo de los gritos y qué lo reduce."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "make_workshop.py"); s = open(p, encoding="utf-8").read()

FUNC = r'''
def arrow(d, p0, p1, color, width=5, head=18):
    d.line((p0, p1), fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (2.6, -2.6):
        d.line((p1, (p1[0] + head * math.cos(ang + da), p1[1] + head * math.sin(ang + da))), fill=color, width=width)

def make_noise_card(w=1600, h=900):
    img = background(w, h, 91).convert("RGBA")
    red_vignette(img, 70)
    cx, cy, k = 1110, 500, 74                      # radio en px = k * sqrt(casillas)
    R = lambda tiles: k * math.sqrt(tiles)
    rings = [(25, (196, 32, 38), "Sin anestesia: grito", "25"), (10, (230, 120, 40), "Analgésicos: grito", "10"),
             (5, (230, 200, 70), "Sierra", "5"), (3, (170, 170, 175), "Muy anestesiado: gemido", "3")]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for tiles, col, _, _ in rings:           # relleno suave + borde
        r = R(tiles); ld.ellipse((cx - r, cy - r * 0.62, cx + r, cy + r * 0.62), fill=col + (28,), outline=col + (230,), width=4)
    img.alpha_composite(layer)
    add_blood(img, [(cx - 10, cy + 40, 60, 0)], seed=33)
    d = ImageDraw.Draw(img)
    fl = font(F_BOLD, 22); fs = font(F_BODY, 22)
    for tiles, col, label, num in rings:
        r = R(tiles)
        x = cx + r * math.cos(math.radians(-38)); y = cy + r * 0.62 * math.sin(math.radians(-38))
        txt = label + " · " + num + " " + "casillas"
        tw = d.textlength(txt, font=fs)
        d.rounded_rectangle((x - 6, y - 16, x + tw + 10, y + 14), radius=6, fill=(0, 0, 0, 190))
        d.text((x + 2, y - 13), txt, font=fs, fill=col)
    # zombis acudiendo desde fuera del anillo de 25
    zs = [("noise_zombie0", -150, 1.12, 150), ("noise_zombie1", 200, 1.05, 140), ("noise_zombie2", 30, 1.18, 130)]
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
        d.text((64 + d.textlength(a, font=font(F_BOLD, 22)) + 12, yy), "→ " + b, font=font(F_BODY, 22), fill=(205, 200, 190)); yy += 38
    d.text((40, yy + 14), "Menos dolor también = menos riesgo de desmayo.", font=font(F_BODY, 22), fill=GREY)
    # pie
    d.rectangle((0, h - 70, w, h), fill=(0, 0, 0, 170))
    fb = font(F_BODY, 24); x = 40
    for b in ("Radio de los gritos ajustable en sandbox (0-80)", "Anillos no a escala", "Opera en un sitio cerrado y despejado"):
        d.rectangle((x, h - 44, x + 10, h - 34), fill=RED); d.text((x + 20, h - 52), b, font=fb, fill=(220, 215, 205)); x += d.textlength(b, font=fb) + 60
    img.convert("RGB").save(os.path.join(OUT, "card_noise.png")); print("card_noise.png")
'''
if "def make_noise_card" not in s:
    s = s.replace("def make_poster(size=512):", FUNC + "\ndef make_poster(size=512):", 1)
    s = s.replace("    make_crawl_card()\n", "    make_crawl_card()\n    make_noise_card()\n", 1)
# textos en inglés
EN_ADD = '''    "EL RUIDO DE OPERAR": "SURGERY IS LOUD", "Cada grito se oye lejos. Los zombis van hacia él.": "Every scream carries. Zombies come to it.",
    "SERRAR EL HUESO": "SAWING THE BONE", "¡grito!": "scream!", "3 gritos durante el serrado · la sierra se oye a 5 casillas": "3 screams while sawing · the saw itself carries 5 tiles",
    "QUÉ LO REDUCE": "WHAT KEEPS IT DOWN", "Sin nada": "Nothing", "grito a 25 casillas": "scream, 25 tiles", "Analgésicos": "Painkillers",
    "grito a 10 casillas": "scream, 10 tiles", "Analgésicos + alcohol": "Painkillers + alcohol", "solo un gemido, 3 casillas": "just a groan, 3 tiles",
    "Somníferos": "Sleeping pills", "también cuentan como anestesia": "also count as anaesthesia",
    "Menos dolor también = menos riesgo de desmayo.": "Less pain also means less chance of fainting.",
    "Radio de los gritos ajustable en sandbox (0-80)": "Scream radius is a sandbox option (0-80)", "Anillos no a escala": "Rings not to scale",
    "Opera en un sitio cerrado y despejado": "Operate somewhere closed and cleared",
    "Sin anestesia: grito · 25 casillas": "No anaesthesia: scream · 25 tiles", "Analgésicos: grito · 10 casillas": "Painkillers: scream · 10 tiles",
    "Sierra · 5 casillas": "Saw · 5 tiles", "Muy anestesiado: gemido · 3 casillas": "Heavily sedated: groan · 3 tiles",
'''
if '"EL RUIDO DE OPERAR"' not in s:
    s = s.replace('    "SIN PIERNAS": "NO LEGS?",', EN_ADD + '    "SIN PIERNAS": "NO LEGS?",', 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("noise card patched")
