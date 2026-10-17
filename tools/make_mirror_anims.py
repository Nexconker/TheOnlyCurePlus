"""Mano fantasma (3.2.0, comentario del Workshop: "when I took some painkillers, they did it with their ghost left hand").
Crea versiones ESPEJADAS (izquierda <-> derecha) de los clips de las acciones de una mano y nodos de animación que las
usan cuando falta la mano que usa la acción:
  - media/anims_X/Bob/TOC_Mirror_<clip>.X       (mismo archivo que el vanilla con el AnimationSet recalculado)
  - media/AnimSets/player/actions/TOC_NoHand<L|R>_<nodo>.xml
    = el nodo vanilla con la herencia x_extends resuelta y UNA condición más (TOC_NoHandL / TOC_NoHandR = true); los de
    la mano que falta con el clip espejado y los huesos L/R y Prop1/Prop2 intercambiados, sus hermanos del mismo
    PerformingAction con su clip (ver families()). El juego elige el nodo con más condiciones cumplidas
    (AnimNode.compareSelectionConditions: m_ConditionPriority, luego número de condiciones): con la variable puesta gana
    la copia, sin ella falla y queda el vanilla. La variable la pone TOC/Plus/GhostHand.lua.

Espejo: plano x = 0 del espacio del modelo (S = diag(-1, 1, 1)). Para cada hueso b y su pareja m(b):
    W'_m = Wb_m · S · inv(Wb_b) · W_b · S          (vectores fila, W = matriz mundo, Wb = bind)
así la malla pesada a m(b) queda como el espejo de la pesada a b, y en bind no cambia nada. Bind: el del cuerpo
(inversa de los offsets de MaleBody.X; los "Frame" de cada clip son su primer fotograma, no el bind). Prop1/Prop2
(objetos en la mano, hijos de Bip01): bind = relación estándar con su mano (Bob_Idle), así el objeto espejado va en la
otra mano como el juego lo pone en esa mano. Huesos centrales sin offset (Dummy01, Bip01, Translation_Data, Body):
referencia = Bob_Idle en t = 0.
Uso: python make_mirror_anims.py [--test]"""
import os, sys, re, json, math
TEST = "--test" in sys.argv
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import xml.etree.ElementTree as ET
import pose_x as P
import build_assets as BA

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(P.ANIMS)
ACT = os.path.join(GAME, "AnimSets", "player", "actions")
MEDIA = os.path.join(BA.MOD)
OUT_ANIM = os.path.join(MEDIA, "anims_X", "Bob")
OUT_NODE = os.path.join(MEDIA, "AnimSets", "player", "actions")
PREFIX = "TOC_Mirror_"

# nodo -> mano que usa (medido con analyze_action_hands.py: recorrido de cada mano respecto al pecho y distancia a la
# cabeza). Fuera a propósito: vendar un brazo concreto, colgar en un cinturón/funda de un lado, recargas de armas,
# trabajos a dos manos y los de movimiento mínimo (Making/Craft).
SELECTED = {
    # mano izquierda
    "TakePills": "L", "TakePills_Sneaking": "L", "TakePills_SneakingLow": "L",
    "Smoke": "L", "SmokePipe": "L",
    "Eat1Hand": "L", "Eat1HandSmallFood": "L", "EatOffStick": "L",
    "DrinkTeacup": "L", "DrinkPopCan": "L", "DrinkFromCan": "L", "DrinkFromCan2": "L", "DrinkFromCan2_food": "L",
    "DrinkBottle": "L", "DrinkBleach": "L", "DrinkFromBourbon": "L",
    # mano derecha
    "DrinkTapWater": "R", "EatFromCan": "R", "EatFromPlate": "R", "EatFromPlateHand": "R", "EatFromPacket": "R",
    "EatFromPacket_Sitting": "R", "DrinkFromBowlSpoon": "R", "book": "R", "OpenTinCan": "R", "OpenBeerBottle": "R",
    "Pour": "R", "PourMug": "R", "PourKettle": "R", "RollDice": "R", "painting": "R", "SniffCorrectionFluid": "R",
}

def swap_name(s):
    s = re.sub(r"Bip01_([LR])_", lambda m: "Bip01_%s_" % ("R" if m.group(1) == "L" else "L"), s)
    return re.sub(r"Bip01_Prop([12])", lambda m: "Bip01_Prop%s" % ("2" if m.group(1) == "1" else "1"), s)

# ------------------------------------------------------------------ cuaterniones (convención de pose_x.quat_to_matrix)
def quat_from_matrix(m):
    """q (w, x, y, z) tal que pose_x.quat_to_matrix(q) == m (3x3)."""
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; q = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; q = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; q = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    q = np.array(q); return q / np.linalg.norm(q)

def decompose(L):
    """local (fila) = Sc · R · T  ->  escala, cuaternión, traslación."""
    M = L[:3, :3]; sc = np.linalg.norm(M, axis=1)
    R = M / sc[:, None]
    return sc, quat_from_matrix(R), L[3, :3].copy()

# ------------------------------------------------------------------ bind
_body = BA.load_body("Male")
BIND = {b: np.linalg.inv(np.array(o, float).reshape(4, 4)) for b, o in _body["offsets"].items()}
_idle = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X"))
_Wi = P.worlds_at(_idle, 0, False)
for b, W in _Wi.items():
    if b in BIND: continue
    if b in ("Bip01_Prop1", "Bip01_Prop2"):
        hand = "Bip01_R_Hand" if b == "Bip01_Prop1" else "Bip01_L_Hand"
        BIND[b] = (W @ np.linalg.inv(_Wi[hand])) @ BIND[hand]      # relación estándar con su mano, sobre el bind de la mano
    else:
        BIND[b] = W
S = np.diag([-1.0, 1.0, 1.0, 1.0])

def mirrored_worlds(W):
    out = {}
    for b, Wb_ in W.items():
        m = swap_name(b)
        if m not in W: m = b
        out[m] = BIND[m] @ S @ np.linalg.inv(BIND[b]) @ Wb_ @ S
    return out

# ------------------------------------------------------------------ escribir el clip
def fmt(x): return ("%.6f" % x).replace("-0.000000", "0.000000")

def write_clip(src, dst, set_name, mirror=True):
    c = P.load_clip(src)
    order = list(c["bones"])
    times = sorted({t for kk in c["keys"].values() for k in kk.values() for t, _ in k})
    keys = {b: [] for b in order}
    prevq = {}
    for t in times:
        W = P.worlds_at(c, t, False)
        Wm = mirrored_worlds(W) if mirror else W
        for b in order:
            par = c["bones"][b]["parent"]
            L = Wm[b] @ np.linalg.inv(Wm[par]) if par else Wm[b]
            sc, q, tr = decompose(L)
            if b in prevq and np.dot(prevq[b], q) < 0: q = -q
            prevq[b] = q
            keys[b].append((t, sc, q, tr))
    text = open(src, encoding="utf-8", errors="ignore").read()
    i = text.index("AnimTicksPerSecond  {") if "AnimTicksPerSecond  {" in text else text.index("AnimTicksPerSecond {")
    out = [text[:i], "AnimTicksPerSecond  {\n %d;\n}\n\nAnimationSet %s {\n" % (c["ticks"], set_name)]
    for b in order:
        if b not in c["keys"]: continue                 # mismo conjunto de huesos animados que el original
        ks = keys[b]
        out.append(" \n Animation {\n  \n  { %s }\n\n" % b)
        for kname, ktype, n, get in (("S", 1, 3, lambda k: k[1]), ("R", 0, 4, lambda k: k[2]), ("T", 2, 3, lambda k: k[3])):
            out.append("  AnimationKey %s {\n   %d;\n   %d;\n" % (kname, ktype, len(ks)))
            rows = ["   %d;%d;%s;;" % (int(round(k[0])), n, ",".join(fmt(v) for v in get(k))) for k in ks]
            out.append(",\n".join(rows) + ";\n  }\n\n")
        out.append(" }\n")
    out.append("}\n")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8", newline="\n").write("".join(out))

# ------------------------------------------------------------------ nodos
def resolve_into(parent, child):
    """PZXmlUtil.resolve: atributos del hijo pisan; cada elemento hijo se fusiona con el del padre de igual etiqueta y
    x_name (o, sin x_name, el de igual posición entre los de su etiqueta); los que no casan se añaden al final."""
    res = ET.Element(parent.tag, dict(parent.attrib)); res.attrib.update(child.attrib)
    if len(parent) == 0 and len(child) == 0:
        res.text = child.text if child.text is not None else parent.text
        return res
    def entries(el):
        cnt, out = {}, []
        for e in el:
            nm = e.get("x_name") or ""
            key = (e.tag, nm) if nm else (e.tag, "#%d" % cnt.get(e.tag, 0))
            cnt[e.tag] = cnt.get(e.tag, 0) + 1
            out.append((key, e))
        return out
    pe = entries(parent); idx = {k: i for i, (k, _) in enumerate(pe)}
    merged = [e for _, e in pe]
    for k, e in entries(child):
        if k in idx: merged[idx[k]] = resolve_into(merged[idx[k]], e)
        else: merged.append(e)
    for e in merged: res.append(e)
    return res

def load_node(path):
    root = ET.parse(path).getroot()
    ext = root.get("x_extends")
    if ext:
        base = load_node(os.path.join(os.path.dirname(path), ext))
        root = resolve_into(base, root)
        root.attrib.pop("x_extends", None)
    return root

def node_conditions(root):
    out = []
    for c in root.findall("m_Conditions"):
        out.append(((c.findtext("m_Name") or "").strip(), (c.findtext("m_Value") or c.findtext("m_StringValue") or "").strip()))
    return out

def family_node(name, hand, mirror):
    """Copia del nodo vanilla con la condición TOC_NoHand<hand> = true. mirror: clip espejado y huesos L/R cambiados
    (el nodo usa la mano que falta); si no, el mismo clip (hermano del grupo que debe seguir ganando como en vanilla)."""
    root = load_node(os.path.join(ACT, name + ".xml"))
    clips = []
    for el in root.iter():
        if el.tag == "m_AnimName" and el.text and el.text.strip():
            clips.append(el.text.strip())
            if mirror: el.text = PREFIX + el.text.strip()
        elif mirror and el.text and el.tag != "m_Name":
            el.text = swap_name(el.text)
    root.find("m_Name").text = "TOC_NoHand%s_%s" % (hand, name)
    cond = ET.SubElement(root, "m_Conditions")
    for tag, val in (("m_Name", "TOC_NoHand" + hand), ("m_Type", "BOOL"), ("m_Value", "true")):
        ET.SubElement(cond, tag).text = val
    # las condiciones juntas, antes de eventos y pesos (como en los nodos del juego)
    conds = [e for e in root if e.tag == "m_Conditions"]
    for e in conds: root.remove(e)
    first = next((i for i, e in enumerate(root) if e.tag in ("m_Events", "m_SubStateBoneWeights", "m_Transitions")), len(root))
    for j, e in enumerate(conds): root.insert(first + j, e)
    ET.indent(root, space="\t")
    txt = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
    open(os.path.join(OUT_NODE, "TOC_NoHand%s_%s.xml" % (hand, name)), "w", encoding="utf-8", newline="\n").write(txt)
    return clips

def families():
    """Por cada mano, los grupos (mismo PerformingAction) con algún nodo seleccionado para esa mano: TODOS sus nodos con
    clip se copian con la condición extra. Así, con la variable puesta, el grupo entero sube +1 condición y el orden del
    juego entre hermanos se mantiene (si sólo se copiara el espejado, empataría con hermanos más específicos: p. ej. el
    espejo de Eat1Hand, el nodo por defecto, con EatFromCan; el juego no define quién gana un empate)."""
    groups, has_anim = {}, {}
    for f in sorted(os.listdir(ACT)):
        if not f.endswith(".xml"): continue
        n = f[:-4]
        r = load_node(os.path.join(ACT, f))
        pa = next((v.lower() for k, v in node_conditions(r) if k == "PerformingAction"), None)
        groups.setdefault(pa, []).append(n)
        has_anim[n] = any(e.text and e.text.strip() for e in r.iter("m_AnimName"))
    out = {"L": [], "R": []}
    for hand in "LR":
        sel = [n for n, h in SELECTED.items() if h == hand]
        gs = sorted({next(g for g, ns in groups.items() if n in ns) for n in sel}, key=str)
        for g in gs:
            for n in groups[g]:
                if has_anim[n]: out[hand].append((n, SELECTED.get(n) == hand))
    return out

def find_clip(name):
    for root, _, files in os.walk(os.path.join(P.ANIMS, "Bob")):
        for f in files:
            if os.path.splitext(f)[0].lower() == name.lower(): return os.path.join(root, f)
    return None

if __name__ == "__main__":
    if TEST:
        # 1) ida y vuelta sin espejo: el escritor reproduce el clip; 2) espejo del espejo = original
        src = find_clip("Bob_IdleTakePills"); tmp = os.path.join(HERE, "out", "mirror_test"); os.makedirs(tmp, exist_ok=True)
        write_clip(src, os.path.join(tmp, "same.X"), "same", mirror=False)
        write_clip(src, os.path.join(tmp, "m1.X"), "m1", mirror=True)
        write_clip(os.path.join(tmp, "m1.X"), os.path.join(tmp, "m2.X"), "m2", mirror=True)
        a, b, c2 = (P.load_clip(p) for p in (src, os.path.join(tmp, "same.X"), os.path.join(tmp, "m2.X")))
        T = max(k[-1][0] for kk in a["keys"].values() for k in kk.values())
        for nm, other in (("ida y vuelta", b), ("espejo x2", c2)):
            err = 0
            for f in np.linspace(0, 1, 7):
                Wa, Wo = P.worlds_at(a, f * T, False), P.worlds_at(other, f * T, False)
                err = max(err, max(np.abs(Wa[k] - Wo[k]).max() for k in BIND if k in Wa))
            print("%s: error max %.5f" % (nm, err))
        m1 = P.load_clip(os.path.join(tmp, "m1.X")); W0 = P.worlds_at(m1, 0, False)
        print("mano izq. original vs der. espejada (x, y, z):", np.round(P.worlds_at(a, 0.3 * T, False)["Bip01_L_Hand"][3, :3], 3),
              np.round(P.worlds_at(m1, 0.3 * T, False)["Bip01_R_Hand"][3, :3], 3))
        sys.exit(0)
    os.makedirs(OUT_NODE, exist_ok=True); os.makedirs(OUT_ANIM, exist_ok=True)
    for f in os.listdir(OUT_NODE):          # regenerar desde cero los nodos propios
        if f.startswith(("TOC_NoHand", PREFIX)): os.remove(os.path.join(OUT_NODE, f))
    done = {}; nn = 0
    for hand, nodes in families().items():
        for node, mirror in nodes:
            clips = family_node(node, hand, mirror); nn += 1
            if not mirror: continue
            for cl in clips:
                if cl in done: continue
                src = find_clip(cl)
                if not src: print("  SIN CLIP", cl, "para", node); continue
                write_clip(src, os.path.join(OUT_ANIM, PREFIX + cl + ".X"), PREFIX + cl)
                done[cl] = src
            print("%s espejo  %-24s %s" % (hand, node, ", ".join(clips)))
    json.dump({"nodes": SELECTED, "clips": sorted(done)}, open(os.path.join(HERE, "out", "mirror_anims.json"), "w"), indent=1)
    print(nn, "nodos,", len(done), "clips ->", MEDIA)
