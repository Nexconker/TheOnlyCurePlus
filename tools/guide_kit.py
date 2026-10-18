"""Piezas de maquetación de la guía PDF (make_guide_pdf.py): tema oscuro de las tarjetas del Workshop, barra de
navegación clicable, marcadores, cajas, pasos con iconos, tablas y casillas rellenables (AcroForm)."""
import os
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame, Table, TableStyle, Image as RLImage, Spacer, KeepInFrame
from PIL import Image as PILImage

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_TEX = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\textures"
RENDERS = os.path.join(HERE, "out", "workshop", "renders")
CARDS = os.path.join(HERE, "out", "workshop", "en")
CACHE = os.path.join(HERE, "out", "guide_cache"); os.makedirs(CACHE, exist_ok=True)

pdfmetrics.registerFont(TTFont("Title", r"C:\Windows\Fonts\impact.ttf"))
pdfmetrics.registerFont(TTFont("Body", r"C:\Windows\Fonts\bahnschrift.ttf"))
pdfmetrics.registerFont(TTFont("BodyB", r"C:\Windows\Fonts\segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("BodyI", r"C:\Windows\Fonts\segoeuii.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")

PW, PH = 842, 595                                   # A4 apaisado
M = 34                                              # margen
TOP = 58                                            # alto de la cabecera
BOT = 34                                            # alto del pie
RED = HexColor("#C42026"); RED2 = HexColor("#780E14"); BONE = HexColor("#ECE2CE"); GREY = HexColor("#96969B")
DARK = HexColor("#0E0D0F"); PANEL = Color(0.125, 0.118, 0.135, 0.82); PANEL2 = Color(0.18, 0.17, 0.19, 0.92)
EDGE = Color(1, 1, 1, 0.07)
GOLD = HexColor("#F0C46E"); GREEN = HexColor("#7FC97A"); BLUE = HexColor("#7FB4E8")

ST = {
    "body": ParagraphStyle("body", fontName="Body", fontSize=10.8, leading=14.6, textColor=BONE),
    "small": ParagraphStyle("small", fontName="Body", fontSize=9.4, leading=12.4, textColor=BONE),
    "tiny": ParagraphStyle("tiny", fontName="Body", fontSize=7.6, leading=9.6, textColor=GREY),
    "h2": ParagraphStyle("h2", fontName="Title", fontSize=17, leading=20, textColor=GOLD, spaceAfter=3),
    "h3": ParagraphStyle("h3", fontName="Title", fontSize=12.5, leading=15, textColor=BONE, spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=8.8, leading=11, textColor=BONE),
    "cellh": ParagraphStyle("cellh", fontName="Title", fontSize=9.6, leading=11, textColor=GOLD),
    "center": ParagraphStyle("center", fontName="Body", fontSize=9.2, leading=12, textColor=BONE, alignment=TA_CENTER),
}

def P(text, style="body", **kw):
    st = ST[style] if not kw else ParagraphStyle("x", parent=ST[style], **kw)
    return Paragraph(text, st)

def link(text, dest, color="#F0C46E"):
    """Enlace interno a un destino (bookmark) dentro de un párrafo."""
    return '<a href="#%s" color="%s"><u>%s</u></a>' % (dest, color, text)

def ext(text, url, color="#7FB4E8"):
    return '<a href="%s" color="%s"><u>%s</u></a>' % (url, color, text)

def icon_path(name, size=64):
    """Icono 32x32 del mod ampliado sin suavizar (pixel art) y cacheado."""
    if name.startswith("v:"):      # icono vanilla extraído de UI.pack/UI2.pack con unpack_ui.py
        src = os.path.join(HERE, "out", "vanilla_icons2", "Item_%s.png" % name[2:])
    else:
        src = os.path.join(MOD_TEX, name if name.endswith(".png") else "Item_%s.png" % name)
    dst = os.path.join(CACHE, "ico_%s_%d.png" % (os.path.basename(src)[:-4], size))
    if not os.path.exists(dst):
        PILImage.open(src).convert("RGBA").resize((size, size), PILImage.NEAREST).save(dst)
    return dst

def render_path(name, folder=RENDERS, maxw=900):
    """Render recortado a su contenido (transparente), cacheado."""
    src = os.path.join(folder, name + ".png")
    dst = os.path.join(CACHE, "r_%s_%d.png" % (name, maxw))
    if not os.path.exists(dst):
        im = PILImage.open(src).convert("RGBA"); bb = im.split()[3].getbbox(); im = im.crop(bb)
        k = min(1.0, maxw / max(im.width, im.height))     # maxw = lado mayor (el PDF guarda los PNG sin pérdida: que no pesen)
        if k < 1: im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), PILImage.LANCZOS)
        im.save(dst, optimize=True)
    return dst

def card_path(name, maxw=1100):
    src = os.path.join(CARDS, name + ".png")
    dst = os.path.join(CACHE, "c_%s.jpg" % name)
    if not os.path.exists(dst):
        im = PILImage.open(src).convert("RGB"); im = im.resize((maxw, int(im.height * maxw / im.width)), PILImage.LANCZOS)
        im.save(dst, quality=85)
    return dst

def img_fit(c, path, x, y, w, h, align="center"):
    """Dibuja una imagen dentro de la caja (x, y abajo-izquierda) manteniendo proporción. Devuelve la caja usada."""
    iw, ih = PILImage.open(path).size
    s = min(w / iw, h / ih); dw, dh = iw * s, ih * s
    dx = x + (w - dw) / 2 if align == "center" else (x if align == "left" else x + w - dw)
    dy = y + (h - dh) / 2
    c.drawImage(path, dx, dy, dw, dh, mask="auto")
    return dx, dy, dw, dh

def panel(c, x, y, w, h, fill=PANEL, stroke=None, r=7):
    c.saveState(); c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke); c.setLineWidth(1)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke else 0); c.restoreState()

def flow(c, items, x, y, w, h, pad=8):
    """Coloca flowables en una caja; si no caben, los encoge (KeepInFrame) para no perder texto."""
    f = Frame(x + pad, y + pad, w - 2 * pad, h - 2 * pad, 0, 0, 0, 0, showBoundary=0)
    f.addFromList([KeepInFrame(w - 2 * pad, h - 2 * pad, items, mode="shrink")], c)

def cross(c, x, y, r, col=RED):
    c.saveState(); c.setFillColor(col)
    c.rect(x - r, y - r / 3, 2 * r, 2 * r / 3, fill=1, stroke=0); c.rect(x - r / 3, y - r, 2 * r / 3, 2 * r, fill=1, stroke=0)
    c.restoreState()

def button(c, x, y, w, h, text, dest=None, url=None, fill=RED, size=11):
    """Botón con enlace interno (dest) o externo (url)."""
    c.saveState()
    c.setFillColor(Color(0, 0, 0, 0.45)); c.roundRect(x + 2, y - 2, w, h, 5, fill=1, stroke=0)
    c.setFillColor(fill); c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
    c.setFillColor(BONE); c.setFont("Title", size); c.drawCentredString(x + w / 2, y + h / 2 - size * 0.36, text)
    c.restoreState()
    if dest: c.linkRect("", dest, (x, y, x + w, y + h), relative=0, thickness=0)
    if url: c.linkURL(url, (x, y, x + w, y + h), relative=0, thickness=0)

def callout(kind, text):
    """Caja de aviso como flowable: tip / warn / info."""
    col = {"tip": GREEN, "warn": RED, "info": BLUE}[kind]
    label = {"tip": "TIP", "warn": "WARNING", "info": "GOOD TO KNOW"}[kind]
    t = Table([[P('<font name="Title" color="%s">%s</font>' % (col.hexval().replace("0x", "#"), label), "small"), P(text, "small")]],
              colWidths=[56, None])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PANEL2), ("LINEBEFORE", (0, 0), (0, -1), 3, col),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t

def table(rows, widths, header=True, zebra=True, valign="MIDDLE"):
    """Tabla del tema: filas = listas de str/flowables (str -> párrafo 'cell'); la primera fila es la cabecera."""
    data = []
    for i, r in enumerate(rows):
        data.append([(P(x, "cellh" if (header and i == 0) else "cell") if isinstance(x, str) else x) for x in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), valign), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
          ("LINEBELOW", (0, 0), (-1, -1), 0.3, Color(1, 1, 1, 0.08))]
    if header: st += [("BACKGROUND", (0, 0), (-1, 0), RED2), ("LINEBELOW", (0, 0), (-1, 0), 1.2, RED)]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            st.append(("BACKGROUND", (0, i), (-1, i), PANEL2 if i % 2 else PANEL))
    t.setStyle(TableStyle(st))
    return t

def icon_cell(name, text, size=22):
    """Celda con icono + texto."""
    t = Table([[RLImage(icon_path(name), size, size), P(text, "cell")]], colWidths=[size + 4, None])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t

def checkbox(c, name, x, y, size=11, tooltip=""):
    """Casilla rellenable (se puede marcar en cualquier lector de PDF)."""
    c.acroForm.checkbox(name=name, tooltip=tooltip or name, x=x, y=y, size=size, buttonStyle="check",
                        borderColor=GOLD, fillColor=Color(0.14, 0.13, 0.15), textColor=GOLD, forceBorder=True, borderWidth=1)
