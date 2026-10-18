-- TOC+ 3.3: prótesis modulares (DISENO_3.3_MODULAR.md). Una prótesis de brazo = BASE (encaje + armazón, ubicación
-- toc:ArmProst_X, la de siempre: el resto del mod la trata como una prótesis normal) + CABEZAL (mano, gancho, motosierra,
-- bayoneta..., ubicación toc:ArmHead_X). El tier puesto es la combinación (StaticData.CombineTier vía
-- ProsthesisHandler.GetEquippedTier). Aquí:
--  - reglas para poner un cabezal (base puesta en ese lado, lado del cabezal, base de metal para la motosierra);
--  - estado del cabezal en DataController (sincronizado con el servidor, RelayProsthesisHead);
--  - quitar la base quita su cabezal;
--  - conversión de las prótesis de brazo antiguas (puestas o en el inventario) en base + cabezal.

local StaticData = require("TOC/StaticData")
local CommandsData = require("TOC/CommandsData")
local DataController = require("TOC/Controllers/DataController")
local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")      -- sus overrides primero; los nuestros los envuelven
local OverridenMethodsArchive = require("TOC/OverridenMethodsArchive")
------------------

---@class ModularProsthesis
local Modular = {}

-- prótesis antigua -> base + cabezal
Modular.OLD_MAP = {
    Prost_PegArm      = { "Prost_BaseWood",  "Prost_HeadKnob" },
    Prost_HookArm     = { "Prost_BaseScrap", "Prost_HeadHook" },
    Prost_NormalArm   = { "Prost_BaseMech",  "Prost_HeadMechHand" },
    Prost_MedicalArm  = { "Prost_BaseMed",   "Prost_HeadMedHand" },
    Prost_ChainsawArm = { "Prost_BaseScrap", "Prost_HeadChainsaw" },
    Prost_KnifeArm    = { "Prost_BaseScrap", "Prost_HeadBayonet" },
}

---@param item InventoryItem?
function Modular.IsHead(item)
    if not item or not item.getBodyLocation or item:getBodyLocation() == nil then return false end
    return string.contains(string.lower(item:getBodyLocation():toString()), StaticData.HEAD_LOCATION_PREFIX)
end

---@param item InventoryItem?
function Modular.IsModularBase(item)
    if not item or not ProsthesisHandler.CheckIfProst(item) then return false end
    local tier = StaticData.GetProsthesisTier(item:getFullType())
    return tier ~= nil and tier.modular == true
end

---Base worn on a side (or nil)
---@param character IsoPlayer
---@param side string
function Modular.GetWornBase(character, side)
    local it = ProsthesisHandler.FindWornProsthesis(character, "Top_" .. side)
    if it and Modular.IsModularBase(it) then return it end
    return nil
end

---Head worn on a side (or nil)
function Modular.GetWornHead(character, side)
    local worn = character:getWornItems()
    if not worn then return nil end
    for i = 0, worn:size() - 1 do
        local it = worn:get(i):getItem()
        if it and Modular.IsHead(it) then
            local _, s = StaticData.GetProsthesisBase(it:getFullType())
            if s == side then return it end
        end
    end
    return nil
end

local function otherSide(s) return s == "L" and "R" or "L" end

local function flippedType(fullType)
    local _, side = StaticData.GetProsthesisBase(fullType)
    if not side then return nil end
    local t = string.gsub(fullType, "_" .. side .. "$", "_" .. otherSide(side))
    if getScriptManager():FindItem(t) then return t end
    return nil
end

---Lado en que irá un cabezal: el suyo si allí hay base; si no, el otro si allí hay base y el cabezal existe de ese lado.
---@return string? side, string? reasonKey
function Modular.ResolveHeadSide(character, fullType)
    local head, side = StaticData.GetHeadTier(fullType)
    if not head then return nil, nil end
    local function fits(s)
        local base = Modular.GetWornBase(character, s)
        if not base then return false, "IGUI_TOC_HeadNeedsBase" end
        if head.side and head.side ~= s then return false, "IGUI_TOC_HeadWrongSide" end
        if head.metalBase then
            local bt = StaticData.GetProsthesisTier(base:getFullType())
            if not bt or bt.material ~= "metal" then return false, "IGUI_TOC_HeadNeedsMetal" end
        end
        if head.minBaseTier then
            local bt = StaticData.GetProsthesisTier(base:getFullType())
            if not bt or (bt.tier or 0) < head.minBaseTier then
                return false, head.minBaseTier >= 3 and "IGUI_TOC_HeadNeedsAdvancedBase" or "IGUI_TOC_HeadNotOnWood"
            end
        end
        return true
    end
    local ok, why = fits(side)
    if ok then return side end
    local ok2 = fits(otherSide(side))
    if ok2 and (head.side == nil or head.side == otherSide(side)) and flippedType(fullType) then return otherSide(side) end
    return nil, why
end

---Estado del cabezal en DataController + servidor
---@param character IsoPlayer
---@param item InventoryItem
---@param isEquipping boolean
function Modular.SetupHead(character, item, isEquipping)
    local _, side = StaticData.GetProsthesisBase(item:getFullType())
    if not side then return end
    local group = "Top_" .. side
    local dcInst = DataController.GetReady(character:getUsername())
    if not dcInst then return end
    local headType = isEquipping and item:getFullType() or nil
    dcInst:setProstHead(group, headType)
    if isClient() and character:isLocalPlayer() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayProsthesisHead, {group = group, headType = headType})
    end
    triggerEvent("OnTOCProsthesisHeadChanged", character, group, headType)
end

local function swapWorn(character, old, newType)
    local newItem = instanceItem(newType)
    if not newItem then return old end
    pcall(function()
        if copyClothingItem then copyClothingItem(old, newItem) else newItem:setCondition(old:getCondition()) end
        local inv = character:getInventory()
        character:removeWornItem(old, false)
        inv:Remove(old)
        if sendRemoveItemFromContainer then sendRemoveItemFromContainer(inv, old) end
        inv:AddItem(newItem)
        if sendAddItemToContainer then sendAddItemToContainer(inv, newItem) end
        character:setWornItem(newItem:getBodyLocation(), newItem)
        if sendClothing then sendClothing(character, newItem:getBodyLocation(), newItem) end
        if syncVisuals then syncVisuals(character) end
        character:resetModelNextFrame()
    end)
    return newItem
end

---Quita el cabezal puesto en un lado (al quitar la base): pasa al inventario.
function Modular.DropHead(character, side)
    local head = Modular.GetWornHead(character, side)
    if not head then return end
    pcall(function()
        character:removeWornItem(head)
        if sendClothing then sendClothing(character, head:getBodyLocation(), nil) end
        if syncVisuals then syncVisuals(character) end
        character:resetModelNextFrame()
    end)
    Modular.SetupHead(character, head, false)
end

-------------------------
--* Overrides (después de los de ProsthesisHandler) *--

LuaEventManager.AddEvent("OnTOCProsthesisHeadChanged")    -- args: character, group, headType?

local og_wear_isValid = ISWearClothing.isValid
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:isValid()
    local ok = og_wear_isValid(self)
    if not ok or not Modular.IsHead(self.item) then return ok end
    local side, why = Modular.ResolveHeadSide(self.character, self.item:getFullType())
    if not side then
        local Messages = require("TOC/Plus/Messages")
        Messages.Say(self.character, getText(why or "IGUI_TOC_HeadNeedsBase"), false)
        return false
    end
    return true
end

local og_wear_complete = ISWearClothing.complete
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:complete()
    local result = og_wear_complete(self)
    if result and Modular.IsHead(self.item) then
        local item = self.item
        local _, side = StaticData.GetProsthesisBase(item:getFullType())
        local want = Modular.ResolveHeadSide(self.character, item:getFullType())
        if want and want ~= side then item = swapWorn(self.character, item, flippedType(item:getFullType())) end
        self.item = item
        Modular.SetupHead(self.character, item, true)
    end
    return result
end

local og_unequip_complete = ISUnequipAction.complete
---@diagnostic disable-next-line: duplicate-set-field
function ISUnequipAction:complete()
    local item, chr = self.item, self.character
    local isHead = Modular.IsHead(item)
    local isBase = Modular.IsModularBase(item)
    local result = og_unequip_complete(self)
    if isHead then Modular.SetupHead(chr, item, false) end
    if isBase then
        local _, side = StaticData.GetProsthesisBase(item:getFullType())
        if side then Modular.DropHead(chr, side) end
    end
    return result
end

local og_extra_complete = ISClothingExtraAction.complete
---@diagnostic disable-next-line: duplicate-set-field
function ISClothingExtraAction:complete()
    -- cambiar de lado un cabezal: el nuevo lado necesita su base (lo comprueba isValid al vestirlo)
    local wasHead = Modular.IsHead(self.item)
    local oldItem = self.item
    local result = og_extra_complete(self)
    if wasHead then
        Modular.SetupHead(self.character, oldItem, false)
        local _, side = StaticData.GetProsthesisBase(self.extra)
        local head = side and Modular.GetWornHead(self.character, side)
        if head then Modular.SetupHead(self.character, head, true) end
    end
    return result
end

-------------------------
--* Conversión de prótesis antiguas *--

---@param fullType string prótesis antigua (con nivel), p. ej. TOC.Prost_HookArmWrist_L
---@return string? baseType, string? headType
function Modular.ConvertedTypes(fullType)
    local old, side = StaticData.GetProsthesisBase(fullType)
    local map = old and Modular.OLD_MAP[old]
    if not map then return nil end
    local lvl = string.match(fullType, "^TOC%." .. old .. "(%a*)_[LR]$") or ""
    return "TOC." .. map[1] .. lvl .. "_" .. side, "TOC." .. map[2] .. "_" .. side
end

local function isWorn(character, item)
    local worn = character:getWornItems()
    for i = 0, (worn and worn:size() or 0) - 1 do
        if worn:get(i):getItem() == item then return true end
    end
    return false
end

local function newPart(inv, fullType, from)
    local it = instanceItem(fullType)
    if not it then return nil end
    pcall(function()
        it:setCondition(math.min(it:getConditionMax(), from:getCondition()))
        local md, omd = it:getModData(), from:getModData()
        for k, v in pairs(omd) do md[k] = v end            -- gasolina de la motosierra, desgaste...
    end)
    inv:AddItem(it)
    if sendAddItemToContainer then sendAddItemToContainer(inv, it) end
    return it
end

---Convierte las prótesis de brazo antiguas del jugador (puestas e inventario). Devuelve cuántas.
---@param character IsoPlayer
function Modular.ConvertOld(character)
    local inv = character:getInventory()
    local n = 0
    -- puestas
    for _, side in ipairs({ "L", "R" }) do
        local old = ProsthesisHandler.FindWornProsthesis(character, "Top_" .. side)
        local bt, ht = old and Modular.ConvertedTypes(old:getFullType())
        if bt and ht then
            local base, head
            pcall(function()
                character:removeWornItem(old, false)
                ProsthesisHandler.SearchAndSetupProsthesis(character, old, false)
                inv:Remove(old)
                if sendRemoveItemFromContainer then sendRemoveItemFromContainer(inv, old) end
                base = newPart(inv, bt, old); head = newPart(inv, ht, old)
                if base then
                    character:setWornItem(base:getBodyLocation(), base)
                    if sendClothing then sendClothing(character, base:getBodyLocation(), base) end
                    ProsthesisHandler.SearchAndSetupProsthesis(character, base, true)
                end
                if base and head then
                    character:setWornItem(head:getBodyLocation(), head)
                    if sendClothing then sendClothing(character, head:getBodyLocation(), head) end
                    Modular.SetupHead(character, head, true)
                end
            end)
            n = n + 1
        end
    end
    -- en el inventario (también dentro de bolsas)
    local found = ArrayList.new()
    pcall(function() inv:getAllEvalRecurse(function(it) return Modular.ConvertedTypes(it:getFullType()) ~= nil end, found) end)
    for i = 0, found:size() - 1 do
        local old = found:get(i)
        local bt, ht = Modular.ConvertedTypes(old:getFullType())
        local cont = old:getContainer() or inv
        if bt and not isWorn(character, old) then
            pcall(function()
                cont:Remove(old)
                if sendRemoveItemFromContainer then sendRemoveItemFromContainer(cont, old) end
                newPart(cont, bt, old); newPart(cont, ht, old)
            end)
            n = n + 1
        end
    end
    if n > 0 then
        character:resetModelNextFrame()
        if syncVisuals then pcall(syncVisuals, character) end
    end
    return n
end

if not isServer() then
    local pending = {}
    Events.OnCreatePlayer.Add(function(playerNum) pending[playerNum] = 0 end)
    local ticks = 0
    Events.OnPlayerUpdate.Add(function(player)
        if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
        -- vigilante: un cabezal sin base (la base se rompió, la quitó otro mod, se cambió de lado...) pasa al inventario
        ticks = ticks + 1
        if ticks % 60 == 0 then
            pcall(function()
                for _, side in ipairs({ "L", "R" }) do
                    if Modular.GetWornHead(player, side) and not Modular.GetWornBase(player, side) then Modular.DropHead(player, side) end
                end
            end)
        end
        local k = player:getPlayerNum()
        if pending[k] == nil then return end
        pending[k] = pending[k] + 1
        if pending[k] < 120 then return end                          -- unos segundos tras cargar: datos de TOC listos
        if not DataController.GetReady(player:getUsername()) then return end
        pending[k] = nil
        local ok, n = pcall(Modular.ConvertOld, player)
        if ok and n and n > 0 then
            local Messages = require("TOC/Plus/Messages")
            Messages.Say(player, getText("IGUI_TOC_ProsthesesConverted"), false)
        elseif not ok then print("[TOC+] ConvertOld: " .. tostring(n)) end
    end)
end

return Modular
