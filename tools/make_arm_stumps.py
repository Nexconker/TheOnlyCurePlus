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

def hidden_faces(body, masks):
    """Caras que el juego deja de dibujar con esas máscaras (mismo criterio que render_combos.body_mesh)."""
    UV = body["uvs"]; ms = [RC.mask_alpha(i) for i in masks]; out = []
    for f in body["faces"]:
        if BA.face_is_hidden(body, f): continue
        c = UV[list(f)].mean(0)
        px, py = int(np.clip(c[0] * 255, 0, 255)), int(np.clip(c[1] * 255, 0, 255))
        if any(m[py, px] > 0 for m in ms): out.append(f)
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

if __name__ == "__main__":
    build()
