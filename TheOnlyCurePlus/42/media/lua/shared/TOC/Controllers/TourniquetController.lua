local CommonMethods = require("TOC/CommonMethods")
local StaticData = require("TOC/StaticData")
---------------------------

---@class TourniquetController
local TourniquetController = {}

---Is this item type one of our tourniquets (arm or leg)?
---@param fType string
---@return boolean
function TourniquetController.IsItemTourniquet(fType)
    return string.contains(fType, "Surg_Arm_Tourniquet_") or string.contains(fType, "Surg_Leg_Tourniquet_")
end

---Check that the patient wears the tourniquet matching the limb (arm/leg group and side)
---@param player IsoPlayer
---@param limbName string
---@return boolean
function TourniquetController.CheckTourniquetOnLimb(player, limbName)
    if not player or not limbName then return false end
    local side = CommonMethods.GetSide(limbName)
    local groupBase = StaticData.IsLegLimb(limbName) and "Bottom" or "Top"
    local prefix = StaticData.TOURNIQUET_TYPE_PREFIX[groupBase]

    local wornItems = player:getWornItems()
    if not wornItems then return false end
    for j = 1, wornItems:size() do
        local wornItem = wornItems:get(j - 1)
        local item = wornItem and wornItem:getItem()
        if item then
            local fType = item:getFullType()
            if string.contains(fType, prefix) and luautils.stringEnds(fType, side) then
                return true
            end
        end
    end
    return false
end

-- kept for compatibility with the original API
TourniquetController.CheckTourniquet = TourniquetController.CheckTourniquetOnLimb

return TourniquetController
