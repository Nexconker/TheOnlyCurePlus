"""Añade a tools/i18n/<LANG>.json las traducciones de los textos del brazo motosierra (17 claves) y deja que
merge_translations.py las pase al mod. Uso: python add_chainsaw_translations.py && python merge_translations.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))

T = {
 "DE": {
  "ContextMenu_TOC_SawMenu": "Kettensägenarm (Benzin %1)", "ContextMenu_TOC_SawStart": "Am Starterseil ziehen",
  "ContextMenu_TOC_SawStop": "Motor abstellen", "ContextMenu_TOC_SawRefuel": "Aus %1 nachtanken",
  "ContextMenu_TOC_SawNoPetrol": "Nachtanken (kein Benzin im Inventar)",
  "IGUI_TOC_SawStarted": "Die Kettensäge heult auf.", "IGUI_TOC_SawSputters": "Sie stottert und geht aus. Nochmal ziehen.",
  "IGUI_TOC_SawNoFuel": "Der Tank ist leer: mit Benzin nachfüllen.", "IGUI_TOC_SawStalled": "Der Kettensäge geht das Benzin aus und sie bleibt stehen.",
  "IGUI_TOC_SawRunning": "Erst den Motor abstellen.", "IGUI_TOC_SawFull": "Der Tank ist voll.",
  "IGUI_TOC_SawArmBusy": "Deine rechte Hand ist eine Kettensäge.", "IGUI_TOC_SawRefueling": "Tanke nach",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Kettensägenarm bauen",
  "TOC.Prost_ChainsawArm_R": "Kettensägenarm", "TOC.Prost_ChainsawArmWrist_R": "Kettensägenarm", "TOC.MountedChainsaw": "Montierte Kettensäge"},
 "FR": {
  "ContextMenu_TOC_SawMenu": "Bras tronçonneuse (essence %1)", "ContextMenu_TOC_SawStart": "Tirer le lanceur",
  "ContextMenu_TOC_SawStop": "Couper le moteur", "ContextMenu_TOC_SawRefuel": "Faire le plein avec %1",
  "ContextMenu_TOC_SawNoPetrol": "Faire le plein (pas d'essence dans l'inventaire)",
  "IGUI_TOC_SawStarted": "La tronçonneuse rugit.", "IGUI_TOC_SawSputters": "Elle toussote et cale. Tirez encore.",
  "IGUI_TOC_SawNoFuel": "Le réservoir est vide : remettez de l'essence.", "IGUI_TOC_SawStalled": "La tronçonneuse tombe à sec et cale.",
  "IGUI_TOC_SawRunning": "Coupez d'abord le moteur.", "IGUI_TOC_SawFull": "Le réservoir est plein.",
  "IGUI_TOC_SawArmBusy": "Votre main droite est une tronçonneuse.", "IGUI_TOC_SawRefueling": "Plein d'essence",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Fabriquer un bras tronçonneuse",
  "TOC.Prost_ChainsawArm_R": "Bras tronçonneuse", "TOC.Prost_ChainsawArmWrist_R": "Bras tronçonneuse", "TOC.MountedChainsaw": "Tronçonneuse montée"},
 "IT": {
  "ContextMenu_TOC_SawMenu": "Braccio motosega (benzina %1)", "ContextMenu_TOC_SawStart": "Tira la corda d'avviamento",
  "ContextMenu_TOC_SawStop": "Spegni il motore", "ContextMenu_TOC_SawRefuel": "Fai rifornimento da %1",
  "ContextMenu_TOC_SawNoPetrol": "Fai rifornimento (niente benzina nell'inventario)",
  "IGUI_TOC_SawStarted": "La motosega ruggisce.", "IGUI_TOC_SawSputters": "Scoppietta e si spegne. Tira ancora.",
  "IGUI_TOC_SawNoFuel": "Il serbatoio è vuoto: rifornisci di benzina.", "IGUI_TOC_SawStalled": "La motosega resta a secco e si spegne.",
  "IGUI_TOC_SawRunning": "Prima spegni il motore.", "IGUI_TOC_SawFull": "Il serbatoio è pieno.",
  "IGUI_TOC_SawArmBusy": "La tua mano destra è una motosega.", "IGUI_TOC_SawRefueling": "Rifornimento",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Costruisci braccio motosega",
  "TOC.Prost_ChainsawArm_R": "Braccio motosega", "TOC.Prost_ChainsawArmWrist_R": "Braccio motosega", "TOC.MountedChainsaw": "Motosega montata"},
 "KO": {
  "ContextMenu_TOC_SawMenu": "전기톱 팔 (연료 %1)", "ContextMenu_TOC_SawStart": "시동줄 당기기",
  "ContextMenu_TOC_SawStop": "엔진 끄기", "ContextMenu_TOC_SawRefuel": "%1(으)로 연료 넣기",
  "ContextMenu_TOC_SawNoPetrol": "연료 넣기 (인벤토리에 휘발유 없음)",
  "IGUI_TOC_SawStarted": "전기톱이 굉음을 내며 깨어난다.", "IGUI_TOC_SawSputters": "털털거리다 꺼졌다. 다시 당기자.",
  "IGUI_TOC_SawNoFuel": "연료통이 비었다: 휘발유를 넣어야 한다.", "IGUI_TOC_SawStalled": "전기톱의 연료가 떨어져 멈췄다.",
  "IGUI_TOC_SawRunning": "먼저 엔진을 꺼야 한다.", "IGUI_TOC_SawFull": "연료통이 가득 찼다.",
  "IGUI_TOC_SawArmBusy": "오른손은 전기톱이다.", "IGUI_TOC_SawRefueling": "연료 넣는 중",
  "Recipe_Craft_Prosthetic_ChainsawArm": "전기톱 팔 만들기",
  "TOC.Prost_ChainsawArm_R": "전기톱 팔", "TOC.Prost_ChainsawArmWrist_R": "전기톱 팔", "TOC.MountedChainsaw": "장착된 전기톱"},
 "PL": {
  "ContextMenu_TOC_SawMenu": "Ramię piła łańcuchowa (paliwo %1)", "ContextMenu_TOC_SawStart": "Pociągnij linkę rozrusznika",
  "ContextMenu_TOC_SawStop": "Wyłącz silnik", "ContextMenu_TOC_SawRefuel": "Zatankuj z: %1",
  "ContextMenu_TOC_SawNoPetrol": "Zatankuj (brak benzyny w ekwipunku)",
  "IGUI_TOC_SawStarted": "Piła ryczy, budząc się do życia.", "IGUI_TOC_SawSputters": "Krztusi się i gaśnie. Pociągnij jeszcze raz.",
  "IGUI_TOC_SawNoFuel": "Bak jest pusty: zatankuj benzynę.", "IGUI_TOC_SawStalled": "Pile skończyło się paliwo i zgasła.",
  "IGUI_TOC_SawRunning": "Najpierw wyłącz silnik.", "IGUI_TOC_SawFull": "Bak jest pełny.",
  "IGUI_TOC_SawArmBusy": "Twoja prawa ręka to piła łańcuchowa.", "IGUI_TOC_SawRefueling": "Tankowanie",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Zbuduj ramię z piłą łańcuchową",
  "TOC.Prost_ChainsawArm_R": "Ramię z piłą łańcuchową", "TOC.Prost_ChainsawArmWrist_R": "Ramię z piłą łańcuchową", "TOC.MountedChainsaw": "Zamontowana piła łańcuchowa"},
 "RU": {
  "ContextMenu_TOC_SawMenu": "Рука-бензопила (топливо %1)", "ContextMenu_TOC_SawStart": "Дёрнуть шнур стартера",
  "ContextMenu_TOC_SawStop": "Заглушить двигатель", "ContextMenu_TOC_SawRefuel": "Заправить из: %1",
  "ContextMenu_TOC_SawNoPetrol": "Заправить (нет бензина в инвентаре)",
  "IGUI_TOC_SawStarted": "Бензопила с рёвом оживает.", "IGUI_TOC_SawSputters": "Чихает и глохнет. Дёрни ещё раз.",
  "IGUI_TOC_SawNoFuel": "Бак пуст: залей бензин.", "IGUI_TOC_SawStalled": "У бензопилы кончилось топливо, и она заглохла.",
  "IGUI_TOC_SawRunning": "Сначала заглуши двигатель.", "IGUI_TOC_SawFull": "Бак полон.",
  "IGUI_TOC_SawArmBusy": "Твоя правая рука — бензопила.", "IGUI_TOC_SawRefueling": "Заправка",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Собрать руку-бензопилу",
  "TOC.Prost_ChainsawArm_R": "Рука-бензопила", "TOC.Prost_ChainsawArmWrist_R": "Рука-бензопила", "TOC.MountedChainsaw": "Закреплённая бензопила"},
 "TR": {
  "ContextMenu_TOC_SawMenu": "Testere kol (yakıt %1)", "ContextMenu_TOC_SawStart": "Marş ipini çek",
  "ContextMenu_TOC_SawStop": "Motoru durdur", "ContextMenu_TOC_SawRefuel": "Yakıt doldur: %1",
  "ContextMenu_TOC_SawNoPetrol": "Yakıt doldur (envanterde benzin yok)",
  "IGUI_TOC_SawStarted": "Motorlu testere kükreyerek çalıştı.", "IGUI_TOC_SawSputters": "Öksürüp stop etti. Tekrar çek.",
  "IGUI_TOC_SawNoFuel": "Depo boş: benzin doldur.", "IGUI_TOC_SawStalled": "Testerenin yakıtı bitti ve stop etti.",
  "IGUI_TOC_SawRunning": "Önce motoru durdur.", "IGUI_TOC_SawFull": "Depo dolu.",
  "IGUI_TOC_SawArmBusy": "Sağ elin bir motorlu testere.", "IGUI_TOC_SawRefueling": "Yakıt dolduruluyor",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Testere Kol Yap",
  "TOC.Prost_ChainsawArm_R": "Testere Kol", "TOC.Prost_ChainsawArmWrist_R": "Testere Kol", "TOC.MountedChainsaw": "Takılı Motorlu Testere"},
 "UA": {
  "ContextMenu_TOC_SawMenu": "Рука-бензопила (пальне %1)", "ContextMenu_TOC_SawStart": "Смикнути шнур стартера",
  "ContextMenu_TOC_SawStop": "Заглушити двигун", "ContextMenu_TOC_SawRefuel": "Заправити з: %1",
  "ContextMenu_TOC_SawNoPetrol": "Заправити (немає бензину в інвентарі)",
  "IGUI_TOC_SawStarted": "Бензопила з ревом оживає.", "IGUI_TOC_SawSputters": "Чхає і глухне. Смикни ще раз.",
  "IGUI_TOC_SawNoFuel": "Бак порожній: залий бензин.", "IGUI_TOC_SawStalled": "У бензопили скінчилося пальне, і вона заглухла.",
  "IGUI_TOC_SawRunning": "Спершу заглуши двигун.", "IGUI_TOC_SawFull": "Бак повний.",
  "IGUI_TOC_SawArmBusy": "Твоя права рука — бензопила.", "IGUI_TOC_SawRefueling": "Заправка",
  "Recipe_Craft_Prosthetic_ChainsawArm": "Зібрати руку-бензопилу",
  "TOC.Prost_ChainsawArm_R": "Рука-бензопила", "TOC.Prost_ChainsawArmWrist_R": "Рука-бензопила", "TOC.MountedChainsaw": "Закріплена бензопила"},
}
FILE_OF = {}
src = json.load(open(os.path.join(HERE, "new_chainsaw_EN.json"), encoding="utf-8"))
for fn, kv in src.items():
    for k in kv: FILE_OF[k] = fn
for lang, kv in T.items():
    assert set(kv) == set(FILE_OF), (lang, set(FILE_OF) ^ set(kv))
    p = os.path.join(HERE, lang + ".json"); d = json.load(open(p, encoding="utf-8"))
    for k, v in kv.items(): d.setdefault(FILE_OF[k], {})[k] = v
    json.dump(d, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(lang, len(kv))
