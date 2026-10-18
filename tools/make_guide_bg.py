"""Fondos de página de la guía PDF (mismo estilo que las tarjetas del Workshop). Uso: python make_guide_bg.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "en"]
exec(compile(open(os.path.join(HERE, "make_workshop.py"), encoding="utf-8").read().split("def make_hero")[0], "make_workshop.py", "exec"))
img = background(1684, 1190, seed=9).convert("RGBA"); red_vignette(img, 45)
img.convert("RGB").save(os.path.join(HERE, "out", "guide_bg.jpg"), quality=86)
img = background(1684, 1190, seed=4).convert("RGBA"); red_vignette(img, 90)
add_blood(img, [(1500, 1050, 160, 3), (150, 120, 90, 2), (1600, 160, 60, 0)], seed=5)
img.convert("RGB").save(os.path.join(HERE, "out", "guide_cover_bg.jpg"), quality=86)
print("ok")
