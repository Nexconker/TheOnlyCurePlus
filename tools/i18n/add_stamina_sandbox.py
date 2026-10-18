"""Textos de las opciones de sandbox de resistencia con muleta / al arrastrarse (3.1.1, comentario del Workshop: "cansado
tras 7-10 pasos con muleta"). EN y ES van directos al mod; el resto a tools/i18n/<LANG>.json y luego merge_translations.py.
Uso: python add_stamina_sandbox.py && python merge_translations.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
T_DIR = os.path.join(os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"), "lua", "shared", "Translate")
K = ["Sandbox_TOC_CrutchStaminaDrain", "Sandbox_TOC_CrutchStaminaDrain_tooltip",
     "Sandbox_TOC_CrawlStaminaDrain", "Sandbox_TOC_CrawlStaminaDrain_tooltip",
     "Sandbox_TOC_AmputeeTraitStaminaDrain", "Sandbox_TOC_AmputeeTraitStaminaDrain_tooltip"]
T = {
 "EN": ["Crutch stamina drain (%%)",
        "Extra stamina used while walking on a crutch, in percent of the default (100 = tired after about a minute of walking without rest, 0 = no extra cost).",
        "Crawling stamina drain (%%)",
        "Extra stamina used while crawling, in percent of the default (100 = tired after about 40 seconds, 0 = no extra cost).",
        "Experienced amputees (%%)",
        "Characters who start with a leg amputee trait already know how to use crutches: their crutch and crawling stamina cost is this percent of the values above (50 = half)."],
 "ES": ["Gasto de resistencia con muleta (%%)",
        "Resistencia extra que se gasta al andar con muleta, en porcentaje del valor por defecto (100 = cansado tras un minuto andando sin parar, 0 = sin gasto extra).",
        "Gasto de resistencia al arrastrarse (%%)",
        "Resistencia extra que se gasta al arrastrarse, en porcentaje del valor por defecto (100 = cansado tras unos 40 segundos, 0 = sin gasto extra).",
        "Amputados con experiencia (%%)",
        "Los personajes que empiezan con un rasgo de pierna amputada ya saben usar muletas: su gasto con muleta y al arrastrarse es este porcentaje de los valores de arriba (50 = la mitad)."],
 "DE": ["Ausdauerverbrauch mit Krücke (%%)",
        "Zusätzlicher Ausdauerverbrauch beim Gehen mit Krücke, in Prozent des Standardwerts (100 = nach etwa einer Minute Gehen ohne Pause erschöpft, 0 = kein Zusatzverbrauch).",
        "Ausdauerverbrauch beim Kriechen (%%)",
        "Zusätzlicher Ausdauerverbrauch beim Kriechen, in Prozent des Standardwerts (100 = nach etwa 40 Sekunden erschöpft, 0 = kein Zusatzverbrauch).",
        "Erfahrene Amputierte (%%)",
        "Charaktere, die mit einem Beinamputations-Merkmal beginnen, können bereits mit Krücken umgehen: ihr Verbrauch mit Krücke und beim Kriechen beträgt diesen Prozentsatz der obigen Werte (50 = die Hälfte)."],
 "FR": ["Coût d'endurance avec béquille (%%)",
        "Endurance supplémentaire dépensée en marchant avec une béquille, en pourcentage de la valeur par défaut (100 = fatigué après environ une minute de marche sans pause, 0 = aucun coût supplémentaire).",
        "Coût d'endurance en rampant (%%)",
        "Endurance supplémentaire dépensée en rampant, en pourcentage de la valeur par défaut (100 = fatigué après environ 40 secondes, 0 = aucun coût supplémentaire).",
        "Amputés expérimentés (%%)",
        "Les personnages qui commencent avec un trait d'amputation de la jambe savent déjà utiliser une béquille : leur coût avec béquille et en rampant est ce pourcentage des valeurs ci-dessus (50 = la moitié)."],
 "IT": ["Consumo di resistenza con la stampella (%%)",
        "Resistenza extra consumata camminando con la stampella, in percentuale del valore predefinito (100 = stanco dopo circa un minuto di cammino senza pause, 0 = nessun consumo extra).",
        "Consumo di resistenza strisciando (%%)",
        "Resistenza extra consumata strisciando, in percentuale del valore predefinito (100 = stanco dopo circa 40 secondi, 0 = nessun consumo extra).",
        "Amputati esperti (%%)",
        "I personaggi che iniziano con un tratto di amputazione della gamba sanno già usare le stampelle: il loro consumo con la stampella e strisciando è questa percentuale dei valori sopra (50 = la metà)."],
 "KO": ["목발 사용 시 지구력 소모 (%%)",
        "목발로 걸을 때 추가로 소모되는 지구력, 기본값 대비 퍼센트 (100 = 쉬지 않고 약 1분 걸으면 지침, 0 = 추가 소모 없음).",
        "기어갈 때 지구력 소모 (%%)",
        "기어갈 때 추가로 소모되는 지구력, 기본값 대비 퍼센트 (100 = 약 40초 후 지침, 0 = 추가 소모 없음).",
        "숙련된 절단 장애인 (%%)",
        "다리 절단 특성을 가지고 시작한 캐릭터는 이미 목발 사용에 익숙하다: 목발과 기어가기 소모량이 위 값의 이 퍼센트가 된다 (50 = 절반)."],
 "PL": ["Zużycie wytrzymałości o kuli (%%)",
        "Dodatkowa wytrzymałość zużywana podczas chodzenia o kuli, w procentach wartości domyślnej (100 = zmęczenie po około minucie marszu bez odpoczynku, 0 = brak dodatkowego kosztu).",
        "Zużycie wytrzymałości podczas czołgania (%%)",
        "Dodatkowa wytrzymałość zużywana podczas czołgania się, w procentach wartości domyślnej (100 = zmęczenie po około 40 sekundach, 0 = brak dodatkowego kosztu).",
        "Doświadczeni po amputacji (%%)",
        "Postacie, które zaczynają z cechą amputacji nogi, umieją już chodzić o kulach: ich zużycie o kuli i podczas czołgania to ten procent powyższych wartości (50 = połowa)."],
 "RU": ["Расход выносливости с костылём (%%)",
        "Дополнительная выносливость, расходуемая при ходьбе с костылём, в процентах от значения по умолчанию (100 = усталость примерно через минуту ходьбы без отдыха, 0 = без дополнительного расхода).",
        "Расход выносливости при ползании (%%)",
        "Дополнительная выносливость, расходуемая при ползании, в процентах от значения по умолчанию (100 = усталость примерно через 40 секунд, 0 = без дополнительного расхода).",
        "Опытные ампутанты (%%)",
        "Персонажи, начинающие с чертой ампутации ноги, уже умеют ходить на костылях: их расход с костылём и при ползании составляет этот процент от значений выше (50 = половина)."],
 "TR": ["Koltuk değneğiyle dayanıklılık tüketimi (%%)",
        "Koltuk değneğiyle yürürken harcanan ek dayanıklılık, varsayılan değerin yüzdesi olarak (100 = ara vermeden yaklaşık bir dakika yürüdükten sonra yorgun, 0 = ek tüketim yok).",
        "Sürünürken dayanıklılık tüketimi (%%)",
        "Sürünürken harcanan ek dayanıklılık, varsayılan değerin yüzdesi olarak (100 = yaklaşık 40 saniye sonra yorgun, 0 = ek tüketim yok).",
        "Deneyimli ampütasyonlular (%%)",
        "Bacak ampütasyonu özelliğiyle başlayan karakterler koltuk değneği kullanmayı zaten bilir: koltuk değneği ve sürünme tüketimleri yukarıdaki değerlerin bu yüzdesidir (50 = yarısı)."],
 "UA": ["Витрата витривалості з милицею (%%)",
        "Додаткова витривалість, що витрачається під час ходьби з милицею, у відсотках від значення за замовчуванням (100 = втома приблизно через хвилину ходьби без відпочинку, 0 = без додаткової витрати).",
        "Витрата витривалості під час повзання (%%)",
        "Додаткова витривалість, що витрачається під час повзання, у відсотках від значення за замовчуванням (100 = втома приблизно через 40 секунд, 0 = без додаткової витрати).",
        "Досвідчені ампутанти (%%)",
        "Персонажі, які починають із рисою ампутації ноги, вже вміють ходити на милицях: їхня витрата з милицею та під час повзання становить цей відсоток від значень вище (50 = половина)."],
}
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
