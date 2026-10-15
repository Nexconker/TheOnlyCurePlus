"""Iconos de los rasgos de amputado (18x18) al estilo de los vanilla: pixel art con contorno oscuro de 1 px, luz desde
arriba a la izquierda (claro / base / sombra) y colores de verdad, en lugar de las siluetas rojas planas del TOC original
y las barras de color de las piernas (2026-10-14: "que se vean como los demás").

Misma convención que los originales: figura de frente; el rasgo del lado izquierdo quita el miembro que queda a la
DERECHA de quien mira. Brazos: busto con camiseta. Piernas: cadera con pantalón corto. El muñón lleva venda y gotea.
Uso: python make_trait_icons.py [carpeta de salida]  (por defecto la del mod) -> media/ui/Traits/trait_Amputee_*.png"""
import os, sys
import numpy as np
from PIL import Image

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\ui\Traits"

# material: (claro, base, sombra)
PAL = {
    "S": ((247, 208, 170), (224, 170, 128), (176, 120, 86)),     # piel
    "H": ((120, 84, 56), (92, 62, 40), (64, 42, 28)),             # pelo
    "T": ((112, 144, 182), (76, 104, 142), (50, 70, 102)),        # camiseta
    "P": ((168, 146, 104), (134, 114, 78), (98, 82, 54)),         # pantalón corto
    "L": ((96, 72, 52), (70, 52, 38), (50, 36, 26)),              # cinturón
    "K": ((90, 80, 76), (62, 54, 52), (40, 34, 34)),              # zapatos
    "W": ((252, 250, 242), (228, 222, 206), (182, 172, 154)),     # venda
    "R": ((226, 52, 46), (176, 22, 20), (116, 10, 10)),           # sangre en la venda
}
OUTLINE = (38, 26, 22)
DROP = ((200, 30, 26), (128, 10, 10))

# Plantillas 18x18. Mayúsculas = material; las minúsculas marcan el segmento del brazo / pierna que se puede quitar
# (a/A brazo, b/B antebrazo, c/C mano; t/T muslo... ver SEG). Izquierda de la plantilla = derecha del personaje.
BUST = [
    "..................",
    ".......HHHH.......",
    "......HHHHHH......",
    "......HSSSSH......",
    "......SSSSSS......",
    ".......SSSS.......",
    "........SS........",
    "....TTTTTTTTTT....",
    "..xxxxTTTTTTyyyy..",
    "..xxxxTTTTTTyyyy..",
    "..aaa.TTTTTT.AAA..",
    "..aaa.TTTTTT.AAA..",
    "..bbb.TTTTTT.BBB..",
    "..bbb.TTTTTT.BBB..",
    "..bbb.TTTTTT.BBB..",
    "..ccc.TTTTTT.CCC..",
    "..ccc.TTTTTT.CCC..",
    "......TTTTTT......",
]
HIPS = [
    "..................",
    "....LLLLLLLLLL....",
    "....PPPPPPPPPP....",
    "....PPPPPPPPPP....",
    "....PPPPPPPPPP....",
    "....PPPP..PPPP....",
    "....PPPP..PPPP....",
    "....uuuu..UUUU....",
    "....uuuu..UUUU....",
    ".....uuu..UUU.....",
    ".....kkk..KKK.....",
    ".....nnn..NNN.....",
    ".....nnn..NNN.....",
    ".....nnn..NNN.....",
    ".....nnn..NNN.....",
    "....ffff..FFFF....",
    "....ffff..FFFF....",
    "..................",
]
# letra -> (material, segmento, lado). Minúscula = lado derecho del personaje (izquierda de la imagen).
SEG = {
    "x": ("T", "sleeve", "R"), "y": ("T", "sleeve", "L"),
    "a": ("S", "upper", "R"), "A": ("S", "upper", "L"),
    "b": ("S", "fore", "R"), "B": ("S", "fore", "L"),
    "c": ("S", "hand", "R"), "C": ("S", "hand", "L"),
    "u": ("S", "thigh", "R"), "U": ("S", "thigh", "L"),
    "k": ("S", "knee", "R"), "K": ("S", "knee", "L"),
    "n": ("S", "shin", "R"), "N": ("S", "shin", "L"),
    "f": ("K", "foot", "R"), "F": ("K", "foot", "L"),
}

def parse(tpl):
    mat = np.full((18, 18), "", dtype=object); seg = np.full((18, 18), "", dtype=object); side = np.full((18, 18), "", dtype=object)
    for y, row in enumerate(tpl):
        for x, ch in enumerate(row):
            if ch == ".": continue
            if ch in SEG: mat[y, x], seg[y, x], side[y, x] = SEG[ch]
            else: mat[y, x] = ch
    return mat, seg, side

# qué se quita y dónde va la venda en cada nivel: (segmentos fuera, filas de venda desde el final del muñón, gotas)
LEVELS = {
    "Hand":     (BUST, {"hand"}, 3),
    "ForeArm":  (BUST, {"hand", "fore"}, 3),
    "UpperArm": (BUST, {"hand", "fore", "upper"}, 2),
    "Foot":     (HIPS, {"foot"}, 3),
    "LowerLeg": (HIPS, {"foot", "shin"}, 3),
}

def icon(level, side):
    tpl, remove, band = LEVELS[level]
    mat, seg, sd = parse(tpl)
    gone = np.vectorize(lambda s, d: s in remove and d == side)(seg, sd)
    mat[gone] = ""
    # muñón: la(s) última(s) fila(s) que quedan de ese brazo / pierna se vendan, con sangre en el centro del borde
    limb = np.vectorize(lambda m, d: m != "" and d == side)(mat, sd)
    rows = sorted({y for y, x in zip(*np.nonzero(limb))})
    stump_rows = rows[-band:]
    tip = []
    for y in stump_rows:
        for x in range(18):
            if limb[y, x]: mat[y, x] = "W"; tip.append((y, x))
    last = stump_rows[-1]
    xs = [x for y, x in tip if y == last]
    for x in xs[1:-1] if len(xs) > 3 else xs: mat[last, x] = "R"     # la punta empapada; en piezas anchas, con borde blanco
    filled = mat != ""
    img = np.zeros((18, 18, 4), np.uint8)
    for y in range(18):
        for x in range(18):
            m = mat[y, x]
            if not m: continue
            hi, base, sh = PAL[m]
            up = y > 0 and mat[y - 1, x] == m; left = x > 0 and mat[y, x - 1] == m
            down = y < 17 and mat[y + 1, x] == m; right = x < 17 and mat[y, x + 1] == m
            c = base
            if not left or not up: c = hi
            if not right or (not down and m in "SKH"): c = sh        # la venda y la ropa no se oscurecen por abajo
            if not left and not right: c = hi if x % 2 == 0 else base     # piezas de 1 px de ancho
            img[y, x] = (*c, 255)
    # contorno de 1 px (vecinos en cruz), sin cerrar el borde inferior del busto (cortado por el marco)
    for y in range(18):
        for x in range(18):
            if filled[y, x]: continue
            if any(0 <= y + dy < 18 and 0 <= x + dx < 18 and filled[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img[y, x] = (*OUTLINE, 255)
    # gotas bajo el muñón (sin contorno, como las salpicaduras vanilla)
    cx = xs[len(xs) // 2]
    for i, (dy, dx) in enumerate(((2, 0), (3, 0), (5, -1 if side == "R" else 1))):
        yy, xx = last + dy, cx + dx
        if 0 <= yy < 18 and 0 <= xx < 18 and not filled[yy, xx] and img[yy, xx, 3] == 0:
            img[yy, xx] = (*DROP[0 if i != 1 else 1], 255)
        elif 0 <= yy < 18 and 0 <= xx < 18 and not filled[yy, xx]:
            img[yy, xx] = (*DROP[1], 255)
    return Image.fromarray(img, "RGBA")

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for level in LEVELS:
        for side, suffix in (("L", ""), ("R", "_R")):
            p = os.path.join(OUT_DIR, "trait_Amputee_%s%s.png" % (level, suffix))
            icon(level, side).save(p); print(os.path.basename(p))
