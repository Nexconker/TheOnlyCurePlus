"""Lua: variantes de prótesis por nivel (sufijo Wrist/Ankle/Thigh), prótesis sobre el muslo permitida,
regla de auto-cirugía separada, y FitToStump (cambia el ítem por la variante del muñón al vestirlo)."""
import os, sys
MOD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TOC_MEDIA", r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media")
LUA = os.path.join(MOD, "lua")

def patch(rel, pairs):
    p = os.path.join(LUA, rel)
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (rel, a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("patched", rel)

# ---------------------------------------------------------------- StaticData
patch("shared/TOC/StaticData.lua", [
("""-- Highest part of each group: no prosthesis can be fitted there.
StaticData.NO_PROSTHESIS_PARTS_IND_STR = { UpperArm = true, UpperLeg = true }""",
"""-- Highest part of each group where no prosthesis can be fitted. Legs have an above-knee
-- prosthesis (thigh socket + articulated knee), arms do not.
StaticData.NO_PROSTHESIS_PARTS_IND_STR = { UpperArm = true }
-- Parts a surgeon cannot amputate on themselves.
StaticData.NO_SELF_SURGERY_PARTS_IND_STR = { UpperArm = true, UpperLeg = true }"""),
("""---@param fullType string e.g. "TOC.Prost_HookArm_L"
---@return table? tierData
function StaticData.GetProsthesisTier(fullType)
    local base = string.match(fullType, "^TOC%.(Prost_%a+)_[LR]$")
    if not base then return nil end
    return StaticData.PROSTHESIS_TIERS[base]
end""",
"""-- Every tier exists in model variants per amputation level (same name, icon and stats; only the
-- worn model differs): item name = base .. suffix .. _side, e.g. Prost_HookArmWrist_L.
StaticData.PROSTHESIS_LEVEL_SUFFIX = { Hand = "Wrist", ForeArm = "", Foot = "Ankle", LowerLeg = "", UpperLeg = "Thigh" }
local LEVEL_SUFFIXES = { "Wrist", "Ankle", "Thigh" }

---@param fullType string e.g. "TOC.Prost_HookArmWrist_L"
---@return string? base e.g. "Prost_HookArm" (level suffix removed), string? side
function StaticData.GetProsthesisBase(fullType)
    if type(fullType) ~= "string" then return nil end
    local base, side = string.match(fullType, "^TOC%.(Prost_%a+)_([LR])$")
    if not base then return nil end
    for _, suf in ipairs(LEVEL_SUFFIXES) do
        if #base > #suf and string.sub(base, -#suf) == suf then
            base = string.sub(base, 1, #base - #suf)
            break
        end
    end
    return base, side
end

---@param fullType string e.g. "TOC.Prost_HookArm_L"
---@return table? tierData
function StaticData.GetProsthesisTier(fullType)
    local base = StaticData.GetProsthesisBase(fullType)
    if not base then return nil end
    return StaticData.PROSTHESIS_TIERS[base]
end

---Item type of the variant modelled for a stump level
---@param fullType string any variant of the prosthesis
---@param part string highest amputated part, e.g. "Hand", "LowerLeg"
---@return string? fullType
function StaticData.GetProsthesisTypeForPart(fullType, part)
    local base, side = StaticData.GetProsthesisBase(fullType)
    local suf = StaticData.PROSTHESIS_LEVEL_SUFFIX[part]
    if not base or suf == nil then return nil end
    return "TOC." .. base .. suf .. "_" .. side
end"""),
])

# ---------------------------------------------------------------- self surgery rule
patch("client/TOC/UI/Interactions/CutLimbInteractionHandler.lua", [
("    if surgeon == patient and StaticData.NO_PROSTHESIS_PARTS_IND_STR[part] then",
 "    if surgeon == patient and StaticData.NO_SELF_SURGERY_PARTS_IND_STR[part] then"),
])

# ---------------------------------------------------------------- ProsthesisHandler
patch("shared/TOC/Handlers/ProsthesisHandler.lua", [
("""---Handle equipping or unequipping prosthetics (runs on the client that owns the character).""",
"""---Type of the variant modelled for the stump the LOCAL/given player has on that side.
---@param username string
---@param fullType string
---@return string fullType (unchanged when no variant applies)
function ProsthesisHandler.GetFittedType(username, fullType)
    local tier = ProsthesisHandler.GetTier(fullType)
    if not tier then return fullType end
    local side = CommonMethods.GetSide(fullType)
    local highest = CachedDataHandler.GetHighestAmputatedLimbs(username)
    local hal = highest and highest[tier.group .. "_" .. side]
    if not hal then return fullType end
    local part = string.match(hal, "^(%a+)_")
    local want = StaticData.GetProsthesisTypeForPart(fullType, part)
    if want and want ~= fullType and getScriptManager():FindItem(want) then return want end
    return fullType
end

---Replace a just-worn prosthesis by the variant modelled for the stump level (visual only: same
---name, stats, condition and mod data). Mirrors vanilla ISClothingExtraAction so MP stays in sync.
---@param character IsoPlayer
---@param item InventoryItem
---@return InventoryItem item worn after the swap
function ProsthesisHandler.FitToStump(character, item)
    local want = ProsthesisHandler.GetFittedType(character:getUsername(), item:getFullType())
    if want == item:getFullType() then return item end
    local newItem = instanceItem(want)
    if not newItem then return item end
    local ok = pcall(function()
        if copyClothingItem then copyClothingItem(item, newItem) else newItem:setCondition(item:getCondition()) end
        local inv = character:getInventory()
        character:removeFromHands(item)
        character:removeWornItem(item, false)
        inv:Remove(item)
        if sendRemoveItemFromContainer then sendRemoveItemFromContainer(inv, item) end
        inv:AddItem(newItem)
        if sendAddItemToContainer then sendAddItemToContainer(inv, newItem) end
        character:setWornItem(newItem:getBodyLocation(), newItem)
        if sendClothing then sendClothing(character, newItem:getBodyLocation(), newItem) end
        if syncVisuals then syncVisuals(character) end
        character:resetModelNextFrame()
    end)
    if not ok then return item end
    return newItem
end

---Handle equipping or unequipping prosthetics (runs on the client that owns the character)."""),
("""function ISWearClothing:complete()
    local result = og_ISWearClothing_complete(self)
    if result then
        ProsthesisHandler.SearchAndSetupProsthesis(self.character, self.item, true)
    end
    return result
end""",
"""function ISWearClothing:complete()
    local result = og_ISWearClothing_complete(self)
    if result and ProsthesisHandler.CheckIfProst(self.item) then
        -- the variant modelled for this stump (foot / calf / thigh, hand / forearm)
        local fitted = ProsthesisHandler.FitToStump(self.character, self.item)
        self.item = fitted
        ProsthesisHandler.SearchAndSetupProsthesis(self.character, fitted, true)
    end
    return result
end"""),
("""function ISClothingExtraAction:complete()
    local extraItem = instanceItem(self.extra)""",
"""function ISClothingExtraAction:complete()
    if ProsthesisHandler.CheckIfProst(self.item) then
        -- vanilla creates the other-side item from self.extra: ask for the variant of that stump directly
        self.extra = ProsthesisHandler.GetFittedType(self.character:getUsername(), self.extra)
    end
    local extraItem = instanceItem(self.extra)"""),
])
print("lua ok")
