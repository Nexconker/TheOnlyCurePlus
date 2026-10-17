"""Escenas del brazo bayoneta (3.2.0): reposo y estocada (Bob_AttackStab) por nivel de amputación, y la estocada
vanilla con un cuchillo de caza para comparar el alcance.
Uso: python export_knife_scene.py -> out/scene_knife ; render: blender -b -P blender_render.py -- out/scene_knife out/preview/knife 600"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P

MOD = P.RC.MOD
GAME = os.path.dirname(P.ANIMS)
P.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_knife")
os.makedirs(P.OUT, exist_ok=True)
TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
KTEX = os.path.join(MOD, "textures", "Prosthesis", "knifeArm.png")
S = 10.0
def bl(p): return [float(p[0] * S), float(-p[2] * S), float(p[1] * S)]

def stump(part, W):
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStumpProst_Right_%s_Male.X" % part), TEX, W); m["alpha"] = True
    # medio milímetro hacia dentro: EEVEE pinta negro dos superficies con alfa en el mismo plano
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * 0.0005
    return m

def static_mesh(path, tex, W, prop="Bip01_Prop1"):
    root = P.pzx.parse(path); vs, fs, uvs = [], [], []
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

idle = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X"))
stab = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_AttackStab.X"))
T = max(k[-1][0] for kk in stab["keys"].values() for k in kk.values())
# fotograma de máxima extensión: la mano derecha más adelantada respecto a la pelvis (frente = -Z)
best = max(np.linspace(0, 1, 41), key=lambda f: -(P.worlds_at(stab, f * T, False)["Bip01_R_Hand"][3, 2] - P.worlds_at(stab, f * T, False)["Bip01_Pelvis"][3, 2]))
POSES = {"rest": P.worlds_at(idle, 0, False), "stab": P.worlds_at(stab, best * T, False)}
LEVELS = [("Wrist", "Hand", [6]), ("", "ForeArm", [5, 6]), ("Upper", "UpperArm", [5, 6])]
jobs = {}
for pose, W in POSES.items():
    focus = bl(W["Bip01_R_Hand"][3, :3])
    for lvl, part, masks in LEVELS:
        nm = "knife%s_%s" % (lvl or "Fore", pose)
        P.export(nm, [P.posed_body_texel("Male", masks, W, shirt=False), stump(part, W),
                      P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "knifeArm%s_R_M.X" % lvl), KTEX, W)])
        for az in (200, 270):
            jobs["%s_%d" % (nm, az)] = [nm, az, focus, 3.6 if pose == "rest" else 3.4, 10]
    nm = "knifeVanilla_%s" % pose
    P.export(nm, [P.posed_body_texel("Male", [], W, shirt=False),
                  static_mesh(os.path.join(GAME, "models_X", "weapons", "1handed", "HuntingKnife.X"), os.path.join(GAME, "textures", "weapons", "1handed", "HuntingKnife.png"), W)])
    for az in (200, 270):
        jobs["%s_%d" % (nm, az)] = [nm, az, focus, 3.6 if pose == "rest" else 3.4, 10]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print("estocada en f=%.2f;" % best, len(jobs), "vistas ->", P.OUT)
