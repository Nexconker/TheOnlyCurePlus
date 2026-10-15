local StaticData = require("TOC/StaticData")
local CommonMethods = require("TOC/CommonMethods")
local CommandsData = require("TOC/CommandsData")
---------------------------

--- Spawns / removes the stump clothing items and handles what falls off with the limb.
---@class ItemsController
local ItemsController = {}

--* Player Methods *--
---@class ItemsController.Player
ItemsController.Player = {}

---Index into the stump item's textureChoices (0-based): 0-4 skin tones bloody, 5-9 hairy bloody,
---10-14 healed, 15-19 hairy healed, 20-31 zombie.
---@param playerObj IsoPlayer
---@param isCicatrized boolean
---@return number
function ItemsController.Player.GetAmputationTexturesIndex(playerObj, isCicatrized, limbName)
    local textureString = playerObj:getHumanVisual():getSkinTexture() or "MaleBody01"
    local isHairy = textureString:sub(-1) == "a"
    local matchedIndex = tonumber(textureString:match("%d%d")) or 1
    if matchedIndex < 1 or matchedIndex > 5 then matchedIndex = 1 end
    -- el cuerpo femenino tiene su propio mapeado, así que sus texturas van aparte (índices 20..29: 5 sangrantes +
    -- 5 cicatrizadas). Desde 3.1.0 también en los brazos: sus muñones son copias del cuerpo como los de pierna.
    local isFemaleBody = string.find(textureString, "Female") ~= nil
    if isFemaleBody then
        return 20 + (matchedIndex - 1) + (isCicatrized and 5 or 0)
    end
    if isHairy then matchedIndex = matchedIndex + 5 end
    if isCicatrized then matchedIndex = matchedIndex + 10 end
    return matchedIndex - 1
end

---@param playerObj IsoPlayer
---@param clothingItem InventoryItem
---@return boolean
function ItemsController.Player.RemoveClothingItem(playerObj, clothingItem)
    if clothingItem and instanceof(clothingItem, "InventoryItem") then
        playerObj:removeWornItem(clothingItem)
        playerObj:getInventory():Remove(clothingItem)
        if isServer() then pcall(function() sendRemoveItemFromContainer(playerObj:getInventory(), clothingItem) end) end
        playerObj:resetModelNextFrame()
        return true
    end
    return false
end

---Deletes an older stump item of the same side AND group (arm stumps never touch leg stumps)
---@param playerObj IsoPlayer
---@param limbName string
function ItemsController.Player.DeleteOldAmputationItem(playerObj, limbName)
    local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
    for _, othLimbName in ipairs(StaticData.AMP_GROUP_TO_LIMBS_MATCH_IND_STR[group] or {}) do
        local othClothingItem = playerObj:getInventory():FindAndReturn(StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. othLimbName)
        if ItemsController.Player.RemoveClothingItem(playerObj, othClothingItem) then return end
    end
end

---@param playerObj IsoPlayer
function ItemsController.Player.DeleteAllOldAmputationItems(playerObj)
    for i = 1, #StaticData.LIMBS_STR do
        local clothItem = playerObj:getInventory():FindAndReturn(StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. StaticData.LIMBS_STR[i])
        ItemsController.Player.RemoveClothingItem(playerObj, clothItem)
    end
end

---Spawns and equips the correct stump item.
---@param playerObj IsoPlayer
---@param limbName string
function ItemsController.Player.SpawnAmputationItem(playerObj, limbName)
    local itemName = StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. limbName
    local existing = playerObj:getInventory():FindAndReturn(itemName)
    if existing then
        ItemsController.Player.RemoveClothingItem(playerObj, existing)
    end
    local clothingItem = playerObj:getInventory():AddItem(itemName)
    if not clothingItem then
        TOC_DEBUG.print("Could not create stump item " .. itemName)
        return
    end
    local texId = ItemsController.Player.GetAmputationTexturesIndex(playerObj, false, limbName)
    pcall(function() clothingItem:getVisual():setTextureChoice(texId) end)
    if isServer() then
        pcall(function() sendAddItemToContainer(playerObj:getInventory(), clothingItem) end)
        sendServerCommand(playerObj, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveWearAmputation, {itemName = itemName, texId = texId})
    else
        local AmputationHandler = require("TOC/Handlers/AmputationHandler")
        AmputationHandler.WearAmputationItem(playerObj, itemName)
    end
end

---Drop worn items and unequip hands for the amputated limb
---@param playerObj IsoPlayer
---@param limbName string
function ItemsController.Player.DropItemsAfterAmputation(playerObj, limbName)
    if not playerObj or not limbName then return end
    local side = CommonMethods.GetSide(limbName)
    local sideStr = CommonMethods.GetSideFull(side)

    local wornItems = playerObj:getWornItems()
    local toRemove = {}
    for i = 1, wornItems:size() do
        local it = wornItems:get(i - 1)
        local wornItem = it and it:getItem()
        if wornItem then
            local bl = wornItem:getBodyLocation()
            local bls = bl and tostring(bl) or ""
            if string.contains(limbName, "Hand_") and (string.contains(bls, sideStr .. "_MiddleFinger") or string.contains(bls, sideStr .. "_RingFinger")) then
                table.insert(toRemove, wornItem)
            end
            if string.contains(limbName, "ForeArm_") and string.contains(bls, sideStr .. "Wrist") then
                table.insert(toRemove, wornItem)
            end
        end
    end
    for _, wi in ipairs(toRemove) do playerObj:removeWornItem(wi) end

    if StaticData.IsArmLimb(limbName) then
        if side == "R" then
            local primaryItem = playerObj:getPrimaryHandItem()
            if primaryItem then
                if primaryItem == playerObj:getSecondaryHandItem() then playerObj:setSecondaryHandItem(nil) end
                playerObj:setPrimaryHandItem(nil)
            end
        else
            local secondaryItem = playerObj:getSecondaryHandItem()
            if secondaryItem then
                if secondaryItem == playerObj:getPrimaryHandItem() then playerObj:setPrimaryHandItem(nil) end
                playerObj:setSecondaryHandItem(nil)
            end
        end
    end
    pcall(function() sendEquip(playerObj) end)
end

---Switch the stump texture between bloody and healed
---@param playerObj IsoPlayer
---@param limbName string
---@param isCicatrized boolean
function ItemsController.Player.OverrideAmputationItemVisuals(playerObj, limbName, isCicatrized)
    local fullType = StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. limbName
    local wornItems = playerObj:getWornItems()
    for i = 1, wornItems:size() do
        local it = wornItems:get(i - 1)
        local wornItem = it and it:getItem()
        if wornItem and wornItem:getFullType() == fullType then
            local texId = ItemsController.Player.GetAmputationTexturesIndex(playerObj, isCicatrized, limbName)
            pcall(function() wornItem:getVisual():setTextureChoice(texId) end)
            playerObj:resetModelNextFrame()
            if isServer() then pcall(function() sendVisual(playerObj) end) end
            return
        end
    end
end

--* Zombie Methods (delegated to the shared ZombieStumps) *--
---@class ItemsController.Zombie
ItemsController.Zombie = {}
local ZombieStumps = require("TOC/Handlers/ZombieStumps")
ItemsController.Zombie.SpawnAmputationItem = ZombieStumps.Spawn
ItemsController.Zombie.GetAmputationTexturesIndex = ZombieStumps.GetTextureIndex

Events.OnAmputatedLimb.Add(ItemsController.Player.DropItemsAfterAmputation)
Events.OnProsthesisUnequipped.Add(ItemsController.Player.DropItemsAfterAmputation)

return ItemsController
