local BaseHandler = require("TOC/UI/Interactions/HealthPanelBaseHandler")
local ExamineWoundAction = require("TOC/TimedActions/ExamineWoundAction")
local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
-------------------------

-- TOC+: "Examine wound" on a bitten / scratched / lacerated body part.
---@class ExamineWoundInteractionHandler : BaseHandler
local ExamineWoundInteractionHandler = BaseHandler:derive("ExamineWoundInteractionHandler")

function ExamineWoundInteractionHandler:new(panel, bodyPart)
    local o = BaseHandler.new(self, panel, bodyPart)
    o.items.ITEMS = {}
    return o
end

function ExamineWoundInteractionHandler:checkItem(item) end

function ExamineWoundInteractionHandler:isWoundExaminable()
    local bp = self.bodyPart
    local ok, res = pcall(function()
        return bp:bitten() or bp:scratched() or bp:isCut() or bp:isDeepWounded()
    end)
    return ok and res == true
end

function ExamineWoundInteractionHandler:addToMenu(context)
    if not self:isWoundExaminable() then return end
    local doctor = self:getDoctor()
    local minLevel = (SandboxVars.TOC and SandboxVars.TOC.DiagnosisMinDoctor) or 2
    local allowed = doctor:getPerkLevel(Perks.Doctor) >= minLevel or SurgeryPlan.KnowsSurgery(doctor)
    local option = context:addOption(getText("ContextMenu_TOC_ExamineWound"), self, self.onMenuOptionSelected)
    if not allowed then
        option.notAvailable = true
        local tip = ISToolTip:new(); tip:initialise(); tip:setVisible(false)
        tip.description = getText("Tooltip_TOC_NeedDoctor", tostring(minLevel))
        option.toolTip = tip
    end
end

function ExamineWoundInteractionHandler:isValid()
    return self:isWoundExaminable()
end

function ExamineWoundInteractionHandler:perform(previousAction)
    local action = ExamineWoundAction:new(self:getDoctor(), self:getPatient(), self.bodyPart)
    ISTimedActionQueue.addAfter(previousAction, action)
end

return ExamineWoundInteractionHandler
