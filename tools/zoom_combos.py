import os, sys
_names = sys.argv[1:]
sys.argv = sys.argv[:1]   # render_icons toma argv[1] como ruta del mod
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import render_combos as RC
from render_icons import rot
OUT = RC.OUTDIR
want = _names or ["Antebrazo + brazo de madera","Pantorrilla + pata de palo","Pantorrilla + pierna mecanica","Pantorrilla + pierna medica","Pie izq. + pata de palo","Torniquete de pierna","Pantorrilla izq. amputada","Muslo izq. amputado","Pie izq. amputado"]
views=[("frente",rot(0,180,0)),("3/4",rot(0,140,0)),("lado",rot(0,90,0)),("espalda",rot(0,0,0))]
for sex in ("Male","Female"):
    cs = {c[0]: c for c in RC.combos(sex)}
    rows=[]
    for name in want:
        label,masks,pieces = cs[name]
        meshes=[RC.body_mesh(sex,masks)]
        for kind,path,tex in pieces:
            meshes += [RC.piece_x(path,tex)] if kind=="x" else RC.piece_fbx(path,tex)
        cells=[]
        for vn,R in views:
            img=Image.fromarray(RC.rasterize(meshes,R,720),"RGBA")
            # recorte: brazo izq (zona superior derecha) o piernas (mitad inferior)
            if "brazo" in name or "Antebrazo" in name or "Mano" in name:
                box=(0,120,360,330) if vn!="espalda" else (360,120,720,330)
            else:
                box=(170,380,550,720)
            cells.append(img.crop(box).resize((380,340) if "brazo" in name or "Antebrazo" in name else (380,340),Image.LANCZOS))
        row=Image.new("RGBA",(380*4+30,340+24),(50,50,54,255)); d=ImageDraw.Draw(row); d.text((4,4),"%s - %s"%(sex,label),fill=(255,255,255,255))
        for i,c in enumerate(cells): row.paste(c,(i*390,24))
        rows.append(row)
    sheet=Image.new("RGBA",(rows[0].width,sum(r.height for r in rows)),(50,50,54,255)); y=0
    for r in rows: sheet.paste(r,(0,y)); y+=r.height
    sheet.save(os.path.join(OUT,"zoom_%s.png"%sex)); print("saved",sex)
