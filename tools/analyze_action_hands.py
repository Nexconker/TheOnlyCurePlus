"""Qué mano usa cada acción del jugador (3.2.0, "mano fantasma"): para cada nodo de media/AnimSets/player/actions (con
la herencia x_extends resuelta) carga su clip y mide cuánto se mueve cada mano respecto al pecho (Bip01_Spine1) y lo
cerca que llega de la cabeza. Salida: out/action_hands.json {nodo: {clip, L, R, head_L, head_R, activa}}.
Uso: python analyze_action_hands.py"""
import os, sys, json, re
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pose_x as P

GAME = os.path.dirname(P.ANIMS)
ACT = os.path.join(GAME, "AnimSets", "player", "actions")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "action_hands.json")

def node(path, seen=None):
    """Texto del nodo con la herencia aplicada (sólo lo que necesitamos: nombre del clip)."""
    s = open(path, encoding="utf-8-sig").read()
    m = re.search(r"<m_AnimName>([^<]*)</m_AnimName>", s)
    if m: return m.group(1).strip()
    e = re.search(r'x_extends="([^"]+)"', s)
    if e:
        base = os.path.join(os.path.dirname(path), e.group(1))
        if os.path.exists(base): return node(base)
    return None

def find_clip(name):
    for root, _, files in os.walk(P.ANIMS):
        for f in files:
            if os.path.splitext(f)[0].lower() == name.lower(): return os.path.join(root, f)
    return None

def measure(path):
    c = P.load_clip(path)
    T = max((k[-1][0] for kk in c["keys"].values() for k in kk.values()), default=0)
    pos = {"L": [], "R": []}; head = {"L": [], "R": []}
    for f in np.linspace(0, 1, 25):
        W = P.worlds_at(c, f * T, False)
        ch = W["Bip01_Spine1"]; inv = np.linalg.inv(ch)
        hd = W["Bip01_Head"][3, :3]
        for s in "LR":
            h = W["Bip01_%s_Hand" % s]
            pos[s].append((h @ inv)[3, :3]); head[s].append(np.linalg.norm(h[3, :3] - hd))
    out = {}
    for s in "LR":
        p = np.array(pos[s]); out[s] = float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())
        out["head_" + s] = float(min(head[s]))
    return out

res = {}
clips = {}
for f in sorted(os.listdir(ACT)):
    if not f.endswith(".xml"): continue
    name = node(os.path.join(ACT, f))
    if not name: continue
    clips.setdefault(name, []).append(os.path.splitext(f)[0])
print(len(clips), "clips distintos")
for name, nodes in sorted(clips.items()):
    path = find_clip(name)
    if not path: print("  sin clip:", name); continue
    try: m = measure(path)
    except Exception as e: print("  error", name, e); continue
    act = "L" if m["L"] > 2.0 * m["R"] else ("R" if m["R"] > 2.0 * m["L"] else "both")
    for n in nodes: res[n] = dict(clip=name, file=os.path.relpath(path, P.ANIMS), active=act, **{k: round(v, 3) for k, v in m.items()})
    print("%-34s %-5s L %.2f R %.2f  cabeza L %.2f R %.2f  %s" % (name[:34], act, m["L"], m["R"], m["head_L"], m["head_R"], ",".join(nodes)[:60]), flush=True)
json.dump(res, open(OUT, "w"), indent=1)
print("->", OUT)
