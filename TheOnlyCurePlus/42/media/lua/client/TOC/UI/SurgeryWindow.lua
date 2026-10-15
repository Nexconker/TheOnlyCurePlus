-- TOC+ SurgeryWindow: the checklist shown before an amputation. Replaces the old yes/no panel.
local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
local StaticData = require("TOC/StaticData")
---------------

---@class SurgeryWindow : ISPanel
local SurgeryWindow = ISPanel:derive("SurgeryWindow")

local FONT = UIFont.Small
local FONT_H = getTextManager():getFontHeight(FONT)
local PAD = 12

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param toolItem InventoryItem?
---@param onConfirm fun(plan: table, risk: table)
function SurgeryWindow:new(x, y, surgeon, patient, limbName, toolItem, onConfirm)
    local o = ISPanel:new(x, y, 520, 100)
    setmetatable(o, self)
    self.__index = self
    o.surgeon = surgeon
    o.patient = patient
    o.limbName = limbName
    o.toolItem = toolItem
    o.onConfirm = onConfirm
    o.plan = SurgeryPlan.Gather(surgeon, patient, limbName, toolItem)
    o.risk = SurgeryPlan.Risk(o.plan)
    o.steps = SurgeryPlan.Steps(o.plan)
    o.lines = {}
    o.backgroundColor = { r = 0.05, g = 0.05, b = 0.05, a = 0.95 }
    o.borderColor = { r = 0.6, g = 0.1, b = 0.1, a = 1 }
    o.moveWithMouse = true
    SurgeryWindow.instance = o
    return o
end

local function itemName(item)
    if not item then return "" end
    local ok, n = pcall(function() return item:getDisplayName() end)
    return ok and n or ""
end

function SurgeryWindow:buildLines()
    local L = {}
    local plan, risk = self.plan, self.risk
    local limbText = getText("ContextMenu_Limb_" .. self.limbName)
    local patientName = self.patient:getDescriptor() and (self.patient:getDescriptor():getForename() .. " " .. self.patient:getDescriptor():getSurname()) or self.patient:getUsername()
    table.insert(L, { t = getText("IGUI_TOC_SW_Title", limbText), c = { 1, 0.85, 0.85 }, font = UIFont.Medium })
    table.insert(L, { t = plan.selfOp and getText("IGUI_TOC_SW_Self") or getText("IGUI_TOC_SW_Patient", patientName), c = { 0.8, 0.8, 0.8 } })
    table.insert(L, { t = "" })
    for _, s in ipairs(self.steps) do
        local mark, col
        if s.ok then mark = "[+] "; col = { 0.4, 0.9, 0.4 }
        elseif s.partial then mark = "[~] "; col = { 0.9, 0.8, 0.3 }
        else mark = "[-] "; col = { 0.9, 0.4, 0.4 } end
        local text = getText("IGUI_TOC_SW_Step_" .. s.key)
        if s.item then text = text .. ": " .. itemName(s.item) end
        if s.key == "Bone" and s.tier then
            text = text .. " (" .. getText("IGUI_TOC_SW_Tier_" .. StaticData.SAW_TIER_NAMES[s.tier]) .. ")"
        end
        if not s.ok and not s.partial then
            text = text .. "  -  " .. getText("IGUI_TOC_SW_Missing_" .. s.key)
        end
        table.insert(L, { t = mark .. text, c = col })
    end
    table.insert(L, { t = "" })

    -- knowledge, surgeon state
    if plan.knows then
        table.insert(L, { t = getText("IGUI_TOC_SW_Knows"), c = { 0.5, 0.9, 0.5 } })
    else
        table.insert(L, { t = getText("IGUI_TOC_SW_NoKnowledge"), c = { 0.9, 0.7, 0.4 } })
    end
    local warn = {}
    if plan.fatigue > 0.5 then table.insert(warn, getText("IGUI_TOC_SW_Warn_Tired")) end
    if plan.panic > 0.3 then table.insert(warn, getText("IGUI_TOC_SW_Warn_Panic")) end
    if plan.drunk > 0.2 then table.insert(warn, getText("IGUI_TOC_SW_Warn_Drunk")) end
    if plan.hemophobic then table.insert(warn, getText("IGUI_TOC_SW_Warn_Hemophobic")) end
    if plan.surgeonOneHanded then table.insert(warn, getText("IGUI_TOC_SW_Warn_OneHanded")) end
    if plan.selfOp then table.insert(warn, getText("IGUI_TOC_SW_Warn_Self")) end
    for _, w in ipairs(warn) do table.insert(L, { t = "! " .. w, c = { 0.95, 0.6, 0.3 } }) end
    if risk.painLevel > 0.2 then
        table.insert(L, { t = "! " .. getText("IGUI_TOC_SW_Warn_Scream", tostring(risk.noiseRadius)), c = { 0.95, 0.6, 0.3 } })
    end
    table.insert(L, { t = "" })

    -- estimate
    local minDoctor = sv("DiagnosisMinDoctor", 2)
    if plan.doctorLevel >= math.max(3, minDoctor) or plan.knows then
        local bracket = SurgeryPlan.Bracket(risk)
        local pct = string.format("%d%%", math.floor(risk.fail * 100 + 0.5))
        local col = ({ Low = { 0.4, 0.9, 0.4 }, Medium = { 0.9, 0.8, 0.3 }, High = { 0.95, 0.5, 0.3 }, VeryHigh = { 0.95, 0.25, 0.25 } })[bracket]
        table.insert(L, { t = getText("IGUI_TOC_SW_Risk", getText("IGUI_TOC_SW_Risk_" .. bracket), pct), c = col })
        table.insert(L, { t = getText("IGUI_TOC_SW_Faint", string.format("%d%%", math.floor(risk.faintChance * 100 + 0.5))), c = { 0.8, 0.8, 0.8 } })
    else
        table.insert(L, { t = getText("IGUI_TOC_SW_RiskUnknown"), c = { 0.8, 0.8, 0.8 } })
    end
    table.insert(L, { t = getText("IGUI_TOC_SW_Confirm"), c = { 1, 1, 1 } })
    self.lines = L
end

function SurgeryWindow:createChildren()
    ISPanel.createChildren(self)
    self:buildLines()
    local h = PAD
    for _, l in ipairs(self.lines) do
        h = h + (l.font == UIFont.Medium and getTextManager():getFontHeight(UIFont.Medium) or FONT_H) + 2
    end
    local btnH = 25
    self:setHeight(h + PAD + btnH + PAD)

    local btnW = 120
    local yBtn = self:getHeight() - PAD - btnH
    self.btnYes = ISButton:new(self:getWidth() / 2 - btnW - 10, yBtn, btnW, btnH, getText("IGUI_TOC_SW_Operate"), self, self.onClick)
    self.btnYes.internal = "YES"
    self.btnYes:initialise()
    self.btnYes.borderColor = { r = 0.8, g = 0.1, b = 0.1, a = 1 }
    self.btnYes:setEnable(self.plan.toolItem ~= nil)
    self:addChild(self.btnYes)

    self.btnNo = ISButton:new(self:getWidth() / 2 + 10, yBtn, btnW, btnH, getText("IGUI_No"), self, self.onClick)
    self.btnNo.internal = "NO"
    self.btnNo:initialise()
    self:addChild(self.btnNo)
end

function SurgeryWindow:prerender()
    ISPanel.prerender(self)
    local y = PAD
    for _, l in ipairs(self.lines) do
        local font = l.font or FONT
        local c = l.c or { 1, 1, 1 }
        if l.t ~= "" then
            self:drawText(l.t, PAD, y, c[1], c[2], c[3], 1, font)
        end
        y = y + getTextManager():getFontHeight(font) + 2
    end
end

function SurgeryWindow:onClick(btn)
    if btn.internal == "YES" then
        local cb = self.onConfirm
        self:close()
        if cb then cb(self.plan, self.risk) end
    else
        self:close()
    end
end

function SurgeryWindow:close()
    self:setVisible(false)
    self:removeFromUIManager()
    if SurgeryWindow.instance == self then SurgeryWindow.instance = nil end
end

---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param toolItem InventoryItem?
---@param onConfirm fun(plan: table, risk: table)
function SurgeryWindow.Open(surgeon, patient, limbName, toolItem, onConfirm)
    if SurgeryWindow.instance then SurgeryWindow.instance:close() end
    local w = 520
    local x = (getCore():getScreenWidth() - w) / 2
    local y = getCore():getScreenHeight() / 3
    local panel = SurgeryWindow:new(x, y, surgeon, patient, limbName, toolItem, onConfirm)
    panel:initialise()
    panel:addToUIManager()
    panel:bringToTop()
    return panel
end

return SurgeryWindow
