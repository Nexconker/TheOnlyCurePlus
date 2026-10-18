"""Textos de las opciones de sandbox de la ronda 2 (somníferos como anestesia, amputarse por encima del codo/rodilla).
EN y ES van directos al mod; el resto a tools/i18n/<LANG>.json y luego merge_translations.py.
Uso: python add_round2_sandbox.py && python merge_translations.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
T_DIR = os.path.join(os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"), "lua", "shared", "Translate")
K = ["Sandbox_TOC_SleepingPillAnesthesia", "Sandbox_TOC_SleepingPillAnesthesia_tooltip",
     "Sandbox_TOC_SelfAmputationHigh", "Sandbox_TOC_SelfAmputationHigh_tooltip"]
T = {
 "EN": ["Sleeping pills as anaesthesia",
        "How much sleeping pills can count towards anaesthesia during surgery, in percent (0 = they do not count). Painkillers count up to 60 and alcohol up to 50.",
        "Self-amputation above the elbow and knee",
        "Lets a survivor cut off their own upper arm or thigh. Much more likely to fail or to faint halfway."],
 "ES": ["Somníferos como anestesia",
        "Cuánto pueden contar los somníferos como anestesia al operar, en porcentaje (0 = no cuentan). Los analgésicos cuentan hasta 60 y el alcohol hasta 50.",
        "Amputarse uno mismo por encima del codo y la rodilla",
        "Permite cortarse uno mismo el brazo o el muslo. Mucho más probable fallar o desmayarse a mitad."],
 "DE": ["Schlaftabletten als Betäubung",
        "Wie stark Schlaftabletten bei einer Operation als Betäubung zählen, in Prozent (0 = gar nicht). Schmerzmittel zählen bis 60, Alkohol bis 50.",
        "Selbstamputation oberhalb von Ellbogen und Knie",
        "Erlaubt es, sich selbst den Oberarm oder Oberschenkel abzutrennen. Deutlich höheres Risiko zu scheitern oder mittendrin ohnmächtig zu werden."],
 "FR": ["Somnifères comme anesthésie",
        "Part maximale des somnifères dans l'anesthésie pendant une opération, en pourcentage (0 = ils ne comptent pas). Les antidouleurs comptent jusqu'à 60 et l'alcool jusqu'à 50.",
        "Auto-amputation au-dessus du coude et du genou",
        "Permet de se couper soi-même le bras ou la cuisse. Bien plus de risques d'échouer ou de s'évanouir en cours de route."],
 "IT": ["Sonniferi come anestesia",
        "Quanto possono contare i sonniferi come anestesia durante un'operazione, in percentuale (0 = non contano). Gli antidolorifici contano fino a 60 e l'alcol fino a 50.",
        "Autoamputazione sopra il gomito e il ginocchio",
        "Permette di amputarsi da soli il braccio o la coscia. Molto più probabile fallire o svenire a metà."],
 "KO": ["수면제를 마취로 사용",
        "수술 중 수면제가 마취로 인정되는 최대 비율(퍼센트, 0 = 인정 안 됨). 진통제는 60, 알코올은 50까지 인정된다.",
        "팔꿈치·무릎 위 자가 절단",
        "생존자가 스스로 위팔이나 허벅지를 절단할 수 있다. 실패하거나 도중에 기절할 확률이 훨씬 높다."],
 "PL": ["Tabletki nasenne jako znieczulenie",
        "Ile tabletki nasenne mogą liczyć się jako znieczulenie podczas operacji, w procentach (0 = nie liczą się). Leki przeciwbólowe liczą się do 60, alkohol do 50.",
        "Samoamputacja powyżej łokcia i kolana",
        "Pozwala ocalałemu samemu odciąć sobie ramię lub udo. Znacznie większa szansa na porażkę lub omdlenie w trakcie."],
 "RU": ["Снотворное как анестезия",
        "Насколько снотворное может засчитываться как анестезия при операции, в процентах (0 = не засчитывается). Обезболивающее засчитывается до 60, алкоголь до 50.",
        "Самоампутация выше локтя и колена",
        "Позволяет выжившему самому отрезать себе плечо или бедро. Гораздо выше шанс провала или обморока посреди операции."],
 "TR": ["Uyku hapı anestezi olarak",
        "Ameliyatta uyku haplarının anesteziye en fazla ne kadar sayılacağı, yüzde olarak (0 = sayılmaz). Ağrı kesiciler 60'a, alkol 50'ye kadar sayılır.",
        "Dirsek ve diz üstünden kendi kendine ampütasyon",
        "Hayatta kalanın kendi üst kolunu veya uyluğunu kesmesine izin verir. Başarısız olma ya da yarıda bayılma olasılığı çok daha yüksektir."],
 "UA": ["Снодійне як анестезія",
        "Наскільки снодійне може зараховуватися як анестезія під час операції, у відсотках (0 = не зараховується). Знеболювальне зараховується до 60, алкоголь до 50.",
        "Самоампутація вище ліктя та коліна",
        "Дозволяє вцілілому самому відрізати собі плече або стегно. Значно вищий шанс провалу чи непритомності посеред операції."],
}
# EN y ES directos al mod; EN también a la fuente
for lang in ("EN", "ES"):
    p = os.path.join(T_DIR, lang, "Sandbox.json"); d = json.load(open(p, encoding="utf-8-sig"))
    d.update(dict(zip(K, T[lang]))); json.dump(d, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=4)
sp = os.path.join(HERE, "source_EN.json"); src = json.load(open(sp, encoding="utf-8"))
src.setdefault("Sandbox.json", {}).update(dict(zip(K, T["EN"])))
json.dump(src, open(sp, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
for lang in ("DE", "FR", "IT", "KO", "PL", "RU", "TR", "UA"):
    p = os.path.join(HERE, lang + ".json"); d = json.load(open(p, encoding="utf-8"))
    d.setdefault("Sandbox.json", {}).update(dict(zip(K, T[lang])))
    json.dump(d, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("ok", len(T), "idiomas")
