"""Mesa del banco de prótesis (2026-10-17, "haz la mesa propia fabricable, con modelo 3D para que se vea bien con el mod de
viewpoint"). Construye el modelo en Blender (metros, Z arriba, frente hacia +Y = Facing N, como los modelos de spriteModels
del juego), lo exporta a models_X/Furniture/TOCWorkbench.glb y renderiza los sprites isométricos de las 4 orientaciones
(128x256 por tile, como los tiles 2x del juego) más el icono y una vista de presentación.
Uso: blender -b -P make_workbench_model.py -- <media> <carpeta_salida_renders>"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
MEDIA, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
TEX = os.path.join(MEDIA, "textures", "Furniture", "TOCWorkbench.png")
CELLS = ["wood", "wooddark", "pegboard", "steel", "iron", "red", "yellow", "rubber",
         "bulb", "brass", "blueprint", "cyberwhite", "cybergrey", "cable", "mat", "leather"]

scene = bpy.context.scene
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
PARTS = []

def add(name, bm, cell):
    """Malla terminada -> objeto con las UV metidas en la celda del atlas (proyección por la normal dominante)."""
    uv = bm.loops.layers.uv.new("UVMap")
    ci = CELLS.index(cell); r, c = divmod(ci, 4)
    u0, v0 = c / 4 + 0.008, 1 - (r + 1) / 4 + 0.008; du = dv = 1 / 4 - 0.016
    pts = [v.co for v in bm.verts]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ext = Vector((max(1e-4, mx.x - mn.x), max(1e-4, mx.y - mn.y), max(1e-4, mx.z - mn.z)))
    for f in bm.faces:
        n = f.normal; a = max(range(3), key=lambda i: abs(n[i]))
        i0, i1 = [(1, 2), (0, 2), (0, 1)][a]
        for l in f.loops:
            p = l.vert.co
            s = (p[i0] - mn[i0]) / ext[i0]; t = (p[i1] - mn[i1]) / ext[i1]
            l[uv].uv = (u0 + du * s, v0 + dv * t)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); PARTS.append(ob)
    return ob

def box(name, c, size, cell, rot=None, bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect="EDGES")
    if rot: bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector(), matrix=rot)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(c))
    return add(name, bm, cell)

def cyl(name, p0, p1, r0, r1, cell, segs=16):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector(), matrix=q.to_matrix())
    bmesh.ops.translate(bm, verts=bm.verts, vec=(p0 + p1) / 2)
    return add(name, bm, cell)

def sphere(name, c, r, cell, segs=10):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(c)); return add(name, bm, cell)

def torus(name, c, R, r, cell, axis="y"):
    bm = bmesh.new(); n, m = 16, 6
    vs = []
    for i in range(n):
        a = 2 * math.pi * i / n
        for j in range(m):
            b = 2 * math.pi * j / m
            x, z, y = (R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)
            vs.append(bm.verts.new((x, y, z) if axis == "y" else (x, z, y)))
    for i in range(n):
        for j in range(m):
            a_ = vs[i * m + j]; b_ = vs[((i + 1) % n) * m + j]; c_ = vs[((i + 1) % n) * m + (j + 1) % m]; d_ = vs[i * m + (j + 1) % m]
            bm.faces.new((a_, b_, c_, d_))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(c)); return add(name, bm, cell)

# ---- mesa: frente hacia +Y
W_, D_, H_ = 0.94, 0.62, 0.84
box("top", (0, 0, H_ - 0.025), (W_, D_, 0.05), "wood", bevel=0.006)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("leg", (sx * (W_ / 2 - 0.05), sy * (D_ / 2 - 0.05), (H_ - 0.05) / 2), (0.06, 0.06, H_ - 0.05), "wooddark")
    box("stretcher", (sx * (W_ / 2 - 0.05), 0, 0.14), (0.04, D_ - 0.12, 0.04), "wooddark")
box("stretcherB", (0, -(D_ / 2 - 0.05), 0.14), (W_ - 0.12, 0.04, 0.04), "wooddark")
box("shelf", (0, -0.02, 0.17), (W_ - 0.14, D_ - 0.16, 0.025), "wooddark")
# cajonera a la derecha
box("drawers", (0.25, 0.01, 0.55), (0.34, D_ - 0.1, 0.46), "wooddark", bevel=0.004)
for k in range(3):
    z = 0.39 + k * 0.15
    box("drawerfront", (0.25, D_ / 2 - 0.035, z), (0.31, 0.012, 0.13), "wood", bevel=0.003)
    box("handle", (0.25, D_ / 2 - 0.022, z + 0.03), (0.09, 0.016, 0.014), "steel", bevel=0.003)
# tablero perforado detrás
box("pegboard", (0, -(D_ / 2 - 0.03), H_ + 0.38), (W_ - 0.04, 0.025, 0.72), "pegboard")
for sx in (-1, 1):
    box("post", (sx * (W_ / 2 - 0.03), -(D_ / 2 - 0.03), H_ + 0.38), (0.05, 0.05, 0.76), "wooddark")
box("peg_shelf", (0, -(D_ / 2 - 0.09), H_ + 0.56), (W_ - 0.1, 0.12, 0.02), "wooddark")
yb = -(D_ / 2 - 0.05)
# herramientas colgadas
box("wrench", (-0.36, yb + 0.005, H_ + 0.42), (0.022, 0.008, 0.2), "steel", bevel=0.002)
cyl("wrenchhead", (-0.36, yb, H_ + 0.53), (-0.36, yb + 0.012, H_ + 0.53), 0.026, 0.026, "steel")
box("hammerhandle", (-0.26, yb + 0.012, H_ + 0.36), (0.022, 0.018, 0.24), "red", bevel=0.004)
box("hammerhead", (-0.26, yb + 0.018, H_ + 0.49), (0.11, 0.03, 0.035), "iron", bevel=0.004)
for k, x in enumerate((-0.16, -0.12, -0.08)):
    cyl("screwdriver", (x, yb + 0.015, H_ + 0.33), (x, yb + 0.015, H_ + 0.42), 0.012, 0.012, "red" if k != 1 else "yellow")
    cyl("screwshaft", (x, yb + 0.015, H_ + 0.25), (x, yb + 0.015, H_ + 0.33), 0.004, 0.004, "steel")
torus("cablecoil", (0.05, yb + 0.02, H_ + 0.38), 0.07, 0.012, "cable")
torus("cablecoil2", (0.05, yb + 0.03, H_ + 0.38), 0.05, 0.01, "rubber")
# mano mecánica colgada en un gancho y una mano cyber en la balda
box("hook", (0.25, yb + 0.03, H_ + 0.47), (0.01, 0.05, 0.01), "steel")
box("mechpalm", (0.25, yb + 0.05, H_ + 0.36), (0.075, 0.03, 0.09), "steel", bevel=0.01)
for k in range(4):
    box("mechfinger", (0.22 + k * 0.022, yb + 0.05, H_ + 0.27), (0.016, 0.02, 0.08), "steel", bevel=0.004)
cyl("mechwrist", (0.25, yb + 0.05, H_ + 0.41), (0.25, yb + 0.05, H_ + 0.45), 0.025, 0.025, "iron")
box("cyberpalm", (0.33, -(D_ / 2 - 0.1), H_ + 0.6), (0.07, 0.08, 0.03), "cyberwhite", bevel=0.006)
for k in range(4):
    box("cyberfinger", (0.31 + k * 0.016, -(D_ / 2 - 0.1) + 0.07, H_ + 0.6), (0.011, 0.06, 0.016), "cybergrey" if k % 2 else "cyberwhite", bevel=0.003)
for k, x in enumerate((-0.35, -0.3, -0.25, -0.2)):
    cyl("jar", (x, -(D_ / 2 - 0.09), H_ + 0.57), (x, -(D_ / 2 - 0.09), H_ + 0.64), 0.022, 0.022, "brass" if k % 2 else "steel")
# sobre la mesa: alfombrilla, tornillo de banco con un antebrazo cyber, flexo, plano, piezas
box("mat", (-0.08, 0.07, H_ + 0.003), (0.46, 0.34, 0.006), "mat")
box("blueprint", (0.26, 0.12, H_ + 0.004), (0.26, 0.2, 0.004), "blueprint", rot=Matrix.Rotation(math.radians(-8), 3, "Z"))
vx, vy = -0.3, 0.17
box("visebase", (vx, vy, H_ + 0.02), (0.12, 0.1, 0.03), "iron", bevel=0.005)
box("visebody", (vx, vy, H_ + 0.08), (0.1, 0.07, 0.08), "red", bevel=0.008)
box("visejawA", (vx - 0.035, vy, H_ + 0.14), (0.03, 0.08, 0.05), "iron", bevel=0.004)
box("visejawB", (vx + 0.035, vy, H_ + 0.14), (0.03, 0.08, 0.05), "iron", bevel=0.004)
cyl("visescrew", (vx + 0.05, vy, H_ + 0.08), (vx + 0.16, vy, H_ + 0.08), 0.01, 0.01, "steel")
cyl("visebar", (vx + 0.16, vy - 0.05, H_ + 0.08), (vx + 0.16, vy + 0.05, H_ + 0.08), 0.006, 0.006, "steel")
# antebrazo cyber sujeto en el tornillo, en diagonal hacia la mesa
a0, a1 = Vector((vx, vy - 0.02, H_ + 0.15)), Vector((vx + 0.3, vy - 0.12, H_ + 0.06))
cyl("armcore", a0, a1, 0.03, 0.024, "cybergrey", segs=12)
for k in range(3):
    f0, f1 = k / 3 + 0.02, (k + 1) / 3 - 0.02
    p, q = a0 + (a1 - a0) * f0, a0 + (a1 - a0) * f1
    cyl("armplate", p, q, 0.035 - 0.003 * k, 0.034 - 0.003 * k, "cyberwhite" if k != 1 else "cybergrey", segs=8)
cyl("armsocket", a0 - (a1 - a0) * 0.18, a0 + (a1 - a0) * 0.02, 0.04, 0.036, "rubber", segs=14)
cyl("armmount", a1, a1 + (a1 - a0).normalized() * 0.02, 0.02, 0.02, "brass")
for k in range(3):
    m0 = a0 + (a1 - a0) * (0.15 + k * 0.3)
    torus("armwire", m0, 0.0, 0.0, "cable") if False else None
# flexo
lx, ly = 0.36, -0.12
cyl("lampbase", (lx, ly, H_), (lx, ly, H_ + 0.02), 0.06, 0.055, "iron")
j1, j2 = Vector((lx, ly, H_ + 0.02)), Vector((lx - 0.05, ly + 0.08, H_ + 0.3))
j3 = Vector((lx - 0.18, ly + 0.16, H_ + 0.36))
cyl("lamparm1", j1, j2, 0.008, 0.008, "yellow"); cyl("lamparm2", j2, j3, 0.008, 0.008, "yellow")
sphere("lampjoint", j2, 0.014, "iron")
cyl("lampshade", j3, j3 + Vector((-0.02, 0.05, -0.08)), 0.03, 0.065, "yellow", segs=16)
sphere("lampbulb", j3 + Vector((-0.016, 0.04, -0.066)), 0.025, "bulb")
# piezas sueltas en la alfombrilla
for k, (x, y) in enumerate(((-0.12, 0.0), (-0.05, 0.12), (0.02, 0.03), (-0.18, 0.08), (0.06, 0.16))):
    cyl("gear", (x, y, H_ + 0.006), (x, y, H_ + 0.016), 0.022 + 0.006 * (k % 2), 0.022 + 0.006 * (k % 2), "brass" if k % 2 else "steel", segs=10)
for k in range(6):
    cyl("screw", (-0.02 + k * 0.025, -0.04, H_ + 0.006), (-0.02 + k * 0.025, -0.04, H_ + 0.02), 0.004, 0.004, "steel", segs=6)
cyl("solderiron", (0.08, -0.06, H_ + 0.02), (0.22, 0.0, H_ + 0.02), 0.01, 0.006, "red", segs=8)
box("solderstand", (0.22, -0.08, H_ + 0.03), (0.06, 0.05, 0.05), "iron", bevel=0.004)
box("toolbox", (-0.22, -0.18, H_ + 0.07), (0.26, 0.14, 0.14), "red", bevel=0.01)
box("toolboxlid", (-0.22, -0.18, H_ + 0.145), (0.26, 0.14, 0.012), "iron", bevel=0.003)
box("toolboxhandle", (-0.22, -0.18, H_ + 0.17), (0.12, 0.012, 0.012), "rubber")

# ---- unir en una malla, material con el atlas
bpy.ops.object.select_all(action="DESELECT")
for ob in PARTS: ob.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
bench = bpy.context.view_layer.objects.active; bench.name = "TOCWorkbench"
mat = bpy.data.materials.new("TOCWorkbench"); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(TEX); tn.interpolation = "Closest"
nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.7
bench.data.materials.append(mat)
for p in bench.data.polygons: p.use_smooth = False

# ---- exportar
glb = os.path.join(MEDIA, "models_X", "Furniture", "TOCWorkbench.glb")
os.makedirs(os.path.dirname(glb), exist_ok=True)
bpy.ops.object.select_all(action="DESELECT"); bench.select_set(True)
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                          export_materials="EXPORT", export_image_format="NONE")
print("GLB", glb)
# modelo para el mod Viewpoint (vista 3D / primera persona): no usa spriteModels.txt sino sus propios packs,
# media/viewpoint/<pack>.properties + OBJ en unidades de casilla, Z arriba, origen en el centro de la casilla
# (formato copiado del pack de Bus Stop Fast Travel). make_workbench_tiles.py escribe el .properties.
vp = os.path.join(MEDIA, "viewpoint", "tocplus_bench")
os.makedirs(vp, exist_ok=True)
bpy.ops.wm.obj_export(filepath=os.path.join(vp, "model.obj"), export_selected_objects=True, forward_axis="Y", up_axis="Z",
                      export_materials=False, export_uv=True, export_normals=True, apply_modifiers=True)
src = open(os.path.join(vp, "model.obj"), encoding="utf-8").read()
NL = chr(10)
open(os.path.join(vp, "model.obj"), "w", encoding="utf-8", newline=NL).write(
    NL.join(["# TOC+ prosthesis workbench (Z up, tile units)", "mtllib model.mtl", "usemtl atlas", ""]) + src)
open(os.path.join(vp, "model.mtl"), "w", encoding="utf-8", newline=NL).write(NL.join(["newmtl atlas", "Kd 1 1 1", "d 1", "map_Kd texture.png", ""]))
import shutil; shutil.copy(TEX, os.path.join(vp, "texture.png"))
print("OBJ", vp)

# ---- render: sprites isométricos (como los tiles 2x: 128x256, rombo del suelo de 128x64 abajo)
try: scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    try: scene.render.engine = "BLENDER_EEVEE"
    except TypeError: pass
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"
try: scene.eevee.taa_render_samples = 64
except Exception: pass
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.55, 0.55, 0.6, 1); bg.inputs[1].default_value = 0.6
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam

def iso_camera(res=(128, 256)):
    scene.render.resolution_x, scene.render.resolution_y = res; scene.render.resolution_percentage = 100
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 2 * math.sqrt(2)
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    d = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
    cam.location = Vector((0, 0, 0)) + d * 10
    cam.data.shift_x = 0.0; cam.data.shift_y = 96 / 256

FACINGS = [("S", 180), ("E", -90), ("N", 0), ("W", 90)]      # orden de los tiles (xy 0..3), como appliances_radio_01
iso_camera()
for i, (f, yaw) in enumerate(FACINGS):
    bench.rotation_euler = (0, 0, math.radians(yaw))
    scene.render.filepath = os.path.join(OUT, "tile_%d_%s.png" % (i, f))
    bpy.ops.render.render(write_still=True); print("tile", f)
# icono y presentación
bench.rotation_euler = (0, 0, math.radians(180))
scene.render.resolution_x = scene.render.resolution_y = 256
cam.data.type = "PERSP"; cam.data.lens = 50; cam.data.shift_x = cam.data.shift_y = 0
t = Vector((0, 0, 0.75))
for name, az, el, dist in (("icon", 35, 25, 3.6), ("show", 25, 18, 3.2)):
    a, e = math.radians(az), math.radians(el)
    cam.location = t + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    if name == "show": scene.render.resolution_x, scene.render.resolution_y = 900, 900
    scene.render.filepath = os.path.join(OUT, "%s.png" % name); bpy.ops.render.render(write_still=True)
print("WORKBENCH DONE")
