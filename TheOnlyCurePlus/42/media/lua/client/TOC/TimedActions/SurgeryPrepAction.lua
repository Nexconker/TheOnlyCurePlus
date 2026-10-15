require "TimedActions/ISBaseTimedAction"
local StaticData = require("TOC/StaticData")
local CommandsData = require("TOC/CommandsData")
local PostOp = require("TOC/Plus/PostOp")
-----------------------------

-- TOC+: disinfect the area before cutting. Consumes the disinfectant like vanilla ISDisinfect.
---@class SurgeryPrepAction : ISBaseTimedAction
local SurgeryPrepAction = ISBaseTimedAction:derive("SurgeryPrepAction")

---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param disinfectItem InventoryItem
function SurgeryPrepAction:new(surgeon, patient, limbName, disinfectItem)
    local o = ISBaseTimedAction.new(self, surgeon)
    o.character = surgeon
    o.patient = patient
    o.limbName = limbName
    o.item = disinfectItem
    o.patientX = patient:getX()
    o.patientY = patient:getY()
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = surgeon:isTimedActionInstant() and 1 or math.max(60, 180 - surgeon:getPerkLevel(Perks.Doctor) * 10)
    return o
end

function SurgeryPrepAction:isValid()
    if not self.item or not self.character:getInventory():contains(self.item) then return false end
    return not ISHealthPanel.DidPatientMove(self.character, self.patient, self.patientX, self.patientY)
end

function SurgeryPrepAction:waitToStart()
    if self.character == self.patient then return false end
    self.character:faceThisObject(self.patient)
    return self.character:shouldBeTurning()
end

function SurgeryPrepAction:start()
    if self.character == self.patient then
        self:setActionAnim(CharacterActionAnims.Bandage)
        pcall(function() self:setAnimVariable("BandageType", "Hand") end)
    else
        self:setActionAnim("Loot")
        self.character:SetVariable("LootPosition", "Mid")
    end
    pcall(function() self:setOverrideHandModels(nil, self.item) end)
    self.sound = self.character:playSound("FirstAidApplyAlcohol")
end

function SurgeryPrepAction:update()
    self.character:setMetabolicTarget(Metabolics.LightDomestic)
end

function SurgeryPrepAction:stop()
    if self.sound then self.character:getEmitter():stopSound(self.sound) end
    ISBaseTimedAction.stop(self)
end

function SurgeryPrepAction:perform()
    if self.sound then self.character:getEmitter():stopSound(self.sound) end
    local power = StaticData.DISINFECTANT_TYPES[self.item:getFullType()] or 0.5
    -- consume
    pcall(function()
        if self.item:hasComponent(ComponentType.FluidContainer) then
            local fc = self.item:getFluidContainer()
            if fc:getAmount() > 0.15 then fc:adjustAmount(fc:getAmount() - 0.15) end
            sendItemStats(self.item)
        elseif instanceof(self.item, "DrainableComboItem") then
            self.item:UseAndSync()
        else
            self.item:getContainer():Remove(self.item)
            sendRemoveItemFromContainer(self.character:getInventory(), self.item)
        end
    end)
    -- alcohol on the part that will stay + a little pain
    local fx = { alcohol = power * 2, pain = 5 }
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayPostOpApply,
            {patientNum = self.patient:getOnlineID(), limbName = self.limbName, fx = fx})
    else
        PostOp.ApplyEffects(self.patient, self.limbName, fx)
    end
    self.character:getXp():AddXP(Perks.Doctor, 3)
    ISBaseTimedAction.perform(self)
end

return SurgeryPrepAction
