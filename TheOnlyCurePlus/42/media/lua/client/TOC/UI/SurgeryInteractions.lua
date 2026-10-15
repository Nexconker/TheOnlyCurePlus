local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
local DataController = require("TOC/Controllers/DataController")
local CauterizeAction = require("TOC/TimedActions/CauterizeAction")
local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
local StaticData = require("TOC/StaticData")
---------------

-- TOC+: cauterize at any lit heat source.

---@param tooltip ISToolTip
---@param desc string
local function AppendToDescription(tooltip, desc)
    if tooltip.description == "" then
        tooltip.description = desc
    else
        tooltip.description = tooltip.description .. getText("Tooltip_Surgery_And") .. desc
    end
end

---Find a usable heat source among the clicked objects
---@param worldObjects table
---@return IsoObject? obj, boolean hot
local function FindHeatSource(worldObjects)
    for _, obj in pairs(worldObjects) do
        if instanceof(obj, "IsoStove") then
            -- B42: IsoStove:Activated() (no isActivated)
            local hot = (obj.Activated and obj:Activated()) or false
            if not hot and obj.getCurrentTemperature then hot = (obj:getCurrentTemperature() - 1) >= 2.5 end
            return obj, hot
        elseif instanceof(obj, "IsoFireplace") or instanceof(obj, "IsoBarbecue") then
            local lit = (obj.isLit and obj:isLit()) or false
            return obj, lit
        elseif instanceof(obj, "IsoFire") then
            return obj, true
        else
            local ok, campfire = pcall(function()
                return CCampfireSystem and CCampfireSystem.instance and CCampfireSystem.instance:getLuaObjectOnSquare(obj:getSquare())
            end)
            if ok and campfire then
                return obj, campfire.isLit == true
            end
        end
    end
    return nil, false
end

---@param playerNum number
---@param context ISContextMenu
---@param worldObjects any
---@param test any
local function AddCauterizeContextMenu(playerNum, context, worldObjects, test)
    if test then return true end
    local pl = getSpecificPlayer(playerNum)
    if not pl then return end
    local dcInst = DataController.GetReady(pl:getUsername())
    if not dcInst or not dcInst:getIsAnyLimbCut() then return end

    local heatObj, hot = FindHeatSource(worldObjects)
    if heatObj == nil then return end

    local amputatedLimbs = CachedDataHandler.GetAmputatedLimbs(pl:getUsername())
    local tempTooltip = ISToolTip:new()
    tempTooltip:initialise()
    tempTooltip.description = ""
    tempTooltip:setVisible(false)

    local subMenu = nil
    for limbName, _ in pairs(amputatedLimbs) do
        if dcInst:getIsVisible(limbName) and not dcInst:getIsCicatrized(limbName) then
            if subMenu == nil then
                local optionMain = context:addOption(getText("ContextMenu_Cauterize"), nil)
                subMenu = context:getNew(context)
                context:addSubMenu(optionMain, subMenu)
            end
            local option = subMenu:addOption(getText("ContextMenu_Limb_" .. limbName), nil, function()
                local adjacent = AdjacentFreeTileFinder.Find(heatObj:getSquare(), pl)
                if adjacent then ISTimedActionQueue.add(ISWalkToTimedAction:new(pl, adjacent)) end
                ISTimedActionQueue.add(CauterizeAction:new(pl, limbName, heatObj))
            end)

            local anesthesia = SurgeryPlan.GetAnesthesia(pl)
            local isPlayerCourageous = pl:hasTrait(CharacterTrait.BRAVE) or pl:hasTrait(CharacterTrait.DESENSITIZED)
                or pl:getPerkLevel(Perks.Strength) > 5 or anesthesia >= 0.4 or SurgeryPlan.KnowsSurgery(pl)
            local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
            local isLimbFree = not dcInst:getIsProstEquippedGroup(group)

            option.notAvailable = not (isPlayerCourageous and hot and isLimbFree)
            if not hot then AppendToDescription(tempTooltip, getText("Tooltip_Surgery_TempTooLow")) end
            if not isPlayerCourageous then AppendToDescription(tempTooltip, getText("Tooltip_Surgery_Coward")) end
            if not isLimbFree then AppendToDescription(tempTooltip, getText("Tooltip_Surgery_LimbNotFree")) end
            if option.notAvailable then
                tempTooltip:setName(getText("Tooltip_Surgery_CantCauterize"))
                option.toolTip = tempTooltip
            end
        end
    end
end

Events.OnFillWorldObjectContextMenu.Add(AddCauterizeContextMenu)
