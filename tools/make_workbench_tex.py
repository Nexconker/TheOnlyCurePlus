"""Atlas de la mesa del banco de prótesis (2026-10-17): textures/Furniture/TOCWorkbench.png, 256x256 en celdas de 64 px
(4x4). make_workbench_model.py mapea cada pieza a una celda. Uso: TOC_MEDIA=...Dev python make_workbench_tex.py"""
import os
import numpy as np
from PIL import Image, ImageDraw
from make_cyber_assets import fbm

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
C = 64
CELLS = ["wood", "wooddark", "pegboard", "steel", "iron", "red", "yellow", "rubber",
         "bulb", "brass", "blueprint", "cyberwhite", "cybergrey", "cable", "mat", "leather"]

def noise_cell(base, var, seed, grain=None):
    n = fbm(C, C, seed, base=4)
    a = np.array(base, float)[None, None, :] * (1 - var / 2 + var * n[..., None])
    if grain == "h":
        y = np.arange(C)[:, None]; w = (fbm(C, C, seed + 1, base=2) - 0.5) * 6
        a *= (0.9 + 0.1 * np.sin((y + w) * 2 * np.pi / 7))[..., None]
    if grain == "v":
        x = np.arange(C)[None, :]; w = (fbm(C, C, seed + 2, base=2) - 0.5) * 6
        a *= (0.92 + 0.08 * np.sin((x + w) * 2 * np.pi / 5))[..., None]
    return a

def main():
    img = np.zeros((C * 4, C * 4, 3), float)
    def put(i, a):
        r, c = divmod(i, 4); img[r * C:(r + 1) * C, c * C:(c + 1) * C] = a
    put(0, noise_cell((150, 108, 66), 0.18, 1, "h"))           # tablero de madera
    put(1, noise_cell((92, 62, 40), 0.18, 3, "v"))             # patas y cajones
    peg = noise_cell((122, 96, 66), 0.12, 5)                    # tablero perforado
    for y in range(4, C, 8):
        for x in range(4, C, 8): peg[y - 1:y + 2, x - 1:x + 2] *= 0.35
    put(2, peg)
    put(3, noise_cell((168, 170, 176), 0.10, 7, "h"))          # acero
    put(4, noise_cell((58, 60, 64), 0.12, 9))                  # hierro oscuro
    put(5, noise_cell((168, 40, 34), 0.10, 11))                # rojo (tornillo de banco, mangos)
    put(6, noise_cell((214, 176, 52), 0.08, 13))               # amarillo (flexo)
    put(7, noise_cell((32, 32, 34), 0.08, 15))                 # goma
    put(8, noise_cell((255, 244, 200), 0.04, 17))              # bombilla
    put(9, noise_cell((190, 146, 62), 0.10, 19))               # latón
    bp = noise_cell((46, 86, 150), 0.08, 21)                    # plano (azul con líneas)
    put(10, bp)
    put(11, noise_cell((214, 212, 204), 0.06, 23))             # placa cyber blanca
    put(12, noise_cell((64, 66, 72), 0.08, 25))                # placa cyber grafito
    put(13, noise_cell((92, 98, 58), 0.12, 27, "v"))           # cables oliva
    put(14, noise_cell((52, 92, 62), 0.10, 29))                # alfombrilla de trabajo verde
    put(15, noise_cell((96, 64, 40), 0.14, 31))                # cuero
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(out)
    r, c = divmod(10, 4); ox, oy = c * C, r * C                  # dibujo de un brazo en el plano
    d.line([(ox + 10, oy + 40), (ox + 40, oy + 26), (ox + 54, oy + 20)], fill=(220, 230, 245, 255), width=1)
    d.rectangle([ox + 12, oy + 30, ox + 34, oy + 46], outline=(220, 230, 245, 255))
    for k in range(5): d.line([(ox + 6, oy + 6 + k * 4), (ox + 30, oy + 6 + k * 4)], fill=(180, 200, 230, 255))
    r, c = divmod(14, 4); ox, oy = c * C, r * C                  # cuadrícula de la alfombrilla
    for k in range(0, C, 8):
        d.line([(ox + k, oy), (ox + k, oy + C - 1)], fill=(70, 116, 82, 255)); d.line([(ox, oy + k), (ox + C - 1, oy + k)], fill=(70, 116, 82, 255))
    path = os.path.join(MOD, "textures", "Furniture", "TOCWorkbench.png")
    os.makedirs(os.path.dirname(path), exist_ok=True); out.save(path); print("tex", path)

if __name__ == "__main__":
    main()
