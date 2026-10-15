"""Sangre y manchas en las imágenes del Workshop + tarjeta de ítems nuevos + renders de modelos de suelo."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

p = os.path.join(HERE, "blender_render.py"); s = open(p, encoding="utf-8").read()
old = '    "crutch": ([("crutch", 0, 0)], 10, 150, None, None),'
new = '''    "crutch": ([("crutch", 0, 0)], 10, 150, None, None),
    "prop_hook": ([("hook_ground", 0, 0)], 40, 150, None, None),
    "prop_mechleg": ([("mechleg_ground", 0, 0)], 40, 150, None, None),
    "prop_leg": ([("severed_leg", 0, 0)], 40, 150, None, None),'''
if old in s and "prop_hook" not in s:
    s = s.replace(old, new); open(p, "w", encoding="utf-8", newline="\n").write(s)
print("render jobs ok")

p = os.path.join(HERE, "make_workshop.py"); s = open(p, encoding="utf-8").read()
BLOOD = '''import random
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

def shadowed(img, blur=18, alpha=170):'''
pairs = [
("def shadowed(img, blur=18, alpha=170):", BLOOD),
('''    paste_render(img, "hero_m", (1180, -30, 1950, 1090))
    paste_render(img, "hero_f", (820, 40, 1460, 1090))
    d = ImageDraw.Draw(img)''',
'''    red_vignette(img, 80)
    add_blood(img, [(1500, 985, 150, 0), (1120, 960, 110, 0), (1760, 1010, 80, 0)], seed=3)
    paste_render(img, "hero_m", (1180, -30, 1950, 1090))
    paste_render(img, "hero_f", (820, 40, 1460, 1090))
    add_blood(img, [(1860, 120, 70, 3), (60, 1000, 90, 0)], seed=11)
    d = ImageDraw.Draw(img)'''),
('''    img = background(size, size, 2).convert("RGBA")
    paste_render(img, "hero_m", (330, 200, 1010, 940))
    paste_render(img, "hero_f", (10, 250, 620, 940))''',
'''    img = background(size, size, 2).convert("RGBA")
    red_vignette(img, 70)
    add_blood(img, [(700, 905, 120, 0), (300, 890, 90, 0)], seed=5)
    paste_render(img, "hero_m", (330, 200, 1010, 940))
    paste_render(img, "hero_f", (10, 250, 620, 940))
    add_blood(img, [(960, 60, 60, 4)], seed=9)'''),
('def make_card(name, renders, title, sub, bullets, w=1600, h=900):\n    img = background(w, h, hash(name) % 1000).convert("RGBA")\n    n = len(renders); cw = (w - 80) // n\n',
 'def make_card(name, renders, title, sub, bullets, w=1600, h=900, blood_before=(), blood_after=(), vignette=0):\n    img = background(w, h, hash(name) % 1000).convert("RGBA")\n    if vignette: red_vignette(img, vignette)\n    if blood_before: add_blood(img, blood_before, seed=len(name))\n    n = len(renders); cw = (w - 80) // n\n'),
('''    d = ImageDraw.Draw(img)
    d.text((44, 34), title, font=font(F_TITLE, 84), fill=(0, 0, 0)); d.text((40, 30), title, font=font(F_TITLE, 84), fill=BONE)''',
'''    if blood_after: add_blood(img, blood_after, seed=len(name) + 1)
    d = ImageDraw.Draw(img)
    d.text((44, 34), title, font=font(F_TITLE, 84), fill=(0, 0, 0)); d.text((40, 30), title, font=font(F_TITLE, 84), fill=BONE)'''),
('''              ["Ventana de cura e infección visible", "Sepsis y convalecencia", "Sierra de hueso y kit quirúrgico", "Muleta o arrastre sin piernas"])''',
'''              ["Ventana de cura e infección visible", "Sepsis y convalecencia", "Sierra de hueso y kit quirúrgico", "Muleta o arrastre sin piernas"],
              blood_before=[(300, 790, 170, 0), (1020, 760, 120, 0)], blood_after=[(210, 650, 40, 5), (300, 640, 30, 3), (1420, 140, 50, 4)], vignette=90)
    make_items_card()'''),
('''              ["Encajes a la medida del muñón", "Rodilla articulada en las de muslo", "Caben bajo el pantalón", "Se desgastan y se reparan"])''',
'''              ["Encajes a la medida del muñón", "Rodilla articulada en las de muslo", "Caben bajo el pantalón", "Se desgastan y se reparan"],
              blood_before=[(120, 800, 90, 0), (1380, 780, 70, 0)], vignette=50)'''),
('def make_poster(size=512):',
'''ITEMS = [("BoneSaw", "Sierra de hueso"), ("SurgicalKit", "Kit quirúrgico"), ("FieldSurgeryGuide", "Guía de cirugía"), ("Crutch", "Muleta"), ("LegTourniquet", "Torniquete de pierna"),
         ("PegArm", "Brazo de madera"), ("HookArm", "Gancho"), ("MechArm", "Brazo mecánico"), ("MedicalArm", "Brazo médico"),
         ("PegLeg", "Pata de palo"), ("MechLeg", "Pierna mecánica"), ("MedicalLeg", "Pierna médica"),
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
    cols, cell, x0, y0 = 6, 170, 40, 200
    fl = font(F_BODY, 20)
    for i, (nm, label) in enumerate(ITEMS):
        cx = x0 + (i % cols) * (cell + 18); cy = y0 + (i // cols) * (cell + 16)
        d.rounded_rectangle((cx, cy, cx + cell, cy + cell), radius=10, fill=(0, 0, 0, 110), outline=(255, 255, 255, 25))
        ic = Image.open(os.path.join(TEXD, "Item_%s.png" % nm)).convert("RGBA").resize((112, 112), Image.NEAREST)
        img.alpha_composite(ic, (cx + (cell - 112) // 2, cy + 10))
        tw = d.textlength(label, font=fl)
        d.text((cx + (cell - tw) / 2, cy + cell - 36), label, font=fl, fill=(225, 220, 210))
    d.text((1180, 200), "En el suelo", font=font(F_BOLD, 26), fill=GREY)
    paste_render(img, "prop_hook", (1180, 240, 1560, 440))
    paste_render(img, "prop_mechleg", (1180, 440, 1560, 640))
    paste_render(img, "prop_leg", (1180, 640, 1560, 860))
    img.convert("RGB").save(os.path.join(OUT, "card_items.png")); print("card_items.png")

def make_poster(size=512):'''),
]
for a, b in pairs:
    if b in s: continue
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("make_workshop patched")
