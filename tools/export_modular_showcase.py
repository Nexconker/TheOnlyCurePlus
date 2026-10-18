"""Láminas 3.3 modular sobre una persona vestida (2026-10-17, "quería que me las mostraras montadas sobre una persona y
con las diferentes variaciones"):
  - combinaciones: las 5 bases x los 7 cabezales en el brazo derecho, nivel antebrazo (las que el juego no deja
    montar, motosierra en base de madera o médica, salen como hueco);
  - niveles: cada base con su cabezal natural sin mano, sin antebrazo y sin brazo.
Uso: TOC_MEDIA=...Dev python export_modular_showcase.py -> out/scene_show
     blender -b -P blender_render.py -- out/scene_show out/preview/show 520
     python export_modular_showcase.py sheet -> out/preview/show_combos.png, out/preview/show_levels.png"""
import os, sys, json
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
# TOC_SEX=F: cuerpo de mujer (2026-10-17, revisar los modelos _F); salidas con sufijo _F
FEMALE = os.environ.get("TOC_SEX", "M").upper().startswith("F")
SX = "_F" if FEMALE else ""
OUTD = os.path.join(HERE, "out", "scene_show" + SX)
REN = os.path.join(HERE, "out", "preview", "show" + SX)
TEX = {"Wood": "pegArm", "Scrap": "knifeArm", "Mech": "normalArm", "Med": "medicalArm", "Cyber": "cyberArm",
       "Knob": "pegArm", "Hook": "hookArm", "MechHand": "normalArm", "MedHand": "medicalArm", "CyberHand": "cyberArm",
       "Chainsaw": "chainsawArm", "Bayonet": "knifeArm"}
BASES = [("Wood", "Wooden base", "Tier 1"), ("Scrap", "Scrap base", "Tier 2"), ("Mech", "Mechanical frame", "Tier 3"),
         ("Med", "Medical base", "Tier 4"), ("Cyber", "Cybernetic frame", "Tier 5")]
HEADS = [("Knob", "Wooden knob"), ("Hook", "Hook"), ("MechHand", "Mech. hand"), ("MedHand", "Medical hand"),
         ("CyberHand", "Cyber hand"), ("Chainsaw", "Chainsaw"), ("Bayonet", "Bayonet")]
NATURAL = {"Wood": "Knob", "Scrap": "Hook", "Mech": "MechHand", "Med": "MedHand", "Cyber": "CyberHand"}
METAL = {"Scrap", "Mech", "Cyber"}
LEVELS = [("Wrist", "Hand", ("RightHand",), "Hand"), ("", "ForeArm", ("RightArm", "RightHand"), "Forearm"),
          ("Upper", "UpperArm", ("RightArm", "RightHand"), "Upper arm")]

def valid(b, h):
    return not (h == "Chainsaw" and b not in METAL) and not (h == "CyberHand" and b in ("Wood", "Scrap")) and not (h in ("MechHand", "MedHand") and b == "Wood")
def why(b, h): return ["needs a", "metal base"] if h == "Chainsaw" else ["needs tier 3", "or better"] if h == "CyberHand" else ["not on a", "wooden base"]

def export():
    import pose_x as P
    import outfits as O
    MOD = P.RC.MOD
    P.OUT = OUTD; os.makedirs(OUTD, exist_ok=True)
    MX = os.path.join(MOD, "models_X")
    def ptex(k): return os.path.join(MOD, "textures", "Prosthesis", TEX[k] + ".png")
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X")); W = P.worlds_at(c, 0.0, False)
    body_name = "FemaleBody02" if FEMALE else "MaleBody02"
    stump_tex = O.stump_tex("LowerLeg", body_name)
    shirt = O.grimy(O.clothes_tex("Shirt_Tshirt_Textures", "TShirt_Grey.png"), 0.2, seed=4)
    pants = O.mesh(os.path.join("Clothes", "Kate_Trousers.x" if FEMALE else "Bob_Trousers.x"), O.grimy(O.clothes_tex("Trousers_Mesh", "TrousersMesh_Black.png"), 0.25, seed=6), W)
    hair = O.female_hair("Bob", W, (60, 40, 28)) if FEMALE else O.hair("Short", W, (46, 34, 26))
    people = {}
    for lvl, part, hide, _ in LEVELS:
        tex = O.body_texture(body_name, overlays=[shirt], hide=hide + ("LeftLeg", "RightLeg", "Crotch"))
        stump = O.inward(P.posed_x(os.path.join(MX, "Amputation", "ArmStumpProst_Right_%s_%s.X" % (part, "Female" if FEMALE else "Male")), stump_tex, W))
        people[lvl] = [O.body(W, tex, "Female" if FEMALE else "Male"), stump, pants, hair]
    fa, hd = W["Bip01_R_Forearm"][3, :3], W["Bip01_R_Hand"][3, :3]
    def bl(q, up=0.0): return [float(q[0] * 10), float(-q[2] * 10), float(q[1] * 10 + up)]
    focus = bl(hd * 0.75 + fa * 0.25, -0.15)       # combinaciones: del codo a la punta de los dedos
    focus_lv = bl(fa, -0.3)                         # niveles: del hombro a la mano
    jobs = {}
    def piece(kind, key, lvl=""):
        return P.posed_x(os.path.join(MX, "Prosthesis", "%s%s%s_R_%s.X" % (kind, key, lvl, "F" if FEMALE else "M")), ptex(key), W)
    for b, _, _ in BASES:
        base = piece("base", b)
        for h, _ in HEADS:
            if not valid(b, h): continue
            nm = "cb_%s_%s" % (b, h)
            P.export(nm, people[""] + [base, piece("head", h)])
            long_ = h in ("Chainsaw", "Bayonet")         # cuelgan más: encuadre más abierto y más bajo
            jobs[nm] = [nm, 215, [focus[0], focus[1], focus[2] - (0.9 if h == "Chainsaw" else 0.35 if long_ else 0.0)], 4.2 if h == "Chainsaw" else 3.3 if long_ else 2.9, 8]
        for lvl, _, _, _ in LEVELS:
            nm = "lv_%s_%s" % (b, lvl or "Fore")
            P.export(nm, people[lvl] + [piece("base", b, lvl), piece("head", NATURAL[b])])
            jobs[nm] = [nm, 215, focus_lv, 4.3, 8]
    json.dump(jobs, open(os.path.join(OUTD, "tomb_jobs.json"), "w"), indent=0)
    print(len(jobs), "vistas")

def sheet():
    from PIL import Image, ImageDraw, ImageFilter
    import make_workshop as MW
    def render(name, box):
        r = Image.open(os.path.join(REN, name + ".png")).convert("RGBA")
        s = min(box[0] / r.width, box[1] / r.height)
        return r.resize((int(r.width * s), int(r.height * s)), Image.LANCZOS)
    def card(img, x, y, cw, ch, gold=False):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle((x, y, x + cw, y + ch), radius=12, fill=(0, 0, 0, 90), outline=(200, 152, 58, 210) if gold else (255, 255, 255, 28), width=3 if gold else 1)
        img.alpha_composite(ov)
    def header(img, d, title, sub, w):
        ft = MW.font(MW.F_BOLD, 70)
        d.text((54, 38), title, font=ft, fill=(0, 0, 0)); d.text((50, 34), title, font=ft, fill=MW.BONE)
        d.rectangle((50, 126, 50 + d.textlength(title, font=ft), 132), fill=MW.RED)
        d.text((50, 146), sub, font=MW.font(MW.F_BODY, 30), fill=MW.GREY)

    # ---- combinaciones: filas = bases, columnas = cabezales
    cw, ch, left, top = 250, 270, 250, 270
    w, h = left + cw * len(HEADS) + 40, top + ch * len(BASES) + 40
    img = MW.background(w, h, 51).convert("RGBA"); d = ImageDraw.Draw(img)
    header(img, d, "EVERY COMBINATION", "5 bases x 7 attachments · swap the attachment without taking the base off", w)
    fh, fn, fs = MW.font(MW.F_BOLD, 24), MW.font(MW.F_BODY, 26), MW.font(MW.F_BODY, 21)
    for j, (hk, hn) in enumerate(HEADS):
        tw = d.textlength(hn.upper(), font=fh); d.text((left + j * cw + (cw - tw) / 2, top - 44), hn.upper(), font=fh, fill=MW.BONE)
    for i, (bk, bn, tier) in enumerate(BASES):
        y = top + i * ch
        d.text((40, y + ch / 2 - 30), bn, font=fn, fill=(232, 226, 214))
        d.text((40, y + ch / 2 + 4), tier, font=fs, fill=(214, 168, 74) if bk == "Cyber" else MW.GREY)
        for j, (hk, _) in enumerate(HEADS):
            x = left + j * cw
            card(img, x + 5, y + 5, cw - 10, ch - 10, gold=(bk == "Cyber" or hk == "CyberHand"))
            if not valid(bk, hk):
                msg = why(bk, hk)
                for k, m in enumerate(msg):
                    tw = d.textlength(m, font=fs); d.text((x + (cw - tw) / 2, y + ch / 2 - 24 + k * 28), m, font=fs, fill=(130, 126, 120))
                continue
            r = render("cb_%s_%s" % (bk, hk), (cw - 14, ch - 14))
            img.alpha_composite(r, (x + (cw - r.width) // 2, y + (ch - r.height) // 2))
    img.convert("RGB").save(os.path.join(HERE, "out", "preview", "show_combos%s.png" % SX))

    # ---- niveles: filas = bases, columnas = nivel de amputación
    cw, ch, left, top = 360, 400, 300, 280
    w, h = left + cw * 3 + 40, top + ch * len(BASES) + 40
    img = MW.background(w, h, 52).convert("RGBA"); d = ImageDraw.Draw(img)
    header(img, d, "EVERY LEVEL", "Each base is modelled for a missing hand, forearm or whole arm", w)
    for j, (_, _, _, ln) in enumerate(LEVELS):
        t = ("NO " + ln).upper(); tw = d.textlength(t, font=fh); d.text((left + j * cw + (cw - tw) / 2, top - 44), t, font=fh, fill=MW.BONE)
    for i, (bk, bn, tier) in enumerate(BASES):
        y = top + i * ch
        d.text((40, y + ch / 2 - 46), bn, font=fn, fill=(232, 226, 214))
        d.text((40, y + ch / 2 - 12), tier, font=fs, fill=(214, 168, 74) if bk == "Cyber" else MW.GREY)
        d.text((40, y + ch / 2 + 18), "+ " + dict(HEADS)[NATURAL[bk]].lower(), font=fs, fill=MW.GREY)
        for j, (lvl, _, _, _) in enumerate(LEVELS):
            x = left + j * cw
            card(img, x + 6, y + 6, cw - 12, ch - 12, gold=(bk == "Cyber"))
            r = render("lv_%s_%s" % (bk, lvl or "Fore"), (cw - 16, ch - 16))
            img.alpha_composite(r, (x + (cw - r.width) // 2, y + (ch - r.height) // 2))
    img.convert("RGB").save(os.path.join(HERE, "out", "preview", "show_levels%s.png" % SX))
    print("show_combos.png, show_levels.png")

if __name__ == "__main__":
    sheet() if _a and _a[0] == "sheet" else export()
