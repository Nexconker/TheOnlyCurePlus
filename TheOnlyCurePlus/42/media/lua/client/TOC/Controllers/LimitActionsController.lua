local DataController = require("TOC/Controllers/DataController")
local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
local StaticData = require("TOC/StaticData")
local OverridenMethodsArchive = require("TOC/OverridenMethodsArchive")
local Messages = require("TOC/Plus/Messages")
-----------------

---@class LimitActionsController
local LimitActionsController = {}

local function HandFeasible(side, player)
    player = player or getPlayer()
    if not player then return true end
    return CachedDataHandler.GetHandFeasibility(side, player:getUsername())
end

---A hook-like prosthesis on either hand?
---@param player IsoPlayer
---@return boolean
---@return boolean, string? clave del mensaje (gancho de verdad, o base modular sin cabezal)
local function HasHookLike(player)
    local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
    for _, side in ipairs(StaticData.SIDES_STR) do
        local tier = ProsthesisHandler.GetEquippedTier(player:getUsername(), "Top_" .. side)
        if tier and tier.hookLike then
            -- 3.3: una base sin cabezal no es un gancho, es que no hay nada con qué sujetar
            if tier.modular and not tier.head then return true, "IGUI_TOC_NoHeadCantHold" end
            return true, "IGUI_TOC_HookCantHold"
        end
    end
    return false
end

---@param item InventoryItem
---@return boolean
local function NeedsBothHands(item)
    if not item then return false end
    local ok, res = pcall(function()
        if item.isRequiresEquippedBothHands and item:isRequiresEquippedBothHands() then return true end
        if instanceof(item, "HandWeapon") and item:isTwoHandWeapon() then return true end
        return false
    end)
    return ok and res == true
end

--* DISABLE WEARING CERTAIN ITEMS WHEN NO LIMB

function LimitActionsController.CheckLimbFeasibility(limbName)
    local dcInst = DataController.GetReady(getPlayer():getUsername())
    if not dcInst or not limbName then return true end
    return (not dcInst:getIsCut(limbName)) or dcInst:getIsProstEquipped(limbName)
end

function LimitActionsController.WrapClothingAction(obj, wrappedFunc, item)
    local isEquippable = wrappedFunc(obj)
    if not isEquippable or not item then return isEquippable end
    local itemBodyLoc = item:getBodyLocation()
    local limbToCheck = StaticData.GetAffectedLimb(itemBodyLoc)            -- antes se buscaba con el objeto y nunca coincidía
    if limbToCheck and not LimitActionsController.CheckLimbFeasibility(limbToCheck) then return false end
    return isEquippable
end

local og_MainOptions_apply = MainOptions.apply
---@diagnostic disable-next-line: duplicate-set-field
function MainOptions:apply(closeAfter)
    og_MainOptions_apply(self, closeAfter)
    pcall(CachedDataHandler.OverrideInteractionsKey)
end

--* EQUIPPING ITEMS *--

local og_ISEquipWeaponAction_isValid = ISEquipWeaponAction.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISEquipWeaponAction:isValid()
    local isValid = og_ISEquipWeaponAction_isValid(self)
    if not isValid or not self.character then return isValid end
    local username = self.character:getUsername()
    local primaryOk = CachedDataHandler.GetHandFeasibility("R", username)
    local secondaryOk = CachedDataHandler.GetHandFeasibility("L", username)
    if not primaryOk and not secondaryOk then return false end
    if NeedsBothHands(self.item) or self.twoHands then
        if not (primaryOk and secondaryOk) then
            Messages.Say(self.character, getText("IGUI_TOC_NeedBothHands"), true)
            return false
        end
        local hooked, why = HasHookLike(self.character)
        if hooked then
            Messages.Say(self.character, getText(why or "IGUI_TOC_HookCantHold"), true)
            return false
        end
    end
    return true
end

---Equip with amputations in mind: a one-handed item goes to the hand that exists
function ISEquipWeaponAction:performWithAmputation()
    local hand, otherHand, getFirst, setFirst, getSecond, setSecond
    if self.primary then
        hand, otherHand = "R", "L"
        getFirst, setFirst = self.character.getSecondaryHandItem, self.character.setSecondaryHandItem
        getSecond, setSecond = self.character.getPrimaryHandItem, self.character.setPrimaryHandItem
    else
        hand, otherHand = "L", "R"
        getFirst, setFirst = self.character.getPrimaryHandItem, self.character.setPrimaryHandItem
        getSecond, setSecond = self.character.getSecondaryHandItem, self.character.setSecondaryHandItem
    end
    local isFirstValid = HandFeasible(hand, self.character)
    local isSecondValid = HandFeasible(otherHand, self.character)

    if not self.twoHands then
        if getFirst(self.character) and getFirst(self.character):isRequiresEquippedBothHands() then
            setFirst(self.character, nil)
        elseif (getFirst(self.character) == self.item or getFirst(self.character) == getSecond(self.character)) then
            setFirst(self.character, nil)
        elseif instanceof(self.item, "HandWeapon") and self.item:getSwingAnim() and self.item:getSwingAnim() == "Handgun" then
            if getFirst(self.character) and instanceof(getFirst(self.character), "HandWeapon") then
                setFirst(self.character, nil)
            end
        else
            setSecond(self.character, nil)
            if isFirstValid then
                setSecond(self.character, self.item)
            elseif isSecondValid then
                setFirst(self.character, self.item)
            end
        end
    else
        setFirst(self.character, nil)
        setSecond(self.character, nil)
        if isFirstValid then setSecond(self.character, self.item) end
        if isSecondValid then setFirst(self.character, self.item) end
    end
end

local og_ISEquipWeaponAction_perform = ISEquipWeaponAction.perform
---@diagnostic disable-next-line: duplicate-set-field
function ISEquipWeaponAction:perform()
    og_ISEquipWeaponAction_perform(self)
    local dcInst = DataController.GetReady(self.character:getUsername())
    if dcInst and dcInst:getIsAnyLimbCut() then
        pcall(self.performWithAmputation, self)
    end
end

--* Equip guard: whatever path put an item in a missing hand (hotbar, belt, keybind), move it *--

---@param player IsoPlayer
---@param item InventoryItem
---@param primary boolean
local function GuardEquip(player, item, primary)
    -- other mods fire this event for NPCs too (Bandits: its bandits are IsoZombie, without isLocalPlayer)
    if not player or not item or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
    local dcInst = DataController.GetReady(player:getUsername())
    if not dcInst or not dcInst:getIsAnyLimbCut() then return end
    local side = primary and "R" or "L"
    local other = primary and "L" or "R"
    if HandFeasible(side, player) then return end
    local both = NeedsBothHands(item) or (player:getPrimaryHandItem() == item and player:getSecondaryHandItem() == item)
    if both or not HandFeasible(other, player) then
        player:setPrimaryHandItem(nil)
        player:setSecondaryHandItem(nil)
        Messages.Say(player, getText("IGUI_TOC_NoHandForThat"), true)
        return
    end
    -- move it to the other hand if free
    if primary then
        player:setPrimaryHandItem(nil)
        if player:getSecondaryHandItem() == nil then player:setSecondaryHandItem(item) end
    else
        player:setSecondaryHandItem(nil)
        if player:getPrimaryHandItem() == nil then player:setPrimaryHandItem(item) end
    end
end

Events.OnEquipPrimary.Add(function(player, item) pcall(GuardEquip, player, item, true) end)
Events.OnEquipSecondary.Add(function(player, item) pcall(GuardEquip, player, item, false) end)

--* Inventory context: grey out the equip option of the missing hand (wrap, do not replace the vanilla function)

local og_doEquipOption = ISInventoryPaneContextMenu.doEquipOption
function ISInventoryPaneContextMenu.doEquipOption(context, playerObj, isWeapon, items, player)
    og_doEquipOption(context, playerObj, isWeapon, items, player)
    pcall(function()
        if not playerObj then return end
        local username = playerObj:getUsername()
        local dcInst = DataController.GetReady(username)
        if not dcInst or not dcInst:getIsAnyLimbCut() then return end
        local optP = context:getOptionFromName(getText("ContextMenu_Equip_Primary"))
        if optP and not CachedDataHandler.GetHandFeasibility("R", username) then optP.notAvailable = true end
        local optS = context:getOptionFromName(getText("ContextMenu_Equip_Secondary"))
        if optS and not CachedDataHandler.GetHandFeasibility("L", username) then optS.notAvailable = true end
        if NeedsBothHands(isWeapon) then
            local optB = context:getOptionFromName(getText("ContextMenu_Equip_Two_Hands"))
            if optB and (not CachedDataHandler.GetHandFeasibilityBoth(username) or HasHookLike(playerObj)) then optB.notAvailable = true end
        end
    end)
end

local noHandsImpossibleActions = {
    "ContextMenu_Add_escape_rope_sheet", "ContextMenu_Add_escape_rope", "ContextMenu_Remove_escape_rope",
    "ContextMenu_Barricade", "ContextMenu_Unbarricade", "ContextMenu_MetalBarricade", "ContextMenu_MetalBarBarricade",
    "ContextMenu_Open_window", "ContextMenu_Close_window", "ContextMenu_PickupBrokenGlass", "ContextMenu_Open_door", "ContextMenu_Close_door",
}

local og_ISWorldObjectContextMenu_createMenu = ISWorldObjectContextMenu.createMenu
function ISWorldObjectContextMenu.createMenu(player, worldobjects, x, y, test)
    local ogContext = og_ISWorldObjectContextMenu_createMenu(player, worldobjects, x, y, test)
    if type(ogContext) ~= "table" then return ogContext end
    pcall(function()
        local playerObj = getSpecificPlayer(player)
        if not playerObj then return end
        local username = playerObj:getUsername()
        local dcInst = DataController.GetReady(username)
        if not dcInst or not dcInst:getIsAnyLimbCut() then return end

        local brokenGlassOption = ogContext:getOptionFromName(getText("ContextMenu_RemoveBrokenGlass"))
        if brokenGlassOption then
            if (CachedDataHandler.GetHandFeasibility("R", username) and playerObj:getPrimaryHandItem()) or
                (CachedDataHandler.GetHandFeasibility("L", username) and playerObj:getSecondaryHandItem()) then
                brokenGlassOption.notAvailable = false
                brokenGlassOption.toolTip = nil
            end
        end
        if not CachedDataHandler.GetBothHandsFeasibility(username) then
            for i = 1, #noHandsImpossibleActions do
                local option = ogContext:getOptionFromName(getText(noHandsImpossibleActions[i]))
                if option then option.notAvailable = true end
            end
        end
    end)
    return ogContext
end

local og_ISWearClothing_isValid = ISWearClothing.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:isValid()
    return LimitActionsController.WrapClothingAction(self, og_ISWearClothing_isValid, self.item)
end

local og_ISClothingExtraAction_isValid = OverridenMethodsArchive.Save("ISClothingExtraAction_isValid", ISClothingExtraAction.isValid)
---@diagnostic disable-next-line: duplicate-set-field
function ISClothingExtraAction:isValid()
    return LimitActionsController.WrapClothingAction(self, og_ISClothingExtraAction_isValid, instanceItem(self.extra))
end

--* Book exception for exp
local og_ISReadABook_perform = ISReadABook.perform
function ISReadABook:perform()
    self.noExp = true
    og_ISReadABook_perform(self)
end

return LimitActionsController
