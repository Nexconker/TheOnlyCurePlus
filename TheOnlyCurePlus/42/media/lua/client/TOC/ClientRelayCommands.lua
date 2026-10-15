local CommandsData = require("TOC/CommandsData")
local AmputationHandler = require("TOC/Handlers/AmputationHandler")
local DataController = require("TOC/Controllers/DataController")
local Messages = require("TOC/Plus/Messages")
--------------------------------------------

local ClientRelayCommands = {}

local function InitAmputationHandler(limbName, surgeonNum)
    local surgeonPl = getSpecificPlayer(surgeonNum)
    return AmputationHandler:new(surgeonPl, getPlayer(), limbName)
end

---@param args receiveDamageDuringAmputationParams
function ClientRelayCommands.ReceiveDamageDuringAmputation(args)
    AmputationHandler.ApplyDamageDuringAmputation(getPlayer(), args.limbName)
end

---@param args receiveExecuteAmputationActionParams
function ClientRelayCommands.ReceiveExecuteAmputationAction(args)
    local dcInst = DataController.GetReady(getPlayer():getUsername())
    if not dcInst or dcInst:getIsCut(args.limbName) then return end
    local handler = InitAmputationHandler(args.limbName, args.surgeonNum)
    handler:execute(args.damagePlayer)
end

function ClientRelayCommands.FinalizeAmputationAction(args)
    ClientRelayCommands.ReceiveCache(args)
end

--* APPLY RELAY *--
function ClientRelayCommands.ReceiveApplyFromServer(args)
    if not args or not args.patientUsername then return end
    local key = CommandsData.GetKey(args.patientUsername)
    ModData.request(key)
end

function ClientRelayCommands.ReceiveCache(args)
    if not args or not args.patientUsername then return end
    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    CachedDataHandler.ApplyFromServer(args.patientUsername, args.cache)
    if getPlayer() and getPlayer():getUsername() == args.patientUsername then
        CachedDataHandler.OverrideInteractionsKey()
    end
end

--* WEAR AMPUTATION ITEM *--
function ClientRelayCommands.ReceiveWearAmputation(args)
    if not args or not args.itemName then return end
    AmputationHandler.WearAmputationItem(getPlayer(), args.itemName)
end

--* TOC+ *--

---@param args receiveSurgeryResultParams
function ClientRelayCommands.ReceiveSurgeryResult(args)
    if not args or not args.limbName then return end
    Messages.SurgeryResult(getPlayer(), args.limbName, args.severity or 0, args.cure)
end

---@param args receivePlusMessageParams
function ClientRelayCommands.ReceivePlusMessage(args)
    if not args or not args.text then return end
    Messages.Say(getPlayer(), args.text, args.bad)
end

---@param args receiveZombieCrawlerParams
function ClientRelayCommands.ReceiveZombieCrawler(args)
    if not args or not args.zombieID then return end
    pcall(function()
        local list = getCell():getZombieList()
        for i = 0, list:size() - 1 do
            local z = list:get(i)
            if z and z:getOnlineID() == args.zombieID and not z:isCrawling() then
                z:toggleCrawling()
                return
            end
        end
    end)
end

--* TRIGGERED BY ADMINS *--
function ClientRelayCommands.ReceiveExecuteInitialization()
    local LocalPlayerController = require("TOC/Controllers/LocalPlayerController")
    LocalPlayerController.InitializePlayer(true)
end

-------------------------

local function OnServerRelayCommand(module, command, args)
    if module == CommandsData.modules.TOC_RELAY and ClientRelayCommands[command] then
        local ok, err = pcall(ClientRelayCommands[command], args)
        if not ok then print("[TOC+] client relay '" .. tostring(command) .. "' failed: " .. tostring(err)) end
    end
end

Events.OnServerCommand.Add(OnServerRelayCommand)

return ClientRelayCommands
