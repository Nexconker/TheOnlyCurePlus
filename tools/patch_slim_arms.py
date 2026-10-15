"""Adelgaza las prótesis de brazo (2026-10-14, "el brazo protésico se ve más grande que el normal"; diag_arm_size.py
medía +10..30 % en las carcasas y hasta +70 % en el manguito de muñeca):
- lo que SUSTITUYE al miembro (carcasas de antebrazo y de brazo): holgura -0.006 -> con el margen de la subdivisión
  (polígono circunscrito +3.5 % y +1.5 mm) queda del tamaño del brazo real;
- lo que ENVUELVE un muñón o un antebrazo entero (encajes, brazal, manguito): 2.5 mm (3.5 mm junto al codo, donde la
  piel se mueve al flexionar);
- bordes, correas, nervios y hebillas más planos.
Uso: python patch_slim_arms.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "blender_build.py"); s = open(p, encoding="utf-8").read()
n_total = 0
def patch(old, new, count=1):
    global s, n_total
    assert old in s, old[:90]
    s = s.replace(old, new, count); n_total += 1

ARM_CL = "ARM_CL = 0.0025          # holgura de encajes/manguitos de brazo sobre la piel (3.1.0, antes 0.0045-0.0048)\nARM_SHELL = -0.006       # carcasas que sustituyen al miembro: del tamaño del brazo real tras el margen del loft\n\n"
patch("def arm_frame(arm):", ARM_CL + "def arm_frame(arm):")

# ---- arm_socket
patch("def arm_socket(B, arm, level, bone, band_socket, band_shell, clearance=0.0045, subsurf=1):",
      "def arm_socket(B, arm, level, bone, band_socket, band_shell, clearance=ARM_CL, subsurf=1):")
patch("""        rim = smooth_rings([arm_ring(arm, 0.066, clearance + 0.004), arm_ring(arm, 0.07, clearance + 0.006), arm_ring(arm, 0.082, clearance + 0.005), arm_ring(arm, 0.086, clearance + 0.001)])""",
      """        rim = smooth_rings([arm_ring(arm, 0.066, clearance + 0.0015), arm_ring(arm, 0.07, clearance + 0.003), arm_ring(arm, 0.082, clearance + 0.0025), arm_ring(arm, 0.086, clearance + 0.0005)])""")
patch("""        B.loft("collar", [arm_ring(arm, 0.142, clearance - 0.004), arm_ring(arm, 0.154, clearance - 0.004)], bone, band_shell, subsurf=1)""",
      """        B.loft("collar", [arm_ring(arm, 0.142, clearance - 0.002), arm_ring(arm, 0.154, clearance - 0.002)], bone, band_shell, subsurf=1)""")
patch("""        B.loft("shell", smooth_rings([arm_ring(arm, t, -0.003) for t in (0.012, 0.035, 0.06, 0.085, 0.105, 0.12)]), bone, band_shell, subsurf=subsurf)""",
      """        B.loft("shell", smooth_rings([arm_ring(arm, t, ARM_SHELL) for t in (0.012, 0.035, 0.06, 0.085, 0.105, 0.12)]), bone, band_shell, subsurf=subsurf)""")
patch("""    ts = [-0.015, 0.0, 0.015, 0.03, 0.045]
    B.loft("socket", smooth_rings([arm_ring(arm, t, clearance) for t in ts]), bone, band_socket, subsurf=subsurf)
    rim = smooth_rings([arm_ring(arm, -0.019, clearance + 0.004), arm_ring(arm, -0.015, clearance + 0.006), arm_ring(arm, -0.003, clearance + 0.005), arm_ring(arm, 0.001, clearance + 0.001)])
    B.loft("rim", rim, bone, band_socket, subsurf=1)
    ts = [0.045, 0.065, 0.085, 0.105, 0.12]
    B.loft("shell", smooth_rings([arm_ring(arm, t, -0.002) for t in ts]), bone, band_shell, subsurf=subsurf)""",
      """    # junto al codo un poco más de holgura: la piel del brazo se mueve al flexionar
    ts = [(-0.015, clearance + 0.001), (0.0, clearance + 0.001), (0.015, clearance), (0.03, clearance), (0.045, clearance)]
    B.loft("socket", smooth_rings([arm_ring(arm, t, c) for t, c in ts]), bone, band_socket, subsurf=subsurf)
    rim = smooth_rings([arm_ring(arm, -0.019, clearance + 0.0025), arm_ring(arm, -0.015, clearance + 0.004), arm_ring(arm, -0.003, clearance + 0.0035), arm_ring(arm, 0.001, clearance + 0.0015)])
    B.loft("rim", rim, bone, band_socket, subsurf=1)
    ts = [0.045, 0.065, 0.085, 0.105, 0.12]
    B.loft("shell", smooth_rings([arm_ring(arm, t, ARM_SHELL) for t in ts]), bone, band_shell, subsurf=subsurf)""")

# ---- correas y hebillas más planas
patch("""        B.loft("strap%d" % i, [arm_ring(arm, t - 0.006, clearance + 0.003), arm_ring(arm, t + 0.006, clearance + 0.003)], bone, B.band("strap"), subsurf=1)
        r = arm_ring(arm, t, clearance + 0.003)
        top = max(r, key=lambda p: -(Vector(p) - o).dot(dn))      # lado superior (-down)
        B.box("buckle%d" % i, Vector(top) - dn * 0.004, (0.003, 0.006, 0.009), (tuple(dn), tuple(fr), tuple(ax)), bone, B.band("strap"), bevel=0.0015)""",
      """        B.loft("strap%d" % i, [arm_ring(arm, t - 0.006, clearance + 0.0018), arm_ring(arm, t + 0.006, clearance + 0.0018)], bone, B.band("strap"), subsurf=1)
        r = arm_ring(arm, t, clearance + 0.0018)
        top = max(r, key=lambda p: -(Vector(p) - o).dot(dn))      # lado superior (-down)
        B.box("buckle%d" % i, Vector(top) - dn * 0.0025, (0.002, 0.005, 0.008), (tuple(dn), tuple(fr), tuple(ax)), bone, B.band("strap"), bevel=0.001)""")
s = s.replace(", 0.0045, bone)\n", ", ARM_CL, bone)\n")            # llamadas a arm_straps de madera y gancho

# ---- nervios del brazo mecánico: sobre la carcasa nueva y más finos
patch("""    cl = 0.0045 if level == "Wrist" else -0.002""", """    cl = ARM_CL if level == "Wrist" else ARM_SHELL""")
patch("""            pts.append(tuple(edge + fr * sgn * 0.0045))
        B.curve(nm, pts, [0.0045] * len(pts), bone, B.band("dark"), res=2)""",
      """            pts.append(tuple(edge + fr * sgn * 0.0032))
        B.curve(nm, pts, [0.0034] * len(pts), bone, B.band("dark"), res=2)""")
patch("""    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("shell"), clearance=0.0048 if medical else 0.0045, subsurf=1)""",
      """    s = arm_socket(B, arm, level, bone, B.band("socket"), B.band("shell"), clearance=ARM_CL, subsurf=1)""")

# ---- brazo motosierra
patch("""    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    cl = 0.0048
    side = -dn""", """    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    cl = ARM_CL
    side = -dn""")
patch("""        B.loft("rim", smooth_rings([arm_ring(arm, 0.026, cl + 0.003), arm_ring(arm, 0.03, cl + 0.005), arm_ring(arm, 0.038, cl + 0.004),
                                   arm_ring(arm, 0.042, cl + 0.001)]), bone, B.band("dark"), subsurf=1)""",
      """        B.loft("rim", smooth_rings([arm_ring(arm, 0.026, cl + 0.0015), arm_ring(arm, 0.03, cl + 0.003), arm_ring(arm, 0.038, cl + 0.0025),
                                   arm_ring(arm, 0.042, cl + 0.0005)]), bone, B.band("dark"), subsurf=1)""")
patch("""        cup = [arm_ring(arm, t, cl + e) for t, e in ((0.112, 0.0), (0.122, 0.0015), (0.134, 0.003), (0.142, 0.0035))]""",
      """        cup = [arm_ring(arm, t, cl + e) for t, e in ((0.112, 0.0), (0.122, 0.001), (0.134, 0.002), (0.142, 0.0025))]""")
patch("""        t_end = 0.142; end_cl = cl + 0.0035""", """        t_end = 0.142; end_cl = cl + 0.0025""")
patch("""        B.loft("rim", smooth_rings([arm_ring(arm, -0.019, cl + 0.004), arm_ring(arm, -0.015, cl + 0.006), arm_ring(arm, -0.003, cl + 0.005),
                                   arm_ring(arm, 0.001, cl + 0.001)]), bone, B.band("dark"), subsurf=1)""",
      """        B.loft("rim", smooth_rings([arm_ring(arm, -0.019, cl + 0.0025), arm_ring(arm, -0.015, cl + 0.004), arm_ring(arm, -0.003, cl + 0.0035),
                                   arm_ring(arm, 0.001, cl + 0.0015)]), bone, B.band("dark"), subsurf=1)""")
patch("""        shell = [arm_ring(arm, t, e) for t, e in ((0.043, cl + 0.002), (0.055, 0.0), (0.075, -0.002), (0.095, -0.003), (0.112, -0.002), (0.12, -0.001))]""",
      """        shell = [arm_ring(arm, t, e) for t, e in ((0.043, cl + 0.001), (0.055, -0.002), (0.075, ARM_SHELL), (0.095, ARM_SHELL), (0.112, ARM_SHELL), (0.12, ARM_SHELL + 0.001))]""")
patch("""        B.loft("band", [arm_ring(arm, 0.043, cl + 0.0035), arm_ring(arm, 0.05, cl + 0.0035)], bone, B.band("dark"), subsurf=1)""",
      """        B.loft("band", [arm_ring(arm, 0.043, cl + 0.002), arm_ring(arm, 0.05, cl + 0.002)], bone, B.band("dark"), subsurf=1)""")
patch("""            pts = [tuple(surf(t, d, 0.0025, -0.002)) for t in (0.056, 0.078, 0.1, 0.116)]""",
      """            pts = [tuple(surf(t, d, 0.0022, ARM_SHELL)) for t in (0.056, 0.078, 0.1, 0.116)]""")
patch("""        t_end = 0.12; end_cl = -0.001
    # ---------------- acople""", """        t_end = 0.12; end_cl = ARM_SHELL + 0.001
    # ---------------- acople""")
patch("""        shell = [arm_ring(arm, t, e) for t, e in ((0.012, -0.002), (0.04, -0.003), (0.07, -0.003), (0.095, -0.003), (0.112, -0.002), (0.12, -0.001))]""",
      """        shell = [arm_ring(arm, t, e) for t, e in ((0.012, ARM_SHELL + 0.002), (0.04, ARM_SHELL), (0.07, ARM_SHELL), (0.095, ARM_SHELL), (0.112, ARM_SHELL), (0.12, ARM_SHELL + 0.001))]""")
patch("""            pts = [tuple(surf(t, d, 0.0025, -0.002)) for t in (0.02, 0.06, 0.1, 0.116)]""",
      """            pts = [tuple(surf(t, d, 0.0022, ARM_SHELL)) for t in (0.02, 0.06, 0.1, 0.116)]""")
patch("""        t_end = 0.12; end_cl = -0.001
    else:""", """        t_end = 0.12; end_cl = ARM_SHELL + 0.001
    else:""")
patch("""    h_cl = -0.003 if level == "Upper" else cl""", """    h_cl = ARM_SHELL if level == "Upper" else cl""")

# ---- sección superior (por encima del codo)
patch("""    cl = 0.0048
    t0 = max(0.012, tc - 0.035)""", """    cl = ARM_CL
    t0 = max(0.012, tc - 0.035)""")
patch("""    B.loft("urim", smooth_rings([upper_ring(arm, t0 - 0.004, cl + 0.003), upper_ring(arm, t0, cl + 0.005), upper_ring(arm, t0 + 0.008, cl + 0.004),
                                upper_ring(arm, t0 + 0.012, cl + 0.001)]), bone, B.band(b_pin), subsurf=1)""",
      """    B.loft("urim", smooth_rings([upper_ring(arm, t0 - 0.004, cl + 0.0015), upper_ring(arm, t0, cl + 0.003), upper_ring(arm, t0 + 0.008, cl + 0.0025),
                                upper_ring(arm, t0 + 0.012, cl + 0.0005)]), bone, B.band(b_pin), subsurf=1)""")
patch("""    B.loft("ushell", smooth_rings([upper_ring(arm, t, cl - 0.002) for t in ts]), bone, B.band(b_shell), subsurf=1)""",
      """    B.loft("ushell", smooth_rings([upper_ring(arm, t, ARM_SHELL) for t in ts]), bone, B.band(b_shell), subsurf=1)""")
patch("""            B.loft("ustrap%d" % i, [upper_ring(arm, t - 0.005, cl + 0.003), upper_ring(arm, t + 0.005, cl + 0.003)], bone, B.band(b_strap), subsurf=1)""",
      """            B.loft("ustrap%d" % i, [upper_ring(arm, t - 0.005, cl + 0.0018), upper_ring(arm, t + 0.005, cl + 0.0018)], bone, B.band(b_strap), subsurf=1)""")
patch("""    half = max(abs((q - c).dot(udn)) for q in ring) + 0.003""", """    half = max(abs((q - c).dot(udn)) for q in ring) + 0.0015""")

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("blender_build.py: prótesis de brazo adelgazadas (%d cambios)" % n_total)
