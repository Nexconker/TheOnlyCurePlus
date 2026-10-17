"""Escenas de la mano fantasma (3.2.0): acción vanilla con las dos manos al lado de su clip espejado (make_mirror_anims.py)
con la mano que usa la acción amputada y el objeto en la otra mano, en el fotograma en que la mano llega a la boca.
Uso: python export_mirror_scene.py -> out/scene_mirror ; render: blender -b -P blender_render.py -- out/scene_mirror out/preview/mirror 600"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import build_assets as BA

MOD = P.RC.MOD
GAME = os.path.dirname(P.ANIMS)
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_mirror")
os.makedirs(P.OUT, exist_ok=True)
TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
S = 10.0
def bl(p): return [float(p[0] * S), float(-p[2] * S), float(p[1] * S)]

# (nombre, clip vanilla, mano que usa, objeto (malla, textura))
CASES = [("pills", "Bob_IdleTakePills", "L", ("PillBottle.X", "PillBottle.png")),
         ("drink", "Bob_IdleDrinkTinCan", "L", ("PillBottle.X", "PillBottle.png")),
         ("smoke", "Bob_IdleSmoke", "L", ("Cigarette.X", None)),
         ("tap", "Bob_IdleDrinkWithHand", "R", None),
         ("book", "Bob_IdleReadBook", "R", None)]

def static_mesh(path, tex, W, prop):
    root = P.pzx.parse(path)
    vs, fs, uvs = [], [], []
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

def stump_hand(side, W):
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStump_%s_Hand_Male.X" % ("Left" if side == "L" else "Right")), TEX, W)
    m["alpha"] = True
    return m

def best_frame(clip, hand):
    T = max(k[-1][0] for kk in clip["keys"].values() for k in kk.values())
    best = (9, 0)
    for f in np.linspace(0, 1, 41):
        W = P.worlds_at(clip, f * T, False)
        d = np.linalg.norm(W["Bip01_%s_Hand" % hand][3, :3] - W["Bip01_Head"][3, :3])
        best = min(best, (d, f))
    return best[1] * T

jobs = {}
for name, clip, hand, item in CASES:
    other = "R" if hand == "L" else "L"
    van = P.load_clip(os.path.join(P.ANIMS, "Bob", clip + ".X"))
    mir = P.load_clip(os.path.join(MOD, "anims_X", "Bob", "TOC_Mirror_" + clip + ".X"))
    tv, tm = best_frame(van, hand), best_frame(mir, other)
    Wv, Wm = P.worlds_at(van, tv, False), P.worlds_at(mir, tm, False)
    pv, pm = ("Bip01_Prop2", "Bip01_Prop1") if hand == "L" else ("Bip01_Prop1", "Bip01_Prop2")
    mv = [P.posed_body_texel("Male", [], Wv, shirt=False)]
    mm = [P.posed_body_texel("Male", [4 if hand == "L" else 6], Wm, shirt=False), stump_hand(hand, Wm)]
    if item:
        tex = os.path.join(GAME, "textures", item[1]) if item[1] else os.path.join(GAME, "textures", "Cigarette.png")
        mv.append(static_mesh(os.path.join(GAME, "models_X", item[0]), tex, Wv, pv))
        mm.append(static_mesh(os.path.join(GAME, "models_X", item[0]), tex, Wm, pm))
    P.export("van_" + name, mv); P.export("mir_" + name, mm)
    fv = bl(Wv["Bip01_Head"][3, :3] * 0.6 + Wv["Bip01_%s_Hand" % hand][3, :3] * 0.4)
    fm = bl(Wm["Bip01_Head"][3, :3] * 0.6 + Wm["Bip01_%s_Hand" % other][3, :3] * 0.4)
    for az in (180, 215, 145):
        jobs["van_%s_%d" % (name, az)] = ["van_" + name, az, fv, 2.6, 8]
        jobs["mir_%s_%d" % (name, az)] = ["mir_" + name, az, fm, 2.6, 8]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print(len(jobs), "vistas ->", P.OUT)
