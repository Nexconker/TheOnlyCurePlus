local CommandsData = require("TOC/CommandsData")
local CommonMethods = require("TOC/CommonMethods")
local StaticData = require("TOC/StaticData")
local DataController = require("TOC/Controllers/DataController")
local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
local OverridenMethodsArchive = require("TOC/OverridenMethodsArchive")
-------------------------

LuaEventManager.AddEvent("OnProsthesisUnequipped")  -- args: playerObj, limbName
LuaEventManager.AddEvent("OnProsthesisEquipped")    -- args: playerObj, group, fullType

---@class ProsthesisHandler
local ProsthesisHandler = {}

local ARM_PREFIX = "toc:armprost_"
local LEG_PREFIX = "toc:legprost_"

---@param item InventoryItem?
---@return boolean
function ProsthesisHandler.CheckIfProst(item)
    if item == nil or item:getBodyLocation() == nil then return false end
    local bl = string.lower(item:getBodyLocation():toString())
    return string.contains(bl, ARM_PREFIX) or string.contains(bl, LEG_PREFIX)
end

---@param item InventoryItem
---@return string? group Top_L / Bottom_R ...
function ProsthesisHandler.GetGroup(item)
    local fullType = item:getFullType()
    local side = CommonMethods.GetSide(fullType)
    local bl = string.lower(item:getBodyLocation():toString())
    local position
    if string.contains(bl, ARM_PREFIX) then position = "Top_" elseif string.contains(bl, LEG_PREFIX) then position = "Bottom_" else return nil end
    return StaticData.AMP_GROUPS_IND_STR[position .. side]
end

---Tier data for an item type
---@param fullType string
---@return table?
function ProsthesisHandler.GetTier(fullType)
    return StaticData.GetProsthesisTier(fullType)
end

---Can the LOCAL player wear this prosthesis? Needs an amputation on that side, in that group,
---and not the highest part of the group (upper arm / upper leg: nothing to strap it to).
---@param fullType string
---@param player IsoPlayer?
---@return boolean
function ProsthesisHandler.CheckIfEquippable(fullType, player)
    player = player or getPlayer()
    if not player then return false end
    local side = CommonMethods.GetSide(fullType)
    local tier = ProsthesisHandler.GetTier(fullType)
    if not tier then return false end
    local highest = CachedDataHandler.GetHighestAmputatedLimbs(player:getUsername())
    if not highest then return false end
    local hal = highest[tier.group .. "_" .. side]
    if not hal then return false end
    local part = string.match(hal, "^(%a+)_")
    if StaticData.NO_PROSTHESIS_PARTS_IND_STR[part] then return false end
    return true
end

---Type of the variant modelled for the stump the LOCAL/given player has on that side.
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

---Handle equipping or unequipping prosthetics (runs on the client that owns the character).
---@param character IsoPlayer
---@param item InventoryItem
---@param isEquipping boolean
---@return boolean
function ProsthesisHandler.SearchAndSetupProsthesis(character, item, isEquipping)
    if not ProsthesisHandler.CheckIfProst(item) then return false end
    local username = character:getUsername()
    local group = ProsthesisHandler.GetGroup(item)
    if not group then return false end
    local dcInst = DataController.GetReady(username)
    if not dcInst then return false end

    local fullType = item:getFullType()
    dcInst:setIsProstEquipped(group, isEquipping)
    dcInst:setProstType(group, isEquipping and fullType or nil)

    if isClient() and character:isLocalPlayer() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayProsthesisState,
            {group = group, isEquipped = isEquipping, prostType = isEquipping and fullType or nil})
    end
    dcInst:apply(character)
    if not isClient() then
        CachedDataHandler.CalculateCacheableValues(username)
    end
    if isEquipping then triggerEvent("OnProsthesisEquipped", character, group, fullType) end
    return true
end

---Equipped prosthesis tier for a group (or nil)
---@param username string
---@param group string
---@return table? tier, string? fullType
function ProsthesisHandler.GetEquippedTier(username, group)
    local dcInst = DataController.GetReady(username)
    if not dcInst then return nil end
    local t = dcInst:getProstType(group)
    if not t then
        -- legacy data without prostType: assume the classic arm
        if dcInst:getIsProstEquippedGroup(group) then
            return StaticData.PROSTHESIS_TIERS.Prost_NormalArm, nil
        end
        return nil
    end
    return StaticData.GetProsthesisTier(t), t
end

---Find the worn prosthesis item for a group
---@param character IsoPlayer
---@param group string
---@return InventoryItem?
function ProsthesisHandler.FindWornProsthesis(character, group)
    local worn = character:getWornItems()
    if not worn then return nil end
    for i = 1, worn:size() do
        local it = worn:get(i - 1)
        local item = it and it:getItem()
        if item and ProsthesisHandler.CheckIfProst(item) and ProsthesisHandler.GetGroup(item) == group then
            return item
        end
    end
    return nil
end

---Wear: one point per timed action, scaled by tier. Breaks the prosthesis at condition 0.
---LOCAL PLAYER ONLY (item condition is owned by the client that wears it; synced with syncItemFields).
---@param character IsoPlayer
function ProsthesisHandler.AddWearForAction(character)
    if isServer() then return end
    if isClient() and not character:isLocalPlayer() then return end
    if not (SandboxVars.TOC and SandboxVars.TOC.ProsthesisWear ~= false) then return end
    local username = character:getUsername()
    local dcInst = DataController.GetReady(username)
    if not dcInst then return end
    for i = 1, #StaticData.AMP_GROUPS_STR do
        local group = StaticData.AMP_GROUPS_STR[i]
        if dcInst:getIsProstEquippedGroup(group) then
            local tier = ProsthesisHandler.GetEquippedTier(username, group)
            local per = tier and tier.wearPerAction or 0.5
            local wear = dcInst:getProstWear(group) + per
            if wear >= StaticData.PROSTHESIS_WEAR_PER_CONDITION then
                wear = wear - StaticData.PROSTHESIS_WEAR_PER_CONDITION
                local item = ProsthesisHandler.FindWornProsthesis(character, group)
                if item then
                    local cond = item:getCondition() - 1
                    item:setCondition(math.max(0, cond))
                    if isClient() then pcall(function() item:syncItemFields() end) end
                    if cond <= 0 then
                        -- broken: falls off
                        character:removeWornItem(item)
                        ProsthesisHandler.SearchAndSetupProsthesis(character, item, false)
                        character:resetModelNextFrame()
                        local Messages = require("TOC/Plus/Messages")
                        Messages.Say(character, getText("IGUI_TOC_ProsthesisBroke"), true)
                    elseif cond <= 3 then
                        local Messages = require("TOC/Plus/Messages")
                        Messages.Say(character, getText("IGUI_TOC_ProsthesisWorn"), true)
                    end
                end
            end
            dcInst:setProstWear(group, wear)
            if isClient() and ZombRand(10) == 0 then
                sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayProsthesisWear, {group = group, wear = wear})
            end
        end
    end
end

---@param item InventoryItem
---@param isEquippable boolean
---@return boolean
function ProsthesisHandler.Validate(item, isEquippable)
    if not ProsthesisHandler.CheckIfProst(item) then return isEquippable end
    if not isEquippable then return false end
    local ok = ProsthesisHandler.CheckIfEquippable(item:getFullType())
    if not ok then
        local Messages = require("TOC/Plus/Messages")
        Messages.Say(getPlayer(), getText("UI_Say_CantEquip"), false)
    end
    return ok
end

-------------------------
--* Overrides *--

local og_ISWearClothing_isValid = ISWearClothing.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:isValid()
    local isEquippable = og_ISWearClothing_isValid(self)
    return ProsthesisHandler.Validate(self.item, isEquippable)
end

local og_ISWearClothing_complete = ISWearClothing.complete
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:complete()
    local result = og_ISWearClothing_complete(self)
    if result and ProsthesisHandler.CheckIfProst(self.item) then
        -- the variant modelled for this stump (foot / calf / thigh, hand / forearm)
        local fitted = ProsthesisHandler.FitToStump(self.character, self.item)
        self.item = fitted
        ProsthesisHandler.SearchAndSetupProsthesis(self.character, fitted, true)
    end
    return result
end

local og_ISClothingExtraAction_isValid = OverridenMethodsArchive.Save("ISClothingExtraAction_isValid", ISClothingExtraAction.isValid)
---@diagnostic disable-next-line: duplicate-set-field
function ISClothingExtraAction:isValid()
    local isEquippable = og_ISClothingExtraAction_isValid(self)
    local testItem = instanceItem(self.extra)
    return ProsthesisHandler.Validate(testItem, isEquippable)
end

local og_ISClothingExtraAction_complete = OverridenMethodsArchive.Save("ISClothingExtraAction_complete", ISClothingExtraAction.complete)
---@diagnostic disable-next-line: duplicate-set-field
function ISClothingExtraAction:complete()
    if ProsthesisHandler.CheckIfProst(self.item) then
        -- vanilla creates the other-side item from self.extra: ask for the variant of that stump directly
        self.extra = ProsthesisHandler.GetFittedType(self.character:getUsername(), self.extra)
    end
    local extraItem = instanceItem(self.extra)
    -- the old side is unequipped by the swap, but ONLY if this very item was being worn: converting a
    -- spare prosthesis from the inventory must not clear the state of the one on the other leg/arm
    if ProsthesisHandler.CheckIfProst(self.item) then
        local wornHere = false
        pcall(function() wornHere = self.character:getWornItem(self.item:getBodyLocation()) == self.item end)
        if wornHere then
            ProsthesisHandler.SearchAndSetupProsthesis(self.character, self.item, false)
        end
    end
    ProsthesisHandler.SearchAndSetupProsthesis(self.character, extraItem, true)
    return og_ISClothingExtraAction_complete(self)
end

local og_ISUnequipAction_complete = ISUnequipAction.complete
---@diagnostic disable-next-line: duplicate-set-field
function ISUnequipAction:complete()
    local isProst = ProsthesisHandler.SearchAndSetupProsthesis(self.character, self.item, false)
    local result = og_ISUnequipAction_complete(self)
    if isProst then
        local group = ProsthesisHandler.GetGroup(self.item)
        local highest = CachedDataHandler.GetHighestAmputatedLimbs(self.character:getUsername())
        if group and highest and highest[group] then
            triggerEvent("OnProsthesisUnequipped", self.character, highest[group])
        end
    end
    return result
end

return ProsthesisHandler
