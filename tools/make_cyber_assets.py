"""Recursos de la gama CYBER (3.3, pedida 2026-10-17 con referencias de brazos de placas blindadas):
- textures/Prosthesis/cyberArm.png: atlas 128x512 con las bandas de BANDS["cyber"] en blender_build.py: fibra de
  carbono (encaje), placa cerámica blanca con líneas de panel, placa grafito, juntas negras, acento dorado y cables oliva
  trenzados (los "músculos" que se ven entre placas).
- iconos Item_BaseCyber.png / Item_HeadCyberHand.png los hace make_modular_icons.py después de blender_to_x.py.
Uso: TOC_MEDIA=...TheOnlyCurePlusDev\\42\\media python make_cyber_assets.py"""
import os
import numpy as np
from PIL import Image

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")
W, H = 128, 512

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

def rows(v0, v1): return int(round(v0 * H)), int(round(v1 * H))

def carbon(w, h, seed):
    """Tejido de fibra de carbono: cuadros en sarga que alternan brillo, con un velo suave."""
    y, x = np.mgrid[0:h, 0:w]
    cell = 2                      # tejido fino y de poco contraste: con cuadros grandes parecía un tablero de ajedrez
    weave = ((x // cell + y // cell) % 2).astype(float)
    v = 34 + 4 * weave + 6 * fbm(w, h, seed, base=4) + 5 * np.sin(y * np.pi / 24)
    return np.stack([v, v, v * 1.06], -1)

def plate(w, h, base, seed, wear=0.25):
    """Placa pintada limpia: color plano con un leve degradado y algún rayón (las juntas las pone la geometría)."""
    rng = np.random.default_rng(seed)
    n = fbm(w, h, seed, base=3)
    arr = np.array(base, float)[None, None, :] * (0.94 + 0.08 * n[..., None])
    arr *= (0.97 + 0.06 * np.linspace(0, 1, h))[:, None, None]
    scratches(arr, rng, int(8 * wear * 4), 8, (150, 150, 152), 0.18)
    return arr

def cables(w, h, seed):
    """Haz de cables oliva trenzados con vetas oscuras (los músculos de las referencias)."""
    y, x = np.mgrid[0:h, 0:w]
    strand = 0.5 + 0.5 * np.sin((x + y * 0.6) * 2 * np.pi / 3)
    v = 0.78 + 0.22 * strand + 0.06 * fbm(w, h, seed, base=6)
    return np.array((92, 98, 58), float)[None, None, :] * v[..., None]

def make_texture():
    img = np.zeros((H, W, 3), float)
    a, b = rows(0.0, 0.14); img[a:b] = carbon(W, b - a, 71)
    a, b = rows(0.14, 0.46); img[a:b] = plate(W, b - a, (214, 212, 204), 73)            # cerámica blanca
    a, b = rows(0.46, 0.60); img[a:b] = plate(W, b - a, (64, 66, 72), 75, wear=0.15)     # grafito
    a, b = rows(0.60, 0.80); img[a:b] = plate(W, b - a, (26, 26, 29), 77, wear=0.08)   # juntas negras
    a, b = rows(0.80, 0.90)                                                              # acento dorado cepillado
    g = np.array((200, 152, 58), float)[None, None, :] * (0.94 + 0.08 * fbm(W, b - a, 79, base=3)[..., None])
    g *= (0.97 + 0.03 * np.random.default_rng(80).random(W))[None, :, None]               # cepillado fino, sin vetas
    img[a:b] = g
    a, b = rows(0.90, 1.0); img[a:b] = cables(W, b - a, 81)
    out_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    out = os.path.join(MOD, "textures", "Prosthesis", "cyberArm.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    out_img.save(out); print("tex", out, out_img.size)

if __name__ == "__main__":
    make_texture()
