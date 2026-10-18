"""Fusiona tools/i18n/<LANG>.json en media/lua/shared/Translate/<LANG>/*.json.
- No pisa textos que ya existían en ese idioma (los del TOC original).
- Comprueba que se conservan %1/%2 y que no aparece ningún % suelto (rompe el Formatter de Java).
- Rellena las variantes de prótesis (…Wrist/Ankle/Thigh, _R) con el nombre traducido de la base.
Uso: python merge_translations.py [LANG ...]   (sin argumentos: todos los presentes)"""
import os, sys, json, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"), "lua", "shared", "Translate")
src = json.load(open(os.path.join(HERE, "source_EN.json"), encoding="utf-8"))
load = lambda p: json.loads(open(p, encoding="utf-8-sig").read()) if os.path.exists(p) else {}
en = {os.path.basename(f): load(f) for f in glob.glob(os.path.join(T, "EN", "*.json"))}
VAR = re.compile(r"^TOC\.Prost_(\w+?)(Wrist|Upper|Ankle|Thigh)?_([LR])$")
PH = re.compile(r"%\d")

langs = sys.argv[1:] or sorted(os.path.splitext(f)[0] for f in os.listdir(HERE) if re.fullmatch(r"[A-Z]{2,4}\.json", f) and f != "EN.json")
problems = 0
for lang in langs:
    tr = json.load(open(os.path.join(HERE, lang + ".json"), encoding="utf-8"))
    added = 0
    for fn, keys in en.items():
        path = os.path.join(T, lang, fn)
        cur = load(path)
        tfile = tr.get(fn, {})
        for k, v_en in keys.items():
            if k in cur: continue
            val = tfile.get(k)
            if val is None and fn == "ItemName.json":
                m = VAR.match(k)
                if m:   # variante: nombre de la base del mismo lado o del izquierdo
                    for base in ("TOC.Prost_%s_%s" % (m.group(1), m.group(3)), "TOC.Prost_%s_L" % m.group(1)):
                        val = cur.get(base) or tfile.get(base)
                        if val: break
                elif k.endswith("_R"):
                    val = cur.get(k[:-2] + "_L") or tfile.get(k[:-2] + "_L")
            if val is None:
                print("  %s: sin traducción para %s/%s, se deja en inglés" % (lang, fn, k)); val = v_en; problems += 1
            if sorted(PH.findall(val)) != sorted(PH.findall(v_en)):
                print("  %s: marcadores distintos en %s: %r" % (lang, k, val)); problems += 1
            if re.search(r"%(?!\d)", val.replace("%%", "")):   # %% = signo % literal (así lo escribe el juego)
                print("  %s: %% suelto en %s: %r" % (lang, k, val)); problems += 1; val = val.replace("%", " ")
            cur[k] = val; added += 1
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(cur, open(path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=4)
    print("%s: %d textos añadidos" % (lang, added))
print("avisos:", problems)
