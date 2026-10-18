"""Recursos del brazo bayoneta (3.2.0, estilo Merle):
- textures/Prosthesis/knifeArm.png: atlas 128x512 con las bandas de BANDS["hook"] en blender_build.py (cuero, correa,
  acero, acero oscuro, goma, pulido), con el cuero cosido del brazo motosierra en vez de las duelas del gancho.
- icono Item_KnifeArm.png (después de blender_to_x.py, que escribe los .X).
El arma interna TOC.MountedBlade usa el modelo invisible de la motosierra (models_X/Weapons/TOC_Invisible.X).
Uso: python make_knife_assets.py [tex|icon ...]  (sin argumentos: todo)"""
import os, sys
_args = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")
what = set(_args) or {"tex", "icon"}
W, H = 128, 512

def noise(size, base, var, seed):
    rng = np.random.default_rng(seed)
    arr = np.array(base, float)[None, None, :] + rng.normal(0, var, (size[1], size[0], 3))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

def rows(v0, v1): return int(round(v0 * H)), int(round(v1 * H))

def fbm(w, h, seed, octaves=4, base=4):
    """Ruido fractal 0..1 (suma de rejillas aleatorias ampliadas): manchas de óxido, desgaste."""
    rng = np.random.default_rng(seed); acc = np.zeros((h, w)); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw, gh = max(2, base * 2 ** o), max(2, int(base * 2 ** o * h / w))
        g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(g, float) / 255; tot += amp; amp *= 0.5
    return acc / tot

def scratches(arr, rng, n, length, color, alpha, vertical=False):
    """Rayones cortos (líneas finas) sobre un trozo de atlas (H x W x 3, float)."""
    h, w = arr.shape[:2]
    for _ in range(n):
        x, y = rng.integers(0, w), rng.integers(0, h)
        L = rng.integers(length // 2, length + 1); ang = rng.normal(np.pi / 2 if vertical else 0, 0.35)
        for t in range(L):
            xi, yi = int(x + t * np.cos(ang)) % w, int(y + t * np.sin(ang))
            if 0 <= yi < h: arr[yi, xi] = arr[yi, xi] * (1 - alpha) + np.array(color, float) * alpha

def rust_metal(w, h, base, seed, rust=0.45, pits=60):
    """Chapa de chatarra: gris sucio, óxido en manchas (más en los bordes de la banda), picaduras y rayones."""
    rng = np.random.default_rng(seed)
    n = fbm(w, h, seed); n2 = fbm(w, h, seed + 7, base=8)
    arr = np.array(base, float)[None, None, :] * (0.82 + 0.3 * n[..., None])
    edge = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None] / max(1, h / 2)       # óxido en los bordes
    r = 0.8 * np.clip((n2 - (1 - rust)) * 2.5 + (0.3 - edge) * 0.8, 0, 1)[..., None]
    rc = np.stack([88 + 26 * n, 56 + 14 * n, 38 + 8 * n], -1)                              # óxido pardo, apagado
    arr = arr * (1 - r) + rc * r
    for _ in range(pits):                                                                 # picaduras
        x, y = rng.integers(0, w), rng.integers(0, h); arr[y, x] *= 0.55
    scratches(arr, rng, 14, 12, (150, 148, 144), 0.28)
    scratches(arr, rng, 10, 9, (40, 36, 32), 0.3)
    return arr

def worn_leather(w, h, base, seed):
    rng = np.random.default_rng(seed)
    n = fbm(w, h, seed, base=3); n2 = fbm(w, h, seed + 3, base=10)
    arr = np.array(base, float)[None, None, :] * (0.84 + 0.24 * n[..., None])
    arr *= (1.0 + 0.12 * np.clip((n2 - 0.65) * 6, 0, 1)[..., None])                      # rozaduras claras
    arr *= (1.0 - 0.18 * np.clip((0.32 - n2) * 6, 0, 1)[..., None])                      # grasa y suciedad
    scratches(arr, rng, 12, 8, (140, 110, 80), 0.22)
    return arr

def make_texture():
    """Rudimentaria (2026-10-16: "quiero que la prótesis se vea rudimentaria con el cuchillo de Merle"): chatarra
    oxidada y rayada, cuero viejo y costuras a mano, hoja usada con marcas de afilado."""
    rng = np.random.default_rng(41)
    img = np.zeros((H, W, 3), float)
    a, b = rows(0.0, 0.26); img[a:b] = worn_leather(W, b - a, (78, 52, 33), 51)           # brazal
    a, b = rows(0.26, 0.30); img[a:b] = worn_leather(W, b - a, (40, 28, 19), 53)          # correas
    a, b = rows(0.30, 0.60); img[a:b] = rust_metal(W, b - a, (104, 102, 98), 55, rust=0.5)   # chapa de las carcasas
    a, b = rows(0.60, 0.86); img[a:b] = rust_metal(W, b - a, (58, 56, 54), 57, rust=0.38)    # hierro negro (casquete, guarda)
    a, b = rows(0.86, 0.94)                                                                 # cinta americana gris, sucia
    tape = np.array((122, 122, 118), float)[None, None, :] * (0.8 + 0.3 * fbm(W, b - a, 59, base=6)[..., None])
    for y in range(0, b - a, 5): tape[y] *= 0.86                                            # bordes de las vueltas
    img[a:b] = tape
    a, b = rows(0.94, 1.0)                                                                  # hoja usada
    blade = np.array((168, 168, 166), float)[None, None, :] * (0.85 + 0.25 * fbm(W, b - a, 61, base=6)[..., None])
    scratches(blade, rng, 40, 18, (205, 205, 203), 0.4); scratches(blade, rng, 14, 12, (100, 96, 90), 0.3)
    stain = (fbm(W, b - a, 63, base=5) > 0.68)[..., None]
    img[a:b] = np.where(stain, blade * np.array([0.78, 0.66, 0.55]), blade)               # manchas de óxido / sangre seca
    out_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(out_img)
    a, b = rows(0.0, 0.26)                                                                  # costuras a mano, irregulares
    for y0 in (a + 3, b - 5):
        x = 0
        while x < W:
            dx = int(rng.integers(4, 8)); yy = y0 + int(rng.integers(-1, 2))
            d.line((x, yy, x + dx // 2, yy + int(rng.integers(-1, 2))), fill=(128, 104, 72, 255)); x += dx
    out = os.path.join(MOD, "textures", "Prosthesis", "knifeArm.png")
    out_img.save(out); print("tex", out, out_img.size)

def make_icon(rot=(-20, 30, -45)):
    """Icono 32x32 del modelo de nivel muñeca (el más corto), en diagonal como el del brazo motosierra."""
    import render_icons as RI
    tex = RI.tex(os.path.join(MOD, "textures", "Prosthesis", "knifeArm.png"))
    v, f, uv = RI.load_x(os.path.join(MOD, "models_X", "Prosthesis", "knifeArmWrist_R_M.X"))
    img = RI.render(v, f, uv, tex, RI.rot(*rot), fill=0.97, bright=1.25)
    ic = RI.to_icon(img, thicken=1)
    ic.save(os.path.join(MOD, "textures", "Item_KnifeArm.png"))
    big = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA")
    sheet = Image.new("RGBA", (big.width + 140, big.height), (60, 60, 60, 255))
    sheet.alpha_composite(big, (0, 0)); sheet.alpha_composite(ic.resize((128, 128), Image.NEAREST), (big.width + 6, 6))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview", "icon_knifeArm.png")
    os.makedirs(os.path.dirname(out), exist_ok=True); sheet.save(out); print("icon Item_KnifeArm.png ->", out)

if "tex" in what: make_texture()
if "icon" in what: make_icon()
