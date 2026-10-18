require "TimedActions/ISBaseTimedAction"
-- TOC+ 3.3: banco de prótesis (DISENO_3.3_MODULAR.md). Ventana con las bases y los cabezales del inventario, vista 3D
-- del personaje y las estadísticas de la combinación; los botones ponen y quitan piezas con las acciones vanilla de
-- vestir / desvestir (ISWearClothing / ISUnequipAction), cuyas reglas de prótesis están en ProsthesisHandler y
-- TOC/Plus/ModularProsthesis. Se abre desde el menú contextual de cualquier base o cabezal.

local StaticData = require("TOC/StaticData")
local Modular = require("TOC/Plus/ModularProsthesis")
local Paint = require("TOC/Plus/ProsthesisPaint")
local PaintMenu = require("TOC/UI/ProsthesisPaintMenu")
------------------

TOC_ProsthesisWorkbench = ISCollapsableWindow:derive("TOC_ProsthesisWorkbench")
local FONT_HGT_SMALL = getTextManager():getFontHeight(UIFont.Small)
local FONT_HGT_MEDIUM = getTextManager():getFontHeight(UIFont.Medium)
local PAD = 10
local BTN_H = math.max(25, FONT_HGT_SMALL + 8)
local BTN_KEYS = { "IGUI_TOC_WB_FitBase", "IGUI_TOC_WB_MountHead", "IGUI_TOC_WB_Remove", "ContextMenu_TOC_Paint", "UI_Close" }
local instance = nil

---Prótesis de pierna (en el banco sólo se pintan)
local function isLeg(item)
    local t = item and StaticData.GetProsthesisTier(item:getFullType())
    return t ~= nil and t.group == "Bottom"
end

local function isPart(item)
    return item ~= nil and (Modular.IsModularBase(item) or Modular.IsHead(item) or isLeg(item))
end

local function sideOf(item)
    local _, s = StaticData.GetProsthesisBase(item:getFullType())
    return s
end

local function wornBy(player, item)
    local worn = player:getWornItems()
    for i = 0, (worn and worn:size() or 0) - 1 do
        if worn:get(i):getItem() == item then return true end
    end
    return false
end

---Fila de las listas: muestra de pintura, nombre (recortado si no cabe) y, a la derecha, lado y estado
local function drawRow(list, y, row, alt)
    local h = list.itemheight
    if list.selected == row.index then list:drawRect(0, y, list:getWidth(), h, 0.3, 0.7, 0.35, 0.15) end
    list:drawRectBorder(0, y, list:getWidth(), h, 0.25, 0.4, 0.4, 0.4)
    local it, tm = row.item, getTextManager()
    local right = row.info or ""
    local rw = tm:MeasureStringX(UIFont.Small, right)
    list:drawTextRight(right, list:getWidth() - 8, y + 3, 0.7, 0.7, 0.7, 1, UIFont.Small)
    local x = 6
    local idx = Paint.GetIndex(it)
    if idx > 0 and Paint.RGB[idx] then
        local c = Paint.RGB[idx]
        list:drawRect(x, y + 4, h - 8, h - 8, 1, c[1] / 255, c[2] / 255, c[3] / 255)
        list:drawRectBorder(x, y + 4, h - 8, h - 8, 1, 0.8, 0.8, 0.8)
        x = x + h - 2
    end
    local name = row.text
    local maxW = list:getWidth() - x - rw - 16
    if tm:MeasureStringX(UIFont.Small, name) > maxW then
        while #name > 3 and tm:MeasureStringX(UIFont.Small, name .. "...") > maxW do name = string.sub(name, 1, #name - 1) end
        name = name .. "..."
    end
    list:drawText(name, x, y + 3, 0.95, 0.95, 0.95, 1, UIFont.Small)
    return y + h
end

function TOC_ProsthesisWorkbench:createChildren()
    ISCollapsableWindow.createChildren(self)
    local th = self:titleBarHeight()
    local listW, avatarW = self.listW, self.avatarW
    local by = self.height - PAD - BTN_H                 -- fila de botones
    self.contentBottom = by - PAD                        -- 2026-10-17: las estadísticas pasaban por encima de los botones
    local listH = math.floor((self.contentBottom - th - PAD * 3) / 3) - FONT_HGT_SMALL - 2     -- bases, cabezales y piernas
    local y = th + PAD
    self.lblBases = ISLabel:new(PAD, y, FONT_HGT_SMALL, getText("IGUI_TOC_WB_Bases"), 1, 1, 1, 1, UIFont.Small, true)
    self:addChild(self.lblBases)
    self.bases = ISScrollingListBox:new(PAD, y + FONT_HGT_SMALL + 2, listW, listH)
    self.bases:initialise(); self.bases:instantiate(); self.bases.itemheight = FONT_HGT_SMALL + 6
    self.bases.font = UIFont.Small; self.bases.drawBorder = true
    self.bases.onmousedown = function() self.lastList = self.bases; self:updateButtons() end
    self.bases.doDrawItem = drawRow
    self:addChild(self.bases)
    local y2 = self.bases:getBottom() + PAD
    self.lblHeads = ISLabel:new(PAD, y2, FONT_HGT_SMALL, getText("IGUI_TOC_WB_Heads"), 1, 1, 1, 1, UIFont.Small, true)
    self:addChild(self.lblHeads)
    self.heads = ISScrollingListBox:new(PAD, y2 + FONT_HGT_SMALL + 2, listW, listH)
    self.heads:initialise(); self.heads:instantiate(); self.heads.itemheight = FONT_HGT_SMALL + 6
    self.heads.font = UIFont.Small; self.heads.drawBorder = true
    self.heads.onmousedown = function() self.lastList = self.heads; self:updateButtons() end
    self.heads.doDrawItem = drawRow
    self:addChild(self.heads)
    local y3 = self.heads:getBottom() + PAD
    self.lblLegs = ISLabel:new(PAD, y3, FONT_HGT_SMALL, getText("IGUI_TOC_WB_Legs"), 1, 1, 1, 1, UIFont.Small, true)
    self:addChild(self.lblLegs)
    self.legs = ISScrollingListBox:new(PAD, y3 + FONT_HGT_SMALL + 2, listW, listH)
    self.legs:initialise(); self.legs:instantiate(); self.legs.itemheight = FONT_HGT_SMALL + 6
    self.legs.font = UIFont.Small; self.legs.drawBorder = true
    self.legs.onmousedown = function() self.lastList = self.legs; self:updateButtons() end
    self.legs.doDrawItem = drawRow
    self:addChild(self.legs)

    self.avatarX = self.bases:getRight() + PAD
    self.avatar = ISUI3DModel:new(self.avatarX, th + PAD, avatarW, self.contentBottom - th - PAD)
    self.avatar:setVisible(true)
    self:addChild(self.avatar)
    self.avatar:setCharacter(self.player)
    self.avatar:setState("idle")
    self.avatar:setDirection(IsoDirections.SE)
    self.avatar:setIsometric(false)
    self.statsX = self.avatar:getRight() + PAD

    local bw = self.btnW                                 -- a la medida del texto más largo (antes 120: "Montar cabeza..." se cortaba)
    local function button(i, key, fn)
        local b = ISButton:new(PAD + i * (bw + 6), by, bw, BTN_H, getText(key), self, fn)
        b:initialise(); b:instantiate(); self:addChild(b); return b
    end
    self.btnFitBase = button(0, "IGUI_TOC_WB_FitBase", TOC_ProsthesisWorkbench.onFitBase)
    self.btnMountHead = button(1, "IGUI_TOC_WB_MountHead", TOC_ProsthesisWorkbench.onMountHead)
    self.btnRemove = button(2, "IGUI_TOC_WB_Remove", TOC_ProsthesisWorkbench.onRemove)
    self.btnPaint = button(3, "ContextMenu_TOC_Paint", TOC_ProsthesisWorkbench.onPaint)       -- sólo se pinta aquí
    self.btnClose = button(4, "UI_Close", TOC_ProsthesisWorkbench.close)
    self:refresh()
end

---Firma de lo que lleva puesto (tipo + pintura): si cambia, el avatar 3D se vuelve a crear
function TOC_ProsthesisWorkbench:wornSignature()
    local parts = {}
    local worn = self.player:getWornItems()
    for i = 0, (worn and worn:size() or 0) - 1 do
        local it = worn:get(i):getItem()
        if it and isPart(it) then parts[#parts + 1] = it:getFullType() .. ":" .. tostring(Paint.GetIndex(it)) end
    end
    table.sort(parts)
    return table.concat(parts, "|")
end

function TOC_ProsthesisWorkbench:refresh()
    local sig = self:wornSignature()
    if self.avatar and self.wornSig ~= nil and sig ~= self.wornSig then
        self.avatar:setCharacter(self.player)            -- 2026-10-17: la pintura no se veía en el avatar hasta reabrir
    end
    self.wornSig = sig
    local selB = self.bases.items[self.bases.selected] and self.bases.items[self.bases.selected].item
    local selH = self.heads.items[self.heads.selected] and self.heads.items[self.heads.selected].item
    local selL = self.legs.items[self.legs.selected] and self.legs.items[self.legs.selected].item
    self.bases:clear(); self.heads:clear(); self.legs:clear()
    local found = ArrayList.new()
    pcall(function() self.player:getInventory():getAllEvalRecurse(isPart, found) end)
    for i = 0, found:size() - 1 do
        local it = found:get(i)
        local label = it:getDisplayName()
        if wornBy(self.player, it) then label = "* " .. label end
        local list = (isLeg(it) and self.legs) or (Modular.IsHead(it) and self.heads) or self.bases
        local row = list:addItem(label, it)
        row.info = (sideOf(it) == "L" and getText("IGUI_TOC_WB_Left") or getText("IGUI_TOC_WB_Right")) .. "  "
            .. math.floor(it:getCondition() / math.max(1, it:getConditionMax()) * 100 + 0.5) .. "%"
        local col = Paint.ColorName(Paint.GetIndex(it))
        if col then row.tooltip = getItemNameFromFullType("Base.Paint" .. col) end
        if it == selB or it == selH or it == selL then list.selected = #list.items end
    end
    self:updateButtons()
end

function TOC_ProsthesisWorkbench:selected(list)
    local row = list.items[list.selected]
    return row and row.item or nil
end

function TOC_ProsthesisWorkbench:updateButtons()
    local b, h = self:selected(self.bases), self:selected(self.heads)
    self.btnFitBase:setEnable(b ~= nil and not wornBy(self.player, b))
    self.btnMountHead:setEnable(h ~= nil and not wornBy(self.player, h))
    self.btnRemove:setEnable((b ~= nil and wornBy(self.player, b)) or (h ~= nil and wornBy(self.player, h)))
    self.btnPaint:setEnable(Paint.IsPaintable(self:paintTarget()))
end

local function queueWear(player, item)
    ISInventoryPaneContextMenu.transferIfNeeded(player, item)
    ISTimedActionQueue.add(ISWearClothing:new(player, item))
end

function TOC_ProsthesisWorkbench:onFitBase()
    local b = self:selected(self.bases)
    if b then queueWear(self.player, b) end
end

function TOC_ProsthesisWorkbench:onMountHead()
    local h = self:selected(self.heads)
    if h then queueWear(self.player, h) end
end

---Pieza a pintar: la seleccionada en la última lista que se tocó (o la que haya seleccionada)
function TOC_ProsthesisWorkbench:paintTarget()
    if self.lastList then
        local it = self:selected(self.lastList)
        if it then return it end
    end
    return self:selected(self.heads) or self:selected(self.bases) or self:selected(self.legs)
end

function TOC_ProsthesisWorkbench:onPaint()
    local it = self:paintTarget()
    if it then PaintMenu.Show(self.player, it) end
end

function TOC_ProsthesisWorkbench:onRemove()
    local h, b = self:selected(self.heads), self:selected(self.bases)
    local target = (h and wornBy(self.player, h)) and h or ((b and wornBy(self.player, b)) and b or nil)
    if target then ISTimedActionQueue.add(ISUnequipAction:new(self.player, target, 50)) end
end

---Texto de estadísticas: lo puesto en cada lado y la combinación seleccionada
function TOC_ProsthesisWorkbench:statsLines()
    local L = {}
    local function pct(x) return tostring(math.floor((x or 1) * 100 + 0.5)) .. "%" end
    local function describe(tier)
        if not tier then return end
        L[#L + 1] = "  " .. getText(tier.hookLike and "IGUI_TOC_WB_NoGrip" or "IGUI_TOC_WB_Grip")
        L[#L + 1] = "  " .. getText(tier.twoHanded and "IGUI_TOC_WB_TwoHanded" or "IGUI_TOC_WB_OneHanded")
        L[#L + 1] = "  " .. getText("IGUI_TOC_WB_Combat", pct(tier.combatMod))
        L[#L + 1] = "  " .. getText("IGUI_TOC_WB_Speed", tostring(tier.timeBonus or 0))
        L[#L + 1] = "  " .. getText("IGUI_TOC_WB_Wear", string.format("%.1f", tier.wearPerAction or 0))
    end
    for _, side in ipairs({ "L", "R" }) do
        local base, head = Modular.GetWornBase(self.player, side), Modular.GetWornHead(self.player, side)
        L[#L + 1] = (side == "L" and getText("IGUI_TOC_WB_Left") or getText("IGUI_TOC_WB_Right")) .. ": "
            .. (base and base:getDisplayName() or getText("IGUI_TOC_WB_None")) .. (head and (" + " .. head:getDisplayName()) or "")
        if base then describe(StaticData.CombineTier(StaticData.GetProsthesisTier(base:getFullType()), head and head:getFullType())) end
    end
    local b, h = self:selected(self.bases), self:selected(self.heads)
    if b and h then
        L[#L + 1] = ""
        L[#L + 1] = getText("IGUI_TOC_WB_Preview") .. ": " .. b:getDisplayName() .. " + " .. h:getDisplayName()
        describe(StaticData.CombineTier(StaticData.GetProsthesisTier(b:getFullType()), h:getFullType()))
        local head = StaticData.GetHeadTier(h:getFullType())
        local bt = StaticData.GetProsthesisTier(b:getFullType())
        if head and head.metalBase and bt and bt.material ~= "metal" then L[#L + 1] = "  " .. getText("IGUI_TOC_HeadNeedsMetal") end
        if head and head.minBaseTier and bt and (bt.tier or 0) < head.minBaseTier then
            L[#L + 1] = "  " .. getText(head.minBaseTier >= 3 and "IGUI_TOC_HeadNeedsAdvancedBase" or "IGUI_TOC_HeadNotOnWood")
        end
        if head and head.side == "R" then L[#L + 1] = "  " .. getText("IGUI_TOC_WB_RightOnly") end
    end
    return L
end

function TOC_ProsthesisWorkbench:prerender()
    ISCollapsableWindow.prerender(self)
    self:drawRect(self.avatarX, self.avatar.y, self.avatar.width, self.avatar.height, 0.6, 0.08, 0.08, 0.09)
end

---------------- columna de estadísticas con dibujos (2026-10-17, "mejora la UI de estadísticas con algún dibujo")
-- Una tarjeta por brazo con prótesis y otra para la combinación seleccionada: iconos de la base y el cabezal, y una fila
-- por estadística con su icono (media/ui/TOC/WB_*.png, tools/make_wb_icons.py), sí / no o barra, y en la selección
-- flechas verdes / rojas frente a lo que lleva puesto en ese brazo.
local ICONS = {}
local function icon(name)
    if ICONS[name] == nil then ICONS[name] = getTexture("media/ui/TOC/WB_" .. name .. ".png") or false end
    return ICONS[name] or nil
end

local function fitText(s, w)
    local tm = getTextManager()
    if tm:MeasureStringX(UIFont.Small, s) <= w then return s end
    while #s > 3 and tm:MeasureStringX(UIFont.Small, s .. "...") > w do s = string.sub(s, 1, #s - 1) end
    return s .. "..."
end

local ROW_KEYS = { "IGUI_TOC_WB_LGrip", "IGUI_TOC_WB_LTwoHanded", "IGUI_TOC_WB_LCombat", "IGUI_TOC_WB_LSpeed", "IGUI_TOC_WB_LWear" }

---Alto de una tarjeta (para colocarlas antes de dibujar)
function TOC_ProsthesisWorkbench:cardHeight(nWarn)
    local rowH = math.max(18, FONT_HGT_SMALL + 2)
    return 6 + FONT_HGT_SMALL + 4 + math.max(34, FONT_HGT_SMALL * 2 + 6) + 4 + #ROW_KEYS * rowH + (nWarn or 0) * (FONT_HGT_SMALL + 2) + 6
end

---@param x number
---@param y number
---@param w number
---@param title string
---@param base InventoryItem?
---@param head InventoryItem?
---@param tier table combinación (StaticData.CombineTier)
---@param cmp table? combinación puesta en ese brazo, para las flechas
---@param warnings string[]
---@return number alto dibujado
function TOC_ProsthesisWorkbench:drawCard(x, y, w, title, base, head, tier, cmp, warnings, accent)
    local FS = FONT_HGT_SMALL
    local rowH = math.max(18, FS + 2)
    local extra = (tier and tier.strengthBonus) and 1 or 0         -- línea verde de bonificación (armazón cibernético)
    local h = self:cardHeight(#warnings + extra)
    self:drawRect(x, y, w, h, 0.45, 0.10, 0.10, 0.12)
    local ar, ag, ab = 0.4, 0.4, 0.4
    if accent then ar, ag, ab = 0.85, 0.55, 0.25 end
    self:drawRectBorder(x, y, w, h, 0.8, ar, ag, ab)
    local cy = y + 6
    self:drawText(title, x + 8, cy, accent and 1 or 0.9, accent and 0.75 or 0.9, accent and 0.45 or 0.9, 1, UIFont.Small)
    cy = cy + FS + 4
    -- iconos y nombres de las piezas
    local ix = x + 8
    if base and base:getTex() then self:drawTextureScaledAspect(base:getTex(), ix, cy, 32, 32, 1, 1, 1, 1) end
    self:drawText("+", ix + 35, cy + 8, 0.7, 0.7, 0.7, 1, UIFont.Small)
    if head and head:getTex() then self:drawTextureScaledAspect(head:getTex(), ix + 46, cy, 32, 32, 1, 1, 1, 1) end
    local tx = ix + 86
    local nw = x + w - 8 - tx
    self:drawText(fitText(base and base:getDisplayName() or getText("IGUI_TOC_WB_None"), nw), tx, cy, 0.95, 0.95, 0.95, 1, UIFont.Small)
    self:drawText(fitText(head and head:getDisplayName() or getText("IGUI_TOC_WB_NoHead"), nw), tx, cy + FS + 2,
        head and 0.95 or 0.6, head and 0.95 or 0.6, head and 0.95 or 0.6, 1, UIFont.Small)
    cy = cy + math.max(34, FS * 2 + 6) + 4
    -- filas
    local right = x + w - 8
    local valW = 46
    local barW = math.max(60, math.min(120, w - 8 - rowH - 4 - getTextManager():MeasureStringX(UIFont.Small, getText("IGUI_TOC_WB_LCombat")) - 16 - valW - 18))
    local function rowStart(iconName, key)
        local t = icon(iconName)
        if t then self:drawTextureScaled(t, x + 8, cy + 1, rowH - 2, rowH - 2, 1, 0.8, 0.8, 0.82) end
        self:drawText(getText(key), x + 8 + rowH + 4, cy + 1, 0.85, 0.85, 0.85, 1, UIFont.Small)
    end
    local function yesno(ok)
        local t = icon(ok and "yes" or "no")
        if t then
            if ok then self:drawTextureScaled(t, right - rowH, cy + 1, rowH - 2, rowH - 2, 1, 0.45, 0.85, 0.4)
            else self:drawTextureScaled(t, right - rowH, cy + 1, rowH - 2, rowH - 2, 1, 0.9, 0.35, 0.3) end
        end
    end
    local function arrow(better)
        if better == nil then return end
        local t = icon(better and "up" or "down")
        if not t then return end
        local ax = right - valW - barW - 16
        if better then self:drawTextureScaled(t, ax, cy + 3, rowH - 6, rowH - 6, 1, 0.45, 0.85, 0.4)
        else self:drawTextureScaled(t, ax, cy + 3, rowH - 6, rowH - 6, 1, 0.9, 0.35, 0.3) end
    end
    local function bar(frac, r, g, b, text)
        frac = math.max(0, math.min(1, frac))
        local bx, by, bh = right - valW - barW, cy + math.floor(rowH / 2) - 4, 8
        self:drawRect(bx, by, barW, bh, 0.8, 0.05, 0.05, 0.06)
        self:drawRect(bx, by, math.floor(barW * frac), bh, 0.95, r, g, b)
        self:drawRectBorder(bx, by, barW, bh, 0.6, 0.45, 0.45, 0.45)
        self:drawTextRight(text, right, cy + 1, 0.9, 0.9, 0.9, 1, UIFont.Small)
    end
    local function cmpv(a, b, higherBetter)
        if not cmp or a == nil or b == nil or math.abs(a - b) < 1e-4 then return nil end
        if higherBetter then return a > b end
        return a < b
    end
    rowStart("grip", ROW_KEYS[1]); yesno(not tier.hookLike); cy = cy + rowH
    rowStart("twohand", ROW_KEYS[2]); yesno(tier.twoHanded == true); cy = cy + rowH
    local cm = tier.combatMod or 1
    rowStart("combat", ROW_KEYS[3]); arrow(cmpv(cm, cmp and cmp.combatMod, true))
    bar((cm - 0.5) / 0.55, 0.85, 0.55, 0.25, tostring(math.floor(cm * 100 + 0.5)) .. "%"); cy = cy + rowH
    local tb = tier.timeBonus or 0
    rowStart("speed", ROW_KEYS[4]); arrow(cmpv(tb, cmp and cmp.timeBonus, true))
    bar(tb / 6, 0.35, 0.65, 0.9, "+" .. tostring(tb)); cy = cy + rowH
    local wp = tier.wearPerAction or 0.5
    rowStart("wear", ROW_KEYS[5]); arrow(cmpv(wp, cmp and cmp.wearPerAction, false))
    local wf = 1 - math.min(1, wp / 1.0)
    bar(wf, 0.9 - 0.5 * wf, 0.35 + 0.5 * wf, 0.3, string.format("%.2f", wp)); cy = cy + rowH
    if extra > 0 then
        self:drawText(fitText("+" .. tostring(tier.strengthBonus) .. " " .. getText("IGUI_perks_Strength"), w - 16), x + 8, cy, 0.45, 0.9, 0.45, 1, UIFont.Small)
        cy = cy + FS + 2
    end
    for _, wtxt in ipairs(warnings) do
        self:drawText(fitText(wtxt, w - 16), x + 8, cy, 0.95, 0.45, 0.35, 1, UIFont.Small)
        cy = cy + FS + 2
    end
    return h
end

function TOC_ProsthesisWorkbench:drawStats()
    local x, w = self.statsX, self.width - self.statsX - PAD
    local y = self:titleBarHeight() + PAD
    self:drawText(getText("IGUI_TOC_WB_Stats"), x, y, 1, 1, 1, 1, UIFont.Medium)
    y = y + FONT_HGT_MEDIUM + 6
    local limit = self.contentBottom or (self.height - PAD)
    local worn, wornItems = {}, {}
    local b, h = self:selected(self.bases), self:selected(self.heads)
    -- la selección sólo se dibuja si no es exactamente lo que ya lleva puesto en ese brazo
    local showSel = false
    if b then
        local s = sideOf(b)
        local wb, wh = Modular.GetWornBase(self.player, s), Modular.GetWornHead(self.player, s)
        showSel = not (wb == b and wh == h)
    end
    local selH = showSel and self:cardHeight(2) + 6 or 0
    for _, side in ipairs({ "R", "L" }) do
        local base, head = Modular.GetWornBase(self.player, side), Modular.GetWornHead(self.player, side)
        local label = getText(side == "L" and "IGUI_TOC_WB_ArmLeft" or "IGUI_TOC_WB_ArmRight")
        if base then
            local tier = StaticData.CombineTier(StaticData.GetProsthesisTier(base:getFullType()), head and head:getFullType())
            worn[side] = tier
            if y + self:cardHeight(0) + selH <= limit then
                y = y + self:drawCard(x, y, w, label, base, head, tier, nil, {}) + 6
            else                                       -- sin sitio: una línea con el resumen
                local txt = label .. ": " .. base:getDisplayName() .. (head and (" + " .. head:getDisplayName()) or "")
                self:drawText(fitText(txt, w - 4), x + 2, y, 0.85, 0.85, 0.85, 1, UIFont.Small)
                y = y + FONT_HGT_SMALL + 6
            end
        else
            self:drawText(label .. ": " .. getText("IGUI_TOC_WB_None"), x + 2, y, 0.6, 0.6, 0.6, 1, UIFont.Small)
            y = y + FONT_HGT_SMALL + 6
        end
    end
    if b and showSel then
        local bt = StaticData.GetProsthesisTier(b:getFullType())
        local tier = StaticData.CombineTier(bt, h and h:getFullType())
        local warnings = {}
        local head = h and StaticData.GetHeadTier(h:getFullType())
        if head and head.metalBase and bt and bt.material ~= "metal" then warnings[#warnings + 1] = getText("IGUI_TOC_HeadNeedsMetal") end
        if head and head.minBaseTier and bt and (bt.tier or 0) < head.minBaseTier then
            warnings[#warnings + 1] = getText(head.minBaseTier >= 3 and "IGUI_TOC_HeadNeedsAdvancedBase" or "IGUI_TOC_HeadNotOnWood")
        end
        if head and head.side == "R" then warnings[#warnings + 1] = getText("IGUI_TOC_WB_RightOnly") end
        y = y + self:drawCard(x, y, w, getText("IGUI_TOC_WB_Preview"), b, h, tier, worn[sideOf(b)], warnings, true) + 6
    end
end

function TOC_ProsthesisWorkbench:render()
    ISCollapsableWindow.render(self)
    self:drawStats()
    self.tick = (self.tick or 0) + 1
    if self.tick % 20 == 0 then
        if not TOC_ProsthesisWorkbench.FindBench(self.player) then self:close(); return end     -- se alejó de la mesa
        self:refresh()                                         -- tras poner / quitar piezas
    end
end

function TOC_ProsthesisWorkbench:close()
    self:setVisible(false); self:removeFromUIManager(); instance = nil
end

function TOC_ProsthesisWorkbench:new(player)
    local tm = getTextManager()
    local btnW = 0
    for _, k in ipairs(BTN_KEYS) do btnW = math.max(btnW, tm:MeasureStringX(UIFont.Small, getText(k)) + 24) end
    btnW = math.max(110, btnW)
    local listW = math.max(360, tm:MeasureStringX(UIFont.Small, "Armazón de prótesis cibernético  derecha 100%") + 40)
    local avatarW = 230
    local statsW = math.max(400, tm:MeasureStringX(UIFont.Small, getText("IGUI_TOC_WB_LCombat")) + 300)
    local w = math.max(PAD * 4 + listW + avatarW + statsW, PAD * 2 + 5 * (btnW + 6))
    -- alto: dos tarjetas de brazo + la vista previa con dos avisos, título y botones
    local rowH = math.max(18, FONT_HGT_SMALL + 2)
    local cardH = 6 + FONT_HGT_SMALL + 4 + math.max(34, FONT_HGT_SMALL * 2 + 6) + 4 + 5 * rowH + 6
    local th = getTextManager():getFontHeight(UIFont.Small) + 4
    local h = th + PAD + FONT_HGT_MEDIUM + 6 + 3 * (cardH + 6) + 2 * (FONT_HGT_SMALL + 2) + PAD + BTN_H + PAD
    h = math.max(560, math.min(h, getCore():getScreenHeight() - 60))
    w = math.min(w, getCore():getScreenWidth() - 40)
    local o = ISCollapsableWindow:new(getCore():getScreenWidth() / 2 - w / 2, getCore():getScreenHeight() / 2 - h / 2, w, h)
    setmetatable(o, self); self.__index = self
    o.listW, o.avatarW, o.btnW = listW, avatarW, btnW
    o.player = player
    o.title = getText("IGUI_TOC_WB_Title")
    o.resizable = false
    return o
end

---------------- la mesa (mueble TOCPlus_bench_0..3, ver scripts/TOC_workbench.txt)
local BENCH_PREFIX = "TOCPlus_bench_"
local BENCH_RANGE = 2

local function isBench(obj)
    local spr = obj and obj.getSprite and obj:getSprite()
    local name = spr and spr:getName()
    return name ~= nil and string.sub(name, 1, #BENCH_PREFIX) == BENCH_PREFIX
end

---Mesa del banco a BENCH_RANGE casillas o menos (misma planta)
---@param player IsoPlayer
---@return IsoObject?
function TOC_ProsthesisWorkbench.FindBench(player)
    local sq = player and player:getCurrentSquare()
    if not sq then return nil end
    local cell = getCell()
    for dx = -BENCH_RANGE, BENCH_RANGE do
        for dy = -BENCH_RANGE, BENCH_RANGE do
            local s = cell:getGridSquare(sq:getX() + dx, sq:getY() + dy, sq:getZ())
            if s then
                local objs = s:getObjects()
                for i = 0, objs:size() - 1 do
                    if isBench(objs:get(i)) then return objs:get(i) end
                end
            end
        end
    end
    return nil
end

function TOC_ProsthesisWorkbench.Open(player)
    if not TOC_ProsthesisWorkbench.FindBench(player) then return end
    if instance then instance:close() end
    instance = TOC_ProsthesisWorkbench:new(player)
    instance:initialise(); instance:addToUIManager()
end

---Acción corta para abrir el banco al llegar a la mesa
local OpenAction = ISBaseTimedAction:derive("TOCOpenWorkbenchAction")
function OpenAction:new(character) local o = ISBaseTimedAction.new(self, character); o.maxTime = 1; o.skipTOC = true; return o end
function OpenAction:isValid() return true end
function OpenAction:perform() TOC_ProsthesisWorkbench.Open(self.character); ISBaseTimedAction.perform(self) end

local function walkAndOpen(player, bench)
    if luautils.walkAdj(player, bench:getSquare(), true) then ISTimedActionQueue.add(OpenAction:new(player)) end
end

local function OnFillWorldObjectContextMenu(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    if not player then return end
    for _, obj in ipairs(worldobjects) do
        if isBench(obj) then
            if test then return true end
            context:addOption(getText("ContextMenu_TOC_Workbench"), player, walkAndOpen, obj)
            return
        end
    end
end
Events.OnFillWorldObjectContextMenu.Add(OnFillWorldObjectContextMenu)

local function OnFillInventoryObjectContextMenu(playerNum, context, items)
    local player = getSpecificPlayer(playerNum)
    if not player then return end
    for i = 1, #items do
        local it = items[i]
        if type(it) == "table" and it.items then it = it.items[1] end
        if isPart(it) then
            local opt = context:addOption(getText("ContextMenu_TOC_Workbench"), player, TOC_ProsthesisWorkbench.Open)
            if not TOC_ProsthesisWorkbench.FindBench(player) then
                opt.notAvailable = true
                local tip = ISInventoryPaneContextMenu.addToolTip(); tip.description = getText("Tooltip_TOC_NeedBench"); opt.toolTip = tip
            end
            return
        end
    end
end
Events.OnFillInventoryObjectContextMenu.Add(OnFillInventoryObjectContextMenu)
