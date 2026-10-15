"""Parche puntual (2026-10-11): membrana por alfa de textura, encajes amplios, correas cerradas,
pie centrado en la caña, copa del brazo sobre la tapa del muñón, vistas con el frente real."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

def patch(path, pairs):
    p = os.path.join(HERE, path); s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            raise SystemExit("no encontrado en %s: %r" % (path, old[:60]))
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("patched", path)

OLD_LIMB = '''def limb_faces(body, bones):
    """Caras con algún vértice pesado a los huesos dados. Se excluyen las caras que tocan la
    membrana entre las piernas (vértices pesados a Bip01_Dress*): el juego no la dibuja y en un
    miembro suelto saldría como una aleta."""
    keep = []
    for f in body["faces"]:
        ws = [body["weights"][vi] for vi in f]
        if any("Dress" in b for w in ws for b in w):
            continue
        if any(any(b in w for b in bones) for w in ws):
            keep.append(f)
    return keep'''
NEW_LIMB = '''_hidden_alpha = None
def hidden_alpha():
    """Alfa de la textura del cuerpo: donde es 0 el juego no dibuja la cara (membrana entre las piernas)."""
    global _hidden_alpha
    if _hidden_alpha is None:
        im = Image.open(os.path.join(PZ, "textures", "Body", "MaleBody01.png")).convert("RGBA")
        _hidden_alpha = np.array(im.split()[3])
    return _hidden_alpha

def face_is_hidden(body, f):
    ws = [body["weights"][vi] for vi in f]
    if any("Dress" in b for w in ws for b in w): return True
    c = body["uvs"][list(f)].mean(0)
    a = hidden_alpha()
    px, py = int(np.clip(c[0] * 255, 0, 255)), int(np.clip(c[1] * 255, 0, 255))
    return a[py, px] < 8

def limb_faces(body, bones):
    """Caras con algún vértice pesado a los huesos dados, sin las caras que el juego no dibuja
    (membrana entre las piernas: pesos Bip01_Dress* o zona transparente de la textura)."""
    keep = []
    for f in body["faces"]:
        if face_is_hidden(body, f): continue
        ws = [body["weights"][vi] for vi in f]
        if any(any(b in w for b in bones) for w in ws):
            keep.append(f)
    return keep'''

OLD_PEG = '''    knee = o + Y * 0.02
    # copa de cuero alrededor de la rodilla/pantorrilla alta
    m.tube([knee, knee + down * 0.05, knee + down * 0.11], [(0.060, 0.070), (0.055, 0.064), (0.046, 0.054)], (X, Z), 16, "Bip01_%s_Calf" % side, (0, 1), (0.0, 0.25), close_start=True)
    # pata de madera, ligeramente cónica, hasta el suelo
    top = knee + down * 0.11
    m.tube([top, top + down * 0.10, np.array([top[0], 0.012, top[2]])], [(0.022, 0.022), (0.018, 0.018), (0.014, 0.014)], (X, Z), 12, "Bip01_%s_Calf" % side, (0, 1), (0.3, 0.9), close_start=True)
    # contera de goma
    tip = np.array([top[0], 0.012, top[2]])
    m.tube([tip, np.array([top[0], 0.0, top[2]])], [(0.017, 0.017), (0.015, 0.015)], (X, Z), 12, "Bip01_%s_Calf" % side, (0, 1), (0.92, 1.0), close_end=True)
    # correas (dos bandas horizontales sobre la copa)
    for yy in (0.03, 0.08):
        c = knee + down * yy
        m.tube([c + Y * 0.006, c - Y * 0.006], [(0.065, 0.075), (0.065, 0.075)], (X, Z), 16, "Bip01_%s_Calf" % side, (0, 1), (0.26, 0.29))
    return m'''
NEW_PEG = '''    bone = "Bip01_%s_Calf" % side
    top_y = 0.335                                      # por encima de la tapa del muñón (0.25-0.27)
    knee = np.array([o[0], top_y, o[2] + 0.025])       # centro del muslo bajo (el cuerpo tiene más carne atrás)
    # encaje de cuero largo: envuelve el muñón y, si sólo falta el pie, toda la pantorrilla
    pts = [knee, knee + down * 0.06, knee + down * 0.13, knee + down * 0.215]
    rad = [(0.075, 0.090), (0.068, 0.082), (0.058, 0.068), (0.046, 0.052)]
    m.tube(pts, rad, (X, Z), 18, bone, (0, 1), (0.0, 0.25), close_start=True, close_end=True)
    # correas cerradas (anillos un poco más anchos que el encaje)
    for d_, r in ((0.035, (0.072, 0.086)), (0.105, (0.063, 0.074)), (0.19, (0.050, 0.056))):
        c = knee + down * d_
        m.tube([c + Y * 0.008, c - Y * 0.008], [(r[0] + 0.004, r[1] + 0.004)] * 2, (X, Z), 18, bone, (0, 1), (0.26, 0.29), close_start=True, close_end=True)
    # pata de madera cónica desde el fondo del encaje hasta el suelo
    top = knee + down * 0.215
    m.tube([top, np.array([top[0], 0.06, top[2]]), np.array([top[0], 0.012, top[2]])], [(0.030, 0.030), (0.022, 0.022), (0.016, 0.016)], (X, Z), 12, bone, (0, 1), (0.3, 0.9), close_start=True)
    tip = np.array([top[0], 0.012, top[2]])
    m.tube([tip, np.array([top[0], 0.0, top[2]])], [(0.019, 0.019), (0.017, 0.017)], (X, Z), 12, bone, (0, 1), (0.92, 1.0), close_end=True)
    return m'''

NEW_MECH = '''def mech_leg(body, side, medical=False):
    o, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Calf" % side)
    fo, _, _, _ = bone_frame(body["offsets"], "Bip01_%s_Foot" % side)
    calf, foot = "Bip01_%s_Calf" % side, "Bip01_%s_Foot" % side
    m = MeshB(); down = -Y
    knee = np.array([o[0], 0.335, o[2] + 0.025])
    cx, cz = knee[0], knee[2]
    # encaje sobre el muñón
    m.tube([knee, knee + down * 0.05, knee + down * 0.10], [(0.074, 0.088), (0.068, 0.080), (0.060, 0.070)], (X, Z), 18, calf, (0, 1), (0.0, 0.2), close_start=True)
    if medical:
        # caña moldeada de carbono: envuelve la pantorrilla y se afina al tobillo
        pts = [knee + down * 0.10, knee + down * 0.15, knee + down * 0.20, np.array([cx, 0.085, cz])]
        m.tube(pts, [(0.060, 0.070), (0.052, 0.060), (0.044, 0.050), (0.036, 0.040)], (X, Z), 18, calf, (0, 1), (0.2, 0.8), close_end=True)
    else:
        # espinillera de chapa que envuelve la pantorrilla + dos barras laterales de acero a la vista
        pts = [knee + down * 0.10, knee + down * 0.17, np.array([cx, 0.085, cz])]
        m.tube(pts, [(0.058, 0.068), (0.050, 0.058), (0.040, 0.046)], (X, Z), 14, calf, (0, 1), (0.2, 0.8), close_end=True)
        for dx in (-0.058, 0.058):
            m.box((cx + dx, (knee[1] - 0.10 + 0.085) / 2, cz), (0.010, knee[1] - 0.10 - 0.085, 0.014), calf, (0.85, 0.2, 0.95, 0.8))
        m.tube([np.array([cx, 0.085, cz]), np.array([cx, 0.04, cz])], [(0.020, 0.020), (0.020, 0.020)], (X, Z), 10, calf, (0, 1), (0.8, 0.86))   # pistón
    # tobillo + pie, centrados en la caña (no en el hueso del pie, que está más afuera)
    ankle = np.array([cx, 0.085, cz])
    m.tube([ankle, np.array([cx, 0.035, cz])], [(0.028, 0.028), (0.030, 0.030)], (X, Z), 12, foot, (0, 1), (0.8, 0.86), close_start=True)
    # pie: del talón a la punta (el frente del cuerpo es -Z)
    m.box((cx, 0.02, fo[2] - 0.015), (0.056 if medical else 0.052, 0.038, 0.165), foot, (0.0, 0.86, 1.0, 1.0))
    if medical:
        m.box((cx, 0.009, fo[2] - 0.085), (0.052, 0.016, 0.045), foot, (0.0, 0.9, 0.5, 1.0))   # puntera flexible
    return m

'''

OLD_ARM = '''    start = o + axis * 0.02
    # copa de cuero sobre el antebrazo
    m.tube([start, start + axis * 0.05, start + axis * 0.10], [(0.040, 0.046), (0.037, 0.042), (0.032, 0.036)], (up, fwd), 14, bone, (0, 1), (0.0, 0.25), close_start=True)
    for d in (0.03, 0.08):
        c = start + axis * d
        m.tube([c - axis * 0.005, c + axis * 0.005], [(0.047, 0.052), (0.047, 0.052)], (up, fwd), 14, bone, (0, 1), (0.26, 0.29))
    # vástago de madera y "mano" de madera (bloque redondeado)
    s = start + axis * 0.10'''
NEW_ARM = '''    start = o - axis * 0.012          # desde el codo: la tapa del muñón (a ~0.027 del codo) queda dentro
    # copa de cuero que envuelve el muñón y el final del antebrazo
    m.tube([start, start + axis * 0.04, start + axis * 0.08, start + axis * 0.12], [(0.050, 0.056), (0.047, 0.053), (0.041, 0.046), (0.034, 0.038)], (up, fwd), 14, bone, (0, 1), (0.0, 0.25), close_start=True, close_end=True)
    for d, r in ((0.025, (0.052, 0.058)), (0.075, (0.045, 0.050))):
        c = start + axis * d
        m.tube([c - axis * 0.006, c + axis * 0.006], [(r[0] + 0.003, r[1] + 0.003)] * 2, (up, fwd), 14, bone, (0, 1), (0.26, 0.29), close_start=True, close_end=True)
    # vástago de madera y "mano" de madera (bloque redondeado)
    s = start + axis * 0.12'''

s = open(os.path.join(HERE, "build_assets.py"), encoding="utf-8").read()
a = s.index("def mech_leg(body, side, medical=False):"); b = s.index("def peg_arm(body, side):")
s = s[:a] + NEW_MECH + s[b:]
open(os.path.join(HERE, "build_assets.py"), "w", encoding="utf-8", newline="\n").write(s)
patch("build_assets.py", [(OLD_LIMB, NEW_LIMB), (OLD_PEG, NEW_PEG), (OLD_ARM, NEW_ARM)])
patch("render_combos.py", [
    ('VIEWS = [("frente", rot(0, 0, 0)), ("3/4", rot(0, -40, 0)), ("espalda", rot(0, 180, 0))]',
     'VIEWS = [("frente", rot(0, 180, 0)), ("3/4", rot(0, 140, 0)), ("espalda", rot(0, 0, 0))]'),
    ('''    for f in body["faces"]:
        if any("Dress" in b for vi in f for b in W[vi]): continue
        c = UV[list(f)].mean(0)''', '''    for f in body["faces"]:
        if BA.face_is_hidden(body, f): continue
        c = UV[list(f)].mean(0)'''),
])
patch("zoom_combos.py", [
    ('views=[("frente",rot(0,0,0)),("3/4",rot(0,-40,0)),("lado",rot(0,-90,0)),("espalda",rot(0,180,0))]',
     'views=[("frente",rot(0,180,0)),("3/4",rot(0,140,0)),("lado",rot(0,90,0)),("espalda",rot(0,0,0))]'),
    ('box=(360,120,720,330) if vn!="espalda" else (0,120,360,330)', 'box=(0,120,360,330) if vn!="espalda" else (360,120,720,330)'),
])
print("done")
