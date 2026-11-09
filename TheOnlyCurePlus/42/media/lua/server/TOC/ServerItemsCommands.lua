require ("TOC/Debug")
local CommandsData = require("TOC/CommandsData")
local CommonMethods = require("TOC/CommonMethods")
local ItemsController = require("TOC/Controllers/ItemsController")
--------------------------------------------

local ServerItemsCommands = {}

---Only the patient itself (or SP) may ask for its own items to be touched
local function Allowed(playerObj, args)
    if not isServer() then return true end
    return playerObj and args and playerObj:getOnlineID() == args.patientNum
end

function ServerItemsCommands.DeleteAllOldAmputationItems(playerObj, args)
    if not Allowed(playerObj, args) then return end
    local patientPl = CommonMethods.GetPatientForServer(args.patientNum)
    if patientPl then ItemsController.Player.DeleteAllOldAmputationItems(patientPl) end
end

function ServerItemsCommands.OverrideAmputationItemVisuals(playerObj, args)
    if not Allowed(playerObj, args) then return end
    local patientPl = CommonMethods.GetPatientForServer(args.patientNum)
    if patientPl and args.limbName then
        ItemsController.Player.OverrideAmputationItemVisuals(patientPl, args.limbName, args.isCicatrized == true)
    end
end

---TOC+: the stump item vanished (issue #288) and the client asks for it again
function ServerItemsCommands.RespawnAmputationItem(playerObj, args)
    if not Allowed(playerObj, args) then return end
    local patientPl = CommonMethods.GetPatientForServer(args.patientNum)
    if not patientPl or not args.limbName then return end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(patientPl:getUsername())
    if not dcInst or not dcInst:getIsCut(args.limbName) or not dcInst:getIsVisible(args.limbName) then return end
    ItemsController.Player.SpawnAmputationItem(patientPl, args.limbName)
    ItemsController.Player.OverrideAmputationItemVisuals(patientPl, args.limbName, dcInst:getIsCicatrized(args.limbName))
end

---TOC+: the chainsaw arm's petrol lives in the prosthesis item's mod data. The client keeps it while playing and
---sends it here (start/stop/refuel and every few minutes) so the server copy that gets saved has it too.
---Only the sender's own items, and only the chainsaw arm.
function ServerItemsCommands.SetSawFuel(playerObj, args)
    if not playerObj or not args or type(args.itemId) ~= "number" or type(args.fuel) ~= "number" then return end
    local item = playerObj:getInventory():getItemById(args.itemId)
    if not item or not (string.find(item:getFullType(), "Prost_ChainsawArm", 1, true) or string.find(item:getFullType(), "Prost_HeadChainsaw", 1, true)) then return end
    -- 3.3.5: desde el cliente sólo puede bajar (el gasto al usarla); llenar va por RefuelSaw, que gasta la gasolina
    local cur = tonumber(item:getModData().TOC_SawFuel) or 0
    item:getModData().TOC_SawFuel = math.max(0, math.min(cur, 0.5, args.fuel))
end

---3.3.5: repostar la motosierra en el servidor: vacía el bidón de verdad y llena el depósito
function ServerItemsCommands.RefuelSaw(playerObj, args)
    if not playerObj or type(args) ~= "table" or type(args.armId) ~= "number" or type(args.petrolId) ~= "number" then return end
    local inv = playerObj:getInventory()
    local arm = inv:getItemWithIDRecursiv(args.armId)
    local can = inv:getItemWithIDRecursiv(args.petrolId)
    if not arm or not can or not (string.find(arm:getFullType(), "Prost_ChainsawArm", 1, true) or string.find(arm:getFullType(), "Prost_HeadChainsaw", 1, true)) then return end
    local ok, fc = pcall(function() return can:getFluidContainer() end)
    if not ok or not fc then return end
    local okp, petrol = pcall(function() return fc:contains(Fluid.Petrol) end)
    if okp and petrol == false then return end
    local fuel = tonumber(arm:getModData().TOC_SawFuel) or 0
    local take = math.min(fc:getAmount(), 0.5 - fuel)
    if take <= 0 then return end
    fc:adjustAmount(fc:getAmount() - take)
    pcall(sendItemStats, can)
    arm:getModData().TOC_SawFuel = math.min(0.5, fuel + take)
    pcall(syncItemModData, playerObj, arm)
end

local CONSUMABLE_REMOVE = { ["Base.AlcoholBandage"] = "Base.BandageDirty", ["Base.Bandage"] = "Base.BandageDirty",
    ["Base.AlcoholRippedSheets"] = "Base.RippedSheetsDirty", ["Base.RippedSheets"] = "Base.RippedSheetsDirty" }

---3.3.5: gastar el desinfectante / la venda de limpiar un muñón o preparar la cirugía. Sólo objetos propios y de los
---tipos que el mod gasta.
function ServerItemsCommands.ConsumeItem(playerObj, args)
    if not playerObj or type(args) ~= "table" or type(args.itemId) ~= "number" then return end
    local StaticData = require("TOC/StaticData")
    local inv = playerObj:getInventory()
    local item = inv:getItemWithIDRecursiv(args.itemId)
    if not item then return end
    local ft = item:getFullType()
    if not StaticData.DISINFECTANT_TYPES[ft] and not CONSUMABLE_REMOVE[ft] then
        local ok, alc = pcall(function() return item:isAlcoholic() and item:getBandagePower() >= 2 end)
        if not (ok and alc) then return end
    end
    local hasFluid = false
    pcall(function() hasFluid = item:hasComponent(ComponentType.FluidContainer) end)
    if hasFluid then
        local fc = item:getFluidContainer()
        local amount = math.max(0, math.min(tonumber(args.amount) or 0.15, 0.15))
        if fc:getAmount() > amount then fc:adjustAmount(fc:getAmount() - amount) end
        pcall(sendItemStats, item)
    elseif instanceof(item, "DrainableComboItem") then
        item:UseAndSync()
    else
        local cont = item:getContainer() or inv
        cont:Remove(item)
        sendRemoveItemFromContainer(cont, item)
        local dirty = args.dirty and CONSUMABLE_REMOVE[ft]
        if dirty then
            local d = inv:AddItem(dirty)
            if d then sendAddItemToContainer(inv, d) end
        end
    end
end

---3.3.1 (Workshop: "the chainsaw and the bayonet always try to equip and get stuck in the equip animation").
---En la Build 42 sólo el servidor crea objetos y equipa (ISEquipWeaponAction:complete corre aquí). La motosierra y la
---hoja montadas se creaban en el cliente: el servidor no las tenía, la acción de equipar fallaba y el cliente la
---repetía cada 3 s. Ahora el cliente lo pide y el servidor crea el arma, la pone en la mano derecha y lo sincroniza.
local MOUNTED = {
    blade = { weapon = "TOC.MountedBlade", arms = { Prost_KnifeArm = true, Prost_HeadBayonet = true } },
    saw = { weapon = "TOC.MountedChainsaw", arms = { Prost_ChainsawArm = true, Prost_HeadChainsaw = true } },
}

local function WearsMountArm(playerObj, def)
    local StaticData = require("TOC/StaticData")
    local worn = playerObj:getWornItems()
    for i = 0, (worn and worn:size() or 0) - 1 do
        local it = worn:get(i):getItem()
        local base = it and StaticData.GetProsthesisBase(it:getFullType())
        if base and def.arms[base] then return true end
    end
    return false
end

local function RemoveMounted(playerObj, weapon)
    local inv = playerObj:getInventory()
    local changed = false
    for _ = 1, 5 do
        local it = inv:getFirstTypeRecurse(weapon)
        if not it then break end
        playerObj:removeFromHands(it)
        local cont = it:getContainer()
        if not cont then break end
        cont:Remove(it)
        sendRemoveItemFromContainer(cont, it)
        changed = true
    end
    if changed then sendEquip(playerObj) end
end

function ServerItemsCommands.MountWeapon(playerObj, args)
    local def = playerObj and args and MOUNTED[args.kind]
    if not def or playerObj:isDead() then return end
    if not WearsMountArm(playerObj, def) then RemoveMounted(playerObj, def.weapon); return end
    local inv = playerObj:getInventory()
    local it = inv:getFirstTypeRecurse(def.weapon)
    if it and it:getContainer() ~= inv then                 -- en una bolsa: al inventario principal
        local cont = it:getContainer()
        cont:Remove(it); sendRemoveItemFromContainer(cont, it)
        inv:AddItem(it); sendAddItemToContainer(inv, it)
    end
    if not it then
        it = inv:AddItem(def.weapon)
        if not it then return end
        sendAddItemToContainer(inv, it)
    end
    -- 3.3.5: si el cliente lo pide es que no la ve en la mano: se le reenvía (antes se callaba y lo pedía cada 3 s)
    if playerObj:getPrimaryHandItem() == it then sendEquip(playerObj); return end
    if playerObj:getSecondaryHandItem() == it then playerObj:setSecondaryHandItem(nil) end
    local prim = playerObj:getPrimaryHandItem()
    -- 3.3.5: un arma llevada a dos manos (aunque no lo exija) también ocupa la izquierda
    if prim and (prim:isRequiresEquippedBothHands() or playerObj:getSecondaryHandItem() == prim) then playerObj:setSecondaryHandItem(nil) end
    playerObj:setPrimaryHandItem(it)
    sendEquip(playerObj)
end

function ServerItemsCommands.UnmountWeapon(playerObj, args)
    local def = playerObj and args and MOUNTED[args.kind]
    if not def or WearsMountArm(playerObj, def) then return end
    RemoveMounted(playerObj, def.weapon)
end

---3.3.4: pintura de una prótesis (sólo objetos del propio jugador y sólo piezas pintables)
function ServerItemsCommands.SetPaint(playerObj, args)
    if not playerObj or not args or type(args.itemId) ~= "number" or type(args.idx) ~= "number" then return end
    local Paint = require("TOC/Plus/ProsthesisPaint")
    local inv = playerObj:getInventory()
    local item = inv:getItemWithIDRecursiv(args.itemId)
    if not item or not Paint.IsPaintable(item) then return end
    local idx = math.floor(args.idx)
    if idx < 0 or idx > #Paint.COLORS then return end
    Paint.Apply(playerObj, item, idx)
    syncItemModData(playerObj, item)
end

---3.3.6: convertir las prótesis de brazo de la 3.2 en el servidor. Antes lo hacía el cliente en multijugador: las piezas
---nuevas no existían en el servidor (desaparecían al reconectar, volvían las antiguas y se convertía otra vez en cada
---carga). Sólo el propio jugador, vivo, y como mucho cada 10 s; ConvertOld no toca nada si no hay piezas antiguas.
local lastConvert = {}
function ServerItemsCommands.ConvertOldProstheses(playerObj, args)
    if not playerObj or playerObj:isDead() then return end
    local username = playerObj:getUsername()
    local now = getTimestampMs()
    if lastConvert[username] and now - lastConvert[username] < 10000 then return end
    lastConvert[username] = now
    local Modular = require("TOC/Plus/ModularProsthesis")
    local ok, n = pcall(Modular.ConvertOld, playerObj)
    if not ok then print("[TOC+] ConvertOldProstheses: " .. tostring(n)); return end
    if n and n > 0 then
        local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
        pcall(function()
            CachedDataHandler.CalculateCacheableValues(username)
            CachedDataHandler.SendCache(playerObj, username, false)
        end)
    end
end

local function OnClientItemsCommands(module, command, playerObj, args)
    if module == CommandsData.modules.TOC_ITEMS and ServerItemsCommands[command] then
        local ok, err = pcall(ServerItemsCommands[command], playerObj, args)
        if not ok then print("[TOC+] items command '" .. tostring(command) .. "' failed: " .. tostring(err)) end
    end
end

Events.OnClientCommand.Add(OnClientItemsCommands)

return ServerItemsCommands
