"""Escena para la tarjeta del ruido: paciente sentado operándose la pierna (Bob_BandageLeftLeg) y zombis
caminando (Zombie_Walk) en distintas fases. Exporta out/scene/noise_patient.json y noise_zombieN.json."""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import pose_x as PX
import render_combos as RC

BODYTEX = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media\textures\Body"

def zombie_tex(level=2):
    tex = Image.open(os.path.join(BODYTEX, "M_ZedBody01_level%d.png" % level)).convert("RGBA")
    bg = Image.new("RGBA", tex.size, (110, 105, 90, 255)); bg.alpha_composite(tex); return bg

# paciente: pose de vendarse la pierna izquierda, a mitad del clip; sin pie izquierdo (máscara 8) + muñón
clip = PX.load_clip(os.path.join(PX.ANIMS, "Bob", "Bob_BandageLeftLeg.X"))
W = PX.worlds_at(clip, 0.5 * clip["ticks"] * (max(t for k in clip["keys"].values() for t, _ in k.get("R", [(0, 0)])) / clip["ticks"]), False)
meshes = [PX.posed_body("Male", [8], W),
          PX.posed_x(os.path.join(PX.MX, "Amputation", "Amputation_Left_Foot_Male.X"),
                     os.path.join(RC.TX, "Amputations", "Human", "Foot", "skin01_b.png"), W)]
PX.export("noise_patient", meshes)

walk = PX.load_clip(os.path.join(PX.ANIMS, "Zombie", "Zombie_Walk.X"))
end = max(t for k in walk["keys"].values() for t, _ in k.get("R", [(0, 0)]))
for i, frac in enumerate((0.1, 0.45, 0.8)):
    W = PX.worlds_at(walk, frac * end, False)
    z = PX.posed_body("Male", [], W); z["tex"] = zombie_tex(1 + i % 3)
    PX.export("noise_zombie%d" % i, [z])
