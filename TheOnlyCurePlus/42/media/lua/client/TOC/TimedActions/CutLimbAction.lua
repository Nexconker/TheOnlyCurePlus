require "TimedActions/ISBaseTimedAction"
local AmputationHandler = require("TOC/Handlers/AmputationHandler")
local CommandsData = require("TOC/CommandsData")
local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
local Messages = require("TOC/Plus/Messages")
-----------------------------

-- TOC+: the "bone" step of the surgery. Screams attract zombies, the patient can faint,
-- and the outcome is rolled on the authoritative side from the plan.
---@class CutLimbAction : ISBaseTimedAction
---@field patient IsoPlayer
---@field character IsoPlayer
---@field limbName string
---@field item InventoryItem
---@field plan table
---@field risk table
local CutLimbAction = ISBaseTimedAction:derive("CutLimbAction")

---Voz vanilla del jugador (los mismos gritos que al ser mordido); si falla, el wav propio.
local function Voice(char, voiceName, fallback)
    local ok = pcall(function() char:playerVoiceSound(voiceName) end)
    if not ok and fallback then pcall(function() char:getEmitter():playSound(fallback) end) end
end


---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param item InventoryItem the saw
---@param stitchesItem InventoryItem?
---@param bandageItem InventoryItem?
---@param plan table?
---@param risk table?
---@return CutLimbAction
function CutLimbAction:new(surgeon, patient, limbName, item, stitchesItem, bandageItem, plan, risk)
    local o = ISBaseTimedAction.new(self, surgeon)
    o.character = surgeon
    o.patient = patient
    o.limbName = limbName
    o.item = item
    o.patientX = patient:getX()
    o.patientY = patient:getY()
    o.stitchesItem = stitchesItem or nil
    o.bandageItem = bandageItem or nil
    o.plan = plan or SurgeryPlan.Gather(surgeon, patient, limbName, item)
    o.risk = risk or SurgeryPlan.Risk(o.plan)
    o.screamAt = { 0.04, 0.38, 0.72 }
    o.screamIdx = 1
    o.faintRolled = false
    o.botched = false
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = o:getDuration()
    return o
end

function CutLimbAction:getDuration()
    if self.character:isTimedActionInstant() then return 1 end
    local baseTime = 1000
    local perkLevel = self.character:getPerkLevel(Perks.Doctor)
    local tierMult = ({ [0] = 0.8, [1] = 1.0, [2] = 1.15, [3] = 0.9 })[self.plan.toolTier or 1] or 1.0
    if self.plan.knows then tierMult = tierMult * 0.9 end
    return math.max(200, (baseTime - perkLevel * 50) * tierMult)
end

function CutLimbAction:isValid()
    if not self.patient or self.patient:isDead() then return false end
    return not ISHealthPanel.DidPatientMove(self.character, self.patient, self.patientX, self.patientY)
end

function CutLimbAction:waitToStart()
    if self.character == self.patient then return false end
    self.character:faceThisObject(self.patient)
    return self.character:shouldBeTurning()
end

function CutLimbAction:start()
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayDamageDuringAmputation,
            {patientNum = self.patient:getOnlineID(), limbName = self.limbName})
    else
        AmputationHandler.ApplyDamageDuringAmputation(self.patient, self.limbName)
    end

    ---@type ISBaseTimedAction
    local prevAction = self
    if self.stitchesItem then
        prevAction = AmputationHandler.PrepareStitchesAction(prevAction, self.limbName, self.character, self.patient, self.stitchesItem)
    end
    if self.bandageItem then
        prevAction = AmputationHandler.PrepareBandagesAction(prevAction, self.limbName, self.character, self.patient, self.bandageItem)
    end

    self:setActionAnim("SawLog")
    pcall(function()
        -- el kit quirúrgico lleva la sierra dentro: en la mano se ve la sierra, no el botiquín
        local model = self.item:getFullType() == "TOC.SurgicalKit" and "BoneSaw" or self.item:getStaticModel()
        self:setOverrideHandModels(model)
    end)

    self.sound = self.character:getEmitter():playSound("TOC_Amputation")
    addSound(self.character, self.character:getX(), self.character:getY(), self.character:getZ(), 5, 5)
end

function CutLimbAction:scream()
    local pain = self.risk.painLevel or 1
    local emitter = self.patient:getEmitter()
    if pain > 0.2 then
        Voice(self.patient, "PainFromBite", self.patient:isFemale() and "TOC_ScreamFemale" or "TOC_ScreamMale")
        local radius = math.max(4, self.risk.noiseRadius or 20)
        addSound(self.patient, self.patient:getX(), self.patient:getY(), self.patient:getZ(), radius, radius)
        local stats = self.patient:getStats()
        stats:set(CharacterStat.PANIC, math.min(100, (stats:get(CharacterStat.PANIC) or 0) + 30 * pain))
    else
        Voice(self.patient, "PainFromScratch", "TOC_Groan")
        addSound(self.patient, self.patient:getX(), self.patient:getY(), self.patient:getZ(), 3, 3)
    end
end

function CutLimbAction:tryFaint()
    self.faintRolled = true
    if ZombRandFloat(0.0, 1.0) >= (self.risk.faintChance or 0) then return end
    pcall(function() self.patient:getEmitter():playSound("TOC_Thud") end)
    local stats = self.patient:getStats()
    stats:set(CharacterStat.PANIC, 100)
    stats:set(CharacterStat.ENDURANCE, 0)
    pcall(function() self.patient:setKnockedDown(true) end)
    if self.character == self.patient then
        -- nobody holds the saw any more: the attempt fails, the limb stays, badly cut
        Messages.Say(self.patient, getText("IGUI_TOC_Fainted_Self"), true)
        self.botched = true
        self:forceStop()
    else
        Messages.Say(self.character, getText("IGUI_TOC_Fainted_Patient"), false)
        self.risk.painLevel = 0      -- out cold: no more screaming
    end
end

function CutLimbAction:update()
    self.character:setMetabolicTarget(Metabolics.HeavyWork)
    if self.character ~= self.patient then
        self.patient:setMetabolicTarget(Metabolics.HeavyWork)
    end
    local progress = self:getJobDelta()
    if self.screamIdx <= #self.screamAt and progress >= self.screamAt[self.screamIdx] then
        self.screamIdx = self.screamIdx + 1
        self:scream()
    end
    if not self.faintRolled and progress >= 0.5 then
        self:tryFaint()
    end
end

function CutLimbAction:stopSound()
    if self.sound then
        self.character:getEmitter():stopSound(self.sound)
        self.sound = nil
    end
end

function CutLimbAction:stop()
    self:stopSound()
    if self.botched then
        if isClient() then
            sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelaySurgeryBotched,
                {patientNum = self.patient:getOnlineID(), limbName = self.limbName})
        else
            AmputationHandler.ApplyBotchedAttempt(self.patient, self.limbName)
        end
    end
    ISBaseTimedAction.stop(self)
end

function CutLimbAction:perform()
    self:stopSound()
    pcall(function() self.character:getEmitter():playSound("TOC_BoneCrack") end)
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayExecuteSurgery,
            {patientNum = self.patient:getOnlineID(), limbName = self.limbName, plan = SurgeryPlan.Pack(self.plan)})
    else
        local outcome = SurgeryPlan.Roll(self.plan, self.risk)
        local handler = AmputationHandler:new(self.character, self.patient, self.limbName)
        handler:execute(true, outcome)
    end
    -- the saw suffers
    pcall(function()
        if self.item and self.item.getCondition and self.item:getCondition() > 0 and ZombRand(3) == 0 then
            self.item:setCondition(self.item:getCondition() - 1)
            if isClient() then self.item:syncItemFields() end
        end
    end)
    ISBaseTimedAction.perform(self)
end

-- 3.1.2: vigilante del sonido de la sierra (en bucle). Si la acción desaparece sin pasar por stop()/perform() (otro mod que
-- limpia la cola, Wounds Expansion / Viewpoint...) el bucle sonaba para siempre ("amputation sound that loops forever").
-- Además el sonido se llamaba "Amputation", un nombre genérico que otro mod podía disparar: ahora es TOC_Amputation.
local watchTick = 0
Events.OnPlayerUpdate.Add(function(player)
    if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
    watchTick = watchTick + 1
    if watchTick % 60 ~= 0 then return end
    pcall(function()
        local emitter = player:getEmitter()
        if not emitter or not emitter:isPlaying("TOC_Amputation") then return end
        local q = ISTimedActionQueue.getTimedActionQueue(player)
        local cur = q and q.queue and q.queue[1]
        if cur and cur.Type == "CutLimbAction" then return end
        emitter:stopSoundByName("TOC_Amputation")
    end)
end)

return CutLimbAction
