import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "build_assets.py")
s = open(p, encoding="utf-8").read()
rep = [
    # sector angular más ancho y más segmentos: la cuerda entre dos puntos del anillo nunca corta la pierna
    ("        sector = d <= math.pi / segs + 0.02\n", "        sector = d <= 1.6 * math.pi / segs + 0.02\n"),
    ("def leg_section(pts_unused, y, clearance=0.003, segs=18, window=0.03, smooth=1, body=None, side=None):",
     "def leg_section(pts_unused, y, clearance=0.003, segs=28, window=0.03, smooth=1, body=None, side=None):"),
    ("def shaped_tube(m, body, side, ys, bone, clearance, uv_v, segs=18, close_start=False, close_end=False, scale=1.0):",
     "def shaped_tube(m, body, side, ys, bone, clearance, uv_v, segs=28, close_start=False, close_end=False, scale=1.0):"),
    # holguras: encaje 4.5 mm, caña 3.5 mm
    ("    centers, rings = shaped_tube(m, body, side, ys, bone, 0.0032, (0.0, 0.25), close_start=True, close_end=True)",
     "    centers, rings = shaped_tube(m, body, side, ys, bone, 0.0042, (0.0, 0.25), close_start=True, close_end=True)"),
    ("        r1 = leg_section(None, y + 0.006, 0.0032 + 0.0025, body=body, side=side); r2 = leg_section(None, y - 0.006, 0.0032 + 0.0025, body=body, side=side)",
     "        r1 = leg_section(None, y + 0.006, 0.0042 + 0.0025, body=body, side=side); r2 = leg_section(None, y - 0.006, 0.0042 + 0.0025, body=body, side=side)"),
    ("    shaped_tube(m, body, side, [0.33, 0.305, 0.28, 0.255], calf, 0.004, (0.0, 0.2), close_start=True, close_end=True)",
     "    shaped_tube(m, body, side, [0.33, 0.305, 0.28, 0.255], calf, 0.0048, (0.0, 0.2), close_start=True, close_end=True)"),
    ("        shaped_tube(m, body, side, ys, calf, 0.003, (0.2, 0.8), close_start=True, close_end=True)",
     "        shaped_tube(m, body, side, ys, calf, 0.0036, (0.2, 0.8), close_start=True, close_end=True)"),
    ("        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0025, (0.2, 0.8), close_start=True, close_end=True)",
     "        centers, rings = shaped_tube(m, body, side, ys, calf, 0.0032, (0.2, 0.8), close_start=True, close_end=True)"),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("legs4 applied")
