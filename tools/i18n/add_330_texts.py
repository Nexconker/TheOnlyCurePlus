"""Textos de la 3.3 modular (bases, cabezales, recetas, banco de prótesis) en el mod de DESARROLLO.
modular_330.json trae EN/ES; modular_330_more.json el resto de idiomas. Los nombres de las bases y cabezales se copian a
los dos lados (_L/_R); las variantes por nivel (Wrist/Upper) las rellena después gen_prosthesis_items.py (MODULAR=1).
Uso: TOC_MEDIA=...TheOnlyCurePlusDev\\42\\media python add_330_texts.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.environ.get("TOC_MEDIA")
assert MEDIA and "Dev" in MEDIA, "sólo para el mod de desarrollo"
T_DIR = os.path.join(MEDIA, "lua", "shared", "Translate")
src = json.load(open(os.path.join(HERE, "modular_330.json"), encoding="utf-8"))
more_p = os.path.join(HERE, "modular_330_more.json")
more = json.load(open(more_p, encoding="utf-8")) if os.path.exists(more_p) else {}
langs = {"EN": {f: {k: v[0] for k, v in ks.items()} for f, ks in src.items()},
         "ES": {f: {k: v[1] for k, v in ks.items()} for f, ks in src.items()}}
langs.update(more)

def both_sides(key):
    if key.startswith("TOC.Prost_") and key[-2:] in ("_L", "_R"):
        if "HeadChainsaw" in key or "HeadBayonet" in key: return [key[:-2] + "_R"]
        return [key[:-2] + "_L", key[:-2] + "_R"]
    return [key]

for lang, files in langs.items():
    for fn, keys in files.items():
        p = os.path.join(T_DIR, lang, fn)
        d = json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else {}
        for k, v in keys.items():
            for kk in both_sides(k): d[kk] = v
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(d, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=4)
    print(lang, "ok")
