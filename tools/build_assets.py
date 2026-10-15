"""Genera los recursos nuevos de TOC+ sin Blender:
- muñones de pierna (12 modelos .X con pesos) + texturas (32 por pieza, mismo orden que TOC);
- prótesis (pata de palo, pierna mecánica, pierna médica, brazo de palo) rígidas sobre un hueso;
- torniquete de pierna; muleta y sierra de hueso (armas estáticas); miembros cercenados (modelos de suelo);
- iconos 32x32, iconos de rasgos 18x18 y superposiciones del panel de salud 123x302.

Uso:  python build_assets.py  [ruta_del_mod]
"""
import os, sys, math, random
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
import pzx
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PZ = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media"
MOD = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
TOC_UP = r"C:\Users\nexco\CODING PARCHEO\TOCPlus\upstream_2.4.0\42\media"

BODY = {"Male": os.path.join(PZ, r"models_X\Skinned\MaleBody.X"), "Female": os.path.join(PZ, r"models_X\Skinned\FemaleBody.X")}
TEMPLATE = {"Male": os.path.join(PZ, r"models_X\Skinned\Clothes\Bob_Trousers.x"), "Female": os.path.join(PZ, r"models_X\Skinned\Clothes\Kate_Trousers.x")}
for k, v in list(TEMPLATE.items()):
    if not os.path.exists(v):
        alt = os.path.join(PZ, r"models_X\Skinned\Clothes\Kate_Trousers.x")
        TEMPLATE[k] = alt if os.path.exists(alt) else os.path.join(PZ, r"models_X\Skinned\Clothes\Bob_Trousers.x")

PATCH = (116, 200, 24, 24)          # zona libre de la textura del cuerpo donde va la herida del muñón
CAP_C = ((PATCH[0] + 12) / 256.0, (PATCH[1] + 12) / 256.0)
CAP_R = 10.0 / 256.0
# 3.1.0: la herida de los muñones que se visten va DENTRO de la mano / el pie de su lado. El juego aplica a cada prenda
# las máscaras de las que van encima, y la zona libre de PATCH cae en las máscaras de pierna (y un 19 % en ninguna): con
# cualquier chaqueta encima se perdía un 19 % del disco, y con las dos piernas amputadas la tapa izquierda perdía el 69 %
# (el muñón derecho va encima). La mano / el pie del mismo lado sólo se ocultan cuando algo tapa ese miembro entero.
# Centros (en texeles) en zonas que ningún muñón usa, con sitio para el disco de radio 10 (ver make_arm_stumps.seam_alpha).
# PATCH sigue pintándose: lo usan los miembros cercenados del suelo (modelos estáticos, sin máscaras).
CAPS = {("Hand", "L"): (230, 140), ("Hand", "R"): (17, 141), ("Foot", "L"): (171, 26), ("Foot", "R"): (85, 27)}

def cap_for(limb, side):
    cx, cy = CAPS[(limb, side)]
    return (cx / 256.0, cy / 256.0), CAP_R

def wound_patches():
    return [PATCH] + [(cx - 12, cy - 12, 24, 24) for cx, cy in CAPS.values()]

def out(*p):
    path = os.path.join(MOD, *p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


class V3:
    __slots__ = ("x", "y", "z")
    def __init__(self, x, y, z): self.x, self.y, self.z = float(x), float(y), float(z)
    def arr(self): return np.array([self.x, self.y, self.z])

def v3(a): return V3(a[0], a[1], a[2])

# ------------------------------------------------------------------ cuerpo

def find_mesh(node):
    for c in node.children:
        if c.type == "Mesh": return c
        r = find_mesh(c)
        if r: return r

def load_body(sex):
    root = pzx.parse(BODY[sex])
    m = pzx.read_mesh(find_mesh(root))
    verts = np.array(m["verts"], float)
    faces = [tuple(f) for f in m["faces"]]
    uvs = np.array(m["uvs"], float)
    weights = [dict() for _ in verts]
    offsets = {}
    for sk in m["skin"]:
        offsets[sk["bone"]] = list(sk["offset"])
        for vi, w in zip(sk["indices"], sk["weights"]):
            if w > 1e-4: weights[vi][sk["bone"]] = weights[vi].get(sk["bone"], 0) + w
    return {"verts": verts, "faces": faces, "uvs": uvs, "weights": weights, "offsets": offsets, "sex": sex}

def bone_frame(offsets, bone):
    off = np.array(offsets[bone]).reshape(4, 4)
    bind = np.linalg.inv(off)
    return bind[3, :3], bind[0, :3], bind[1, :3], bind[2, :3]     # origen, X, Y, Z (filas = ejes en espacio cuerpo)

def smooth_normals(verts, faces):
    n = np.zeros((len(verts), 3))
    for a, b, c in faces:
        fn = np.cross(verts[b] - verts[a], verts[c] - verts[a])
        n[a] += fn; n[b] += fn; n[c] += fn
    l = np.linalg.norm(n, axis=1); l[l == 0] = 1
    return n / l[:, None]

# ------------------------------------------------------------------ recorte del cuerpo

_hidden_alpha = {}
def hidden_alpha(sex="Male"):
    """Alfa de la textura del cuerpo: donde es 0 el juego no dibuja la cara (membrana entre las piernas)."""
    if sex not in _hidden_alpha:
        im = Image.open(os.path.join(PZ, "textures", "Body", ("MaleBody01" if sex == "Male" else "FemaleBody01") + ".png")).convert("RGBA")
        _hidden_alpha[sex] = np.array(im.split()[3])
    return _hidden_alpha[sex]

def face_is_hidden(body, f):
    """El juego dibuja todas las caras; la membrana entre las piernas es invisible sólo porque su zona
    de textura tiene alfa 0. No usar los pesos Bip01_Dress*: en el cuerpo femenino hay caras reales
    (entrepierna / cara interna del muslo) pesadas a esos huesos que sí se ven."""
    a = hidden_alpha(body.get("sex", "Male"))
    UV = body["uvs"]
    pts = [UV[vi] for vi in f] + [UV[list(f)].mean(0)]
    for u, v in pts:
        px, py = int(np.clip(u * 255, 0, 255)), int(np.clip(v * 255, 0, 255))
        if a[py, px] >= 8: return False
    return True

def limb_faces(body, bones):
    """Caras con algún vértice pesado a los huesos dados, sin las caras que el juego no dibuja
    (membrana entre las piernas: pesos Bip01_Dress* o zona transparente de la textura)."""
    keep = []
    for f in body["faces"]:
        if face_is_hidden(body, f): continue
        ws = [body["weights"][vi] for vi in f]
        if any(any(b in w for b in bones) for w in ws):
            keep.append(f)
    return keep

def clip_mesh(body, faces, cut_y, keep_above):
    """Recorta las caras por el plano y=cut_y. Devuelve verts, uvs, weights, faces nuevos y el lazo del borde."""
    V, UV, W = body["verts"], body["uvs"], body["weights"]
    nv, nuv, nw, nf = [], [], [], []
    index = {}
    edge_pts = []            # puntos sobre el plano (para la tapa)
    def side(y): return (y - cut_y) if keep_above else (cut_y - y)
    def add_orig(vi):
        key = ("o", vi)
        if key not in index:
            index[key] = len(nv); nv.append(V[vi].copy()); nuv.append(UV[vi].copy()); nw.append(dict(W[vi]))
        return index[key]
    def add_cut(a, b):
        key = ("c", min(a, b), max(a, b))
        if key not in index:
            ya, yb = V[a][1], V[b][1]
            t = (cut_y - ya) / (yb - ya)
            p = V[a] + (V[b] - V[a]) * t
            uv = UV[a] + (UV[b] - UV[a]) * t
            w = {}
            for bone in set(W[a]) | set(W[b]):
                w[bone] = W[a].get(bone, 0) * (1 - t) + W[b].get(bone, 0) * t
            index[key] = len(nv); nv.append(p); nuv.append(uv); nw.append(w)
        return index[key]
    for f in faces:
        poly = []
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            sa, sb = side(V[a][1]), side(V[b][1])
            if sa >= 0: poly.append(add_orig(a))
            if (sa >= 0) != (sb >= 0): poly.append(add_cut(a, b))
        if len(poly) >= 3:
            for k in range(1, len(poly) - 1):
                nf.append((poly[0], poly[k], poly[k + 1]))
        if len(poly) >= 3:
            cuts = [p for p in poly if p >= 0 and abs(nv[p][1] - cut_y) < 1e-6]
            if len(cuts) == 2: edge_pts.append(tuple(cuts))
    return np.array(nv), np.array(nuv), nw, nf, edge_pts

def add_cap(nv, nuv, nw, nf, edge_pts, normal_down, cap=None):
    """Tapa en abanico sobre el borde del corte (usa el centroide del lazo). cap = (centro UV, radio UV) de la herida."""
    if not edge_pts: return nv, nuv, nw, nf
    cap_c, cap_r = cap or (CAP_C, CAP_R)
    nv = list(map(np.array, nv)); nuv = list(map(np.array, nuv)); nf = list(nf)
    pts = sorted({p for e in edge_pts for p in e})
    center = np.mean([nv[p] for p in pts], axis=0)
    # radio máximo para la UV
    rmax = max(np.hypot(nv[p][0] - center[0], nv[p][2] - center[2]) for p in pts) or 1e-3
    # vértices nuevos para la tapa (UV en la zona de la herida; normal propia)
    cap_idx = {}
    for p in pts:
        dx, dz = (nv[p][0] - center[0]) / rmax, (nv[p][2] - center[2]) / rmax
        cap_idx[p] = len(nv)
        nv.append(nv[p].copy()); nuv.append(np.array([cap_c[0] + dx * cap_r, cap_c[1] + dz * cap_r])); nw.append(dict(nw[p]))
    ci = len(nv)
    wsum = {}
    for p in pts:
        for b, w in nw[p].items(): wsum[b] = wsum.get(b, 0) + w
    tot = sum(wsum.values()) or 1
    nv.append(center + np.array([0, -0.004 if normal_down else 0.004, 0])); nuv.append(np.array(cap_c)); nw.append({b: w / tot for b, w in wsum.items()})
    for a, b in edge_pts:
        # orientar: la normal de la tapa debe mirar hacia abajo (normal_down) = -Y
        tri = (ci, cap_idx[a], cap_idx[b])
        n = np.cross(nv[tri[1]] - nv[tri[0]], nv[tri[2]] - nv[tri[0]])
        if (n[1] > 0) == normal_down: tri = (ci, cap_idx[b], cap_idx[a])
        nf.append(tri)
    return np.array(nv), np.array(nuv), nw, nf

def write_skinned(path, name, texture, sex, body, verts, uvs, weights, faces):
    normals = smooth_normals(verts, faces)
    wl = []
    for w in weights:
        ws = sorted(w.items(), key=lambda t: -t[1])[:4]
        tot = sum(x for _, x in ws) or 1
        wl.append([(b, x / tot) for b, x in ws])
    return pzx.write_skinned_x(TEMPLATE[sex], path, name, texture,
                               [v3(v) for v in verts], [v3(n) for n in normals], [(float(u), float(v)) for u, v in uvs],
                               [tuple(int(i) for i in f) for f in faces], wl, body["offsets"])

LEG_BONES = {"L": ["Bip01_L_Thigh", "Bip01_L_Calf", "Bip01_L_Foot", "Bip01_L_Toe0"], "R": ["Bip01_R_Thigh", "Bip01_R_Calf", "Bip01_R_Foot", "Bip01_R_Toe0"]}
ARM_BONES = {"L": ["Bip01_L_UpperArm", "Bip01_L_Forearm", "Bip01_L_Hand", "Bip01_L_Finger0", "Bip01_L_Finger1"], "R": ["Bip01_R_UpperArm", "Bip01_R_Forearm", "Bip01_R_Hand", "Bip01_R_Finger0", "Bip01_R_Finger1"]}
LEG_CUTS = {"Foot": 0.075, "LowerLeg": 0.25, "UpperLeg": 0.40}
SIDE_NAME = {"L": "Left", "R": "Right"}

def build_leg_stumps():
    stats = {}
    for sex in ("Male", "Female"):
        body = load_body(sex)
        for side in ("L", "R"):
            for part, cut in LEG_CUTS.items():
                bones = LEG_BONES[side] if part != "Foot" else [LEG_BONES[side][2], LEG_BONES[side][3]]
                faces = limb_faces(body, bones)
                nv, nuv, nw, nf, edge = clip_mesh(body, faces, cut, keep_above=True)
                nv, nuv, nw, nf = add_cap(nv, nuv, nw, nf, edge, normal_down=True, cap=cap_for("Foot", side))
                name = "Amputation_%s_%s_%s" % (SIDE_NAME[side], part, sex)
                tex = "Amputations/Human/%s/skin01_b" % part
                r = write_skinned(out("models_X", "Amputation", name + ".X"), name, tex, sex, body, nv, nuv, nw, nf)
                stats[name] = r
    return stats

# ------------------------------------------------------------------ texturas de muñón

def skin_sample(img, part):
    # color medio de la zona de muslo/pantorrilla (UV v 0.61..0.79 u 0.2..0.8 -> píxeles)
    box = (60, 160, 200, 200)
    reg = img.crop(box).convert("RGB").resize((1, 1), Image.BOX)
    return reg.getpixel((0, 0))

def paint_disc(img, kind, seed=0):
    """La herida en todas las zonas de tapa (PATCH y las de mano / pie de cada lado), igual en todas."""
    for box in wound_patches(): paint_disc_at(img, kind, seed, box)
    return img

def paint_disc_at(img, kind, seed, box):
    x, y, w, h = box
    rng = random.Random(seed)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = x + w / 2, y + h / 2
    if kind == "blood":
        d.ellipse((x + 1, y + 1, x + w - 2, y + h - 2), fill=(120, 14, 10, 255))
        d.ellipse((x + 4, y + 4, x + w - 5, y + h - 5), fill=(160, 22, 16, 255))
        for _ in range(26):
            px, py = rng.uniform(x + 3, x + w - 4), rng.uniform(y + 3, y + h - 4)
            d.ellipse((px, py, px + 2, py + 2), fill=(rng.randint(70, 110), rng.randint(5, 15), rng.randint(5, 12), 255))
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(230, 220, 200, 255))      # hueso
        d.ellipse((cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5), fill=(150, 60, 50, 255))
    elif kind == "scar":
        base = skin_sample(img, None)
        d.ellipse((x + 1, y + 1, x + w - 2, y + h - 2), fill=(max(0, base[0] - 10), max(0, base[1] - 25), max(0, base[2] - 25), 255))
        d.ellipse((x + 5, y + 5, x + w - 6, y + h - 6), fill=(min(255, base[0] + 5), max(0, base[1] - 35), max(0, base[2] - 30), 255))
        d.line((x + 6, cy, x + w - 7, cy), fill=(max(0, base[0] - 40), max(0, base[1] - 60), max(0, base[2] - 55), 255), width=2)
        for i in range(5):
            px = x + 7 + i * 3
            d.line((px, cy - 3, px, cy + 3), fill=(max(0, base[0] - 50), max(0, base[1] - 70), max(0, base[2] - 60), 255), width=1)
    elif kind == "zombie":
        d.ellipse((x + 1, y + 1, x + w - 2, y + h - 2), fill=(70, 50, 30, 255))
        d.ellipse((x + 4, y + 4, x + w - 5, y + h - 5), fill=(95, 40, 30, 255))
        for _ in range(20):
            px, py = rng.uniform(x + 3, x + w - 4), rng.uniform(y + 3, y + h - 4)
            d.ellipse((px, py, px + 2, py + 2), fill=(rng.randint(40, 80), rng.randint(50, 70), rng.randint(20, 35), 255))
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(190, 180, 150, 255))
    return img

def build_stump_textures():
    bodydir = os.path.join(PZ, "textures", "Body")
    for part in LEG_CUTS:
        for i in range(1, 6):
            for hairy in ("", "a"):
                src = Image.open(os.path.join(bodydir, "MaleBody%02d%s.png" % (i, hairy))).convert("RGBA")
                suffix = "_hairy" if hairy else ""
                paint_disc(src.copy(), "blood", i).save(out("textures", "Amputations", "Human", part, "skin%02d%s_b.png" % (i, suffix)))
                paint_disc(src.copy(), "scar", i).save(out("textures", "Amputations", "Human", part, "skin%02d%s_c.png" % (i, suffix)))
        for i in range(1, 6):
            src = Image.open(os.path.join(bodydir, "FemaleBody%02d.png" % i)).convert("RGBA")
            paint_disc(src.copy(), "blood", 50 + i).save(out("textures", "Amputations", "Human", part, "skinF%02d_b.png" % i))
            paint_disc(src.copy(), "scar", 50 + i).save(out("textures", "Amputations", "Human", part, "skinF%02d_c.png" % i))
        for z in range(1, 5):
            for lvl in range(1, 4):
                src = Image.open(os.path.join(bodydir, "M_ZedBody%02d_level%d.png" % (z, lvl))).convert("RGBA")
                paint_disc(src, "zombie", z * 10 + lvl).save(out("textures", "Amputations", "Zombie", part, "z_skin%02d_l%d.png" % (z, lvl)))
    # las de LowerLeg también las usan los muñones de brazo: alfa en la costura del hombro (make_arm_stumps.seam_alpha)
    import make_arm_stumps
    make_arm_stumps.seam_alpha()

# ------------------------------------------------------------------ geometría procedural

class MeshB:
    def __init__(self): self.v, self.n, self.uv, self.f, self.w = [], [], [], [], []
    def add_tri(self, a, b, c): self.f.append((a, b, c))
    def tube(self, path_pts, radii, axes, segs=14, bone=None, uv_u=(0.0, 1.0), uv_v=(0.0, 1.0), close_start=False, close_end=False):
        """Tubo a lo largo de puntos (centro) con radio (rx, rz) por anillo. axes=(ax, az) vectores del plano del anillo."""
        ax, az = axes
        rings = []
        for k, (p, r) in enumerate(zip(path_pts, radii)):
            ring = []
            for s in range(segs):
                t = 2 * math.pi * s / segs
                q = p + ax * (r[0] * math.cos(t)) + az * (r[1] * math.sin(t))
                nrm = ax * math.cos(t) + az * math.sin(t)
                ring.append(len(self.v)); self.v.append(q); self.n.append(nrm / (np.linalg.norm(nrm) or 1))
                self.uv.append((uv_u[0] + (uv_u[1] - uv_u[0]) * s / segs, uv_v[0] + (uv_v[1] - uv_v[0]) * k / max(1, len(path_pts) - 1)))
                self.w.append(bone)
            rings.append(ring)
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            for s in range(segs):
                s2 = (s + 1) % segs
                self.add_tri(a[s], b[s], b[s2]); self.add_tri(a[s], b[s2], a[s2])
        first_face = len(self.f) - (len(rings) - 1) * segs * 2
        fwd_dir = np.array(path_pts[-1]) - np.array(path_pts[0])
        if np.linalg.norm(fwd_dir) < 1e-9: fwd_dir = np.cross(ax, az)
        fwd_dir = fwd_dir / (np.linalg.norm(fwd_dir) or 1)
        for closing, ring, p, flip in ((close_start, rings[0], path_pts[0], True), (close_end, rings[-1], path_pts[-1], False)):
            if closing:
                axis = -fwd_dir if flip else fwd_dir
                ci = len(self.v); self.v.append(np.array(p, float)); self.n.append(axis); self.uv.append(((uv_u[0] + uv_u[1]) / 2, (uv_v[0] + uv_v[1]) / 2)); self.w.append(bone)
                for s in range(segs):
                    s2 = (s + 1) % segs
                    self.add_tri(ci, ring[s], ring[s2])
        self.orient(first_face)
    def orient(self, first_face=0):
        """Da la vuelta a las caras (desde first_face) cuyo producto vectorial no apunta como la normal media de sus vértices."""
        for i in range(max(0, first_face), len(self.f)):
            a, b, c = self.f[i]
            fn = np.cross(self.v[b] - self.v[a], self.v[c] - self.v[a])
            ref = self.n[a] + self.n[b] + self.n[c]
            if np.dot(fn, ref) < 0: self.f[i] = (a, c, b)
    def box(self, center, size, bone=None, uv=(0.0, 0.0, 1.0, 1.0)):
        cx, cy, cz = center; sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        faces = [((1, 0, 0), ((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1))), ((-1, 0, 0), ((-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1))),
                 ((0, 1, 0), ((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1))), ((0, -1, 0), ((-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1))),
                 ((0, 0, 1), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))), ((0, 0, -1), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)))]
        u0, v0, u1, v1 = uv
        for nrm, corners in faces:
            base = len(self.v)
            for k, (a, b, c) in enumerate(corners):
                self.v.append(np.array([cx + a * sx, cy + b * sy, cz + c * sz])); self.n.append(np.array(nrm, float))
                self.uv.append((u0 if k in (0, 3) else u1, v0 if k in (0, 1) else v1)); self.w.append(bone)
            self.add_tri(base, base + 1, base + 2); self.add_tri(base, base + 2, base + 3)
    def mirror_x(self, bone_map):
        m = MeshB()
        m.v = [np.array([-p[0], p[1], p[2]]) for p in self.v]; m.n = [np.array([-p[0], p[1], p[2]]) for p in self.n]
        m.uv = list(self.uv); m.f = [(a, c, b) for a, b, c in self.f]; m.w = [bone_map.get(b, b) for b in self.w]
        return m
    def transformed(self, fn):
        m = MeshB(); m.v = [fn(p) for p in self.v]; m.n = list(self.n); m.uv = list(self.uv); m.f = list(self.f); m.w = list(self.w); return m

def write_rigid(path, name, texture, sex, body, mesh):
    weights = [[(b, 1.0)] for b in mesh.w]
    return pzx.write_skinned_x(TEMPLATE[sex], path, name, texture, [v3(v) for v in mesh.v], [v3(n) for n in mesh.n],
                               [(float(u), float(v)) for u, v in mesh.uv], mesh.f, weights, body["offsets"])

def write_static(path, name, texture, mesh):
    return pzx.write_static_x(path, name, texture, [v3(v) for v in mesh.v], [v3(n) for n in mesh.n], [(float(u), float(v)) for u, v in mesh.uv], mesh.f)

X, Y, Z = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])

_leg_cache = {}
def _leg_mesh(body, side):
    """Vértices y caras visibles de la pierna (muslo, pantorrilla, pie) de un lado."""
    key = (id(body), side)
    if key not in _leg_cache:
        V = body["verts"]; W = body["weights"]
        bones = ("Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side)
        faces = []
        for f in body["faces"]:
            if face_is_hidden(body, f): continue
            if any(any(bn in W[vi] for bn in bones) for vi in f):
                # sólo caras del lado correcto (la cadera comparte vértices)
                if (np.mean([V[vi][0] for vi in f]) > 0) == (side == "L"):
                    faces.append(f)
        _leg_cache[key] = (V, faces)
    return _leg_cache[key]

def _leg_points(body, side):
    V, faces = _leg_mesh(body, side)
    idx = sorted({vi for f in faces for vi in f})
    return np.array([V[i] for i in idx])

def plane_section(body, side, y):
    """Puntos de la intersección de la superficie de la pierna con el plano y."""
    V, faces = _leg_mesh(body, side)
    pts = []
    for f in faces:
        for k in range(3):
            a_, b_ = V[f[k]], V[f[(k + 1) % 3]]
            ya, yb = a_[1], b_[1]
            if (ya - y) * (yb - y) <= 0 and ya != yb:
                t = (y - ya) / (yb - ya)
                pts.append(a_ + (b_ - a_) * t)
    return np.array(pts) if pts else np.zeros((0, 3))

def leg_section(pts_unused, y, clearance=0.003, segs=28, window=0.03, smooth=1, body=None, side=None):
    """Anillo (segs puntos) que envuelve la sección real de la pierna a la altura y + holgura."""
    sl = plane_section(body, side, y)
    # además de la sección exacta, los vértices de la banda [y-band, y+band]: la superficie entre dos
    # secciones es lineal por triángulos y un vértice intermedio puede sobresalir de la interpolación
    P = _leg_points(body, side)
    band = P[np.abs(P[:, 1] - y) <= 0.016]
    if len(band): sl = np.vstack([sl, band]) if len(sl) else band
    if len(sl) < 4:
        sl = P[np.argsort(np.abs(P[:, 1] - y))[:10]]
    cx, cz = (sl[:, 0].min() + sl[:, 0].max()) / 2, (sl[:, 2].min() + sl[:, 2].max()) / 2
    ang = np.arctan2(sl[:, 2] - cz, sl[:, 0] - cx)
    dist = np.hypot(sl[:, 0] - cx, sl[:, 2] - cz)
    r = np.zeros(segs)
    for k in range(segs):
        t = -math.pi + 2 * math.pi * k / segs
        d = np.abs((ang - t + math.pi) % (2 * math.pi) - math.pi)
        sector = d <= 1.6 * math.pi / segs + 0.02
        if sector.any():
            r[k] = dist[sector].max()
        else:
            # sin puntos en el sector: interpolar entre los vecinos angulares más cercanos
            order = np.argsort(d)[:2]
            r[k] = dist[order].max()
    for _ in range(smooth):
        r = np.maximum(r, (np.roll(r, 1) + np.roll(r, -1)) / 2 * 0.98)
    r = r + clearance
    ring = [np.array([cx + r[k] * math.cos(-math.pi + 2 * math.pi * k / segs), y, cz + r[k] * math.sin(-math.pi + 2 * math.pi * k / segs)]) for k in range(segs)]
    return ring

def leg_profile(body, side, y, clearance=0.003, window=0.028):
    """Compatibilidad: centro y radios medios de la sección."""
    ring = leg_section(None, y, clearance, body=body, side=side)
    R = np.array(ring); c = R.mean(0)
    return np.array([c[0], y, c[2]]), (R[:, 0].max() - R[:, 0].min()) / 2, (R[:, 2].max() - R[:, 2].min()) / 2

def loft(m, rings, bone, uv_v=(0.0, 1.0), close_start=False, close_end=False, flip=False):
    """Une anillos consecutivos (misma cantidad de puntos) con triángulos; tapas en abanico opcionales."""
    segs = len(rings[0]); ids = []
    for k, ring in enumerate(rings):
        row = []
        for s_, q in enumerate(ring):
            row.append(len(m.v)); m.v.append(np.array(q)); m.n.append(np.array([0.0, 1.0, 0.0]))
            m.uv.append((s_ / segs, uv_v[0] + (uv_v[1] - uv_v[0]) * k / max(1, len(rings) - 1))); m.w.append(bone)
        ids.append(row)
    centers = [np.mean([m.v[i] for i in row], axis=0) for row in ids]
    first_face = len(m.f)
    refs = []            # dirección "hacia fuera" de referencia por cara nueva
    for k in range(len(rings) - 1):
        a_, b_ = ids[k], ids[k + 1]
        cmid = (centers[k] + centers[k + 1]) / 2
        for s_ in range(segs):
            s2 = (s_ + 1) % segs
            m.add_tri(a_[s_], b_[s_], b_[s2]); m.add_tri(a_[s_], b_[s2], a_[s2])
            refs.append(cmid); refs.append(cmid)
    for closing, row, first in ((close_start, ids[0], True), (close_end, ids[-1], False)):
        if closing:
            c = centers[0] if first else centers[-1]
            axis_dir = (centers[0] - centers[1]) if first else (centers[-1] - centers[-2])
            ci = len(m.v); m.v.append(c); m.n.append(np.array([0.0, 1.0, 0.0])); m.uv.append(((0.5), (uv_v[0] + uv_v[1]) / 2)); m.w.append(bone)
            for s_ in range(segs):
                s2 = (s_ + 1) % segs
                m.add_tri(ci, row[s_], row[s2]); refs.append(("cap", axis_dir))
    # orientar: caras laterales hacia fuera del eje; tapas en la dirección del eje
    for i, ref in zip(range(first_face, len(m.f)), refs):
        a, b, c = m.f[i]
        fn = np.cross(m.v[b] - m.v[a], m.v[c] - m.v[a])
        if isinstance(ref, tuple): outward = ref[1]
        else: outward = (m.v[a] + m.v[b] + m.v[c]) / 3 - ref
        if np.dot(fn, outward) < 0: m.f[i] = (a, c, b)
    # normales suaves reales (de las caras ya orientadas)
    V = np.array(m.v); F = np.array(m.f)
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3): np.add.at(N, F[:, k], fn)
    l = np.linalg.norm(N, axis=1); l[l == 0] = 1
    m.n = list(N / l[:, None])
    return ids

def shaped_tube(m, body, side, ys, bone, clearance, uv_v, segs=28, close_start=False, close_end=False, scale=1.0):
    rings = [leg_section(None, y, clearance, segs, body=body, side=side) for y in ys]
    # suavizado a lo largo de la pierna (evita escalones entre franjas)
    # (en polares: el max coordenada a coordenada encogia el lado -X/-Z del anillo)
    R = np.array(rings)
    C = np.array([[r[:, 0].mean(), 0, r[:, 2].mean()] for r in R])
    rad = np.hypot(R[:, :, 0] - C[:, None, 0], R[:, :, 2] - C[:, None, 2])
    ang = np.arctan2(R[:, :, 2] - C[:, None, 2], R[:, :, 0] - C[:, None, 0])
    for _ in range(2):
        for k in range(1, len(R) - 1):
            rad[k] = np.maximum(rad[k], (rad[k - 1] + rad[k + 1]) / 2 * 0.97)
    R[:, :, 0] = C[:, None, 0] + rad * np.cos(ang)
    R[:, :, 2] = C[:, None, 2] + rad * np.sin(ang)
    rings = [list(r) for r in R]
    loft(m, rings, bone, uv_v, close_start, close_end)
    centers = [np.array(r).mean(0) for r in rings]
    return centers, rings

def shaped_foot(m, body, side, bone, uv_v, clearance=0.003, lift=0.0):
    """Pie protésico en cuña con las medidas del pie del cuerpo: talón alto y redondo, punta baja.
    Anillos (x,y) a lo largo de Z desde el talón (+z) a la punta (-z)."""
    V = body["verts"]; W = body["weights"]
    bn = "Bip01_%s_Foot" % side
    pts = np.array([V[i] for i in range(len(V)) if bn in W[i] and not any("Dress" in b for b in W[i])])
    zh, zt = pts[:, 2].max(), pts[:, 2].min()
    cx = (pts[:, 0].min() + pts[:, 0].max()) / 2
    half_w = (pts[:, 0].max() - pts[:, 0].min()) / 2 + clearance
    L = zh - zt
    rings = []
    segs = 14
    prof = [(0.00, 0.60, 0.040), (0.10, 0.80, 0.046), (0.25, 1.00, 0.040), (0.45, 1.00, 0.032), (0.65, 0.98, 0.026), (0.85, 0.90, 0.018), (1.00, 0.65, 0.012)]
    for t, wf, h in prof:
        z = zh - L * t
        for_ring = []
        for k in range(segs):
            ang = 2 * math.pi * k / segs
            x = cx + half_w * wf * math.cos(ang)
            y = 0.002 + lift + h / 2 + (h / 2) * math.sin(ang)
            for_ring.append(np.array([x, y, z]))
        rings.append(for_ring)
    loft(m, rings, bone, uv_v, close_start=True, close_end=True, flip=True)

# ------------------------------------------------------------------ secciones genéricas a lo largo de un eje

_limb_cache = {}
def _limb_mesh(body, bones, side):
    key = (id(body), tuple(bones), side)
    if key not in _limb_cache:
        V = body["verts"]; W = body["weights"]; faces = []
        for f in body["faces"]:
            if face_is_hidden(body, f): continue
            if any(any(bn in W[vi] for bn in bones) for vi in f):
                if (np.mean([V[vi][0] for vi in f]) > 0) == (side == "L"): faces.append(f)
        idx = sorted({vi for f in faces for vi in f})
        _limb_cache[key] = (V, faces, np.array([V[i] for i in idx]))
    return _limb_cache[key]

def axis_section(body, bones, side, o, axis, t):
    """Intersección de la superficie del miembro con el plano perpendicular a axis a distancia t de o."""
    V, faces, _ = _limb_mesh(body, bones, side)
    pts = []
    for f in faces:
        for k in range(3):
            a_, b_ = V[f[k]], V[f[(k + 1) % 3]]
            ta, tb = (a_ - o) @ axis - t, (b_ - o) @ axis - t
            if ta * tb <= 0 and ta != tb:
                s_ = ta / (ta - tb); pts.append(a_ + (b_ - a_) * s_)
    return np.array(pts) if pts else np.zeros((0, 3))

def axis_ring(body, bones, side, o, axis, u, v, t, clearance, segs=24, band=0.014, smooth=1):
    """Anillo que envuelve la sección real del miembro (más los vértices a ±band) con holgura."""
    V, faces, P = _limb_mesh(body, bones, side)
    sl = axis_section(body, bones, side, o, axis, t)
    tt = (P - o) @ axis
    bandp = P[np.abs(tt - t) <= band]
    if len(bandp): sl = np.vstack([sl, bandp]) if len(sl) else bandp
    if len(sl) < 4: sl = P[np.argsort(np.abs(tt - t))[:10]]
    pu, pv = (sl - o) @ u, (sl - o) @ v
    cu, cv = (pu.min() + pu.max()) / 2, (pv.min() + pv.max()) / 2
    ang = np.arctan2(pv - cv, pu - cu); dist = np.hypot(pu - cu, pv - cv)
    r = np.zeros(segs)
    for k in range(segs):
        th = -math.pi + 2 * math.pi * k / segs
        d = np.abs((ang - th + math.pi) % (2 * math.pi) - math.pi)
        sector = d <= 1.6 * math.pi / segs + 0.02
        r[k] = dist[sector].max() if sector.any() else dist[np.argsort(d)[:2]].max()
    for _ in range(smooth): r = np.maximum(r, (np.roll(r, 1) + np.roll(r, -1)) / 2 * 0.98)
    r = r + clearance
    c = o + axis * t
    return [c + u * (cu + r[k] * math.cos(-math.pi + 2 * math.pi * k / segs)) + v * (cv + r[k] * math.sin(-math.pi + 2 * math.pi * k / segs)) for k in range(segs)]

def axis_tube(m, body, bones, side, o, axis, u, v, ts, bone, clearance, uv_v, segs=24, close_start=False, close_end=False, scale=1.0):
    rings = [axis_ring(body, bones, side, o, axis, u, v, t, clearance, segs) for t in ts]
    R = np.array(rings)
    C = R.mean(1)
    rel = R - C[:, None, :]
    pu, pv = rel @ u, rel @ v
    rad = np.hypot(pu, pv); ang = np.arctan2(pv, pu)
    for _ in range(2):
        for k in range(1, len(R) - 1):
            rad[k] = np.maximum(rad[k], (rad[k - 1] + rad[k + 1]) / 2 * 0.97)
    rad = rad * scale
    R = C[:, None, :] + u[None, None, :] * (rad * np.cos(ang))[:, :, None] + v[None, None, :] * (rad * np.sin(ang))[:, :, None]
    rings = [list(r) for r in R]
    loft(m, rings, bone, uv_v, close_start, close_end)
    return [np.array(r).mean(0) for r in rings], rings

def path_tube(m, pts, radii, ref, segs, bone, uv_v, close_start=True, close_end=True):
    """Tubo cuyos anillos son perpendiculares a la tangente local del camino (para curvas: gancho, pulgar)."""
    rings = []
    for k, (p, r) in enumerate(zip(pts, radii)):
        tan = np.array(pts[min(k + 1, len(pts) - 1)]) - np.array(pts[max(k - 1, 0)])
        tan = tan / (np.linalg.norm(tan) or 1)
        u = np.array(ref, float) - tan * (np.array(ref, float) @ tan); u = u / (np.linalg.norm(u) or 1)
        v = np.cross(tan, u)
        rings.append([np.array(p) + u * (r[0] * math.cos(2 * math.pi * s_ / segs)) + v * (r[1] * math.sin(2 * math.pi * s_ / segs)) for s_ in range(segs)])
    loft(m, rings, bone, uv_v, close_start, close_end)

# ------------------------------------------------------------------ piernas (por nivel)

LEG_LEVELS = {"Ankle": "Foot", "": "LowerLeg", "Thigh": "UpperLeg"}      # sufijo del modelo -> parte amputada
ARM_LEVELS = {"Wrist": "Hand", "": "ForeArm"}

def peg_shaft(m, cx, cz, y_top, y_knee, thigh, calf, r_top=0.028):
    """Pata de madera torneada desde y_top hasta el suelo; si cruza la rodilla se parte en dos huesos."""
    def prof(y):
        t = (y_top - y) / max(1e-6, y_top)        # 0 arriba .. 1 abajo
        return r_top * (1 - t) + 0.016 * t + 0.004 * math.sin(math.pi * t) * (1 if t < 0.5 else 0.3)
    def seg(y0, y1, bone, uv):
        n = max(2, int((y0 - y1) / 0.035) + 2)
        ys = [y0 + (y1 - y0) * k / (n - 1) for k in range(n)]
        pts = [np.array([cx, y, cz]) for y in ys]; rr = [(prof(y), prof(y)) for y in ys]
        m.tube(pts, rr, (X, Z), 12, bone, (0, 1), uv, close_start=True, close_end=True)
    if y_top > y_knee + 0.02:
        seg(y_top, y_knee, thigh, (0.3, 0.6)); seg(y_knee, 0.012, calf, (0.6, 0.9))
    else:
        seg(y_top, 0.012, calf, (0.3, 0.9))
    m.tube([np.array([cx, 0.012, cz]), np.array([cx, 0.0, cz])], [(0.019, 0.019), (0.017, 0.017)], (X, Z), 12, calf, (0, 1), (0.92, 1.0), close_start=True, close_end=True)

def leg_straps(m, body, side, bone, ys, clearance):
    for y in ys:
        r1 = leg_section(None, y + 0.006, clearance + 0.0025, body=body, side=side); r2 = leg_section(None, y - 0.006, clearance + 0.0025, body=body, side=side)
        for q in r1: q[1] = y + 0.006
        for q in r2: q[1] = y - 0.006
        loft(m, [r1, r2], bone, (0.26, 0.29), close_start=True, close_end=True)

def peg_leg(body, side, level=""):
    """Pata de palo esbelta con encaje de cuero a la medida del muñón:
    Ankle: manguito en la pantorrilla baja + pata corta; "": encaje muslo bajo + pantorrilla + pata;
    Thigh: encaje en el muslo, cono de madera, rótula y pata larga."""
    thigh, calf = "Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side
    m = MeshB()
    if level == "Ankle":
        ys = [0.19, 0.17, 0.15, 0.13, 0.11, 0.095, 0.08, 0.068]
        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0042, (0.0, 0.25), close_start=True, close_end=True)
        leg_straps(m, body, side, calf, (0.183, 0.10), 0.0042)
        base = centers[-1]
        peg_shaft(m, base[0], base[2], 0.068, 0.25, thigh, calf, r_top=0.026)
    elif level == "Thigh":
        ys = [0.47, 0.45, 0.43, 0.41, 0.39]
        centers, rings = shaped_tube(m, body, side, ys, thigh, 0.0045, (0.0, 0.25), close_start=True, close_end=True)
        leg_straps(m, body, side, thigh, (0.462, 0.40), 0.0045)
        # cono de madera del muslo hasta la rodilla, rótula y pata
        R = np.array(rings[-1]); c = R.mean(0)
        rx, rz = (R[:, 0].max() - R[:, 0].min()) / 2 - 0.004, (R[:, 2].max() - R[:, 2].min()) / 2 - 0.004
        m.tube([np.array([c[0], 0.39, c[2]]), np.array([c[0], 0.33, c[2]]), np.array([c[0], 0.27, c[2]])], [(rx, rz), (rx * 0.8, rz * 0.8), (0.032, 0.032)], (X, Z), 16, thigh, (0, 1), (0.3, 0.6), close_start=True, close_end=True)
        m.tube([np.array([c[0], 0.27, c[2]]), np.array([c[0], 0.258, c[2]]), np.array([c[0], 0.242, c[2]]), np.array([c[0], 0.232, c[2]])], [(0.030, 0.030), (0.036, 0.036), (0.036, 0.036), (0.030, 0.030)], (X, Z), 16, calf, (0, 1), (0.3, 0.6), close_start=True, close_end=True)
        peg_shaft(m, c[0], c[2], 0.232, 0.25, thigh, calf, r_top=0.028)
    else:
        ys = [0.33, 0.30, 0.27, 0.24, 0.21, 0.18, 0.15, 0.12, 0.095, 0.075, 0.062]
        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0042, (0.0, 0.25), close_start=True, close_end=True)
        leg_straps(m, body, side, calf, (0.325, 0.20, 0.10), 0.0042)
        base = centers[-1]
        peg_shaft(m, base[0], base[2], 0.062, 0.25, thigh, calf, r_top=0.028)
    return m

def mech_shin(m, body, side, ys, calf, medical, uv=(0.2, 0.8)):
    """Caña con la forma de la pantorrilla; mecánica: chapa + barras laterales."""
    if medical:
        return shaped_tube(m, body, side, ys, calf, 0.0036, uv, close_start=True, close_end=True)
    centers, rings = shaped_tube(m, body, side, ys, calf, 0.0032, uv, close_start=True, close_end=True)
    for sgn in (-1, 1):
        path = []
        for k, r in enumerate(rings):
            R = np.array(r); c = R.mean(0)
            edge = R[:, 0].max() if sgn > 0 else R[:, 0].min()
            path.append(np.array([edge + sgn * 0.004, ys[k], c[2]]))
        m.tube(path, [(0.0045, 0.006)] * len(path), (X, Z), 8, calf, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
    return centers, rings

def mech_leg(body, side, medical=False, level=""):
    """Pierna mecánica (chapa + barras) o médica (carbono moldeado) por nivel: Ankle (manguito en la
    pantorrilla + tobillo + pie), "" (encaje bajo la rodilla + caña + pie), Thigh (encaje de muslo,
    muslo moldeado, rodilla articulada, caña y pie)."""
    thigh, calf, foot = "Bip01_%s_Thigh" % side, "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side
    m = MeshB()
    if level == "Ankle":
        shaped_tube(m, body, side, [0.19, 0.165, 0.14], calf, 0.0048, (0.0, 0.2), close_start=True, close_end=True)
        mech_shin(m, body, side, [0.14, 0.115, 0.09, 0.07], calf, medical)
    elif level == "Thigh":
        shaped_tube(m, body, side, [0.47, 0.45, 0.43, 0.41, 0.39], thigh, 0.0048, (0.0, 0.2), close_start=True, close_end=True)
        ys = [0.39, 0.36, 0.33, 0.30, 0.275]
        if medical:
            shaped_tube(m, body, side, ys, thigh, -0.003, (0.2, 0.8), close_start=True, close_end=True)
        else:
            centers, rings = shaped_tube(m, body, side, ys, thigh, -0.004, (0.2, 0.8), close_start=True, close_end=True)
            for sgn in (-1, 1):
                path = []
                for k, r in enumerate(rings):
                    R = np.array(r); c = R.mean(0)
                    edge = R[:, 0].max() if sgn > 0 else R[:, 0].min()
                    path.append(np.array([edge + sgn * 0.004, ys[k], c[2]]))
                m.tube(path, [(0.0045, 0.006)] * len(path), (X, Z), 8, thigh, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
        # rodilla: cilindro central (Calf) + discos de bisagra a los lados
        r_k = leg_section(None, 0.27, -0.004, body=body, side=side); Rk = np.array(r_k); ck = Rk.mean(0)
        m.tube([np.array([ck[0], 0.278, ck[2]]), np.array([ck[0], 0.236, ck[2]])], [(0.030, 0.034), (0.028, 0.032)], (X, Z), 14, calf, (0, 1), (0.8, 0.86), close_start=True, close_end=True)
        for sgn in (-1, 1):
            x0 = (Rk[:, 0].max() if sgn > 0 else Rk[:, 0].min()) + sgn * 0.002
            m.tube([np.array([x0, 0.255, ck[2]]), np.array([x0 + sgn * 0.012, 0.255, ck[2]])], [(0.016, 0.016), (0.016, 0.016)], (Y, Z), 12, calf, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
        mech_shin(m, body, side, [0.236, 0.21, 0.185, 0.16, 0.135, 0.105, 0.085, 0.07], calf, medical)
    else:
        shaped_tube(m, body, side, [0.33, 0.305, 0.28, 0.255], calf, 0.0048, (0.0, 0.2), close_start=True, close_end=True)
        mech_shin(m, body, side, [0.255, 0.225, 0.195, 0.165, 0.135, 0.105, 0.085, 0.07], calf, medical)
    # tobillo y pie
    r_top = leg_section(None, 0.07, 0.0, body=body, side=side); c = np.array(r_top).mean(0)
    m.tube([np.array([c[0], 0.072, c[2]]), np.array([c[0], 0.04, c[2]])], [(0.024, 0.028), (0.026, 0.03)], (X, Z), 12, foot, (0, 1), (0.8, 0.86), close_start=True, close_end=True)
    shaped_foot(m, body, side, foot, (0.86, 1.0), clearance=0.0035 if medical else 0.003)
    return m

# ------------------------------------------------------------------ brazos (por nivel)

def arm_frame(body, side):
    o, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Forearm" % side)
    ho, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Hand" % side)
    axis = ho - o; L = np.linalg.norm(axis); axis = axis / L
    down = np.array([0.0, -1.0, 0.0]); down = down - axis * (down @ axis); down = down / np.linalg.norm(down)   # palma (abajo)
    front = np.cross(down, axis); front = front / np.linalg.norm(front)                                           # hacia -Z aprox
    if front[2] > 0: front = -front
    return o, axis, down, front, L

def arm_socket(m, body, side, level, bone, uv_socket, uv_shell, clearance=0.0045):
    """Encaje: antebrazo (sobre el muñón junto al codo + caña con forma de antebrazo) o muñeca (manguito).
    Devuelve el punto donde arranca el dispositivo terminal y la base (u, v)."""
    o, axis, down, front, L = arm_frame(body, side)
    bones = ARM_BONES[side]
    if level == "Wrist":
        axis_tube(m, body, bones, side, o, axis, down, front, [0.07, 0.085, 0.10, 0.115, 0.13, 0.142], bone, clearance, uv_socket, close_start=True, close_end=True)
        axis_tube(m, body, bones, side, o, axis, down, front, [0.142, 0.152], bone, clearance - 0.004, uv_shell, close_start=True, close_end=True)
        return o + axis * 0.152
    axis_tube(m, body, bones, side, o, axis, down, front, [-0.015, 0.0, 0.015, 0.03, 0.045], bone, clearance, uv_socket, close_start=True, close_end=True)
    axis_tube(m, body, bones, side, o, axis, down, front, [0.045, 0.07, 0.095, 0.12], bone, -0.002, uv_shell, close_start=True, close_end=True)
    return o + axis * 0.12

def arm_straps(m, body, side, bone, ts, clearance):
    o, axis, down, front, L = arm_frame(body, side)
    bones = ARM_BONES[side]
    for t in ts:
        r1 = axis_ring(body, bones, side, o, axis, down, front, t - 0.005, clearance + 0.0025)
        r2 = axis_ring(body, bones, side, o, axis, down, front, t + 0.005, clearance + 0.0025)
        loft(m, [r1, r2], bone, (0.26, 0.29), close_start=True, close_end=True)

def peg_arm(body, side, level=""):
    """Brazo de madera: copa de cuero a medida + vástago y "mano" de madera."""
    bone = "Bip01_%s_Forearm" % side
    o, axis, down, front, L = arm_frame(body, side)
    m = MeshB()
    s = arm_socket(m, body, side, level, bone, (0.0, 0.25), (0.3, 0.6), clearance=0.0045)
    arm_straps(m, body, side, bone, (0.085, 0.13) if level == "Wrist" else (0.0, 0.035), 0.0045)
    rod = 0.02 if level == "Wrist" else 0.045
    m.tube([s, s + axis * rod], [(0.016, 0.016), (0.013, 0.013)], (down, front), 10, bone, (0, 1), (0.3, 0.7), close_start=True, close_end=True)
    e = s + axis * rod
    m.tube([e, e + axis * 0.015, e + axis * 0.05, e + axis * 0.065], [(0.014, 0.014), (0.026, 0.020), (0.026, 0.020), (0.012, 0.010)], (down, front), 12, bone, (0, 1), (0.72, 1.0), close_start=True, close_end=True)
    return m

def hook_arm(body, side, level=""):
    """Gancho: copa de cuero a medida, caña de acero y gancho partido (dos púas curvas) con goma."""
    bone = "Bip01_%s_Forearm" % side
    o, axis, down, front, L = arm_frame(body, side)
    m = MeshB()
    s = arm_socket(m, body, side, level, bone, (0.0, 0.25), (0.3, 0.6), clearance=0.0045)
    arm_straps(m, body, side, bone, (0.085, 0.13) if level == "Wrist" else (0.0, 0.035), 0.0045)
    # unidad de muñeca (acero oscuro) y caña
    m.tube([s, s + axis * 0.014], [(0.015, 0.015), (0.012, 0.012)], (down, front), 12, bone, (0, 1), (0.6, 0.84), close_start=True, close_end=True)
    sh = s + axis * 0.014
    m.tube([sh, sh + axis * 0.03], [(0.0085, 0.0085), (0.008, 0.008)], (down, front), 10, bone, (0, 1), (0.3, 0.6), close_start=True, close_end=True)
    base = sh + axis * 0.03
    # banda de goma en la base de las púas
    m.tube([base - axis * 0.004, base + axis * 0.004], [(0.012, 0.012), (0.012, 0.012)], (down, front), 10, bone, (0, 1), (0.86, 0.94), close_start=True, close_end=True)
    # dos púas: arco de radio R en el plano (axis, front) que se curva hacia delante (front)
    R = 0.031
    for off in (-0.0075, 0.0075):
        c = base + front * R + down * off
        pts, rr = [], []
        n = 9
        for k in range(n):
            th = math.radians(165.0) * k / (n - 1)
            pts.append(c + axis * (R * math.sin(th)) - front * (R * math.cos(th)))
            rr.append((0.0058 - 0.0028 * k / (n - 1), 0.0058 - 0.0028 * k / (n - 1)))
        path_tube(m, pts, rr, down, 8, bone, (0.94, 1.0))
    return m

def mech_hand(m, s, axis, down, front, bone, uv, medical):
    """Mano protésica estilizada: palma elíptica, cuatro dedos con ligera curva y pulgar."""
    pw = 0.032 if medical else 0.031           # media anchura (front/back)
    pt = 0.013 if medical else 0.0115          # medio grosor (palma)
    m.tube([s, s + axis * 0.014, s + axis * 0.048, s + axis * 0.056], [(pt * 0.8, pw * 0.7), (pt, pw), (pt, pw), (pt * 0.9, pw * 0.95)], (down, front), 14, bone, (0, 1), uv, close_start=True, close_end=True)
    e = s + axis * 0.056
    fr = 0.0068 if medical else 0.0062
    for k, off in enumerate((-0.0225, -0.0075, 0.0075, 0.0225)):
        ln = 0.044 if k in (1, 2) else 0.036
        p0 = e + front * off
        pts = [p0, p0 + axis * (ln * 0.5), p0 + axis * (ln * 0.85) + down * 0.005, p0 + axis * ln + down * 0.011]
        rr = [(fr, fr), (fr, fr), (fr * 0.9, fr * 0.9), (fr * 0.75, fr * 0.75)]
        m.tube(pts, rr, (down, front), 8, bone, (0, 1), uv, close_start=True, close_end=True)
    # pulgar: sale del lado delantero de la palma, hacia delante y adelante
    t0 = s + axis * 0.014 + front * pw * 0.9 + down * (pt * 0.3)
    pts = [t0, t0 + front * 0.014 + axis * 0.009, t0 + front * 0.024 + axis * 0.026, t0 + front * 0.027 + axis * 0.042]
    path_tube(m, pts, [(fr * 1.15, fr * 1.15), (fr * 1.1, fr * 1.1), (fr, fr), (fr * 0.8, fr * 0.8)], down, 8, bone, uv)

def mech_arm(body, side, medical=False, level=""):
    """Brazo mecánico (chapa) o médico (carbono): encaje a medida, caña con forma de antebrazo y mano."""
    bone, hand = "Bip01_%s_Forearm" % side, "Bip01_%s_Hand" % side
    o, axis, down, front, L = arm_frame(body, side)
    m = MeshB()
    s = arm_socket(m, body, side, level, bone, (0.0, 0.2), (0.2, 0.8), clearance=0.0048 if medical else 0.0045)
    if not medical:
        # barras laterales en la caña (nivel antebrazo) o en el manguito (muñeca)
        bones = ARM_BONES[side]
        ts = [0.08, 0.10, 0.12, 0.14] if level == "Wrist" else [0.03, 0.06, 0.09, 0.12]
        for sgn in (-1, 1):
            path = []
            for t in ts:
                ring = np.array(axis_ring(body, bones, side, o, axis, down, front, t, 0.0045 if level == "Wrist" else -0.002))
                c = ring.mean(0); d = (ring - c) @ front
                edge = c + front * (d.max() if sgn > 0 else d.min())
                path.append(edge + front * sgn * 0.004)
            m.tube(path, [(0.0045, 0.0045)] * len(path), (down, axis), 8, bone, (0, 1), (0.85, 0.95), close_start=True, close_end=True)
    # muñeca y mano (hueso de la mano: acompaña la animación de agarre)
    m.tube([s, s + axis * 0.01], [(0.012, 0.018), (0.012, 0.019)], (down, front), 12, hand, (0, 1), (0.8, 0.86), close_start=True, close_end=True)
    mech_hand(m, s + axis * 0.01, axis, down, front, hand, (0.86, 1.0), medical)
    return m

def leg_tourniquet(body, side):
    o, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Thigh" % side)
    bone = "Bip01_%s_Thigh" % side
    m = MeshB()
    # muslo medio: centro aproximado del muslo
    c = np.array([o[0] + (0.008 if side == "L" else -0.008), 0.43, 0.028])
    m.tube([c + Y * 0.014, c - Y * 0.014], [(0.062, 0.076), (0.062, 0.076)], (X, Z), 18, bone, (0, 1), (0.0, 0.5))
    m.tube([c + Y * 0.014, c - Y * 0.014], [(0.058, 0.072), (0.058, 0.072)], (X, Z), 18, bone, (0, 1), (0.0, 0.5))   # cara interior
    # molinete (varilla) y hebilla al frente (-Z)
    m.box((c[0], c[1], c[2] - 0.082), (0.03, 0.022, 0.012), bone, (0.55, 0.0, 0.75, 0.3))
    m.box((c[0], c[1] + 0.03, c[2] - 0.085), (0.008, 0.08, 0.008), bone, (0.8, 0.0, 1.0, 0.5))
    return m

def crutch():
    """Muleta axilar en el espacio de armas: +Y arriba, origen en la empuñadura, 'hoja' en el plano YZ."""
    m = MeshB()
    # dos barras laterales (en Z) desde la contera (-0.55) hasta la almohadilla (+0.35), empuñadura en 0
    # escala del juego: un bate mide 0.49 unidades (~0.85 m) -> muleta de 1.2 m = 0.70 unidades
    for dz in (-0.025, 0.025):
        m.box((0, -0.10, dz), (0.014, 0.70, 0.012), None, (0.0, 0.0, 0.3, 1.0))
    m.box((0, -0.455, 0), (0.016, 0.03, 0.016), None, (0.3, 0.0, 0.4, 0.3))         # contera
    m.box((0, -0.475, 0), (0.022, 0.016, 0.022), None, (0.3, 0.3, 0.4, 0.5))        # goma
    m.box((0, 0.0, 0), (0.024, 0.024, 0.062), None, (0.4, 0.0, 0.6, 1.0))           # empuñadura
    m.box((0, 0.235, 0), (0.036, 0.03, 0.12), None, (0.6, 0.0, 1.0, 1.0))           # almohadilla axilar
    for yy in (-0.16, 0.12):
        m.box((0, yy, 0), (0.007, 0.007, 0.06), None, (0.3, 0.6, 0.4, 0.7))          # travesaños
    return m

def bone_saw(teeth_scale=1.0, teeth_n=20, teeth_w=0.0062):
    """Sierra de amputación (tipo Satterlee): hoja ancha con lomo reforzado, dientes abajo y mango
    de pistola de madera con guarda. +Y a lo largo, origen en el mango. ~0.28 u = 49 cm."""
    m = MeshB()
    # mango de madera, inclinado hacia atrás (eje Y hacia -Z), con guarda metálica
    grip_len, grip_tilt = 0.085, -0.35
    for k in range(6):                      # mango por rodajas para que quede inclinado y algo ovalado
        t = k / 5.0
        cy = -0.01 + t * grip_len * math.cos(grip_tilt)
        cz = -0.012 + t * grip_len * math.sin(grip_tilt)
        w = 0.024 - 0.004 * abs(t - 0.5)
        m.box((0, cy, cz), (w, grip_len / 5.0 + 0.002, 0.03), None, (0.02, 0.1 + t * 0.8, 0.22, 0.12 + t * 0.8))
    m.box((0, 0.025, -0.045), (0.012, 0.09, 0.008), None, (0.26, 0.2, 0.31, 0.9))      # guarda (barra delantera)
    m.box((0, 0.07, -0.025), (0.012, 0.008, 0.045), None, (0.26, 0.2, 0.31, 0.9))      # guarda (barra superior)
    m.box((0, 0.065, 0.02), (0.02, 0.03, 0.04), None, (0.26, 0.05, 0.31, 0.5))         # talón metálico de la hoja
    # hoja: placa fina en el plano YZ, más alta en el talón que en la punta
    y0, y1 = 0.08, 0.30
    segs = 8
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        ya, yb = y0 + (y1 - y0) * t0, y0 + (y1 - y0) * t1
        ha, hb = 0.05 - 0.02 * t0, 0.05 - 0.02 * t1
        h = (ha + hb) / 2
        m.box((0, (ya + yb) / 2, 0.02 + h / 2 - 0.045), (0.0022, (yb - ya) + 0.0005, h), None, (0.34 + 0.6 * t0, 0.05, 0.34 + 0.6 * t1, 0.75))
    # lomo reforzado (latón) a lo largo del borde superior de la hoja
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        ya, yb = y0 + (y1 - y0) * t0, y0 + (y1 - y0) * t1
        h = 0.05 - 0.02 * (t0 + t1) / 2
        m.box((0, (ya + yb) / 2, 0.02 + h - 0.045 + 0.003), (0.007, (yb - ya) + 0.0005, 0.007), None, (0.26, 0.05, 0.31, 0.5))
    # dientes a lo largo del borde inferior (pequeños prismas)
    n = teeth_n
    for k in range(n):
        y = y0 + 0.008 + (y1 - y0 - 0.016) * k / (n - 1)
        m.box((0, y, 0.02 - 0.045 - 0.005 * teeth_scale), (0.0022, teeth_w, 0.010 * teeth_scale), None, (0.9, 0.8, 1.0, 0.95))
    return m

def severed_limb(body, side, part):
    """Modelo de suelo del miembro cercenado: caras del cuerpo del lado quitado, tumbadas."""
    bones = {"Hand": ARM_BONES[side][2:], "ForeArm": ARM_BONES[side][1:], "UpperArm": ARM_BONES[side],
             "Foot": LEG_BONES[side][2:], "LowerLeg": LEG_BONES[side][1:], "UpperLeg": LEG_BONES[side]}[part]
    faces = limb_faces(body, bones)
    is_leg = part in LEG_CUTS
    if is_leg:
        nv, nuv, nw, nf, edge = clip_mesh(body, faces, LEG_CUTS[part], keep_above=False)
        nv, nuv, nw, nf = add_cap(nv, nuv, nw, nf, edge, normal_down=False)
    else:
        cut_x = {"Hand": 0.385, "ForeArm": 0.25, "UpperArm": 0.118}[part] * (1 if side == "L" else -1)
        # recortar por un plano x usando el mismo recortador: giramos x<->y temporalmente
        tmp = dict(body); tmp["verts"] = body["verts"][:, [1, 0, 2]].copy()
        nv, nuv, nw, nf, edge = clip_mesh(tmp, faces, cut_x, keep_above=(side == "L"))
        nv, nuv, nw, nf = add_cap(nv, nuv, nw, nf, edge, normal_down=(side != "L"))
        nv = nv[:, [1, 0, 2]].copy()
    verts = np.array(nv, float)
    # tumbar: el eje largo del miembro a lo largo de X, sobre el suelo (y >= 0)
    c = verts.mean(axis=0)
    verts = verts - c
    if is_leg:
        R = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float)     # Y -> X
        verts = verts @ R.T
    verts = verts - verts.min(axis=0) * np.array([0, 1, 0]) + np.array([0, 0.002, 0])
    m = MeshB(); m.v = list(verts); m.n = list(smooth_normals(verts, nf)); m.uv = [tuple(u) for u in nuv]; m.f = list(nf); m.w = [None] * len(verts)
    return m

# ------------------------------------------------------------------ texturas de prótesis / ítems

def noise_img(size, base, var, seed):
    rng = np.random.default_rng(seed)
    arr = np.array(base, float)[None, None, :] + rng.normal(0, var, (size[1], size[0], 3))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

def tex_wood_leather(path, seed=1):
    img = noise_img((128, 128), (150, 105, 60), 10, seed)
    d = ImageDraw.Draw(img)
    for i in range(0, 128, 6):
        d.line((0, i, 128, i + 3), fill=(120, 80, 45, 255), width=1)
    d.rectangle((0, 0, 128, 32), fill=(78, 50, 32, 255))           # cuero (copa) v 0..0.25
    for i in range(0, 128, 9): d.line((i, 0, i + 4, 32), fill=(60, 38, 24, 255))
    d.rectangle((0, 33, 128, 37), fill=(45, 30, 20, 255))         # correa v 0.26..0.29
    d.rectangle((0, 118, 128, 128), fill=(40, 40, 40, 255))        # goma/punta
    img.save(path)

def tex_metal(path, seed=2, dark=False, foot=None):
    """foot: color de la banda inferior (v 0.86..1, "dark" en blender_build). El brazo médico la pinta de polímero
    claro para la mano (3.1.0); el resto la deja oscura."""
    base = (40, 42, 46) if dark else (150, 152, 158)
    img = noise_img((128, 128), base, 6, seed)
    d = ImageDraw.Draw(img)
    for i in range(0, 128, 16): d.line((0, i, 128, i), fill=tuple(max(0, c - 25) for c in base) + (255,))
    d.rectangle((0, 0, 128, 26), fill=(60, 62, 66, 255))           # encaje negro
    d.rectangle((0, 110, 128, 128), fill=foot or (35, 35, 38, 255))        # pie (o mano del brazo médico)
    if dark:
        for i in range(0, 128, 4): d.line((i, 26, i + 2, 110), fill=(55, 58, 64, 255))   # trama de carbono
        d.rectangle((0, 20, 128, 24), fill=(220, 220, 220, 255))
    img.save(path)

def tex_hook(path, seed=9):
    """v 0..0.25 cuero, 0.26..0.29 correa, 0.3..0.6 acero, 0.6..0.84 acero oscuro, 0.86..0.94 goma, 0.94..1 acero pulido."""
    img = noise_img((128, 128), (168, 170, 176), 6, seed)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 128, 32), fill=(78, 50, 32, 255))
    for i in range(0, 128, 9): d.line((i, 0, i + 4, 32), fill=(60, 38, 24, 255))
    d.rectangle((0, 33, 128, 37), fill=(45, 30, 20, 255))
    for i in range(38, 77, 5): d.line((0, i, 128, i), fill=(150, 152, 158, 255))
    d.rectangle((0, 77, 128, 108), fill=(70, 72, 78, 255))
    for i in range(0, 128, 6): d.line((i, 77, i, 108), fill=(58, 60, 66, 255))
    d.rectangle((0, 110, 128, 120), fill=(30, 30, 32, 255))
    d.rectangle((0, 121, 128, 128), fill=(205, 207, 212, 255))
    img.save(path)

def tex_tourniquet_leg(path):
    img = noise_img((64, 64), (40, 40, 44), 5, 3); d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 64, 32), fill=(190, 40, 30, 255)); d.rectangle((35, 0, 48, 20), fill=(120, 120, 125, 255)); d.rectangle((50, 0, 64, 32), fill=(230, 230, 230, 255))
    img.save(path)

def tex_crutch(path):
    img = noise_img((64, 64), (190, 190, 195), 6, 4); d = ImageDraw.Draw(img)
    d.rectangle((19, 0, 25, 64), fill=(50, 50, 50, 255)); d.rectangle((25, 0, 38, 64), fill=(60, 60, 60, 255)); d.rectangle((38, 0, 64, 64), fill=(70, 70, 80, 255))
    img.save(path)

def tex_bonesaw(path):
    img = noise_img((128, 128), (196, 198, 204), 6, 5); d = ImageDraw.Draw(img)
    # u 0..0.24 madera del mango (veta vertical), 0.26..0.31 latón, 0.34..0.94 acero de la hoja, 0.9.. dientes
    wood = noise_img((31, 128), (120, 78, 42), 9, 11)
    wd = ImageDraw.Draw(wood)
    for y in range(0, 128, 5): wd.line((0, y, 31, y + 2), fill=(96, 60, 32, 255))
    img.paste(wood, (0, 0))
    d.rectangle((33, 0, 40, 128), fill=(170, 140, 70, 255)); d.line((34, 0, 34, 128), fill=(205, 175, 95, 255))
    for x in range(44, 120, 2):      # acero cepillado horizontal
        d.line((x, 0, x, 128), fill=(188 + (x % 3) * 6, 190 + (x % 3) * 6, 196 + (x % 3) * 6, 255))
    for y in range(0, 128, 9): d.line((44, y, 120, y), fill=(176, 178, 184, 255))
    d.rectangle((116, 100, 128, 128), fill=(225, 227, 232, 255))
    img.save(path)

def tex_medical_arm(src, path):
    img = Image.open(src).convert("RGBA")
    g = img.convert("L")
    arr = np.array(g, float) * 0.35 + 20
    rgb = np.stack([arr, arr * 1.02, arr * 1.08], axis=-1)
    outimg = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    outimg.putalpha(img.split()[3])
    outimg.save(path)

# ------------------------------------------------------------------ iconos

def icon(name, painter):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    painter(d, img)
    img.save(out("textures", "Item_%s.png" % name))

SKIN = (222, 184, 150, 255); SKIN_D = (170, 130, 100, 255); RED = (150, 20, 20, 255); BONE = (240, 232, 215, 255)

def ic_hand(d, img):
    d.rounded_rectangle((8, 10, 24, 26), 5, fill=SKIN, outline=SKIN_D)
    for i, x in enumerate((9, 13, 17, 21)): d.rounded_rectangle((x, 3 + abs(i - 1.5), x + 3, 12), 1, fill=SKIN, outline=SKIN_D)
    d.rectangle((9, 24, 23, 29), fill=RED); d.ellipse((14, 25, 18, 29), fill=BONE)
def ic_forearm(d, img):
    d.rounded_rectangle((5, 12, 27, 20), 4, fill=SKIN, outline=SKIN_D)
    d.rounded_rectangle((3, 10, 10, 22), 3, fill=SKIN, outline=SKIN_D)
    d.rectangle((24, 11, 29, 21), fill=RED); d.ellipse((26, 14, 29, 18), fill=BONE)
def ic_upperarm(d, img):
    d.rounded_rectangle((3, 13, 29, 20), 4, fill=SKIN, outline=SKIN_D)
    d.ellipse((2, 11, 10, 22), fill=SKIN, outline=SKIN_D)
    d.rectangle((25, 12, 30, 21), fill=RED); d.ellipse((27, 14, 30, 18), fill=BONE)
def ic_foot(d, img):
    d.rounded_rectangle((6, 16, 28, 26), 5, fill=SKIN, outline=SKIN_D)
    d.rounded_rectangle((18, 8, 26, 20), 3, fill=SKIN, outline=SKIN_D)
    d.rectangle((18, 7, 26, 11), fill=RED); d.ellipse((20, 7, 24, 11), fill=BONE)
def ic_lowerleg(d, img):
    d.rounded_rectangle((12, 4, 21, 26), 4, fill=SKIN, outline=SKIN_D)
    d.rounded_rectangle((10, 22, 26, 29), 3, fill=SKIN, outline=SKIN_D)
    d.rectangle((12, 3, 21, 8), fill=RED); d.ellipse((14, 4, 19, 8), fill=BONE)
def ic_upperleg(d, img):
    d.rounded_rectangle((11, 3, 22, 29), 5, fill=SKIN, outline=SKIN_D)
    d.rectangle((11, 2, 22, 8), fill=RED); d.ellipse((14, 3, 19, 8), fill=BONE)
def ic_bonesaw(d, img):
    d.rectangle((3, 20, 12, 25), fill=(110, 70, 40, 255)); d.rectangle((12, 6, 15, 26), fill=(170, 170, 175, 255))
    d.rectangle((12, 6, 29, 9), fill=(170, 170, 175, 255)); d.rectangle((27, 6, 29, 26), fill=(170, 170, 175, 255))
    d.rectangle((13, 24, 28, 26), fill=(230, 232, 235, 255))
    for x in range(13, 28, 2): d.line((x, 26, x + 1, 28), fill=(200, 200, 205, 255))
def ic_kit(d, img):
    d.rounded_rectangle((3, 8, 29, 27), 3, fill=(220, 220, 225, 255), outline=(120, 120, 125, 255))
    d.rectangle((12, 4, 20, 9), fill=(120, 120, 125, 255)); d.rectangle((14, 13, 18, 23), fill=(200, 30, 30, 255)); d.rectangle((11, 16, 21, 20), fill=(200, 30, 30, 255))
def ic_crutch(d, img):
    d.rectangle((12, 2, 20, 6), fill=(60, 60, 60, 255)); d.rectangle((13, 6, 15, 29), fill=(190, 190, 195, 255)); d.rectangle((17, 6, 19, 29), fill=(190, 190, 195, 255))
    d.rectangle((11, 14, 21, 17), fill=(60, 60, 60, 255)); d.rectangle((14, 27, 18, 31), fill=(40, 40, 40, 255))
def ic_guide(d, img):
    d.rectangle((5, 3, 27, 29), fill=(235, 235, 230, 255), outline=(90, 90, 90, 255)); d.rectangle((5, 3, 27, 10), fill=(160, 30, 30, 255))
    d.line((9, 14, 23, 14), fill=(60, 60, 60, 255)); d.line((9, 18, 23, 18), fill=(60, 60, 60, 255)); d.line((9, 22, 19, 22), fill=(60, 60, 60, 255))
    d.rectangle((10, 23, 22, 27), fill=(200, 200, 200, 255)); d.line((12, 25, 20, 25), fill=(150, 30, 30, 255), width=1)
def ic_pegarm(d, img):
    d.rounded_rectangle((3, 11, 14, 21), 3, fill=(90, 60, 40, 255), outline=(50, 35, 25, 255)); d.rectangle((14, 14, 26, 18), fill=(160, 115, 70, 255)); d.ellipse((24, 11, 30, 21), fill=(160, 115, 70, 255))
def ic_medicalarm(d, img):
    d.rounded_rectangle((3, 11, 14, 21), 3, fill=(40, 40, 45, 255), outline=(20, 20, 20, 255)); d.rectangle((14, 13, 24, 19), fill=(60, 62, 70, 255))
    for i, x in enumerate((24, 26, 28)): d.rectangle((x, 11 + i, x + 1, 21 - i), fill=(90, 92, 100, 255))
def ic_pegleg(d, img):
    d.polygon(((9, 3), (23, 3), (20, 12), (12, 12)), fill=(90, 60, 40, 255)); d.rectangle((14, 12, 18, 28), fill=(160, 115, 70, 255)); d.rectangle((13, 28, 19, 31), fill=(40, 40, 40, 255))
def ic_mechleg(d, img):
    d.polygon(((9, 3), (23, 3), (20, 11), (12, 11)), fill=(60, 62, 66, 255)); d.rectangle((15, 11, 17, 24), fill=(150, 152, 158, 255))
    d.rectangle((11, 12, 12, 23), fill=(120, 120, 125, 255)); d.rectangle((20, 12, 21, 23), fill=(120, 120, 125, 255)); d.rectangle((9, 24, 26, 29), fill=(40, 40, 44, 255))
def ic_medicalleg(d, img):
    d.polygon(((9, 3), (23, 3), (20, 11), (12, 11)), fill=(35, 35, 40, 255)); d.polygon(((12, 11), (20, 11), (18, 24), (14, 24)), fill=(50, 52, 58, 255))
    d.rectangle((12, 9, 20, 10), fill=(220, 220, 220, 255)); d.rectangle((10, 24, 26, 29), fill=(30, 30, 34, 255))
def ic_tourniquet_leg(d, img):
    d.ellipse((4, 8, 28, 24), outline=(190, 40, 30, 255), width=4); d.rectangle((13, 2, 19, 10), fill=(120, 120, 125, 255))

def build_icons():
    icon("SeveredHand", ic_hand); icon("SeveredForeArm", ic_forearm); icon("SeveredUpperArm", ic_upperarm)
    icon("SeveredFoot", ic_foot); icon("SeveredLowerLeg", ic_lowerleg); icon("SeveredUpperLeg", ic_upperleg)
    icon("BoneSaw", ic_bonesaw); icon("SurgicalKit", ic_kit); icon("Crutch", ic_crutch); icon("FieldSurgeryGuide", ic_guide)
    icon("PegArm", ic_pegarm); icon("MedicalArm", ic_medicalarm); icon("PegLeg", ic_pegleg); icon("MechLeg", ic_mechleg); icon("MedicalLeg", ic_medicalleg)
    icon("LegTourniquet", ic_tourniquet_leg)
    # rasgos: lado derecho = espejo de los de TOC; piernas: dibujo simple
    tdir = os.path.join(TOC_UP, "ui", "Traits")
    for t in ("Hand", "ForeArm", "UpperArm"):
        im = Image.open(os.path.join(tdir, "trait_Amputee_%s.png" % t)).convert("RGBA")
        im.transpose(Image.FLIP_LEFT_RIGHT).save(out("ui", "Traits", "trait_Amputee_%s_R.png" % t))
    for t, h in (("Foot", 5), ("LowerLeg", 9)):
        for suf in ("", "_R"):
            im = Image.new("RGBA", (18, 18), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.rectangle((7, 1, 11, 1 + h), fill=SKIN, outline=SKIN_D); d.rectangle((7, 1 + h, 11, 3 + h), fill=RED)
            if suf: im = im.transpose(Image.FLIP_LEFT_RIGHT)
            im.save(out("ui", "Traits", "trait_Amputee_%s%s.png" % (t, suf)))

# ------------------------------------------------------------------ superposiciones del panel de salud

def blob(img, box, color=(0, 0, 0, 255)):
    d = ImageDraw.Draw(img); d.rounded_rectangle(box, 9, fill=color)

def build_overlays():
    # Cajas en el lienzo 123x302 de TOC. Derivadas de las de los brazos de TOC y de la tabla
    # BodyDamage_* del juego (lienzo 110x220, escala ~1.2 en Y, ~1.5 en X desde el centro).
    layout = {
        "Male":   {"UpperLeg": (161, 300), "LowerLeg": (215, 300), "Foot": (268, 300), "xL": (66, 92), "xR": (31, 57)},
        "Female": {"UpperLeg": (150, 290), "LowerLeg": (198, 290), "Foot": (252, 290), "xL": (66, 90), "xR": (33, 57)},
    }
    for sex, L in layout.items():
        for side in ("L", "R"):
            x0, x1 = L["x" + side]
            for part in ("UpperLeg", "LowerLeg", "Foot"):
                y0, y1 = L[part]
                img = Image.new("RGBA", (123, 302), (0, 0, 0, 0))
                blob(img, (x0, y0, x1, y1))
                img.save(out("ui", sex, "%s_%s.png" % (part, side)))
    # prótesis de pierna (gris claro, como ProstArm): pierna completa bajo la rodilla
    for side in ("L", "R"):
        img = Image.new("RGBA", (123, 302), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        x0, x1 = (68, 90) if side == "L" else (33, 55)
        d.polygon(((x0 + 2, 218), (x1 - 2, 218), (x1 - 6, 232), (x0 + 6, 232)), fill=(0, 0, 0, 255))
        d.rectangle((x0 + 8, 232, x1 - 8, 290), fill=(0, 0, 0, 255)); d.rectangle((x0 + 2, 288, x1, 298), fill=(0, 0, 0, 255))
        img.save(out("ui", "ProstLeg_%s.png" % side))

# ------------------------------------------------------------------ main

PROST_LEG_BUILDERS = {"pegLeg": lambda b, sd, lv: peg_leg(b, sd, lv), "mechLeg": lambda b, sd, lv: mech_leg(b, sd, False, lv), "medicalLeg": lambda b, sd, lv: mech_leg(b, sd, True, lv)}
PROST_ARM_BUILDERS = {"pegArm": lambda b, sd, lv: peg_arm(b, sd, lv), "hookArm": lambda b, sd, lv: hook_arm(b, sd, lv), "normalArm": lambda b, sd, lv: mech_arm(b, sd, False, lv), "medicalArm": lambda b, sd, lv: mech_arm(b, sd, True, lv)}

def build_models():
    report = {}
    report["stumps"] = build_leg_stumps()
    bodies = {s: load_body(s) for s in ("Male", "Female")}
    for sex, body in bodies.items():
        sx = "M" if sex == "Male" else "F"
        for side in ("L", "R"):
            for lvl in LEG_LEVELS:
                for nm, fn in PROST_LEG_BUILDERS.items():
                    full = "%s%s_%s_%s" % (nm, lvl, side, sx)
                    report[full] = write_rigid(out("models_X", "Prosthesis", full + ".X"), full, "Prosthesis/" + nm, sex, body, fn(body, side, lvl))
            for lvl in ARM_LEVELS:
                for nm, fn in PROST_ARM_BUILDERS.items():
                    full = "%s%s_%s_%s" % (nm, lvl, side, sx)
                    report[full] = write_rigid(out("models_X", "Prosthesis", full + ".X"), full, "Prosthesis/" + nm, sex, body, fn(body, side, lvl))
            report["tourniquetLeg_%s_%s" % (side, sx)] = write_rigid(out("models_X", "Surgery", "TourniquetLeg_%s_%s.X" % (side, sx)), "TourniquetLeg_%s_%s" % (side, sx), "Surgery/tourniquetLeg", sex, body, leg_tourniquet(body, side))
    # modelos de suelo (estáticos): prótesis tumbadas = la pieza izquierda masculina girada
    body = bodies["Male"]
    def lay(mesh, rot_axis="z"):
        c = np.mean(mesh.v, axis=0)
        R = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float)
        m2 = mesh.transformed(lambda p: (p - c) @ R.T)
        mn = np.min(m2.v, axis=0); m2 = m2.transformed(lambda p: p - np.array([0, mn[1] - 0.002, 0]))
        m2.n = [n @ R.T for n in mesh.n]
        return m2
    ground = [(nm + "_Ground", fn(body, "L", ""), "Prosthesis/" + nm) for nm, fn in list(PROST_LEG_BUILDERS.items()) + list(PROST_ARM_BUILDERS.items())]
    ground.append(("TourniquetLeg_Ground", leg_tourniquet(body, "L"), "Surgery/tourniquetLeg"))
    for nm, mesh, tex in ground:
        folder = "Surgery" if "Tourniquet" in nm else "Prosthesis"
        report[nm] = write_static(out("models_X", folder, nm + ".X"), nm, tex, lay(mesh))
    # armas / herramientas
    report["Crutch"] = write_static(out("models_X", "Weapons", "Crutch.X"), "Crutch", "Weapons/crutch", crutch())
    report["BoneSaw"] = write_static(out("models_X", "Weapons", "BoneSaw.X"), "BoneSaw", "Weapons/bonesaw", bone_saw())
    for nm, mesh, tex in (("Crutch_Ground", crutch(), "Weapons/crutch"), ("BoneSaw_Ground", bone_saw(), "Weapons/bonesaw")):
        report[nm] = write_static(out("models_X", "Weapons", nm + ".X"), nm, tex, lay(mesh))
    # miembros cercenados (suelo)
    for part in ("Hand", "ForeArm", "UpperArm", "Foot", "LowerLeg", "UpperLeg"):
        texpart = {"Hand": "Hand", "ForeArm": "Forearm", "UpperArm": "Upperarm"}.get(part, part)
        report["Severed" + part] = write_static(out("models_X", "Severed", "Severed%s.X" % part), "Severed" + part, "Amputations/Human/%s/skin01_b" % texpart, severed_limb(body, "L", part))
    return report

def build_textures():
    build_stump_textures()
    tex_wood_leather(out("textures", "Prosthesis", "pegLeg.png"), 1)
    tex_wood_leather(out("textures", "Prosthesis", "pegArm.png"), 7)
    tex_metal(out("textures", "Prosthesis", "mechLeg.png"), 2, False)
    tex_metal(out("textures", "Prosthesis", "medicalLeg.png"), 3, True)
    tex_hook(out("textures", "Prosthesis", "hookArm.png"))
    tex_metal(out("textures", "Prosthesis", "normalArm.png"), 4, False)
    tex_metal(out("textures", "Prosthesis", "medicalArm.png"), 5, True, foot=(196, 190, 180, 255))
    tex_tourniquet_leg(out("textures", "Surgery", "tourniquetLeg.png"))
    tex_crutch(out("textures", "Weapons", "crutch.png"))
    tex_bonesaw(out("textures", "Weapons", "bonesaw.png"))

if __name__ == "__main__":
    what = sys.argv[2] if len(sys.argv) > 2 else "all"
    if what in ("all", "textures"): build_textures(); print("textures ok")
    if what in ("all", "icons"): build_icons(); build_overlays(); print("icons+overlays ok")
    if what in ("all", "models"):
        rep = build_models()
        for k, v in rep.items(): print(k, v)
