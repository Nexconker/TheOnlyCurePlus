"""Muñones de brazo hechos del propio cuerpo vanilla (como los de pierna), en lugar de los FBX del TOC original.

Por qué: la máscara de brazo del juego (CharacterMask LeftArm/RightArm) oculta desde casi el cuello (x = 0.03) hasta
la mano: hombro, parte del pecho y de la espalda. El FBX del TOC rehacía todo eso con su propia malla, normales y
textura, y en la costura del hombro salía una raya oscura (comentario de la ronda 2, 2026-10-14). Aquí el muñón son
EXACTAMENTE las caras que oculta la máscara (mismos vértices, normales, UV y pesos que el cuerpo), recortadas por el
plano del corte, más una tapa cuya UV cae en la zona libre donde va pintada la herida. Las texturas son las mismas
copias del cuerpo con herida que usan las piernas (Amputations/Human/LowerLeg/...): mismo orden de 42 entradas.

Uso: python make_arm_stumps.py  ->  models_X/Amputation/ArmStump_<Left|Right>_<Hand|ForeArm|UpperArm>_<Male|Female>.X"""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import build_assets as BA
import render_combos as RC

# |x| del corte en la pose de reposo (brazos en X). Brazo: 0.155 y no 0.118 (el del TOC): bajo la axila hay caras
# del torso dentro de la máscara hasta |x| = 0.134; un corte que las cruce deja huecos en la espalda y una tapa
# que une dos lazos (se veía como una solapa).
ARM_CUTS = {"Hand": 0.385, "ForeArm": 0.25, "UpperArm": 0.155}
MASKS = {"Hand": {"L": (4,), "R": (6,)}, "ForeArm": {"L": (3, 4), "R": (5, 6)}, "UpperArm": {"L": (3, 4), "R": (5, 6)}}

def tri_texels(uvs):
    """Texeles (256x256, como las máscaras) que cubre un triángulo en UV, bordes incluidos."""
    from PIL import Image, ImageDraw
    im = Image.new("L", (256, 256), 0)
    ImageDraw.Draw(im).polygon([(float(u * 255), float(v * 255)) for u, v in uvs], fill=255, outline=255)
    return np.array(im) > 0

def hidden_zone(masks, grow=1):
    """Lo que el juego deja sin piel: la máscara se aplica TEXEL a texel (alfa de la textura del cuerpo), no por caras.
    Se ensancha 1 texel para que muñón y cuerpo se solapen en la costura en vez de dejar una rendija."""
    from scipy.ndimage import binary_dilation
    z = np.zeros((256, 256), bool)
    for i in masks: z |= RC.mask_alpha(i) > 0
    return binary_dilation(z, iterations=grow) if grow else z

def hidden_faces(body, masks):
    """Caras con ALGÚN texel oculto por esas máscaras. Antes se miraba sólo el centro de la cara: en la costura del
    hombro unas 20 caras quedaban medio ocultas por el juego y fuera del muñón, y se veía el suelo a través
    (2026-10-14: "se corta un poco"). La parte de esas caras que el cuerpo sí dibuja va transparente en la textura del
    muñón (seam_alpha)."""
    UV = body["uvs"]; zone = hidden_zone(masks); out = []
    for f in body["faces"]:
        if BA.face_is_hidden(body, f): continue
        if (tri_texels(UV[list(f)]) & zone).any(): out.append(f)
    return out

def body_normals(sex):
    """Normales del .X del cuerpo vanilla (por vértice, alineadas con load_body)."""
    import pzx
    m = pzx.read_mesh(BA.find_mesh(pzx.parse(BA.BODY[sex])))
    n = np.array(m["normals"], float)
    assert len(n) == len(m["verts"]), "el cuerpo no trae una normal por vértice"
    return np.array(m["verts"], float), n / np.linalg.norm(n, axis=1, keepdims=True)

def seam_normals(nv, nf, n_cap_from, bverts, bnorms):
    """Normales del muñón: las del CUERPO en sus vértices (si se calculan sólo con las caras del muñón, en el borde
    no coinciden con las del torso y el juego dibuja una raya de luz/sombra en la costura del hombro); en los del
    corte, interpoladas de los vértices del cuerpo más cercanos; en la tapa, la normal de la propia tapa."""
    out = np.zeros((len(nv), 3))
    for i in range(min(n_cap_from, len(nv))):
        d = np.linalg.norm(bverts - nv[i], axis=1)
        k = np.argsort(d)[:3]
        if d[k[0]] < 1e-6:
            out[i] = bnorms[k[0]]
        else:
            w = 1.0 / np.maximum(d[k], 1e-6)
            v = (bnorms[k] * w[:, None]).sum(0); out[i] = v / (np.linalg.norm(v) or 1)
    if n_cap_from < len(nv):
        acc = np.zeros(3)
        for f in nf:
            if all(v >= n_cap_from for v in f):
                a, b, c = (nv[v] for v in f); acc += np.cross(b - a, c - a)
        acc /= (np.linalg.norm(acc) or 1)
        out[n_cap_from:] = acc
    return out

def write(path, name, texture, sex, body, verts, uvs, weights, faces, normals):
    import pzx
    wl = []
    for w in weights:
        ws = sorted(w.items(), key=lambda t: -t[1])[:4]
        tot = sum(x for _, x in ws) or 1
        wl.append([(b, x / tot) for b, x in ws])
    return pzx.write_skinned_x(BA.TEMPLATE[sex], path, name, texture, [BA.v3(v) for v in verts], [BA.v3(n) for n in normals],
                               [(float(u), float(v)) for u, v in uvs], [tuple(int(i) for i in f) for f in faces], wl, body["offsets"])

# ---------------- variantes "con prótesis" (modelo alternativo del muñón mientras se lleva una prótesis de brazo)
# La prótesis oculta el brazo entero del cuerpo (máscaras de brazo y mano) y el muñón pasa a este modelo: el brazo
# del cuerpo cortado 5 mm por DEBAJO del borde del encaje. Dentro del encaje no hay piel que pueda asomar en ninguna
# animación (2026-10-14: "hay algo de piel que se cuela en las prótesis").
PROST_MASKS = {"L": (3, 4), "R": (5, 6)}
TORSO_MAX_X = 0.136          # bajo la axila hay caras del torso dentro de la máscara hasta |x| = 0.134

def prost_cut(fit_arm, part):
    """|x| del corte bajo el borde del encaje de cada nivel (mismos t que blender_build)."""
    import numpy as np
    o, ax = np.array(fit_arm["o"]), np.array(fit_arm["axis"])
    if part == "Hand": return abs(o[0] + ax[0] * 0.075)               # brazal desde t = 0.07
    if part == "ForeArm": return abs(o[0] + ax[0] * (-0.010))         # encaje desde t = -0.015 (sobre el codo)
    up = fit_arm["upper"]; uo, uax = np.array(up["o"]), np.array(up["axis"])
    t0 = max(0.012, up["t_cut"] - 0.035)                               # build_upper_section: encaje desde t0
    return max(abs(uo[0] + uax[0] * (t0 + 0.005)), TORSO_MAX_X)

def build_prost_variants():
    import json
    fit = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "fit.json"), encoding="utf-8"))
    BODY_N = {sx: body_normals(sx) for sx in ("Male", "Female")}
    report = []
    for sex in ("Male", "Female"):
        body = BA.load_body(sex)
        for side in ("L", "R"):
            faces = hidden_faces(body, PROST_MASKS[side])
            for part in ("ForeArm", "UpperArm"):        # mano: sin variante (el antebrazo del cuerpo sigue visible)
                cut = prost_cut(fit["bodies"][sex]["arms"][side], part)
                tmp = dict(body); tmp["verts"] = body["verts"][:, [1, 0, 2]].copy()
                nv, nuv, nw, nf, edge = BA.clip_mesh(tmp, faces, cut if side == "L" else -cut, keep_above=(side == "R"))
                n_cap_from = len(nv)
                nv, nuv, nw, nf = BA.add_cap(nv, nuv, nw, nf, edge, normal_down=(side == "L"))
                nv = np.asarray(nv)[:, [1, 0, 2]].copy()
                bv, bn = BODY_N[sex]
                name = "ArmStumpProst_%s_%s_%s" % (BA.SIDE_NAME[side], part, sex)
                write(BA.out("models_X", "Amputation", name + ".X"), name, "Amputations/Human/LowerLeg/skin01_b",
                      sex, body, nv, nuv, nw, nf, seam_normals(nv, nf, n_cap_from, bv, bn))
                report.append((name, cut, len(nv), len(nf)))
    for r in report: print("%-38s corte |x| %.3f  %4d verts %4d tris" % r)

def build():
    report = []
    BODY_N = {sx: body_normals(sx) for sx in ("Male", "Female")}
    for sex in ("Male", "Female"):
        body = BA.load_body(sex)
        for side in ("L", "R"):
            for part, cut in ARM_CUTS.items():
                faces = hidden_faces(body, MASKS[part][side])
                # el recortador corta por Y: se intercambian X e Y y se deshace al final
                tmp = dict(body); tmp["verts"] = body["verts"][:, [1, 0, 2]].copy()
                cut_t = cut if side == "L" else -cut
                keep_above = (side == "R")                    # nos quedamos con el lado del cuerpo
                nv, nuv, nw, nf, edge = BA.clip_mesh(tmp, faces, cut_t, keep_above=keep_above)
                n_cap_from = len(nv)                          # add_cap añade la tapa al final
                # tapa hacia fuera del cuerpo (+X a la izquierda, -X a la derecha). add_cap orienta en el espacio
                # intercambiado, que es un reflejo: hay que pedirle la orientación contraria
                nv, nuv, nw, nf = BA.add_cap(nv, nuv, nw, nf, edge, normal_down=(side == "L"))
                nv = np.asarray(nv)[:, [1, 0, 2]].copy()
                name = "ArmStump_%s_%s_%s" % (BA.SIDE_NAME[side], part, sex)
                bv, bn = BODY_N[sex]
                normals = seam_normals(nv, nf, n_cap_from, bv, bn)
                write(BA.out("models_X", "Amputation", name + ".X"), name, "Amputations/Human/LowerLeg/skin01_b",
                      sex, body, nv, nuv, nw, nf, normals)
                report.append((name, len(nv), len(nf), len(edge)))
    for r in report: print("%-34s %4d verts %4d tris, borde %d" % r)

# ---------------- alfa de la costura en las texturas de muñón
# Las caras del borde (parte oculta, parte visible en el cuerpo) van enteras en el muñón; en su zona de la textura el
# alfa es la máscara: el muñón pinta sólo donde el cuerpo ya no pinta, y donde sigue el cuerpo se ve el cuerpo (y la
# camiseta pintada sobre él). Las texturas son las de la carpeta LowerLeg, compartidas con las piernas: sólo se tocan
# los texeles de esos triángulos, que están en la zona del brazo.
STUMP_TEX_DIRS = [("Human", "LowerLeg"), ("Zombie", "LowerLeg")]

def seam_alpha(verbose=True):
    import glob
    from PIL import Image
    import json
    fit = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "fit.json"), encoding="utf-8"))
    need_on = np.zeros((256, 256), bool); need_off = np.zeros((256, 256), bool)
    for sex in ("Male", "Female"):
        body = BA.load_body(sex); UV = body["uvs"]; X = body["verts"][:, 0]
        stumps = [(MASKS[p][s], s, c) for p, c in ARM_CUTS.items() for s in ("L", "R")]
        stumps += [(PROST_MASKS[s], s, prost_cut(fit["bodies"][sex]["arms"][s], p)) for p in ("ForeArm", "UpperArm") for s in ("L", "R")]
        for masks, side, cut in stumps:
            zone = hidden_zone(masks)
            for f in hidden_faces(body, masks):
                xs = X[list(f)]
                if not ((xs < cut).any() if side == "L" else (xs > -cut).any()): continue    # recortada por el corte
                t = tri_texels(UV[list(f)])
                if (t & ~zone).any():                         # cara de borde
                    need_on |= t & zone; need_off |= t & ~zone
                else:
                    need_on |= t
    # los muñones de pierna usan las mismas texturas: sus caras (y un texel alrededor, por el filtrado) siempre opacas
    import pzx
    from scipy.ndimage import binary_dilation
    legs = np.zeros((256, 256), bool)
    for p in glob.glob(os.path.join(BA.out("models_X", "Amputation", "x"), os.pardir, "Amputation_*.X")):
        m = pzx.read_mesh(BA.find_mesh(pzx.parse(p))); uv = np.array(m["uvs"], float)
        for f in m["faces"]: legs |= tri_texels(uv[list(f)])
    need_on |= binary_dilation(legs, iterations=1)
    off = need_off & ~need_on                                 # en caso de duda, opaco: mejor solape que agujero
    x, y, w, h = BA.PATCH
    assert not off[y:y + h, x:x + w].any(), "la costura toca la zona de la herida"
    n = 0
    for kind, part in STUMP_TEX_DIRS:
        for p in sorted(glob.glob(os.path.join(BA.out("textures", "Amputations", kind, part), "*.png"))):
            im = Image.open(p).convert("RGBA"); a = np.array(im)
            a[..., 3][off] = 0
            Image.fromarray(a).save(p); n += 1
    if verbose: print("alfa de costura: %d texeles transparentes, %d en conflicto (quedan opacos), %d texturas" % (off.sum(), (need_off & need_on).sum(), n))

if __name__ == "__main__":
    build()
    build_prost_variants()
    seam_alpha()
