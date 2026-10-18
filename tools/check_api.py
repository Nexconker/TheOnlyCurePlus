"""Comprueba que los métodos que el mod llama existen en la clase Java correcta (con herencia),
leyendo la tabla de métodos de cada .class del jar del juego. Uso: python check_api.py"""
import zipfile, struct, sys

JAR = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\projectzomboid.jar"
z = zipfile.ZipFile(JAR)
_cache = {}

def parse_class(name):
    """-> (superclase, set(métodos), [interfaces]) leyendo el constant pool y la tabla de métodos."""
    if name in _cache: return _cache[name]
    try: d = z.read(name + ".class")
    except KeyError:
        _cache[name] = None; return None
    p = 10; n = struct.unpack(">H", d[8:10])[0]; cp = [None] * n; i = 1
    while i < n:
        tag = d[p]
        if tag == 1:
            ln = struct.unpack(">H", d[p + 1:p + 3])[0]; cp[i] = ("utf8", d[p + 3:p + 3 + ln].decode("utf-8", "replace")); p += 3 + ln
        elif tag == 7: cp[i] = ("class", struct.unpack(">H", d[p + 1:p + 3])[0]); p += 3
        elif tag in (8, 16, 19, 20): p += 3
        elif tag == 15: p += 4
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18): p += 5
        elif tag in (5, 6): p += 9; i += 1
        else: raise ValueError("tag %d en %s" % (tag, name))
        i += 1
    p += 2
    this, sup = struct.unpack(">HH", d[p:p + 4]); p += 4
    nif = struct.unpack(">H", d[p:p + 2])[0]; p += 2
    ifaces = []
    for _ in range(nif):
        ifaces.append(cp[cp[struct.unpack(">H", d[p:p + 2])[0]][1]][1]); p += 2
    def skip_members(p, collect=None):
        cnt = struct.unpack(">H", d[p:p + 2])[0]; p += 2
        for _ in range(cnt):
            acc, ni, di, ac = struct.unpack(">HHHH", d[p:p + 8]); p += 8
            if collect is not None: collect.add(cp[ni][1])
            for _ in range(ac):
                ln = struct.unpack(">I", d[p + 2:p + 6])[0]; p += 6 + ln
        return p
    p = skip_members(p)
    methods = set(); skip_members(p, methods)
    supname = cp[cp[sup][1]][1] if sup else None
    _cache[name] = (supname, methods, ifaces)
    return _cache[name]

def has_method(cls, method):
    seen = set(); stack = [cls]
    while stack:
        c = stack.pop()
        if not c or c in seen: continue
        seen.add(c)
        info = parse_class(c)
        if not info: continue
        sup, ms, ifs = info
        if method in ms: return True
        stack.append(sup); stack.extend(ifs)
    return False

CHECKS = {
    "zombie/iso/objects/IsoStove": ["isActivated", "Activated", "getCurrentTemperature", "isLit"],
    "zombie/iso/objects/IsoFireplace": ["isLit"],
    "zombie/iso/objects/IsoBarbecue": ["isLit"],
    "zombie/characters/SurvivorDesc": ["getProfession", "getCharacterProfession"],
    "zombie/scripting/objects/CharacterProfession": ["getName", "toString"],
    "zombie/characters/BodyDamage/BodyDamage": ["isInfected", "getPainReductionFromMeds", "ReduceGeneralHealth", "getBodyPart", "getReduceInfectionPower"],
    "zombie/characters/BodyDamage/BodyPart": ["IsInfected", "setAdditionalPain", "getAdditionalPain", "setAlcoholLevel", "getAlcoholLevel", "setBleeding",
                                               "setBleedingTime", "setDeepWounded", "setDeepWoundTime", "AddDamage", "bitten", "HasInjury", "bandaged",
                                               "isBandageDirty", "setInfectedWound", "setWoundInfectionLevel"],
    "zombie/characters/IsoPlayer": ["playerVoiceSound", "setKnockedDown", "isRecipeKnown", "getKnownRecipes", "getSleepingTabletEffect", "getAccessLevel",
                                     "getRole", "isCriticalHit", "setBlockMovement", "setMoodleCantSprint", "isSprinting", "setSprinting", "isRunning",
                                     "setRunning", "isSneaking", "setSneaking", "isPlayerMoving", "setVariable", "isKnockedDown", "getDescriptor",
                                     "getHumanVisual", "setWornItem", "removeWornItem", "getWornItem", "resetModelNextFrame", "setMaxWeightDelta",
                                     "getMaxWeightDelta", "Say", "isLocalPlayer", "getStats", "getEmitter", "getBodyDamage"],
    "zombie/characters/IsoZombie": ["isCrawling", "toggleCrawling", "getHumanVisual"],
    "zombie/inventory/types/HandWeapon": ["getMaxDamage", "getCategories", "isTwoHandWeapon", "getSwingAnim"],
    "zombie/inventory/InventoryItem": ["getBandagePower", "getStaticModel", "syncItemFields", "getDisplayName", "getVisual", "isRequiresEquippedBothHands",
                                       "getBodyLocation", "getFullType", "setCondition", "getCondition"],
    "zombie/core/skinnedmodel/visual/HumanVisual": ["getSkinTexture"],
    "zombie/core/skinnedmodel/visual/ItemVisual": ["setTextureChoice"],
    "zombie/characters/WornItems/BodyLocationGroup": ["setAltModel", "isAltModel", "isHideModel"],
    # brazo motosierra (TOC/Plus/ChainsawArm.lua, TOC/TimedActions/ChainsawActions.lua)
    "zombie/inventory/types/HandWeapon#saw": ["setMinDamage", "setMaxDamage", "setCriticalChance", "setMaxHitCount", "setDoorDamage", "setTreeDamage",
                                              "setSwingSound", "setZombieHitSound", "setDoorHitSound", "setHitFloorSound", "getConditionMax"],
    "zombie/characters/IsoPlayer#saw": ["getPlayerNum", "getWornItems", "isDead", "isAsleep", "isAiming", "getInventory", "getPrimaryHandItem",
                                        "getSecondaryHandItem", "removeFromHands", "playSound", "stopOrTriggerSound", "getUsername", "getPerkLevel",
                                        "setMetabolicTarget", "SetVariable", "isTimedActionInstant", "getX", "getY", "getZ"],
    "zombie/characters/WornItems/WornItems": ["size", "get"],
    "zombie/characters/WornItems/WornItem": ["getItem"],
    "zombie/characters/BaseCharacterSoundEmitter": ["isPlaying", "stopSoundByName"],
    "zombie/inventory/ItemContainer": ["getAllEvalRecurse", "getFirstTypeRecurse", "getFirstEvalRecurse", "containsRecursive", "AddItem", "Remove"],
    "zombie/inventory/InventoryItem#saw": ["getModData", "getID", "setName", "getContainer", "getFluidContainer", "setJobType", "setJobDelta",
                                           "getScriptItem"],
    "zombie/entity/components/fluids/FluidContainer": ["contains", "getAmount", "adjustAmount"],
    "zombie/scripting/objects/Item": ["getDisplayName", "containsWeaponCategory"],
    # 3.1.0: limpieza de miembros amputados compartida cliente/servidor (TOC/Plus/CutLimbHeal) y muleta inicial
    "zombie/characters/BodyDamage/BodyPart#heal": ["HasInjury", "haveGlass", "bitten", "IsInfected", "setFractureTime", "setScratched",
                                                   "setScratchTime", "setBleeding", "setBleedingTime", "SetBitten", "setBiteTime", "SetInfected",
                                                   "setInfectedWound", "setWoundInfectionLevel", "setCut", "setCutTime", "setDeepWounded",
                                                   "setDeepWoundTime", "setHaveBullet", "setHaveGlass", "setSplint", "setBurnTime", "setNeedBurnWash"],
    "zombie/inventory/ItemContainer#trait": ["containsTypeRecurse"],
}
bad = 0
for key, ms in CHECKS.items():
    cls = key.split("#")[0]          # "clase#grupo": la misma clase en otro bloque de comprobaciones
    if parse_class(cls) is None:
        print("NO EXISTE LA CLASE", cls); bad += 1; continue
    for m in ms:
        ok = has_method(cls, m)
        if not ok: bad += 1
        print("%-5s %s.%s" % ("ok" if ok else "FALTA", cls.split("/")[-1], m))
print("faltan:", bad)
