"""Iconos de inventario renderizados desde los modelos .X del mod (rasterizador propio, sin Blender).
Salida: media/textures/Item_<Icon>.png a 32x32 con contorno oscuro, como los iconos vanilla.
Uso: python render_icons.py [ruta_media_del_mod] [--big]  (--big guarda también una lámina ampliada)"""
import os, sys, math
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzx
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MOD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")
TOC_UP = r"C:\Users\nexco\CODING PARCHEO\TOCPlus\upstream_2.4.0\42\media"
OUT = os.path.join(MOD, "textures")
SHEET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview", "icons_rendered.png")
RES = 192          # resolución de render antes de reducir
ICON = 32

# ------------------------------------------------------------------ carga

def find_mesh(n):
    for c in n.children:
        if c.type == "Mesh": return c
        r = find_mesh(c)
        if r: return r

def load_x(path):
    m = pzx.read_mesh(find_mesh(pzx.parse(path)))
    v = np.array(m["verts"], float); f = np.array([list(x) for x in m["faces"]], int)
    uv = np.array(m["uvs"], float) if m["uvs"] else np.zeros((len(v), 2))
    return v, f, uv

def smooth_normals(v, f):
    n = np.zeros_like(v)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3): np.add.at(n, f[:, k], fn)
    l = np.linalg.norm(n, axis=1); l[l == 0] = 1
    return n / l[:, None]

# ------------------------------------------------------------------ rasterizador

def rot(deg_x, deg_y, deg_z):
    ax, ay, az = map(math.radians, (deg_x, deg_y, deg_z))
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry

def render(v, f, uv, tex, R, size=RES, fill=0.86, light=(-0.45, 0.75, 0.5), ambient=0.55, spec=0.3, two_sided=True, bright=1.0):
    """Ortográfica mirando hacia -Z (z mayor = más cerca). Devuelve RGBA float (size,size,4)."""
    n = smooth_normals(v, f)
    vr = v @ R.T; nr = n @ R.T
    mn, mx = vr[:, :2].min(0), vr[:, :2].max(0)
    ext = max(mx - mn); s = size * fill / (ext if ext > 0 else 1)
    c = (mn + mx) / 2
    sx = (vr[:, 0] - c[0]) * s + size / 2
    sy = size / 2 - (vr[:, 1] - c[1]) * s
    sz = vr[:, 2] * s
    T = np.array(tex.convert("RGBA"), float) / 255.0
    th, tw = T.shape[:2]
    img = np.zeros((size, size, 4)); zbuf = np.full((size, size), -1e9)
    L = np.array(light, float); L /= np.linalg.norm(L)
    V = np.array([0, 0, 1.0])
    H = L + V; H /= np.linalg.norm(H)
    for tri in f:
        xs, ys, zs = sx[tri], sy[tri], sz[tri]
        x0, x1 = int(max(0, np.floor(xs.min()))), int(min(size - 1, np.ceil(xs.max())))
        y0, y1 = int(max(0, np.floor(ys.min()))), int(min(size - 1, np.ceil(ys.max())))
        if x1 < x0 or y1 < y0: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        def edge(ax, ay, bx, by, px, py): return (px - ax) * (by - ay) - (py - ay) * (bx - ax)
        area = edge(xs[0], ys[0], xs[1], ys[1], xs[2], ys[2])
        if abs(area) < 1e-9: continue
        w0 = edge(xs[1], ys[1], xs[2], ys[2], X, Y) / area
        w1 = edge(xs[2], ys[2], xs[0], ys[0], X, Y) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any(): continue
        z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        zb = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (z > zb)
        if not upd.any(): continue
        nn = w0[..., None] * nr[tri[0]] + w1[..., None] * nr[tri[1]] + w2[..., None] * nr[tri[2]]
        nn /= (np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9)
        if two_sided:
            flip = nn[..., 2] < 0
            nn[flip] = -nn[flip]
        u = w0 * uv[tri[0], 0] + w1 * uv[tri[1], 0] + w2 * uv[tri[2], 0]
        vv = w0 * uv[tri[0], 1] + w1 * uv[tri[1], 1] + w2 * uv[tri[2], 1]
        ti = np.clip((u % 1.0) * tw, 0, tw - 1).astype(int); tj = np.clip((vv % 1.0) * th, 0, th - 1).astype(int)
        col = T[tj, ti, :3]
        diff = np.clip(nn @ L, 0, 1)
        specv = np.clip(nn @ H, 0, 1) ** 24 * spec
        shade = ambient + 0.7 * diff
        rgb = np.clip((col * bright) * shade[..., None] + specv[..., None], 0, 1) ** 0.9
        out = img[y0:y1 + 1, x0:x1 + 1]
        out[upd, :3] = rgb[upd]; out[upd, 3] = 1.0
        zb[upd] = z[upd]
    return img

def to_icon(img, size=ICON, outline=(28, 18, 14), shadow=True, thicken=0):
    """Reduce con alfa premultiplicada, añade contorno de 1 px y un toque de contraste.
    thicken: engrosa (dilata) el render en píxeles de alta resolución para objetos finos."""
    rgba = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")
    if thicken > 0:
        k = thicken * 2 + 1
        rgb = im.convert("RGB").filter(ImageFilter.MaxFilter(k))
        a = im.split()[3].filter(ImageFilter.MaxFilter(k))
        base = np.array(im, float); grown = np.array(rgb, float); ga = np.array(a, float)
        keep = base[..., 3] > 0
        merged = np.where(keep[..., None], base[..., :3], grown)
        im = Image.fromarray(np.concatenate([merged, ga[..., None]], -1).astype(np.uint8), "RGBA")
    # premultiplicar para que el borde no se oscurezca al reducir
    arr = np.array(im, float); a = arr[..., 3:4] / 255.0
    pre = Image.fromarray(np.concatenate([arr[..., :3] * a, arr[..., 3:4]], -1).astype(np.uint8), "RGBA")
    small = pre.resize((size, size), Image.LANCZOS)
    s = np.array(small, float); a = s[..., 3:4] / 255.0
    rgb = np.where(a > 0.02, s[..., :3] / np.maximum(a, 0.02), 0)
    alpha = s[..., 3]
    # contraste suave
    rgb = np.clip((rgb - 128) * 1.08 + 128, 0, 255)
    # contorno: píxeles vacíos pegados a píxeles llenos
    filled = alpha > 110
    dil = np.zeros_like(filled)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            dil |= np.roll(np.roll(filled, dy, 0), dx, 1)
    ring = dil & ~filled
    outc = np.array(outline, float)
    rgb[ring] = outc; alpha[ring] = 255
    # bordes internos: oscurecer un poco los píxeles llenos que tocan el vacío (sombra de contorno)
    inner = filled & ~np.array([[all(filled[max(0, y - 1):y + 2, max(0, x - 1):x + 2].ravel()) for x in range(size)] for y in range(size)])
    rgb[inner] = rgb[inner] * 0.78
    alpha[filled] = 255
    out = np.concatenate([rgb, alpha[..., None]], -1).astype(np.uint8)
    return Image.fromarray(out, "RGBA")

# ------------------------------------------------------------------ mallas procedurales (kit, guía)

class M:
    def __init__(self): self.v, self.f, self.uv = [], [], []
    def box(self, c, s, uvrect):
        cx, cy, cz = c; sx, sy, sz = s[0] / 2, s[1] / 2, s[2] / 2
        u0, v0, u1, v1 = uvrect
        faces = [((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)), ((-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)),
                 ((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)), ((-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)),
                 ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1))]
        for corners in faces:
            b = len(self.v)
            for k, (a, bb, cc) in enumerate(corners):
                self.v.append([cx + a * sx, cy + bb * sy, cz + cc * sz]); self.uv.append([u0 if k in (0, 3) else u1, v0 if k in (0, 1) else v1])
            self.f += [[b, b + 1, b + 2], [b, b + 2, b + 3]]
    def box_uv_top(self, c, s, top_uv, side_uv):
        """Caja con la cara +Y (tapa) con su propia UV (portada) y el resto con otra."""
        cx, cy, cz = c; sx, sy, sz = s[0] / 2, s[1] / 2, s[2] / 2
        defs = [((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1), side_uv), ((-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1), side_uv),
                ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1), top_uv), ((-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1), side_uv),
                ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1), side_uv), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1), side_uv)]
        for corners in defs:
            u0, v0, u1, v1 = corners[4]; b = len(self.v)
            for k, (a, bb, cc) in enumerate(corners[:4]):
                self.v.append([cx + a * sx, cy + bb * sy, cz + cc * sz]); self.uv.append([u0 if k in (0, 3) else u1, v0 if k in (0, 1) else v1])
            self.f += [[b, b + 1, b + 2], [b, b + 2, b + 3]]
    def arrays(self): return np.array(self.v, float), np.array(self.f, int), np.array(self.uv, float)

def kit_model():
    m = M()
    m.box((0, 0.04, 0), (0.22, 0.08, 0.15), (0, 0.5, 1, 1))           # maletín (textura: mitad inferior)
    m.box((0, 0.082, 0), (0.20, 0.004, 0.13), (0, 0, 1, 0.5))         # tapa (textura: mitad superior con cruz)
    m.box((0, 0.09, -0.02), (0.07, 0.012, 0.025), (0.9, 0.9, 1, 1))   # asa
    m.box((0, 0.045, -0.077), (0.03, 0.02, 0.006), (0.9, 0.9, 1, 1))  # cierre
    return m.arrays()

def kit_texture():
    im = Image.new("RGBA", (128, 128), (225, 226, 228, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 64, 128, 128), fill=(205, 207, 210, 255))
    for y in range(66, 128, 8): d.line((0, y, 128, y), fill=(190, 192, 196, 255))
    d.rectangle((0, 0, 128, 64), fill=(238, 238, 240, 255))
    d.rectangle((56, 10, 72, 54), fill=(205, 30, 30, 255)); d.rectangle((42, 24, 86, 40), fill=(205, 30, 30, 255))
    d.rectangle((115, 115, 128, 128), fill=(70, 70, 75, 255))
    return im

def guide_model():
    m = M()
    m.box_uv_top((0, 0.005, 0), (0.21, 0.01, 0.28), (0, 0, 1, 0.78), (0, 0.8, 1, 1))
    return m.arrays()

def guide_texture():
    im = Image.new("RGBA", (256, 256), (236, 230, 214, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 205, 256, 256), fill=(225, 220, 205, 255))          # canto de páginas
    for x in range(0, 256, 3): d.line((x, 206, x, 256), fill=(210, 204, 190, 255))
    d.rectangle((0, 0, 256, 42), fill=(150, 25, 25, 255))                # banda de título
    try:
        font = ImageFont.truetype("arialbd.ttf", 22); small = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        font = ImageFont.load_default(); small = font
    d.text((12, 9), "FIELD AMPUTATION", font=font, fill=(245, 235, 225, 255))
    d.text((12, 48), "A survivor's guide", font=small, fill=(90, 60, 50, 255))
    # ilustración: brazo con línea de corte y sierra
    d.rounded_rectangle((40, 95, 190, 135), 18, fill=(222, 184, 150, 255), outline=(120, 90, 70, 255), width=2)
    d.line((150, 85, 150, 145), fill=(190, 30, 30, 255), width=4)
    d.rectangle((60, 150, 200, 160), fill=(150, 150, 155, 255)); d.rectangle((60, 160, 200, 164), fill=(230, 230, 235, 255))
    for x in range(62, 200, 6): d.polygon(((x, 164), (x + 3, 169), (x + 6, 164)), fill=(230, 230, 235, 255))
    d.rectangle((36, 148, 60, 166), fill=(110, 70, 40, 255))
    d.rectangle((0, 180, 256, 183), fill=(150, 25, 25, 255))
    d.text((12, 186), "Tourniquet. Cut. Tie. Bandage.", font=small, fill=(70, 50, 40, 255))
    return im

# ------------------------------------------------------------------ lista de iconos

def tex(path): return Image.open(path).convert("RGBA")

def skin_tex(part): return tex(os.path.join(MOD, "textures", "Amputations", "Human", part, "skin01_b.png"))

MX = os.path.join(MOD, "models_X")
ITEMS = [
    # nombre, modelo, textura, rot(x,y,z), fill, bright, thicken
    ("Crutch",      os.path.join(MX, "Weapons", "Crutch.X"),             tex(os.path.join(MOD, "textures", "Weapons", "crutch.png")),   (6, 90, -30),   0.95, 1.1, 3, 3.0),
    ("PegArm",      os.path.join(MX, "Prosthesis", "pegArm_L_M.X"),      tex(os.path.join(MOD, "textures", "Prosthesis", "pegArm.png")), (22, 0, -40),  0.9, 1.35, 0),
    ("HookArm",     os.path.join(MX, "Prosthesis", "hookArm_L_M.X"),     tex(os.path.join(MOD, "textures", "Prosthesis", "hookArm.png")), (22, 0, -40),  0.9, 1.3, 1),
    ("MechArm",     os.path.join(MX, "Prosthesis", "normalArm_L_M.X"),   tex(os.path.join(MOD, "textures", "Prosthesis", "normalArm.png")), (22, 0, -40), 0.9, 1.3, 1),
    ("MedicalArm",  os.path.join(MX, "Prosthesis", "medicalArm_L_M.X"),  tex(os.path.join(MOD, "textures", "Prosthesis", "medicalArm.png")), (22, 0, -40), 0.9, 1.6, 0),
    ("PegLeg",      os.path.join(MX, "Prosthesis", "pegLeg_L_M.X"),      tex(os.path.join(MOD, "textures", "Prosthesis", "pegLeg.png")), (12, 35, 8),   0.9, 1.35, 2),
    ("MechLeg",     os.path.join(MX, "Prosthesis", "mechLeg_L_M.X"),     tex(os.path.join(MOD, "textures", "Prosthesis", "mechLeg.png")), (12, 35, 8),  0.9, 1.25, 2),
    ("MedicalLeg",  os.path.join(MX, "Prosthesis", "medicalLeg_L_M.X"),  tex(os.path.join(MOD, "textures", "Prosthesis", "medicalLeg.png")), (12, 35, 8), 0.9, 1.6, 0),
    ("CyberLeg",    os.path.join(MX, "Prosthesis", "cyberLeg_L_M.X"),    tex(os.path.join(MOD, "textures", "Prosthesis", "cyberArm.png")), (12, 35, 8),  0.9, 1.3, 1),
    ("LegTourniquet", os.path.join(MX, "Surgery", "TourniquetLeg_Ground.X"), tex(os.path.join(MOD, "textures", "Surgery", "tourniquetLeg.png")), (62, 15, 0), 0.9, 1.1, 2),
    ("SeveredHand",  os.path.join(MX, "Severed", "SeveredHand.X"),      skin_tex("Hand"),      (35, 25, -20), 0.88, 1.1, 0),
    ("SeveredForeArm", os.path.join(MX, "Severed", "SeveredForeArm.X"), skin_tex("Forearm"),   (35, 25, -25), 0.9, 1.1, 0),
    ("SeveredUpperArm", os.path.join(MX, "Severed", "SeveredUpperArm.X"), skin_tex("Upperarm"), (35, 25, -25), 0.9, 1.1, 0),
    ("SeveredFoot",  os.path.join(MX, "Severed", "SeveredFoot.X"),      skin_tex("Foot"),      (30, 40, -15), 0.88, 1.1, 0),
    ("SeveredLowerLeg", os.path.join(MX, "Severed", "SeveredLowerLeg.X"), skin_tex("LowerLeg"), (35, 25, -25), 0.9, 1.1, 0),
    ("SeveredUpperLeg", os.path.join(MX, "Severed", "SeveredUpperLeg.X"), skin_tex("UpperLeg"), (35, 25, -25), 0.9, 1.1, 0),
]

def medical_arm_icon():
    """Mismo modelo que el brazo mecánico de TOC (FBX, no se puede leer): recolor del icono original a carbono."""
    im = Image.open(os.path.join(TOC_UP, "textures", "item_armProsthetic.png")).convert("RGBA")
    a = im.split()[3]; g = np.array(im.convert("L"), float)
    rgb = np.stack([g * 0.30 + 14, g * 0.31 + 16, g * 0.34 + 22], -1)
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA"); out.putalpha(a)
    d = ImageDraw.Draw(out); d.line((9, 13, 23, 13), fill=(215, 215, 220, 255), width=1)
    return out

def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    # sierra de hueso: misma malla que el modelo pero con los dientes exagerados para que se lean a 32 px
    import build_assets as BA
    saw = BA.bone_saw(teeth_scale=3.0, teeth_n=7, teeth_w=0.014)
    v, f, uv = np.array(saw.v, float), np.array(saw.f, int), np.array(saw.uv, float)
    ic = to_icon(render(v, f, uv, tex(os.path.join(MOD, "textures", "Weapons", "bonesaw.png")), rot(10, -90, 45), fill=0.93, bright=1.05), thicken=1)
    ic.save(os.path.join(OUT, "Item_BoneSaw.png")); results.append(("BoneSaw", ic)); print("icon BoneSaw (exaggerated teeth)")
    for item in ITEMS:
        name, path, texture, r, fill, bright, thick = item[:7]
        xz = item[7] if len(item) > 7 else 1.0
        v, f, uv = load_x(path)
        if xz != 1.0:
            c = v.mean(0); v = v.copy(); v[:, 0] = c[0] + (v[:, 0] - c[0]) * xz; v[:, 2] = c[2] + (v[:, 2] - c[2]) * xz
        img = render(v, f, uv, texture, rot(*r), fill=fill, bright=bright)
        ic = to_icon(img, thicken=thick)
        ic.save(os.path.join(OUT, "Item_%s.png" % name)); results.append((name, ic))
        print("icon", name)
    v, f, uv = kit_model(); ic = to_icon(render(v, f, uv, kit_texture(), rot(35, -30, 0)))
    ic.save(os.path.join(OUT, "Item_SurgicalKit.png")); results.append(("SurgicalKit", ic))
    v, f, uv = guide_model(); ic = to_icon(render(v, f, uv, guide_texture(), rot(55, 0, -20), fill=0.92))
    ic.save(os.path.join(OUT, "Item_FieldSurgeryGuide.png")); results.append(("FieldSurgeryGuide", ic))
    # lámina ampliada x3 para revisar
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    sheet = Image.new("RGBA", (104 * len(results), 120), (60, 60, 60, 255)); d = ImageDraw.Draw(sheet)
    for i, (n, ic) in enumerate(results):
        sheet.paste(ic.resize((96, 96), Image.NEAREST), (i * 104 + 4, 4)); d.text((i * 104 + 4, 104), n[:14], fill=(255, 255, 255, 255))
    sheet.save(SHEET); print("sheet", SHEET)

if __name__ == "__main__":
    main()
