"""Vestir personajes para las imágenes del Workshop con ropa REAL del juego, como la compone el juego:
- prendas de textura (camisas, camisetas, botas, pantalón corto): capas sobre la textura del cuerpo;
- prendas de malla (pantalón, chaqueta, pelo, barba): .X con pesos posados con el mismo esqueleto;
- bajo la ropa de malla el cuerpo se oculta con las máscaras del juego (texel a texel).
Lo usan export_merle_scene / export_ash_scene (su propio código, más antiguo) y export_card_people.py."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import pose_x as P
import build_assets as BA
from render_icons import find_mesh

G = P.RC.PZ
TEX = os.path.join(G, "textures")
MASKS = os.path.join(TEX, "Body", "Masks")
CLOTHES = os.path.join(TEX, "Clothes")

def tinted(img_or_path, rgb):
    im = Image.open(img_or_path) if isinstance(img_or_path, str) else img_or_path
    a = np.array(im.convert("RGBA")).astype(float)
    a[..., :3] *= np.array(rgb, float) / 255.0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def grimy(img_or_path, amount=0.3, blood=0, seed=7):
    """Mugre en manchas y, si blood > 0, salpicaduras de sangre seca (sólo donde la prenda tiene alfa)."""
    im = Image.open(img_or_path) if isinstance(img_or_path, str) else img_or_path
    a = np.array(im.convert("RGBA")).astype(float); h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    g = np.asarray(Image.fromarray((rng.random((max(2, h // 16), max(2, w // 16))) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255
    a[..., :3] *= (1 - amount + amount * g)[..., None]
    if blood:
        layer = Image.new("L", (w, h), 0); d = ImageDraw.Draw(layer)
        for _ in range(blood):
            x, y, r = rng.integers(0, w), rng.integers(0, h), rng.integers(1, 5)
            d.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.integers(120, 230)))
        bm = np.asarray(layer.filter(ImageFilter.GaussianBlur(0.8)), float)[..., None] / 255 * (a[..., 3:4] > 0)
        a[..., :3] = a[..., :3] * (1 - bm) + np.array([92, 18, 14], float) * bm
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def clothes_tex(*rel):
    return os.path.join(CLOTHES, *rel)

def body_texture(base, overlays=(), hide=()):
    """base: nombre en textures/Body (MaleBody02, M_ZedBody01...) o imagen; overlays: capas (rutas o imágenes) en el UV
    del cuerpo; hide: máscaras de textures/Body/Masks (LeftLeg, Chest...) que se ocultan (alfa 0)."""
    tex = (Image.open(os.path.join(TEX, "Body", base + ".png")) if isinstance(base, str) else base).convert("RGBA")
    if tex.getextrema()[3][0] < 255:                                   # bases con huecos de alfa: fondo de piel
        bg = Image.new("RGBA", tex.size, (150, 128, 108, 255)); bg.alpha_composite(tex); tex = bg
    for o in overlays:
        layer = (Image.open(o) if isinstance(o, str) else o).convert("RGBA").resize(tex.size)
        tex = Image.alpha_composite(tex, layer)
    a = np.array(tex)
    hidden = np.zeros(a.shape[:2], bool)
    for n in hide:
        hidden |= np.array(Image.open(os.path.join(MASKS, n + ".png")).convert("RGBA").resize(tex.size).split()[3]) > 0
    a[..., 3] = np.where(hidden, 0, 255)
    return Image.fromarray(a)

def body(W, tex, sex="Male"):
    b = BA.load_body(sex)
    keep = np.array([f for f in b["faces"] if not BA.face_is_hidden(b, f)], int)
    weights = [sorted(w.items(), key=lambda t: -t[1])[:4] for w in b["weights"]]
    return {"v": P.skin(np.array(b["verts"], float), weights, b["offsets"], W), "f": keep, "uv": b["uvs"], "tex": tex, "alpha": True}

def mesh(rel, tex, W, drop_bones=None, drop_w=0.5, which=0):
    """Prenda de malla del juego (models_X/Skinned/<rel>) posada. drop_bones: quita las caras con vértices pesados a
    esos huesos (manga o pernera cortada). which: índice de malla dentro del .X (Bob_Trousers.x trae también los shorts)."""
    root = P.pzx.parse(os.path.join(G, "models_X", "Skinned", rel))
    meshes = []
    def walk(n):
        for c in n.children:
            if c.type == "Mesh": meshes.append(c)
            walk(c)
    walk(root)
    m = P.pzx.read_mesh(meshes[which])
    verts = np.array(m["verts"], float); faces = np.array([list(f) for f in m["faces"]], int); uv = np.array(m["uvs"], float)
    weights = [[] for _ in verts]; offsets = {}
    for sk in m["skin"]:
        offsets[sk["bone"]] = list(sk["offset"])
        for vi, w in zip(sk["indices"], sk["weights"]): weights[vi].append((sk["bone"], w))
    if drop_bones:
        cut = np.array([sum(w for bn, w in ws if bn.startswith(tuple(drop_bones))) > drop_w for ws in weights])
        faces = np.array([f for f in faces if not cut[f].any()], int)
    return {"v": P.skin(verts, weights, offsets, W), "f": faces, "uv": uv, "tex": tex}

HAIR_WHITE = os.path.join(TEX, "F_Hair_White.png")
def hair(style, W, rgb=(60, 44, 30)):
    return mesh(os.path.join("Hair", "Bob_Hair_%s.X" % style), tinted(HAIR_WHITE, rgb), W)

def female_hair(style, W, rgb=(60, 44, 30)):
    return mesh(os.path.join("Hair", "F_Hair_%s.X" % style), tinted(HAIR_WHITE, rgb), W)

def beard(style, W, rgb=(60, 44, 30)):
    return mesh(os.path.join("Beards", "Bob_Beard_%s.X" % style), tinted(HAIR_WHITE, rgb), W)

def stump_tex(folder, body="MaleBody02", cicatrized=True):
    """Textura de muñón con el tono del cuerpo, como la elige el juego (ItemsController.GetAmputationTexturesIndex):
    MaleBody0N -> skin0N; _c cicatrizada (ya lleva prótesis), _b sangrante. 2026-10-17: los renders mezclaban piel 02 y 01."""
    import re
    m = re.search(r"(\d\d)", body)
    n = int(m.group(1)) if m else 1
    hairy = "_hairy" if body.endswith("a") else ""
    f = "F" if "Female" in body else ""                     # cuerpo de mujer: skinF0N (sin variante con vello)
    if f: hairy = ""
    return os.path.join(P.RC.MOD, "textures", "Amputations", "Human", folder, "skin%s%02d%s_%s.png" % (f, n, hairy, "c" if cicatrized else "b"))

def inward(m, d=0.0005):
    """Muñones con alfa: medio milímetro hacia dentro (EEVEE pinta negro dos superficies con alfa en el mismo plano)."""
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * d; m["alpha"] = True
    return m
