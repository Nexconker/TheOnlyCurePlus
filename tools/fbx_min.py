"""Lector mínimo de FBX binario (7.x): saca vértices, triángulos y UV de cada Geometry, con las
transformaciones de su Model. Suficiente para dibujar los modelos de The Only Cure (ropa en espacio
del cuerpo). No lee animación ni pesos."""
import struct, zlib
import numpy as np

def _read_prop(f):
    t = f.read(1)
    if t in (b"Y",): return struct.unpack("<h", f.read(2))[0]
    if t == b"C": return struct.unpack("<?", f.read(1))[0]
    if t == b"I": return struct.unpack("<i", f.read(4))[0]
    if t == b"F": return struct.unpack("<f", f.read(4))[0]
    if t == b"D": return struct.unpack("<d", f.read(8))[0]
    if t == b"L": return struct.unpack("<q", f.read(8))[0]
    if t in (b"S", b"R"):
        n = struct.unpack("<I", f.read(4))[0]; data = f.read(n)
        return data.decode("latin-1") if t == b"S" else data
    if t in (b"f", b"d", b"l", b"i", b"b"):
        n, enc, clen = struct.unpack("<III", f.read(12))
        raw = f.read(clen)
        if enc == 1: raw = zlib.decompress(raw)
        dt = {b"f": "<f4", b"d": "<f8", b"l": "<i8", b"i": "<i4", b"b": "<i1"}[t]
        return np.frombuffer(raw, dtype=dt, count=n)
    raise ValueError("tipo de propiedad FBX desconocido %r" % t)

def _read_node(f, version):
    if version >= 7500:
        end, nprops, plen = struct.unpack("<QQQ", f.read(24)); nlen = struct.unpack("<B", f.read(1))[0]
    else:
        end, nprops, plen = struct.unpack("<III", f.read(12)); nlen = struct.unpack("<B", f.read(1))[0]
    if end == 0:
        return None
    name = f.read(nlen).decode("latin-1")
    props = [_read_prop(f) for _ in range(nprops)]
    children = []
    while f.tell() < end:
        c = _read_node(f, version)
        if c is None: break
        children.append(c)
    f.seek(end)
    return {"name": name, "props": props, "children": children}

def parse(path):
    with open(path, "rb") as f:
        magic = f.read(23)
        if not magic.startswith(b"Kaydara FBX Binary"): raise ValueError("no es FBX binario: " + path)
        version = struct.unpack("<I", f.read(4))[0]
        nodes = []
        while True:
            n = _read_node(f, version)
            if n is None: break
            nodes.append(n)
    return {"version": version, "nodes": nodes}

def find(nodes, name):
    return [n for n in nodes if n["name"] == name]

def child(node, name):
    for c in node["children"]:
        if c["name"] == name: return c
    return None

def props70(node):
    out = {}
    p = child(node, "Properties70")
    if not p: return out
    for c in p["children"]:
        if c["name"] == "P" and len(c["props"]) >= 4:
            out[c["props"][0]] = c["props"][4:] if len(c["props"]) > 4 else []
    return out

def geometries(doc):
    """Devuelve lista de dict(verts (N,3), faces (M,3), uvs (N,2) por vértice, name)."""
    objs = find(doc["nodes"], "Objects")
    out = []
    if not objs: return out
    for g in find(objs[0]["children"], "Geometry"):
        V = child(g, "Vertices"); I = child(g, "PolygonVertexIndex")
        if not V or not I: continue
        verts = np.array(V["props"][0], float).reshape(-1, 3)
        idx = np.array(I["props"][0], int)
        # polígonos: índice negativo = último (valor ~idx-1)
        polys, cur = [], []
        for k in idx:
            if k < 0:
                cur.append(-k - 1); polys.append(cur); cur = []
            else:
                cur.append(k)
        # UV
        uv_el = child(g, "LayerElementUV")
        uv_per_corner = None
        if uv_el:
            UV = child(uv_el, "UV"); UVI = child(uv_el, "UVIndex"); mapping = child(uv_el, "MappingInformationType")
            uvs = np.array(UV["props"][0], float).reshape(-1, 2)
            ref = child(uv_el, "ReferenceInformationType")
            if UVI is not None and ref and ref["props"][0] == "IndexToDirect":
                uvidx = np.array(UVI["props"][0], int); uv_per_corner = uvs[uvidx]
            elif mapping and mapping["props"][0] == "ByVertice":
                uv_per_corner = None; uv_per_vertex = uvs
            else:
                uv_per_corner = uvs
        # construir malla partida por esquina para que cada vértice tenga una UV
        nv, nuv, faces = [], [], []
        corner = 0
        for poly in polys:
            ids = []
            for k, vi in enumerate(poly):
                nv.append(verts[vi])
                if uv_el:
                    if uv_per_corner is not None: nuv.append(uv_per_corner[corner])
                    else: nuv.append(uv_per_vertex[vi])
                else:
                    nuv.append([0.0, 0.0])
                ids.append(len(nv) - 1); corner += 1
            for k in range(1, len(ids) - 1):
                faces.append([ids[0], ids[k], ids[k + 1]])
        nuv = np.array(nuv, float)
        if len(nuv): nuv[:, 1] = 1.0 - nuv[:, 1]       # FBX: v hacia arriba; nuestras texturas: v hacia abajo
        out.append({"name": g["props"][1] if len(g["props"]) > 1 else "", "verts": np.array(nv, float), "faces": np.array(faces, int), "uvs": nuv, "id": g["props"][0]})
    return out

def unit_scale(doc):
    gs = find(doc["nodes"], "GlobalSettings")
    if not gs: return 1.0
    p = props70(gs[0])
    v = p.get("UnitScaleFactor")
    return float(v[0]) if v else 1.0

def model_transforms(doc):
    """id -> (translation, rotation deg, scaling) de los nodos Model."""
    objs = find(doc["nodes"], "Objects")
    out = {}
    if not objs: return out
    for m in find(objs[0]["children"], "Model"):
        p = props70(m)
        t = np.array(p.get("Lcl Translation", [0, 0, 0])[:3], float) if "Lcl Translation" in p else np.zeros(3)
        r = np.array(p.get("Lcl Rotation", [0, 0, 0])[:3], float) if "Lcl Rotation" in p else np.zeros(3)
        s = np.array(p.get("Lcl Scaling", [1, 1, 1])[:3], float) if "Lcl Scaling" in p else np.ones(3)
        out[m["props"][0]] = {"name": m["props"][1] if len(m["props"]) > 1 else "", "t": t, "r": r, "s": s}
    return out

def connections(doc):
    """Lista (hijo_id, padre_id) de las conexiones OO."""
    out = []
    for c in find(doc["nodes"], "Connections"):
        for k in c["children"]:
            if k["name"] == "C" and len(k["props"]) >= 3 and k["props"][0] == "OO":
                out.append((k["props"][1], k["props"][2]))
    return out

def _euler_xyz(r):
    import math
    ax, ay, az = [math.radians(v) for v in r]
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def load_meshes(path, skip_body=True, mirror_z=False):
    """mirror_z: los FBX de The Only Cure están en un sistema con Z invertida respecto a los .X del
    cuerpo (el juego lo corrige al importar); para dibujarlos sobre el cuerpo .X hay que negar Z."""
    out = _load_meshes(path, skip_body)
    if mirror_z:
        for m in out:
            m["verts"] = m["verts"] * np.array([1.0, 1.0, -1.0])
            m["faces"] = m["faces"][:, [0, 2, 1]]
    return out

def _load_meshes(path, skip_body=True):
    """Geometrías en el espacio del archivo (con la transformación de su Model y de sus padres).
    Salta el cuerpo de referencia (Model 'Body' o malla que abarca todo el cuerpo) y las cámaras/luces."""
    doc = parse(path)
    geos = geometries(doc)
    models = model_transforms(doc)
    parent = {}
    for ch, pa in connections(doc): parent.setdefault(ch, pa)
    out = []
    for g in geos:
        mid = parent.get(g["id"])
        v = g["verts"].copy()
        name = ""
        # cadena de padres
        chain = []
        while mid in models:
            chain.append(models[mid]); mid = parent.get(mid)
        for m in chain:
            v = v * m["s"]
            v = v @ _euler_xyz(m["r"]).T
            v = v + m["t"]
        if chain: name = chain[0]["name"]
        lo, hi = v.min(0), v.max(0)
        full_body = (lo[0] < -0.3 and hi[0] > 0.3 and hi[1] > 0.9)
        if skip_body and (name == "Body" or full_body): continue
        out.append({"name": name or g["name"], "verts": v, "faces": g["faces"], "uvs": g["uvs"]})
    return out

if __name__ == "__main__":
    import sys
    doc = parse(sys.argv[1])
    print("version", doc["version"], "unit scale", unit_scale(doc))
    for g in geometries(doc):
        v = g["verts"]
        print(g["name"], "verts", len(v), "tris", len(g["faces"]), "min", v.min(0).round(3), "max", v.max(0).round(3))
    for k, m in model_transforms(doc).items():
        print("model", m["name"], "t", m["t"].round(3), "r", m["r"].round(1), "s", m["s"].round(3))
    for m in load_meshes(sys.argv[1]):
        print("MESH", m["name"], len(m["verts"]), "min", m["verts"].min(0).round(3), "max", m["verts"].max(0).round(3))
