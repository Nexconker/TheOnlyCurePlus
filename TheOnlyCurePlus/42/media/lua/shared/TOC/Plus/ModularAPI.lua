-- TOC+ 3.3: API para que otros mods añadan bases y cabezales a las prótesis modulares (guía: API_MODULAR.md del repo).
-- Global TOC_Modular (también en TOC_Compat, cliente). Los valores se acotan para que un mod no rompa el equilibrio.
--
--   TOC_Modular.RegisterHead("Prost_HeadClaw", { hookLike = false, twoHanded = true, combatMod = 0.98, timeBonus = 1,
--                                                 wearMul = 1.0, side = nil, metalBase = false, minBaseTier = 2 })
--   TOC_Modular.RegisterBase("Prost_BaseBone", { tier = 2, timeBonus = 1, twoHanded = true, combatMod = 0.92,
--                                                 wearPerAction = 0.6, material = "wood" })
--
-- Los ítems deben estar en el módulo TOC con el nombre <tipo>_L / <tipo>_R (bases: también <tipo>Wrist_X y
-- <tipo>Upper_X, una por nivel), los cabezales en la ubicación toc:ArmHead_X y las bases en toc:ArmProst_X.

local StaticData = require("TOC/StaticData")
------------------

TOC_Modular = TOC_Modular or {}
TOC_Modular.API_VERSION = 1

local function clamp(v, lo, hi, def)
    if type(v) ~= "number" then return def end
    return math.max(lo, math.min(hi, v))
end

local function checkType(typeBase, prefix)
    if type(typeBase) ~= "string" or not string.match(typeBase, "^Prost_%a+$") then
        print("[TOC+] TOC_Modular: tipo no válido '" .. tostring(typeBase) .. "' (se espera " .. prefix .. "Nombre, sólo letras)")
        return false
    end
    for _, suf in ipairs({ "Wrist", "Upper", "Ankle", "Thigh" }) do
        if string.sub(typeBase, -#suf) == suf then
            print("[TOC+] TOC_Modular: '" .. typeBase .. "' no puede acabar en " .. suf .. " (es un sufijo de nivel)")
            return false
        end
    end
    return true
end

---Registra un cabezal. Devuelve true si se aceptó.
---@param typeBase string p. ej. "Prost_HeadClaw" (ítems TOC.Prost_HeadClaw_L / _R)
---@param def table
---@return boolean
function TOC_Modular.RegisterHead(typeBase, def)
    if not checkType(typeBase, "Prost_Head") or type(def) ~= "table" then return false end
    StaticData.PROSTHESIS_HEADS[typeBase] = {
        hookLike = def.hookLike == true,
        twoHanded = def.twoHanded ~= false and def.hookLike ~= true,
        combatMod = clamp(def.combatMod, 0.5, 1.05, 1.0),
        timeBonus = math.floor(clamp(def.timeBonus, 0, 2, 0)),
        wearMul = clamp(def.wearMul, 0.5, 3.0, 1.0),
        side = (def.side == "L" or def.side == "R") and def.side or nil,
        metalBase = def.metalBase == true,
        minBaseTier = def.minBaseTier and math.floor(clamp(def.minBaseTier, 1, 5, 1)) or nil,
        paintable = def.paintable == true,
        external = true,
    }
    return true
end

---Registra una base (tier 1-5). Devuelve true si se aceptó.
---@param typeBase string p. ej. "Prost_BaseBone"
---@param def table
---@return boolean
function TOC_Modular.RegisterBase(typeBase, def)
    if not checkType(typeBase, "Prost_Base") or type(def) ~= "table" then return false end
    StaticData.PROSTHESIS_TIERS[typeBase] = {
        tier = math.floor(clamp(def.tier, 1, 5, 2)),
        group = "Top",
        timeBonus = math.floor(clamp(def.timeBonus, 0, 4, 1)),
        twoHanded = def.twoHanded ~= false,
        combatMod = clamp(def.combatMod, 0.5, 1.0, 0.9),
        wearPerAction = clamp(def.wearPerAction, 0.1, 2.0, 0.6),
        modular = true,
        material = (def.material == "wood" or def.material == "metal" or def.material == "polymer") and def.material or "metal",
        paintable = def.paintable == true,
        external = true,
    }
    return true
end

---@return table<string, table> cabezales registrados (los de TOC+ y los de otros mods)
function TOC_Modular.GetHeads() return StaticData.PROSTHESIS_HEADS end

---@return table<string, table> tiers de prótesis (bases modulares incluidas)
function TOC_Modular.GetTiers() return StaticData.PROSTHESIS_TIERS end

---Combinación base + cabezal tal y como la usa el juego
---@param baseFullType string
---@param headFullType string?
function TOC_Modular.Combine(baseFullType, headFullType)
    return StaticData.CombineTier(StaticData.GetProsthesisTier(baseFullType), headFullType)
end

return TOC_Modular
