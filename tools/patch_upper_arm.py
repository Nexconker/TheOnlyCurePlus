"""Prótesis por encima del codo (nivel "Upper", 3.1.0) en blender_build.py:
- upper_ring(): anillos del brazo superior (fit.json -> arms[side]["upper"]).
- build_upper_section(): encaje sobre el muñón del brazo + carcasa con la forma del brazo hasta el codo + correas +
  bisagra de codo en el eje real de flexión (pesado TODO al hueso del brazo: Bip01_X_UpperArm).
- arm_socket(level="Upper"): el antebrazo es entero protésico (carcasa del codo a la muñeca, hueso del antebrazo).
- build_saw_arm(level="Upper"): ídem para el brazo motosierra.
- el catálogo añade la sección superior a todo modelo de nivel Upper.
Uso: python patch_upper_arm.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "blender_build.py"); s = open(p, encoding="utf-8").read()

def patch(old, new, count=1):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new, count)

# ---------------- helpers del brazo superior (tras arm_ring)
patch('''def smooth_rings(rings, passes=1):''', '''def upper_ring(arm, t, clearance):
    """Anillo del brazo superior a distancia t del hombro (3.1.0, prótesis por encima del codo)."""
    up = arm["upper"]
    t = max(0.0, min(t, up["len"]))
    key = "%.3f" % (round(t / 0.005) * 0.005)
    if key not in up["rings"]: key = max(up["rings"], key=lambda k: -abs(float(k) - t))
    out = offset_ring(up["rings"][key], clearance)
    o, ax = Vector(up["o"]), Vector(up["axis"])
    return [tuple(Vector(q) + ax * (t - (Vector(q) - o).dot(ax))) for q in out]

UPPER_STYLE = {   # banda por textura: encaje, carcasa, correa (o None), pasador, tapas
    "peg": ("socket", "wood", "strap", "rubber", "rubber"),
    "hook": ("socket", "steel", "strap", "dark", "polished"),
    "metal": ("socket", "shell", None, "dark", "dark"),
    "saw": ("socket", "steel", "strap", "dark", "polished"),
}

def build_upper_section(B, arm):
    """Encaje sobre el muñón del brazo, carcasa hasta el codo con la forma del brazo y bisagra de codo. Todo en el
    hueso del brazo; el antebrazo protésico (hueso del antebrazo) gira en la bisagra con las animaciones."""
    up = arm["upper"]; bone = up["bone"]
    uo, uax, udn, ufr = Vector(up["o"]), Vector(up["axis"]), Vector(up["down"]), Vector(up["front"])
    L, tc = up["len"], up["t_cut"]
    b_sock, b_shell, b_strap, b_pin, b_cap = UPPER_STYLE[B.tex]
    cl = 0.0048
    t0 = max(0.012, tc - 0.035)
    B.loft("usocket", smooth_rings([upper_ring(arm, t, cl) for t in (t0, t0 + 0.012, t0 + 0.024, tc, tc + 0.012)]), bone, B.band(b_sock), subsurf=1)
    B.loft("urim", smooth_rings([upper_ring(arm, t0 - 0.004, cl + 0.003), upper_ring(arm, t0, cl + 0.005), upper_ring(arm, t0 + 0.008, cl + 0.004),
                                upper_ring(arm, t0 + 0.012, cl + 0.001)]), bone, B.band(b_pin), subsurf=1)
    ts = [tc + 0.012, tc + 0.03, tc + 0.05, L - 0.03, L - 0.014]
    ts = sorted({round(t, 4) for t in ts if tc + 0.01 <= t <= L - 0.01})
    B.loft("ushell", smooth_rings([upper_ring(arm, t, cl - 0.002) for t in ts]), bone, B.band(b_shell), subsurf=1)
    if b_strap:
        for i, t in enumerate((t0 + 0.012, tc - 0.004)):
            B.loft("ustrap%d" % i, [upper_ring(arm, t - 0.005, cl + 0.003), upper_ring(arm, t + 0.005, cl + 0.003)], bone, B.band(b_strap), subsurf=1)
    # bisagra: el codo flexiona alrededor del eje "abajo" del marco (vertical en la pose de reposo, palmas abajo)
    elbow = Vector(arm["o"])
    ring = [Vector(q) for q in upper_ring(arm, L - 0.006, cl)]
    c = sum(ring, Vector()) / len(ring)
    half = max(abs((q - c).dot(udn)) for q in ring) + 0.003
    B.cyl("upin", tuple(elbow - udn * half), tuple(elbow + udn * half), 0.0085, 0.0085, bone, B.band(b_pin), segs=14, bevel=0.0012, ref=tuple(uax))
    for k, sg in enumerate((-1, 1)):
        cc = elbow + udn * sg * half
        B.cyl("ucap%d" % k, tuple(cc - udn * sg * 0.002), tuple(cc + udn * sg * 0.003), 0.0135, 0.0125, bone, B.band(b_cap), segs=14, bevel=0.0012, ref=tuple(uax))
        # pletina de la bisagra hacia el brazo
        q0 = cc - uax * 0.004; q1 = cc - uax * 0.032
        B.box("uplate%d" % k, (q0 + q1) / 2, (0.0022, 0.009, (q1 - q0).length / 2), (tuple(udn), tuple(ufr), tuple(uax)), bone, B.band(b_pin), bevel=0.0008)

def smooth_rings(rings, passes=1):''')

# ---------------- arm_socket: rama Upper (antebrazo entero protésico)
patch('''    ts = [-0.015, 0.0, 0.015, 0.03, 0.045]
    B.loft("socket", smooth_rings([arm_ring(arm, t, clearance) for t in ts]), bone, band_socket, subsurf=subsurf)''',
      '''    if level == "Upper":
        # sin muñón en el antebrazo: carcasa del codo a la muñeca (algo más fina que el brazo) y anillo en el codo
        B.loft("ecuff", smooth_rings([arm_ring(arm, t, clearance - 0.001) for t in (-0.004, 0.004, 0.012)]), bone, band_socket, subsurf=1)
        B.loft("shell", smooth_rings([arm_ring(arm, t, -0.003) for t in (0.012, 0.035, 0.06, 0.085, 0.105, 0.12)]), bone, band_shell, subsurf=subsurf)
        return o + ax * 0.12
    ts = [-0.015, 0.0, 0.015, 0.03, 0.045]
    B.loft("socket", smooth_rings([arm_ring(arm, t, clearance) for t in ts]), bone, band_socket, subsurf=subsurf)''')

# correas del antebrazo sólo donde hay muñón de antebrazo
s = s.replace('''(0.09, 0.128) if level == "Wrist" else (0.005, 0.038)''', '''(0.09, 0.128) if level == "Wrist" else ((0.005, 0.038) if level == "" else ())''')

# ---------------- brazo motosierra: rama Upper
patch('''        t_end = 0.142; end_cl = cl + 0.0035
    else:''', '''        t_end = 0.142; end_cl = cl + 0.0035
    elif level == "Upper":
        # antebrazo entero protésico: carcasa de acero del codo al acople, con nervios
        B.loft("ecuff", smooth_rings([arm_ring(arm, t, cl - 0.001) for t in (-0.004, 0.004, 0.012)]), bone, B.band("dark"), subsurf=1)
        shell = [arm_ring(arm, t, e) for t, e in ((0.012, -0.002), (0.04, -0.003), (0.07, -0.003), (0.095, -0.003), (0.112, -0.002), (0.12, -0.001))]
        B.loft("shell", smooth_rings(shell), bone, B.band("steel"), subsurf=1)
        for k, d in enumerate((fr, -fr)):
            pts = [tuple(surf(t, d, 0.0025, -0.002)) for t in (0.02, 0.06, 0.1, 0.116)]
            B.curve("rib%d" % k, pts, [0.003] * 4, bone, B.band("dark"), res=2)
        t_end = 0.12; end_cl = -0.001
    else:''')

# ---------------- catálogo: sección superior en todo modelo de nivel Upper
patch('''            B = Builder(name, tex)
            fn(B, data, lv)''', '''            B = Builder(name, tex)
            fn(B, data, lv)
            if lv == "Upper": build_upper_section(B, data)''')

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("blender_build.py: nivel Upper añadido")
