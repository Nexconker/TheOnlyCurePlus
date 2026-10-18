"""Imagen de presentación del brazo bayoneta (3.2.0, estilo Merle) con ropa real del juego posada con el mismo esqueleto:
chaqueta de cuero negra con la manga derecha cortada por encima del codo (se ve el brazal), vaqueros, botas militares
(textura sobre el cuerpo, como el juego), pelo corto y barba. Mano derecha amputada y brazo bayoneta de nivel muñeca.
Como el juego, el cuerpo bajo la ropa de malla se oculta con las máscaras (texel a texel).
Uso: python export_merle_scene.py -> out/scene_merle ; render: blender -b -P blender_render.py -- out/scene_merle out/preview/merle 1600"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import pose_x as P
import build_assets as BA
from render_icons import find_mesh

MOD = P.RC.MOD
G = P.RC.PZ
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_merle")
os.makedirs(P.OUT, exist_ok=True)
STUMP_TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin02_c.png")      # tono de MaleBody02, cicatrizado
KTEX = os.path.join(MOD, "textures", "Prosthesis", "knifeArm.png")
MASKS = os.path.join(G, "textures", "Body", "Masks")
SKIN = "MaleBody02"
S = 10.0
def bl(p): return [float(p[0] * S), float(-p[2] * S), float(p[1] * S)]

def tinted(path, rgb):
    im = Image.open(path).convert("RGBA"); a = np.array(im).astype(float)
    a[..., :3] = a[..., :3] * (np.array(rgb, float) / 255.0)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def body(W):
    b = BA.load_body("Male")
    keep = np.array([f for f in b["faces"] if not BA.face_is_hidden(b, f)], int)
    tex = Image.open(os.path.join(G, "textures", "Body", SKIN + ".png")).convert("RGBA")
    boots = Image.open(os.path.join(G, "textures", "Clothes", "Shoes_Socks_Textres", "ArmyBoots.png")).convert("RGBA").resize(tex.size)
    tex = Image.alpha_composite(tex, boots)                         # las botas son una textura sobre el cuerpo
    a = np.array(tex)
    def mask(n): return np.array(Image.open(os.path.join(MASKS, n + ".png")).convert("RGBA").resize(tex.size).split()[3]) > 0
    # bajo la chaqueta y el pantalón (ropa de malla) el juego oculta el cuerpo; el antebrazo derecho queda a la vista
    hidden = mask("Chest") | mask("Waist") | mask("LeftArm") | mask("LeftLeg") | mask("RightLeg") | mask("Crotch") | mask("RightHand")
    a[..., 3] = np.where(hidden, 0, 255)
    weights = [sorted(w.items(), key=lambda t: -t[1])[:4] for w in b["weights"]]
    verts = P.skin(np.array(b["verts"], float), weights, b["offsets"], W)
    return {"v": verts, "f": keep, "uv": b["uvs"], "tex": Image.fromarray(a), "alpha": True}

def clothing(rel, tex, W, drop_bones=None, drop_w=0.5):
    """Prenda de malla del juego posada. drop_bones: quita las caras con vértices pesados a esos huesos (manga cortada)."""
    m = P.pzx.read_mesh(find_mesh(P.pzx.parse(os.path.join(G, "models_X", "Skinned", rel))))
    verts = np.array(m["verts"], float); faces = np.array([list(f) for f in m["faces"]], int); uv = np.array(m["uvs"], float)
    weights = [[] for _ in verts]; offsets = {}
    for sk in m["skin"]:
        offsets[sk["bone"]] = list(sk["offset"])
        for vi, w in zip(sk["indices"], sk["weights"]): weights[vi].append((sk["bone"], w))
    if drop_bones:
        cut = np.array([sum(w for bn, w in ws if bn.startswith(drop_bones)) > drop_w for ws in weights])
        faces = np.array([f for f in faces if not cut[f].any()], int)
    return {"v": P.skin(verts, weights, offsets, W), "f": faces, "uv": uv, "tex": tex}

def stump(W):
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStumpProst_Right_Hand_Male.X"), STUMP_TEX, W); m["alpha"] = True
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * 0.0005
    return m

HAIR = tinted(os.path.join(G, "textures", "F_Hair_White.png"), (70, 52, 38))
JACKET = os.path.join(G, "textures", "Clothes", "Jacket", "Jacket_Leather_Black.png")
JEANS = os.path.join(G, "textures", "Clothes", "Trousers_Mesh", "TrousersMesh_Denim.png")

def outfit(W):
    return [body(W), stump(W),
            clothing(os.path.join("Clothes", "Bob_JacketLeather.X"), JACKET, W, drop_bones=("Bip01_R_Forearm", "Bip01_R_Hand", "Bip01_R_Finger")),
            clothing(os.path.join("Clothes", "Bob_Trousers.x"), JEANS, W),
            clothing(os.path.join("Hair", "Bob_Hair_CrewCut.X"), HAIR, W),
            clothing(os.path.join("Beards", "Bob_Beard_Chin.X"), HAIR, W),
            # 3.3: base de chatarra de muñeca + cabezal de bayoneta
            P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "baseScrapWrist_R_M.X"), KTEX, W),
            P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "headBayonet_R_M.X"), KTEX, W)]

def frame_of(clip, pick):
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", clip))
    T = max(k[-1][0] for kk in c["keys"].values() for k in kk.values())
    return P.worlds_at(c, pick(c, T) * T, False)

stab_pick = lambda c, T: max(np.linspace(0, 1, 41), key=lambda f: -(P.worlds_at(c, f * T, False)["Bip01_R_Hand"][3, 2] - P.worlds_at(c, f * T, False)["Bip01_Pelvis"][3, 2]))
POSES = {"stab": frame_of("Bob_AttackStab.X", stab_pick),
         "idle": frame_of("Bob_Idle1HandExt02.X", lambda c, T: 0.0)}
jobs = {}
for name, W in POSES.items():
    P.export("merle_" + name, outfit(W))
    upper = bl(W["Bip01_Spine1"][3, :3] * 0.7 + W["Bip01_Head"][3, :3] * 0.15 + W["Bip01_R_Hand"][3, :3] * 0.15)
    arm = bl((W["Bip01_R_Forearm"][3, :3] + W["Bip01_R_Hand"][3, :3]) / 2)
    jobs["merle_%s_full" % name] = ["merle_" + name, 205, upper, 7.0, 6, "nocull"]
    jobs["merle_%s_side" % name] = ["merle_" + name, 245, upper, 7.0, 6, "nocull"]
    jobs["merle_%s_close2" % name] = ["merle_" + name, 215, [arm[0], arm[1], arm[2] - 0.9], 3.6, 10, "nocull"]
    # para la tarjeta del Workshop (make_workshop.make_bayonet_card, out/workshop/renders): cuerpo entero y primer plano
    mid = bl(W["Bip01_Pelvis"][3, :3] * 0.8 + W["Bip01_Head"][3, :3] * 0.2)
    if name == "stab": jobs["knife_attack"] = ["merle_" + name, 245, mid, 12.0, 6, "nocull"]
    else:
        jobs["knife_idle"] = ["merle_" + name, 205, mid, 12.0, 6, "nocull"]
        jobs["knife_close"] = ["merle_" + name, 215, [arm[0], arm[1], arm[2] - 0.9], 3.6, 10, "nocull"]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas ->", P.OUT)
