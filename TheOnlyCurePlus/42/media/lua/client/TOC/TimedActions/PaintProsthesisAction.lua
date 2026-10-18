require "TimedActions/ISBaseTimedAction"
local Paint = require("TOC/Plus/ProsthesisPaint")
-----------------------------

-- TOC+ 3.3: pintar una pieza modular (base o cabezal) con un bote de pintura vanilla y un pincel, o rascar la pintura
-- para volver al acabado original. Corre en el cliente como el resto de acciones de TOC+; el modelo puesto se envía con
-- sendClothing y el bote se gasta con UseAndSync.

---@class TOCPaintProsthesisAction : ISBaseTimedAction
local PaintAction = ISBaseTimedAction:derive("TOCPaintProsthesisAction")

---@param character IsoPlayer
---@param item InventoryItem pieza a pintar
---@param paint InventoryItem? bote de pintura (nil = rascar la pintura)
---@param idx integer índice de color (0 = original)
function PaintAction:new(character, item, paint, idx)
    local o = ISBaseTimedAction.new(self, character)
    o.character = character
    o.item = item
    o.paint = paint
    o.idx = idx
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = character:isTimedActionInstant() and 1 or (paint and 180 or 260)
    return o
end

function PaintAction:isValid()
    local inv = self.character:getInventory()
    if not inv:containsRecursive(self.item) then return false end
    -- sólo en el banco de prótesis (mesa a 2 casillas)
    if TOC_ProsthesisWorkbench and TOC_ProsthesisWorkbench.FindBench and not TOC_ProsthesisWorkbench.FindBench(self.character) then return false end
    if self.paint then
        if not inv:containsRecursive(self.paint) or self.paint:getCurrentUsesFloat() <= 0 then return false end
        if not inv:getFirstTagRecurse(ItemTag.PAINTBRUSH) then return false end
    end
    return true
end

function PaintAction:start()
    self:setActionAnim("Craft")
    self.character:setMetabolicTarget(Metabolics.LightWork)
end

function PaintAction:update()
    self.item:setJobDelta(self:getJobDelta())
end

function PaintAction:stop()
    self.item:setJobDelta(0.0)
    ISBaseTimedAction.stop(self)
end

function PaintAction:perform()
    self.item:setJobDelta(0.0)
    Paint.Apply(self.character, self.item, self.idx)
    if self.paint then self.paint:UseAndSync() end
    ISBaseTimedAction.perform(self)
end

return PaintAction
