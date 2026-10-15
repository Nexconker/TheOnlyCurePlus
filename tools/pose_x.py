"""Posa mallas con pesos (.X) usando un clip de animación .X del juego (AnimationSet con claves S/R/T).
Convención DirectX: matrices fila-mayor, vectores fila (p' = p @ M), mundo = local @ mundo_padre,
piel: v' = sum w_i * v @ offset_i @ mundo_i.  Cuaterniones del .X: (w, x, y, z).

Uso: python pose_x.py            -> valida la convención y exporta out/scene/crawl*.json
"""
import os, sys, json, math
sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pzx
import build_assets as BA
import render_combos as RC
from render_icons import find_mesh

ANIMS = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media\anims_X"
MX = os.path.join(RC.MOD, "models_X")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene")

# ------------------------------------------------------------------ clip
def load_clip(path):
    root = pzx.parse(path)
    bones = {}          # name -> {"parent": str|None, "local": 4x4}
    def walk(node, parent):
        for fr in node.all("Frame"):
            ftm = fr.child("FrameTransformMatrix")
            m = np.array(ftm.data[:16], float).reshape(4, 4) if ftm else np.eye(4)
            bones[fr.name] = {"parent": parent, "local": m}
            walk(fr, fr.name)
    walk(root, None)
    keys = {}           # bone -> {"S": [(t, v)], "R": [...], "T": [...]}
    aset = root.child("AnimationSet")
    for an in aset.all("Animation"):
        ref = an.child("REF"); bone = ref.name if ref else None
        if not bone: continue
        k = {}
        for ak in an.all("AnimationKey"):
            kind = ak.name                 # S / R / T
            d = ak.data; ktype, n = int(d[0]), int(d[1]); i = 2; lst = []
            for _ in range(n):
                t = d[i]; cnt = int(d[i + 1]); vals = d[i + 2:i + 2 + cnt]; i += 2 + cnt
                lst.append((float(t), np.array(vals, float)))
            k[kind] = lst
        keys[bone] = k
    tps = root.child("AnimTicksPerSecond")
    return {"bones": bones, "keys": keys, "ticks": int(tps.data[0]) if tps else 4800}

def quat_to_matrix(q, transpose=False):
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0; w, x, y, z = w / n, x / n, y / n, z / n
    m = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
                  [0, 0, 0, 1]], float)
    return m.T if transpose else m

def interp(lst, t):
    if len(lst) == 1 or t <= lst[0][0]: return lst[0][1]
    if t >= lst[-1][0]: return lst[-1][1]
    for i in range(len(lst) - 1):
        t0, v0 = lst[i]; t1, v1 = lst[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            v = v0 * (1 - f) + v1 * f
            if len(v0) == 4 and np.dot(v0, v1) < 0: v = v0 * (1 - f) - v1 * f
            return v
    return lst[-1][1]

def local_at(clip, bone, t, qt):
    k = clip["keys"].get(bone)
    if not k: return clip["bones"][bone]["local"]
    S = interp(k["S"], t) if "S" in k else np.ones(3)
    R = quat_to_matrix(interp(k["R"], t), qt) if "R" in k else np.eye(4)
    T = interp(k["T"], t) if "T" in k else np.zeros(3)
    Sm = np.diag([S[0], S[1], S[2], 1.0]); Tm = np.eye(4); Tm[3, :3] = T
    return Sm @ R @ Tm

def worlds_at(clip, t, qt, use_bind=False):
    W = {}
    def get(b):
        if b in W: return W[b]
        info = clip["bones"][b]
        loc = info["local"] if use_bind else local_at(clip, b, t, qt)
        W[b] = loc @ get(info["parent"]) if info["parent"] else loc
        return W[b]
    for b in clip["bones"]: get(b)
    return W

def skin(verts, weights, offsets, W):
    """verts (n,3); weights: lista por vértice de [(bone, w)]; offsets: bone -> 16 floats."""
    out = np.zeros((len(verts), 3))
    P = np.hstack([verts, np.ones((len(verts), 1))])
    cache = {}
    for i, ws in enumerate(weights):
        acc = np.zeros(4); tot = 0.0
        for b, w in ws:
            if b not in W or b not in offsets: continue
            if b not in cache: cache[b] = np.array(offsets[b], float).reshape(4, 4) @ W[b]
            acc += w * (P[i] @ cache[b]); tot += w
        out[i] = (acc / tot)[:3] if tot > 0 else verts[i]
    return out

# ------------------------------------------------------------------ validación de la convención
def validate(clip, offsets):
    Wb = worlds_at(clip, 0, False, use_bind=True)
    errs = []
    for b, off in offsets.items():
        if b in Wb:
            inv = np.linalg.inv(np.array(off, float).reshape(4, 4))
            errs.append(np.abs(inv - Wb[b]).max())
    print("bind: inversa(offset) vs mundo(FrameTransformMatrix): error max %.4f (debe ser ~0)" % max(errs))
    # cuaternión: Dummy01 (sin S/T) debe reproducir su FrameTransformMatrix
    d = clip["bones"]["Dummy01"]["local"]
    for qt in (False, True):
        m = local_at(clip, "Dummy01", 0, qt)
        print("cuaternión %s: error vs bind de Dummy01 %.4f" % ("transpuesto" if qt else "directo", np.abs(m - d).max()))

# ------------------------------------------------------------------ escena posada
def posed_body(sex, masks, W):
    body = BA.load_body(sex)
    mesh = RC.body_mesh(sex, masks)
    weights = [sorted(w.items(), key=lambda t: -t[1])[:4] for w in body["weights"]]
    verts = skin(np.array(body["verts"], float), weights, body["offsets"], W)
    return {"v": verts, "f": mesh["f"], "uv": mesh["uv"], "tex": mesh["tex"]}

def posed_body_texel(sex, masks, W, shirt=True):
    """Cuerpo como lo dibuja el juego con máscaras: todas las caras, y el alfa de la textura = máscaras de las partes
    visibles (texel a texel, no por caras). shirt: pinta de rojo el pecho y la cintura, como una camiseta de textura."""
    from PIL import Image
    body = BA.load_body(sex)
    keep = np.array([f for f in body["faces"] if not BA.face_is_hidden(body, f)], int)
    tex = Image.open(os.path.join(RC.PZ, "textures", "Body", ("MaleBody01" if sex == "Male" else "FemaleBody01") + ".png")).convert("RGBA")
    a = np.array(tex)
    hidden = np.zeros(a.shape[:2], bool)
    for i in masks: hidden |= RC.mask_alpha(i) > 0
    if shirt:
        for n in ("Chest", "Waist"):
            mk = np.array(Image.open(os.path.join(RC.PZ, "textures", "Body", "Masks", n + ".png")).convert("RGBA").split()[3]) > 0
            a[mk, :3] = (a[mk, :3] * np.array([0.55, 0.12, 0.12])).astype(np.uint8) + np.array([70, 0, 0], np.uint8)
    a[..., 3] = np.where(hidden, 0, 255)
    weights = [sorted(w.items(), key=lambda t: -t[1])[:4] for w in body["weights"]]
    verts = skin(np.array(body["verts"], float), weights, body["offsets"], W)
    return {"v": verts, "f": keep, "uv": body["uvs"], "tex": Image.fromarray(a), "alpha": True}

def posed_x(path, tex, W):
    m = pzx.read_mesh(find_mesh(pzx.parse(path)))
    verts = np.array(m["verts"], float); faces = np.array([list(f) for f in m["faces"]], int); uv = np.array(m["uvs"], float)
    weights = [[] for _ in verts]; offsets = {}
    for sk in m["skin"]:
        offsets[sk["bone"]] = list(sk["offset"])
        for vi, w in zip(sk["indices"], sk["weights"]): weights[vi].append((sk["bone"], w))
    return {"v": skin(verts, weights, offsets, W), "f": faces, "uv": uv, "tex": tex}

def export(name, meshes):
    from PIL import Image
    out = []
    for i, m in enumerate(meshes):
        tex = m["tex"]
        if not isinstance(tex, str):
            p = os.path.join(OUT, "%s_tex%d.png" % (name, i)); tex.save(p); tex = p
        out.append({"verts": np.asarray(m["v"], float).round(5).tolist(), "faces": np.asarray(m["f"], int).tolist(),
                    "uvs": np.asarray(m["uv"], float).round(5).tolist(), "tex": tex, "alpha": bool(m.get("alpha"))})
    json.dump(out, open(os.path.join(OUT, name + ".json"), "w")); print("scene", name, len(out), "mallas")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    clip = load_clip(os.path.join(ANIMS, "Zombie", "Zombie_Crawl.X"))
    body = BA.load_body("Male")
    validate(clip, body["offsets"])
    QT = False
    TX = RC.TX
    skin_tex = os.path.join(TX, "Amputations", "Human", "LowerLeg", "skin01_b.png")
    for name, frac in (("crawl", 0.38), ("crawl2", 0.80)):
        W = worlds_at(clip, frac * clip["ticks"], QT)
        # mano izquierda oculta (máscara 4) y gancho de nivel muñeca en su lugar
        meshes = [posed_body("Male", [4, 7, 8, 9, 10], W),
                  posed_x(os.path.join(MX, "Amputation", "Amputation_Left_LowerLeg_Male.X"), skin_tex, W),
                  posed_x(os.path.join(MX, "Amputation", "Amputation_Right_LowerLeg_Male.X"), skin_tex, W),
                  posed_x(os.path.join(MX, "Prosthesis", "hookArmWrist_L_M.X"), os.path.join(TX, "Prosthesis", "hookArm.png"), W)]
        # el gancho sustituye al antebrazo izquierdo: ocultar brazo y mano izq. (máscaras 3,4) requiere el muñón FBX;
        # aquí dejamos el brazo y ponemos el gancho sobre la mano: ocultamos la mano izq. (4)
        export(name, meshes)
    idle = load_clip(os.path.join(ANIMS, "Zombie", "Zombie_CrawlIdle.x"))
    W = worlds_at(idle, 0, QT)
    export("crawl_idle", [posed_body("Male", [7, 8, 9, 10], W),
                          posed_x(os.path.join(MX, "Amputation", "Amputation_Left_LowerLeg_Male.X"), skin_tex, W),
                          posed_x(os.path.join(MX, "Amputation", "Amputation_Right_LowerLeg_Male.X"), skin_tex, W)])
