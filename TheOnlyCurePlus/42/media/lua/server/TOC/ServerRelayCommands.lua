require ("TOC/Debug")
local CommandsData = require("TOC/CommandsData")
local CommonMethods = require("TOC/CommonMethods")
local StaticData = require("TOC/StaticData")
local PostOp = require("TOC/Plus/PostOp")
--------------------------------------------

-- Every handler validates its arguments: a crafted packet can at most touch the sender's own
-- body, or a patient standing next to the sender.

local ServerRelayCommands = {}

local function IsAdmin(playerObj)
    if not isServer() then return true end
    local ok, r = pcall(function() return playerObj:getAccessLevel() end)
    if ok and r and tostring(r) ~= "None" and tostring(r) ~= "" then return true end
    ok, r = pcall(function() return playerObj:getRole() and playerObj:getRole():getName() end)
    if ok and r and string.lower(tostring(r)) ~= "player" then return true end
    return false
end

---@return boolean
local function Near(a, b, maxDist)
    if not a or not b then return false end
    if a == b then return true end
    local ok, d = pcall(function() return IsoUtils.DistanceTo(a:getX(), a:getY(), b:getX(), b:getY()) end)
    return ok and d ~= nil and d <= (maxDist or 3)
end

---Resolve the patient of a command; the sender may only act on itself or on someone next to it
---@param senderPl IsoPlayer
---@param patientNum number?
---@return IsoPlayer?
local function Patient(senderPl, patientNum)
    if patientNum == nil then return senderPl end
    local patient = CommonMethods.GetPatientForServer(patientNum)
    if not patient then return nil end
    if patient ~= senderPl and not Near(senderPl, patient, 3) then
        TOC_DEBUG.print("Relay rejected: patient too far from " .. tostring(senderPl:getUsername()))
        return nil
    end
    return patient
end

local function ValidLimb(limbName)
    return type(limbName) == "string" and StaticData.LIMBS_TO_BODYLOCS_IND_BPT[limbName] ~= nil
end

--* DATA CONTROLLER
function ServerRelayCommands.RelayRequestDataController(playerObj, args)
    if type(args) ~= "table" or type(args.username) ~= "string" then return end
    -- only your own data can be reset; reading someone else's data is fine (medical check)
    local isForced = args.isForced == true and args.username == playerObj:getUsername()
    local ServerDataController = require("TOC/Controllers/ServerDataController")
    local target = CommonMethods.FindOnlinePlayer(args.username) or playerObj
    ServerDataController.Initialize(args.username, isForced, target)
    if target ~= playerObj then
        local dcInst = require("TOC/Controllers/DataController").GetInstance(args.username)
        if dcInst then dcInst:apply(playerObj) end
    end
end

---@param playerObj IsoPlayer
---@param args table
function ServerRelayCommands.UpdateDataControllerFromClient(playerObj, args)
    if type(args) ~= "table" then return end
    local DataController = require("TOC/Controllers/DataController")
    local h = DataController.GetReady(playerObj:getUsername())
    if not h then return end
    if ValidLimb(args.limbName) then
        if type(args.cicTime) == "number" then h:setCicatrizationTime(args.limbName, math.max(0, args.cicTime)) end
        if type(args.dirtyness) == "number" then h:setWoundDirtyness(args.limbName, math.max(0, math.min(1, args.dirtyness))) end
        if type(args.sepsis) == "number" then h:setSepsis(args.limbName, args.sepsis) end
        if args.isInfected ~= nil then h:setIsInfected(args.limbName, args.isInfected == true) end
        if args.isCauterized ~= nil then h:setIsCauterized(args.limbName, args.isCauterized == true) end
        if args.isCicatrized ~= nil then h:setIsCicatrized(args.limbName, args.isCicatrized == true) end
    end
    if args.isIgnoredPartInfected ~= nil then
        h:setIsIgnoredPartInfected(args.isIgnoredPartInfected == true)
    end
end

---@param playerObj IsoPlayer
---@param args relayPlusDataParams
function ServerRelayCommands.RelayPlusData(playerObj, args)
    if type(args) ~= "table" or type(args.plus) ~= "table" then return end
    local DataController = require("TOC/Controllers/DataController")
    local h = DataController.GetReady(playerObj:getUsername())
    if not h then return end
    local plus = h:plus()
    local p = args.plus
    if type(p.lastDiagnosis) == "table" then plus.lastDiagnosis = p.lastDiagnosis end
    if type(p.phantomNext) == "number" then plus.phantomNext = p.phantomNext end
    if type(p.carryDelta) == "number" then plus.carryDelta = p.carryDelta end
    if type(p.carryApplied) == "number" then plus.carryApplied = p.carryApplied end
end

--* AMPUTATION

---@param args relayDamageDuringAmputationParams
function ServerRelayCommands.RelayDamageDuringAmputation(surgeonPl, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    local patientPl = Patient(surgeonPl, args.patientNum)
    if not patientPl then return end
    local AmputationHandler = require("TOC/Handlers/AmputationHandler")
    AmputationHandler.ApplyDamageDuringAmputation(patientPl, args.limbName)
end

---Legacy path (admin tools): plain amputation without the TOC+ surgery
---@param args relayExecuteAmputationActionParams
function ServerRelayCommands.RelayExecuteAmputationAction(surgeonPl, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    local patientPl = Patient(surgeonPl, args.patientNum)
    if not patientPl then return end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(patientPl:getUsername())
    if dcInst and dcInst:getIsCut(args.limbName) then return end
    local AmputationHandler = require("TOC/Handlers/AmputationHandler")
    AmputationHandler:new(surgeonPl, patientPl, args.limbName):execute(true)
end

---TOC+: the staged surgery. The server rebuilds the plan from its own view of both players and rolls.
---@param args relayExecuteSurgeryParams
function ServerRelayCommands.RelayExecuteSurgery(surgeonPl, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    local patientPl = Patient(surgeonPl, args.patientNum)
    if not patientPl then return end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(patientPl:getUsername())
    if dcInst and dcInst:getIsCut(args.limbName) then return end
    if StaticData.IsLegLimb(args.limbName) and SandboxVars.TOC and SandboxVars.TOC.EnableLegAmputations == false then return end

    local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
    local toolItem = nil
    if type(args.plan) == "table" and type(args.plan.toolType) == "string" and StaticData.SAWS_TYPES[args.plan.toolType] then
        toolItem = surgeonPl:getInventory():FindAndReturn(args.plan.toolType)
    end
    local plan = SurgeryPlan.Gather(surgeonPl, patientPl, args.limbName, toolItem)
    local risk = SurgeryPlan.Risk(plan)
    local outcome = SurgeryPlan.Roll(plan, risk)
    TOC_DEBUG.print("Surgery " .. args.limbName .. " by " .. surgeonPl:getUsername() .. " fail=" .. tostring(risk.fail) .. " roll=" .. tostring(outcome.roll) .. " severity=" .. tostring(outcome.severity))
    local AmputationHandler = require("TOC/Handlers/AmputationHandler")
    AmputationHandler:new(surgeonPl, patientPl, args.limbName):execute(true, outcome)
end

---@param args relaySurgeryBotchedParams
function ServerRelayCommands.RelaySurgeryBotched(surgeonPl, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    local patientPl = Patient(surgeonPl, args.patientNum)
    if not patientPl then return end
    local AmputationHandler = require("TOC/Handlers/AmputationHandler")
    AmputationHandler.ApplyBotchedAttempt(patientPl, args.limbName)
end

--* POST-OP: the client computes, the server applies to the body it owns

---@param args relayPostOpApplyParams
function ServerRelayCommands.RelayPostOpApply(senderPl, args)
    if type(args) ~= "table" or type(args.fx) ~= "table" then return end
    local patientPl = Patient(senderPl, args.patientNum)
    if not patientPl then return end
    local limbName = ValidLimb(args.limbName) and args.limbName or nil
    local fx = PostOp.SanitizeEffects(args.fx)
    PostOp.ApplyEffects(patientPl, limbName, fx)
end

--* XP

---@param args relayAddXpParams
function ServerRelayCommands.RelayAddXp(playerObj, args)
    if type(args) ~= "table" or type(args.perkName) ~= "string" or type(args.xp) ~= "number" then return end
    if not Perks[args.perkName] or (args.perkName ~= "Side_L" and args.perkName ~= "Side_R" and args.perkName ~= "ProstFamiliarity") then return end
    addXp(playerObj, Perks[args.perkName], math.max(0, math.min(args.xp, 50)))
end

--* TRAITS *--

---@param args relayApplyTraitAmputationParams
function ServerRelayCommands.RelayApplyTraitAmputation(playerObj, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    if not StaticData.TRAITS_BP then return end
    local allowed = false
    for _, limb in pairs(StaticData.TRAITS_BP) do if limb == args.limbName then allowed = true end end
    if not allowed then return end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(playerObj:getUsername())
    if not dcInst or dcInst:getIsCut(args.limbName) then return end

    local AmputationHandler = require("TOC/Handlers/AmputationHandler")
    AmputationHandler:new(playerObj, playerObj, args.limbName):execute(false)
    dcInst:setCicatrizationTime(args.limbName, 0)
    dcInst:setIsCicatrized(args.limbName, true)
    dcInst:plus().shockUntil = 0
    dcInst:plus().convalescenceUntil = 0
    dcInst:apply(playerObj)
    local ItemsController = require("TOC/Controllers/ItemsController")
    ItemsController.Player.OverrideAmputationItemVisuals(playerObj, args.limbName, true)
    -- a character who starts without a leg starts with a crutch (without one they can only crawl)
    if string.find(args.limbName, "Leg_", 1, true) or string.find(args.limbName, "Foot_", 1, true) then
        local inv = playerObj:getInventory()
        if not inv:containsTypeRecurse("TOC.Crutch") then
            local crutch = inv:AddItem("TOC.Crutch")
            if crutch and isServer() and sendAddItemToContainer then sendAddItemToContainer(inv, crutch) end
        end
    end
end

--* PROSTHESES *--

---@param args relayProsthesisStateParams
function ServerRelayCommands.RelayProsthesisState(playerObj, args)
    if type(args) ~= "table" or type(args.group) ~= "string" then return end
    local username = playerObj:getUsername()
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(username)
    if not dcInst or not StaticData.AMP_GROUPS_IND_STR[args.group] then return end

    local isEquipped = args.isEquipped == true
    local prostType = type(args.prostType) == "string" and StaticData.GetProsthesisTier(args.prostType) and args.prostType or nil
    dcInst:setIsProstEquipped(args.group, isEquipped)
    dcInst:setProstType(args.group, isEquipped and prostType or nil)
    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    CachedDataHandler.CalculateCacheableValues(username)
    dcInst:apply(playerObj)
    -- the client needs the new hand/leg feasibility right away (mobility, equip rules)
    CachedDataHandler.SendCache(playerObj, username, false)

    if not isEquipped then
        local highest = CachedDataHandler.GetHighestAmputatedLimbs(username)
        if highest and highest[args.group] then
            triggerEvent("OnProsthesisUnequipped", playerObj, highest[args.group])
        end
    end
end

---@param args relayProsthesisWearParams
function ServerRelayCommands.RelayProsthesisWear(playerObj, args)
    if type(args) ~= "table" or type(args.group) ~= "string" or type(args.wear) ~= "number" then return end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(playerObj:getUsername())
    if not dcInst or not StaticData.AMP_GROUPS_IND_STR[args.group] then return end
    dcInst:setProstWear(args.group, args.wear)
end

--* ZOMBIES *--

---@param args relayZombieCrawlerParams
function ServerRelayCommands.RelayZombieCrawler(playerObj, args)
    if type(args) ~= "table" or type(args.zombieID) ~= "number" then return end
    if not isServer() then return end
    pcall(function()
        local list = getCell():getZombieList()
        for i = 0, list:size() - 1 do
            local z = list:get(i)
            if z and z:getOnlineID() == args.zombieID then
                if Near(playerObj, z, 6) and not z:isCrawling() then
                    z:toggleCrawling()
                    sendServerCommand(CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveZombieCrawler, {zombieID = args.zombieID})
                end
                return
            end
        end
    end)
end

--* ADMIN ONLY *--

---@param args relayExecuteInitializationParams
function ServerRelayCommands.RelayExecuteInitialization(adminObj, args)
    if type(args) ~= "table" then return end
    local patientPl = CommonMethods.GetPatientForServer(args.patientNum)
    if not patientPl then return end
    if patientPl ~= adminObj and not IsAdmin(adminObj) then return end
    local key = CommandsData.GetKey(patientPl:getUsername())
    ModData.remove(key)
    sendServerCommand(patientPl, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveExecuteInitialization, {})
end

---@param args relayForcedAmputationParams
function ServerRelayCommands.RelayForcedAmputation(adminObj, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    if not IsAdmin(adminObj) then return end
    local patientPl = CommonMethods.GetPatientForServer(args.patientNum)
    if not patientPl then return end
    local DataController = require("TOC/Controllers/DataController")
    local h = DataController.GetReady(patientPl:getUsername())
    if h and h:getIsCut(args.limbName) then return end
    local AmputationHandler = require("TOC/Handlers/AmputationHandler")
    AmputationHandler:new(adminObj, patientPl, args.limbName):execute(false)
    h = DataController.GetReady(patientPl:getUsername())
    if h then
        h:setCicatrizationTime(args.limbName, 0)
        h:setIsCicatrized(args.limbName, true)
        h:apply(patientPl)
        local ItemsController = require("TOC/Controllers/ItemsController")
        ItemsController.Player.OverrideAmputationItemVisuals(patientPl, args.limbName, true)
    end
end

---@param args requestSanitizeCutLimbParams
function ServerRelayCommands.RequestSanitizeCutLimb(playerObj, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) then return end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(playerObj:getUsername())
    if not dcInst or not dcInst:getIsCut(args.limbName) then return end
    local ServerDamageSanitizer = require("TOC/Controllers/ServerDamageSanitizer")
    local ok, err = pcall(ServerDamageSanitizer.SanitizePlayer, playerObj)
    if not ok then TOC_DEBUG.print("RequestSanitizeCutLimb error: " .. tostring(err)) end
end

---@param args relayTriggerBleedParams
function ServerRelayCommands.RelayTriggerBleed(playerObj, args)
    if type(args) ~= "table" or not ValidLimb(args.limbName) or type(args.bleedingTime) ~= "number" then return end
    if playerObj:getOnlineID() ~= args.patientNum then return end
    local adjacentBodyPartType = BodyPartType[StaticData.LIMBS_ADJACENT_IND_STR[args.limbName]]
    local bp = playerObj:getBodyDamage():getBodyPart(adjacentBodyPartType)
    if bp then
        bp:setBleeding(true)
        bp:setBleedingTime(math.max(1, math.min(60, args.bleedingTime)))
        if isServer() then pcall(function() syncBodyPart(bp, 0xFFFFFFFFFFF) end) end
    end
end

function ServerRelayCommands.DeleteAllOldAmputationItems(playerObj, args)
    if type(args) ~= "table" then return end
    local patientPl = CommonMethods.GetPatientForServer(args.patientNum)
    if not patientPl or (patientPl ~= playerObj and not IsAdmin(playerObj)) then return end
    local ItemsController = require("TOC/Controllers/ItemsController")
    ItemsController.Player.DeleteAllOldAmputationItems(patientPl)
end

function ServerRelayCommands.SendCache(playerObj, args)
    if type(args) ~= "table" or type(args.patientUsername) ~= "string" then return end
    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    CachedDataHandler.SendCache(playerObj, args.patientUsername, args.recalculate == true)
end

-------------------------

local function OnClientRelayCommand(module, command, playerObj, args)
    if module == CommandsData.modules.TOC_RELAY and ServerRelayCommands[command] then
        local ok, err = pcall(ServerRelayCommands[command], playerObj, args)
        if not ok then print("[TOC+] relay '" .. tostring(command) .. "' failed: " .. tostring(err)) end
    end
end

Events.OnClientCommand.Add(OnClientRelayCommand)

return ServerRelayCommands
