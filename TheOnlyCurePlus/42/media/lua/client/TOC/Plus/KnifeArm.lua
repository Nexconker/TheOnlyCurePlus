local StaticData = require("TOC/StaticData")
local Messages = require("TOC/Plus/Messages")
------------------

-- TOC+ 3.2.0: Merle-style bayonet arm. While Prost_KnifeArm_R is worn the right hand holds TOC.MountedBlade, a
-- one-handed knife with an invisible model: the blade you see is part of the prosthesis (rigid on the forearm, in
-- line with it), so the left hand stays free. Same pattern as TOC/Plus/ChainsawArm, without engine or fuel: the blade
-- never breaks, the arm wears out with use.

---@class KnifeArm
local KnifeArm = {}

KnifeArm.WEAPON = "TOC.MountedBlade"
KnifeArm.BASE = "Prost_KnifeArm"
KnifeArm.SWINGS_PER_CONDITION = 50

local states = {}

---@param player IsoPlayer
local function State(player)
    local key = player:getPlayerNum()
    local st = states[key]
    if not st then
        st = { nextEquip = 0, ticks = 0 }
        states[key] = st
    end
    return st
end

local function IsLocal(player)
    return player ~= nil and instanceof(player, "IsoPlayer") and player:isLocalPlayer()
end

---Worn bayonet arm, or nil
---@param player IsoPlayer
---@return InventoryItem?
function KnifeArm.GetArm(player)
    if not player then return nil end
    local worn = player:getWornItems()
    if not worn then return nil end
    for i = 0, worn:size() - 1 do
        local item = worn:get(i):getItem()
        if item and StaticData.GetProsthesisBase(item:getFullType()) == KnifeArm.BASE then return item end
    end
    return nil
end

---@param item InventoryItem?
function KnifeArm.IsBlade(item)
    return item ~= nil and item:getFullType() == KnifeArm.WEAPON
end

local function FindBlade(player)
    return player:getInventory():getFirstTypeRecurse(KnifeArm.WEAPON)
end

---Remove every mounted blade the player carries (the arm came off, broke or was never worn)
local function RemoveBlades(player)
    for _ = 1, 5 do
        local blade = FindBlade(player)
        if not blade then return end
        player:removeFromHands(blade)
        local cont = blade:getContainer()
        if cont then
            cont:Remove(blade)
            if sendRemoveItemFromContainer then sendRemoveItemFromContainer(cont, blade) end
        end
    end
end

---Keep the blade in the right hand while the arm is worn; take it away when it is not
---@param player IsoPlayer
function KnifeArm.Enforce(player)
    local st = State(player)
    if not KnifeArm.GetArm(player) then
        if FindBlade(player) then RemoveBlades(player) end
        return
    end
    if player:isDead() or player:isAsleep() then return end
    local blade = FindBlade(player)
    if not blade then
        local inv = player:getInventory()
        blade = inv:AddItem(KnifeArm.WEAPON)
        if not blade then return end
        if sendAddItemToContainer then sendAddItemToContainer(inv, blade) end
    end
    if player:getPrimaryHandItem() == blade then return end
    -- re-attach with the vanilla equip action (syncs in multiplayer) when the hands are not busy
    local now = getTimestampMs()
    if now < st.nextEquip or player:isAiming() or ISTimedActionQueue.isPlayerDoingAction(player) then return end
    st.nextEquip = now + 3000
    if blade:getContainer() ~= player:getInventory() then
        ISTimedActionQueue.add(ISInventoryTransferAction:new(player, blade, blade:getContainer(), player:getInventory(), 1))
    end
    ISTimedActionQueue.add(ISEquipWeaponAction:new(player, blade, 10, true, false))
end

-------------------------
--* Events *--

local function OnPlayerUpdate(player)
    if not IsLocal(player) then return end
    local st = State(player)
    st.ticks = st.ticks + 1
    if st.ticks % 20 ~= 0 then return end
    local ok, err = pcall(KnifeArm.Enforce, player)
    if not ok then print("[TOC+] KnifeArm.Enforce: " .. tostring(err)) end
end

---Wear of the arm from use: one condition point every SWINGS_PER_CONDITION swings
local function AddSwingWear(player, arm)
    local md = arm:getModData()
    md.TOC_BladeWear = (tonumber(md.TOC_BladeWear) or 0) + 1
    if md.TOC_BladeWear < KnifeArm.SWINGS_PER_CONDITION then return end
    md.TOC_BladeWear = 0
    local cond = arm:getCondition() - 1
    arm:setCondition(math.max(0, cond))
    if isClient() then pcall(function() arm:syncItemFields() end) end
    if cond <= 0 then
        local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
        player:removeWornItem(arm)
        ProsthesisHandler.SearchAndSetupProsthesis(player, arm, false)
        player:resetModelNextFrame()
        Messages.Say(player, getText("IGUI_TOC_ProsthesisBroke"), true)
    elseif cond <= 3 then
        Messages.Say(player, getText("IGUI_TOC_ProsthesisWorn"), true)
    end
end

local function OnWeaponSwing(character, weapon)
    if not IsLocal(character) or not KnifeArm.IsBlade(weapon) then return end
    local arm = KnifeArm.GetArm(character)
    if not arm then return end
    pcall(function() weapon:setCondition(weapon:getConditionMax()) end)
    AddSwingWear(character, arm)
end

---Something else went into the right hand (hotbar, context menu): it moves to the left hand if that is free and
---it fits in one hand, and the blade comes back
local function OnEquipPrimary(player, item)
    if not IsLocal(player) or item == nil or KnifeArm.IsBlade(item) then return end
    if not KnifeArm.GetArm(player) then return end
    local blade = FindBlade(player)
    if not blade then return end
    local twoHanded = item:isRequiresEquippedBothHands() or (instanceof(item, "HandWeapon") and item:isTwoHandWeapon())
    Messages.Say(player, getText("IGUI_TOC_BladeArmBusy"), false)
    ISTimedActionQueue.add(ISEquipWeaponAction:new(player, blade, 10, true, false))
    if not twoHanded and player:getSecondaryHandItem() ~= item then
        local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
        if CachedDataHandler.GetHandFeasibility("L", player:getUsername()) then
            ISTimedActionQueue.add(ISEquipWeaponAction:new(player, item, 20, false, false))
        end
    end
    State(player).nextEquip = getTimestampMs() + 3000
end

local function OnCreatePlayer(playerNum, player)
    states[playerNum] = nil
end

-------------------------
--* The blade is part of the arm: it cannot be put away or dropped *--

local og_ISInventoryTransferAction_isValid = ISInventoryTransferAction.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISInventoryTransferAction:isValid()
    if KnifeArm.IsBlade(self.item) and self.character and self.destContainer ~= self.character:getInventory() then return false end
    return og_ISInventoryTransferAction_isValid(self)
end

if ISDropWorldItemAction then
    local og_ISDropWorldItemAction_isValid = ISDropWorldItemAction.isValid
    ---@diagnostic disable-next-line: duplicate-set-field
    function ISDropWorldItemAction:isValid()
        if KnifeArm.IsBlade(self.item) then return false end
        return og_ISDropWorldItemAction_isValid(self)
    end
end

Events.OnPlayerUpdate.Add(OnPlayerUpdate)
Events.OnWeaponSwing.Add(function(character, weapon) pcall(OnWeaponSwing, character, weapon) end)
Events.OnEquipPrimary.Add(function(player, item) pcall(OnEquipPrimary, player, item) end)
Events.OnCreatePlayer.Add(OnCreatePlayer)

return KnifeArm
