"""Recursos del brazo motosierra (tipo Ash):
- textures/Prosthesis/chainsawArm.png: atlas 128x512. v 0..0.75 = chainsaw.png vanilla repetida 3 veces (la malla
  vanilla usa v hasta 2.12) y v 0.75..1 = bandas de la prótesis (BANDS["saw"] en blender_build.py).
- models_X/Weapons/TOC_Invisible.X: un triángulo minúsculo. Es el modelo en mano del arma interna TOC.Chainsaw:
  la sierra que se ve va dentro de la prótesis (pesada a la mano), el arma sólo existe para que el juego use
  las animaciones de motosierra.
- icono Item_ChainsawArm.png (después de blender_to_x.py, que escribe los .X).
Uso: python make_chainsaw_assets.py [tex|model|icon ...]  (sin argumentos: todo)"""
import os, sys
_args = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

MOD = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
VANILLA_TEX = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media\textures\chainsaw.png"
TILES = 3
what = set(_args) or {"tex", "model", "icon"}

def noise(size, base, var, seed):
    rng = np.random.default_rng(seed)
    arr = np.array(base, float)[None, None, :] + rng.normal(0, var, (size[1], size[0], 3))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

def rows(v0, v1, H=512):
    return int(round(v0 * H)), int(round(v1 * H))

def make_texture():
    W, H = 128, 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    saw = Image.open(VANILLA_TEX).convert("RGBA").resize((W, 128), Image.NEAREST)
    for k in range(TILES): img.paste(saw, (0, 128 * k))
    # bandas (mismas que BANDS["saw"]): cuero, correa, acero, acero oscuro, goma, acero pulido
    band = noise((W, 128), (112, 115, 122), 5, 21)                  # acero pavonado (gris medio, no blanco)
    img.paste(band, (0, 384))
    d = ImageDraw.Draw(img)
    a, b = rows(0.75, 0.80)                     # cuero: grano suave y pespunte en los bordes (sin rayas de duela)
    img.paste(noise((W, b - a), (84, 56, 36), 7, 23), (0, a)); d = ImageDraw.Draw(img)
    for y in (a + 2, b - 3):
        for x in range(0, W, 6): d.line((x, y, x + 3, y), fill=(150, 120, 80, 255))
    a, b = rows(0.80, 0.818); d.rectangle((0, a, W, b), fill=(45, 30, 20, 255))
    a, b = rows(0.818, 0.89)
    for y in range(a, b, 5): d.line((0, y, W, y), fill=(96, 99, 106, 255))
    a, b = rows(0.89, 0.95); d.rectangle((0, a, W, b), fill=(62, 64, 70, 255))
    for x in range(0, W, 6): d.line((x, a, x, b), fill=(50, 52, 58, 255))
    a, b = rows(0.95, 0.97); d.rectangle((0, a, W, b), fill=(30, 30, 32, 255))
    a, b = rows(0.97, 1.0); d.rectangle((0, a, W, H), fill=(205, 207, 212, 255))
    out = os.path.join(MOD, "textures", "Prosthesis", "chainsawArm.png")
    img.save(out); print("tex", out, img.size)

def make_invisible():
    import pzx, build_assets as BA
    v = [BA.v3((0.0, 0.0, 0.0)), BA.v3((0.0005, 0.0, 0.0)), BA.v3((0.0, 0.0005, 0.0))]
    n = [BA.v3((0.0, 0.0, -1.0))] * 3
    out = os.path.join(MOD, "models_X", "Weapons", "TOC_Invisible.X")
    pzx.write_static_x(out, "TOC_Invisible", "Prosthesis/chainsawArm", v, n, [(0.0, 0.99), (0.01, 0.99), (0.0, 0.98)], [(0, 2, 1)])
    print("model", out)

def make_icon(rot=(-20, 30, -45)):
    """Icono 32x32 del modelo de nivel muñeca (el más corto): en diagonal para aprovechar el cuadrado."""
    import render_icons as RI
    tex = RI.tex(os.path.join(MOD, "textures", "Prosthesis", "chainsawArm.png"))
    v, f, uv = RI.load_x(os.path.join(MOD, "models_X", "Prosthesis", "chainsawArmWrist_R_M.X"))
    img = RI.render(v, f, uv, tex, RI.rot(*rot), fill=0.97, bright=1.3)
    ic = RI.to_icon(img, thicken=1)
    # fuera píxeles sueltos (islas de menos de 10 px que deja el contorno)
    a = np.array(ic)[..., 3] > 0; seen = np.zeros_like(a); arr = np.array(ic)
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            if a[y, x] and not seen[y, x]:
                stack, comp = [(y, x)], []; seen[y, x] = True
                while stack:
                    cy, cx = stack.pop(); comp.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < a.shape[0] and 0 <= nx < a.shape[1] and a[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
                if len(comp) < 10:
                    for cy, cx in comp: arr[cy, cx] = 0
    ic = Image.fromarray(arr, "RGBA")
    ic.save(os.path.join(MOD, "textures", "Item_ChainsawArm.png"))
    big = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA")
    sheet = Image.new("RGBA", (big.width + 140, big.height), (60, 60, 60, 255))
    sheet.alpha_composite(big, (0, 0)); up = ic.resize((128, 128), Image.NEAREST); sheet.alpha_composite(up, (big.width + 6, 6))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview", "icon_chainsawArm.png")
    os.makedirs(os.path.dirname(out), exist_ok=True); sheet.save(out); print("icon Item_ChainsawArm.png ->", out)

if "tex" in what: make_texture()
if "model" in what: make_invisible()
if "icon" in what: make_icon()
