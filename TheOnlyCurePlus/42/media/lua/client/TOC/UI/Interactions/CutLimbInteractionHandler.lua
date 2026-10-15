local BaseHandler = require("TOC/UI/Interactions/HealthPanelBaseHandler")
local StaticData = require("TOC/StaticData")
local DataController = require("TOC/Controllers/DataController")
local SurgeryWindow = require("TOC/UI/SurgeryWindow")
local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
local CutLimbAction = require("TOC/TimedActions/CutLimbAction")
local SurgeryPrepAction = require("TOC/TimedActions/SurgeryPrepAction")
local SurgeryIncisionAction = require("TOC/TimedActions/SurgeryIncisionAction")
---------------------

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

---@param fullItemType string
---@return boolean
local function CheckIfSaw(fullItemType)
    return StaticData.SAWS_TYPES[fullItemType] ~= nil
end

---Can this limb be offered for amputation?
---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@return boolean ok, string? reasonKey
local function CanOffer(surgeon, patient, limbName)
    local dc = DataController.GetReady(patient:getUsername())
    if not dc then return false, "Tooltip_TOC_NoData" end
    if dc:getIsCut(limbName) then return false, nil end
    if StaticData.IsLegLimb(limbName) and not sv("EnableLegAmputations", true) then return false, nil end
    local part = string.match(limbName, "^(%a+)_")
    if surgeon == patient and StaticData.NO_SELF_SURGERY_PARTS_IND_STR[part] then
        return false, "Tooltip_TOC_CantSelfHigh"
    end
    return true, nil
end

---Queue the whole procedure after the checklist is confirmed
---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param plan table
---@param risk table
---@param previousAction ISBaseTimedAction?
local function QueueSurgery(surgeon, patient, limbName, plan, risk, previousAction)
    local function add(action)
        if previousAction then
            ISTimedActionQueue.addAfter(previousAction, action)
        else
            ISTimedActionQueue.add(action)
        end
        previousAction = action
    end
    if plan.disinfectItem then add(SurgeryPrepAction:new(surgeon, patient, limbName, plan.disinfectItem)) end
    if plan.bladeItem then add(SurgeryIncisionAction:new(surgeon, patient, limbName, plan.bladeItem)) end
    if plan.toolItem then
        add(ISEquipWeaponAction:new(surgeon, plan.toolItem, 50, true, false))
        local lHandItem = surgeon:getSecondaryHandItem()
        if lHandItem and lHandItem ~= plan.toolItem then
            add(ISUnequipAction:new(surgeon, lHandItem, 50))
        end
        add(CutLimbAction:new(surgeon, patient, limbName, plan.toolItem, plan.stitchesItem, plan.bandageItem, plan, risk))
    end
end

---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param sawItem InventoryItem?
local function OpenWindow(surgeon, patient, limbName, sawItem, previousAction)
    SurgeryWindow.Open(surgeon, patient, limbName, sawItem, function(plan, risk)
        QueueSurgery(surgeon, patient, limbName, plan, risk, previousAction)
    end)
end

--* Inventory context menu (right click on a saw) *--

local function AddInvAmputationOptions(player, context, sawItem)
    local option = context:addOption(getText("ContextMenu_Amputate"), nil)
    local subMenu = context:getNew(context)
    context:addSubMenu(option, subMenu)
    for i = 1, #StaticData.LIMBS_STR do
        local limbName = StaticData.LIMBS_STR[i]
        local ok, reason = CanOffer(player, player, limbName)
        if ok or reason then
            local opt = subMenu:addOption(getText("ContextMenu_Limb_" .. limbName), nil, function()
                OpenWindow(player, player, limbName, sawItem, nil)
            end)
            if not ok then
                opt.notAvailable = true
                local tip = ISToolTip:new(); tip:initialise(); tip:setVisible(false)
                tip.description = getText(reason)
                opt.toolTip = tip
            end
        end
    end
end

---@param playerNum number
---@param context ISContextMenu
---@param items table
local function AddInventoryAmputationMenu(playerNum, context, items)
    local item
    for _, v in ipairs(items) do
        item = v
        if not instanceof(v, "InventoryItem") then item = v.items[1] end
        break
    end
    if not item then return end
    if CheckIfSaw(item:getFullType()) then
        local player = getSpecificPlayer(playerNum)
        if not player then return end
        if not DataController.GetReady(player:getUsername()) then return end
        AddInvAmputationOptions(player, context, item)
    end
end

Events.OnFillInventoryObjectContextMenu.Add(AddInventoryAmputationMenu)

-------------------------------------

---@class CutLimbInteractionHandler : BaseHandler
local CutLimbInteractionHandler = BaseHandler:derive("CutLimbInteractionHandler")

function CutLimbInteractionHandler:new(panel, bodyPart)
    local o = BaseHandler.new(self, panel, bodyPart)
    o.items.ITEMS = {}
    o.limbName = BodyPartType.ToString(bodyPart:getType())
    return o
end

function CutLimbInteractionHandler:checkItem(item)
    if CheckIfSaw(item:getFullType()) then
        self:addItem(self.items.ITEMS, item)
    end
end

function CutLimbInteractionHandler:addToMenu(context)
    if not StaticData.LIMBS_TO_BODYLOCS_IND_BPT[self.limbName] then return end
    local types = self:getAllItemTypes(self.items.ITEMS)
    if #types == 0 then return end
    local ok, reason = CanOffer(self:getDoctor(), self:getPatient(), self.limbName)
    if not ok and not reason then return end
    local option = context:addOption(getText("ContextMenu_Amputate"), nil)
    if not ok then
        option.notAvailable = true
        local tip = ISToolTip:new(); tip:initialise(); tip:setVisible(false)
        tip.description = getText(reason)
        option.toolTip = tip
        return
    end
    local subMenu = context:getNew(context)
    context:addSubMenu(option, subMenu)
    for i = 1, #types do
        local item = self:getItemOfType(self.items.ITEMS, types[i])
        local tier = StaticData.SAWS_TYPES[types[i]]
        local label = item:getDisplayName() .. " (" .. getText("IGUI_TOC_SW_Tier_" .. StaticData.SAW_TIER_NAMES[tier]) .. ")"
        subMenu:addOption(label, self, self.openWindow, types[i])
    end
end

function CutLimbInteractionHandler:openWindow(itemType)
    local item = self:getItemOfType(self.items.ITEMS, itemType)
    local previousAction = nil
    if item and item:getContainer() ~= self:getDoctor():getInventory() then
        previousAction = self:toPlayerInventory(item, nil)
    end
    OpenWindow(self:getDoctor(), self:getPatient(), self.limbName, item, previousAction)
end

function CutLimbInteractionHandler:dropItems(items)
    local types = self:getAllItemTypes(items)
    if #self.items.ITEMS > 0 and #types == 1 and StaticData.LIMBS_TO_BODYLOCS_IND_BPT[self.limbName] then
        local ok = CanOffer(self:getDoctor(), self:getPatient(), self.limbName)
        if not ok then return false end
        self:openWindow(types[1])
        return true
    end
    return false
end

function CutLimbInteractionHandler:isValid()
    self:checkItems()
    local ok = CanOffer(self:getDoctor(), self:getPatient(), self.limbName)
    return ok
end

function CutLimbInteractionHandler:perform(previousAction, itemType)
    -- not used any more (the window queues the actions), kept for the base class
    self:openWindow(itemType)
end

return CutLimbInteractionHandler
