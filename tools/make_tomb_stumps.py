"""Submod "The Only Cure+ - TombBody fit": muñones hechos del cuerpo de Tomb's Player Body (en vez del vanilla), para que
cadera y hombro casen con su malla. PUBLICAR SÓLO CON PERMISO DE TOMB (su página prohíbe editar su mod sin permiso; estas
mallas salen de la suya). No se copia ninguna textura suya: los XML apuntan a las texturas del CUERPO del juego
(Body/MaleBody01...), así que con TombBody activo se ven las suyas (normal, DOLL o NUDE) y sin él las vanilla.

Diferencias con los muñones del mod principal (make_arm_stumps.py / build_assets.build_leg_stumps):
- caras: las de su pieza principal (sin su "membrana" transparente) con ALGÚN texel oculto por las máscaras;
- costura: sin alfa propio (la textura es la del cuerpo), el muñón va 1 mm HACIA DENTRO: donde el cuerpo sigue visible
  (y con la camiseta pintada) el cuerpo queda delante; donde las máscaras lo ocultan se ve el muñón;
- tapa: en la mano / el pie de su lado (build_assets.CAPS), que en la textura del cuerpo es piel: muñón cerrado, sin herida.
Uso: python make_tomb_stumps.py [carpeta del submod]  (necesita out/tomb/*.json de tomb_export.py)"""
import os, sys, json, uuid, re
_ARGV = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import build_assets as BA
import make_arm_stumps as MS
from tomb_common import tomb_main_faces

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = _ARGV[0] if _ARGV else os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlusTombBody")
MEDIA = os.path.join(SUB, "42", "media")
MAIN_CI = os.path.join(BA.MOD, "clothing", "clothingItems")
INSET = 0.0006            # ~1 mm (el cuerpo mide 0.98 u): el cuerpo visible siempre por delante del muñón
LEG_MASKS = {"Foot": {"L": (8,), "R": (10,)}, "LowerLeg": {"L": (7, 8), "R": (9, 10)}, "UpperLeg": {"L": (7, 8), "R": (9, 10)}}

def tomb_body(sex):
    """Cuerpo de Tomb en el espacio del juego, con vértices partidos por UV/normal (sus UV van por esquina)."""
    T = json.load(open(os.path.join(HERE, "out", "tomb", sex + ".json")))["meshes"][0]
    tv = np.load(os.path.join(HERE, "out", "tomb", sex + "_verts_pz.npy"))
    offsets = BA.load_body(sex)["offsets"]
    verts, uvs, nors, wts, faces, index = [], [], [], [], [], {}
    for k in tomb_main_faces(T["tris"], len(tv)):
        f = []
        for vi, (u, v), n in zip(T["tris"][k], T["uvs"][k], T["nors"][k]):
            n = np.array([n[0], n[2], n[1]]); n /= (np.linalg.norm(n) or 1)
            key = (vi, round(u, 5), round(v, 5))
            if key not in index:
                w = {b: x for b, x in T["weights"][vi].items() if b in offsets}
                tot = sum(w.values()) or 1
                index[key] = len(verts); verts.append(tv[vi]); uvs.append((u, 1 - v)); nors.append(n); wts.append({b: x / tot for b, x in w.items()})
            else:
                nors[index[key]] = nors[index[key]] + n
            f.append(index[key])
        # (x, y, z) de Blender -> (x, z, y) del juego es una reflexión: invierte el sentido de las caras. Se recupera
        # dándole la vuelta a cada triángulo (si no, el juego las ve de espaldas y el muñón no se dibuja).
        faces.append((f[0], f[2], f[1]))
    nors = np.array(nors); nors /= np.maximum(np.linalg.norm(nors, axis=1, keepdims=True), 1e-9)
    return {"verts": np.array(verts), "uvs": np.array(uvs), "weights": wts, "faces": faces, "normals": nors, "offsets": offsets, "sex": sex}

def faces_with_hidden_texels(body, masks):
    zone = MS.hidden_zone(masks); UV = body["uvs"]
    return [f for f in body["faces"] if (MS.tri_texels(UV[list(f)]) & zone).any()]

def finish(body, nv, nuv, nw, nf, n_cap_from):
    normals = MS.seam_normals(nv, nf, n_cap_from, body["verts"], body["normals"])
    nv = np.array(nv, float)
    nv[:n_cap_from] -= normals[:n_cap_from] * INSET
    return nv, nuv, nw, nf, normals

def write(name, sex, body, nv, nuv, nw, nf, normals):
    os.makedirs(os.path.join(MEDIA, "models_X", "Amputation"), exist_ok=True)
    MS.write(os.path.join(MEDIA, "models_X", "Amputation", name + ".X"), name, "Body/%s01" % ("MaleBody" if sex == "Male" else "FemaleBody"),
             sex, body, nv, nuv, nw, nf, normals)

def build_arms(sex, body, fit, report):
    for side in ("L", "R"):
        for part, cut in MS.ARM_CUTS.items():
            for prost in (False, True):
                if prost and part == "Hand": continue
                masks = MS.PROST_MASKS[side] if prost else MS.MASKS[part][side]
                c = MS.prost_cut(fit["bodies"][sex]["arms"][side], part) if prost else cut
                tmp = dict(body); tmp["verts"] = body["verts"][:, [1, 0, 2]].copy()
                nv, nuv, nw, nf, edge = BA.clip_mesh(tmp, faces_with_hidden_texels(body, masks), c if side == "L" else -c, keep_above=(side == "R"))
                n_cap_from = len(nv)
                nv, nuv, nw, nf = BA.add_cap(nv, nuv, nw, nf, edge, normal_down=(side == "L"), cap=BA.cap_for("Hand", side))
                nv = np.asarray(nv)[:, [1, 0, 2]].copy()
                name = "ArmStump%s_%s_%s_%s" % ("Prost" if prost else "", BA.SIDE_NAME[side], part, sex)
                write(name, sex, body, *finish(body, nv, nuv, nw, nf, n_cap_from))
                report.append((name, len(nf)))

def build_legs(sex, body, report):
    for side in ("L", "R"):
        for part, cut in BA.LEG_CUTS.items():
            nv, nuv, nw, nf, edge = BA.clip_mesh(body, faces_with_hidden_texels(body, LEG_MASKS[part][side]), cut, keep_above=True)
            n_cap_from = len(nv)
            nv, nuv, nw, nf = BA.add_cap(nv, nuv, nw, nf, edge, normal_down=True, cap=BA.cap_for("Foot", side))
            name = "Amputation_%s_%s_%s" % (BA.SIDE_NAME[side], part, sex)
            write(name, sex, body, *finish(body, nv, nuv, nw, nf, n_cap_from))
            report.append((name, len(nf)))

def body_textures():
    """Las 42 entradas en el orden de ItemsController.GetAmputationTexturesIndex / ZombieStumps.GetTextureIndex, pero
    apuntando a la textura del cuerpo: sangrante y cicatrizado son la misma (el muñón de Tomb no lleva herida pintada)."""
    tex = []
    for hairy in ("", "a", "", "a"):
        for i in range(1, 6): tex.append("Body\\MaleBody%02d%s" % (i, hairy))
    for _ in range(2):
        for i in range(1, 6): tex.append("Body\\FemaleBody%02d" % i)
    for z in range(1, 5):
        for l in range(1, 4): tex.append("Body\\M_ZedBody%02d_level%d" % (z, l))
    return tex

def write_xmls():
    """Mismos ítems, GUID, modelos y máscaras que el mod principal; sólo cambian las texturas."""
    out = os.path.join(MEDIA, "clothing", "clothingItems"); os.makedirs(out, exist_ok=True)
    rows = []
    for f in sorted(os.listdir(MAIN_CI)):
        if not f.startswith("Amputation_"): continue
        s = open(os.path.join(MAIN_CI, f), encoding="utf-8").read()
        s = re.sub(r"\s*<textureChoices>[^<]*</textureChoices>", "", s)
        s = s.replace("</clothingItem>", "".join("    <textureChoices>%s</textureChoices>\n" % t for t in body_textures()) + "</clothingItem>")
        s = s.replace("<m_Masks>", "<m_Masks>", 1)
        open(os.path.join(out, f), "w", encoding="utf-8", newline="\n").write(s)
        rows.append((f, re.search(r"<m_GUID>([^<]+)</m_GUID>", s).group(1)))
    L = ['<?xml version="1.0" encoding="utf-8"?>', "<fileGuidTable>"]
    for f, g in rows: L += ["    <files>", "        <path>media/clothing/clothingItems/%s</path>" % f, "        <guid>%s</guid>" % g, "    </files>"]
    L.append("</fileGuidTable>")
    open(os.path.join(MEDIA, "fileGuidTable.xml"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    return len(rows)

MOD_INFO = """name=The Only Cure+ - TombBody fit
poster=poster.png
icon=icon.png
description=Optional add-on for The Only Cure+ with Tomb's Player Body: stumps built on Tomb's body so hips and shoulders match it, using your body texture (normal, DOLL or NUDE). Load it after The Only Cure+ and Tomb's Player Body. Tomb's Player Body is by Tomb.
id=TheOnlyCurePlusTombBody
modversion=1.0.0
versionMin=42.20
require={req}
loadModAfter=\\TheOnlyCurePlus,\\TombBody,\\TombBodyTex,\\TombBodyTexDOLL,\\TombBodyTexNUDE
"""

def write_mod_info():
    import shutil
    for d, req in ((SUB, "TheOnlyCurePlus,TombBody"), (os.path.join(SUB, "42"), "\\TheOnlyCurePlus,\\TombBody")):
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "mod.info"), "w", encoding="utf-8", newline="\n").write(MOD_INFO.format(req=req))
        for img in ("poster.png", "icon.png"):
            src = os.path.join(os.path.dirname(BA.MOD), img)
            if os.path.exists(src): shutil.copy(src, os.path.join(d, img))

if __name__ == "__main__":
    fit = json.load(open(os.path.join(HERE, "out", "fit.json"), encoding="utf-8"))
    report = []
    for sex in ("Male", "Female"):
        body = tomb_body(sex)
        build_arms(sex, body, fit, report)
        build_legs(sex, body, report)
    n = write_xmls(); write_mod_info()
    for r in report: print("%-40s %5d tris" % r)
    print(len(report), "modelos,", n, "XML ->", SUB)
