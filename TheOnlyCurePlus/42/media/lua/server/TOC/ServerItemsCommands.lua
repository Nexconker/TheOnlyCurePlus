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
    item:getModData().TOC_SawFuel = math.max(0, math.min(0.5, args.fuel))
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
    if not def then return end
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
    if playerObj:getPrimaryHandItem() == it then return end
    if playerObj:getSecondaryHandItem() == it then playerObj:setSecondaryHandItem(nil) end
    local prim = playerObj:getPrimaryHandItem()
    if prim and prim:isRequiresEquippedBothHands() then playerObj:setSecondaryHandItem(nil) end
    playerObj:setPrimaryHandItem(it)
    sendEquip(playerObj)
end

function ServerItemsCommands.UnmountWeapon(playerObj, args)
    local def = playerObj and args and MOUNTED[args.kind]
    if not def or WearsMountArm(playerObj, def) then return end
    RemoveMounted(playerObj, def.weapon)
end

local function OnClientItemsCommands(module, command, playerObj, args)
    if module == CommandsData.modules.TOC_ITEMS and ServerItemsCommands[command] then
        local ok, err = pcall(ServerItemsCommands[command], playerObj, args)
        if not ok then print("[TOC+] items command '" .. tostring(command) .. "' failed: " .. tostring(err)) end
    end
end

Events.OnClientCommand.Add(OnClientItemsCommands)

return ServerItemsCommands
