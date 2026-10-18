"""Imágenes de presentación 1920x1080 de los brazos-arma (3.2.0): la pose de ataque en grande y dos recuadros (cuerpo
entero y el brazo de cerca), con ropa del juego (export_merle_scene.py, export_ash_scene.py). Se guardan con el resto de
imágenes del Workshop: out/workshop/showcase_*.png (ES) y out/workshop/en/showcase_*.png (EN).
Renders: out/preview/merle_hi y out/preview/ash_hi (blender_render.py, 1600 px).
Uso: python make_showcase.py"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.join(HERE, "out", "preview")
OUT = {"es": os.path.join(HERE, "out", "workshop"), "en": os.path.join(HERE, "out", "workshop", "en")}

SHOWS = {
    "bayonet": dict(dir="merle_hi", main="merle_stab_side", full="merle_idle_full", full_crop=(470, 0, 1134, 1600),
                    close="merle_idle_close2", close_crop=(410, 0, 978, 1600),
                    es=("EL BRAZO DE MERLE", "Cabezal de bayoneta sobre una base de chatarra: cuero, cinta americana y una bayoneta.", "Brazo derecho, Soldadura 2  ·  The Only Cure+ 3.3"),
                    en=("MERLE'S BAYONET ARM", "Bayonet attachment on a scrap base: leather, duct tape and a bayonet.", "Right arm, Welding 2  ·  The Only Cure+ 3.3")),
    "chainsaw": dict(dir="ash_hi", main="ash_hero_full", full="ash_idle_back", full_crop=(400, 0, 1210, 1600),
                     close="ash_close", close_crop=(576, 0, 1144, 1600),
                     es=("GROOVY: EL BRAZO MOTOSIERRA", "Estilo Ash: cabezal de motosierra montado en cualquier base de metal.", "Brazo derecho, Soldadura 5 y Mecánica 4  ·  The Only Cure+ 3.3"),
                     en=("GROOVY: THE CHAINSAW ARM", "Ash style: a chainsaw attachment mounted on any metal base.", "Right arm, Welding 5 and Mechanics 4  ·  The Only Cure+ 3.3")),
}

def compose(cfg, lang):
    W, H = 1920, 1080
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W * 0.36) / W) ** 2 + ((y - H * 0.45) / H) ** 2)
    v = np.clip(1 - r * 1.25, 0, 1)
    img = Image.fromarray(np.stack([26 + 30 * v, 25 + 26 * v, 24 + 20 * v], -1).astype(np.uint8), "RGB").convert("RGBA")
    def place(name, box, crop=None, valign="center"):
        im = Image.open(os.path.join(PV, cfg["dir"], name + ".png")).convert("RGBA")
        if crop: im = im.crop(crop)
        s = min(box[2] / im.width, box[3] / im.height)
        im = im.resize((int(round(im.width * s)), int(round(im.height * s))), Image.LANCZOS)
        yy = box[1] + (box[3] - im.height) // 2 if valign == "center" else box[1] + box[3] - im.height
        img.alpha_composite(im, (box[0] + (box[2] - im.width) // 2, yy))
    place(cfg["main"], (-40, 0, 1180, 1080))
    for k, (name, crop, va) in enumerate(((cfg["full"], cfg["full_crop"], "bottom"), (cfg["close"], cfg["close_crop"], "center"))):
        x0, y0, w0, h0 = 1140 + k * 380, 40, 360, 1000
        img.alpha_composite(Image.new("RGBA", (w0, h0), (34, 33, 32, 235)), (x0, y0))
        place(name, (x0 + 4, y0 + 4, w0 - 8, h0 - 8), crop, va)
        ImageDraw.Draw(img).rectangle((x0, y0, x0 + w0 - 1, y0 + h0 - 1), outline=(120, 96, 64, 255), width=2)
    d = ImageDraw.Draw(img)
    title, sub, foot = cfg[lang]
    size = 64
    while True:
        ft = ImageFont.truetype("arialbd.ttf", size)
        if d.textlength(title, font=ft) <= 1060 or size <= 40: break
        size -= 2
    fs = ImageFont.truetype("arial.ttf", 30)
    d.text((60, 860), title, fill=(232, 222, 200, 255), font=ft)
    d.text((64, 940), sub, fill=(200, 190, 170, 255), font=fs)
    d.text((64, 980), foot, fill=(170, 140, 96, 255), font=fs)
    return img.convert("RGB")

if __name__ == "__main__":
    for name, cfg in SHOWS.items():
        for lang, out in OUT.items():
            p = os.path.join(out, "showcase_%s.png" % name)
            compose(cfg, lang).save(p); print(p)
