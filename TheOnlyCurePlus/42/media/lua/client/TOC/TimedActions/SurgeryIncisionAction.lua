require "TimedActions/ISBaseTimedAction"
local CommandsData = require("TOC/CommandsData")
local PostOp = require("TOC/Plus/PostOp")
-----------------------------

-- TOC+: the incision with a blade before the saw. Cosmetic step with a bit of pain and XP;
-- its real effect is already in the risk (a clean incision closes better).
---@class SurgeryIncisionAction : ISBaseTimedAction
local SurgeryIncisionAction = ISBaseTimedAction:derive("SurgeryIncisionAction")

---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param bladeItem InventoryItem
function SurgeryIncisionAction:new(surgeon, patient, limbName, bladeItem)
    local o = ISBaseTimedAction.new(self, surgeon)
    o.character = surgeon
    o.patient = patient
    o.limbName = limbName
    o.item = bladeItem
    o.patientX = patient:getX()
    o.patientY = patient:getY()
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = surgeon:isTimedActionInstant() and 1 or math.max(80, 220 - surgeon:getPerkLevel(Perks.Doctor) * 12)
    return o
end

function SurgeryIncisionAction:isValid()
    if not self.item or not self.character:getInventory():contains(self.item) then return false end
    return not ISHealthPanel.DidPatientMove(self.character, self.patient, self.patientX, self.patientY)
end

function SurgeryIncisionAction:waitToStart()
    if self.character == self.patient then return false end
    self.character:faceThisObject(self.patient)
    return self.character:shouldBeTurning()
end

function SurgeryIncisionAction:start()
    self:setActionAnim("Loot")
    self.character:SetVariable("LootPosition", "Mid")
    pcall(function() self:setOverrideHandModels(self.item:getStaticModel()) end)
    if not pcall(function() self.patient:playerVoiceSound("PainFromLacerate") end) then
        pcall(function() self.patient:getEmitter():playSound("TOC_Groan") end)
    end
    addSound(self.patient, self.patient:getX(), self.patient:getY(), self.patient:getZ(), 4, 4)
end

function SurgeryIncisionAction:update()
    self.character:setMetabolicTarget(Metabolics.LightWork)
end

function SurgeryIncisionAction:perform()
    local fx = { pain = 8 }
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayPostOpApply,
            {patientNum = self.patient:getOnlineID(), limbName = self.limbName, fx = fx})
    else
        PostOp.ApplyEffects(self.patient, self.limbName, fx)
    end
    pcall(function() addBloodSplat(self.patient:getSquare(), 3) end)
    self.character:getXp():AddXP(Perks.Doctor, 5)
    ISBaseTimedAction.perform(self)
end

return SurgeryIncisionAction
