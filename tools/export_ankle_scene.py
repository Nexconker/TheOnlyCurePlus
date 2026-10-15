"""Escenas de prueba del tobillo bajo el pantalón (comentario de la ronda 2: "hueco en el tobillo con pantalones"):
cuerpo con las piernas ocultas como las oculta el pantalón (máscaras 7 y 9), pie izquierdo amputado (8), pantalón
vaquero vanilla, muñón de pie y la variante "Under" de la prótesis de tobillo (la que el juego usa bajo el
pantalón). Uso: python export_ankle_scene.py -> out/scene/ankle_*.json
Render (con culling como el juego): blender -b -P blender_render.py -- out/scene out/preview/ankle 900 ankle_peg,ankle_mech,ankle_med"""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_x as P

PZ = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media"
MOD = P.RC.MOD
TROUSERS = os.path.join(PZ, "models_X", "Skinned", "Clothes", "Bob_Trousers.x")
TROUSERS_TEX = os.path.join(PZ, "textures", "Clothes", "Trousers_Mesh", "TrousersMesh_DenimLight.png")
STUMP = os.path.join(MOD, "models_X", "Amputation", "Amputation_Left_Foot_Male.X")
STUMP_TEX = os.path.join(MOD, "textures", "Amputations", "Human", "Foot", "skin01_b.png")

clip = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X"))
W = P.worlds_at(clip, 0, False)
for name, tier, tex in (("ankle_peg", "pegLeg", "pegLeg"), ("ankle_mech", "mechLeg", "mechLeg"), ("ankle_med", "medicalLeg", "medicalLeg")):
    meshes = [P.posed_body("Male", [7, 8, 9], W),
              P.posed_x(TROUSERS, TROUSERS_TEX, W),
              P.posed_x(STUMP, STUMP_TEX, W),
              P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%sAnkleUnder_L_M.X" % tier), os.path.join(MOD, "textures", "Prosthesis", tex + ".png"), W)]
    P.export(name, meshes)
# nivel pantorrilla: pilar fino bajo el bajo del pantalón
STUMP_LL = os.path.join(MOD, "models_X", "Amputation", "Amputation_Left_LowerLeg_Male.X")
STUMP_LL_TEX = os.path.join(MOD, "textures", "Amputations", "Human", "LowerLeg", "skin01_b.png")
for name, tier in (("calf_peg", "pegLeg"), ("calf_mech", "mechLeg")):
    P.export(name, [P.posed_body("Male", [7, 8, 9], W), P.posed_x(TROUSERS, TROUSERS_TEX, W), P.posed_x(STUMP_LL, STUMP_LL_TEX, W),
                    P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%sUnder_L_M.X" % tier), os.path.join(MOD, "textures", "Prosthesis", tier + ".png"), W)])
