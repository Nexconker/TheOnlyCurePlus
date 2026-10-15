"""Banner de Ko-fi para la descripción del Workshop (mismo estilo que las portadas de make_workshop.py: fondo oscuro,
viñeta roja, sangre, el brazo motosierra de cerca) con una taza en pixel art como los iconos del juego.
Se sube al repositorio (docs/kofi_banner.png) para enlazarlo con [img] desde la descripción de Steam.
Uso: python make_kofi_banner.py  ->  out/workshop/en/kofi_banner.png"""
import os, sys
sys.argv = [sys.argv[0], "en"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make_workshop as MW

URL = "ko-fi.com/nexconker"

MUG = [
    "....s...s...s...........",
    "...s...s...s............",
    "....s...s...s...........",
    "...s...s...s............",
    "....s...s...s...........",
    "........................",
    "...WWWWWWWWWWWWW........",
    "...WCCCCCCCCCCCW........",
    "...WWWWWWWWWWWWWWWW.....",
    "...WWWWWWWWWWWWW..WW....",
    "...WWWWWWRWWWWWW...W....",
    "...WWWWWWRWWWWWW...W....",
    "...WWWWRRRRRWWWW...W....",
    "...WWWWWWRWWWWWW...W....",
    "...WWWWWWRWWWWWW..WW....",
    "...WWWWWWWWWWWWWWWW.....",
    "...WWWWWWWWWWWWW........",
    "....WWWWWWWWWWW.........",
    ".....WWWWWWWWW..........",
    "........................",
]
PAL = {"W": ((250, 246, 236), (226, 220, 206), (176, 168, 152)), "R": ((232, 58, 52), (196, 32, 38), (130, 14, 18)),
       "C": ((110, 70, 44), (78, 48, 30), (52, 30, 18))}
OUTLINE = (30, 22, 20)

def pixel_mug(scale=10):
    h, w = len(MUG), len(MUG[0])
    mat = np.array([list(r) for r in MUG])
    solid = np.isin(mat, list(PAL))
    img = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            m = mat[y, x]
            if m in PAL:
                hi, base, sh = PAL[m]
                c = base
                if x == 0 or mat[y, x - 1] != m or y == 0 or mat[y - 1, x] != m: c = hi
                if x == w - 1 or not solid[y, x + 1]: c = sh
                if m == "W" and y < h - 1 and not solid[y + 1, x]: c = sh
                img[y, x] = (*c, 255)
            elif m == "s":
                img[y, x] = (220, 220, 225, 150)
    for y in range(h):
        for x in range(w):
            if solid[y, x] or mat[y, x] == "s": continue
            if any(0 <= y + dy < h and 0 <= x + dx < w and solid[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img[y, x] = (*OUTLINE, 255)
    return Image.fromarray(img, "RGBA").resize((w * scale, h * scale), Image.NEAREST)

def make(w=1200, h=400):
    img = MW.background(w, h, 77).convert("RGBA")
    MW.red_vignette(img, 110)
    MW.add_blood(img, [(110, 360, 70, 2), (1150, 50, 40, 1), (1080, 380, 45, 0)], seed=31)
    MW.paste_render(img, "saw_close", (-30, 10, 380, 400), soft=True)
    d = ImageDraw.Draw(img)
    x = 360
    ft = MW.font(MW.F_TITLE, 84)
    d.text((x + 5, 40), "ENJOYING TOC+?", font=ft, fill=(0, 0, 0)); d.text((x, 35), "ENJOYING TOC+?", font=ft, fill=MW.BONE)
    tw = d.textlength("ENJOYING TOC+?", font=ft)
    d.rectangle((x, 128, x + tw, 135), fill=MW.RED)
    fb = MW.font(MW.F_BODY, 32)
    d.text((x, 152), "Buy the surgeon a coffee on Ko-fi.", font=fb, fill=(225, 220, 210))
    d.text((x, 192), "It keeps the updates coming. The mod stays free.", font=MW.font(MW.F_BODY, 26), fill=MW.GREY)
    # botón
    fu = MW.font(MW.F_BOLD, 34)
    uw = d.textlength(URL, font=fu)
    bx0, by0, bx1, by1 = x, 262, x + uw + 70, 334
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((bx0 + 6, by0 + 8, bx1 + 6, by1 + 8), 18, fill=(0, 0, 0, 160))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((bx0, by0, bx1, by1), 18, fill=MW.RED, outline=(240, 120, 120), width=2)
    d.text((bx0 + 35, by0 + 13), URL, font=fu, fill=(255, 240, 236))
    mug = pixel_mug(10)
    img.alpha_composite(MW.shadowed(mug, 10, 150), (w - mug.width - 34 + 8, 72 + 14))
    img.alpha_composite(mug, (w - mug.width - 34, 72))
    out = os.path.join(MW.OUT, "kofi_banner.png")
    os.makedirs(MW.OUT, exist_ok=True)
    img.convert("RGB").save(out); print(out)
    return out

if __name__ == "__main__":
    make()
