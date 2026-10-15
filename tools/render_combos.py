"""Render de todas las combinaciones de muñones / prótesis / torniquetes sobre el personaje (sin la
membrana entre las piernas y ocultando las partes del cuerpo que el ítem enmascara, como hace el juego).
Salida: out/preview/combos_Male.png y combos_Female.png.  Uso: python render_combos.py [--size 220]"""
import os, sys, math
sys.path.insert(0, r"C:\Users\nexco\CODING PARCHEO\HerreriaPZ\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import pzx, fbx_min
import build_assets as BA
from render_icons import load_x, rot, smooth_normals

MOD = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"
PZ = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview")
SIZE = int(sys.argv[sys.argv.index("--size") + 1]) if "--size" in sys.argv else 220

MASK_FILES = {3: "LeftArm", 4: "LeftHand", 5: "RightArm", 6: "RightHand", 7: "LeftLeg", 8: "LeftFoot", 9: "RightLeg", 10: "RightFoot"}
_mask_cache = {}
def mask_alpha(idx):
    if idx not in _mask_cache:
        im = Image.open(os.path.join(PZ, "textures", "Body", "Masks", MASK_FILES[idx] + ".png")).convert("RGBA")
        _mask_cache[idx] = np.array(im.split()[3])
    return _mask_cache[idx]

def body_mesh(sex, hidden_masks):
    body = BA.load_body(sex)
    V, UV, W = body["verts"], body["uvs"], body["weights"]
    keep = []
    masks = [mask_alpha(i) for i in hidden_masks]
    for f in body["faces"]:
        if BA.face_is_hidden(body, f): continue
        c = UV[list(f)].mean(0)
        px, py = int(np.clip(c[0] * 255, 0, 255)), int(np.clip(c[1] * 255, 0, 255))
        if any(m[py, px] > 0 for m in masks): continue
        keep.append(f)
    tex = Image.open(os.path.join(PZ, "textures", "Body", ("MaleBody01" if sex == "Male" else "FemaleBody01") + ".png")).convert("RGBA")
    # la textura del cuerpo tiene zonas con alfa (membrana); forzamos opaco sobre gris para no ver a través
    bg = Image.new("RGBA", tex.size, (180, 150, 130, 255)); bg.alpha_composite(tex)
    return {"v": V, "f": np.array(keep, int), "uv": UV, "tex": bg}

def piece_x(path, tex):
    v, f, uv = load_x(path)
    return {"v": v, "f": f, "uv": uv, "tex": Image.open(tex).convert("RGBA")}

def piece_fbx(path, tex):
    out = []
    for m in fbx_min.load_meshes(path, mirror_z=True):
        out.append({"v": m["verts"], "f": m["faces"], "uv": m["uvs"], "tex": Image.open(tex).convert("RGBA")})
    return out

def rasterize(meshes, R, size, fill=0.9, light=(-0.4, 0.8, 0.6), ambient=0.5):
    """Varias mallas con su textura, z-buffer común. Devuelve RGBA uint8."""
    allv = np.vstack([m["v"] @ R.T for m in meshes])
    mn, mx = allv[:, :2].min(0), allv[:, :2].max(0)
    ext = max(mx - mn); s = size * fill / ext; c = (mn + mx) / 2
    img = np.zeros((size, size, 4)); zbuf = np.full((size, size), -1e9)
    L = np.array(light, float); L /= np.linalg.norm(L); H = L + np.array([0, 0, 1.0]); H /= np.linalg.norm(H)
    for m in meshes:
        v, f, uv = m["v"], m["f"], m["uv"]
        n = smooth_normals(v, f)
        vr = v @ R.T; nr = n @ R.T
        sx = (vr[:, 0] - c[0]) * s + size / 2; sy = size / 2 - (vr[:, 1] - c[1]) * s; sz = vr[:, 2] * s
        T = np.array(m["tex"], float) / 255.0; th, tw = T.shape[:2]
        for tri in f:
            xs, ys, zs = sx[tri], sy[tri], sz[tri]
            x0, x1 = int(max(0, np.floor(xs.min()))), int(min(size - 1, np.ceil(xs.max())))
            y0, y1 = int(max(0, np.floor(ys.min()))), int(min(size - 1, np.ceil(ys.max())))
            if x1 < x0 or y1 < y0: continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            def edge(ax, ay, bx, by, px, py): return (px - ax) * (by - ay) - (py - ay) * (bx - ax)
            area = edge(xs[0], ys[0], xs[1], ys[1], xs[2], ys[2])
            if abs(area) < 1e-9: continue
            w0 = edge(xs[1], ys[1], xs[2], ys[2], X, Y) / area; w1 = edge(xs[2], ys[2], xs[0], ys[0], X, Y) / area; w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any(): continue
            z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]; upd = inside & (z > zb)
            if not upd.any(): continue
            nn = w0[..., None] * nr[tri[0]] + w1[..., None] * nr[tri[1]] + w2[..., None] * nr[tri[2]]
            nn /= (np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9)
            flip = nn[..., 2] < 0; nn[flip] = -nn[flip]
            u = w0 * uv[tri[0], 0] + w1 * uv[tri[1], 0] + w2 * uv[tri[2], 0]
            vv = w0 * uv[tri[0], 1] + w1 * uv[tri[1], 1] + w2 * uv[tri[2], 1]
            ti = np.clip((u % 1.0) * tw, 0, tw - 1).astype(int); tj = np.clip((vv % 1.0) * th, 0, th - 1).astype(int)
            col = T[tj, ti, :3]
            shade = ambient + 0.65 * np.clip(nn @ L, 0, 1)
            spec = np.clip(nn @ H, 0, 1) ** 20 * 0.15
            rgb = np.clip(col * shade[..., None] + spec[..., None], 0, 1)
            out = img[y0:y1 + 1, x0:x1 + 1]; out[upd, :3] = rgb[upd]; out[upd, 3] = 1
            zb[upd] = z[upd]
    return (img * 255).astype(np.uint8)

# ------------------------------------------------------------------ combinaciones

UP = os.path.join(MOD, "models_X")          # los FBX originales de TOC están copiados en el mod
TX = os.path.join(MOD, "textures")

def combos(sex):
    sx = "M" if sex == "Male" else "F"
    S = {"Male": "Male", "Female": "Female"}[sex]
    fb = lambda rel, tex: ("fbx", os.path.join(UP, rel), os.path.join(TX, tex))
    xx = lambda rel, tex: ("x", os.path.join(UP, rel), os.path.join(TX, tex))
    armtex = lambda part: os.path.join("Amputations", "Human", part, "skin01_b.png")
    C = []
    # brazos (lado izquierdo). masks: 3 LeftArm, 4 LeftHand
    C.append(("Mano izq. amputada", [4], [fb("Amputation/Amputation_Left_Hand_%s.fbx" % S, armtex("Hand"))]))
    C.append(("Antebrazo izq. amputado", [3, 4], [fb("Amputation/Amputation_Left_LowerArm_%s.fbx" % S, armtex("Forearm"))]))
    C.append(("Brazo izq. amputado", [3, 4], [fb("Amputation/Amputation_Left_UpperArm_%s.fbx" % S, armtex("Upperarm"))]))
    for lbl, nm, tex in (("brazo de madera", "pegArm", "pegArm"), ("gancho", "hookArm", "hookArm"), ("brazo mecanico", "normalArm", "normalArm"), ("brazo medico", "medicalArm", "medicalArm")):
        C.append(("Antebrazo + " + lbl, [3, 4], [fb("Amputation/Amputation_Left_LowerArm_%s.fbx" % S, armtex("Forearm")), xx("Prosthesis/%s_L_%s.X" % (nm, sx), "Prosthesis/%s.png" % tex)]))
        C.append(("Mano izq. + " + lbl, [4], [fb("Amputation/Amputation_Left_Hand_%s.fbx" % S, armtex("Hand")), xx("Prosthesis/%sWrist_L_%s.X" % (nm, sx), "Prosthesis/%s.png" % tex)]))
    C.append(("Torniquete de brazo", [], [fb("Surgery/Tourniquet_Left.fbx", "Surgery/tourniquet.png")]))
    # piernas (lado izquierdo). masks: 7 LeftLeg, 8 LeftFoot
    C.append(("Pie izq. amputado", [8], [xx("Amputation/Amputation_Left_Foot_%s.X" % S, "Amputations/Human/Foot/skin01_b.png")]))
    C.append(("Pantorrilla izq. amputada", [7, 8], [xx("Amputation/Amputation_Left_LowerLeg_%s.X" % S, "Amputations/Human/LowerLeg/skin01_b.png")]))
    C.append(("Muslo izq. amputado", [7, 8], [xx("Amputation/Amputation_Left_UpperLeg_%s.X" % S, "Amputations/Human/UpperLeg/skin01_b.png")]))
    for lbl, nm in (("pata de palo", "pegLeg"), ("pierna mecanica", "mechLeg"), ("pierna medica", "medicalLeg")):
        C.append(("Pie izq. + " + lbl, [8], [xx("Amputation/Amputation_Left_Foot_%s.X" % S, "Amputations/Human/Foot/skin01_b.png"), xx("Prosthesis/%sAnkle_L_%s.X" % (nm, sx), "Prosthesis/%s.png" % nm)]))
        C.append(("Pantorrilla + " + lbl, [7, 8], [xx("Amputation/Amputation_Left_LowerLeg_%s.X" % S, "Amputations/Human/LowerLeg/skin01_b.png"), xx("Prosthesis/%s_L_%s.X" % (nm, sx), "Prosthesis/%s.png" % nm)]))
        C.append(("Muslo + " + lbl, [7, 8], [xx("Amputation/Amputation_Left_UpperLeg_%s.X" % S, "Amputations/Human/UpperLeg/skin01_b.png"), xx("Prosthesis/%sThigh_L_%s.X" % (nm, sx), "Prosthesis/%s.png" % nm)]))
    C.append(("Torniquete de pierna", [], [xx("Surgery/TourniquetLeg_L_%s.X" % sx, "Surgery/tourniquetLeg.png")]))
    C.append(("Cuerpo sin cambios", [], []))
    return C

VIEWS = [("frente", rot(0, 180, 0)), ("3/4", rot(0, 140, 0)), ("espalda", rot(0, 0, 0))]

def render_sex(sex):
    cs = combos(sex)
    cols = 6
    rows = math.ceil(len(cs) / cols)
    cell_w = SIZE * len(VIEWS) + 10; cell_h = SIZE + 28
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (52, 52, 56, 255)); d = ImageDraw.Draw(sheet)
    for i, (label, masks, pieces) in enumerate(cs):
        meshes = [body_mesh(sex, masks)]
        for kind, path, tex in pieces:
            try:
                if kind == "x": meshes.append(piece_x(path, tex))
                else: meshes += piece_fbx(path, tex)
            except Exception as e:
                print("WARN", label, os.path.basename(path), e)
        cx = (i % cols) * cell_w; cy = (i // cols) * cell_h
        for k, (vname, R) in enumerate(VIEWS):
            img = Image.fromarray(rasterize(meshes, R, SIZE), "RGBA")
            sheet.alpha_composite(img, (cx + k * SIZE, cy + 24))
        d.text((cx + 4, cy + 6), "%s" % label, fill=(255, 255, 255, 255))
        print("render", sex, label)
    out = os.path.join(OUTDIR, "combos_%s.png" % sex)
    sheet.save(out); print("saved", out)

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    for sex in ("Male", "Female"):
        render_sex(sex)
