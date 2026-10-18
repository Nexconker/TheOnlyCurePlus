"""Imagen de presentación del brazo motosierra (estilo Ash Williams, Evil Dead 2): camisa vaquera clara sucia y con
sangre, pantalón oscuro, botas, pelo peinado hacia atrás, la mano derecha amputada con el brazo motosierra de nivel
muñeca y la escopeta de dos cañones a la espalda (Bip01_BackPack, como cuelga el juego las armas largas). Ropa real del juego posada con
el mismo esqueleto; el cuerpo bajo la ropa de malla se oculta con las máscaras, como el juego.
Uso: python export_ash_scene.py [candidatas] -> out/scene_ash ; render: blender -b -P blender_render.py -- out/scene_ash out/preview/ash 1600"""
import os, sys, json
CANDIDATES = "candidatas" in sys.argv
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import pose_x as P
import build_assets as BA
from render_icons import find_mesh

MOD = P.RC.MOD
G = P.RC.PZ
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_ash")
os.makedirs(P.OUT, exist_ok=True)
STUMP_TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin02_c.png")      # tono de MaleBody02, cicatrizado
STEX = os.path.join(MOD, "textures", "Prosthesis", "chainsawArm.png")
MASKS = os.path.join(G, "textures", "Body", "Masks")
S = 10.0
def bl(p): return [float(p[0] * S), float(-p[2] * S), float(p[1] * S)]

def tinted(path, rgb):
    a = np.array(Image.open(path).convert("RGBA")).astype(float)
    a[..., :3] *= np.array(rgb, float) / 255.0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def dirty_shirt():
    """Camisa vaquera clara de Ash: mugre en manchas y salpicaduras de sangre seca."""
    im = Image.open(os.path.join(G, "textures", "Clothes", "Shirt_Tshirt_Textures", "Shirt_DenimLight.png")).convert("RGBA")
    a = np.array(im).astype(float); h, w = a.shape[:2]
    rng = np.random.default_rng(7)
    grime = np.asarray(Image.fromarray((rng.random((h // 16, w // 16)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255
    a[..., :3] *= (0.72 + 0.3 * grime)[..., None]
    blood = Image.new("L", (w, h), 0); d = ImageDraw.Draw(blood)
    for _ in range(26):
        x, y, r = rng.integers(0, w), rng.integers(0, h), rng.integers(1, 5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.integers(120, 230)))
    bm = np.asarray(blood.filter(ImageFilter.GaussianBlur(0.8)), float)[..., None] / 255 * (a[..., 3:4] > 0)
    a[..., :3] = a[..., :3] * (1 - bm) + np.array([92, 18, 14], float) * bm
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def body(W):
    b = BA.load_body("Male")
    keep = np.array([f for f in b["faces"] if not BA.face_is_hidden(b, f)], int)
    tex = Image.open(os.path.join(G, "textures", "Body", "MaleBody02.png")).convert("RGBA")
    for layer in (Image.open(os.path.join(G, "textures", "Clothes", "Shoes_Socks_Textres", "BikerBoots.png")).convert("RGBA").resize(tex.size),
                  dirty_shirt().resize(tex.size)):
        tex = Image.alpha_composite(tex, layer)                     # botas y camisa: texturas sobre el cuerpo, como el juego
    a = np.array(tex)
    def mask(n): return np.array(Image.open(os.path.join(MASKS, n + ".png")).convert("RGBA").resize(tex.size).split()[3]) > 0
    hidden = mask("LeftLeg") | mask("RightLeg") | mask("Crotch") | mask("RightHand")      # bajo el pantalón de malla; mano amputada
    a[..., 3] = np.where(hidden, 0, 255)
    weights = [sorted(w.items(), key=lambda t: -t[1])[:4] for w in b["weights"]]
    return {"v": P.skin(np.array(b["verts"], float), weights, b["offsets"], W), "f": keep, "uv": b["uvs"], "tex": Image.fromarray(a), "alpha": True}

def clothing(rel, tex, W):
    m = P.pzx.read_mesh(find_mesh(P.pzx.parse(os.path.join(G, "models_X", "Skinned", rel))))
    verts = np.array(m["verts"], float); faces = np.array([list(f) for f in m["faces"]], int); uv = np.array(m["uvs"], float)
    weights = [[] for _ in verts]; offsets = {}
    for sk in m["skin"]:
        offsets[sk["bone"]] = list(sk["offset"])
        for vi, w in zip(sk["indices"], sk["weights"]): weights[vi].append((sk["bone"], w))
    return {"v": P.skin(verts, weights, offsets, W), "f": faces, "uv": uv, "tex": tex}

def static_in(rel, tex, W, prop):
    root = P.pzx.parse(os.path.join(G, "models_X", rel)); vs, fs, uvs = [], [], []
    def walk(node, parent):
        for fr in node.all("Frame"):
            ftm = fr.child("FrameTransformMatrix")
            m = (np.array(ftm.data[:16], float).reshape(4, 4) if ftm else np.eye(4)) @ parent
            for me in fr.all("Mesh"):
                d = P.pzx.read_mesh(me); base = sum(len(v) for v in vs)
                v = np.hstack([np.array(d["verts"], float), np.ones((len(d["verts"]), 1))]) @ m
                vs.append(v[:, :3]); uvs.append(np.array(d["uvs"], float)); fs.append(np.array([list(f) for f in d["faces"]], int) + base)
            walk(fr, m)
    walk(root, np.eye(4))
    V = np.vstack(vs); V = (np.hstack([V, np.ones((len(V), 1))]) @ W[prop])[:, :3]
    return {"v": V, "f": np.vstack(fs), "uv": np.vstack(uvs), "tex": tex}

def stump(W):
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStumpProst_Right_Hand_Male.X"), STUMP_TEX, W); m["alpha"] = True
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * 0.0005
    return m

HAIR = tinted(os.path.join(G, "textures", "F_Hair_White.png"), (58, 40, 28))
PANTS = tinted(os.path.join(G, "textures", "Clothes", "Trousers_Mesh", "TrousersMesh_Black.png"), (150, 120, 96))
GUN_TEX = os.path.join(G, "textures", "weapons", "firearm", "DoubleBarrelShotgun.png")

# La escopeta grande (de dos cañones, JS_2000) a la espalda, como cuelga el juego las armas largas: del hueso
# Bip01_BackPack. Se coloca en la pose de bind (culata arriba sobre el hombro izquierdo, al alcance de la mano libre,
# cañones hacia la cadera derecha, el costado pegado a la espalda) y sigue al hueso en cualquier pose.
GUN_BIG = os.path.join("weapons", "firearm", "JS_2000.x")
_b = BA.load_body("Male")
BP_BIND = np.linalg.inv(np.array(_b["offsets"]["Bip01_BackPack"], float).reshape(4, 4))
_V = np.array(_b["verts"], float)

def gun_back_bind():
    """Matriz (filas) modelo de la escopeta -> espacio del cuerpo en bind."""
    bp = BP_BIND[3, :3]
    near = _V[(np.abs(_V[:, 0]) < 0.08) & (np.abs(_V[:, 1] - bp[1]) < 0.06)]
    z_back = near[:, 2].max()                                   # superficie de la espalda (frente = -Z)
    up, left, back = np.array([0, 1.0, 0]), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])
    ang = np.radians(32)
    d = -up * np.cos(ang) - left * np.sin(ang)                  # cañones hacia abajo y a la derecha
    gx = back                                                   # costado del arma contra la espalda
    gz = np.cross(gx, d); gz /= np.linalg.norm(gz)
    center = np.array([0.0, bp[1] - 0.01, z_back + 0.022])
    origin = center - d * 0.14                                  # el origen (empuñadura) queda arriba a la izquierda
    M = np.eye(4); M[0, :3] = gx; M[1, :3] = d; M[2, :3] = gz; M[3, :3] = origin
    return M

GUN_M = gun_back_bind()

def gun_back(W):
    g = static_in(GUN_BIG, GUN_TEX, {"I": np.eye(4)}, "I")
    V = np.hstack([g["v"], np.ones((len(g["v"]), 1))]) @ GUN_M @ np.linalg.inv(BP_BIND) @ W["Bip01_BackPack"]
    g["v"] = V[:, :3]
    return g

def outfit(W):
    return [body(W), stump(W),
            clothing(os.path.join("Clothes", "Bob_Trousers.x"), PANTS, W),
            clothing(os.path.join("Hair", "Bob_Hair_GreasedBack.X"), HAIR, W),
            # 3.3: base de chatarra de muñeca + cabezal de motosierra (el brazo motosierra de la 3.2 se convierte en esto)
            P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "baseScrapWrist_R_M.X"), os.path.join(MOD, "textures", "Prosthesis", "knifeArm.png"), W),
            P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "headChainsaw_R_M.X"), STEX, W),
            gun_back(W)]

def worlds(clip, frac):
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", clip))
    T = max(k[-1][0] for kk in c["keys"].values() for k in kk.values())
    return P.worlds_at(c, frac * T, False)

if CANDIDATES:
    POSES = {"atk00": ("Bob_Attack1Hand01_Hit.X", 0.0), "atk35": ("Bob_Attack1Hand01_Hit.X", 0.35), "ext01_25": ("Bob_Idle1HandExt01.X", 0.25),
             "ext01_75": ("Bob_Idle1HandExt01.X", 0.75), "ext02_00": ("Bob_Idle1HandExt02.X", 0.0), "aim": ("Bob_IdleAim1Hand.X", 0.0)}
else:
    POSES = {"hero": ("Bob_Attack1Hand01_Hit.X", 0.35), "idle": ("Bob_Idle1HandExt02.X", 0.0)}
jobs = {}
for name, (clip, frac) in POSES.items():
    W = worlds(clip, frac)
    P.export("ash_" + name, outfit(W))
    upper = bl(W["Bip01_Spine1"][3, :3] * 0.7 + W["Bip01_Head"][3, :3] * 0.15 + W["Bip01_R_Hand"][3, :3] * 0.15)
    arm = bl((W["Bip01_R_Forearm"][3, :3] + W["Bip01_R_Hand"][3, :3]) / 2)
    jobs["ash_%s_full" % name] = ["ash_" + name, 205, upper, 7.6, 6, "nocull"]
    jobs["ash_%s_side" % name] = ["ash_" + name, 245, upper, 7.6, 6, "nocull"]
    jobs["ash_%s_back" % name] = ["ash_" + name, 335, upper, 7.6, 6, "nocull"]       # la escopeta a la espalda
    jobs["ash_%s_close" % name] = ["ash_" + name, 215, [arm[0], arm[1], arm[2] - 1.2], 4.4, 10, "nocull"]
    # para la tarjeta del Workshop (make_workshop.make_chainsaw_card, out/workshop/renders): cuerpo entero y primer plano
    mid = bl(W["Bip01_Pelvis"][3, :3] * 0.8 + W["Bip01_Head"][3, :3] * 0.2)
    card = {"hero": "ash_attack", "idle": "ash_idle"}[name]
    jobs[card] = ["ash_" + name, 205 if name == "hero" else 335, mid, 12.5, 6, "nocull"]   # reposo de espaldas: se ve la escopeta
    if name == "idle": jobs["ash_close"] = ["ash_" + name, 215, [arm[0], arm[1], arm[2] - 1.2], 4.4, 10, "nocull"]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas ->", P.OUT)
