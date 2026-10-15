local BaseHandler = require("TOC/UI/Interactions/HealthPanelBaseHandler")
local CommonMethods = require("TOC/CommonMethods")
local DataController = require("TOC/Controllers/DataController")
local CleanWoundAction = require("TOC/TimedActions/CleanWoundAction")
-------------------------

---@class WoundCleaningInteractionHandler : BaseHandler
local WoundCleaningInteractionHandler = BaseHandler:derive("WoundCleaningInteractionHandler")

function WoundCleaningInteractionHandler:new(panel, bodyPart, username)
    local o = BaseHandler.new(self, panel, bodyPart)
    o.items.ITEMS = {}
    o.username = username
    o.limbName = CommonMethods.GetLimbNameFromBodyPart(bodyPart)
    return o
end

function WoundCleaningInteractionHandler:checkItem(item)
    if CleanWoundAction.CleanPower(item) then
        self:addItem(self.items.ITEMS, item)
    end
end

function WoundCleaningInteractionHandler:addToMenu(context)
    local types = self:getAllItemTypes(self.items.ITEMS)
    if #types > 0 and self:isValid() then
        local option = context:addOption(getText("ContextMenu_CleanWound"), nil)
        local subMenu = context:getNew(context)
        context:addSubMenu(option, subMenu)
        for i = 1, #types do
            local item = self:getItemOfType(self.items.ITEMS, types[i])
            subMenu:addOption(item:getDisplayName(), self, self.onMenuOptionSelected, item:getFullType())
        end
    end
end

function WoundCleaningInteractionHandler:dropItems(items)
    local types = self:getAllItemTypes(items)
    if #self.items.ITEMS > 0 and #types == 1 and self:isActionValid() then
        self:onMenuOptionSelected(types[1])
        return true
    end
    return false
end

function WoundCleaningInteractionHandler:isValid()
    self:checkItems()
    return self:isActionValid()
end

function WoundCleaningInteractionHandler:isActionValid()
    if self.limbName == nil then return false end
    local dcInst = DataController.GetReady(self.username)
    if not dcInst then return false end
    return dcInst:getIsCut(self.limbName) and dcInst:getIsVisible(self.limbName) and not dcInst:getIsCicatrized(self.limbName)
        and (dcInst:getWoundDirtyness(self.limbName) > 0 or dcInst:getSepsis(self.limbName) > 0)
end

function WoundCleaningInteractionHandler:perform(previousAction, itemType)
    local item = self:getItemOfType(self.items.ITEMS, itemType)
    previousAction = self:toPlayerInventory(item, previousAction)
    local action = CleanWoundAction:new(self:getDoctor(), self:getPatient(), item, self.bodyPart)
    ISTimedActionQueue.addAfter(previousAction, action)
end

return WoundCleaningInteractionHandler
