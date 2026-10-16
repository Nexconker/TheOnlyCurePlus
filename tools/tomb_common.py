"""Utilidades comunes para el ajuste a Tomb's Player Body (tomb_export.py, export_fit.py --tomb, tomb_clip.py)."""

def tomb_main_faces(tris, nverts):
    """Caras de la pieza principal del cuerpo de Tomb. Las dos piezas sueltas que unen las piernas (delante y detrás, su
    "membrana" para vestidos) son 100 % transparentes en sus texturas: no se ven y no cuentan."""
    import collections
    par = list(range(nverts))
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b, c in tris: par[f(b)] = f(a); par[f(c)] = f(a)
    big = collections.Counter(f(i) for i in range(nverts)).most_common(1)[0][0]
    return [i for i, t in enumerate(tris) if f(t[0]) == big]
