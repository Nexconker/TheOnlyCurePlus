local StaticData = require("TOC/StaticData")
local CommandsData = require("TOC/CommandsData")
local Messages = require("TOC/Plus/Messages")
------------------

-- TOC+: Ash-style chainsaw arm. While Prost_ChainsawArm_R is worn the right hand holds TOC.MountedChainsaw, a
-- one-handed weapon with an invisible model: the saw you see is part of the prosthesis (rigid on the forearm, bar in
-- line with it), so the left hand stays free. The engine is started with the pull cord, burns petrol from the arm's
-- own tank (mod data of the prosthesis item) and is loud; with the engine off the saw is only a heavy club.

---@class ChainsawArm
local ChainsawArm = {}

ChainsawArm.WEAPON = "TOC.MountedChainsaw"
ChainsawArm.BASE = "Prost_ChainsawArm"
ChainsawArm.TANK = 0.5              -- litres
ChainsawArm.IDLE_DRAIN = 0.004      -- litres per game minute while running: a full tank idles about two game hours
ChainsawArm.SWING_DRAIN = 0.002     -- litres per swing while running
ChainsawArm.IDLE_NOISE = 20         -- tiles, renewed every game minute while running
ChainsawArm.SWING_NOISE = 35        -- tiles, every swing while running
ChainsawArm.SWINGS_PER_CONDITION = 60

-- Running = the item script. Off = a heavy club (the vanilla engine maul sounds).
local STATS = {
    on  = { min = 2.2, max = 3.4, crit = 30, hits = 3, door = 40, tree = 60, swing = "TOC_ChainsawRev", hit = "TOC_ChainsawCut" },
    off = { min = 0.6, max = 1.2, crit = 5,  hits = 1, door = 8,  tree = 5,  swing = "EngineMaulSwing", hit = "EngineMaulHit" },
}

local states = {}

---@param player IsoPlayer
local function State(player)
    local key = player:getPlayerNum()
    local st = states[key]
    if not st then
        st = { running = false, sound = nil, loopAt = 0, nextEquip = 0, ticks = 0, minutes = 0, applied = nil }
        states[key] = st
    end
    return st
end

local function IsLocal(player)
    return player ~= nil and instanceof(player, "IsoPlayer") and player:isLocalPlayer()
end

---Worn chainsaw arm, or nil
---@param player IsoPlayer
---@return InventoryItem?
function ChainsawArm.GetArm(player)
    if not player then return nil end
    local worn = player:getWornItems()
    if not worn then return nil end
    for i = 0, worn:size() - 1 do
        local item = worn:get(i):getItem()
        if item and StaticData.GetProsthesisBase(item:getFullType()) == ChainsawArm.BASE then return item end
    end
    return nil
end

---@param item InventoryItem?
function ChainsawArm.IsSaw(item)
    return item ~= nil and item:getFullType() == ChainsawArm.WEAPON
end

---@param arm InventoryItem?
---@return number litres
function ChainsawArm.GetFuel(arm)
    if not arm then return 0 end
    return tonumber(arm:getModData().TOC_SawFuel) or 0
end

local function FuelText(arm)
    return tostring(math.floor(ChainsawArm.GetFuel(arm) / ChainsawArm.TANK * 100 + 0.5)) .. "%"
end

local function SyncFuel(arm)
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_ITEMS, "SetSawFuel", {itemId = arm:getID(), fuel = ChainsawArm.GetFuel(arm)})
    end
end

local function SetFuel(arm, litres, sync)
    arm:getModData().TOC_SawFuel = math.max(0, math.min(ChainsawArm.TANK, litres))
    if sync then SyncFuel(arm) end
end

---@param player IsoPlayer
function ChainsawArm.IsRunning(player)
    if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return false end
    return State(player).running
end

local function FindSaw(player)
    return player:getInventory():getFirstTypeRecurse(ChainsawArm.WEAPON)
end

local function ApplyStats(player, saw, running)
    local st = State(player)
    if st.applied == saw and st.appliedRunning == running then return end
    local s = running and STATS.on or STATS.off
    saw:setMinDamage(s.min); saw:setMaxDamage(s.max)
    saw:setCriticalChance(s.crit); saw:setMaxHitCount(s.hits)
    saw:setDoorDamage(s.door); saw:setTreeDamage(s.tree)
    saw:setSwingSound(s.swing); saw:setZombieHitSound(s.hit)
    saw:setDoorHitSound(s.hit); saw:setHitFloorSound(s.hit)
    st.applied, st.appliedRunning = saw, running
end

local function UpdateName(saw, arm, running)
    local base = getScriptManager():FindItem(ChainsawArm.WEAPON)
    local name = base and base:getDisplayName() or "Chainsaw"
    saw:setName(name .. " (" .. FuelText(arm) .. (running and ", ON" or "") .. ")")
end

---Remove every mounted saw the player carries (the arm came off, broke or was never worn)
local function RemoveSaws(player)
    for _ = 1, 5 do
        local saw = FindSaw(player)
        if not saw then return end
        player:removeFromHands(saw)
        local cont = saw:getContainer()
        if cont then
            cont:Remove(saw)
            if sendRemoveItemFromContainer then sendRemoveItemFromContainer(cont, saw) end
        end
    end
end

local function StopLoop(player, st)
    if st.sound then
        pcall(function() player:stopOrTriggerSound(st.sound) end)
        st.sound = nil
    end
end

local function StartLoop(player, st)
    if st.sound then
        local playing = false
        pcall(function() playing = player:getEmitter():isPlaying(st.sound) end)
        if playing then return end
    end
    st.sound = player:playSound("TOC_ChainsawIdle")
end

---Start or stop the engine (the start sound is played by the start action; the idle loop begins after it)
---@param player IsoPlayer
---@param running boolean
---@param loopDelayMs number?
function ChainsawArm.SetRunning(player, running, loopDelayMs)
    local st = State(player)
    if st.running == running then return end
    st.running = running
    local arm = ChainsawArm.GetArm(player)
    local saw = FindSaw(player)
    if saw then ApplyStats(player, saw, running) end
    if running then
        st.loopAt = getTimestampMs() + (loopDelayMs or 0)
    else
        StopLoop(player, st)
        player:playSound("TOC_ChainsawStop")
    end
    if arm then
        SyncFuel(arm)
        if saw then UpdateName(saw, arm, running) end
    end
end

local function LeftHandFree(player)
    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    return CachedDataHandler.GetHandFeasibility("L", player:getUsername()) and player:getSecondaryHandItem() == nil
end

---Keep the saw in the right hand while the arm is worn; take it away when it is not
---@param player IsoPlayer
function ChainsawArm.Enforce(player)
    local st = State(player)
    local arm = ChainsawArm.GetArm(player)
    if not arm then
        if st.running then ChainsawArm.SetRunning(player, false) end
        if FindSaw(player) then RemoveSaws(player) end
        return
    end
    if player:isDead() or player:isAsleep() then
        if st.running then ChainsawArm.SetRunning(player, false) end
        return
    end
    local saw = FindSaw(player)
    if not saw then
        local inv = player:getInventory()
        saw = inv:AddItem(ChainsawArm.WEAPON)
        if not saw then return end
        if sendAddItemToContainer then sendAddItemToContainer(inv, saw) end
        UpdateName(saw, arm, st.running)
    end
    ApplyStats(player, saw, st.running)
    if player:getPrimaryHandItem() == saw then return end
    -- re-attach with the vanilla equip action (syncs in multiplayer) when the hands are not busy
    local now = getTimestampMs()
    if now < st.nextEquip or player:isAiming() or ISTimedActionQueue.isPlayerDoingAction(player) then return end
    st.nextEquip = now + 3000
    if saw:getContainer() ~= player:getInventory() then
        ISTimedActionQueue.add(ISInventoryTransferAction:new(player, saw, saw:getContainer(), player:getInventory(), 1))
    end
    ISTimedActionQueue.add(ISEquipWeaponAction:new(player, saw, 10, true, false))
end

-------------------------
--* Events *--

local function OnPlayerUpdate(player)
    if not IsLocal(player) then return end
    local st = State(player)
    st.ticks = st.ticks + 1
    if st.running and not st.sound and getTimestampMs() >= st.loopAt then StartLoop(player, st) end
    if st.ticks % 20 ~= 0 then return end
    local ok, err = pcall(ChainsawArm.Enforce, player)
    if not ok then print("[TOC+] ChainsawArm.Enforce: " .. tostring(err)) end
end

local function EveryOneMinute()
    for i = 0, getNumActivePlayers() - 1 do
        local player = getSpecificPlayer(i)
        if player and not player:isDead() then
            local st = State(player)
            if st.running then
                local arm = ChainsawArm.GetArm(player)
                if not arm then
                    ChainsawArm.SetRunning(player, false)
                else
                    SetFuel(arm, ChainsawArm.GetFuel(arm) - ChainsawArm.IDLE_DRAIN, false)
                    addSound(player, player:getX(), player:getY(), player:getZ(), ChainsawArm.IDLE_NOISE, ChainsawArm.IDLE_NOISE)
                    StartLoop(player, st)
                    st.minutes = st.minutes + 1
                    if st.minutes % 10 == 0 then SyncFuel(arm) end
                    local saw = FindSaw(player)
                    if saw then UpdateName(saw, arm, true) end
                    if ChainsawArm.GetFuel(arm) <= 0 then
                        ChainsawArm.SetRunning(player, false)
                        Messages.Say(player, getText("IGUI_TOC_SawStalled"), true)
                    end
                end
            end
        end
    end
end

---Wear of the arm from use: one condition point every SWINGS_PER_CONDITION swings with the engine running
local function AddSwingWear(player, arm)
    local md = arm:getModData()
    md.TOC_SawWear = (tonumber(md.TOC_SawWear) or 0) + 1
    if md.TOC_SawWear < ChainsawArm.SWINGS_PER_CONDITION then return end
    md.TOC_SawWear = 0
    local cond = arm:getCondition() - 1
    arm:setCondition(math.max(0, cond))
    if isClient() then pcall(function() arm:syncItemFields() end) end
    if cond <= 0 then
        local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
        player:removeWornItem(arm)
        ProsthesisHandler.SearchAndSetupProsthesis(player, arm, false)
        player:resetModelNextFrame()
        ChainsawArm.SetRunning(player, false)
        Messages.Say(player, getText("IGUI_TOC_ProsthesisBroke"), true)
    elseif cond <= 3 then
        Messages.Say(player, getText("IGUI_TOC_ProsthesisWorn"), true)
    end
end

local function OnWeaponSwing(character, weapon)
    if not IsLocal(character) or not ChainsawArm.IsSaw(weapon) then return end
    local st = State(character)
    if not st.running then return end
    local arm = ChainsawArm.GetArm(character)
    if not arm then return end
    SetFuel(arm, ChainsawArm.GetFuel(arm) - ChainsawArm.SWING_DRAIN, false)
    addSound(character, character:getX(), character:getY(), character:getZ(), ChainsawArm.SWING_NOISE, ChainsawArm.SWING_NOISE)
    pcall(function() weapon:setCondition(weapon:getConditionMax()) end)
    AddSwingWear(character, arm)
    if ChainsawArm.GetFuel(arm) <= 0 then
        ChainsawArm.SetRunning(character, false)
        Messages.Say(character, getText("IGUI_TOC_SawStalled"), true)
    end
end

---Something else went into the right hand (hotbar, context menu): it moves to the left hand if that is free and
---it fits in one hand, and the saw comes back
local function OnEquipPrimary(player, item)
    if not IsLocal(player) or item == nil or ChainsawArm.IsSaw(item) then return end
    if not ChainsawArm.GetArm(player) then return end
    local saw = FindSaw(player)
    if not saw then return end
    local twoHanded = item:isRequiresEquippedBothHands() or (instanceof(item, "HandWeapon") and item:isTwoHandWeapon())
    Messages.Say(player, getText("IGUI_TOC_SawArmBusy"), false)
    ISTimedActionQueue.add(ISEquipWeaponAction:new(player, saw, 10, true, false))
    if not twoHanded and player:getSecondaryHandItem() ~= item then
        local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
        if CachedDataHandler.GetHandFeasibility("L", player:getUsername()) then
            ISTimedActionQueue.add(ISEquipWeaponAction:new(player, item, 20, false, false))
        end
    end
    State(player).nextEquip = getTimestampMs() + 3000
end

local function OnCreatePlayer(playerNum, player)
    local st = states[playerNum]
    if st and player then StopLoop(player, st) end
    states[playerNum] = nil
end

-------------------------
--* Context menu *--

local function PetrolPredicate(item)
    local fc = item:getFluidContainer()
    return fc ~= nil and fc:contains(Fluid.Petrol) and fc:getAmount() >= 0.05
end

local function AddMenu(playerNum, context)
    local player = getSpecificPlayer(playerNum)
    if not player or player:isDead() then return end
    local arm = ChainsawArm.GetArm(player)
    if not arm then return end
    local st = State(player)
    local root = context:addOption(getText("ContextMenu_TOC_SawMenu", FuelText(arm)), nil, nil)
    local sub = ISContextMenu:getNew(context)
    context:addSubMenu(root, sub)
    local ChainsawActions = require("TOC/TimedActions/ChainsawActions")
    if st.running then
        sub:addOption(getText("ContextMenu_TOC_SawStop"), player, function(p) ChainsawArm.SetRunning(p, false) end)
    else
        local opt = sub:addOption(getText("ContextMenu_TOC_SawStart"), player, function(p)
            ISTimedActionQueue.add(ChainsawActions.Start:new(p))
        end)
        if ChainsawArm.GetFuel(arm) <= 0 then
            opt.notAvailable = true
            local tip = ISInventoryPaneContextMenu.addToolTip(); tip.description = getText("IGUI_TOC_SawNoFuel"); opt.toolTip = tip
        end
    end
    local petrol = player:getInventory():getFirstEvalRecurse(PetrolPredicate)
    if petrol then
        local opt = sub:addOption(getText("ContextMenu_TOC_SawRefuel", petrol:getDisplayName()), player, function(p)
            ISTimedActionQueue.add(ChainsawActions.Refuel:new(p, petrol))
        end)
        if st.running or ChainsawArm.GetFuel(arm) >= ChainsawArm.TANK - 0.005 then
            opt.notAvailable = true
            local tip = ISInventoryPaneContextMenu.addToolTip()
            tip.description = getText(st.running and "IGUI_TOC_SawRunning" or "IGUI_TOC_SawFull"); opt.toolTip = tip
        end
    else
        local opt = sub:addOption(getText("ContextMenu_TOC_SawNoPetrol"), nil, nil)
        opt.notAvailable = true
    end
end

local function OnFillInventoryObjectContextMenu(playerNum, context, items)
    local player = getSpecificPlayer(playerNum)
    if not player or not ChainsawArm.GetArm(player) then return end
    -- only when the clicked item is the arm, the saw or a petrol container
    local relevant = false
    for i = 1, #items do
        local it = items[i]
        if type(it) == "table" and it.items then it = it.items[1] end
        if it and (ChainsawArm.IsSaw(it) or StaticData.GetProsthesisBase(it:getFullType()) == ChainsawArm.BASE or PetrolPredicate(it)) then relevant = true end
    end
    if relevant then pcall(AddMenu, playerNum, context) end
end

local function OnFillWorldObjectContextMenu(playerNum, context, worldobjects, test)
    if test then return end
    pcall(AddMenu, playerNum, context)
end

-------------------------
--* The saw is part of the arm: it cannot be put away or dropped *--

local og_ISInventoryTransferAction_isValid = ISInventoryTransferAction.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISInventoryTransferAction:isValid()
    if ChainsawArm.IsSaw(self.item) and self.character and self.destContainer ~= self.character:getInventory() then return false end
    return og_ISInventoryTransferAction_isValid(self)
end

if ISDropWorldItemAction then
    local og_ISDropWorldItemAction_isValid = ISDropWorldItemAction.isValid
    ---@diagnostic disable-next-line: duplicate-set-field
    function ISDropWorldItemAction:isValid()
        if ChainsawArm.IsSaw(self.item) then return false end
        return og_ISDropWorldItemAction_isValid(self)
    end
end

Events.OnPlayerUpdate.Add(OnPlayerUpdate)
Events.EveryOneMinute.Add(EveryOneMinute)
Events.OnWeaponSwing.Add(function(character, weapon) pcall(OnWeaponSwing, character, weapon) end)
Events.OnEquipPrimary.Add(function(player, item) pcall(OnEquipPrimary, player, item) end)
Events.OnCreatePlayer.Add(OnCreatePlayer)
Events.OnFillInventoryObjectContextMenu.Add(OnFillInventoryObjectContextMenu)
Events.OnFillWorldObjectContextMenu.Add(OnFillWorldObjectContextMenu)

return ChainsawArm
