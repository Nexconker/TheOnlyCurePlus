------------------------------------------
--      Compatibility API (original by Dhert, extended for TOC+)
------------------------------------------

local DataController = require("TOC/Controllers/DataController")
local StaticData = require("TOC/StaticData")

local TOC_Compat = {}

--- @param player IsoPlayer
--- @param part string limb name, e.g. "Hand_L"
--- @return boolean true when the part exists or a prosthesis replaces it
function TOC_Compat.hasPart(player, part)
    if not player or not part then return true end
    local dc = DataController.GetReady(player:getUsername())
    if not dc then return true end
    return (not dc:getIsCut(part)) or dc:getIsProstEquipped(part)
end

---@param player IsoPlayer
---@param left boolean
---@return boolean
function TOC_Compat.hasHand(player, left)
    return TOC_Compat.hasPart(player, left and "Hand_L" or "Hand_R")
end

---@param player IsoPlayer
---@return boolean
function TOC_Compat.hasBothHands(player)
    return TOC_Compat.hasHand(player, false) and TOC_Compat.hasHand(player, true)
end

-- 11 == both hands, 10 == left hand, 1 == right hand, 0 == no hands
---@param player IsoPlayer
---@return integer
function TOC_Compat.getHands(player)
    return ((TOC_Compat.hasHand(player, false) and 1) or 0) + ((TOC_Compat.hasHand(player, true) and 10) or 0)
end

---@param player IsoPlayer
---@param left boolean
---@return boolean
function TOC_Compat.hasLeg(player, left)
    return TOC_Compat.hasPart(player, left and "Foot_L" or "Foot_R")
end

function TOC_Compat.hasBothLegs(player)
    return TOC_Compat.hasLeg(player, true) and TOC_Compat.hasLeg(player, false)
end

---@param player IsoPlayer
---@return string NONE | CRUTCH | PEG | FULL (see StaticData.MOBILITY)
function TOC_Compat.getMobility(player)
    local ok, LegMobility = pcall(require, "TOC/Plus/LegMobility")
    if ok and LegMobility and player then return LegMobility.Evaluate(player) end
    return StaticData.MOBILITY.FULL
end

---@param player IsoPlayer
---@param limbName string
---@return boolean
function TOC_Compat.isCut(player, limbName)
    local dc = player and DataController.GetReady(player:getUsername())
    return dc and dc:getIsCut(limbName) or false
end

-- 3.3: bases y cabezales de otros mods (TOC/Plus/ModularAPI, global TOC_Modular; ver API_MODULAR.md)
local ModularAPI = require("TOC/Plus/ModularAPI")
TOC_Compat.RegisterHead = ModularAPI.RegisterHead
TOC_Compat.RegisterBase = ModularAPI.RegisterBase
TOC_Compat.CombineProsthesis = ModularAPI.Combine

TOC_Compat.version = StaticData.PLUS_VERSION

return TOC_Compat
