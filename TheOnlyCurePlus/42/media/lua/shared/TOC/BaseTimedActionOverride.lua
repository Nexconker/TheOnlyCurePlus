local DataController = require("TOC/Controllers/DataController")
local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
local CommonMethods = require("TOC/CommonMethods")
local StaticData = require("TOC/StaticData")
local PostOp = require("TOC/Plus/PostOp")

--* Time to perform actions overrides
local og_ISBaseTimedAction_adjustMaxTime = ISBaseTimedAction.adjustMaxTime
---@diagnostic disable-next-line: duplicate-set-field
function ISBaseTimedAction:adjustMaxTime(maxTime)
    local time = og_ISBaseTimedAction_adjustMaxTime(self, maxTime)
    if self.skipTOC then return time end
    if time == -1 or not self.character then return time end

    local username = self.character:getUsername()
    local dcInst = DataController.GetReady(username)
    if not dcInst or not dcInst:getIsAnyLimbCut() then return time end
    local amputatedLimbs = CachedDataHandler.GetAmputatedLimbs(username)

    local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
    local worst = 1.0
    for limbName, _ in pairs(amputatedLimbs) do
        if dcInst:getIsCut(limbName) and dcInst:getIsVisible(limbName) then
            local side = CommonMethods.GetSide(limbName)
            local perkLevel = self.character:getPerkLevel(Perks["Side_" .. side])
            local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
            if dcInst:getIsProstEquippedGroup(group) then
                local tier = ProsthesisHandler.GetEquippedTier(username, group)
                perkLevel = perkLevel + self.character:getPerkLevel(Perks["ProstFamiliarity"]) + (tier and tier.timeBonus or 0)
            end
            local perkLevelScaled = math.min(perkLevel, 10) / 10
            local base = StaticData.LIMBS_TIME_MULTIPLIER_IND_NUM[limbName] or 1
            -- level 10 (+prosthesis) brings the multiplier back to 1
            local mult = 1 + (base - 1) * (1 - perkLevelScaled)
            if mult > worst then worst = mult end
        end
    end
    if PostOp.IsInShock(dcInst) then worst = worst * 1.3
    elseif PostOp.IsConvalescent(dcInst) then worst = worst * 1.1 end
    return time * worst
end

---@param character IsoPlayer
---@param limbName string
local function TryRandomBleed(character, limbName)
    local dcInst = DataController.GetReady(character:getUsername())
    if not dcInst then return end
    local cicTime = dcInst:getCicatrizationTime(limbName)
    if cicTime <= 0 then return end
    local normCicTime = CommonMethods.Normalize(cicTime, 0, dcInst:getCicatrizationMax(limbName)) / 2
    if ZombRandFloat(0.0, 1.0) < normCicTime then
        local bleedingTime = math.max(1, math.floor(normCicTime * 2 * 20))
        if isClient() then
            local CommandsData = require("TOC/CommandsData")
            sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayTriggerBleed, {
                patientNum = character:getOnlineID(), limbName = limbName, bleedingTime = bleedingTime })
        else
            local adjacentBodyPartType = BodyPartType[StaticData.LIMBS_ADJACENT_IND_STR[limbName]]
            local bp = character:getBodyDamage():getBodyPart(adjacentBodyPartType)
            bp:setBleedingTime(bleedingTime)
        end
        local Messages = require("TOC/Plus/Messages")
        Messages.Say(character, getText("IGUI_TOC_StumpBleeds"), true)
    end
end

--* Random bleeding when using a prosthesis on a wound that is not closed yet + prosthesis wear
local og_ISBaseTimedAction_perform = ISBaseTimedAction.perform
---@diagnostic disable-next-line: duplicate-set-field
function ISBaseTimedAction:perform()
    og_ISBaseTimedAction_perform(self)
    if isServer() or not self.character or self.skipTOC then return end
    if isClient() and not self.character:isLocalPlayer() then return end
    local username = self.character:getUsername()
    local dcInst = DataController.GetReady(username)
    if not dcInst or not dcInst:getIsAnyLimbCut() then return end

    local amputatedLimbs = CachedDataHandler.GetAmputatedLimbs(username)
    for limbName, _ in pairs(amputatedLimbs) do
        if dcInst:getIsCut(limbName) and dcInst:getIsVisible(limbName) then
            if not dcInst:getIsCicatrized(limbName) and dcInst:getIsProstEquipped(limbName) then
                TryRandomBleed(self.character, limbName)
            end
        end
    end
    local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
    pcall(ProsthesisHandler.AddWearForAction, self.character)
end
