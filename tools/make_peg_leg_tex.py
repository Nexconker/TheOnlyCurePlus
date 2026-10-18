"""Atlas de la pata de palo 3.3 (2026-10-17, referencia de una pata de museo): textures/Prosthesis/pegLeg.png, 128x512,
con las bandas de BANDS["peg"] en blender_build.py: cuero del borde (v 0..0.25), correa (0.26..0.29), madera vieja con
la veta a lo largo de la pata (0.3..0.9: antes las vetas iban de través y de lejos parecían ladrillos) y goma (0.92..1).
Uso: TOC_MEDIA=...Dev python make_peg_leg_tex.py"""
import os
import numpy as np
from PIL import Image
from make_cyber_assets import fbm, scratches

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
W, H = 128, 512

def rows(v0, v1): return int(round(v0 * H)), int(round(v1 * H))

def wood(w, h, seed):
    """Madera vieja: vetas largas en la dirección de v (a lo largo de la pata), nudos suaves y desgaste más claro."""
    rng = np.random.default_rng(seed)
    x = np.arange(w)[None, :]
    warp = (fbm(w, h, seed, base=2) - 0.5) * 18                          # la veta serpentea
    grain = 0.5 + 0.5 * np.sin((x + warp) * 2 * np.pi / 9.0)
    fine = 0.5 + 0.5 * np.sin((x + warp * 1.3) * 2 * np.pi / 3.1)
    tone = fbm(w, h, seed + 3, base=3)
    v = 0.78 + 0.12 * grain + 0.05 * fine + 0.14 * (tone - 0.5)
    base = np.array((128, 92, 56), float)
    arr = base[None, None, :] * v[..., None]
    worn = np.clip((fbm(w, h, seed + 9, base=5) - 0.62) * 4, 0, 1)[..., None]   # zonas rozadas, más claras
    arr = arr * (1 - 0.25 * worn) + np.array((170, 128, 84), float) * 0.25 * worn
    scratches(arr, rng, 18, 10, (80, 56, 34), 0.25, vertical=True)
    return arr

def leather(w, h, base, seed):
    n = fbm(w, h, seed, base=4)
    return np.array(base, float)[None, None, :] * (0.85 + 0.25 * n[..., None])

img = np.zeros((H, W, 3), float)
a, b = rows(0.0, 0.26); img[a:b] = leather(W, b - a, (84, 54, 34), 11)
a, b = rows(0.26, 0.30); img[a:b] = leather(W, b - a, (46, 31, 21), 13)
a, b = rows(0.30, 0.91); img[a:b] = wood(W, b - a, 15)
a, b = rows(0.91, 1.0); img[a:b] = leather(W, b - a, (38, 36, 34), 17)
out = os.path.join(MOD, "textures", "Prosthesis", "pegLeg.png")
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA").save(out); print("tex", out)
