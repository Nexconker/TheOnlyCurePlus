local CommandsData = require("TOC/CommandsData")
local StaticData = require("TOC/StaticData")
local PostOp = require("TOC/Plus/PostOp")
---------------------------

LuaEventManager.AddEvent("OnAmputatedLimb")     -- Triggered when a limb is amputated; args: playerObj, limbName

--- Manages an amputation. Runs on the authoritative side (server in MP, anywhere in SP).
---@class AmputationHandler
---@field surgeonPl IsoPlayer
---@field patientPl IsoPlayer
---@field limbName string
---@field bodyPartType BodyPartType
local AmputationHandler = {}

---@param surgeonPl IsoPlayer
---@param patientPl IsoPlayer
---@param limbName string
---@return AmputationHandler
function AmputationHandler:new(surgeonPl, patientPl, limbName)
    local o = {}
    setmetatable(o, self)
    self.__index = self
    o.patientPl = patientPl
    o.surgeonPl = surgeonPl or patientPl
    o.limbName = limbName
    o.bodyPartType = BodyPartType[limbName]
    AmputationHandler.instance = o
    return o
end

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

--* Static methods *--

---Bleeding while the saw is working. Authoritative side.
---@param player IsoPlayer
---@param limbName string
function AmputationHandler.ApplyDamageDuringAmputation(player, limbName)
    if not player or not BodyPartType[limbName] then return end
    local TourniquetController = require("TOC/Controllers/TourniquetController")
    local isTourniquetEquipped = TourniquetController.CheckTourniquetOnLimb(player, limbName)

    local bodyDamage = player:getBodyDamage()
    local bodyDamagePart = bodyDamage:getBodyPart(BodyPartType[limbName])
    bodyDamagePart:setBleeding(true)
    bodyDamagePart:setCut(true)
    bodyDamagePart:setBleedingTime(isTourniquetEquipped and ZombRand(1, 5) or ZombRand(10, 20))
    if isServer() then pcall(function() syncBodyPart(bodyDamagePart, 0xFFFFFFFFFFF) end) end
end

---A failed self-surgery (fainted half way): the limb stays, badly hurt. Authoritative side.
---@param player IsoPlayer
---@param limbName string
function AmputationHandler.ApplyBotchedAttempt(player, limbName)
    if not player or not BodyPartType[limbName] then return end
    local bd = player:getBodyDamage()
    local part = bd:getBodyPart(BodyPartType[limbName])
    part:setDeepWounded(true)
    part:setDeepWoundTime(40)
    part:setBleeding(true)
    part:setBleedingTime(25)
    part:AddDamage(35)
    part:setAdditionalPain(60)
    local stats = player:getStats()
    stats:set(CharacterStat.PANIC, 100)
    if isServer() then pcall(function() syncBodyPart(part, 0xFFFFFFFFFFF) end) end
    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetReady(player:getUsername())
    if dcInst then
        dcInst:plus().botched[limbName] = PostOp.Now()
        dcInst:apply(player)
    end
end

---@param prevAction ISBaseTimedAction
function AmputationHandler.PrepareStitchesAction(prevAction, limbName, surgeonPl, patientPl, stitchesItem)
    local bd = patientPl:getBodyDamage()
    local adjacentLimb = StaticData.LIMBS_ADJACENT_IND_STR[limbName]
    local bodyPart = bd:getBodyPart(BodyPartType[adjacentLimb])
    local stitchesAction = ISStitch:new(surgeonPl, patientPl, stitchesItem, bodyPart, true)
    ISTimedActionQueue.addAfter(prevAction, stitchesAction)
    return stitchesAction
end

---@param prevAction ISBaseTimedAction
function AmputationHandler.PrepareBandagesAction(prevAction, limbName, surgeonPl, patientPl, bandageItem)
    local bd = patientPl:getBodyDamage()
    local adjacentLimb = StaticData.LIMBS_ADJACENT_IND_STR[limbName]
    local bodyPart = bd:getBodyPart(BodyPartType[adjacentLimb])
    local bandageAction = ISApplyBandage:new(surgeonPl, patientPl, bandageItem, bodyPart, true)
    ISTimedActionQueue.addAfter(prevAction, bandageAction)
    return bandageAction
end

---@param player IsoPlayer
---@param itemName string
function AmputationHandler.WearAmputationItem(player, itemName)
    local clothingItem = player:getInventory():FindAndReturn(itemName)
    if clothingItem then
        player:setWornItem(clothingItem:getBodyLocation(), clothingItem)
        player:resetModelNextFrame()
    end
end

---Heal the cut area (the body part no longer exists)
function AmputationHandler:healArea()
    local bd = self.patientPl:getBodyDamage()
    local bodyPart = bd:getBodyPart(self.bodyPartType)
    bodyPart:RestoreToFullHealth()
    pcall(function()
        bodyPart:SetBitten(false); bodyPart:setBiteTime(0)
        bodyPart:SetInfected(false); bodyPart:setInfectedWound(false)
        bodyPart:setScratched(false, true); bodyPart:setScratchTime(0)
        bodyPart:setCut(false); bodyPart:setCutTime(0)
        bodyPart:setDeepWounded(false); bodyPart:setDeepWoundTime(0)
        bodyPart:setBleeding(false); bodyPart:setBleedingTime(0)
        bodyPart:setFractureTime(0)
    end)
    if isServer() then pcall(function() syncBodyPart(bodyPart, 0xFFFFFFFFFFF) end) end
end

---The whole point of the mod. TOC+: configurable window and a late gamble.
---@param isPartInfected boolean a bite on a body part that cannot be cut
---@return string outcome "none" | "cured" | "late" | "doomed"
function AmputationHandler:healInfection(isPartInfected)
    local plStats = self.patientPl:getStats()
    local bd = self.patientPl:getBodyDamage()
    if isPartInfected then return "doomed" end
    if not bd:isInfected() then return "none" end

    local infectionLevel = plStats:get(CharacterStat.ZOMBIE_INFECTION) or 0
    local window = sv("CureWindow", 20)
    local gamble = sv("LateGambleWindow", 40)

    local cured = false
    if infectionLevel < window then
        cured = true
    elseif gamble > window and infectionLevel < gamble then
        local p = 1 - (infectionLevel - window) / (gamble - window)
        cured = ZombRandFloat(0.0, 1.0) < p
        TOC_DEBUG.print("Late gamble: level " .. tostring(infectionLevel) .. " p=" .. tostring(p) .. " cured=" .. tostring(cured))
    end

    if cured then
        plStats:set(CharacterStat.ZOMBIE_INFECTION, 0)
        bd:setInfected(false)
        bd:setInfectionMortalityDuration(-1)
        bd:setInfectionTime(-1)
        pcall(function() plStats:set(CharacterStat.ZOMBIE_FEVER, 0) end)
        return "cured"
    end
    return "late"
end

--* Main methods *--

---Damage to the part next to the cut. TOC+: outcome scales it.
---@param surgeonFactor number
---@param outcome table
function AmputationHandler:damageAfterAmputation(surgeonFactor, outcome)
    local patientStats = self.patientPl:getStats()
    local bd = self.patientPl:getBodyDamage()

    local adjacentLimb = StaticData.LIMBS_ADJACENT_IND_STR[self.limbName]
    local bodyPart = bd:getBodyPart(BodyPartType[adjacentLimb])
    local baseDamage = StaticData.LIMBS_BASE_DAMAGE_IND_NUM[self.limbName]

    local TourniquetController = require("TOC/Controllers/TourniquetController")
    if TourniquetController.CheckTourniquetOnLimb(self.patientPl, self.limbName) then
        baseDamage = baseDamage * 0.5
    end
    baseDamage = baseDamage * (outcome.damageMult or 1) + (outcome.extraDamage or 0)
    local dmg = math.max(5, baseDamage - surgeonFactor)

    bodyPart:AddDamage(dmg)
    bodyPart:setAdditionalPain(math.min(100, dmg))
    bodyPart:setBleeding(true)
    bodyPart:setBleedingTime(math.max(2, dmg * (outcome.bleedMult or 1)))
    bodyPart:setDeepWounded(true)
    bodyPart:setDeepWoundTime(math.max(2, dmg * 0.8))

    -- Original TOC assigned ENDURANCE = surgeonFactor (a 0..30 number into a 0..1 stat). Fixed.
    local endurance = patientStats:get(CharacterStat.ENDURANCE) or 1
    patientStats:set(CharacterStat.ENDURANCE, math.max(0, endurance - 0.45))
    local stress = patientStats:get(CharacterStat.STRESS) or 0
    patientStats:set(CharacterStat.STRESS, math.min(1, stress + 0.5))
    patientStats:set(CharacterStat.PANIC, 100)

    if isServer() then pcall(function() syncBodyPart(bodyPart, 0xFFFFFFFFFFF) end) end
end

---Drop the severed limb on the floor next to the patient (authoritative side)
function AmputationHandler:dropSeveredLimb()
    if not sv("DropSeveredLimbs", true) then return end
    local itemType = StaticData.LIMBS_SEVERED_ITEM_IND_STR[self.limbName]
    if not itemType then return end
    local sq = self.patientPl:getSquare()
    if not sq then return end
    pcall(function()
        sq:AddWorldInventoryItem(itemType, ZombRandFloat(0.2, 0.8), ZombRandFloat(0.2, 0.8), 0)
        addBloodSplat(sq, 6)
    end)
end

--- Execute the amputation. Checks must be made BEFORE running the AmputationHandler.
---@param damagePlayer boolean
---@param outcome table? {severity, cicMult, dirt0, bleedMult, extraDamage, damageMult}
---@return string cureOutcome
function AmputationHandler:execute(damagePlayer, outcome)
    outcome = outcome or { severity = 0, cicMult = 1, dirt0 = 0.1, bleedMult = 1, extraDamage = 0, damageMult = 1 }
    local surgeonFactor = self.surgeonPl:getPerkLevel(Perks.Doctor) * (sv("SurgeonAbilityImportance", 2))
    local patientUsername = self.patientPl:getUsername()

    local DataController = require("TOC/Controllers/DataController")
    local dcInst = DataController.GetInstance(patientUsername)
    if not dcInst or not dcInst:getIsDataReady() then
        local ServerDataController = require("TOC/Controllers/ServerDataController")
        dcInst = ServerDataController.GetOrCreate(patientUsername, self.patientPl)
    end
    dcInst:setCutLimb(self.limbName, false, false, false, surgeonFactor, outcome.cicMult, outcome.dirt0)
    local cureOutcome = self:healInfection(dcInst:getIsIgnoredPartInfected())
    dcInst:plus().cureOutcome = cureOutcome
    if damagePlayer then PostOp.StartAfterSurgery(dcInst, outcome.severity or 0) end

    dcInst:apply(self.patientPl)

    local ItemsController = require("TOC/Controllers/ItemsController")
    ItemsController.Player.DeleteOldAmputationItem(self.patientPl, self.limbName)
    ItemsController.Player.SpawnAmputationItem(self.patientPl, self.limbName)

    triggerEvent("OnAmputatedLimb", self.patientPl, self.limbName)
    for i = 1, #StaticData.LIMBS_DEPENDENCIES_IND_STR[self.limbName] do
        triggerEvent("OnAmputatedLimb", self.patientPl, StaticData.LIMBS_DEPENDENCIES_IND_STR[self.limbName][i])
    end

    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    CachedDataHandler.AddAmputatedLimb(patientUsername, self.limbName)
    for i = 1, #StaticData.LIMBS_DEPENDENCIES_IND_STR[self.limbName] do
        CachedDataHandler.AddAmputatedLimb(patientUsername, StaticData.LIMBS_DEPENDENCIES_IND_STR[self.limbName][i])
    end
    CachedDataHandler.CalculateCacheableValues(patientUsername)

    self:healArea()

    if damagePlayer then
        self:damageAfterAmputation(surgeonFactor, outcome)
        self:dropSeveredLimb()
    end

    if isServer() then
        local cache = CachedDataHandler.GetAll(patientUsername)
        sendServerCommand(self.patientPl, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.FinalizeAmputationAction,
            {patientUsername = patientUsername, cache = cache, limbName = self.limbName, damagePlayer = damagePlayer})
        sendServerCommand(self.patientPl, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveSurgeryResult,
            {limbName = self.limbName, severity = outcome.severity or 0, cure = sv("RevealOutcome", false) and cureOutcome or nil})
        if self.patientPl ~= self.surgeonPl then
            dcInst:apply(self.surgeonPl)
            sendServerCommand(self.surgeonPl, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveCache,
                {patientUsername = patientUsername, cache = cache})
            sendServerCommand(self.surgeonPl, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveSurgeryResult,
                {limbName = self.limbName, severity = outcome.severity or 0, patientUsername = patientUsername})
        end
    else
        -- SP: tell the UI directly
        local Messages = require("TOC/Plus/Messages")
        if Messages then Messages.SurgeryResult(self.patientPl, self.limbName, outcome.severity or 0, sv("RevealOutcome", false) and cureOutcome or nil) end
    end

    return cureOutcome
end

function AmputationHandler:close()
    AmputationHandler.instance = nil
end

return AmputationHandler
