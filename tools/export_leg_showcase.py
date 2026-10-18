"""Piernas protésicas sobre una persona con pantalón corto (2026-10-17, nueva pata de palo): cada tier en los tres
niveles (sin pie, sin pantorrilla, sin muslo), pierna derecha, en reposo y a media zancada.
Uso: TOC_MEDIA=...Dev python export_leg_showcase.py [carpeta_media_de_modelos] -> out/scene_legs
     blender -b -P blender_render.py -- out/scene_legs out/preview/legs 520
     python export_leg_showcase.py sheet -> out/preview/show_legs.png"""
import os, sys, json
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
FEMALE = os.environ.get("TOC_SEX", "M").upper().startswith("F")      # TOC_SEX=F: cuerpo de mujer, salidas con _F
SX = "_F" if FEMALE else ""
OUTD = os.path.join(HERE, "out", "scene_legs" + SX)
REN = os.path.join(HERE, "out", "preview", "legs" + SX)
TIERS = [("pegLeg", "Peg leg", "Tier 1"), ("mechLeg", "Mechanical leg", "Tier 3"), ("medicalLeg", "Medical leg", "Tier 4"), ("cyberLeg", "Cybernetic leg", "Tier 5")]
TEXF = {"cyberLeg": "cyberArm"}
LEVELS = [("Ankle", "Foot", ("RightFoot",), "No foot"), ("", "LowerLeg", ("RightLeg", "RightFoot"), "No lower leg"),
          ("Thigh", "UpperLeg", ("RightLeg", "RightFoot"), "No thigh")]
POSES = [("rest", "Bob_Idle.X", 0.0), ("walk", "Bob_Walk.X", 0.25), ("walk2", "Bob_Walk.X", 0.75)]

def export():
    import pose_x as P
    import outfits as O
    MOD = P.RC.MOD
    SRC = _a[0] if _a else MOD
    P.OUT = OUTD; os.makedirs(OUTD, exist_ok=True)
    shirt = O.clothes_tex("Shirt_Tshirt_Textures", "TShirt_Grey.png")
    shorts = O.clothes_tex("Shorts_Textures", "LongShorts_Denim.png")
    jobs = {}
    for pose, clip, frac in POSES:
        c = P.load_clip(os.path.join(P.ANIMS, "Bob", clip))
        end = max(t for k in c["keys"].values() for t, _ in k.get("R", [(0, 0)]))
        W = P.worlds_at(c, frac * end, False)
        hair = O.female_hair("Bob", W, (60, 40, 28)) if FEMALE else O.hair("Short", W, (46, 34, 26))
        BODY = "FemaleBody02" if FEMALE else "MaleBody02"; SEXN = "Female" if FEMALE else "Male"
        kn = W["Bip01_R_Calf"][3, :3]
        focus = [float(kn[0] * 10), float(-kn[2] * 10), float(kn[1] * 10 - 0.9)]
        for lvl, part, hide, _ in LEVELS:
            tex = O.body_texture(BODY, overlays=[shirt, shorts], hide=hide)
            st = O.inward(P.posed_x(os.path.join(MOD, "models_X", "Amputation", "Amputation_Right_%s_%s.X" % (part, SEXN)),
                                    O.stump_tex({"Foot": "Foot", "LowerLeg": "LowerLeg", "UpperLeg": "UpperLeg"}[part], BODY), W))
            for tier, _, _ in TIERS:
                nm = "lg_%s_%s_%s" % (tier, lvl or "Calf", pose)
                P.export(nm, [O.body(W, tex, SEXN), st, hair,
                              P.posed_x(os.path.join(SRC, "models_X", "Prosthesis", "%s%s_R_%s.X" % (tier, lvl, "F" if FEMALE else "M")), os.path.join(MOD, "textures", "Prosthesis", TEXF.get(tier, tier) + ".png"), W)])
                jobs[nm] = [nm, 225 if pose == "rest" else 270, focus, 6.4, 6]
                if pose == "rest": jobs["cl_" + nm] = [nm, 250, [focus[0], focus[1], focus[2] - 0.6], 3.8, 8]
    json.dump(jobs, open(os.path.join(OUTD, "tomb_jobs.json"), "w"), indent=0)
    print(len(jobs), "vistas")

def sheet():
    from PIL import Image, ImageDraw
    import make_workshop as MW
    cw, ch, left, top = 300, 420, 270, 280
    cols = [(lvl, pose) for lvl, _, _, _ in LEVELS for pose, _, _ in POSES]
    w, h = left + cw * len(cols) + 30, top + ch * len(TIERS) + 30
    img = MW.background(w, h, 71).convert("RGBA"); d = ImageDraw.Draw(img)
    ft = MW.font(MW.F_BOLD, 70)
    d.text((54, 38), "LEG PROSTHESES", font=ft, fill=(0, 0, 0)); d.text((50, 34), "LEG PROSTHESES", font=ft, fill=MW.BONE)
    d.rectangle((50, 126, 50 + d.textlength("LEG PROSTHESES", font=ft), 132), fill=MW.RED)
    d.text((50, 146), "Each tier for a missing foot, lower leg or thigh · standing and walking", font=MW.font(MW.F_BODY, 30), fill=MW.GREY)
    fh, fn, fs = MW.font(MW.F_BOLD, 22), MW.font(MW.F_BODY, 26), MW.font(MW.F_BODY, 21)
    for j, (lvl, pose) in enumerate(cols):
        t = (dict((l, n) for l, _, _, n in LEVELS)[lvl]).upper(); x = left + j * cw
        if pose == "rest":
            tw = d.textlength(t, font=fh); d.text((x + cw - tw / 2, top - 60), t, font=fh, fill=MW.BONE)
        tw = d.textlength(pose, font=fs); d.text((x + (cw - tw) / 2, top - 30), pose, font=fs, fill=MW.GREY)
    for i, (tier, name, sub) in enumerate(TIERS):
        y = top + i * ch
        d.text((40, y + ch / 2 - 30), name, font=fn, fill=(232, 226, 214)); d.text((40, y + ch / 2 + 4), sub, font=fs, fill=MW.GREY)
        for j, (lvl, pose) in enumerate(cols):
            x = left + j * cw
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle((x + 5, y + 5, x + cw - 5, y + ch - 5), radius=12, fill=(0, 0, 0, 90), outline=(255, 255, 255, 28))
            img.alpha_composite(ov)
            r = Image.open(os.path.join(REN, "lg_%s_%s_%s.png" % (tier, lvl or "Calf", pose))).convert("RGBA")
            bb = r.getbbox(); r = r.crop((max(0, bb[0] - 10), max(0, bb[1] - 10), min(r.width, bb[2] + 10), min(r.height, bb[3] + 10)))
            s = min((cw - 16) / r.width, (ch - 16) / r.height); r = r.resize((int(r.width * s), int(r.height * s)), Image.LANCZOS)
            img.alpha_composite(r, (x + (cw - r.width) // 2, y + (ch - r.height) // 2))
    img.convert("RGB").save(os.path.join(HERE, "out", "preview", "show_legs%s.png" % SX)); print("show_legs.png")

if __name__ == "__main__":
    sheet() if _a and _a[0] == "sheet" else export()
