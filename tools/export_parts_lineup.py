"""Lámina de todas las piezas modulares 3.3 (bases y cabezales) sueltas, como foto de producto: cada pieza posada en
reposo, girada para quedar tumbada en diagonal y centrada en su propia escena (out/scene_parts).
Uso: TOC_MEDIA=...Dev python export_parts_lineup.py ; render: blender -b -P blender_render.py -- out/scene_parts out/preview/parts 700
Después: python export_parts_lineup.py sheet  -> out/preview/parts_lineup.png"""
import os, sys, json
_a = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = {"Wood": "pegArm", "Scrap": "knifeArm", "Mech": "normalArm", "Med": "medicalArm", "Cyber": "cyberArm",
       "Knob": "pegArm", "Hook": "hookArm", "MechHand": "normalArm", "MedHand": "medicalArm", "CyberHand": "cyberArm",
       "Chainsaw": "chainsawArm", "Bayonet": "knifeArm"}
BASES = [("Wood", "Wooden base", "Tier 1"), ("Scrap", "Scrap base", "Tier 2"), ("Mech", "Mechanical frame", "Tier 3"),
         ("Med", "Medical base", "Tier 4"), ("Cyber", "Cybernetic frame", "Tier 5")]
HEADS = [("Knob", "Wooden knob", ""), ("Hook", "Hook", ""), ("MechHand", "Mechanical hand", ""), ("MedHand", "Medical hand", ""),
         ("CyberHand", "Cybernetic hand", ""), ("Chainsaw", "Chainsaw", "right arm"), ("Bayonet", "Bayonet", "right arm")]
OUTD = os.path.join(HERE, "out", "scene_parts")

def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a.dot(b)); s = np.linalg.norm(v)
    if s < 1e-8: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)

def export():
    import pose_x as P
    MOD = P.RC.MOD
    P.OUT = OUTD; os.makedirs(OUTD, exist_ok=True)
    c = P.load_clip(os.path.join(P.ANIMS, "Bob", "Bob_Idle.X")); W = P.worlds_at(c, 0.0, False)
    sh = W["Bip01_R_Forearm"][3, :3]; hd = W["Bip01_R_Hand"][3, :3]
    down = hd - sh                                   # dirección del antebrazo en reposo (hacia la mano)
    R = rot_between(down, np.array([1.0, -0.42, 0.0]))   # tumbada en diagonal, mano a la derecha
    jobs = {}
    for kind, items in (("base", BASES), ("head", HEADS)):
        sizes = {}
        for key, _, _ in items:
            m = P.posed_x(os.path.join(MOD, "models_X", "Prosthesis", "%s%s_R_M.X" % (kind, key)),
                          os.path.join(MOD, "textures", "Prosthesis", TEX[key] + ".png"), W)
            v = (np.asarray(m["v"], float) - hd) @ R.T
            mn, mx = v.min(0), v.max(0); v -= (mn + mx) / 2
            m["v"] = v; sizes[key] = float(max(mx - mn))
            P.export("part_%s" % key, [m])
        zoom = max(sizes.values()) * 10 * 0.95       # misma escala en toda la fila
        for key, _, _ in items:
            jobs["part_%s" % key] = ["part_%s" % key, 20, [0.0, 0.0, 0.0], zoom, 18]
    json.dump(jobs, open(os.path.join(OUTD, "tomb_jobs.json"), "w"), indent=0)
    print(len(jobs), "piezas")

def sheet():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import make_workshop as MW
    w, h = 2000, 1250
    img = MW.background(w, h, 33).convert("RGBA")
    d = ImageDraw.Draw(img)
    ft, fs, fl, fsub = MW.font(MW.F_BOLD, 74), MW.font(MW.F_BODY, 30), MW.font(MW.F_BODY, 28), MW.font(MW.F_BODY, 22)
    d.text((54, 40), "MODULAR PROSTHESES", font=ft, fill=(0, 0, 0)); d.text((50, 36), "MODULAR PROSTHESES", font=ft, fill=MW.BONE)
    d.rectangle((50, 132, 50 + d.textlength("MODULAR PROSTHESES", font=ft), 138), fill=MW.RED)
    d.text((50, 152), "Fit any base, mount any attachment · stats come from the combination", font=fs, fill=MW.GREY)
    def row(items, y, cell_w, cell_h, label):
        d.text((50, y - 44), label, font=MW.font(MW.F_BOLD, 30), fill=MW.GREY)
        x0 = (w - cell_w * len(items)) // 2
        for i, (key, name, sub) in enumerate(items):
            x = x0 + i * cell_w
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)    # tarjeta translúcida (encima del fondo)
            od.rounded_rectangle((x + 8, y, x + cell_w - 8, y + cell_h), radius=14, fill=(0, 0, 0, 95), outline=(255, 255, 255, 30))
            if key in ("Cyber", "CyberHand"):
                od.rounded_rectangle((x + 8, y, x + cell_w - 8, y + cell_h), radius=14, outline=(200, 152, 58, 210), width=3)
            img.alpha_composite(ov)
            r = Image.open(os.path.join(HERE, "out", "preview", "parts", "part_%s.png" % key)).convert("RGBA")
            bb = r.getbbox(); r = r.crop(bb)
            box = cell_w - 40, cell_h - 90
            s = min(box[0] / r.width, box[1] / r.height, 1.4); r = r.resize((int(r.width * s), int(r.height * s)), Image.LANCZOS)
            shadow = Image.new("RGBA", r.size, (0, 0, 0, 0)); shadow.putalpha(r.getchannel("A").point(lambda a: int(a * 0.55)))
            px, py = x + (cell_w - r.width) // 2, y + 14 + (box[1] - r.height) // 2
            img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)), (px + 8, py + 12)); img.alpha_composite(r, (px, py))
            tw = d.textlength(name, font=fl); d.text((x + (cell_w - tw) / 2, y + cell_h - 70), name, font=fl, fill=(232, 226, 214))
            if sub:
                col = (214, 168, 74) if sub == "Tier 5" else MW.GREY
                tw = d.textlength(sub, font=fsub); d.text((x + (cell_w - tw) / 2, y + cell_h - 36), sub, font=fsub, fill=col)
    row(BASES, 270, 370, 430, "BASES")
    row(HEADS, 790, 272, 400, "ATTACHMENTS")
    out = os.path.join(HERE, "out", "preview", "parts_lineup.png")
    img.convert("RGB").save(out); print(out)

if __name__ == "__main__":
    sheet() if _a and _a[0] == "sheet" else export()
