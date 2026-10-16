"""Lee los cuerpos FBX de Tomb's Player Body (sólo para ANALIZAR: no se redistribuye nada suyo) y vuelca vértices, UV,
caras y pesos a JSON para compararlos con el cuerpo vanilla. Uso:
blender -b -P tomb_export.py -- <carpeta con MaleBody.fbx/FemaleBody.fbx> <salida>"""
import bpy, sys, os, json
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
for sex in ("Male", "Female"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, sex + "Body.fbx"))
    res = {"meshes": [], "bones": {}}
    for ob in bpy.data.objects:
        if ob.type == "ARMATURE":
            for b in ob.data.bones:
                res["bones"][b.name] = {"head": list(ob.matrix_world @ b.head_local), "tail": list(ob.matrix_world @ b.tail_local)}
        if ob.type != "MESH": continue
        me = ob.data; me.calc_loop_triangles()
        uvl = me.uv_layers.active.data if me.uv_layers.active else None
        verts = [list(ob.matrix_world @ v.co) for v in me.vertices]
        tris, uvs, nors = [], [], []
        nm = ob.matrix_world.to_3x3().inverted().transposed()
        cn = me.corner_normals if hasattr(me, "corner_normals") else None
        for t in me.loop_triangles:
            tris.append(list(t.vertices))
            uvs.append([list(uvl[li].uv) for li in t.loops] if uvl else [])
            nors.append([list((nm @ (cn[li].vector if cn else me.loops[li].normal)).normalized()) for li in t.loops])
        groups = {g.index: g.name for g in ob.vertex_groups}
        weights = [{groups[g.group]: g.weight for g in v.groups if g.weight > 0.001} for v in me.vertices]
        mats = [m.name for m in me.materials]
        res["meshes"].append({"name": ob.name, "verts": verts, "tris": tris, "uvs": uvs, "nors": nors, "weights": weights, "materials": mats,
                              "tri_mat": [t.material_index for t in me.loop_triangles]})
        print(sex, ob.name, len(verts), "verts", len(tris), "tris", "uv" if uvl else "SIN UV", mats)
    json.dump(res, open(os.path.join(OUT, sex + ".json"), "w"))
print("TOMB EXPORT DONE")
