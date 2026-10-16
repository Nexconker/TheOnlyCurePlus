"""Escenas para ver las prótesis sobre el cuerpo de Tomb's Player Body como lo dibuja el juego (máscaras por texel con su
textura), al lado del cuerpo vanilla. Sólo para mirar en local: no se publica nada de Tomb.
Uso: python tomb_preview.py [carpeta del submod con los .X ajustados]  ->  out/scene/tomb_*.json  y imprime los JOBS
Render: blender -b -P blender_render.py -- out/scene out/preview/tomb 600 tomb_wrist_v,tomb_wrist_t,..."""
import os, sys, json
_ARGV = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import pose_x as P
import build_assets as BA, render_combos as RC
from tomb_common import tomb_main_faces

MOD = RC.MOD
PROST = _ARGV[0] if _ARGV else os.path.join(MOD, "models_X", "Prosthesis")
TT = r"D:\SteamLibrary\steamapps\workshop\content\108600\3429790870\mods\Tomb's Player Body - Textures\common\media\textures\Body"
clip = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X"))
W = P.worlds_at(clip, 0, False)

def masked_tex(img, masks):
    a = np.array(img.convert("RGBA")); H = a.shape[0]
    hidden = np.zeros((256, 256), bool)
    for i in masks: hidden |= RC.mask_alpha(i) > 0
    hidden = np.array(Image.fromarray(hidden.astype(np.uint8) * 255).resize((H, H), Image.NEAREST)) > 0
    a[..., 3] = np.where(hidden, 0, np.where(a[..., 3] < 8, 0, 255))
    return Image.fromarray(a)

def tomb_body(sex, masks):
    T = json.load(open(os.path.join("out", "tomb", sex + ".json")))["meshes"][0]
    v = np.load(os.path.join("out", "tomb", sex + "_verts_pz.npy"))
    keep = tomb_main_faces(T["tris"], len(v))
    # vértices por esquina (las UV de Tomb van por esquina de triángulo)
    verts, uvs, faces, wts = [], [], [], []
    for k in keep:
        f = []
        for vi, (u, w) in zip(T["tris"][k], T["uvs"][k]):
            f.append(len(verts)); verts.append(v[vi]); uvs.append((u, 1 - w)); wts.append(sorted(T["weights"][vi].items(), key=lambda t: -t[1])[:4])
        faces.append([f[0], f[2], f[1]])           # deshace la reflexión (x, y, z) -> (x, z, y)
    vb = BA.load_body(sex)
    posed = P.skin(np.array(verts), wts, vb["offsets"], W)
    tex = masked_tex(Image.open(os.path.join(TT, ("MaleBody01" if sex == "Male" else "FemaleBody01") + ".png")), masks)
    return {"v": posed, "f": np.array(faces), "uv": np.array(uvs), "tex": tex, "alpha": True}

def inward(m, d=0.0005):
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * d; m["alpha"] = True
    return m

def stump(kind, part, side, sex):
    tex = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png" if sex == "Male" else "skinF01_b.png")
    if kind == "arm":
        name = "ArmStump%s_%s_%s_%s" % ("" if part == "Hand" else "Prost", BA.SIDE_NAME[side], part, sex)
    else:
        name = "Amputation_%s_%s_%s" % (BA.SIDE_NAME[side], part, sex)
        tex = tex.replace("LowerLeg", part)
    return inward(P.posed_x(os.path.join(MOD, "models_X", "Amputation", name + ".X"), tex, W))

def prost(model, sex):
    texname = model.split("Arm")[0] + "Arm" if "Arm" in model else model.split("Leg")[0] + "Leg"
    return P.posed_x(os.path.join(PROST, "%s_%s.X" % (model, "M" if sex == "Male" else "F")), os.path.join(MOD, "textures", "Prosthesis", texname + ".png"), W)

CASES = {  # nombre: (máscaras ocultas, (tipo, parte), modelo)
    "wrist": ((5 + 1,), ("arm", "Hand"), "normalArmWrist_R"),
    "ankle": ((10,), ("leg", "Foot"), "mechLegAnkle_R"),
    "thigh": ((9, 10), ("leg", "UpperLeg"), "mechLegThigh_R"),
    "calf": ((9, 10), ("leg", "LowerLeg"), "mechLeg_R"),
}
if __name__ == "__main__":
    jobs = {}
    for case, (masks, (kind, part), model) in CASES.items():
        for sex in ("Male", "Female"):
            st = stump(kind, part, "R", sex); pr = prost(model, sex)
            c = np.asarray(pr["v"]).mean(0); focus = (round(c[0] * 10, 2), round(-c[2] * 10, 2), round(c[1] * 10, 2))
            tag = "%s_%s" % (case, sex[0].lower())
            P.export("tomb_%s_v" % tag, [P.posed_body_texel(sex, list(masks), W, shirt=False), st, pr])
            P.export("tomb_%s_t" % tag, [tomb_body(sex, masks), st, pr])
            for suffix in ("v", "t"):
                for view, az in (("", 200), ("b", 20)):
                    jobs["tomb_%s_%s%s" % (tag, suffix, view)] = ("tomb_%s_%s" % (tag, suffix), az, focus)
    json.dump(jobs, open(os.path.join("out", "scene", "tomb_jobs.json"), "w"))
    print(len(jobs), "vistas")
