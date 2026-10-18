"""Guía del jugador en PDF interactivo (2026-10-18, "haz la guía lo más interactiva posible en formato pdf y bien
decorada", para que dejen de preguntar en el Workshop). Inglés, como el Workshop.
Interactivo: marcadores (panel lateral), índice y barra de capítulos clicables en todas las páginas, diagrama
"me han mordido" con cajas que llevan a cada sección, preguntas frecuentes que saltan a su respuesta, enlaces externos
y casillas rellenables (lista de la cirugía).
Uso: python make_guide_bg.py (una vez) ; python make_guide_pdf.py -> out/TOCPlus_Guide.pdf (y copia en el repo)"""
import os, shutil
from reportlab.pdfgen import canvas
from guide_kit import *
from guide_content import CHAPTERS, PAGES

OUT = os.path.join(HERE, "out", "TOCPlus_Guide.pdf")
REPO_DOCS = os.path.join(os.path.dirname(HERE), "github", "TheOnlyCurePlus", "docs")
BG = os.path.join(HERE, "out", "guide_bg.jpg"); COVER_BG = os.path.join(HERE, "out", "guide_cover_bg.jpg")

def chrome(c, page_no, total, chapter):
    """Fondo, cabecera con la barra de capítulos (clicable) y pie con navegación."""
    c.drawImage(BG, 0, 0, PW, PH)
    # cabecera
    c.setFillColor(Color(0.05, 0.045, 0.055, 0.92)); c.rect(0, PH - 30, PW, 30, fill=1, stroke=0)
    c.setFillColor(RED); c.rect(0, PH - 31.5, PW, 1.5, fill=1, stroke=0)
    cross(c, 18, PH - 15, 6)
    c.setFillColor(BONE); c.setFont("Title", 12.5); c.drawString(29, PH - 20, "TOC+ GUIDE")
    c.linkRect("", "contents", (10, PH - 30, 100, PH), relative=0, thickness=0)
    x = 108
    for ch in CHAPTERS:
        lab = ch["tab"]; w = pdfmetrics.stringWidth(lab, "Title", 9.4) + 12
        on = chapter == ch["id"]
        if on:
            c.setFillColor(RED); c.roundRect(x, PH - 24, w, 17, 3, fill=1, stroke=0)
        c.setFillColor(BONE if on else GREY); c.setFont("Title", 9.4); c.drawCentredString(x + w / 2, PH - 19.5, lab)
        c.linkRect("", ch["id"], (x, PH - 26, x + w, PH - 4), relative=0, thickness=0)
        x += w + 3
    # pie
    c.setFillColor(Color(0.05, 0.045, 0.055, 0.85)); c.rect(0, 0, PW, 22, fill=1, stroke=0)
    c.setFont("Body", 7.8); c.setFillColor(GREY)
    c.drawString(M, 8, "The Only Cure+ (Field Surgery) 3.3  ·  Player Guide  ·  Build 42")
    c.drawRightString(PW - M, 8, "%d / %d" % (page_no, total))
    bw = 104; button(c, PW / 2 - bw - 4, 4, bw, 14, "CONTENTS", dest="contents", fill=RED2, size=8.5)
    button(c, PW / 2 + 4, 4, bw, 14, "I GOT BITTEN!", dest="bitten", fill=RED2, size=8.5)

def title(c, text, sub=None, y=PH - 70):
    c.setFillColor(Color(0, 0, 0, 0.8)); c.setFont("Title", 30); c.drawString(M + 2, y - 2, text)
    c.setFillColor(BONE); c.drawString(M, y, text)
    w = pdfmetrics.stringWidth(text, "Title", 30)
    c.setFillColor(RED); c.rect(M, y - 7, w, 3.2, fill=1, stroke=0)
    if sub:
        c.setFillColor(GREY); c.setFont("Body", 10.5); c.drawString(M + w + 14, y + 2, sub)
    return y - 16

def build():
    c = canvas.Canvas(OUT, pagesize=(PW, PH))
    c.setTitle("The Only Cure+ — Player Guide"); c.setAuthor("Nexconker"); c.setSubject("Project Zomboid B42 mod guide")
    c.setCreator("TOC+ tools/make_guide_pdf.py")
    c.showOutline()
    total = len(PAGES)
    for i, pg in enumerate(PAGES, 1):
        if pg.get("dest"):
            c.bookmarkPage(pg["dest"], fit="Fit")
            if pg.get("outline"): c.addOutlineEntry(pg["outline"], pg["dest"], level=pg.get("level", 0))
        if pg.get("cover"):
            c.drawImage(COVER_BG, 0, 0, PW, PH)
        else:
            chrome(c, i, total, pg.get("chapter"))
        y = title(c, pg["title"], pg.get("sub")) if pg.get("title") else PH - 60
        pg["draw"](c, y)
        c.showPage()
    c.save()
    print(OUT, total, "páginas")
    if os.path.isdir(REPO_DOCS):
        shutil.copy(OUT, os.path.join(REPO_DOCS, "TOCPlus_Guide.pdf")); print("copiada a", REPO_DOCS)

if __name__ == "__main__":
    build()
