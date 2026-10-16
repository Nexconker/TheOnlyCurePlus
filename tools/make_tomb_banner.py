"""Banner "compatible con Tomb's Player Body" para la descripción del Workshop. SÓLO para publicar junto con el submod
TombBody fit (cuando Tomb dé permiso): sin el submod, la 3.1.x sola no arregla cadera ni hombro en su cuerpo.
Usa los renders tbanner_* de tomb_preview/tomb_showcase (su cuerpo con su textura). Uso: python make_tomb_banner.py"""
import os, sys
sys.argv = [sys.argv[0], "en"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import make_workshop as MW

def make(w=1200, h=420):
    img = MW.background(w, h, 91).convert("RGBA")
    MW.red_vignette(img, 100)
    MW.add_blood(img, [(80, 400, 60, 1), (1170, 40, 35, 0)], seed=12)
    MW.paste_render(img, "tbanner_m", (600, 10, 820, 415))
    MW.paste_render(img, "tbanner_f", (790, 0, 990, 418))
    MW.paste_render(img, "tbanner_f2", (965, 10, 1190, 415))
    d = ImageDraw.Draw(img)
    x = 40
    ft = MW.font(MW.F_TITLE, 66)
    for i, (txt, col) in enumerate((("TOMB'S PLAYER BODY", MW.BONE), ("NOW SUPPORTED", MW.RED))):
        y = 34 + i * 74
        d.text((x + 4, y + 4), txt, font=ft, fill=(0, 0, 0)); d.text((x, y), txt, font=ft, fill=col)
    d.rectangle((x, 186, x + d.textlength("TOMB'S PLAYER BODY", font=ft), 192), fill=MW.RED)
    d.text((x, 206), "Optional add-on: The Only Cure+ - TombBody fit", font=MW.font(MW.F_BODY, 27), fill=(228, 222, 210))
    fb = MW.font(MW.F_BODY, 22)
    for i, b in enumerate(("Stumps built on Tomb's body: hips and shoulders match",
                           "Every prosthesis refitted to its shape",
                           "Uses your Tomb texture: normal, DOLL or NUDE")):
        yy = 256 + i * 34
        d.rectangle((x, yy + 8, x + 10, yy + 18), fill=MW.RED)
        d.text((x + 22, yy), b, font=fb, fill=(215, 210, 200))
    d.text((x, 372), "Tomb's Player Body is made by Tomb.", font=MW.font(MW.F_BODY, 18), fill=MW.GREY)
    out = os.path.join(MW.OUT, "tombbody_banner.png")
    os.makedirs(MW.OUT, exist_ok=True)
    img.convert("RGB").save(out); print(out)

def make_poster(size=512):
    """Póster e icono del submod en la lista de mods del juego."""
    img = MW.background(size, size, 93).convert("RGBA")
    MW.red_vignette(img, 110)
    MW.paste_render(img, "tbanner_f2", (150, 40, 510, 512))
    d = ImageDraw.Draw(img)
    for i, (txt, col, sz) in enumerate((("THE ONLY", MW.BONE, 62), ("CURE+", MW.BONE, 62), ("TOMBBODY", MW.RED, 54), ("FIT", MW.RED, 54))):
        f = MW.font(MW.F_TITLE, sz); y = 24 + i * 66
        d.text((24 + 3, y + 3), txt, font=f, fill=(0, 0, 0)); d.text((24, y), txt, font=f, fill=col)
    out = os.path.join(MW.OUT, "tombbody_poster.png")
    img.convert("RGB").save(out); img.convert("RGB").resize((64, 64), Image.LANCZOS).save(os.path.join(MW.OUT, "tombbody_icon.png")); print(out)

if __name__ == "__main__":
    make()
    make_poster()
