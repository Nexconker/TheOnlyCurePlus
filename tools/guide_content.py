"""Contenido de la guía PDF (make_guide_pdf.py). Todos los datos salen del código del mod 3.3 (recetas de scripts/,
StaticData.lua, SurgeryPlan.lua, PostOp.lua, LegMobility.lua, sandbox-options.txt...): si cambia el mod, cambiar aquí."""
from guide_kit import *
from reportlab.platypus import Spacer, Image as RLImage

WORKSHOP = "https://steamcommunity.com/sharedfiles/filedetails/?id=3818733381"
ISSUES = "https://github.com/Nexconker/TheOnlyCurePlus/issues"
GITHUB = "https://github.com/Nexconker/TheOnlyCurePlus"
KOFI = "https://ko-fi.com/nexconker"

CHAPTERS = [
    {"id": "bitten", "tab": "BITTEN?", "name": "I got bitten!", "icon": "SeveredHand", "desc": "What to do, in order. Start here."},
    {"id": "infection", "tab": "INFECTION", "name": "Infection & diagnosis", "icon": "FieldSurgeryGuide", "desc": "Examine Wound, the cure window, symptoms."},
    {"id": "surgery", "tab": "SURGERY", "name": "Field surgery", "icon": "BoneSaw", "desc": "Starting it, the checklist, risk, screams, fainting."},
    {"id": "postop", "tab": "POST-OP", "name": "After the operation", "icon": "SurgicalKit", "desc": "Shock, healing, sepsis, cleaning the stump."},
    {"id": "arms", "tab": "ARMS", "name": "Modular arm prostheses", "icon": "BaseMech", "desc": "Bases, attachments, what fits, stats, repair."},
    {"id": "recipes", "tab": "RECIPES", "name": "Recipes & loot", "icon": "HeadMechHand", "desc": "Every prosthesis, crutch, tourniquet and kit."},
    {"id": "legs", "tab": "LEGS", "name": "Legs, crutches & crawling", "icon": "PegLeg", "desc": "How you move with each leg."},
    {"id": "workbench", "tab": "BENCH", "name": "Workbench & paint", "icon": "ProsthesisWorkbench", "desc": "Build it, fit parts, paint them."},
    {"id": "weapons", "tab": "WEAPONS", "name": "Chainsaw & bayonet", "icon": "HeadChainsaw", "desc": "Weapon attachments for the right arm."},
    {"id": "options", "tab": "OPTIONS", "name": "Traits, skills & sandbox", "icon": "HeadCyberHand", "desc": "Amputee traits, skills, every option."},
    {"id": "faq", "tab": "FAQ", "name": "FAQ & help", "icon": "CyberLeg", "desc": "The questions people ask most."},
]
CH = {c["id"]: c for c in CHAPTERS}
X0, X1 = M, PW - M
YB = 30                                   # base del contenido (encima del pie)

def col(c, items, x, ytop, w, ybot=YB, pad=9, fill=PANEL, stroke=EDGE):
    panel(c, x, ybot, w, ytop - ybot, fill=fill, stroke=stroke)
    flow(c, items, x, ybot, w, ytop - ybot, pad=pad)

def gallery(c, items, x, y, w, h, label_size=9.5, folder=None):
    """Fila de renders con su rótulo debajo: items = [(render, rótulo, destino o None)]."""
    n = len(items); gw = w / n
    for i, (r, lab, dest) in enumerate(items):
        gx = x + i * gw
        img_fit(c, render_path(r, maxw=340) if folder is None else card_path(r), gx + 3, y + 14, gw - 6, h - 16)
        c.setFillColor(GOLD); c.setFont("Title", label_size); c.drawCentredString(gx + gw / 2, y + 2, lab)
        if dest: c.linkRect("", dest, (gx, y, gx + gw, y + h), relative=0, thickness=0)

def icon_strip(c, icons, x, y, size=34, gap=8, dest=None):
    """Fila de iconos grandes (pixel art)."""
    for i, ic in enumerate(icons):
        img_fit(c, icon_path(ic, 96), x + i * (size + gap), y, size, size)
    if dest: c.linkRect("", dest, (x, y, x + len(icons) * (size + gap), y + size), relative=0, thickness=0)

def bullets(lines, style="body"):
    return [P('<font color="#C42026">+</font>&nbsp; ' + ln, style, leftIndent=10, firstLineIndent=-10, spaceAfter=2.5) for ln in lines]

def arrow(c, x0, y0, x1, y1, col=RED, w=2.2):
    import math
    c.saveState(); c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(w)
    a = math.atan2(y1 - y0, x1 - x0); hx, hy = x1 - 7 * math.cos(a), y1 - 7 * math.sin(a)
    c.line(x0, y0, hx, hy)
    p = c.beginPath(); p.moveTo(x1, y1)
    p.lineTo(hx + 4.5 * math.sin(a), hy - 4.5 * math.cos(a)); p.lineTo(hx - 4.5 * math.sin(a), hy + 4.5 * math.cos(a)); p.close()
    c.drawPath(p, fill=1, stroke=0); c.restoreState()

def node(c, x, y, w, h, head, text, dest, col=RED2, icon=None):
    """Caja clicable del diagrama."""
    panel(c, x, y, w, h, fill=PANEL2, stroke=col)
    c.setFillColor(col); c.roundRect(x, y + h - 17, w, 17, 7, fill=1, stroke=0); c.rect(x, y + h - 17, w, 8, fill=1, stroke=0)
    c.setFillColor(BONE); c.setFont("Title", 10.5); c.drawString(x + 7, y + h - 12.5, head)
    tx = x + 6
    if icon:
        img_fit(c, icon_path(icon), x + 5, y + 5, 28, h - 26); tx = x + 37
    flow(c, [P(text, "small")], tx - 6, y, x + w - tx + 6, h - 17, pad=5)
    if dest:
        c.setFillColor(GOLD); c.setFont("Title", 7.5); c.drawRightString(x + w - 6, y + 4, "GO >")
        c.linkRect("", dest, (x, y, x + w, y + h), relative=0, thickness=0)

# ======================================================================================== portada
def p_cover(c, y):
    img_fit(c, render_path("hero_m", maxw=760), 470, 30, 220, 470)
    img_fit(c, render_path("cyber_grip", maxw=760), 600, 40, 240, 420)
    img_fit(c, render_path("hero_f", maxw=760), 380, 40, 170, 360)
    c.setFillColor(Color(0, 0, 0, 0.85)); c.setFont("Title", 56); c.drawString(M + 3, PH - 120, "THE ONLY CURE")
    c.setFillColor(BONE); c.drawString(M, PH - 117, "THE ONLY CURE")
    c.setFillColor(RED); c.setFont("Title", 70); c.drawString(M, PH - 190, "+")
    c.setFillColor(BONE); c.setFont("Title", 42); c.drawString(M + 48, PH - 180, "FIELD SURGERY")
    c.setFillColor(RED); c.rect(M, PH - 196, 360, 4, fill=1, stroke=0)
    c.setFillColor(GOLD); c.setFont("Title", 30); c.drawString(M, PH - 236, "PLAYER GUIDE")
    c.setFillColor(GREY); c.setFont("Body", 12); c.drawString(M, PH - 256, "Version 3.3  ·  Project Zomboid Build 42  ·  Singleplayer and multiplayer")
    flow(c, [P("Everything you need to survive a bite, cut the limb off properly, heal, and get back on your feet "
               "(or onto a mechanical one). Every box, tab and line marked like " + link("this", "contents") +
               " is clickable. Use the bookmarks panel of your PDF reader to jump around.", "body")], M - 8, PH - 350, 340, 90)
    button(c, M, 150, 160, 30, "START: CONTENTS", dest="contents", size=13)
    button(c, M + 172, 150, 160, 30, "I GOT BITTEN!", dest="bitten", size=13)
    button(c, M, 110, 160, 30, "FAQ", dest="faq", fill=RED2, size=13)
    button(c, M + 172, 110, 160, 30, "WORKSHOP PAGE", url=WORKSHOP, fill=RED2, size=13)
    c.setFillColor(GREY); c.setFont("Body", 8.5)
    c.drawString(M, 40, "Fork of ZioPao's The Only Cure (GPL-3.0). Guide made for The Only Cure+ by Nexconker.")

# ======================================================================================== índice
def p_contents(c, y):
    cols, rows = 4, 3; gw = (X1 - X0 - 3 * 10) / cols; gh = (y - YB - 2 * 10) / rows
    for i, ch in enumerate(CHAPTERS + [{"id": "support", "name": "Compatibility & support", "icon": "HeadHook",
                                         "desc": "Other mods, multiplayer, bug reports, Ko-fi."}]):
        cx = X0 + (i % cols) * (gw + 10); cy = y - (i // cols + 1) * gh - (i // cols) * 10
        panel(c, cx, cy, gw, gh, fill=PANEL, stroke=Color(1, 1, 1, 0.08))
        c.setFillColor(RED); c.rect(cx, cy + gh - 4, gw, 4, fill=1, stroke=0)
        img_fit(c, icon_path(ch["icon"], 96), cx + 10, cy + gh - 70, 54, 54)
        c.setFillColor(GOLD); c.setFont("Title", 22); c.drawRightString(cx + gw - 10, cy + gh - 34, "%02d" % (i + 1))
        flow(c, [P(ch["name"], "h3"), P(ch["desc"], "small")], cx + 4, cy + 4, gw - 8, gh - 80, pad=6)
        c.linkRect("", ch["id"], (cx, cy, cx + gw, cy + gh), relative=0, thickness=0)

# ======================================================================================== me han mordido
def p_bitten(c, y):
    t = y - 6
    node(c, X0, t - 70, 170, 70, "1. WHERE IS THE BITE?", "Hand, forearm, upper arm, foot, calf or thigh: it can be cut off. "
         "Head, neck, torso or groin: no surgery can save you.", "infection", icon="SeveredHand")
    node(c, X0 + 200, t - 70, 170, 70, "2. EXAMINE THE WOUND", "Health panel, right-click the wound. Needs First Aid 2 or the "
         "Field Amputation Guide. A scratch may be clean.", "examine", icon="FieldSurgeryGuide")
    node(c, X0 + 400, t - 70, 170, 70, "3. YOU HAVE LITTLE TIME", "Amputate inside the cure window (first 20% of the infection) "
         "and it is gone. Up to 40% it is a gamble.", "curewindow", icon="v:PillsPainkiller")
    node(c, X0 + 600, t - 70, 174, 70, "4. GATHER THE KIT", "Tourniquet worn, disinfectant, painkillers, a blade, a saw, needle "
         "and thread, a bandage.", "checklist", icon="SurgicalKit")
    for xa in (X0 + 170, X0 + 370, X0 + 570): arrow(c, xa + 3, t - 35, xa + 27, t - 35)
    t2 = t - 112
    node(c, X0 + 600, t2 - 70, 174, 70, "5. OPERATE", "Saw > Amputate > limb, or health panel. Read the risk window, "
         "then press Operate. Somewhere closed: screams carry.", "start", icon="BoneSaw")
    node(c, X0 + 400, t2 - 70, 170, 70, "6. FIRST HOURS", "Shock and blood loss. Bandage, rest, eat and drink. Keep the "
         "stump clean or sepsis starts.", "postop", icon="v:Antibiotics")
    node(c, X0 + 200, t2 - 70, 170, 70, "7. HEALING", "The stump closes in 5 to 10 days (faster with skill). "
         "Cauterizing at a fire closes it at once.", "healing", icon="LegTourniquet")
    node(c, X0, t2 - 70, 170, 70, "8. BACK ON YOUR FEET", "Crutch for a leg, then a prosthesis: arm base + attachment, "
         "or a prosthetic leg.", "arms", icon="BaseMech")
    arrow(c, X0 + 687, t - 74, X0 + 687, t2 + 2)
    for xa in (X0 + 600, X0 + 400, X0 + 200): arrow(c, xa - 3, t2 - 35, xa - 27, t2 - 35)
    # recuadros de abajo
    yb = t2 - 82
    col(c, [P("COMMON MISTAKES", "h2")] + bullets([
        "Operating in the open: each scream is heard up to <b>25 tiles</b> away. Painkillers and alcohol make it quieter.",
        "No tourniquet: heavy bleeding while sawing (+15% failure chance). Make one from ripped sheets or a belt and a stick, and <b>wear it</b> on that limb.",
        "Waiting too long: past 40% of the infection the surgery no longer cures you.",
        "Leaving the stump dirty: sepsis. Clean it from the health panel and keep it bandaged.",
    ], "small"), X0, yb, 470)
    col(c, [P("NOT SURE IT IS INFECTED?", "h2"), P("Bites are the dangerous ones, but scratches and lacerations can carry "
        "the virus too. Use " + link("Examine Wound", "examine") + ": doctors get a clear answer, everyone else gets a "
        "hunch. Symptoms (chills, fever, burning wound) also tell you it is in your blood.", "small"),
        Spacer(1, 4), callout("tip", "The surgery window shows every missing item before you start, and the risk if you are "
                              "skilled enough to judge it. Pressing <b>No</b> costs nothing.")], X0 + 480, yb, X1 - X0 - 480)

# ======================================================================================== infección
def p_infection(c, y):
    c.bookmarkHorizontal("examine", 0, y)
    w1 = 360
    col(c, [P("EXAMINE WOUND", "h2"),
            P("Health panel > right-click a part with a bite, scratch, cut or deep wound > <b>Examine Wound</b>.", "body")] +
        bullets(["Needs <b>First Aid 2</b> (sandbox <i>DiagnosisMinDoctor</i>) or having read the <b>Field Amputation Guide</b>.",
                 "Takes about 250 ticks, less with First Aid. Gives First Aid XP.",
                 "Accuracy grows with First Aid and with how far the infection has gone. A miss can say \"unsure\" or the wrong answer.",
                 "First Aid 4+: clear wording (\"infected with the Knox virus\" / \"looks clean\"). Below that: a hunch (\"Probably infected\").",
                 "The health panel remembers the result: <i>Examined: infected (3 h ago)</i>."], "small") +
        [Spacer(1, 5), callout("info", "The guide is literature: reading it teaches the surgery. Doctors, nurses, paramedics, "
                               "vets and medics start knowing it. It spawns in clinics, hospitals, bookstores and libraries.")],
        X0, y, w1, ybot=y - 290)
    panel(c, X0, YB, w1, y - 298 - YB, stroke=EDGE)
    img_fit(c, render_path("stumps", maxw=420), X0 + 6, YB + 4, 150, y - 306 - YB)
    flow(c, [P("WHAT CAN BE CUT", "h3")] + bullets(["Hand, forearm, upper arm", "Foot, lower leg, thigh",
             "Not the head, neck, torso or groin: a bite there cannot be cut out."], "small"), X0 + 150, YB, w1 - 150, y - 298 - YB, pad=8)
    c.bookmarkHorizontal("curewindow", 0, y)
    gx, gy, gw, gh = X0 + w1 + 12, y - 128, X1 - X0 - w1 - 12, 128
    panel(c, gx, gy, gw, gh, stroke=EDGE)
    c.setFillColor(GOLD); c.setFont("Title", 17); c.drawString(gx + 10, gy + gh - 24, "THE CURE WINDOW")
    c.setFillColor(BONE); c.setFont("Body", 9.4)
    c.drawString(gx + 14, gy + gh - 42, "Amputate the infected limb before 20% and you are cured. From 20% to 40% the chance")
    c.drawString(gx + 14, gy + gh - 54, "drops to zero. After that the surgery no longer helps.")
    bx, by, bw, bh = gx + 14, gy + 30, gw - 28, 24
    for a, b, colr, lab in [(0, 20, GREEN, "CURED"), (20, 40, GOLD, "GAMBLE"), (40, 100, RED, "TOO LATE")]:
        c.setFillColor(colr); c.rect(bx + bw * a / 100, by, bw * (b - a) / 100, bh, fill=1, stroke=0)
        c.setFillColor(DARK); c.setFont("Title", 11); c.drawCentredString(bx + bw * (a + b) / 200, by + 8, lab)
    c.setFillColor(GREY); c.setFont("Body", 8)
    for v in (0, 20, 40, 100): c.drawCentredString(bx + bw * v / 100, by - 10, "%d%%" % v)
    c.drawRightString(gx + gw - 14, gy + 6, "% = progress of the vanilla Knox infection (sandbox CureWindow 20, LateGambleWindow 40)")
    col(c, [P("SYMPTOMS", "h3"), P("Rolled every hour while infected (sandbox <i>ShowSymptoms</i>):", "small"),
            table([["Infection", "Chance / hour", "You hear"],
            ["early", "15%", "\"Chills.\""], ["inside the window", "35%", "\"I am sweating and my wound burns.\""],
            ["past the window", "50%", "\"Fever. My head is pounding.\""], ["late", "60%", "\"I can barely stand. It is in my blood.\""]],
            [96, 74, None]), Spacer(1, 8),
            callout("warn", "By default you are <b>not told</b> whether the surgery cured you (sandbox <i>RevealOutcome</i>). "
                    "Watch the symptoms: if the fever stays, it was too late or the bite that matters is somewhere else."),
            Spacer(1, 6), callout("tip", "Scratches and lacerations can carry the virus too, just less often than bites. "
                                  "Examine them before you reach for the saw.")], gx, gy - 8, gw)


# ======================================================================================== cirugía 1: empezar
def p_surgery1(c, y):
    c.bookmarkHorizontal("start", 0, y)
    w1 = 390
    col(c, [P("HOW TO START", "h2"),
            P("<b>On yourself:</b> right-click a saw in your inventory > <b>Amputate</b> > choose the limb.", "body"),
            P("<b>On yourself or another player:</b> health panel > right-click the body part > <b>Amputate</b> > choose the saw "
              "(or drag the saw onto the part). The patient must stay within 3 tiles and not move.", "body"), Spacer(1, 4)] +
        bullets(["Arms: <b>hand, forearm, upper arm</b>. Legs: <b>foot, lower leg, thigh</b>. Cutting higher also removes everything below.",
                 "You cannot cut your own upper arm or thigh: someone else must do it (sandbox <i>SelfAmputationHigh</i> allows it).",
                 "Rings, gloves and watches on the lost part drop; the item in that hand is unequipped.",
                 "The severed limb drops on the floor (it rots like food)."], "small") +
        [Spacer(1, 4), P("THE SURGERY WINDOW", "h3"),
         P("Nothing happens until you confirm. The window lists each step as <b>[+]</b> ready, <b>[~]</b> partial or <b>[-]</b> "
           "missing, with what is missing, warnings (tired, shaking hands, drunk, one hand, fainting) and, if your First Aid is 3+ "
           "or you know the surgery, the <b>estimated risk</b> and <b>chance of fainting</b>. It ends with <i>There is no going "
           "back.</i> and the buttons <b>Operate</b> / <b>No</b>.", "small")], X0, y, w1, ybot=YB + 74)
    panel(c, X0, YB, w1, 66, fill=PANEL2, stroke=RED)
    c.setFillColor(GOLD); c.setFont("Title", 12); c.drawString(X0 + 10, YB + 48, "YOU WILL NEED")
    c.setFillColor(GREY); c.setFont("Body", 8); c.drawString(X0 + 112, YB + 49, "(click for the full checklist)")
    icon_strip(c, ["LegTourniquet", "v:AlcoholWipes", "v:PillsPainkiller", "v:Scalpel", "BoneSaw", "v:SutureNeedle", "v:BandageDirty", "SurgicalKit"],
               X0 + 12, YB + 6, size=36, gap=10, dest="checklist")
    img_fit(c, card_path("card_surgery"), X0 + w1 + 12, y - 225, X1 - X0 - w1 - 12, 225)
    col(c, [P("WHAT HAPPENS WHEN YOU PRESS OPERATE", "h3"), table([
        ["Action", "Needs", "Notes"],
        ["Prepare the area", "disinfectant", "One dose is used. Starts the wound clean."],
        ["Incision", "a blade", "Pain, blood, a little noise."],
        ["Sawing (the long one)", "the saw", "Animation of sawing a log. 3 screams. Faint roll at half way."],
        ["Stitch + bandage", "needle/thread, bandage", "Vanilla stitching and bandaging on the stump."]],
        [100, 92, None]), Spacer(1, 4), P("The severed limb is an item: " + link("what happens next", "postop") + ".", "small")],
        X0 + w1 + 12, y - 233, X1 - X0 - w1 - 12)


# ======================================================================================== cirugía 2: lista
STEPS = [
    ("1", "Tourniquet worn on that limb", "LegTourniquet", "Arm tourniquet for arms, leg tourniquet for legs. Missing: heavy bleeding, +15% failure."),
    ("2", "Disinfect", "v:AlcoholWipes", "Disinfectant (best), alcohol wipes, alcohol bandage or sheets, whiskey, vodka. Missing: dirty wound, +4%."),
    ("3", "Anaesthesia", "v:PillsPainkiller", "Painkillers (up to 60%), alcohol (up to 50%), sleeping pills (up to 30%). OK at 50%+. Less pain = fewer screams, fainting less likely."),
    ("4", "Blade for the incision", "v:Scalpel", "Scalpel / kit (best), hunting / kitchen / small knife, then flint knife, machete, cleaver... Missing: +8%."),
    ("5", "Saw for the bone", "BoneSaw", "Bone saw / kit (best), saw, garden / small / plank saw, then machete, hatchet, hand axe (crude, +25%)."),
    ("6", "Stitches", "v:SutureNeedle", "Suture needle, or needle and thread. Missing: the stump bleeds longer, +10%."),
    ("7", "Bandage", "v:BandageDirty", "Alcohol bandage, bandage, alcohol or plain ripped sheets."),
]
def p_surgery2(c, y):
    c.bookmarkHorizontal("checklist", 0, y)
    w1 = 520
    panel(c, X0, YB, w1, y - YB)
    c.setFillColor(GOLD); c.setFont("Title", 17); c.drawString(X0 + 10, y - 22, "THE CHECKLIST")
    c.setFillColor(GREY); c.setFont("Body", 8.4); c.drawString(X0 + 140, y - 21, "Tick the boxes while you gather the kit (they really tick).")
    rh = (y - 34 - YB - 8) / len(STEPS)
    for i, (n, name, ico, txt) in enumerate(STEPS):
        ry = y - 34 - (i + 1) * rh
        if i % 2 == 0: c.setFillColor(PANEL2); c.rect(X0 + 4, ry + 1, w1 - 8, rh - 2, fill=1, stroke=0)
        checkbox(c, "step%s" % n, X0 + 12, ry + rh / 2 - 7, 14, name)
        c.setFillColor(RED); c.setFont("Title", 20); c.drawString(X0 + 36, ry + rh / 2 - 7, n)
        img_fit(c, icon_path(ico), X0 + 54, ry + 4, rh - 8, rh - 8)
        flow(c, [P("<b>%s</b>" % name, "body"), P(txt, "small")], X0 + 54 + rh, ry, w1 - 64 - rh, rh, pad=3)
    x2 = X0 + w1 + 12; w2 = X1 - x2
    col(c, [P("THE FIELD SURGERY KIT", "h3"),
            icon_cell("SurgicalKit", "Counts as the best saw <b>and</b> the best blade. Assemble it (needs the guide read): "
                      "bone saw + scalpel + suture needle + tweezers + arm tourniquet. You can unpack it again.", 26),
            Spacer(1, 6), P("TOURNIQUETS", "h3"),
            icon_cell("v:Belt", "Arm: 2 ripped sheets (or denim/leather strips) + a stick, branch, pencil or spoon. "
                      "Or a belt + a stick.", 26),
            icon_cell("LegTourniquet", "Leg: 3 strips + a stick, or a belt + a stick. Right-click > <i>Put tourniquet on...</i>", 26),
            Spacer(1, 6), callout("tip", "Hospitals and clinics have bone saws, scalpels and suture needles. A doctor friend in "
                                  "multiplayer can do the surgery on you, even above the elbow or knee.")], x2, y, w2)

# ======================================================================================== cirugía 3: riesgo
def p_surgery3(c, y):
    w = (X1 - X0 - 24) / 3
    col(c, [P("RISK", "h2"), P("The base failure chance depends on the limb:", "small"),
            table([["Limb", "Base"], ["Hand", "8%"], ["Forearm", "12%"], ["Upper arm", "20%"], ["Foot", "10%"], ["Lower leg", "16%"], ["Thigh", "26%"]], [70, None]),
            Spacer(1, 4)] + bullets([
                "Missing steps and worse tools add to it (see " + link("the checklist", "checklist") + ").",
                "Knowing the surgery: -8%. Each First Aid level: -2.5%.",
                "On yourself: +12% (+15% more above the elbow/knee).",
                "One-handed surgeon +10%, hemophobic +10%; tired, panicking or drunk adds more.",
                "Sandbox <i>SurgeryRiskMultiplier</i> scales everything."], "small"), X0, y, w)
    col(c, [P("SCREAMS & FAINTING", "h2")] + bullets([
                "Three screams while sawing if the patient is in pain, each heard up to <b>25 tiles</b> (sandbox <i>ScreamRadius</i>), less with anaesthesia. With little pain: just a groan (3 tiles).",
                "The saw itself is heard 5 tiles away.",
                "Fainting is rolled half way through the sawing. More pain = more likely; a tourniquet lowers it.",
                "<b>Fainting on yourself:</b> <i>Everything goes black...</i> The limb is NOT removed: you get a deep, bleeding wound "
                "(a <i>botched attempt</i>). Treat it and try again.",
                "<b>Patient faints</b> while someone else operates: the surgery goes on, in silence."], "small") +
        [Spacer(1, 8), RLImage(card_path("card_noise"), w - 20, (w - 20) * 0.5625)], X0 + w + 12, y, w)
    c.bookmarkHorizontal("outcome", 0, y)
    col(c, [P("THE OUTCOME", "h2"), table([["Result", "Stump"],
            ["Clean cut", "Normal healing."], ["Rough", "Heals 1.4x slower, dirtier, bleeds more."],
            ["Botched (something tore)", "Heals 1.8x slower, very dirty, bleeds hard."]], [80, None]),
            Spacer(1, 6), P("CAUTERIZE", "h3"),
            P("Right-click a lit stove, fireplace, barbecue or campfire > <b>Cauterize</b> > the stump. It closes at once and "
              "sepsis becomes much less likely. Hurts a lot and you scream. Needs guts: Brave or Desensitized, Strength 6+, "
              "painkillers/alcohol, or knowing the surgery. Take the prosthesis off first.", "small"),
            Spacer(1, 6), callout("info", "In multiplayer the result is rolled on the server with its own copy of both "
                                  "inventories: no cheating the dice.")], X0 + 2 * (w + 12), y, w)

# ======================================================================================== post-op
def p_postop(c, y):
    w = (X1 - X0 - 12) / 2
    col(c, [P("THE FIRST DAYS", "h2"),
            table([["State", "How long", "Effect"],
                   ["Shock", "about 1 day (longer if it went badly)", "All actions 1.3x slower; endurance capped."],
                   ["Convalescence", "5 days (sandbox <i>ConvalescenceDays</i>)", "Actions 1.1x slower; more tired, hungry and thirsty."],
                   ["Phantom pain", "6-30 h after, then every 8-48 h", "\"The limb that is not there hurts.\""]], [74, 120, None]),
            Spacer(1, 6), P("HEALING (CICATRIZATION)", "h3"),
            table([["Stump", "Hand", "Forearm", "Upper arm", "Foot", "Lower leg", "Thigh"],
                   ["Base hours", "120", "144", "192", "150", "180", "240"]], [64] + [None] * 6),
            Spacer(1, 3), P("Faster with the surgeon's First Aid, the best tools and knowing the surgery; slower if rough or "
                            "botched and while the stump is dirty. <b>Cauterizing</b> closes it instantly.", "small"),
            Spacer(1, 4), callout("warn", "A prosthesis on a stump that has not closed can make it bleed again. Wait for "
                                  "<i>The stump has closed.</i>")], X0, y, w, ybot=YB + 120)
    panel(c, X0, YB, w, 112, stroke=EDGE)
    img_fit(c, render_path("props", maxw=360), X0 + 6, YB + 6, 170, 100)
    flow(c, [P("THE SEVERED LIMB", "h3"), P("Drops on the floor after the surgery (sandbox <i>DropSeveredLimbs</i>). It is "
             "an item: carry it, bury it, or do not ask. It rots in a few days and makes you unhappy to look at.", "small")],
         X0 + 176, YB, w - 176, 112, pad=8)
    c.bookmarkHorizontal("healing", 0, y)
    col(c, [P("SEPSIS", "h2"), P("While the stump is open, dirt builds up every hour (blood and grime on that part make it "
            "worse; a clean bandage helps). Past <b>45%</b> dirt, sepsis grows:", "small"),
            table([["Sepsis", "What happens"], ["10+", "The stump gets a wound infection."], ["25+", "Pain. \"The stump is hot and swollen.\""],
                   ["40+", "Sickness."], ["60+", "\"Fever. The stump stinks. Antibiotics, now.\""], ["100", "You lose health every hour."]], [50, None]),
            Spacer(1, 5), P("HOW TO STOP IT", "h3")] + bullets([
                "<b>Clean Stump</b>: health panel, on an open dirty stump. Uses a disinfectant (or alcohol bandage). Hurts.",
                "<b>Antibiotics</b> lower it every hour. Keep a clean bandage on and stay clean.",
                "Once the stump closes, sepsis fades. Without a hand you carry 2 less (sandbox <i>CarryPenalty</i>)."], "small") +
            [Spacer(1, 4), P("HEALTH PANEL CHEAT SHEET", "h3"),
            table([["You see", "Means"], ["In shock / Convalescence: 2 d 5 h", "Post-op weakness, see the table on the left"],
                   ["Cicatrization 40%", "How far the stump has healed"], ["Wound Dirtyness 12%", "Keep it under 45%"],
                   ["Sepsis 0%", "Infection of the stump"], ["Cicatrized / Cauterized", "Healed: safe for a prosthesis"],
                   ["Botched amputation attempt", "You fainted on yourself: treat the wound, try again"]], [150, None])], X0 + w + 12, y, w)


# ======================================================================================== brazos 1
BASES = ["Wood", "Scrap", "Mech", "Med", "Cyber"]
FIT = {"Knob": [1, 1, 1, 1, 1], "Hook": [1, 1, 1, 1, 1], "MechHand": [0, 1, 1, 1, 1], "MedHand": [0, 1, 1, 1, 1],
       "CyberHand": [0, 0, 1, 1, 1], "Chainsaw": [0, 1, 1, 0, 1], "Bayonet": [1, 1, 1, 1, 1]}
HEADN = {"Knob": "Wooden knob", "Hook": "Hook", "MechHand": "Mechanical hand", "MedHand": "Medical hand",
         "CyberHand": "Cybernetic hand", "Chainsaw": "Chainsaw (R)", "Bayonet": "Bayonet (R)"}
def p_arms1(c, y):
    w1 = 330
    col(c, [P("TWO PIECES", "h2"),
            P("An arm prosthesis is a <b>base</b> (strapped to the stump, one model per level: hand, forearm or whole arm) "
              "plus an <b>attachment</b> on its end, which you can swap without taking the base off.", "body"), Spacer(1, 3)] +
        bullets(["Wear the base first, then the attachment (or use the " + link("workbench", "workbench") + ").",
                 "Recipes give the left one: it moves to the side you are missing when you wear it, and changes to the model for your stump.",
                 "Fits the upper arm and the thigh too.",
                 "<b>Grip</b> comes from the attachment: only hands hold things like a hand. A base alone holds nothing.",
                 "<b>Two-handed</b> weapons need a hand attachment (mechanical, medical, cyber) on a base.",
                 "Your old 3.2 arms convert by themselves into the matching base + attachment."], "small"), X0, y, w1, ybot=YB + 170)
    img_fit(c, card_path("card_modular"), X0, YB, w1, 162)
    x2 = X0 + w1 + 12; w2 = X1 - x2
    rows = [["Attachment \\ Base"] + [icon_cell("Base" + b, b, 18) for b in BASES]]
    for h, fits in FIT.items():
        rows.append([icon_cell("Head" + h, HEADN[h], 18)] + [P('<font color="%s"><b>%s</b></font>' % ("#7FC97A" if f else "#C42026", "YES" if f else "NO"), "center") for f in fits])
    t = table(rows, [118] + [(w2 - 18 - 118) / 5] * 5)
    col(c, [P("WHAT FITS WHAT", "h2"), t, Spacer(1, 5)] + bullets([
        "Mechanical and medical hands do not fit wood. The cybernetic hand needs a mechanical, medical or cyber base.",
        "Chainsaw: metal base only (scrap, mechanical, cyber), right arm. Bayonet: any base, right arm.",
        "Messages tell you why: <i>Doesn't fit a wooden base.</i>, <i>This attachment only fits the right arm.</i>"], "small"),
        x2, y, w2, ybot=YB + 128)
    panel(c, x2, YB, w2, 120, stroke=EDGE)
    gallery(c, [("mod_Knob", "Knob", None), ("mod_Hook", "Hook", None), ("mod_MechHand", "Mech hand", None),
                ("mod_Chainsaw", "Chainsaw", "weapons"), ("mod_Bayonet", "Bayonet", "weapons")], x2 + 4, YB + 4, w2 - 8, 112)


def p_arms2(c, y):
    w = X1 - X0
    rows = [["Base", "Tier", "Action bonus", "2-handed", "Wear", "Condition", "Weight", "Get it"],
            [icon_cell("BaseWood", "Wooden base", 18), "1", "+0", "with a hand", "fast", "15", "0.8", link("craft", "recipes")],
            [icon_cell("BaseScrap", "Scrap base", 18), "2", "+1", "with a hand", "medium", "22", "1.3", link("craft", "recipes") + " / clinics"],
            [icon_cell("BaseMech", "Mechanical frame", 18), "3", "+2", "with a hand", "slow", "30", "1.6", link("craft", "recipes") + " / clinics"],
            [icon_cell("BaseMed", "Medical base", 18), "4", "+3", "with a hand", "very slow", "40", "1.0", "hospitals only"],
            [icon_cell("BaseCyber", "Cybernetic frame", 18), "5", "+4", "with a hand", "slowest", "60", "1.2", link("craft", "recipes") + " (hard)"]]
    hrows = [["Attachment", "Grip", "2-handed", "Action bonus", "Wear", "Condition"],
             [icon_cell("HeadKnob", "Wooden knob", 18), "no", "no", "+0", "x1.0", "15"],
             [icon_cell("HeadHook", "Hook", 18), "no", "no", "+0", "x1.0", "25"],
             [icon_cell("HeadMechHand", "Mechanical hand", 18), "<b>yes</b>", "yes", "+0", "x1.0", "30"],
             [icon_cell("HeadMedHand", "Medical hand", 18), "<b>yes</b>", "yes", "+1", "x0.8", "40"],
             [icon_cell("HeadCyberHand", "Cybernetic hand", 18), "<b>yes</b>", "yes", "+1", "x0.7", "60"],
             [icon_cell("HeadChainsaw", "Chainsaw", 18), "no", "no", "+0", "x1.5", "30"],
             [icon_cell("HeadBayonet", "Bayonet", 18), "no", "no", "+0", "x1.2", "25"]]
    col(c, [P("BASES", "h3"), table(rows, [128, 34, 66, 70, 62, 58, 46, None]), Spacer(1, 6),
            P("ATTACHMENTS", "h3"), table(hrows, [128, 50, 60, 76, 50, None])], X0, y, 520, ybot=YB + 96)
    panel(c, X0, YB, 520, 88, stroke=EDGE)
    gallery(c, [("prop_basemech", "Mechanical frame", None), ("prop_hook", "Scrap + hook", None), ("prop_cyberhand", "Cyber hand", None),
                ("prop_mechleg", "Mechanical leg", "legs"), ("prop_cyberleg", "Cyber leg", "legs")], X0 + 4, YB + 2, 512, 84, label_size=8.5)
    x2 = X0 + 532; w2 = X1 - x2
    col(c, [P("WHAT THE NUMBERS DO", "h3")] + bullets([
                "<b>Action bonus</b>: counts as extra skill levels for how fast you do things one-handed (base + attachment + "
                "your " + link("Prosthesis Familiarity", "skills") + ").",
                "<b>Wear</b>: every action wears it a little; at 0 condition it falls off (<i>The prosthesis broke.</i>). "
                "At 3 or less you get a warning.",
                "<b>Cybernetic frame</b>: +1 Strength while worn (only one point, even with two).",
                "Sandbox <i>ProsthesisWear</i> turns wear off."], "small") +
        [Spacer(1, 4), P("REPAIR", "h3"), table([["Part", "Repair with"],
            ["Wood, knob, peg leg, crutch", "wood glue or duct tape"], ["Scrap base, hook, bayonet", "welding rods or duct tape"],
            ["Mechanical frame / hand / leg", "welding rods, screws or duct tape"], ["Medical parts", "duct tape or screws"],
            ["Cybernetic parts", "electronics scrap, welding rods or wire"], ["Chainsaw", "engine parts, welding rods, duct tape"]], [96, None])],
        x2, y, w2)

# ======================================================================================== recetas
R_ARMS = [
    ("BaseWood", "Wooden Prosthesis Base", "Carpentry 2", "2 planks, 1 leather strips, 4 nails", "hammer, saw"),
    ("HeadKnob", "Wooden Knob Attachment", "Carpentry 1", "1 plank", "saw"),
    ("BaseScrap", "Scrap Prosthesis Base", "Welding 2", "1 sheet / scrap metal, 3 leather strips, 2 duct tape, blowtorch, 1 welding rod", "hammer"),
    ("HeadHook", "Hook Attachment", "Welding 2", "1 metal pipe, blowtorch, 1 welding rod", ""),
    ("BaseMech", "Mechanical Prosthesis Frame", "Welding 4", "3 metal pipes, 1 sheet metal, 4 screws, blowtorch, 3 welding rods", "screwdriver"),
    ("HeadMechHand", "Mechanical Hand Attachment", "Welding 4, Mechanics 2", "1 metal pipe, 1 sheet metal, 6 screws, blowtorch, 1 welding rod", "screwdriver"),
    ("HeadChainsaw", "Chainsaw Attachment", "Welding 5, Mechanics 4", "4 engine parts, 2 small sheet metal, 1 metal pipe, 6 screws, 1 saw, blowtorch, 3 rods", "welding mask, screwdriver, wrench"),
    ("HeadBayonet", "Bayonet Attachment", "Welding 2", "1 knife (hunting, kitchen, flint, butterfly, large), 1 scrap metal, 1 duct tape, blowtorch", "hammer"),
    ("BaseCyber", "Cybernetic Prosthesis Frame", "Welding 7, Electrical 6, Mechanics 5", "2 sheet metal, 2 aluminium, car battery charger, amplifier, 6 electronics scrap, 4 wire, 10 screws, blowtorch, 4 rods", "welding mask, screwdriver"),
    ("HeadCyberHand", "Cybernetic Hand Attachment", "Electrical 7, Mechanics 6, Welding 4", "motion sensor, pager / calculator / remote, 1 aluminium, 5 electronics scrap, 3 wire, 12 screws, blowtorch", "screwdriver"),
]
R_LEGS = [
    ("PegLeg", "Peg Leg", "Carpentry 3", "3 planks, 2 leather strips, 6 nails, 2 screws", "hammer, saw"),
    ("MechLeg", "Mechanical Leg", "Welding 4", "3 metal pipes, 1 sheet metal, 4 screws, 1 leather strips, blowtorch, 4 rods", ""),
    ("CyberLeg", "Cybernetic Leg", "Welding 7, Electrical 6, Mechanics 6", "3 sheet metal, 2 aluminium, car battery charger, motion sensor, 8 electronics scrap, 5 wire, 14 screws, blowtorch, 5 rods", "welding mask, screwdriver, wrench"),
    ("Crutch", "Crutch", "Carpentry 1", "2 planks, 4 nails, 2 ripped sheets", "hammer"),
    ("ProsthesisWorkbench", "Prosthesis Workbench", "Carpentry 3", "8 planks, 20 nails, 1 sheet metal, 8 screws", "hammer, saw, screwdriver"),
]
def recipe_table(rows, w):
    data = [["Item", "Skill", "Ingredients", "Tools (kept)"]]
    for ico, name, sk, ing, tools in rows:
        data.append([icon_cell(ico, "<b>%s</b>" % name, 22), sk, ing, tools or "-"])
    return table(data, [168, 100, None, 96])

def p_recipes(c, y):
    col(c, [P("ARM PROSTHESES", "h2"), P("All are hand crafts in the crafting menu, no recipe to learn. Welding recipes use "
            "blowtorch fuel and welding rods. Click a name in " + link("What fits what", "arms") + " to see which pairs work.", "small"),
            recipe_table(R_ARMS, X1 - X0)], X0, y, X1 - X0, ybot=YB + 128)
    panel(c, X0, YB, X1 - X0, 120, stroke=EDGE)
    gallery(c, [("arms_peg", "Wood + knob", None), ("arms_hook", "Scrap + hook", None), ("arms_mech", "Mech + mech hand", None),
                ("arms_medical", "Medical", None), ("arms_cyber", "Cybernetic", None), ("cyber_hand", "Cyber hand, gripping", None)],
            X0 + 4, YB + 4, X1 - X0 - 8, 112)


def p_recipes2(c, y):
    col(c, [P("LEGS, CRUTCH & WORKBENCH", "h2"), recipe_table(R_LEGS, X1 - X0)], X0, y, X1 - X0, ybot=y - 206)
    w = (X1 - X0 - 24) / 3; yt = y - 214
    panel(c, X0, YB, X1 - X0, 112, stroke=EDGE)
    gallery(c, [("crutch", "Crutch", "legs"), ("legs_peg", "Peg leg", "legs"), ("legs_mech", "Mechanical leg", "legs"),
                ("legs_medical", "Medical leg (loot)", "legs"), ("legs_cyber", "Cybernetic leg", "legs"), ("prop_bench", "Workbench", "workbench")],
            X0 + 4, YB + 2, X1 - X0 - 8, 108)
    col(c, [P("SURGERY ITEMS", "h3"),
            icon_cell("v:Belt", "<b>Arm tourniquet</b>: 2 ripped sheets / denim / leather strips + a stick, branch, pencil or spoon; or a belt + a stick.", 24),
            icon_cell("LegTourniquet", "<b>Leg tourniquet</b>: 3 strips + a stick; or a belt + a stick.", 24),
            icon_cell("SurgicalKit", "<b>Field Surgery Kit</b>: bone saw + scalpel + suture needle + tweezers + arm tourniquet (needs the guide read).", 24)],
        X0, yt, w, ybot=YB + 120)
    col(c, [P("FOUND, NOT MADE", "h3"), P("No recipe. Hospital lockers, hospital wardrobes and clinic tool cabinets:", "small"),
            icon_cell("BaseMed", "<b>Medical Prosthesis Base</b>", 24), icon_cell("HeadMedHand", "<b>Medical Hand Attachment</b>", 24),
            icon_cell("MedicalLeg", "<b>Medical Prosthetic Leg</b>", 24)], X0 + w + 12, yt, w, ybot=YB + 120)
    col(c, [P("ALSO IN LOOT", "h3")] + bullets([
        "Clinic tool cabinets also hide scrap and mechanical bases, hooks, mechanical hands, peg legs and mechanical legs.",
        "Crutches: hospitals, clinics, medical storage.",
        "Never in loot: wooden base and knob, everything cybernetic, chainsaw and bayonet attachments.",
        "The Field Amputation Guide: clinics, hospitals, bookstores, libraries."], "small"), X0 + 2 * (w + 12), yt, w, ybot=YB + 120)


# ======================================================================================== piernas
def p_legs(c, y):
    w1 = 470
    rows = [["How you move", "When", "What you can do"],
            ["<b>CRAWL</b>", "Both legs missing, or one missing and no crutch", "Crawl on the ground. No running. Stamina drains. You can still fight from the ground."],
            ["<b>CRUTCH</b>", "One leg missing, crutch in a hand", "Walk only, no running. Stamina drains."],
            ["<b>PEG</b>", "Peg leg worn", "Run, but never sprint."],
            ["<b>FULL</b>", "Mechanical, medical or cyber leg (or no leg amputated)", "Normal. The cyber leg runs 10% faster than a healthy leg."]]
    col(c, [P("FOUR WAYS TO MOVE", "h2"), table(rows, [62, 150, None]), Spacer(1, 6)] + bullets([
        "A leg counts as missing from any leg amputation (foot, lower leg or thigh) without a prosthesis on that side.",
        "One prosthetic leg and one missing leg: you still need a crutch.",
        "Crutch: about 1 minute of walking to get tired; crawling: about 40 seconds (sandbox <i>CrutchStaminaDrain</i>, "
        "<i>CrawlStaminaDrain</i>). Characters who start as amputees tire half as fast.",
        "Leg amputee traits give you a crutch at the start. Recipe: " + link("Crutch", "recipes2") + "."], "small"),
        X0, y, w1, ybot=YB + 178)
    img_fit(c, card_path("card_crawl"), X0, YB, w1, 170)
    x2 = X0 + w1 + 12; w2 = X1 - x2
    panel(c, x2, YB, w2, y - YB, stroke=EDGE)
    names = [("legs_peg", "Peg leg"), ("legs_mech", "Mechanical"), ("legs_medical", "Medical"), ("legs_cyber", "Cybernetic")]
    gw = (w2 - 16) / 2; gh = (y - YB - 16) / 2
    for i, (r, lab) in enumerate(names):
        gx = x2 + 8 + (i % 2) * gw; gy = y - 8 - (i // 2 + 1) * gh
        img_fit(c, render_path(r, maxw=420), gx, gy + 14, gw, gh - 16)
        c.setFillColor(GOLD); c.setFont("Title", 11); c.drawCentredString(gx + gw / 2, gy + 2, lab)


# ======================================================================================== banco y pintura
def p_workbench(c, y):
    w1 = 380
    col(c, [P("BUILD IT", "h2"), icon_cell("ProsthesisWorkbench", "<b>Prosthesis Workbench</b>: crafting menu > Carpentry. "
            "Carpentry 3, 8 planks, 20 nails, 1 sheet metal, 8 screws; hammer, saw and screwdriver. It is furniture: "
            "place it from your inventory like any other (it is not in the build menu).", 30),
            Spacer(1, 4), callout("info", "It has a real 3D model, also in 3D / first-person camera mods such as Viewpoint."),
            Spacer(1, 6), P("USE IT", "h2")] + bullets([
                "Right-click the bench > <b>Prosthesis workbench</b> (you walk to it), or right-click a prosthesis in your "
                "inventory while standing within 2 tiles of a bench.",
                "Three lists from your inventory and bags: <b>bases</b>, <b>attachments</b>, <b>legs</b> (worn ones are marked).",
                "Your character in 3D, and stat cards per arm with a preview of the selection: grip, two-handed, combat speed, "
                "action bonus, wear. Green / red arrows compare with what you wear.",
                "Buttons: <b>Fit base</b>, <b>Mount attachment</b>, <b>Take off</b>, <b>Paint</b>, <b>Close</b>. Taking a base off also removes its attachment."], "small"),
        X0, y, w1, ybot=YB + 150)
    panel(c, X0, YB, w1, 142, stroke=EDGE)
    gallery(c, [("paint_red", "Red", None), ("paint_yellow", "Yellow", None), ("paint_blue", "Blue", None)], X0 + 4, YB + 2, w1 - 8, 138)
    x2 = X0 + w1 + 12; w2 = X1 - x2
    img_fit(c, card_path("card_workbench"), x2, y - 205, w2, 205)
    COLS = [("Black", "#26262A"), ("White", "#E8E8E4"), ("Grey", "#808286"), ("Red", "#A8221E"), ("Orange", "#D6681C"),
            ("Yellow", "#DEB828"), ("Green", "#4E6634"), ("Blue", "#284896"), ("Purple", "#623482"), ("Pink", "#D67496")]
    panel(c, x2, YB, w2, y - 213 - YB)
    c.setFillColor(GOLD); c.setFont("Title", 17); c.drawString(x2 + 10, y - 236, "PAINT")
    sw = (w2 - 20) / 10
    for i, (n, hx) in enumerate(COLS):
        c.setFillColor(HexColor(hx)); c.roundRect(x2 + 10 + i * sw, y - 268, sw - 4, 22, 3, fill=1, stroke=0)
        c.setFillColor(GREY); c.setFont("Body", 6.8); c.drawCentredString(x2 + 10 + i * sw + (sw - 4) / 2, y - 278, n)
    flow(c, bullets(["Only at the bench: <b>Paint</b> button. Needs a vanilla paint can of that colour (one use) and a <b>paintbrush</b>.",
                     "Bases, attachments (not the chainsaw) and every leg. <b>Scrape off the paint</b> to get the original finish back (no items needed)."], "small"),
         x2, YB + 92, w2, y - 284 - YB - 92, pad=8)
    icon_strip(c, ["v:Paint_Black", "v:Paint_Grey", "v:Paint_Orange", "v:Paint_Yellow", "v:Paint_Pink", "v:Paintbrush"], x2 + 14, YB + 14, size=40, gap=14)
    c.setFillColor(GREY); c.setFont("Body", 8.4); c.drawString(x2 + 14, YB + 62, "Vanilla paint cans and a paintbrush: that is all you need.")

# ======================================================================================== armas
def p_weapons(c, y):
    w = (X1 - X0 - 12) / 2
    for k, (card, head, lines) in enumerate([
        ("card_chainsaw", "GROOVY: THE CHAINSAW", [
            "Right arm, on a metal base (scrap, mechanical, cyber). The right hand holds the mounted chainsaw; the left stays free.",
            "Right-click > <b>Chainsaw arm</b>: <i>Pull the starter cord</i> (Mechanics raises the chance), <i>Stop the engine</i>, "
            "<i>Refuel from...</i> any petrol can in your inventory.",
            "0.5 L tank, starts empty. About 2 in-game hours idling; each swing burns a bit more.",
            "Running: cuts through zombies and limbs, heard 20 tiles away (35 per swing). Off: a heavy club.",
            "It wears out with use; it stalls when the tank runs dry. It cannot be painted."]),
        ("card_bayonet", "MERLE'S BAYONET", [
            "Right arm, any base. The right hand holds the mounted bayonet: stabs like a hunting knife, never breaks "
            "(the attachment wears instead).",
            "Anything else you try to hold in the right hand goes to the left hand if it is free and one-handed.",
            "<b>Pistols (3.3.1):</b> equip a one-handed pistol or revolver and it is held in your left hand while the "
            "blade stays on the right. Rifles and shotguns still need a real hand.",
            "Recipe: a knife, scrap metal, duct tape, Welding 2 (" + link("recipes", "recipes") + ")."])]):
        x = X0 + k * (w + 12)
        img_fit(c, card_path(card), x, y - w * 0.5625, w, w * 0.5625)
        col(c, [P(head, "h2")] + bullets(lines, "small"), x, y - w * 0.5625 - 8, w)


# ======================================================================================== rasgos, habilidades, sandbox
def p_options(c, y):
    c.bookmarkHorizontal("skills", 0, y)
    w1 = 330
    col(c, [P("AMPUTEE TRAITS", "h2"), table([["Trait", "Points"],
            ["Amputated Left / Right Hand", "+8 / +10"], ["Amputated Left / Right Forearm", "+10 / +12"],
            ["Amputated Left / Right Upper Arm", "+20 / +22"], ["Amputated Left / Right Foot", "+10"],
            ["Amputated Left / Right Lower Leg", "+14"]], [200, None]),
            P("You start healed and practised: +4 in that side's skill, -1 Fitness and -1 Strength (arms) or Sprinting "
              "(legs). Legs start with a crutch. Sandbox <i>HideAmputeeTraits</i> hides them.", "small"),
            Spacer(1, 6), P("SKILLS (AMPUTATIONS)", "h2")] + bullets([
                "<b>Left Side</b> / <b>Right Side</b>: you get faster at actions with that side missing. XP comes from doing "
                "work while amputated (crafting, first aid, barricading, chopping, reloading...).",
                "<b>Prosthesis Familiarity</b>: XP while wearing a prosthesis; adds to the prosthesis's action bonus.",
                "Without help, actions take up to 2x (hand), 3x (forearm) or 4x (upper arm) longer. Skill levels bring "
                "it down to normal at level 10."], "small"), X0, y, w1, ybot=YB + 194)
    img_fit(c, card_path("card_cyber"), X0, YB, w1, 186)
    rows = [["Option", "Default", "What it does"],
            ["Cure window / Late gamble window", "20 / 40", "Infection % where cutting always cures / can still cure"],
            ["First Aid to examine a wound", "2", "Without it you need the guide"],
            ["Surgery risk multiplier", "1.0", "Scales every failure chance"],
            ["Scream radius", "25", "Tiles a scream carries"],
            ["Self-amputation above elbow/knee", "off", "Lets you cut your own upper arm / thigh"],
            ["Allow leg amputations", "on", ""],
            ["Sepsis / Sepsis speed", "on / 2", ""],
            ["Convalescence days", "5", ""],
            ["Cicatrization speed", "1", "Higher heals faster"],
            ["Phantom pain / Carry penalty", "on / on", ""],
            ["Prostheses wear out", "on", ""],
            ["Crutch / crawl stamina drain", "100% / 100%", "Experienced amputees pay 50%"],
            ["Sleeping pills as anaesthesia", "30", ""],
            ["Reveal the outcome after surgery", "off", "Tells you at once if it worked"],
            ["Enable zombie amputations", "<b>off</b>", "Zombies lose the limb you hit hard"],
            ["Zombies that lose a leg crawl", "on", ""],
            ["Hide amputee traits", "off", ""]]
    x2 = X0 + w1 + 12
    col(c, [P("SANDBOX OPTIONS (page \"The Only Cure+\")", "h3"), table(rows, [170, 60, None])], x2, y, X1 - x2)

# ======================================================================================== FAQ
FAQ = [
    ("Do I need the original The Only Cure?", "No. The Only Cure+ is the whole mod. Do <b>not</b> enable both: they share items and save data. \"Field Surgery\" is part of the name, not another mod."),
    ("Where do I find prostheses?", "Most are crafted: see " + link("Recipes", "recipes") + ". Medical ones only spawn in hospitals and clinics. Some scrap and mechanical parts also spawn in clinics."),
    ("How do I build the prosthesis workbench?", "Crafting menu > Carpentry, needs <b>Carpentry 3</b>. It is not in the build menu. Then place it from your inventory. See " + link("Workbench", "workbench") + "."),
    ("Why can't I hold two-handed weapons?", "You need a <b>hand attachment</b> (mechanical, medical or cybernetic) mounted on a base. A base alone, a wooden knob, a hook, the chainsaw or the bayonet cannot hold them."),
    ("Does amputating ask before cutting?", "Yes. The surgery window shows the checklist and the risk; nothing happens until you press <b>Operate</b>."),
    ("Can I amputate a friend? Can a friend amputate me?", "Yes, from the health panel of the other player, within 3 tiles. Only someone else can cut your upper arm or thigh (unless the sandbox allows it)."),
    ("The \"zombie amputations\" option does nothing?", "It is off by default and it is not for practising. When on, axes and long blades can cut off the zombie limb you hit; zombies that lose a leg crawl."),
    ("Can I hide the amputee traits?", "Yes: sandbox <i>Hide amputee traits</i>."),
    ("Is it compatible with Viewpoint / Tomb's Player Body / multiplayer?", "Yes. The bench has a Viewpoint model; enable the included <b>TombBody fit</b> add-on for Tomb's body; everything is validated on the server in MP."),
    ("Can I add it to an existing save, or replace The Only Cure mid-save?", "Yes (restart the server in MP). Back up your save first. Old arms convert into base + attachment on load."),
    ("What if a zombie bites my prosthesis?", "A prosthesis is never a target, and wounds on a limb you no longer have are removed. A bite on the stump that is left is a normal bite."),
    ("Why can't I amputate my own upper arm or thigh?", "Too high to do on yourself: someone else has to do it. The sandbox option <i>Self-amputation above the elbow and knee</i> allows it."),
    ("Can I fight while crawling?", "Yes, you can still attack from the ground. Zombies still find you down there."),
    ("How do I paint a prosthesis?", "At the " + link("workbench", "workbench") + ": <b>Paint</b> button, with a vanilla paint can and a paintbrush."),
    ("My prosthesis fell off!", "It broke from wear (condition 0). Repair it before it gets there: see " + link("repair", "arms2") + "."),
    ("Build 41?", "No. Build 42 only (42.20 or newer)."),
]
def p_faq(c, y):
    w = (X1 - X0 - 12) / 2
    half = (len(FAQ) + 1) // 2
    for k, part in enumerate((FAQ[:half], FAQ[half:])):
        x = X0 + k * (w + 12)
        items = []
        for i, (q, a) in enumerate(part):
            items += [P('<font color="#F0C46E">Q.</font> <b>%s</b>' % q, "body", spaceBefore=2), P(a, "small", leftIndent=14, spaceAfter=4)]
        col(c, items, x, y, w)


def p_support(c, y):
    c.bookmarkHorizontal("support", 0, y)
    w = (X1 - X0 - 24) / 3
    col(c, [P("OTHER MODS", "h2")] + bullets([
        "Enable <b>only one</b> of The Only Cure / The Only Cure+.",
        "Not compatible with BB First Aid Overhaul.",
        "Fancy Handwork and Brutal Handwork have no Build 42 version (their hooks stay and do nothing).",
        "Reported working: Wounds Overhaul, AHS, Viewpoint, Bandits, large modpacks.",
        "Modders can add their own bases and attachments (API_MODULAR.md on GitHub)."], "small") +
        [Spacer(1, 6), P("MULTIPLAYER", "h2")] + bullets([
        "Every body change is checked and applied by the server; the surgery dice are rolled there too.",
        "You can operate on another player within 3 tiles.",
        "Safe to add to a running server (restart it). TOC data is wiped when the character dies.",
        "Admins: right-click a player > <i>TOC - name</i> > Reset / Force Amputation."], "small"), X0, y, w)
    col(c, [P("TOMB'S PLAYER BODY", "h2"), P("Enable the optional <b>The Only Cure+ - TombBody fit</b>, included in the same "
            "Workshop item, and load it after The Only Cure+ and Tomb's Player Body. Stumps and every prosthesis are "
            "refitted to Tomb's body with your own Tomb texture (normal, DOLL or NUDE).", "small"),
            Spacer(1, 6), RLImage(card_path("tombbody_banner", 700), w - 20, (w - 20) * 0.33)], X0 + w + 12, y, w)
    img_fit(c, card_path("kofi_banner", 700), X0 + w + 22, YB + 10, w - 20, 120)
    c.linkURL(KOFI, (X0 + w + 22, YB + 10, X0 + 2 * w + 2, YB + 130), relative=0, thickness=0)
    col(c, [P("FOUND A BUG?", "h2"), P("Report it on " + ext("GitHub issues", ISSUES) + " or in the Workshop comments, with "
            "your <b>console.txt</b> (in your Zomboid user folder) and a screenshot. Say which prosthesis and which clothing "
            "if something clips.", "small"), Spacer(1, 8), P("SUPPORT THE MOD", "h2"),
            P("The Only Cure+ is free and will stay free. If you enjoy it you can buy me a coffee on " + ext("Ko-fi", KOFI) + ".", "small"),
            Spacer(1, 8), P("Credits: ZioPao and contributors of The Only Cure (GPL-3.0); RabenRabo (body locations); Tomb "
                            "(Tomb's Player Body, add-on made with permission).", "tiny")], X0 + 2 * (w + 12), y, w)
    button(c, X0 + 2 * (w + 12) + 10, YB + 52, w - 20, 26, "BUY ME A COFFEE", url=KOFI, size=12)
    button(c, X0 + 2 * (w + 12) + 10, YB + 16, w - 20, 26, "REPORT A BUG", url=ISSUES, fill=RED2, size=12)

PAGES = [
    {"cover": True, "dest": "cover", "outline": "Cover", "draw": p_cover},
    {"dest": "contents", "outline": "Contents", "title": "CONTENTS", "sub": "Click any box", "draw": p_contents},
    {"dest": "bitten", "outline": "1. I got bitten!", "chapter": "bitten", "title": "I GOT BITTEN!", "sub": "Click a box to read more", "draw": p_bitten},
    {"dest": "infection", "outline": "2. Infection & diagnosis", "chapter": "infection", "title": "INFECTION & DIAGNOSIS", "draw": p_infection},
    {"dest": "surgery", "outline": "3. Field surgery", "chapter": "surgery", "title": "FIELD SURGERY", "sub": "Starting it", "draw": p_surgery1},
    {"dest": "surgery2", "outline": "The checklist", "level": 1, "chapter": "surgery", "title": "FIELD SURGERY", "sub": "The checklist", "draw": p_surgery2},
    {"dest": "surgery3", "outline": "Risk, screams, fainting", "level": 1, "chapter": "surgery", "title": "FIELD SURGERY", "sub": "Risk, screams, fainting, outcome", "draw": p_surgery3},
    {"dest": "postop", "outline": "4. After the operation", "chapter": "postop", "title": "AFTER THE OPERATION", "draw": p_postop},
    {"dest": "arms", "outline": "5. Modular arm prostheses", "chapter": "arms", "title": "MODULAR ARM PROSTHESES", "draw": p_arms1},
    {"dest": "arms2", "outline": "Stats, wear, repair", "level": 1, "chapter": "arms", "title": "MODULAR ARM PROSTHESES", "sub": "Stats, wear and repair", "draw": p_arms2},
    {"dest": "recipes", "outline": "6. Recipes & loot", "chapter": "recipes", "title": "RECIPES", "sub": "Arm prostheses", "draw": p_recipes},
    {"dest": "recipes2", "outline": "Legs, crutch, workbench, loot", "level": 1, "chapter": "recipes", "title": "RECIPES & LOOT", "draw": p_recipes2},
    {"dest": "legs", "outline": "7. Legs, crutches & crawling", "chapter": "legs", "title": "LEGS, CRUTCHES & CRAWLING", "draw": p_legs},
    {"dest": "workbench", "outline": "8. Workbench & paint", "chapter": "workbench", "title": "WORKBENCH & PAINT", "draw": p_workbench},
    {"dest": "weapons", "outline": "9. Chainsaw & bayonet", "chapter": "weapons", "title": "CHAINSAW & BAYONET", "sub": "Right arm only", "draw": p_weapons},
    {"dest": "options", "outline": "10. Traits, skills & sandbox", "chapter": "options", "title": "TRAITS, SKILLS & SANDBOX", "draw": p_options},
    {"dest": "faq", "outline": "11. FAQ", "chapter": "faq", "title": "FAQ", "sub": "The questions people ask most", "draw": p_faq},
    {"dest": "help", "outline": "12. Compatibility & support", "chapter": "faq", "title": "COMPATIBILITY & SUPPORT", "draw": p_support},
]
