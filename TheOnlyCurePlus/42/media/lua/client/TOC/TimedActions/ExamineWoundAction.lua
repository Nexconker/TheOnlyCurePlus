require "TimedActions/ISBaseTimedAction"
local DataController = require("TOC/Controllers/DataController")
local Messages = require("TOC/Plus/Messages")
local PostOp = require("TOC/Plus/PostOp")
-----------------------------

-- TOC+: examine a bite / scratch / laceration and get a (fallible) opinion on whether it is
-- the Knox infection. Better doctors and more advanced infections give clearer answers.
---@class ExamineWoundAction : ISBaseTimedAction
local ExamineWoundAction = ISBaseTimedAction:derive("ExamineWoundAction")

---@param doctor IsoPlayer
---@param patient IsoPlayer
---@param bodyPart BodyPart
function ExamineWoundAction:new(doctor, patient, bodyPart)
    local o = ISBaseTimedAction.new(self, doctor)
    o.character = doctor
    o.patient = patient
    o.bodyPart = bodyPart
    o.patientX = patient:getX()
    o.patientY = patient:getY()
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = doctor:isTimedActionInstant() and 1 or math.max(60, 250 - doctor:getPerkLevel(Perks.Doctor) * 15)
    return o
end

function ExamineWoundAction:isValid()
    return not ISHealthPanel.DidPatientMove(self.character, self.patient, self.patientX, self.patientY)
end

function ExamineWoundAction:waitToStart()
    if self.character == self.patient then return false end
    self.character:faceThisObject(self.patient)
    return self.character:shouldBeTurning()
end

function ExamineWoundAction:start()
    self:setActionAnim("Loot")
    self.character:SetVariable("LootPosition", "Mid")
    pcall(function() self:setOverrideHandModels(nil, nil) end)
end

function ExamineWoundAction:update()
    local jobType = getText("ContextMenu_TOC_ExamineWound")
    ISHealthPanel.setBodyPartActionForPlayer(self.patient, self.bodyPart, self, jobType, {})
    self.character:setMetabolicTarget(Metabolics.LightDomestic)
end

function ExamineWoundAction:stop()
    ISHealthPanel.setBodyPartActionForPlayer(self.patient, self.bodyPart, nil, nil, nil)
    ISBaseTimedAction.stop(self)
end

---@return string verdict "infected" | "clean" | "unsure"
function ExamineWoundAction:computeVerdict()
    local doctorLevel = self.character:getPerkLevel(Perks.Doctor)
    local truth = false
    pcall(function() truth = self.bodyPart:IsInfected() == true end)
    local level = 0
    if self.patient:isLocalPlayer() then
        level = self.patient:getStats():get(CharacterStat.ZOMBIE_INFECTION) or 0
    else
        level = 10
    end
    local visibility = math.min(0.3, level / 100)
    local accuracy = math.min(0.95, 0.5 + 0.045 * doctorLevel + visibility)
    local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
    if SurgeryPlan.KnowsSurgery(self.character) then accuracy = math.min(0.97, accuracy + 0.1) end
    if ZombRandFloat(0.0, 1.0) < accuracy then
        return truth and "infected" or "clean"
    end
    if ZombRand(2) == 0 then return "unsure" end
    return truth and "clean" or "infected"
end

function ExamineWoundAction:perform()
    ISHealthPanel.setBodyPartActionForPlayer(self.patient, self.bodyPart, nil, nil, nil)
    local verdict = self:computeVerdict()
    local doctorLevel = self.character:getPerkLevel(Perks.Doctor)
    local confident = doctorLevel >= 4
    local key = "IGUI_TOC_Diag_" .. verdict .. (confident and "" or "_Maybe")
    Messages.Say(self.character, getText(key), verdict == "infected")

    local dcInst = DataController.GetReady(self.patient:getUsername())
    if dcInst then
        local partName = BodyPartType.ToString(self.bodyPart:getType())
        dcInst:plus().lastDiagnosis[partName] = { verdict = verdict, hours = PostOp.Now(), confident = confident }
        if self.patient:isLocalPlayer() then dcInst:updatePlusFromClient() end
    end
    self.character:getXp():AddXP(Perks.Doctor, 4)
    ISBaseTimedAction.perform(self)
end

return ExamineWoundAction
