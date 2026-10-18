"""Iconos 32x32 de las piezas modulares 3.3 (bases y cabezales), renderizados de sus modelos como el resto de iconos.
Uso: TOC_MEDIA=...TheOnlyCurePlusDev\\42\\media python make_modular_icons.py  -> textures/Item_<Pieza>.png + lámina"""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import render_icons as RI

MX = os.path.join(RI.MOD, "models_X", "Prosthesis")
TX = os.path.join(RI.MOD, "textures", "Prosthesis")
# icono: (modelo, atlas, giro, relleno, brillo, contorno)
ICONS = {
    "BaseWood":     ("baseWood_L_M", "pegArm", (22, 0, -40), 0.9, 1.3, 1),
    "BaseScrap":    ("baseScrap_L_M", "knifeArm", (22, 0, -40), 0.9, 1.3, 1),
    "BaseMech":     ("baseMech_L_M", "normalArm", (22, 0, -40), 0.9, 1.3, 1),
    "BaseMed":      ("baseMed_L_M", "medicalArm", (22, 0, -40), 0.9, 1.6, 0),
    "HeadKnob":     ("headKnob_L_M", "pegArm", (10, 0, -40), 0.85, 1.3, 1),
    "HeadHook":     ("headHook_L_M", "hookArm", (10, 0, -40), 0.85, 1.3, 1),
    "HeadMechHand": ("headMechHand_L_M", "normalArm", (10, 0, -40), 0.85, 1.3, 1),
    "HeadMedHand":  ("headMedHand_L_M", "medicalArm", (10, 0, -40), 0.85, 1.6, 0),
    "HeadChainsaw": ("headChainsaw_R_M", "chainsawArm", (-20, 30, -45), 0.95, 1.3, 1),
    "HeadBayonet":  ("headBayonet_R_M", "knifeArm", (-20, 30, -45), 0.9, 1.25, 1),
    "BaseCyber":    ("baseCyber_L_M", "cyberArm", (22, 0, -40), 0.9, 1.3, 1),
    "HeadCyberHand": ("headCyberHand_L_M", "cyberArm", (10, 0, -40), 0.85, 1.3, 1),
}
res = []
for name, (model, tex, r, fill, bright, thick) in ICONS.items():
    v, f, uv = RI.load_x(os.path.join(MX, model + ".X"))
    ic = RI.to_icon(RI.render(v, f, uv, RI.tex(os.path.join(TX, tex + ".png")), RI.rot(*r), fill=fill, bright=bright), thicken=thick)
    ic.save(os.path.join(RI.MOD, "textures", "Item_%s.png" % name)); res.append((name, ic)); print("icon", name)
sheet = Image.new("RGBA", (104 * len(res), 120), (60, 60, 60, 255)); d = ImageDraw.Draw(sheet)
for i, (n, ic) in enumerate(res):
    sheet.paste(ic.resize((96, 96), Image.NEAREST), (i * 104 + 4, 4)); d.text((i * 104 + 4, 104), n[:14], fill=(255, 255, 255, 255))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview", "icons_modular.png")
sheet.save(out); print("lámina", out)
