"""Tile de la mesa del banco de prótesis (2026-10-17): empaqueta los 4 sprites (S, E, N, W) de make_workbench_model.py en
media/texturepacks/TOCPlus_bench.pack (formato PZPK v1, como los packs de los mods de B42), escribe la definición
media/TOCPlus_bench.tiles (formato tdef v1) y media/spriteModels.txt (el modelo 3D de cada tile, que es lo que ven el
juego en 3D y los mods de cámara). Uso: TOC_MEDIA=...Dev python make_workbench_tiles.py
Formatos leídos de un pack / tiles de mod existentes:
  pack:  "PZPK", int version=1, int páginas; por página: str nombre, int entradas, int máscara=1; por entrada: str nombre,
         int x, y, w, h (recorte en la página), int ox, oy (desplazamiento en el marco), int fw, fh (marco 128x256);
         luego int tamaño + PNG de la página.  (str = int longitud + bytes)
  tiles: "tdef", int version=1, int tilesets; por tileset: nombre\\n, imagen\\n, int columnas, filas, id, nº de tiles;
         por tile: int nº de propiedades y pares clave\\n valor\\n."""
import os, io, struct
from PIL import Image

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
HERE = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(HERE, "out", "preview", "bench")
NAME = "TOCPlus_bench"
FACINGS = [("S", 180), ("E", -90), ("N", 0), ("W", 90)]
# rotación del modelo por orientación, como appliances_radio_01 en el spriteModels.txt del juego
ROT = {"S": "180.0000 0.0000 180.0000", "E": "0.0000 -90.0000 0.0000", "N": "0.0000 0.0000 0.0000", "W": "0.0000 90.0000 0.0000"}

def s32(v): return struct.pack("<i", v)
def pstr(s): b = s.encode("utf-8"); return s32(len(b)) + b

def write_pack():
    tiles = [Image.open(os.path.join(REN, "tile_%d_%s.png" % (i, f))).convert("RGBA") for i, (f, _) in enumerate(FACINGS)]
    crops, x = [], 0
    for im in tiles:
        bb = im.getbbox(); c = im.crop(bb); crops.append((c, bb, x)); x += c.width + 2
    page = Image.new("RGBA", (x, max(c.height for c, _, _ in crops)), (0, 0, 0, 0))
    for c, bb, px in crops: page.paste(c, (px, 0))
    buf = io.BytesIO(); page.save(buf, "PNG"); png = buf.getvalue()
    out = b"PZPK" + s32(1) + s32(1) + pstr(NAME + "0") + s32(len(crops)) + s32(1)
    for i, (c, bb, px) in enumerate(crops):
        out += pstr("%s_%d" % (NAME, i)) + s32(px) + s32(0) + s32(c.width) + s32(c.height) + s32(bb[0]) + s32(bb[1]) + s32(128) + s32(256)
    out += s32(len(png)) + png
    p = os.path.join(MOD, "texturepacks", NAME + ".pack"); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(out); print("pack", p, len(out), "bytes", page.size)

def tile_props(facing):
    return [("BlocksPlacement", ""), ("CanScrap", ""), ("CustomItem", "TOC.ProsthesisWorkbench"), ("CustomName", "Prosthesis Workbench"),
            ("Facing", facing), ("GroupName", "TOC"), ("IsMoveAble", ""), ("IsTable", ""), ("Material", "Wood"), ("Material2", "MetalScrap"),
            ("MaterialType", "Wood"), ("PickUpWeight", "300"), ("Surface", "28"), ("solidtrans", "")]

def write_tiles():
    cols, rows = 8, 1
    out = b"tdef" + s32(1) + s32(1) + (NAME + "\n").encode() + (NAME + ".png\n").encode() + s32(cols) + s32(rows) + s32(1) + s32(cols * rows)
    for i in range(cols * rows):
        if i < len(FACINGS):
            props = tile_props(FACINGS[i][0])
            out += s32(len(props)) + b"".join(("%s\n%s\n" % (k, v)).encode() for k, v in props)
        else:
            out += s32(0)
    p = os.path.join(MOD, NAME + ".tiles"); open(p, "wb").write(out); print("tiles", p, len(out), "bytes")

def write_sprite_models():
    L = ["spriteModel", "{", "    VERSION = 1,", "", "    tileset", "    {", "        name = %s," % NAME, ""]
    for i, (f, _) in enumerate(FACINGS):
        L += ["        tile", "        {", "            xy = %d 0," % i, "            modelScript = TOC.ProsthesisWorkbench_World,",
              "            translate = 0.0000 0.0000 0.0000,", "            rotate = %s," % ROT[f], "            scale = 1.0000,", "        }", ""]
    L += ["    }", "}", ""]
    p = os.path.join(MOD, "spriteModels.txt"); open(p, "w", encoding="utf-8", newline="\n").write("\n".join(L)); print("spriteModels", p)

def write_icon():
    im = Image.open(os.path.join(REN, "icon.png")).convert("RGBA"); im = im.crop(im.getbbox())
    s = 30 / max(im.size); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    icon = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); icon.alpha_composite(im, ((32 - im.width) // 2, (32 - im.height) // 2))
    p = os.path.join(MOD, "textures", "Item_ProsthesisWorkbench.png"); icon.save(p); print("icon", p)

# giro del modelo por orientación para Viewpoint (grados alrededor de Z). El modelo mira a +Y. Si en primera persona la
# mesa sale de espaldas o de lado en alguna orientación, se corrige aquí.
VP_DEG = {"S": 0, "E": 90, "N": 180, "W": 270}

def write_viewpoint():
    L = ["id=tocplus-prosthesis-workbench", "name=The Only Cure+ prosthesis workbench (Viewpoint)", "version=1",
         "model.tocplus-bench=tocplus_bench/model.obj"]
    for i, (f, _) in enumerate(FACINGS):
        L.append("bind.%s_%d=tocplus-bench,%d,0,0,0,1" % (NAME, i, VP_DEG[f]))
    p = os.path.join(MOD, "viewpoint", "tocplus_bench.properties")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    NL = chr(10)
    open(p, "w", encoding="utf-8", newline=NL).write(NL.join(L) + NL); print("viewpoint", p)

if __name__ == "__main__":
    write_pack(); write_tiles(); write_sprite_models(); write_icon(); write_viewpoint()
