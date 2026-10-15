local StaticData = require("TOC/StaticData")
local DataController = require("TOC/Controllers/DataController")
local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
local Compat = require("TOC/Compat")
local PostOp = require("TOC/Plus/PostOp")

local CutLimbInteractionHandler = require("TOC/UI/Interactions/CutLimbInteractionHandler")
local WoundCleaningInteractionHandler = require("TOC/UI/Interactions/WoundCleaningInteractionHandler")
local ExamineWoundInteractionHandler = require("TOC/UI/Interactions/ExamineWoundInteractionHandler")
------------------------

local isReady = false

-- B42: the body texture is shifted compared to the panel origin (measured by the original author)
local xMod, yMod = 5, 13
if not StaticData.COMPAT_42 then xMod, yMod = 0, 0 end

function SetHealthPanelTOC()
    isReady = true
end

--* Drag and drop of the saw / cleaning items on a body part *--

local og_ISHealthPanel_dropItemsOnBodyPart = ISHealthPanel.dropItemsOnBodyPart
function ISHealthPanel:dropItemsOnBodyPart(bodyPart, items)
    og_ISHealthPanel_dropItemsOnBodyPart(self, bodyPart, items)
    local cutLimbInteraction = CutLimbInteractionHandler:new(self, bodyPart)
    local woundCleaningInteraction = WoundCleaningInteractionHandler:new(self, bodyPart, self.character:getUsername())
    for _, item in ipairs(items) do
        cutLimbInteraction:checkItem(item)
        woundCleaningInteraction:checkItem(item)
    end
    if cutLimbInteraction:dropItems(items) or woundCleaningInteraction:dropItems(items) then
        return
    end
end

local og_ISHealthPanel_doBodyPartContextMenu = ISHealthPanel.doBodyPartContextMenu
function ISHealthPanel:doBodyPartContextMenu(bodyPart, x, y)
    og_ISHealthPanel_doBodyPartContextMenu(self, bodyPart, x, y)
    local playerNum = self.otherPlayer and self.otherPlayer:getPlayerNum() or self.character:getPlayerNum()
    local context = getPlayerContextMenu(playerNum)
    if not context then return end
    context:bringToTop()
    context:setVisible(true)

    local ok, err = pcall(function()
        local cutLimbInteraction = CutLimbInteractionHandler:new(self, bodyPart)
        self:checkItems({cutLimbInteraction})
        cutLimbInteraction:addToMenu(context)

        local woundCleaningInteraction = WoundCleaningInteractionHandler:new(self, bodyPart, self.character:getUsername())
        self:checkItems({woundCleaningInteraction})
        woundCleaningInteraction:addToMenu(context)

        local examine = ExamineWoundInteractionHandler:new(self, bodyPart)
        examine:addToMenu(context)
    end)
    if not ok then TOC_DEBUG.print("doBodyPartContextMenu error: " .. tostring(err)) end
end

--* Overlays on the body *--

local function GetColorFromCicatrizationTime(dcInst, cicTime, limbName)
    local defaultTime = dcInst and dcInst:getCicatrizationMax(limbName) or StaticData.LIMBS_CICATRIZATION_TIME_IND_NUM[limbName]
    local delta = cicTime / math.max(1, defaultTime)
    return math.max(0.15, math.min(delta, 1))
end

---@param group string Top_L ...
function ISHealthPanel:tryDrawAmputation(highestAmputations, group, username)
    local limbName = highestAmputations[group]
    if limbName == nil then return end
    local dcInst = DataController.GetReady(username)
    local cicTime = dcInst and dcInst:getCicatrizationTime(limbName) or 0
    local redColor = GetColorFromCicatrizationTime(dcInst, cicTime, limbName)
    local sexPl = self.character:isFemale() and "Female" or "Male"
    local texture = StaticData.HEALTH_PANEL_TEXTURES[sexPl][limbName]
    if texture then
        self:drawTexture(texture, self.healthPanel.x - xMod, self.healthPanel.y - yMod, 1, redColor, 0, 0)
    end
end

function ISHealthPanel:tryDrawProsthesis(highestAmputations, group, username)
    local dc = DataController.GetReady(username)
    local limbName = highestAmputations[group]
    if limbName and dc and dc:getIsProstEquippedGroup(group) then
        local side = string.sub(group, -1)
        local tex = string.sub(group, 1, 3) == "Top" and StaticData.HEALTH_PANEL_TEXTURES.ProstArm[side] or StaticData.HEALTH_PANEL_TEXTURES.ProstLeg[side]
        if tex then
            self:drawTexture(tex, self.healthPanel.x - xMod, self.healthPanel.y - yMod, 1, 1, 1, 1)
        end
    end
end

local og_ISHealthPanel_render = ISHealthPanel.render
function ISHealthPanel:render()
    og_ISHealthPanel_render(self)
    local username = self.character:getUsername()
    local highestAmputations = CachedDataHandler.GetHighestAmputatedLimbs(username)
    if highestAmputations ~= nil then
        for i = 1, #StaticData.AMP_GROUPS_STR do
            local group = StaticData.AMP_GROUPS_STR[i]
            self:tryDrawAmputation(highestAmputations, group, username)
            self:tryDrawProsthesis(highestAmputations, group, username)
        end
    end
    -- TOC+: shock / convalescence under the body
    local dc = DataController.GetReady(username)
    if dc and dc:getIsAnyLimbCut() then
        local y = self.healthPanel:getBottom() + 2
        local x = self.healthPanel.x
        if PostOp.IsInShock(dc) then
            self:drawText(getText("IGUI_TOC_HP_Shock"), x, y, 0.95, 0.3, 0.3, 1, UIFont.Small)
            y = y + getTextManager():getFontHeight(UIFont.Small)
        end
        local left = PostOp.ConvalescenceLeft(dc)
        if left > 0 then
            local days = math.floor(left / 24)
            local hours = math.floor(left - days * 24)
            self:drawText(getText("IGUI_TOC_HP_Convalescence", tostring(days), tostring(hours)), x, y, 0.95, 0.75, 0.3, 1, UIFont.Small)
        end
    end
end

-- Force alpha 1 so the overlays read well
local og_ISCharacterInfoWindow_render = ISCharacterInfoWindow.prerender
function ISCharacterInfoWindow:prerender()
    og_ISCharacterInfoWindow_render(self)
    self.backgroundColor.a = 1
end

local og_ISHealthPanel_prerender = ISHealthPanel.prerender
function ISHealthPanel:prerender()
    og_ISHealthPanel_prerender(self)
    self.backgroundColor.a = 1
end

local og_ISMedicalCheckAction_perform = ISMedicalCheckAction.perform
function ISMedicalCheckAction:perform()
    if self.otherPlayer then
        local username = self.otherPlayer:getUsername()
        local ClientDataController = require("TOC/Controllers/ClientDataController")
        pcall(ClientDataController.Request, username, false)
        if isClient() then pcall(CachedDataHandler.RequestFromServer, username, true) end
    end
    og_ISMedicalCheckAction_perform(self)
end

--* Body part list lines *--

local og_ISHealthBodyPartListBox_doDrawItem = ISHealthBodyPartListBox.doDrawItem
function ISHealthBodyPartListBox:doDrawItem(y, item, alt)
    y = og_ISHealthBodyPartListBox_doDrawItem(self, y, item, alt)
    y = y - 5
    local x = 15
    local fontHgt = getTextManager():getFontHeight(UIFont.Small)
    local username = self.parent.character:getUsername()
    local bodyPart = item.item.bodyPart
    local bodyPartTypeStr = BodyPartType.ToString(bodyPart:getType())
    local limbName = StaticData.LIMBS_IND_STR[bodyPartTypeStr]
    local dcInst = DataController.GetReady(username)

    if dcInst and limbName and dcInst:getIsCut(limbName) and dcInst:getIsVisible(limbName) then
        if dcInst:getIsCicatrized(limbName) then
            if dcInst:getIsCauterized(limbName) then
                self:drawText("- " .. getText("IGUI_HealthPanel_Cauterized"), x, y, 0.58, 0.75, 0.28, 1, UIFont.Small)
            else
                self:drawText("- " .. getText("IGUI_HealthPanel_Cicatrized"), x, y, 0.28, 0.89, 0.28, 1, UIFont.Small)
            end
            y = y + fontHgt
        else
            local cicaTime = dcInst:getCicatrizationTime(limbName)
            local maxCicaTime = dcInst:getCicatrizationMax(limbName)
            local percentage = math.max(0, (1 - cicaTime / math.max(1, maxCicaTime)) * 100)
            self:drawText("- " .. getText("IGUI_HealthPanel_Cicatrization") .. string.format(" %.0f", percentage) .. "%", x, y, 0.89, 0.28, 0.28, 1, UIFont.Small)
            y = y + fontHgt
            local scaledDirtyness = math.floor(math.max(0, dcInst:getWoundDirtyness(limbName)) * 100)
            self:drawText("- " .. getText("IGUI_HealthPanel_WoundDirtyness") .. string.format(" %d", scaledDirtyness) .. "%", x, y, 0.89, 0.28, 0.28, 1, UIFont.Small)
            y = y + fontHgt
        end
        local sepsis = dcInst:getSepsis(limbName)
        if sepsis > 0 then
            local r, g = 0.95, 0.7
            if sepsis > 50 then g = 0.3 end
            self:drawText("- " .. getText("IGUI_TOC_HP_Sepsis") .. string.format(" %d", math.floor(sepsis)) .. "%", x, y, r, g, 0.2, 1, UIFont.Small)
            y = y + fontHgt
        end
        if dcInst:getIsProstEquipped(limbName) then
            local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
            local t = dcInst:getProstType(group)
            local label = getText("IGUI_HealthPanel_ProstEquipped")
            if t then
                local ok, si = pcall(function() return getScriptManager():FindItem(t) end)
                if ok and si then label = label .. " (" .. si:getDisplayName() .. ")" end
            end
            self:drawText("- " .. label, x, y, 0.28, 0.89, 0.28, 1, UIFont.Small)
            y = y + fontHgt
        end
    end
    -- botched attempt on this limb
    if dcInst and limbName and dcInst:plus().botched[limbName] and not dcInst:getIsCut(limbName) then
        self:drawText("- " .. getText("IGUI_TOC_HP_Botched"), x, y, 0.95, 0.4, 0.2, 1, UIFont.Small)
        y = y + fontHgt
    end
    -- diagnosis on this part
    if dcInst then
        local d = dcInst:plus().lastDiagnosis[bodyPartTypeStr]
        if d and d.verdict then
            local ago = math.max(0, math.floor(PostOp.Now() - (d.hours or 0)))
            local col = ({ infected = { 0.95, 0.3, 0.3 }, clean = { 0.3, 0.9, 0.3 }, unsure = { 0.8, 0.8, 0.5 } })[d.verdict] or { 0.8, 0.8, 0.8 }
            self:drawText("- " .. getText("IGUI_TOC_HP_Diag_" .. d.verdict, tostring(ago)), x, y, col[1], col[2], col[3], 1, UIFont.Small)
            y = y + fontHgt
        end
    end
    y = y + 5
    return y
end

local og_ISHealthPanel_getDamagedParts = ISHealthPanel.getDamagedParts
function ISHealthPanel:getDamagedParts()
    if isReady == false or (Compat.handlers['iMeds'] and Compat.handlers['iMeds'].isActive) or (Compat.handlers['iMedsFixed'] and Compat.handlers['iMedsFixed'].isActive) then
        return og_ISHealthPanel_getDamagedParts(self)
    end
    local result = {}
    local bodyParts = self:getPatient():getBodyDamage():getBodyParts()
    if isClient() and not self:getPatient():isLocalPlayer() then
        bodyParts = self:getPatient():getBodyDamageRemote():getBodyParts()
    end
    local patientUsername = self:getPatient():getUsername()
    local mdh = DataController.GetReady(patientUsername)
    for i = 1, bodyParts:size() do
        local bodyPart = bodyParts:get(i - 1)
        local bodyPartTypeStr = BodyPartType.ToString(bodyPart:getType())
        local limbName = StaticData.LIMBS_IND_STR[bodyPartTypeStr]
        local extra = false
        if mdh then
            if limbName and mdh:getIsCut(limbName) and mdh:getIsVisible(limbName) then extra = true end
            if mdh:plus().lastDiagnosis[bodyPartTypeStr] then extra = true end
            if limbName and mdh:plus().botched[limbName] then extra = true end
        end
        if ISHealthPanel.cheat or bodyPart:HasInjury() or bodyPart:bandaged() or bodyPart:stitched() or bodyPart:getSplintFactor() > 0 or bodyPart:getAdditionalPain() > 10 or bodyPart:getStiffness() > 5 or extra then
            table.insert(result, bodyPart)
        end
    end
    return result
end
