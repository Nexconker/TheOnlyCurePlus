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

local function OnClientItemsCommands(module, command, playerObj, args)
    if module == CommandsData.modules.TOC_ITEMS and ServerItemsCommands[command] then
        local ok, err = pcall(ServerItemsCommands[command], playerObj, args)
        if not ok then print("[TOC+] items command '" .. tostring(command) .. "' failed: " .. tostring(err)) end
    end
end

Events.OnClientCommand.Add(OnClientItemsCommands)

return ServerItemsCommands
