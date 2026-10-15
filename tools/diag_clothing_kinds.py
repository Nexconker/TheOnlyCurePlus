"""Clasifica la ropa vanilla por ubicación (en el orden de BodyLocations.lua): cuántas prendas son MALLA y cuántas TEXTURA, y qué máscaras usan. Sirve para decidir dónde van las ubicaciones TOC. Uso: python diag_clothing_kinds.py"""
import os, re, glob, collections
M = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media"
order = []
for ln in open(os.path.join(M, "lua", "shared", "NPCs", "BodyLocations.lua"), encoding="utf-8", errors="ignore"):
    m = re.match(r"\s*group:getOrCreateLocation\(ItemBodyLocation\.(\w+)\)", ln)
    if m: order.append(m.group(1))
# constant name -> registry id: ItemBodyLocation.X = "base:..." ; map via lowercase without underscores heuristic
items = {}
for p in glob.glob(os.path.join(M, "scripts", "**", "*.txt"), recursive=True):
    s = open(p, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"item\s+(\w+)\s*\{(.*?)\n\s*\}", s, re.S):
        body = m.group(2)
        bl = re.search(r"BodyLocation\s*=\s*([\w:]+)", body); ci = re.search(r"ClothingItem\s*=\s*(\w+)", body)
        if bl and ci: items[m.group(1)] = (bl.group(1).split(":")[-1].lower(), ci.group(1))
def kind(ci):
    p = os.path.join(M, "clothing", "clothingItems", ci + ".xml")
    if not os.path.exists(p): return None, ()
    x = open(p, encoding="utf-8", errors="ignore").read()
    mm = re.search(r"<m_MaleModel>([^<]*)</m_MaleModel>", x)
    masks = tuple(int(v) for v in re.findall(r"<m_Masks>(\d+)</m_Masks>", x))
    return ("mesh" if mm and mm.group(1).strip() else "tex"), masks
per = collections.defaultdict(lambda: collections.Counter())
masks_per = collections.defaultdict(set)
for it, (bl, ci) in items.items():
    k, ms = kind(ci)
    if k: per[bl][k] += 1; masks_per[bl] |= set(ms)
ARM = {3, 4, 5, 6}; LEG = {7, 8, 9, 10}
for i, loc in enumerate(order):
    key = loc.lower().replace("_", "")
    c = None
    for bl in per:
        if bl.replace("_", "").replace(" ", "").lower() == key: c = bl
    if c is None: continue
    ms = masks_per[c]
    tag = ("ARM " if ms & ARM else "    ") + ("LEG" if ms & LEG else "   ")
    print("%3d %-26s %-12s mesh %3d tex %3d  masks %s" % (i, loc, tag, per[c]["mesh"], per[c]["tex"], sorted(ms)))
