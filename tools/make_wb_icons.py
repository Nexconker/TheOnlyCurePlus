"""Iconos de la columna de estadísticas del banco de prótesis (2026-10-17, "mejora la UI de estadísticas con algún
dibujo"): media/ui/TOC/WB_<nombre>.png, 32x32 blancos con contorno oscuro; la UI los tiñe. Se dibujan a 128 px y se
reducen para que salgan suaves.
Uso: TOC_MEDIA=...Dev python make_wb_icons.py"""
import os, math
from PIL import Image, ImageDraw, ImageFilter

MOD = os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlusDev\42\media")
OUT = os.path.join(MOD, "ui", "TOC")
N = 128; W = (255, 255, 255, 255)

def canvas(): return Image.new("RGBA", (N, N), (0, 0, 0, 0))

def finish(im, name):
    a = im.split()[3]
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0)); shadow.putalpha(a.filter(ImageFilter.MaxFilter(9)).point(lambda v: int(v * 0.85)))
    out = Image.alpha_composite(shadow, im).resize((32, 32), Image.LANCZOS)
    out.save(os.path.join(OUT, "WB_%s.png" % name)); print("icon", name)

def hand(d, ox=0, oy=0, s=1.0, closed=False):
    """Mano esquemática: palma y cuatro dedos (cerrados = puño) más pulgar."""
    def P(x, y): return (ox + x * s, oy + y * s)
    d.rounded_rectangle([P(34, 58), P(94, 112)], radius=int(16 * s), fill=W)
    for i, x in enumerate((36, 52, 68, 84)):
        top = 58 - (14 if closed else (34 + (8 if i in (1, 2) else 0)))
        d.rounded_rectangle([P(x, top), P(x + 13, 70)], radius=int(6 * s), fill=W)
    d.rounded_rectangle([P(14, 66), P(40, 80)], radius=int(7 * s), fill=W)

def grip():
    im = canvas(); d = ImageDraw.Draw(im); hand(d, 0, 4, 1.0, closed=True)
    d.rounded_rectangle([20, 56, 108, 70], radius=6, fill=(0, 0, 0, 0))     # mango que se agarra
    d.rounded_rectangle([20, 58, 108, 68], radius=5, fill=W)
    finish(im, "grip")

def twohand():
    im = canvas(); d = ImageDraw.Draw(im)
    hand(d, -14, 10, 0.78); hand(d, 42, 10, 0.78)
    finish(im, "twohand")

def combat():
    im = canvas(); d = ImageDraw.Draw(im)
    for sg in (1, -1):                                                    # dos espadas cruzadas
        c, s_ = math.cos(math.radians(45 * sg)), math.sin(math.radians(45 * sg))
        def R(x, y): return (64 + x * c - y * s_, 64 + x * s_ + y * c)
        d.polygon([R(-5, -52), R(5, -52), R(5, 26), R(-5, 26)], fill=W)
        d.polygon([R(-5, -52), R(0, -62), R(5, -52)], fill=W)
        d.polygon([R(-18, 26), R(18, 26), R(18, 33), R(-18, 33)], fill=W)
        d.polygon([R(-4, 33), R(4, 33), R(4, 52), R(-4, 52)], fill=W)
    finish(im, "combat")

def speed():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([16, 16, 112, 112], outline=W, width=12)                     # reloj
    d.line([64, 64, 64, 32], fill=W, width=10); d.line([64, 64, 88, 76], fill=W, width=10)
    d.ellipse([56, 56, 72, 72], fill=W)
    finish(im, "speed")

def wear():
    im = canvas(); d = ImageDraw.Draw(im)                                  # llave inglesa
    c, s_ = math.cos(math.radians(-45)), math.sin(math.radians(-45))
    def R(x, y): return (64 + x * c - y * s_, 64 + x * s_ + y * c)
    d.polygon([R(-8, -20), R(8, -20), R(8, 50), R(-8, 50)], fill=W)
    cx, cy = R(0, -34); d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=W)
    jx, jy = R(0, -48); d.ellipse([jx - 12, jy - 12, jx + 12, jy + 12], fill=(0, 0, 0, 0))
    d.polygon([R(-9, -62), R(9, -62), R(9, -40), R(-9, -40)], fill=(0, 0, 0, 0))
    finish(im, "wear")

def check():
    im = canvas(); d = ImageDraw.Draw(im); d.line([24, 66, 54, 96, 106, 36], fill=W, width=18, joint="curve"); finish(im, "yes")

def cross():
    im = canvas(); d = ImageDraw.Draw(im); d.line([32, 32, 96, 96], fill=W, width=18); d.line([96, 32, 32, 96], fill=W, width=18); finish(im, "no")

def arrow(up):
    im = canvas(); d = ImageDraw.Draw(im)
    d.polygon([(64, 18), (108, 70), (20, 70)] if up else [(64, 110), (108, 58), (20, 58)], fill=W)
    d.rectangle([48, 66, 80, 106] if up else [48, 22, 80, 62], fill=W)
    finish(im, "up" if up else "down")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    grip(); twohand(); combat(); speed(); wear(); check(); cross(); arrow(True); arrow(False)
