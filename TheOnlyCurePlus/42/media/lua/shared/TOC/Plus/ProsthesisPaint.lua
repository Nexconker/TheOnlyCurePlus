-- TOC+ 3.3: apariencias pintables de las piezas modulares (bases y cabezales). Cada pieza trae en su clothing XML las
-- texturas de tools/make_paint_variants.py como textureChoices: 0 = acabado original, 1.. = un color de pintura vanilla
-- (Base.Paint<Color>). La elección va en el visual del ítem (setTextureChoice) y en modData.TOCPaint.
-- Ojo: el juego elige un textureChoice al azar al crear la prenda; Paint.Normalize lo deja en el original la primera vez.

require "TimedActions/ISWearClothing"
local Modular = require("TOC/Plus/ModularProsthesis")
local StaticData = require("TOC/StaticData")
------------------

local Paint = {}

-- mismo orden que PAINTS en tools/make_paint_variants.py (índice de textureChoices = posición)
Paint.COLORS = { "Black", "White", "Grey", "Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Pink" }
-- color de muestra de cada pintura (mismos valores que tools/make_paint_variants.py), para la UI
Paint.RGB = { { 38, 38, 42 }, { 232, 232, 228 }, { 128, 130, 134 }, { 168, 34, 30 }, { 214, 104, 28 }, { 222, 184, 40 },
    { 78, 102, 52 }, { 40, 72, 150 }, { 98, 52, 130 }, { 214, 116, 150 } }
Paint.INDEX = {}
for i, c in ipairs(Paint.COLORS) do Paint.INDEX[c] = i end

---@param item InventoryItem
---@return boolean
function Paint.IsPaintable(item)
    if not item then return false end
    local tier = StaticData.GetProsthesisTier(item:getFullType())
    local leg = tier ~= nil and tier.group == "Bottom"                  -- piernas: todas pintables (2026-10-17)
    if not leg and not (Modular.IsModularBase(item) or Modular.IsHead(item)) then return false end
    if string.find(item:getFullType(), "HeadChainsaw", 1, true) then return false end      -- la motosierra conserva su carcasa
    -- piezas de otros mods (TOC_Modular): sólo si traen las 11 textureChoices en este orden (paintable = true)
    local t = StaticData.GetHeadTier(item:getFullType()) or StaticData.GetProsthesisTier(item:getFullType())
    return not (t and t.external and not t.paintable)
end

---@param item InventoryItem
---@return integer 0 = original
function Paint.GetIndex(item)
    local md = item and item:getModData()
    return (md and md.TOCPaint) or 0
end

---Color de un índice ("Red"...) o nil para el original
function Paint.ColorName(idx)
    return Paint.COLORS[idx or 0]
end

local function applyVisual(item, idx)
    local vis = item:getVisual()
    if vis then vis:setTextureChoice(idx) end
    item:synchWithVisual()
    item:getModData().TOCPaint = idx
end

---Aplica un color (0 = original). Si la pieza está puesta, refresca el modelo y lo envía en multijugador.
---@param character IsoPlayer
---@param item InventoryItem
---@param idx integer
function Paint.Apply(character, item, idx)
    applyVisual(item, idx)
    if character and character:isEquippedClothing(item) then
        character:resetModelNextFrame()
        if isServer() or isClient() then sendClothing(character, item:getBodyLocation(), item) end
    end
end

---Primera vez que se ve la pieza: deshace el textureChoice al azar con el que la crea el juego
---@param item InventoryItem
function Paint.Normalize(item)
    if Paint.IsPaintable(item) and item:getModData().TOCPaint == nil then applyVisual(item, 0) end
end

---Normaliza todo lo que lleva puesto y en el inventario (al cargar y de vez en cuando)
---@param character IsoPlayer
function Paint.NormalizeAll(character)
    local found = ArrayList.new()
    pcall(function() character:getInventory():getAllEvalRecurse(function(it) return Paint.IsPaintable(it) and it:getModData().TOCPaint == nil end, found) end)
    local worn = false
    for i = 0, found:size() - 1 do
        local it = found:get(i)
        applyVisual(it, 0)
        if character:isEquippedClothing(it) then worn = true end
    end
    if worn then character:resetModelNextFrame() end
end

-- al ponerse una pieza: si nunca se ha visto, acabado original (no el textureChoice al azar)
local og_wear_complete = ISWearClothing.complete
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:complete()
    pcall(Paint.Normalize, self.item)
    return og_wear_complete(self)
end
local og_wear_perform = ISWearClothing.perform
---@diagnostic disable-next-line: duplicate-set-field
function ISWearClothing:perform()
    pcall(Paint.Normalize, self.item)
    return og_wear_perform(self)
end

if not isServer() then
    local ticks = 0
    Events.OnPlayerUpdate.Add(function(player)
        if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
        ticks = ticks + 1
        if ticks % 300 == 0 then pcall(Paint.NormalizeAll, player) end
    end)
end

return Paint
