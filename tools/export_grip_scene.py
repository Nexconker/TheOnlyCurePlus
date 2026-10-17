"""Escenas de la mano protésica posada con clips de agarre del juego (3.2.0, "la mano se cierra al agarrar"), junto a la
mano vanilla en la misma pose. Los .X se leen de una carpeta de mod (por defecto el mod; para probar sin tocarlo,
la que escribe blender_to_x.py en otra ruta).
Uso: python export_grip_scene.py [carpeta_media] [out/scene_grip]
Render: blender -b -P blender_render.py -- out/scene_grip out/preview/grip 900"""
import os, sys, json, math
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P

MOD = P.RC.MOD
SRC = _a[0] if _a else MOD
P.OUT = os.path.abspath(_a[1] if len(_a) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene_grip"))
os.makedirs(P.OUT, exist_ok=True)
TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
S = 10.0
def bl(p): return [float(p[0] * S), float(-p[2] * S), float(p[1] * S)]

GAME = os.path.dirname(P.ANIMS)
WEAPONS = {"pistol": ("weapons/firearm/M9_Pistol.x", "weapons/firearm/M9_Pistol.png"),
           "heavy": ("weapons/2handed/SledgeHammer.X", "weapons/2handed/Sledgehammer.png"),
           "onehand": ("weapons/1handed/Hammer_Forged_Hand.x", "weapons/1handed/Hammer_New.png"),
           "aim": ("weapons/firearm/M9_Pistol.x", "weapons/firearm/M9_Pistol.png")}
# (nombre, clip, fracción): agarres con los dedos más cerrados y la muñeca más girada / flexionada (medido con rot_axes)
POSES = [("pistol", "Bob_AimToIdle_Handgun.X", 0.0),      # dedos 77°, muñeca 60°
         ("heavy", "Bob_Idle2H_Heavy.X", 0.0),            # dedos 61°, pulgar 70°
         ("onehand", "Bob_Idle1HandExt02.X", 0.6),        # muñeca girada ~60° (en Ext01 f=0.5 el arma sale de la mano)
         ("aim", "Bob_IdleAim1Hand.X", 0.12)]             # dedos 52°, muñeca flexionada

def held(pname, W):
    """El arma en la mano derecha como la pone el juego: el origen del modelo en Bip01_Prop1, sin giro extra."""
    mesh, tex = WEAPONS[pname]
    root = P.pzx.parse(os.path.join(GAME, "models_X", mesh))
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
    V = np.vstack(vs); V = (np.hstack([V, np.ones((len(V), 1))]) @ W["Bip01_Prop1"])[:, :3]
    return {"v": V, "f": np.vstack(fs), "uv": np.vstack(uvs), "tex": os.path.join(GAME, "textures", tex)}
# lado: TOC_SIDE=L en el entorno prueba la mano izquierda (máscaras del juego: brazo/mano izq. 3/4, der. 5/6)
SIDE = os.environ.get("TOC_SIDE", "R"); SIDE_W = "Left" if SIDE == "L" else "Right"
MH, MA = (4, 3) if SIDE == "L" else (6, 5)
AZS = (160, 60) if SIDE == "L" else (200, 300)
MODELS = [("normalArmWrist", "Hand", [MH], "normalArm"), ("normalArm", "ForeArm", [MA, MH], "normalArm"),
          ("medicalArmWrist", "Hand", [MH], "medicalArm"), ("medicalArm", "ForeArm", [MA, MH], "medicalArm")]

def stump(part, W):
    m = P.posed_x(os.path.join(MOD, "models_X", "Amputation", "ArmStumpProst_%s_%s_Male.X" % (SIDE_W, part)), TEX, W)
    m["alpha"] = True
    v = np.asarray(m["v"], float); n = np.zeros_like(v)
    for a, b, c in m["f"]:
        fn = np.cross(v[b] - v[a], v[c] - v[a]); n[a] += fn; n[b] += fn; n[c] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    m["v"] = v - n * 0.0005
    return m

jobs = {}
for pname, clip, frac in POSES:
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", clip))
    T = max(k[-1][0] for kk in c["keys"].values() for k in kk.values())
    W = P.worlds_at(c, frac * T, False)
    # foco: entre la muñeca y los nudillos de la mano derecha en esta pose
    focus =bl(W["Bip01_%s_Hand" % SIDE][3, :3] + (W["Bip01_%s_Finger1" % SIDE][3, :3] - W["Bip01_%s_Hand" % SIDE][3, :3]) * 0.6)
    item = held(pname, W)
    P.export("vanilla_%s" % pname, [P.posed_body_texel("Male", [], W, shirt=False), item])
    for az in AZS:
        jobs["%s_vanilla_%d" % (pname, az)] = ["vanilla_%s" % pname, az, focus, 1.5, 15]
    for model, part, masks, tex in MODELS:
        nm = "%s_%s" % (pname, model)
        P.export(nm, [P.posed_body_texel("Male", masks, W, shirt=False), stump(part, W), item,
                      P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "%s_%s_M.X" % (model, SIDE)), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), W)])
        for az in AZS:
            jobs["%s_%d" % (nm, az)] = [nm, az, focus, 1.5, 15]
# secuencia de cierre (para un GIF): pose de la pistola con dedos y pulgar interpolados desde el reposo (bind) hasta el
# agarre del clip, sin arma (abierta la atravesaría)
def _quat(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; return np.array([0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s])
    i = int(np.argmax(np.diag(m)))
    if i == 0:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; return np.array([(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s])
    if i == 1:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; return np.array([(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s])
    s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; return np.array([(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s])
def _mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def _slerp(a, b, t):
    if np.dot(a, b) < 0: b = -b
    d = min(1.0, float(np.dot(a, b))); th = math.acos(d)
    if th < 1e-6: return a
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)
offs = P.BA.load_body("Male")["offsets"]
Wb = {b: np.linalg.inv(np.array(o, float).reshape(4, 4)) for b, o in offs.items()}
c = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_AimToIdle_Handgun.X"))
W = P.worlds_at(c, 0.0, False)
focus = bl(W["Bip01_%s_Hand" % SIDE][3, :3] + (W["Bip01_%s_Finger1" % SIDE][3, :3] - W["Bip01_%s_Hand" % SIDE][3, :3]) * 0.6)
# cámara a lo largo de la bisagra de los dedos, del lado del meñique: los dedos se ven de perfil al cerrarse
h = W["Bip01_%s_Finger1" % SIDE][1, :3] / np.linalg.norm(W["Bip01_%s_Finger1" % SIDE][1, :3])
if np.dot(W["Bip01_%s_Finger0" % SIDE][3, :3] - W["Bip01_%s_Finger1" % SIDE][3, :3], h) > 0: h = -h
hb_ = np.array([h[0], -h[2], h[1]])
AZ = math.degrees(math.atan2(hb_[0], -hb_[1])); EL = max(-30.0, min(60.0, math.degrees(math.asin(hb_[2]))))
N_FR = 7
for k in range(N_FR):
    t = k / (N_FR - 1)
    Wt = dict(W)
    for b in ("Bip01_%s_Finger0" % SIDE, "Bip01_%s_Finger1" % SIDE):
        ra = W[b] @ np.linalg.inv(W["Bip01_%s_Hand" % SIDE]); rb = Wb[b] @ np.linalg.inv(Wb["Bip01_%s_Hand" % SIDE])
        q = _slerp(_quat(rb[:3, :3].T), _quat(ra[:3, :3].T), t)
        r = np.eye(4); r[:3, :3] = _mat(q).T; r[3, :3] = rb[3, :3] * (1 - t) + ra[3, :3] * t
        Wt[b] = r @ W["Bip01_%s_Hand" % SIDE]
    for model, part, masks, tex in MODELS[1:2] + MODELS[3:4]:
        nm = "close_%s_%d" % (model, k)
        P.export(nm, [P.posed_body_texel("Male", masks, Wt, shirt=False), stump(part, Wt),
                      P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "%s_%s_M.X" % (model, SIDE)), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), Wt)])
        jobs[nm] = [nm, AZ, focus, 1.5, EL]
    nm = "close_vanilla_%d" % k
    P.export(nm, [P.posed_body_texel("Male", [], Wt, shirt=False)])
    jobs[nm] = [nm, AZ, focus, 1.5, EL]
json.dump(jobs, open(os.path.join(P.OUT, "tomb_jobs.json"), "w"), indent=0)
print("trabajos:", len(jobs), "->", P.OUT)
