"""Apariencias pintables de las piezas modulares (2026-10-17, parte opcional de la 3.3, prevista para la 3.4): una
variante de cada atlas por color de pintura vanilla, en textures/Prosthesis/Paint/<atlas>_<color>.png. Sólo se tiñen las
bandas pintables (carcasas, placas, madera); cuero, goma, juntas y acentos quedan como están. Se conserva la luminancia
del original (arañazos, desgaste, líneas), así que la pintura se ve gastada igual que la pieza.
El orden de PAINTS es el índice de textureChoices (0 = acabado original) que usa TOC/Plus/ProsthesisPaint.lua.
Uso: TOC_MEDIA=...Dev python make_paint_variants.py"""
import os
import numpy as np
from PIL import Image

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
# mismo orden que PAINTS en ProsthesisPaint.lua (índice + 1)
PAINTS = [("Black", (38, 38, 42)), ("White", (232, 232, 228)), ("Grey", (128, 130, 134)), ("Red", (168, 34, 30)),
          ("Orange", (214, 104, 28)), ("Yellow", (222, 184, 40)), ("Green", (78, 102, 52)), ("Blue", (40, 72, 150)),
          ("Purple", (98, 52, 130)), ("Pink", (214, 116, 150))]
# atlas -> bandas pintables (fracciones de v = alto de la imagen), de BANDS en blender_build.py
PAINTABLE = {"pegArm": [(0.30, 0.90)], "knifeArm": [(0.30, 0.60)], "hookArm": [(0.30, 0.60)],
             "normalArm": [(0.20, 0.86)], "medicalArm": [(0.20, 1.0)], "cyberArm": [(0.14, 0.46)],
             # piernas (2026-10-17, "quiero que las piernas se pinten también"): madera de la pata de palo, acero de la
             # mecánica, polímero (encaje y carcasa) de la médica; la cyber comparte cyberArm
             "pegLeg": [(0.30, 0.91)], "mechLeg": [(0.20, 0.86)], "medicalLeg": [(0.0, 0.20)]}

def tint(region, rgb):
    a = region.astype(float)
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    m = max(1.0, float(np.median(lum)))
    rel = np.clip(lum / m, 0.35, 1.6)[..., None]              # detalle del original alrededor de 1
    col = np.array(rgb, float)[None, None, :]
    out = col * (0.55 + 0.45 * rel) if sum(rgb) > 450 else col * rel
    a[..., :3] = np.clip(out, 0, 255)
    return a.astype(np.uint8)

def main():
    src_dir = os.path.join(MOD, "textures", "Prosthesis"); out_dir = os.path.join(src_dir, "Paint")
    os.makedirs(out_dir, exist_ok=True)
    for atlas, bands in PAINTABLE.items():
        im = np.array(Image.open(os.path.join(src_dir, atlas + ".png")).convert("RGBA"))
        H = im.shape[0]
        for name, rgb in PAINTS:
            out = im.copy()
            for v0, v1 in bands:
                a, b = int(round(v0 * H)), int(round(v1 * H))
                out[a:b] = tint(im[a:b], rgb)
            Image.fromarray(out, "RGBA").save(os.path.join(out_dir, "%s_%s.png" % (atlas, name.lower())))
        print("pintura", atlas, len(PAINTS))

if __name__ == "__main__":
    main()
