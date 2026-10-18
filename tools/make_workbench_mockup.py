"""Maqueta del banco de prótesis (TOC/UI/ProsthesisWorkbench.lua) con la misma distribución y lógica de dibujo que el
Lua, para enseñarla sin abrir el juego. Uso: TOC_MEDIA=...Dev python make_workbench_mockup.py -> out/preview/workbench_mockup.png
(el avatar sale de out/preview/wb/wb_avatar.png)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import make_workshop as MW
LANG = (sys.argv[1] if len(sys.argv) > 1 else "es").lower()
EN = {'Banco de prótesis': 'Prosthesis Workbench', 'Bases': 'Bases', 'Cabezales': 'Attachments', 'Estadísticas': 'Stats', '* Armazón de prótesis cibernético': '* Cybernetic Prosthesis Frame', 'Armazón de prótesis mecánico': 'Mechanical Prosthesis Frame', 'Base de prótesis de madera': 'Wooden Prosthesis Base', '* Cabezal: mano cibernética': '* Cybernetic Hand Attachment', 'Cabezal: motosierra': 'Chainsaw Attachment', 'Cabezal: gancho': 'Hook Attachment', 'derecha  100%': 'right  100%', 'derecha  74%': 'right  74%', 'izquierda  55%': 'left  55%', 'derecha  96%': 'right  96%', 'derecha  81%': 'right  81%', 'izquierda  60%': 'left  60%', 'Agarre': 'Grip', 'A dos manos': 'Two-handed', 'Combate': 'Combat speed', 'Acciones': 'Action bonus', 'Desgaste': 'Wear', 'Brazo derecho': 'Right arm', 'Brazo izquierdo: nada': 'Left arm: nothing', 'Selección': 'Selected', 'Armazón de prótesis cibernético': 'Cybernetic Prosthesis Frame', 'Cabezal: mano cibernética': 'Cybernetic Hand Attachment', 'Sólo brazo derecho': 'Right arm only', 'Poner base': 'Fit base', 'Montar cabezal': 'Mount attachment', 'Quitar': 'Take off', 'Pintar': 'Paint', 'Cerrar': 'Close'}
def L(t): return EN.get(t, t) if LANG == "en" else t

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
HERE = os.path.dirname(os.path.abspath(__file__))
S = 1.5; W_, H_ = 1000, 560
F = r"C:\Windows\Fonts\NotoSans-Regular.ttf"
fs, fm = ImageFont.truetype(F, int(14 * S)), ImageFont.truetype(F, int(18 * S))
FS, FM = 17, 22
def sc(v): return int(round(v * S))
margin = 50
img = MW.background(sc(W_) + margin * 2, sc(H_) + margin * 2, 5).convert("RGBA").filter(ImageFilter.GaussianBlur(3))
ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); ox = oy = margin
pastes = []
def R(x, y, w, h, fill=None, outline=None, width=1):
    d.rectangle((ox + sc(x), oy + sc(y), ox + sc(x + w) - 1, oy + sc(y + h) - 1), fill=fill, outline=outline, width=width)
def tl(s): return d.textlength(L(s), font=fs) / S
def T(x, y, s, font=fs, fill=(230, 230, 230, 255), right=False):
    s = L(s)
    if right: x = x - d.textlength(s, font=font) / S
    d.text((ox + sc(x), oy + sc(y)), s, font=font, fill=fill)
def tex(path, x, y, w, h, tint=None):
    im = Image.open(path).convert("RGBA").resize((sc(w), sc(h)), Image.LANCZOS)
    if tint:
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (r.point(lambda v: int(v * tint[0])), g.point(lambda v: int(v * tint[1])), b.point(lambda v: int(v * tint[2])), a))
    pastes.append((im, (ox + sc(x), oy + sc(y))))
def fit(s, w):
    if tl(s) <= w: return s
    while len(s) > 3 and tl(s + "...") > w: s = s[:-1]
    return s + "..."
IC = os.path.join(MOD, "ui", "TOC")
th, PAD = 19, 10
R(0, 0, W_, H_, fill=(0, 0, 0, 205), outline=(102, 102, 102, 255)); R(0, 0, W_, th, fill=(40, 40, 40, 235), outline=(102, 102, 102, 255))
title = "Banco de prótesis"; T(W_ / 2 - tl(title) / 2, 0, title); T(W_ - 16, -1, "x", fill=(200, 200, 200, 255))
listW, avatarW = 360, 230
listH = (H_ - th - PAD * 4 - 30) // 2 - FS - 4
PAINT = {"red": (168, 34, 30), "green": (78, 102, 52)}
def listbox(x, y, w, h, rows, sel):
    R(x, y, w, h, fill=(0, 0, 0, 130), outline=(102, 102, 102, 230)); rh = FS + 6
    for i, (name, info, sw) in enumerate(rows):
        ry = y + i * rh
        if i == sel: R(x + 1, ry, w - 2, rh, fill=(178, 89, 38, 80))
        R(x, ry, w, rh, outline=(102, 102, 102, 64))
        T(x + w - 8, ry + 2, info, fill=(178, 178, 178, 255), right=True)
        tx = x + 6
        if sw: R(tx, ry + 4, rh - 8, rh - 8, fill=PAINT[sw] + (255,), outline=(204, 204, 204, 255)); tx += rh - 2
        T(tx, ry + 2, fit(name, w - (tx - x) - tl(info) - 16), fill=(242, 242, 242, 255))
y = th + PAD
T(PAD, y, "Bases")
listbox(PAD, y + FS + 2, listW, listH, [("* Armazón de prótesis cibernético", "derecha  100%", None), ("Armazón de prótesis mecánico", "derecha  74%", None),
                                        ("Base de prótesis de madera", "izquierda  55%", "green")], 1)
y2 = y + FS + 2 + listH + PAD
T(PAD, y2, "Cabezales")
listbox(PAD, y2 + FS + 2, listW, listH, [("* Cabezal: mano cibernética", "derecha  96%", "red"), ("Cabezal: motosierra", "derecha  81%", None),
                                         ("Cabezal: gancho", "izquierda  60%", None)], 1)
ax = PAD + listW + PAD; ah = H_ - th - PAD * 3 - 30
R(ax, th + PAD, avatarW, ah, fill=(20, 20, 23, 153))
av = Image.open(os.path.join(HERE, "out", "preview", "wb", "wb_avatar.png")).convert("RGBA"); av = av.crop(av.getbbox())
s_ = min(sc(avatarW - 10) / av.width, sc(ah - 10) / av.height); av = av.resize((int(av.width * s_), int(av.height * s_)), Image.LANCZOS)
pastes.append((av, (ox + sc(ax) + (sc(avatarW) - av.width) // 2, oy + sc(th + PAD) + (sc(ah) - av.height) // 2)))
# ---- columna de estadísticas (TOC_ProsthesisWorkbench:drawStats / drawCard)
statsX = ax + avatarW + PAD; cw = W_ - statsX - PAD
yy = th + PAD
T(statsX, yy, "Estadísticas", font=fm); yy += FM + 6
ROWH = max(18, FS + 2)
LABELS = ["Agarre", "A dos manos", "Combate", "Acciones", "Desgaste"]
def card(x, y, w, title, base_ic, head_ic, base_n, head_n, t, cmp, warns, accent=False):
    h = 6 + FS + 4 + max(34, FS * 2 + 6) + 4 + 5 * ROWH + len(warns) * (FS + 2) + 6
    R(x, y, w, h, fill=(26, 26, 31, 115), outline=(217, 140, 64, 204) if accent else (102, 102, 102, 204))
    cy = y + 6
    T(x + 8, cy, title, fill=(255, 191, 115, 255) if accent else (230, 230, 230, 255)); cy += FS + 4
    tex(os.path.join(MOD, "textures", base_ic), x + 8, cy, 32, 32)
    T(x + 8 + 35, cy + 8, "+", fill=(178, 178, 178, 255))
    if head_ic: tex(os.path.join(MOD, "textures", head_ic), x + 8 + 46, cy, 32, 32)
    tx = x + 8 + 86; nw = x + w - 8 - tx
    T(tx, cy, fit(base_n, nw), fill=(242, 242, 242, 255)); T(tx, cy + FS + 2, fit(head_n, nw), fill=(242, 242, 242, 255))
    cy += max(34, FS * 2 + 6) + 4
    right = x + w - 8; valW = 46
    barW = max(60, min(120, w - 8 - ROWH - 4 - tl("Combate") - 16 - valW - 18))
    def start(icn, lab):
        tex(os.path.join(IC, "WB_%s.png" % icn), x + 8, cy + 1, ROWH - 2, ROWH - 2, (0.8, 0.8, 0.82))
        T(x + 8 + ROWH + 4, cy + 1, lab, fill=(217, 217, 217, 255))
    def yesno(ok):
        tex(os.path.join(IC, "WB_%s.png" % ("yes" if ok else "no")), right - ROWH, cy + 1, ROWH - 2, ROWH - 2, (0.45, 0.85, 0.4) if ok else (0.9, 0.35, 0.3))
    def arrow(better):
        if better is None: return
        tex(os.path.join(IC, "WB_%s.png" % ("up" if better else "down")), right - valW - barW - 16, cy + 3, ROWH - 6, ROWH - 6, (0.45, 0.85, 0.4) if better else (0.9, 0.35, 0.3))
    def bar(frac, col, text):
        frac = max(0, min(1, frac)); bx, by = right - valW - barW, cy + ROWH // 2 - 4
        R(bx, by, barW, 8, fill=(13, 13, 15, 204)); R(bx, by, barW * frac, 8, fill=tuple(int(c * 255) for c in col) + (242,)); R(bx, by, barW, 8, outline=(115, 115, 115, 153))
        T(right, cy + 1, text, fill=(230, 230, 230, 255), right=True)
    def cmpv(a, b, hi):
        if cmp is None or abs(a - b) < 1e-4: return None
        return a > b if hi else a < b
    start("grip", LABELS[0]); yesno(not t["hook"]); cy += ROWH
    start("twohand", LABELS[1]); yesno(t["two"]); cy += ROWH
    start("combat", LABELS[2]); arrow(cmpv(t["cm"], cmp and cmp["cm"] or 0, True)); bar((t["cm"] - 0.5) / 0.55, (0.85, 0.55, 0.25), "%d%%" % round(t["cm"] * 100)); cy += ROWH
    start("speed", LABELS[3]); arrow(cmpv(t["tb"], cmp and cmp["tb"] or 0, True)); bar(t["tb"] / 6, (0.35, 0.65, 0.9), "+%d" % t["tb"]); cy += ROWH
    wf = 1 - min(1, t["wp"])
    start("wear", LABELS[4]); arrow(cmpv(t["wp"], cmp and cmp["wp"] or 0, False)); bar(wf, (0.9 - 0.5 * wf, 0.35 + 0.5 * wf, 0.3), "%.2f" % t["wp"]); cy += ROWH
    for wt in warns: T(x + 8, cy, fit(wt, w - 16), fill=(242, 115, 89, 255)); cy += FS + 2
    return h
cyber = {"hook": False, "two": True, "cm": 1.0, "tb": 5, "wp": 0.084}
mech_saw = {"hook": True, "two": False, "cm": 0.97 * 0.98, "tb": 2, "wp": 0.4 * 1.5}
yy += card(statsX, yy, cw, "Brazo derecho", "Item_BaseCyber.png", "Item_HeadCyberHand.png", "Armazón de prótesis cibernético", "Cabezal: mano cibernética", cyber, None, []) + 6
T(statsX + 2, yy, "Brazo izquierdo: nada", fill=(153, 153, 153, 255)); yy += FS + 6
yy += card(statsX, yy, cw, "Selección", "Item_BaseMech.png", "Item_HeadChainsaw.png", "Armazón de prótesis mecánico", "Cabezal: motosierra", mech_saw, cyber, ["Sólo brazo derecho"], accent=True)
by = H_ - PAD - 25
for i, (lab, en) in enumerate((("Poner base", True), ("Montar cabezal", True), ("Quitar", False), ("Pintar", True), ("Cerrar", True))):
    x = PAD + i * 126
    R(x, by, 120, 25, fill=(0, 0, 0, 255), outline=(178, 178, 178, 255) if en else (90, 90, 90, 255))
    T(x + 60 - tl(lab) / 2, by + 3, lab, fill=(240, 240, 240, 255) if en else (110, 110, 110, 255))
img.alpha_composite(ov)
for im, pos in pastes: img.alpha_composite(im, pos)
img.convert("RGB").save(os.path.join(HERE, "out", "preview", "workbench_mockup%s.png" % ("_en" if LANG == "en" else ""))); print("ok")
