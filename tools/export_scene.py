"""Exporta a JSON las escenas del muestrario (personajes con muñones y prótesis, herramientas) para
renderizarlas en Blender con luces de verdad. Uso: python export_scene.py  ->  out/scene/*.json + texturas"""
import os, sys, json
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import render_combos as RC
from render_icons import load_x

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scene")
os.makedirs(OUT, exist_ok=True)
MX = os.path.join(RC.MOD, "models_X")

def save_tex(img, name):
    p = os.path.join(OUT, name + ".png"); img.save(p); return p

def mesh_entry(m, texpath):
    return {"verts": np.asarray(m["v"], float).round(5).tolist(), "faces": np.asarray(m["f"], int).tolist(),
            "uvs": np.asarray(m["uv"], float).round(5).tolist(), "tex": texpath}

def character(sex, combo_name):
    cs = {c[0]: c for c in RC.combos(sex)}
    label, masks, pieces = cs[combo_name]
    body = RC.body_mesh(sex, masks)
    meshes = [mesh_entry(body, save_tex(body["tex"], "body_%s_%s" % (sex, "".join(c for c in combo_name if c.isalnum()))))]
    for kind, path, tex in pieces:
        if kind == "x":
            meshes.append(mesh_entry(RC.piece_x(path, tex), tex))
        else:
            for pm in RC.piece_fbx(path, tex): meshes.append(mesh_entry(pm, tex))
    return meshes

def multi(sex, combo_names):
    """Varias combinaciones sobre el mismo cuerpo (pierna izq. + brazo izq.): une máscaras y piezas."""
    cs = {c[0]: c for c in RC.combos(sex)}
    masks, pieces = [], []
    for n in combo_names:
        _, m, p = cs[n]; masks += m; pieces += p
    body = RC.body_mesh(sex, sorted(set(masks)))
    meshes = [mesh_entry(body, save_tex(body["tex"], "body_%s_%s" % (sex, len(combo_names))))]
    for kind, path, tex in pieces:
        if kind == "x": meshes.append(mesh_entry(RC.piece_x(path, tex), tex))
        else:
            for pm in RC.piece_fbx(path, tex): meshes.append(mesh_entry(pm, tex))
    return meshes

scenes = {
    "hero_female": multi("Female", ["Muslo + pierna mecanica", "Antebrazo + gancho"]),
    "hero_male": multi("Male", ["Pantorrilla + pierna medica", "Mano izq. + brazo mecanico"]),
    "legs_peg": character("Male", "Pantorrilla + pata de palo"),
    "legs_mech": character("Male", "Muslo + pierna mecanica"),
    "legs_medical": character("Female", "Pie izq. + pierna medica"),
    "arms_peg": character("Male", "Antebrazo + brazo de madera"),
    "arms_hook": character("Female", "Antebrazo + gancho"),
    "arms_mech": character("Male", "Antebrazo + brazo mecanico"),
    "arms_medical": character("Female", "Mano izq. + brazo medico"),
    "stumps": multi("Male", ["Pantorrilla izq. amputada", "Antebrazo izq. amputado"]),
}
for name, meshes in scenes.items():
    json.dump(meshes, open(os.path.join(OUT, name + ".json"), "w"))
    print("scene", name, len(meshes), "mallas")
# herramientas sueltas
for nm, rel, tex in (("bonesaw", "Weapons/BoneSaw.X", "Weapons/bonesaw.png"), ("crutch", "Weapons/Crutch.X", "Weapons/crutch.png"),
                     ("severed_leg", "Severed/SeveredLowerLeg.X", "Amputations/Human/LowerLeg/skin01_b.png"),
                     ("hook_ground", "Prosthesis/hookArm_Ground.X", "Prosthesis/hookArm.png"), ("mechleg_ground", "Prosthesis/mechLeg_Ground.X", "Prosthesis/mechLeg.png")):
    v, f, uv = load_x(os.path.join(MX, rel))
    json.dump([mesh_entry({"v": v, "f": f, "uv": uv}, os.path.join(RC.TX, tex))], open(os.path.join(OUT, nm + ".json"), "w"))
    print("prop", nm)
