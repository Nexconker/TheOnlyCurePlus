"""Miniatura clicable de la guía para la descripción del Workshop (2026-10-18, "un thumbnail clicable en la descripción
que les deje ver una guía del mod"). Mismo estilo que las tarjetas (make_workshop.py: fondo, cinta, renders).
Sale en out/workshop/en/guide_banner.png (1260x440, Steam la muestra a ~630 px) y se copia a docs/ del repo.
Uso: python make_guide_banner.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "en"]
src = open(os.path.join(HERE, "make_workshop.py"), encoding="utf-8").read().split("def make_hero")[0]
exec(compile(src, "make_workshop.py", "exec"))

W, H = 1260, 440
img = background(W, H, seed=5).convert("RGBA")
red_vignette(img, 60)
add_blood(img, [(1180, 420, 70, 0), (40, 30, 50, 2)], seed=21)
# a la derecha: la chica cyber con la pistola, la mano mecánica y el libro de la guía
paste_render(img, "cyber_grip", (860, 20, 1250, 460))
paste_render(img, "prop_bench", (640, 210, 900, 430))
paste_render(img, "prop_cyberhand", (520, 300, 680, 430), rotate=12)
MOD_TEX = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\textures"
book = Image.open(os.path.join(MOD_TEX, "Item_FieldSurgeryGuide.png")).convert("RGBA").resize((128, 128), Image.NEAREST)
img.alpha_composite(shadowed(book, 8, 160), (655, 74)); img.alpha_composite(book, (648, 64))
d = ImageDraw.Draw(img)
def cross(d, x, y, r, col=RED):
    d.rectangle((x - r, y - r // 3, x + r, y + r // 3), fill=col); d.rectangle((x - r // 3, y - r, x + r // 3, y + r), fill=col)
d.rectangle((0, 0, W, 40), fill=RED2)
x = -20
while x < W:
    d.text((x, 8), "READ BEFORE ASKING", font=font(F_BOLD, 22), fill=(255, 220, 220)); x += d.textlength("READ BEFORE ASKING", font=font(F_BOLD, 22)) + 30
    cross(d, x - 2, 20, 8, (255, 220, 220)); x += 30
y = title_block(d, 44, 62, "PLAYER GUIDE", "The Only Cure+ 3.3 · interactive PDF", size=104, subsize=30)
for i, ln in enumerate(["Bitten? What to do, step by step", "Surgery, prostheses, workbench and paint", "Recipes, sandbox options and FAQ"]):
    cross(d, 60, y + 25 + i * 38, 8); d.text((80, y + 8 + i * 38), ln, font=font(F_BODY, 28), fill=(215, 210, 200))
# botón
bx, by, bw, bh = 50, H - 76, 330, 54
d.rounded_rectangle((bx + 5, by + 6, bx + bw + 5, by + bh + 6), 10, fill=(0, 0, 0, 160))
d.rounded_rectangle((bx, by, bx + bw, by + bh), 10, fill=RED)
d.text((bx + bw // 2 - 16, by + bh // 2), "OPEN THE GUIDE", font=font(F_TITLE, 32), fill=BONE, anchor="mm")
d.polygon([(bx + bw - 44, by + 15), (bx + bw - 44, by + bh - 15), (bx + bw - 22, by + bh // 2)], fill=BONE)
out = os.path.join(OUT, "guide_banner.png")
img.convert("RGB").save(out); print(out)
