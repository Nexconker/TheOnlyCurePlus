"""Extrae subtexturas de un .pack de PZ buscando los nombres y la tabla de ints que les sigue."""
import sys, re, struct, io, os
from PIL import Image
pack, prefix, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
d = open(pack, "rb").read()
pngs = [m.start() for m in re.finditer(rb"\x89PNG\r\n\x1a\n", d)]
print("png chunks:", len(pngs))
entries = []
for m in re.finditer(re.escape(prefix.encode()) + rb"[A-Za-z0-9_]*", d):
    name = m.group(0).decode(); end = m.end()
    for endian in ("<", ">"):
        vals = struct.unpack(endian + "8i", d[end:end + 32])
        x, y, w, h, ox, oy, ow, oh = vals
        if 0 <= x < 8192 and 0 <= y < 8192 and 0 < w <= 2048 and 0 < h <= 2048 and 0 <= ox <= 4096 and 0 <= oy <= 4096 and 0 < ow <= 4096 and 0 < oh <= 4096:
            entries.append((name, endian, vals, end)); break
print("entries:", len(entries))
for name, endian, vals, pos in entries:
    nxt = min([p for p in pngs if p > pos], default=None)
    if nxt is None: continue
    # PNG length: find IEND
    iend = d.find(b"IEND", nxt) + 8
    page = Image.open(io.BytesIO(d[nxt:iend])).convert("RGBA")
    x, y, w, h, ox, oy, ow, oh = vals
    sub = page.crop((x, y, x + w, y + h))
    canvas = Image.new("RGBA", (ow, oh), (0, 0, 0, 0)); canvas.paste(sub, (ox, oy))
    canvas.save(os.path.join(outdir, name + ".png"))
    print("%-28s endian=%s x=%d y=%d w=%d h=%d off=(%d,%d) orig=%dx%d page=%s" % (name, endian, x, y, w, h, ox, oy, ow, oh, page.size))
