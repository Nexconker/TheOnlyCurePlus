"""Patrones para las prótesis (2026-10-18, prueba pedida: "patrones a las prótesis como forma de personalización").
Van como calcomanías del juego (ClothingDecal): una imagen con transparencia del tamaño de todo el atlas que el juego
pinta ENCIMA de la textura elegida (ModelInstanceTextureCreator.addClothingItem -> ItemSmartTexture.addRect), así que se
combinan con los 11 colores de pintura (textureChoices) sin multiplicar archivos. Sólo tocan las bandas pintables
(PAINTABLE de make_paint_variants.py): juntas, cables, cuero y palma quedan limpios.
Los tonales (camo, tigre, carbono, rayas) son negro / blanco semitransparente: oscurecen o aclaran el color de debajo.
UV de las piezas (blender_build.py): u = vuelta alrededor del eje de la pieza (el patrón tiene que repetirse en x),
v = a lo largo de la pieza dentro de su banda.
Uso: TOC_MEDIA=...Dev\\42\\media python make_pattern_decals.py -> textures/Prosthesis/Pattern/<atlas>_<patrón>.png"""
import os
import numpy as np
from PIL import Image
from make_paint_variants import PAINTABLE

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
# alto real de la banda frente a su ancho: px de v por px de u a igual distancia sobre la pieza (aprox., a ojo de los
# modelos: la vuelta de un antebrazo ~30 cm frente a ~25 cm de largo). Corrige que el patrón salga estirado.
ASPECT = {"normalArm": 0.8, "mechLeg": 1.6, "cyberArm": 1.5, "medicalArm": 1.0, "pegArm": 1.2, "knifeArm": 0.6,
          "hookArm": 0.6, "pegLeg": 2.0, "medicalLeg": 0.5}

def noise(h, w, scale, seed):
    """Ruido suave periódico (se repite en x e y), escala en px de u."""
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.normal(size=(h, w)))
    ky = np.fft.fftfreq(h)[:, None]; kx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-((kx * scale) ** 2 + (ky * scale) ** 2) * 4.0)
    n = np.real(np.fft.ifft2(f * g)); n -= n.mean(); return n / (n.std() + 1e-9)

def pat_camo(h, w, asp, seed):
    a = noise(h, w, w / 3.5, seed); b = noise(h, w, w / 5.0, seed + 7)
    rgba = np.zeros((h, w, 4))
    dark = a > 0.35; light = (b > 0.55) & ~dark
    rgba[dark] = (12, 14, 10, 150); rgba[light] = (235, 230, 200, 70)
    return rgba

def pat_tiger(h, w, asp, seed):
    y = np.arange(h)[:, None] / asp; x = np.arange(w)[None, :]
    warp = noise(h, w, w / 2.5, seed) * 3.0
    s = np.sin(2 * np.pi * (y / 11.0 + warp * 0.12 + 0.15 * np.sin(2 * np.pi * x / w * 2)))
    width = 0.55 + 0.35 * noise(h, w, w / 3, seed + 3)
    rgba = np.zeros((h, w, 4)); m = s > width; rgba[m] = (10, 8, 6, 175)
    return rgba

def pat_hazard(h, w, asp, seed):
    y = np.arange(h)[:, None] / asp; x = np.arange(w)[None, :]
    n = 6                                                  # rayas por vuelta: número entero para que cierre en u
    s = ((x / w + y / w) * n) % 1.0
    rgba = np.zeros((h, w, 4)); rgba[s < 0.5] = (14, 14, 14, 215)
    return rgba

def pat_carbon(h, w, asp, seed):
    y = (np.arange(h)[:, None] / asp).astype(int); x = np.arange(w)[None, :]
    c = 4                                                  # sarga 2x2: celdas de 4 px
    t = ((x // c) + (y // c)) % 2
    shade = np.where(t == 0, (x % c) / c, (y % c) / c)     # cada hilo con su brillo en dirección contraria
    rgba = np.zeros((h, w, 4))
    rgba[..., :3] = 8; rgba[..., 3] = 70 + 130 * (1 - shade)       # más contraste: sobre gris casi no se veía
    return rgba

def pat_flames(h, w, asp, seed):
    y = np.arange(h)[:, None] / max(1, h - 1); x = np.arange(w)[None, :]
    n = noise(h, w, w / 6, seed)
    tongues = 0.5 + 0.25 * np.sin(2 * np.pi * x / w * 5) + 0.12 * n
    f = (1 - y) - (1 - tongues)                            # llamas desde el extremo v0 de cada pieza
    rgba = np.zeros((h, w, 4))
    core = f > 0.12; edge = (f > 0) & ~core
    rgba[core] = (250, 196, 40, 235); rgba[edge] = (220, 70, 20, 225)
    rgba[f > 0.32] = (255, 236, 140, 235)
    return rgba

# ---- segunda tanda (2026-10-18, "genera más patrones")
def grid(h, w, asp):
    return np.arange(h)[:, None] / asp + np.zeros((1, w)), np.arange(w)[None, :] + np.zeros((h, 1))

def pat_digital(h, w, asp, seed):
    """Camuflaje pixelado: bloques de 4 px con tres tonos."""
    b = 4
    a = noise(h, w, w / 4.0, seed); c = noise(h, w, w / 6.0, seed + 5)
    y, x = grid(h, w, asp); by = (y // b).astype(int); bx = (x // b).astype(int)
    rng = np.random.default_rng(seed); jit = rng.normal(0, 0.35, (by.max() + 2, w // b + 2))
    A = a[np.clip((by * b * asp).astype(int), 0, h - 1), np.clip(bx * b, 0, w - 1)] + jit[by, bx]
    C = c[np.clip((by * b * asp).astype(int), 0, h - 1), np.clip(bx * b, 0, w - 1)] + jit[by, bx]
    rgba = np.zeros((h, w, 4))
    rgba[A > 0.5] = (14, 16, 12, 165); rgba[(A < -0.4) & (C > 0)] = (230, 228, 210, 80); rgba[(A <= 0.5) & (A > 0.05) & (C < -0.3)] = (14, 16, 12, 85)
    return rgba

def pat_urban(h, w, asp, seed):
    """Camuflaje urbano: manchas negras y blancas más pequeñas."""
    a = noise(h, w, w / 6.0, seed); b = noise(h, w, w / 7.0, seed + 11)
    rgba = np.zeros((h, w, 4))
    rgba[a > 0.45] = (10, 10, 12, 175); rgba[(b > 0.5) & (a <= 0.45)] = (245, 245, 245, 150); rgba[(a < -0.6) & (b <= 0.5)] = (10, 10, 12, 70)
    return rgba

def pat_splinter(h, w, asp, seed):
    """Fragmentos angulosos (Voronoi que se repite en u), cada uno oscuro, claro o sin tocar."""
    rng = np.random.default_rng(seed); n = 16
    py = rng.uniform(0, h / asp, n); px = rng.uniform(0, w, n); tone = rng.integers(0, 3, n)
    y, x = grid(h, w, asp)
    dx = np.abs(x[..., None] - px); dx = np.minimum(dx, w - dx)
    d = np.maximum(dx, np.abs(y[..., None] - py) * 1.6) + np.abs(y[..., None] - py) * 0.4    # distancia rara = bordes rectos
    k = np.argmin(d, axis=-1); t = tone[k]
    rgba = np.zeros((h, w, 4)); rgba[t == 1] = (16, 18, 14, 150); rgba[t == 2] = (240, 236, 220, 75)
    return rgba

def pat_racing(h, w, asp, seed):
    """Dos franjas de carreras a lo largo de la pieza (repetidas a media vuelta: se ven por los dos lados)."""
    y, x = grid(h, w, asp); u = (x / w * 2) % 1.0
    rgba = np.zeros((h, w, 4)); m = ((u > 0.36) & (u < 0.46)) | ((u > 0.54) & (u < 0.64))
    rgba[m] = (245, 245, 240, 230)
    return rgba

def pat_checker(h, w, asp, seed):
    """Cuadros de bandera de carreras: 8 por vuelta."""
    y, x = grid(h, w, asp); c = w / 8
    rgba = np.zeros((h, w, 4)); rgba[((x // c) + (y // c)) % 2 == 0] = (12, 12, 12, 225)
    return rgba

def pat_dots(h, w, asp, seed):
    """Lunares en filas alternas."""
    y, x = grid(h, w, asp); c = w / 6
    row = (y // c).astype(int); xs = (x + (row % 2) * c / 2) % c - c / 2; ys = y % c - c / 2
    rgba = np.zeros((h, w, 4)); rgba[xs ** 2 + ys ** 2 < (c * 0.28) ** 2] = (245, 245, 240, 220)
    return rgba

def pat_chevron(h, w, asp, seed):
    """Zigzag (chevrones) alrededor de la pieza."""
    y, x = grid(h, w, asp); n = 5; per = w / n
    s = ((y + np.abs((x / per) % 1.0 - 0.5) * per) / (per * 0.5)) % 1.0
    rgba = np.zeros((h, w, 4)); rgba[s < 0.45] = (12, 12, 12, 205)
    return rgba

def pat_lightning(h, w, asp, seed):
    """Rayos a lo largo de la pieza, con halo."""
    rng = np.random.default_rng(seed)
    y, x = grid(h, w, asp); d = np.full((h, w), 99.0)
    for k in range(4):
        xs = w * (k + rng.uniform(0.2, 0.8)) / 4; pts = []
        for yy in np.linspace(0, h / asp, 9):
            pts.append((yy, xs)); xs += rng.uniform(-w / 10, w / 10)
        for (y0, x0), (y1, x1) in zip(pts, pts[1:]):
            t = np.clip(((y - y0) * (y1 - y0) + (x - x0) * (x1 - x0)) / max(1e-6, (y1 - y0) ** 2 + (x1 - x0) ** 2), 0, 1)
            dx = np.abs(x - (x0 + t * (x1 - x0))); dx = np.minimum(dx, w - dx)
            d = np.minimum(d, np.hypot(y - (y0 + t * (y1 - y0)), dx))
    rgba = np.zeros((h, w, 4))
    glow = d < 3.2; core = d < 1.1
    rgba[glow] = (60, 170, 255, 120); rgba[core] = (225, 245, 255, 245)
    return rgba

def pat_rust(h, w, asp, seed):
    """Óxido y desgaste: manchas pardas con picaduras."""
    a = noise(h, w, w / 5.0, seed); fine = noise(h, w, 2.0, seed + 2)
    rgba = np.zeros((h, w, 4))
    m = a + 0.35 * fine
    rgba[m > 0.2] = (126, 62, 24, 120); rgba[m > 0.75] = (92, 40, 14, 190); rgba[(fine > 1.7)] = (40, 20, 10, 200)
    return rgba

def pat_circuit(h, w, asp, seed):
    """Pistas de circuito impreso que brillan (va bien con la gama cyber)."""
    rng = np.random.default_rng(seed); c = 6
    y, x = grid(h, w, asp); gy = (y // c).astype(int); gx = (x // c).astype(int); ly = y % c; lx = x % c
    H_, W_ = gy.max() + 2, w // c + 1
    hor = rng.random((H_, W_)) < 0.45; ver = rng.random((H_, W_)) < 0.35; pad = rng.random((H_, W_)) < 0.12
    m = (hor[gy, gx] & (np.abs(ly - c / 2) < 0.8)) | (ver[gy, gx] & (np.abs(lx - c / 2) < 0.8))
    p = pad[gy, gx] & (np.abs(ly - c / 2) < 1.8) & (np.abs(lx - c / 2) < 1.8)
    rgba = np.zeros((h, w, 4)); rgba[m] = (70, 230, 200, 200); rgba[p] = (200, 255, 240, 235)
    return rgba

def pat_scales(h, w, asp, seed):
    """Escamas (de dragón): arcos solapados con borde oscuro."""
    y, x = grid(h, w, asp); c = w / 10
    row = (y // (c * 0.6)).astype(int); xs = (x + (row % 2) * c / 2) % c - c / 2; ys = (y % (c * 0.6))
    r = np.hypot(xs, ys)
    rgba = np.zeros((h, w, 4)); rgba[(r > c * 0.42) & (r < c * 0.56)] = (12, 12, 12, 170); rgba[r < c * 0.25] = (255, 255, 255, 40)
    return rgba

def pat_hex(h, w, asp, seed):
    """Panal hexagonal (contornos)."""
    y, x = grid(h, w, asp); s = w / 8
    q = x / (s * np.sqrt(3)); r_ = y / (s * 1.5)
    row = np.floor(r_).astype(int); qo = q - (row % 2) * 0.5
    cx = (np.floor(qo) + 0.5 + (row % 2) * 0.5) * s * np.sqrt(3); cy = (row + 0.5) * s * 1.5
    best = np.full((h, w), 1e9); second = np.full((h, w), 1e9)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            rr = row + dy; ccx = (np.floor(qo) + dx + 0.5 + (rr % 2) * 0.5) * s * np.sqrt(3); ccy = (rr + 0.5) * s * 1.5
            ddx = np.abs(x - ccx); ddx = np.minimum(ddx, w - ddx); dd = np.hypot(ddx, y - ccy)
            second = np.where(dd < best, best, np.minimum(second, dd)); best = np.minimum(best, dd)
    rgba = np.zeros((h, w, 4)); rgba[(second - best) < 1.2] = (12, 12, 12, 175)
    return rgba

PATTERNS = {"camo": pat_camo, "tiger": pat_tiger, "hazard": pat_hazard, "carbon": pat_carbon, "flames": pat_flames,
            "digital": pat_digital, "urban": pat_urban, "splinter": pat_splinter, "racing": pat_racing,
            "checker": pat_checker, "dots": pat_dots, "chevron": pat_chevron, "lightning": pat_lightning,
            "rust": pat_rust, "circuit": pat_circuit, "scales": pat_scales, "hex": pat_hex}

def make(atlas, name, src_dir):
    im = Image.open(os.path.join(src_dir, atlas + ".png")); W, H = im.size
    out = np.zeros((H, W, 4), np.uint8)
    for v0, v1 in PAINTABLE[atlas]:
        a, b = int(round(v0 * H)), int(round(v1 * H))
        out[a:b] = np.clip(PATTERNS[name](b - a, W, ASPECT.get(atlas, 1.0), sum(map(ord, atlas + name)) % 1000), 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")

def main(atlases=None, names=None):
    src_dir = os.path.join(MOD, "textures", "Prosthesis"); out_dir = os.path.join(src_dir, "Pattern")
    os.makedirs(out_dir, exist_ok=True)
    for atlas in atlases or PAINTABLE:
        for name in names or PATTERNS:
            make(atlas, name, src_dir).save(os.path.join(out_dir, "%s_%s.png" % (atlas, name)))
        print("patrones", atlas)

if __name__ == "__main__":
    main()
