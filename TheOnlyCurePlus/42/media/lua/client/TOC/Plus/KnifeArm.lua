local StaticData = require("TOC/StaticData")
local Messages = require("TOC/Plus/Messages")
local CommandsData = require("TOC/CommandsData")
------------------

-- TOC+ 3.2.0: Merle-style bayonet arm. While Prost_KnifeArm_R is worn the right hand holds TOC.MountedBlade, a
-- one-handed knife with an invisible model: the blade you see is part of the prosthesis (rigid on the forearm, in
-- line with it), so the left hand stays free. Same pattern as TOC/Plus/ChainsawArm, without engine or fuel: the blade
-- never breaks, the arm wears out with use.

---@class KnifeArm
local KnifeArm = {}

KnifeArm.WEAPON = "TOC.MountedBlade"
KnifeArm.BASE = "Prost_KnifeArm"
KnifeArm.HEAD = "Prost_HeadBayonet"      -- 3.3: cabezal modular
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
        local b = item and StaticData.GetProsthesisBase(item:getFullType())
        if b == KnifeArm.BASE or b == KnifeArm.HEAD then return item end
    end
    return nil
end

KnifeArm.VISUAL = "TOC.PistolVisual"
KnifeArm.INVISIBLE = "TOC_Invisible"

---3.3.1 (pedido): con la bayoneta se pueden usar pistolas (sólo pistolas: armas de fuego con el gesto "Handgun"), como
---Merle. Mientras haya una en la mano derecha la hoja se guarda; al soltarla, la hoja vuelve sola (Enforce).
---@param item InventoryItem?
---@return boolean
function KnifeArm.IsVisual(item)
    return item ~= nil and item:getFullType() == KnifeArm.VISUAL
end

---@param item InventoryItem?
---@return boolean
function KnifeArm.IsPistol(item)
    if item == nil or not instanceof(item, "HandWeapon") then return false end
    local ok, res = pcall(function()
        return item:isRanged() and item:getSwingAnim() == "Handgun" and not item:isTwoHandWeapon()
            and not item:isRequiresEquippedBothHands()
    end)
    return ok and res == true
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

---3.3.1 (multijugador): la hoja la crea y la equipa el servidor (ServerItemsCommands.MountWeapon). Creada en el
---cliente no existía para el servidor y la acción de equipar se repetía cada 3 s sin terminar nunca.
local function EnforceMP(player, st)
    local now = getTimestampMs()
    if now < (st.nextMount or 0) then return end
    local blade = FindBlade(player)
    if not KnifeArm.GetArm(player) then
        if blade then
            st.nextMount = now + 3000
            sendClientCommand(CommandsData.modules.TOC_ITEMS, "UnmountWeapon", {kind = "blade"})
        end
        return
    end
    if player:isDead() or player:isAsleep() then return end
    local prim = player:getPrimaryHandItem()
    if (blade and prim == blade) or KnifeArm.IsPistol(prim) then return end
    if player:isAiming() or ISTimedActionQueue.isPlayerDoingAction(player) then return end
    st.nextMount = now + 3000
    sendClientCommand(CommandsData.modules.TOC_ITEMS, "MountWeapon", {kind = "blade"})
end

---Keep the blade in the right hand while the arm is worn; take it away when it is not
---@param player IsoPlayer
function KnifeArm.Enforce(player)
    local st = State(player)
    if isClient() then return EnforceMP(player, st) end
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
    if KnifeArm.IsPistol(player:getPrimaryHandItem()) then return end      -- 3.3.1: pistola en mano, la hoja espera
    -- re-attach with the vanilla equip action (syncs in multiplayer) when the hands are not busy
    local now = getTimestampMs()
    if now < st.nextEquip or player:isAiming() or ISTimedActionQueue.isPlayerDoingAction(player) then return end
    -- 3.3.1: si la mano derecha no cuenta como presente (el estado guardado perdió la base), equipar acaba en la otra
    -- mano y se repetía cada 3 s. Se vuelve a registrar la base puesta; si aun así no, se deja de insistir un rato.
    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    if not CachedDataHandler.GetHandFeasibility("R", player:getUsername()) then
        local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
        local base = ProsthesisHandler.FindWornProsthesis(player, "Top_R")
        if base then pcall(ProsthesisHandler.SearchAndSetupProsthesis, player, base, true) end
        if not CachedDataHandler.GetHandFeasibility("R", player:getUsername()) then st.nextEquip = now + 30000; return end
    end
    st.nextEquip = now + 3000
    if blade:getContainer() ~= player:getInventory() then
        ISTimedActionQueue.add(ISInventoryTransferAction:new(player, blade, blade:getContainer(), player:getInventory(), 1))
    end
    ISTimedActionQueue.add(ISEquipWeaponAction:new(player, blade, 10, true, false))
end

-------------------------
--* Pistola en la mano izquierda (3.3.1) *--
-- La pistola real va en la mano derecha (el juego solo dispara con esa) con el modelo invisible, y en la izquierda una
-- copia visual (TOC.PistolVisual) con el modelo de la pistola. Si la mano izquierda esta ocupada con otra cosa no se
-- esconde nada: la pistola se ve en la derecha como siempre. El modelo original se guarda en el modData del arma.

local function RemoveVisuals(player)
    local inv = player:getInventory()
    for _ = 1, 10 do
        local v = inv:getFirstTypeRecurse(KnifeArm.VISUAL)
        if not v then return end
        if player:getSecondaryHandItem() == v then player:setSecondaryHandItem(nil) end
        local cont = v:getContainer()
        if not cont then return end
        cont:Remove(v)
        if sendRemoveItemFromContainer then sendRemoveItemFromContainer(cont, v) end
    end
end

---@param gun InventoryItem
local function RestoreGun(gun)
    if not gun then return end
    local md = gun:getModData()
    if md.TOC_OrigSprite then
        pcall(function() gun:setWeaponSprite(md.TOC_OrigSprite) end)
        md.TOC_OrigSprite = nil
    end
end

---Deja la pistola y su copia como toca segun lo que lleva puesto y en las manos
---@param player IsoPlayer
function KnifeArm.SyncPistol(player)
    local st = State(player)
    local prim, sec = player:getPrimaryHandItem(), player:getSecondaryHandItem()
    local want = not isClient() and KnifeArm.GetArm(player) ~= nil and KnifeArm.IsPistol(prim) and (sec == nil or KnifeArm.IsVisual(sec) or sec == prim)
    local changed = false
    if st.hiddenGun and (not want or st.hiddenGun ~= prim) then
        RestoreGun(st.hiddenGun); st.hiddenGun = nil; changed = true
    end
    if want then
        local md = prim:getModData()
        if not md.TOC_OrigSprite then
            md.TOC_OrigSprite = prim:getWeaponSprite()
            prim:setWeaponSprite(KnifeArm.INVISIBLE)
            changed = true
        end
        st.hiddenGun = prim
        if sec == prim then player:setSecondaryHandItem(nil); sec = nil end
        if not KnifeArm.IsVisual(sec) then
            local inv = player:getInventory()
            local v = inv:getFirstTypeRecurse(KnifeArm.VISUAL)
            if not v then
                v = inv:AddItem(KnifeArm.VISUAL)
                if v and sendAddItemToContainer then pcall(sendAddItemToContainer, inv, v) end
            end
            if v then
                pcall(function() v:setStaticModel(md.TOC_OrigSprite) end)
                player:setSecondaryHandItem(v)
                changed = true
            end
        else
            pcall(function() sec:setStaticModel(md.TOC_OrigSprite) end)
        end
    elseif KnifeArm.IsVisual(sec) or player:getInventory():getFirstTypeRecurse(KnifeArm.VISUAL) then
        RemoveVisuals(player); changed = true
    end
    if changed then pcall(function() player:resetEquippedHandsModels() end) end
end

---Al cargar: armas que se quedaron con el modelo invisible (se cerro el juego con la pistola en la mano)
local function RestoreStray(player)
    local list = player:getInventory():getAllEvalRecurse(function(it) return it:getModData().TOC_OrigSprite ~= nil end)
    for i = 0, list:size() - 1 do RestoreGun(list:get(i)) end
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
    ok, err = pcall(KnifeArm.SyncPistol, player)
    if not ok then print("[TOC+] KnifeArm.SyncPistol: " .. tostring(err)) end
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
        local Modular = require("TOC/Plus/ModularProsthesis")
        if Modular.IsHead(arm) then Modular.SetupHead(player, arm, false) else ProsthesisHandler.SearchAndSetupProsthesis(player, arm, false) end
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
    if IsLocal(player) then pcall(KnifeArm.SyncPistol, player) end
    if not IsLocal(player) or item == nil or KnifeArm.IsBlade(item) then return end
    if not KnifeArm.GetArm(player) then return end
    if KnifeArm.IsPistol(item) then return end                              -- 3.3.1: las pistolas sí se quedan
    local blade = FindBlade(player)
    if not blade then return end
    local twoHanded = item:isRequiresEquippedBothHands() or (instanceof(item, "HandWeapon") and item:isTwoHandWeapon())
    Messages.Say(player, getText("IGUI_TOC_BladeArmBusy"), false)
    if isClient() then State(player).nextMount = 0 else ISTimedActionQueue.add(ISEquipWeaponAction:new(player, blade, 10, true, false)) end
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
    if IsLocal(player) then pcall(RestoreStray, player) end
end

-------------------------
--* The blade is part of the arm: it cannot be put away or dropped *--

local og_ISInventoryTransferAction_isValid = ISInventoryTransferAction.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISInventoryTransferAction:isValid()
    if (KnifeArm.IsBlade(self.item) or KnifeArm.IsVisual(self.item)) and self.character and self.destContainer ~= self.character:getInventory() then return false end
    return og_ISInventoryTransferAction_isValid(self)
end

if ISDropWorldItemAction then
    local og_ISDropWorldItemAction_isValid = ISDropWorldItemAction.isValid
    ---@diagnostic disable-next-line: duplicate-set-field
    function ISDropWorldItemAction:isValid()
        if KnifeArm.IsBlade(self.item) or KnifeArm.IsVisual(self.item) then return false end
        return og_ISDropWorldItemAction_isValid(self)
    end
end

Events.OnPlayerUpdate.Add(OnPlayerUpdate)
Events.OnWeaponSwing.Add(function(character, weapon) pcall(OnWeaponSwing, character, weapon) end)
Events.OnEquipPrimary.Add(function(player, item) pcall(OnEquipPrimary, player, item) end)
Events.OnCreatePlayer.Add(OnCreatePlayer)

return KnifeArm
