"""Textos de la 3.2.0: brazo bayoneta (estilo Merle). Se escriben directamente en el mod y en source_EN.json; las
variantes por nivel (…Wrist_R, …Upper_R) las rellena gen_prosthesis_items.py con el nombre de la base.
Uso: python add_320_texts.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
T_DIR = os.path.join(os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"), "lua", "shared", "Translate")
KEYS = {
 "ItemName.json": ["TOC.Prost_KnifeArm_R", "TOC.MountedBlade"],
 "Recipes.json": ["Recipe_Craft_Prosthetic_KnifeArm"],
 "IG_UI.json": ["IGUI_TOC_BladeArmBusy"],
}
T = {
 "EN": ["Bayonet Arm", "Mounted Bayonet", "Build Bayonet Arm", "Your right hand is a bayonet."],
 "ES": ["Brazo bayoneta", "Bayoneta montada", "Montar brazo bayoneta", "Tu mano derecha es una bayoneta."],
 "DE": ["Bajonettarm", "Montiertes Bajonett", "Bajonettarm bauen", "Deine rechte Hand ist ein Bajonett."],
 "FR": ["Bras-baïonnette", "Baïonnette montée", "Fabriquer un bras-baïonnette", "Votre main droite est une baïonnette."],
 "IT": ["Braccio a baionetta", "Baionetta montata", "Costruisci braccio a baionetta", "La tua mano destra è una baionetta."],
 "KO": ["총검 팔", "장착된 총검", "총검 팔 만들기", "오른손이 총검이다."],
 "PL": ["Ramię z bagnetem", "Zamontowany bagnet", "Zrób ramię z bagnetem", "Twoja prawa ręka to bagnet."],
 "PTBR": ["Braço-baioneta", "Baioneta montada", "Montar braço-baioneta", "Sua mão direita é uma baioneta."],
 "RU": ["Рука-штык", "Закреплённый штык", "Сделать руку-штык", "Ваша правая рука — штык."],
 "TR": ["Süngü kol", "Takılı süngü", "Süngü kol yap", "Sağ elin bir süngü."],
 "UA": ["Рука-багнет", "Закріплений багнет", "Зробити руку-багнет", "Ваша права рука — багнет."],
}
order = [(fn, k) for fn, ks in KEYS.items() for k in ks]
for lang, vals in T.items():
    v = dict(zip(order, vals))
    for fn in KEYS:
        p = os.path.join(T_DIR, lang, fn)
        d = json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else {}
        for k in KEYS[fn]: d[k] = v[(fn, k)]
        json.dump(d, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=4)
    print(lang, "ok")
sp = os.path.join(HERE, "source_EN.json"); src = json.load(open(sp, encoding="utf-8"))
for (fn, k), val in zip(order, T["EN"]): src.setdefault(fn, {})[k] = val
json.dump(src, open(sp, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
