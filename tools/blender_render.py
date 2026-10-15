"""Renderiza las escenas exportadas por export_scene.py con EEVEE (luz de 3 puntos, sombras, fondo
transparente). Uso: blender -b -P blender_render.py -- out/scene out/workshop/renders [size]"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = os.path.abspath(argv[0]) if argv else os.path.abspath("out/scene")
OUT = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.abspath("out/workshop/renders")
SIZE = int(argv[2]) if len(argv) > 2 else 1600
os.makedirs(OUT, exist_ok=True)
S = 10.0
def bl(p): return (p[0] * S, -p[2] * S, p[1] * S)

scene = bpy.context.scene
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
try: scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    try: scene.render.engine = "BLENDER_EEVEE"
    except TypeError: pass
scene.render.film_transparent = True
scene.render.resolution_x = SIZE; scene.render.resolution_y = SIZE; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"
try:
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_shadows = True
except Exception: pass
scene.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else scene.view_settings.view_transform
scene.view_settings.look = "None"

def material(texpath, name):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.get(os.path.basename(texpath)) or bpy.data.images.load(texpath)
    tex.image = img; tex.interpolation = "Closest" if img.size[0] <= 256 else "Linear"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    if "metal" in texpath.lower() or "hook" in texpath.lower() or "normalArm" in texpath or "medical" in texpath.lower():
        bsdf.inputs["Metallic"].default_value = 0.35; bsdf.inputs["Roughness"].default_value = 0.4
    mat.blend_method = "OPAQUE" if hasattr(mat, "blend_method") else None
    return mat

KEEP_WINDING = False
def add_mesh(entry, name, offset=(0, 0, 0), rotz=0.0):
    me = bpy.data.meshes.new(name)
    verts = [bl(v) for v in entry["verts"]]
    me.from_pydata(verts, [], entry["faces"]); me.update()
    uv = me.uv_layers.new(name="uv")
    uvs = entry["uvs"]
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = (uvs[vi][0], 1.0 - uvs[vi][1])
    if not KEEP_WINDING:   # con culling (como el juego) se respeta el orden de vértices del archivo
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ob.location = Vector(offset); ob.rotation_euler = (0, 0, math.radians(rotz))
    ob.data.materials.append(material(entry["tex"], name + "_mat"))
    return ob

def lights():
    for o in [o for o in scene.objects if o.type in ("LIGHT", "CAMERA")]: bpy.data.objects.remove(o, do_unlink=True)
    def light(name, kind, loc, energy, color=(1, 1, 1), size=3.0):
        ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
        if kind == "AREA": ld.size = size
        if kind == "SUN": ld.angle = math.radians(3)
        lo = bpy.data.objects.new(name, ld); scene.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        return lo
    light("key", "AREA", (-9, 10, 12), 2500, (1.0, 0.95, 0.88), 5)
    light("fill", "AREA", (10, 8, 6), 600, (0.85, 0.9, 1.0), 6)
    light("rim", "AREA", (4, -10, 9), 1800, (0.8, 0.9, 1.0), 3)
    world = scene.world or bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (0.08, 0.08, 0.1, 1); bg.inputs[1].default_value = 0.6

def camera(target, dist, elev=10, azim=-30, ortho=False, scale=10):
    cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); scene.collection.objects.link(cam); scene.camera = cam
    cd.lens = 70
    if ortho: cd.type = "ORTHO"; cd.ortho_scale = scale
    t = Vector(target); a, e = math.radians(azim), math.radians(elev)
    cam.location = t + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam

def bounds(objs):
    pts = [ob.matrix_world @ Vector(c) for ob in objs for c in ob.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx

def render(name, objs, elev=8, azim=-28, fit=1.0, zoom=None, focus=None):
    mn, mx = bounds(objs); c = (mn + mx) / 2; size = max(mx - mn)
    if focus is not None: c = Vector(focus)
    if zoom: size = zoom
    camera(c, size * 2.2 * fit, elev, azim)
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("render", name)

def clear():
    for ob in [o for o in scene.objects if o.type == "MESH"]: bpy.data.objects.remove(ob, do_unlink=True)

lights()
JOBS = {
    # nombre: (escenas [(json, offset_x)], elev, azim, zoom, foco)
    "hero": ([("hero_female", -2.6, 25), ("hero_male", 2.6, -25)], 6, 180, None, None),
    "hero_f": ([("hero_female", 0, 0)], 6, 150, None, None),
    "hero_m": ([("hero_male", 0, 0)], 6, 150, None, None),
    "legs_peg": ([("legs_peg", 0, 0)], 4, 145, 4.2, (0, 0, 2.1)),
    "legs_mech": ([("legs_mech", 0, 0)], 4, 145, 5.2, (0, 0, 2.4)),
    "legs_medical": ([("legs_medical", 0, 0)], 4, 145, 3.4, (0, 0, 1.6)),
    "arms_peg": ([("arms_peg", 0, 0)], 12, 150, 3.6, (2.6, 0, 7.4)),
    "arms_hook": ([("arms_hook", 0, 0)], 12, 150, 3.6, (2.6, 0, 7.4)),
    "arms_mech": ([("arms_mech", 0, 0)], 12, 150, 3.6, (2.6, 0, 7.4)),
    "arms_medical": ([("arms_medical", 0, 0)], 12, 150, 3.6, (2.6, 0, 7.4)),
    "stumps": ([("stumps", 0, 0)], 8, 150, None, None),
    "bonesaw": ([("bonesaw", 0, 0)], 25, 140, None, None),
    "crutch": ([("crutch", 0, 0)], 10, 150, None, None),
    "crawl": ([("crawl", 0, 0)], 14, 150, None, None),
    "crawl2": ([("crawl2", 0, 0)], 14, 210, None, None),
    "crawl_idle": ([("crawl_idle", 0, 0)], 18, 165, None, None),
    "noise_patient": ([("noise_patient", 0, 0)], 18, 110, None, None),
    "noise_zombie0": ([("noise_zombie0", 0, 0)], 22, 150, None, None),
    "noise_zombie1": ([("noise_zombie1", 0, 0)], 22, 200, None, None),
    "noise_zombie2": ([("noise_zombie2", 0, 0)], 22, 250, None, None),
    "prop_hook": ([("hook_ground", 0, 0)], 40, 150, None, None),
    "prop_mechleg": ([("mechleg_ground", 0, 0)], 40, 150, None, None),
    "prop_leg": ([("severed_leg", 0, 0)], 40, 150, None, None),
    "saw_idle": ([("saw_idle", 0, 0)], 6, 190, None, None),
    "saw_walk": ([("saw_walk", 0, 0)], 8, 225, None, None),
    "saw_attack": ([("saw_attack", 0, 0)], 10, 200, None, None),
    "saw_idle_fa": ([("saw_idle_fa", 0, 0)], 6, 190, None, None),
    "saw_close": ([("saw_idle", 0, 0)], 12, 215, 3.0, (-2.2, 0.0, 4.2)),
    "saw_close_fa": ([("saw_idle_fa", 0, 0)], 12, 215, 3.0, (-2.2, 0.0, 4.2)),
    "saw_close2": ([("saw_idle", 0, 0)], 14, 290, 3.0, (-2.2, 0.0, 4.2)),
    "saw_idle_f": ([("saw_idle_f", 0, 0)], 8, 150, None, None),
    "ankle_peg": ([("ankle_peg", 0, 0)], 12, 160, 2.4, (0.9, -0.3, 0.9)),
    "ankle_mech": ([("ankle_mech", 0, 0)], 12, 160, 2.4, (0.9, -0.3, 0.9)),
    "ankle_med": ([("ankle_med", 0, 0)], 12, 160, 2.4, (0.9, -0.3, 0.9)),
    "iso_ankle_peg": ([("ankle_peg", 0, 0)], 38, 200, 2.6, (0.9, -0.3, 0.9)),
    "iso_ankle_mech": ([("ankle_mech", 0, 0)], 38, 200, 2.6, (0.9, -0.3, 0.9)),
    "iso_calf_peg": ([("calf_peg", 0, 0)], 38, 200, 2.6, (0.9, -0.3, 0.9)),
    "iso_calf_mech": ([("calf_mech", 0, 0)], 38, 200, 2.6, (0.9, -0.3, 0.9)),
}
for _n in ("stump_hand", "stump_fa", "stump_ua", "stump_fa_mech", "stump_ua_f"):
    JOBS[_n] = ([(_n, 0, 0)], 10, 205, 3.2, (-2.0, 0.0, 6.6))
    JOBS[_n + "_back"] = ([(_n, 0, 0)], 10, 320, 3.2, (-2.0, 0.0, 6.6))
for _n in ("hand_normalArmWrist", "hand_normalArm", "hand_medicalArmWrist", "hand_medicalArm"):
    JOBS[_n] = ([(_n, 0, 0)], 10, 215, 2.2, (-2.3, 0.2, 4.2))
for _t in ("pegArm", "hookArm", "normalArm", "medicalArm", "chainsawArm"):
    JOBS["upper_" + _t] = ([("upper_" + _t, 0, 0)], 10, 210, None, None)
    JOBS["upperatk_" + _t] = ([("upperatk_" + _t, 0, 0)], 12, 215, None, None)
CULL = {"stump_hand", "stump_fa", "stump_ua", "stump_fa_mech", "stump_ua_f",
        "stump_hand_back", "stump_fa_back", "stump_ua_back", "stump_fa_mech_back", "stump_ua_f_back",
        "ankle_peg", "ankle_mech", "ankle_med", "iso_ankle_peg", "iso_ankle_mech", "iso_calf_peg", "iso_calf_mech"}     # como el juego: sin caras traseras (se ve a través de un hueco)
ONLY = set(argv[3].split(",")) if len(argv) > 3 else None     # p. ej. saw_walk,saw_close
for name, (parts, elev, azim, zoom, focus) in JOBS.items():
    if ONLY and name not in ONLY: continue
    clear(); objs = []
    KEEP_WINDING = name in CULL
    for js, ox, rz in parts:
        for i, entry in enumerate(json.load(open(os.path.join(SRC, js + ".json")))):
            objs.append(add_mesh(entry, "%s_%d" % (js, i), (ox, 0, 0), rz))
    if name in CULL:
        for ob in objs:
            for m in ob.data.materials: m.use_backface_culling = True
    render(name, objs, elev, azim, zoom=zoom, focus=focus)
print("RENDER DONE")
