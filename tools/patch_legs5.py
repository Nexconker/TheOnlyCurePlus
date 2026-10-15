import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "build_assets.py")
s = open(p, encoding="utf-8").read()
old = '''    sl = plane_section(body, side, y)
    if len(sl) < 4:
        P = _leg_points(body, side)
        sl = P[np.argsort(np.abs(P[:, 1] - y))[:10]]'''
new = '''    sl = plane_section(body, side, y)
    # además de la sección exacta, los vértices de la banda [y-band, y+band]: la superficie entre dos
    # secciones es lineal por triángulos y un vértice intermedio puede sobresalir de la interpolación
    P = _leg_points(body, side)
    band = P[np.abs(P[:, 1] - y) <= 0.016]
    if len(band): sl = np.vstack([sl, band]) if len(sl) else band
    if len(sl) < 4:
        sl = P[np.argsort(np.abs(P[:, 1] - y))[:10]]'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("legs5 applied")
