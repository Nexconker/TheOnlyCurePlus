"""Sustituye build_saw_arm en blender_build.py por la versión con acople mecánico y piezas distintas por nivel.
Uso: python patch_saw_arm.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "blender_build.py"); s = open(p, encoding="utf-8").read()
a = s.index("def build_saw_arm(B, arm, level, saw):")
b = s.index("# ------------------------------------------------------------------ exportación")
NEW = r'''def build_saw_arm(B, arm, level, saw):
    """Brazo motosierra como el de Ash (Evil Dead 2): la motosierra vanilla sin asas con la espada como prolongación
    del antebrazo, unida por un acople mecánico (abrazadera con orejeta y perno, vástago, dos pletinas laterales
    atornilladas, piñón y placa de montaje). Todo rígido al hueso del antebrazo (como la mano mecánica).
    Por nivel de amputación:
      - Wrist (falta la mano): el antebrazo está entero -> brazal de cuero con dos férulas de acero y copa en la muñeca.
      - ForeArm (falta medio antebrazo): encaje de cuero en el muñón y carcasa de acero que sustituye lo que falta."""
    o, ax, dn, fr = arm_frame(arm); bone = arm["bones"]["forearm"]
    cl = 0.0048
    side = -dn                               # con el brazo colgando: -dn = hacia fuera, dn = hacia el cuerpo
    def rivet(name, p, r=0.003): B.sphere(name, tuple(p), r, bone, B.band("polished"), segs=8)
    def surf(t, d, extra, clr=cl):
        r = [Vector(p) for p in arm_ring(arm, t, clr)]
        c = sum(r, Vector()) / len(r)
        return max(r, key=lambda p: (p - c).dot(d)) + d * extra
    def hexbolt(name, p, axis, r=0.0042, hgt=0.003):
        axis = norm(Vector(axis))
        B.cyl(name, tuple(p), tuple(p + axis * hgt), r, r, bone, B.band("polished"), segs=6, bevel=0.0007,
              ref=tuple(ax if abs(axis.dot(ax)) < 0.9 else fr))
    # ---------------- parte del antebrazo según el nivel
    if level == "Wrist":
        ts = [0.03, 0.045, 0.06, 0.075, 0.09, 0.105, 0.118]
        B.loft("bracer", smooth_rings([arm_ring(arm, t, cl) for t in ts]), bone, B.band("socket"), subsurf=1)
        B.loft("rim", smooth_rings([arm_ring(arm, 0.026, cl + 0.003), arm_ring(arm, 0.03, cl + 0.005), arm_ring(arm, 0.038, cl + 0.004),
                                   arm_ring(arm, 0.042, cl + 0.001)]), bone, B.band("dark"), subsurf=1)
        arm_straps(B, arm, (0.052, 0.09), cl, bone)
        for k, d in enumerate((fr, -fr)):        # férulas de acero delante y detrás del antebrazo
            pts = [tuple(surf(t, d, 0.0035)) for t in (0.034, 0.06, 0.088, 0.114)]
            B.curve("splint%d" % k, pts, [0.0034] * 4, bone, B.band("steel"), res=2)
            rivet("splintrivet%da" % k, Vector(pts[0]) + d * 0.002); rivet("splintrivet%db" % k, Vector(pts[-1]) + d * 0.002)
        cup = [arm_ring(arm, t, cl + e) for t, e in ((0.112, 0.0), (0.122, 0.0015), (0.134, 0.003), (0.142, 0.0035))]
        B.loft("cup", smooth_rings(cup), bone, B.band("steel"), subsurf=1)
        t_end = 0.142; end_cl = cl + 0.0035
    else:
        ts = [-0.015, 0.0, 0.015, 0.03, 0.045]
        B.loft("socket", smooth_rings([arm_ring(arm, t, cl) for t in ts]), bone, B.band("socket"), subsurf=1)
        B.loft("rim", smooth_rings([arm_ring(arm, -0.019, cl + 0.004), arm_ring(arm, -0.015, cl + 0.006), arm_ring(arm, -0.003, cl + 0.005),
                                   arm_ring(arm, 0.001, cl + 0.001)]), bone, B.band("dark"), subsurf=1)
        arm_straps(B, arm, (0.005, 0.034), cl, bone)
        # carcasa de acero que sustituye la parte del antebrazo que falta (algo más fina que el brazo)
        shell = [arm_ring(arm, t, e) for t, e in ((0.043, cl + 0.002), (0.055, 0.0), (0.075, -0.002), (0.095, -0.003), (0.112, -0.002), (0.12, -0.001))]
        B.loft("shell", smooth_rings(shell), bone, B.band("steel"), subsurf=1)
        B.loft("band", [arm_ring(arm, 0.043, cl + 0.0035), arm_ring(arm, 0.05, cl + 0.0035)], bone, B.band("dark"), subsurf=1)
        for k, d in enumerate((fr, -fr)):        # nervios con remaches a lo largo de la carcasa
            pts = [tuple(surf(t, d, 0.0025, -0.002)) for t in (0.056, 0.078, 0.1, 0.116)]
            B.curve("rib%d" % k, pts, [0.003] * 4, bone, B.band("dark"), res=2)
            for j, pp in enumerate(pts[::3]): rivet("ribrivet%d%d" % (k, j), Vector(pp) + d * 0.0022, 0.0026)
        t_end = 0.12; end_cl = -0.001
    # ---------------- acople
    end = [Vector(p) for p in arm_ring(arm, t_end, end_cl)]
    c_end = sum(end, Vector()) / len(end)
    e_dn = max(abs((p - c_end).dot(dn)) for p in end) + 0.004
    e_fr = max(abs((p - c_end).dot(fr)) for p in end) + 0.004
    ho, hn = saw["body_half"]
    L = 0.052                                # del extremo del antebrazo a la cara de la placa
    # abrazadera (collar elíptico ajustado al extremo) con orejeta delante y perno pasante
    B.cyl("collar", tuple(c_end - ax * 0.004), tuple(c_end + ax * 0.012), (e_dn, e_fr), (e_dn, e_fr), bone, B.band("dark"), segs=20, bevel=0.0018, ref=tuple(dn))
    lug_c = c_end + ax * 0.004 + fr * (e_fr + 0.005)
    for k, sg in enumerate((-1, 1)):
        B.box("lug%d" % k, lug_c + dn * (sg * 0.0048), (0.0065, 0.0016, 0.0062), (tuple(ax), tuple(dn), tuple(fr)), bone, B.band("dark"), bevel=0.0008)
    B.cyl("clampbolt", tuple(lug_c - dn * 0.011), tuple(lug_c + dn * 0.011), 0.0022, 0.0022, bone, B.band("polished"), segs=8, ref=tuple(ax))
    hexbolt("nut0", lug_c + dn * 0.0064, dn, 0.0040, 0.0032); hexbolt("nut1", lug_c - dn * 0.0064, -dn, 0.0040, 0.0032)
    # placa de montaje: rectángulo redondeado del tamaño del motor, biselada
    def rr(center, a_, b_, e=4.0, n=24):
        pts = []
        for k in range(n):
            th = 2 * math.pi * k / n; c_, s_ = math.cos(th), math.sin(th)
            r = 1.0 / ((abs(c_) ** e + abs(s_) ** e) ** (1.0 / e))
            pts.append(tuple(center + dn * (a_ * r * c_) + fr * (b_ * r * s_)))
        return pts
    P_top, P_bot = c_end + ax * (L - 0.009), c_end + ax * L
    B.loft("plate", [rr(P_top, ho * 1.03, hn * 1.03), rr(P_bot, ho * 1.03, hn * 1.03)], bone, B.band("dark"), subsurf=0, bevel=0.0025)
    # vástago central
    B.cyl("stem", tuple(c_end + ax * 0.011), tuple(P_top + ax * 0.001), 0.0125, 0.0155, bone, B.band("steel"), segs=16, bevel=0.0015, ref=tuple(dn))
    B.cyl("stemring", tuple(P_top - ax * 0.008), tuple(P_top), 0.0185, 0.021, bone, B.band("dark"), segs=16, bevel=0.0015, ref=tuple(dn))
    # pletinas laterales: del collar a la placa, abiertas hacia fuera, con tornillos hexagonales en los extremos
    for k, sg in enumerate((1, -1)):
        A = c_end + ax * 0.003 + dn * sg * (e_dn + 0.0032)
        Bp = P_top + dn * sg * (ho * 0.78)
        w = norm(Bp - A); u = fr; v = norm(w.cross(u))
        if v.dot(dn * sg) < 0: v = -v
        B.box("bar%d" % k, (A + Bp) / 2, (0.0115, 0.0026, (Bp - A).length / 2 + 0.003), (tuple(u), tuple(v), tuple(w)), bone, B.band("steel"), bevel=0.0012)
        hexbolt("hexA%d" % k, A + v * 0.0024, v); hexbolt("hexB%d" % k, Bp + v * 0.0024 - w * 0.004, v)
        if sg < 0:
            # piñón sobre la pletina exterior, como el de la figura
            gc = (A + Bp) / 2 + v * 0.0026
            B.cyl("gear", tuple(gc), tuple(gc + v * 0.0045), 0.0125, 0.0125, bone, B.band("dark"), segs=12, ref=tuple(w))
            for j in range(10):
                an = 2 * math.pi * j / 10; rd = w * math.cos(an) + u * math.sin(an)
                B.box("tooth%d" % j, gc + v * 0.00225 + rd * 0.0145, (0.0026, 0.002, 0.00225), (tuple(rd), tuple(v.cross(rd)), tuple(v)), bone, B.band("dark"))
            B.sphere("hub", tuple(gc + v * 0.005), 0.0042, bone, B.band("polished"), segs=8)
    # manguera de gasolina: del antebrazo, por delante, hasta el borde de la placa
    h = norm(side * 0.45 + fr * 0.9)
    t_h = 0.07 if level == "Wrist" else 0.025
    p_plate = P_top + h * (max(ho, hn) * 0.92) - ax * 0.002
    B.curve("hose", [tuple(surf(t_h, h, 0.0045)), tuple(surf(t_end - 0.012, h, 0.006, end_cl)),
                     tuple(c_end + ax * (L * 0.45) + h * (max(e_dn, e_fr) + 0.012)), tuple(p_plate)], [0.0042] * 4, bone, B.band("rubber"), res=3)
    # motosierra: base del motor sobre la placa, espada (b) por el eje del antebrazo, o -> dn, n -> +-fr
    sb, so, sn, base = Vector(saw["b"]), Vector(saw["o"]), Vector(saw["n"]), Vector(saw["base"])
    det_l = sb.dot(so.cross(sn)); det_w = ax.dot(dn.cross(fr))
    fr_s = fr if (det_l > 0) == (det_w > 0) else -fr
    S0 = P_bot - ax * 0.004
    def place(p):
        d = Vector(p) - base
        return S0 + ax * d.dot(sb) + dn * d.dot(so) + fr_s * d.dot(sn)
    def turn(nv):
        nv = Vector(nv)
        return norm(ax * nv.dot(sb) + dn * nv.dot(so) + fr_s * nv.dot(sn))
    B.raw.append({"verts": [tuple(place(p)) for p in saw["verts"]], "normals": [tuple(turn(n)) for n in saw["normals"]],
                  "uvs": saw["uvs"], "faces": saw["faces"], "bone": bone, "name": "saw"})

'''
s = s[:a] + NEW + s[b:]
old = '''             "adapter", "adapterlip", "bolt", "gear", "tooth", "hub")'''
new2 = '''             "cup", "collar", "lug", "clampbolt", "nut", "plate", "stem", "bar", "hex", "gear", "tooth", "hub")'''
if old in s: s = s.replace(old, new2)
assert new2 in s
open(p, "w", encoding="utf-8", newline="\n").write(s); print("build_saw_arm actualizado")
