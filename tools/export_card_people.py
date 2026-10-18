"""Personajes vestidos para las tarjetas del Workshop (2026-10-17, "ponle algo de ropa y pelo al render de arrastrarse y
al de surgery is loud"). Mismas poses y nombres de escena que antes (pose_x.py y export_noise_scene.py), así las
tarjetas de make_workshop.py no cambian:
  - crawl2: sin las dos piernas por debajo de la rodilla y con gancho en la mano izquierda, arrastrándose (Zombie_Crawl):
    camisa de franela, vaqueros cortados bajo la rodilla sobre los muñones, pelo y barba.
  - noise_patient: se opera el pie izquierdo (Bob_BandageLeftLeg): camiseta, pantalón corto vaquero, bota, pelo.
  - noise_zombie0..2: zombis caminando (Zombie_Walk) con camiseta y pantalón sucios y pelo despeinado.
Uso: python export_card_people.py -> out/scene ; render: blender -b -P blender_render.py -- out/scene out/workshop/renders 1600 crawl2,noise_patient,noise_zombie0,noise_zombie1,noise_zombie2"""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import pose_x as P
import render_combos as RC
import outfits as O

MX = os.path.join(RC.MOD, "models_X")
DENIM = O.clothes_tex("Trousers_Mesh", "TrousersMesh_Denim.png")
CALF_FOOT = ("Bip01_L_Calf", "Bip01_R_Calf", "Bip01_L_Foot", "Bip01_R_Foot", "Bip01_L_Toe", "Bip01_R_Toe")

# ---- crawl2: la pose de la tarjeta (Zombie_Crawl al 80 %, como pose_x.py)
clip = P.load_clip(os.path.join(P.ANIMS, "Zombie", "Zombie_Crawl.X"))
W = P.worlds_at(clip, 0.80 * clip["ticks"], False)
leg_tex = O.stump_tex("LowerLeg", "MaleBody02")
tex = O.body_texture("MaleBody02", overlays=[O.grimy(O.clothes_tex("Shirt_Tshirt_Textures", "Shirt_LumberjackRed.png"), 0.3, blood=10, seed=3)],
                     hide=("LeftHand", "LeftLeg", "LeftFoot", "RightLeg", "RightFoot", "Crotch"))
P.export("crawl2", [O.body(W, tex),
                    P.posed_x(os.path.join(MX, "Amputation", "Amputation_Left_LowerLeg_Male.X"), leg_tex, W),
                    P.posed_x(os.path.join(MX, "Amputation", "Amputation_Right_LowerLeg_Male.X"), leg_tex, W),
                    O.mesh(os.path.join("Clothes", "Bob_Trousers.x"), O.grimy(DENIM, 0.35, seed=5), W, drop_bones=CALF_FOOT),
                    O.hair("Messy", W), O.beard("Full", W),
                    P.posed_x(os.path.join(MX, "Prosthesis", "baseScrapWrist_L_M.X"), os.path.join(RC.TX, "Prosthesis", "knifeArm.png"), W),
                    P.posed_x(os.path.join(MX, "Prosthesis", "headHook_L_M.X"), os.path.join(RC.TX, "Prosthesis", "hookArm.png"), W)])

# ---- noise_patient: se venda el pie izquierdo amputado (Bob_BandageLeftLeg a mitad, como export_noise_scene.py)
clip = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_BandageLeftLeg.X"))
end = max(t for k in clip["keys"].values() for t, _ in k.get("R", [(0, 0)]))
W = P.worlds_at(clip, 0.5 * end, False)
tex = O.body_texture("MaleBody03", overlays=[O.clothes_tex("Shoes_Socks_Textres", "ArmyBoots.png"),
                                             O.grimy(O.clothes_tex("Shirt_Tshirt_Textures", "TShirt_Grey.png"), 0.25, blood=8, seed=9),
                                             O.clothes_tex("Shorts_Textures", "LongShorts_Denim.png")],
                     hide=("LeftFoot",))
P.export("noise_patient", [O.body(W, tex),
                           P.posed_x(os.path.join(MX, "Amputation", "Amputation_Left_Foot_Male.X"), O.stump_tex("Foot", "MaleBody03", cicatrized=False), W),
                           O.hair("Short", W, (40, 30, 22))])

# ---- zombis: camiseta y pantalón sucios, pelo despeinado
walk = P.load_clip(os.path.join(P.ANIMS, "Zombie", "Zombie_Walk.X"))
end = max(t for k in walk["keys"].values() for t, _ in k.get("R", [(0, 0)]))
SHIRTS = ["TShirt_White.png", "Shirt_LumberjackGrey.png", "TShirt_Grey.png"]
PANTS = [DENIM, O.clothes_tex("Trousers_Mesh", "TrousersMesh_Black.png"), O.clothes_tex("Trousers_Mesh", "TrousersMesh_DenimLight.png")]
HAIRS = [("Messy", (54, 46, 38)), ("Grungey", (70, 62, 52)), ("Recede", (96, 90, 82))]
for i, frac in enumerate((0.1, 0.45, 0.8)):
    W = P.worlds_at(walk, frac * end, False)
    zb = Image.open(os.path.join(O.TEX, "Body", "M_ZedBody01_level%d.png" % (1 + i % 3))).convert("RGBA")
    base = Image.new("RGBA", zb.size, (118, 112, 96, 255)); base.alpha_composite(zb)
    tex = O.body_texture(base, overlays=[O.grimy(O.clothes_tex("Shirt_Tshirt_Textures", SHIRTS[i]), 0.55, blood=30, seed=20 + i)],
                         hide=("LeftLeg", "RightLeg", "Crotch"))
    P.export("noise_zombie%d" % i, [O.body(W, tex),
                                    O.mesh(os.path.join("Clothes", "Bob_Trousers.x"), O.grimy(O.tinted(PANTS[i], (180, 172, 160)), 0.5, blood=12, seed=30 + i), W),
                                    O.hair(HAIRS[i][0], W, HAIRS[i][1])])
print("escenas: crawl2, noise_patient, noise_zombie0-2")
