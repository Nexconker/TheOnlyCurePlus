"""Escenas del brazo motosierra posadas con animaciones vanilla de arma de una mano (para revisar el montaje y para
las imágenes del Workshop). Uso: python export_chainsaw_scene.py  ->  out/scene/saw_*.json
Render: blender -b -P blender_render.py -- out/scene out/preview/saw 900 saw_idle,saw_idle_fa,saw_close,saw_close_fa,saw_attack"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P
import build_assets as BA

MX = os.path.join(P.RC.MOD, "models_X", "Prosthesis")
TEX = os.path.join(P.RC.MOD, "textures", "Prosthesis", "chainsawArm.png")
FIT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "fit.json"), encoding="utf-8"))
os.makedirs(P.OUT, exist_ok=True)

def cut_forearm(posed, sex, t_cut):
    """Sin el modelo del muñón (FBX sin pesos): quita del cuerpo las caras del antebrazo/mano derechos más allá
    del corte, medido en la pose de reposo a lo largo del eje del antebrazo."""
    b = BA.load_body(sex); arm = FIT["bodies"][sex]["arms"]["R"]
    o, a = np.array(arm["o"]), np.array(arm["axis"])
    V = np.array(b["verts"], float); t = (V - o) @ a
    lower = np.array([sum(w for bn, w in b["weights"][i].items() if bn.startswith(("Bip01_R_Fore", "Bip01_R_Hand", "Bip01_R_Finger"))) > 0.5
                      for i in range(len(V))])
    drop = lower & (t > t_cut)
    posed["f"] = np.array([f for f in np.asarray(posed["f"]) if not drop[list(f)].any()], int)
    return posed

def scene(name, clip, frac, sex="Male", level="Wrist"):
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", clip))
    T = max(k["R"][-1][0] for k in c["keys"].values() if "R" in k)
    W = P.worlds_at(c, frac * T, False)
    sx = "M" if sex == "Male" else "F"
    body = P.posed_body(sex, [6], W)                 # mano derecha oculta (máscara 6)
    if level == "ForeArm": body = cut_forearm(body, sex, 0.045)
    arm = P.posed_x(os.path.join(MX, "chainsawArm%s_R_%s.X" % ("Wrist" if level == "Wrist" else "", sx)), TEX, W)
    P.export(name, [body, arm])

# brazo motosierra rígido al antebrazo: animaciones de arma de una mano (brazo relajado, tajo con el brazo)
scene("saw_idle", "Bob_Idle.X", 0.0)
scene("saw_idle_fa", "Bob_Idle.X", 0.0, level="ForeArm")
scene("saw_walk", "Bob_Walk.X", 0.3)
scene("saw_attack", "Bob_Attack1Hand01_Hit.X", 0.35)
scene("saw_idle_f", "Bob_Idle.X", 0.0, "Female")
