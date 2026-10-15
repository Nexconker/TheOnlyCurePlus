local DataController = require("TOC/Controllers/DataController")
local CommonMethods = require("TOC/CommonMethods")
local StaticData = require("TOC/StaticData")
local CommandsData = require("TOC/CommandsData")
local PostOp = require("TOC/Plus/PostOp")
--------------------

-- TOC+: clean the stump with an alcohol bandage OR a disinfectant / wipes / spirits.
-- Consumes the item properly (the original left dirty bandages stuck, issue #259).
---@class CleanWoundAction : ISBaseTimedAction
local CleanWoundAction = ISBaseTimedAction:derive("CleanWoundAction")

---Cleaning power 0..1 of an item, or nil if it cannot clean
---@param item InventoryItem
---@return number?
function CleanWoundAction.CleanPower(item)
    if not item then return nil end
    local ft = item:getFullType()
    local p = StaticData.DISINFECTANT_TYPES[ft]
    if p then
        if instanceof(item, "DrainableComboItem") and item:getCurrentUsesFloat() <= 0 then return nil end
        if item.hasComponent and item:hasComponent(ComponentType.FluidContainer) and item:getFluidContainer():getAmount() < 0.15 then return nil end
        return p
    end
    local ok, power = pcall(function() return item:getBandagePower() end)
    if ok and power and power >= 2 and item:isAlcoholic() then return math.min(1, power / 4) end
    return nil
end

---@param character IsoPlayer doctor performing the action
---@param patient IsoPlayer
---@param item InventoryItem
---@param bodyPart BodyPart
function CleanWoundAction:new(character, patient, item, bodyPart)
    local o = ISBaseTimedAction.new(self, character)
    o.patient = patient
    o.characterLevel = character:getPerkLevel(Perks.Doctor)
    o.bodyPart = bodyPart
    o.item = item
    o.bandage = item
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.bandagedPlayerX = patient:getX()
    o.bandagedPlayerY = patient:getY()
    o.maxTime = 250 - (o.characterLevel * 6)
    if character:isTimedActionInstant() then o.maxTime = 1 end
    return o
end

function CleanWoundAction:isValid()
    if not self.item or not self.character:getInventory():contains(self.item) then return false end
    return not ISHealthPanel.DidPatientMove(self.character, self.patient, self.bandagedPlayerX, self.bandagedPlayerY)
end

function CleanWoundAction:waitToStart()
    if self.character == self.patient then return false end
    self.character:faceThisObject(self.patient)
    return self.character:shouldBeTurning()
end

function CleanWoundAction:update()
    if self.character ~= self.patient then
        self.character:faceThisObject(self.patient)
    end
    local jobType = getText("ContextMenu_CleanWound")
    ISHealthPanel.setBodyPartActionForPlayer(self.patient, self.bodyPart, self, jobType, { cleanBurn = true })
    self.character:setMetabolicTarget(Metabolics.LightDomestic)
end

function CleanWoundAction:start()
    if self.character == self.patient then
        self:setActionAnim(CharacterActionAnims.Bandage)
        self:setAnimVariable("BandageType", ISHealthPanel.getBandageType(self.bodyPart))
        self.character:reportEvent("EventBandage")
    else
        self:setActionAnim("Loot")
        self.character:SetVariable("LootPosition", "Mid")
        self.character:reportEvent("EventLootItem")
    end
    pcall(function() self:setOverrideHandModels(nil, nil) end)
end

function CleanWoundAction:stop()
    ISHealthPanel.setBodyPartActionForPlayer(self.patient, self.bodyPart, nil, nil, nil)
    ISBaseTimedAction.stop(self)
end

function CleanWoundAction:consume()
    local item = self.item
    local inv = self.character:getInventory()
    local ft = item:getFullType()
    pcall(function()
        if item:hasComponent(ComponentType.FluidContainer) then
            local fc = item:getFluidContainer()
            if fc:getAmount() > 0.15 then fc:adjustAmount(fc:getAmount() - 0.15) end
            sendItemStats(item)
        elseif instanceof(item, "DrainableComboItem") then
            item:UseAndSync()
        else
            item:getContainer():Remove(item)
            sendRemoveItemFromContainer(inv, item)
            local dirty = nil
            if ft == "Base.AlcoholBandage" or ft == "Base.Bandage" then dirty = "Base.BandageDirty"
            elseif ft == "Base.AlcoholRippedSheets" or ft == "Base.RippedSheets" then dirty = "Base.RippedSheetsDirty" end
            if dirty then
                local d = inv:AddItem(dirty)
                if d then sendAddItemToContainer(inv, d) end
            end
        end
    end)
end

function CleanWoundAction:perform()
    if self.character:hasTrait(CharacterTrait.HEMOPHOBIC) then
        self.character:getStats():set(CharacterStat.PANIC, math.min(100, (self.character:getStats():get(CharacterStat.PANIC) or 0) + 15))
    end
    self.character:getXp():AddXP(Perks.Doctor, 10)
    local power = CleanWoundAction.CleanPower(self.item) or 0.3
    self:consume()

    local limbName = CommonMethods.GetLimbNameFromBodyPart(self.bodyPart)
    local dcInst = DataController.GetReady(self.patient:getUsername())
    if dcInst and limbName then
        local dirt = dcInst:getWoundDirtyness(limbName) - 0.6 * power
        dcInst:setWoundDirtyness(limbName, math.max(0, dirt))
        dcInst:setSepsis(limbName, dcInst:getSepsis(limbName) - 10 * power)
        if self.patient:isLocalPlayer() then dcInst:updateAmputationsFromClient(limbName) end
        local bbptEnum = BloodBodyPartType[limbName]
        if bbptEnum then
            local visual = self.patient:getHumanVisual()
            visual:setDirt(bbptEnum, 0)
            visual:setBlood(bbptEnum, 0)
        end
    end

    local fx = { alcohol = power * 2, pain = math.max(0, 40 * power - self.characterLevel) }
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayPostOpApply,
            {patientNum = self.patient:getOnlineID(), limbName = limbName, fx = fx})
    else
        PostOp.ApplyEffects(self.patient, limbName, fx)
    end

    ISHealthPanel.setBodyPartActionForPlayer(self.patient, self.bodyPart, nil, nil, nil)
    ISBaseTimedAction.perform(self)
end

return CleanWoundAction
