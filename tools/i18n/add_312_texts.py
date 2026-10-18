"""Textos de la 3.1.2: recetas de torniquete improvisado, pista de la ventana de cirugía (cómo conseguir un torniquete) y la
opción de sandbox para ocultar los rasgos de amputado. Se escriben DIRECTAMENTE en el mod (la pista cambia un texto que ya
existía y merge_translations no pisa textos existentes). Uso: python add_312_texts.py [PTBR]"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
T_DIR = os.path.join(os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media"), "lua", "shared", "Translate")
KEYS = {
 "Recipes.json": ["Recipe_Craft_Tourniquet_Arm", "Recipe_Craft_Tourniquet_Arm_Belt", "Recipe_Craft_Tourniquet_Leg", "Recipe_Craft_Tourniquet_Leg_Belt"],
 "IG_UI.json": ["IGUI_TOC_SW_Missing_Tourniquet"],
 "Sandbox.json": ["Sandbox_TOC_HideAmputeeTraits", "Sandbox_TOC_HideAmputeeTraits_tooltip"],
}
T = {
 "EN": ["Make Improvised Arm Tourniquet", "Make Arm Tourniquet from a Belt", "Make Improvised Leg Tourniquet", "Make Leg Tourniquet from a Belt",
        "no tourniquet on that side: heavy bleeding. Make one from ripped sheets or a belt and a stick, and wear it on that limb.",
        "Hide amputee traits", "Amputee traits do not appear in character creation. Characters that already have them keep them."],
 "ES": ["Hacer torniquete de brazo improvisado", "Hacer torniquete de brazo con un cinturón", "Hacer torniquete de pierna improvisado", "Hacer torniquete de pierna con un cinturón",
        "sin torniquete en ese lado: sangrado fuerte. Hazlo con tiras de tela o un cinturón y un palo, y póntelo en ese miembro.",
        "Ocultar rasgos de amputado", "Los rasgos de amputado no salen en la creación de personaje. Los personajes que ya los tienen los conservan."],
 "DE": ["Behelfs-Tourniquet für den Arm herstellen", "Arm-Tourniquet aus einem Gürtel herstellen", "Behelfs-Tourniquet für das Bein herstellen", "Bein-Tourniquet aus einem Gürtel herstellen",
        "kein Tourniquet auf dieser Seite: starke Blutung. Stell eines aus Stoffstreifen oder einem Gürtel und einem Stock her und leg es an diesem Körperteil an.",
        "Amputations-Merkmale ausblenden", "Amputations-Merkmale erscheinen nicht bei der Charaktererstellung. Charaktere, die sie bereits haben, behalten sie."],
 "FR": ["Fabriquer un garrot de bras improvisé", "Fabriquer un garrot de bras avec une ceinture", "Fabriquer un garrot de jambe improvisé", "Fabriquer un garrot de jambe avec une ceinture",
        "pas de garrot de ce côté : forte hémorragie. Fabriquez-en un avec des bandes de tissu ou une ceinture et un bâton, puis portez-le sur ce membre.",
        "Masquer les traits d'amputé", "Les traits d'amputé n'apparaissent pas lors de la création du personnage. Les personnages qui les ont déjà les conservent."],
 "IT": ["Crea laccio emostatico improvvisato per braccio", "Crea laccio emostatico per braccio con una cintura", "Crea laccio emostatico improvvisato per gamba", "Crea laccio emostatico per gamba con una cintura",
        "nessun laccio emostatico su quel lato: forte emorragia. Creane uno con strisce di stoffa o una cintura e un bastoncino, e indossalo su quell'arto.",
        "Nascondi i tratti da amputato", "I tratti da amputato non compaiono nella creazione del personaggio. I personaggi che li hanno già li mantengono."],
 "KO": ["임시 팔 지혈대 만들기", "벨트로 팔 지혈대 만들기", "임시 다리 지혈대 만들기", "벨트로 다리 지혈대 만들기",
        "그쪽에 지혈대가 없음: 대량 출혈. 찢은 천이나 벨트와 막대기로 만들어 그 부위에 착용하세요.",
        "절단 특성 숨기기", "캐릭터 생성 화면에 절단 특성이 나타나지 않는다. 이미 가진 캐릭터는 그대로 유지된다."],
 "PL": ["Zrób prowizoryczną opaskę uciskową na rękę", "Zrób opaskę uciskową na rękę z paska", "Zrób prowizoryczną opaskę uciskową na nogę", "Zrób opaskę uciskową na nogę z paska",
        "brak opaski uciskowej po tej stronie: silne krwawienie. Zrób ją z pasków materiału albo paska i patyka, i załóż na tę kończynę.",
        "Ukryj cechy amputacji", "Cechy amputacji nie pojawiają się przy tworzeniu postaci. Postacie, które już je mają, zachowują je."],
 "RU": ["Сделать самодельный жгут для руки", "Сделать жгут для руки из ремня", "Сделать самодельный жгут для ноги", "Сделать жгут для ноги из ремня",
        "на этой стороне нет жгута: сильное кровотечение. Сделайте его из полосок ткани или ремня и палки и наденьте на эту конечность.",
        "Скрыть черты ампутации", "Черты ампутации не появляются при создании персонажа. Персонажи, у которых они уже есть, сохраняют их."],
 "TR": ["Doğaçlama kol turnikesi yap", "Kemerden kol turnikesi yap", "Doğaçlama bacak turnikesi yap", "Kemerden bacak turnikesi yap",
        "o tarafta turnike yok: ağır kanama. Kumaş şeritlerden ya da bir kemer ve bir çubuktan yapıp o uzva tak.",
        "Ampütasyon özelliklerini gizle", "Ampütasyon özellikleri karakter oluşturmada görünmez. Bunlara zaten sahip olan karakterler onları korur."],
 "UA": ["Зробити саморобний джгут для руки", "Зробити джгут для руки з ременя", "Зробити саморобний джгут для ноги", "Зробити джгут для ноги з ременя",
        "немає джгута з цього боку: сильна кровотеча. Зробіть його зі смужок тканини або ременя та палиці й надягніть на цю кінцівку.",
        "Приховати риси ампутації", "Риси ампутації не з'являються під час створення персонажа. Персонажі, які вже їх мають, зберігають їх."],
 "PTBR": ["Fazer torniquete improvisado para braço", "Fazer torniquete para braço com um cinto", "Fazer torniquete improvisado para perna", "Fazer torniquete para perna com um cinto",
          "sem torniquete desse lado: sangramento intenso. Faça um com tiras de pano ou um cinto e um graveto, e use-o nesse membro.",
          "Ocultar características de amputado", "As características de amputado não aparecem na criação de personagem. Personagens que já as têm continuam com elas."],
}
langs = sys.argv[1:] or [l for l in T if l != "PTBR"]
order = [(fn, k) for fn, ks in KEYS.items() for k in ks]
for lang in langs:
    vals = dict(zip(order, T[lang]))
    for fn in KEYS:
        p = os.path.join(T_DIR, lang, fn)
        d = json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else {}
        for k in KEYS[fn]: d[k] = vals[(fn, k)]
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(d, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=4)
    print(lang, "ok")
# fuente EN para futuras traducciones
sp = os.path.join(HERE, "source_EN.json"); src = json.load(open(sp, encoding="utf-8"))
for (fn, k), v in zip(order, T["EN"]): src.setdefault(fn, {})[k] = v
json.dump(src, open(sp, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
