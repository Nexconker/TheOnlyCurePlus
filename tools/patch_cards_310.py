"""Portadas del Workshop para la 3.1.0 en make_workshop.py:
- tarjeta de brazos: el mecánico va por encima del codo y el subtítulo lo dice;
- tarjeta de ítems: icono del brazo motosierra (rejilla de 7 columnas);
- tarjeta nueva "GROOVY.": brazo motosierra (renders saw_attack / saw_idle / saw_close);
- tarjeta nueva "TUMBADO NO ESTÁS A SALVO": el personaje arrastrándose y los zombis yendo a por él (tres
  personas leyeron en la descripción que en el suelo los zombis te ignoran).
Uso: python patch_cards_310.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "make_workshop.py"); s = open(p, encoding="utf-8").read()

def patch(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new, 1)

# ---- textos en inglés
patch('''    "Brazo de madera · Gancho · Brazo mecánico · Brazo médico — por mano o por antebrazo": "Wooden arm · Hook · Mechanical arm · Medical arm — for a missing hand or forearm",''',
      '''    "Brazo de madera · Gancho · Brazo mecánico · Brazo médico — por mano o por antebrazo": "Wooden arm · Hook · Mechanical arm · Medical arm — for a missing hand or forearm",
    "Madera · Gancho · Mecánico · Médico — sin mano, sin antebrazo o sin brazo entero": "Wood · Hook · Mechanical · Medical — for a missing hand, forearm or whole arm",
    "Por encima del codo: bisagra de codo": "Above the elbow: elbow hinge",
    "Brazo motosierra": "Chainsaw arm",
    "Brazo motosierra estilo Ash: el motor al muñón, la espada en línea con el antebrazo": "Ash-style chainsaw arm: motor bolted to the stump, bar in line with the forearm",
    "Tirón de arranque (la Mecánica ayuda)": "Pull-start (Mechanics helps)", "Depósito de 0,5 L: échale gasolina": "0.5 L tank: refuel with petrol",
    "En marcha corta zombis y extremidades": "Running, it cuts zombies and limbs", "Ruido: lo oyen desde lejos": "Loud: they hear it from afar",
    "Mano izquierda libre": "Left hand stays free", "Sólo brazo derecho": "Right arm only", "Mano, antebrazo o brazo entero": "Hand, forearm or whole arm",
    "TUMBADO": "ON THE GROUND", "NO ESTÁS A SALVO": "YOU ARE NOT SAFE",
    "Arrastrarte no te esconde: los zombis te ven, te oyen y te alcanzan.": "Crawling does not hide you: zombies see you, hear you and catch up.",
    "Los zombis no te ignoran en el suelo": "Zombies do not ignore you on the ground", "Te mueves a paso de rastrero": "You move at a crawler's pace",
    "Busca una muleta o una prótesis": "Find a crutch or a prosthesis", "Opera en un sitio cerrado": "Operate somewhere closed",''')

# ---- tarjeta de brazos
patch('''    make_card("arms", ["arms_peg", "arms_hook", "arms_mech", "arms_medical"], "PRÓTESIS DE BRAZO", "Brazo de madera · Gancho · Brazo mecánico · Brazo médico — por mano o por antebrazo",
              ["Cada tier con sus limitaciones", "Gancho: nada que exija dedos", "Mecánico y médico: armas a dos manos", "Familiaridad con prótesis"])''',
      '''    make_card("arms", ["arms_peg", "arms_hook", "arms_mech", "arms_medical"], "PRÓTESIS DE BRAZO", "Madera · Gancho · Mecánico · Médico — sin mano, sin antebrazo o sin brazo entero",
              ["Cada tier con sus limitaciones", "Gancho: nada que exija dedos", "Mecánico y médico: armas a dos manos", "Por encima del codo: bisagra de codo"])
    make_chainsaw_card()
    make_findyou_card()''')

# ---- ítems: icono del brazo motosierra, 7 columnas
patch('''         ("PegArm", "Brazo de madera"), ("HookArm", "Gancho"), ("MechArm", "Brazo mecánico"), ("MedicalArm", "Brazo médico"),''',
      '''         ("PegArm", "Brazo de madera"), ("HookArm", "Gancho"), ("MechArm", "Brazo mecánico"), ("MedicalArm", "Brazo médico"), ("ChainsawArm", "Brazo motosierra"),''')
patch('''    cols, cell, x0, y0 = 6, 170, 40, 200''', '''    cols, cell, x0, y0 = 7, 150, 40, 200''')
patch('''        cx = x0 + (i % cols) * (cell + 18); cy = y0 + (i // cols) * (cell + 16)''', '''        cx = x0 + (i % cols) * (cell + 14); cy = y0 + (i // cols) * (cell + 16)''')
patch('''        ic = Image.open(os.path.join(TEXD, "Item_%s.png" % nm)).convert("RGBA").resize((112, 112), Image.NEAREST)
        img.alpha_composite(ic, (cx + (cell - 112) // 2, cy + 10))''', '''        ic = Image.open(os.path.join(TEXD, "Item_%s.png" % nm)).convert("RGBA").resize((96, 96), Image.NEAREST)
        img.alpha_composite(ic, (cx + (cell - 96) // 2, cy + 12))''')

# ---- tarjetas nuevas
NEW = r'''
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
    add_blood(img, [(330, 520, 210, 0), (520, 380, 90, 2), (180, 700, 120, 1), (1460, 820, 80, 0)], seed=66)
    paste_render(img, "saw_attack", (-40, 150, 860, 900))
    paste_render(img, "saw_idle", (820, 170, 1240, 880), soft=True)
    box = (1230, 190, 1580, 540)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=14, fill=(0, 0, 0, 150), outline=(196, 32, 38, 200), width=3)
    paste_render(img, "saw_close", box, shadow=False)
    add_blood(img, [(560, 430, 50, 3), (600, 470, 30, 4)], seed=77)
    d = ImageDraw.Draw(img)
    d.text((44, 34), "GROOVY.", font=font(F_TITLE, 96), fill=(0, 0, 0)); d.text((40, 30), "GROOVY.", font=font(F_TITLE, 96), fill=RED)
    d.rectangle((40, 136, 40 + d.textlength("GROOVY.", font=font(F_TITLE, 96)), 143), fill=BONE)
    d.text((40, 156), "Brazo motosierra estilo Ash: el motor al muñón, la espada en línea con el antebrazo", font=font(F_BODY, 30), fill=(215, 210, 200))
    d.text((box[0], box[3] + 14), "Mano, antebrazo o brazo entero", font=font(F_BODY, 22), fill=GREY)
    footer(img, d, ["Tirón de arranque (la Mecánica ayuda)", "Depósito de 0,5 L: échale gasolina", "En marcha corta zombis y extremidades",
                    "Ruido: lo oyen desde lejos", "Mano izquierda libre", "Sólo brazo derecho"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_chainsaw.png")); print("card_chainsaw.png")

def make_findyou_card(w=1600, h=900):
    """Aclara lo que la frase vieja del arrastre daba a entender: en el suelo los zombis NO te ignoran."""
    img = background(w, h, 271).convert("RGBA")
    red_vignette(img, 140)
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(0, 600), (w, 560), (w, h), (0, h)], fill=(30, 28, 30, 255))
    for y in range(580, h, 28): d.line((0, y + 20, w, y), fill=(255, 255, 255, 6))
    blood_smear(img, (1180, 720), (720, 780), 60, seed=9)
    # zombis acercándose desde los lados y desde el fondo
    zs = [("noise_zombie0", (40, 250, 420, 860)), ("noise_zombie1", (1180, 230, 1560, 860)), ("noise_zombie2", (980, 170, 1260, 640))]
    for name, b in zs: paste_render(img, name, b, mirror=(name == "noise_zombie0"))
    pbox = paste_render(img, "crawl2", (360, 470, 1160, 880))
    add_blood(img, [(pbox[0] + 470, pbox[3] - 90, 55, 0)], seed=19)
    d = ImageDraw.Draw(img)
    cx, cy = (pbox[0] + pbox[2]) // 2, (pbox[1] + pbox[3]) // 2 + 20
    for (x0, y0) in ((330, 520), (1270, 500), (1100, 430)):
        arrow(d, (x0, y0), (cx + (x0 - cx) * 0.35, cy + (y0 - cy) * 0.35), (196, 32, 38, 255), width=6, head=22)
    d.text((44, 34), "TUMBADO", font=font(F_TITLE, 96), fill=(0, 0, 0)); d.text((40, 30), "TUMBADO", font=font(F_TITLE, 96), fill=BONE)
    d.text((40, 130), "NO ESTÁS A SALVO", font=font(F_TITLE, 96), fill=RED)
    d.rectangle((40, 236, 40 + d.textlength("NO ESTÁS A SALVO", font=font(F_TITLE, 96)), 243), fill=RED)
    d.text((40, 262), "Arrastrarte no te esconde: los zombis te ven, te oyen y te alcanzan.", font=font(F_BODY, 32), fill=(215, 210, 200))
    footer(img, d, ["Los zombis no te ignoran en el suelo", "Te mueves a paso de rastrero", "Ni correr ni esprintar", "Busca una muleta o una prótesis"], w, h)
    img.convert("RGB").save(os.path.join(OUT, "card_findyou.png")); print("card_findyou.png")
'''
patch('''def make_poster(size=512):''', NEW + '''
def make_poster(size=512):''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("make_workshop.py: tarjetas 3.1.0 añadidas")
