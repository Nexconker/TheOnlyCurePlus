-- TOC+ 3.3: menú "Pintar" de las piezas modulares. Sólo se abre desde el banco de prótesis (botón Pintar, con la mesa
-- al lado; 2026-10-17: "sólo quiero que el banco de prótesis te deje pintar la prótesis"). Un color por cada bote de
-- pintura vanilla que lleve el jugador (hace falta un pincel); "Rascar la pintura" vuelve al acabado original.

local Paint = require("TOC/Plus/ProsthesisPaint")
local PaintAction = require("TOC/TimedActions/PaintProsthesisAction")
------------------

local PaintMenu = {}

local function queuePaint(player, item, paint, idx)
    ISInventoryPaneContextMenu.transferIfNeeded(player, item)
    if paint then ISInventoryPaneContextMenu.transferIfNeeded(player, paint) end
    ISTimedActionQueue.add(PaintAction:new(player, item, paint, idx))
end

---Rellena un menú con los colores disponibles para la pieza
---@param player IsoPlayer
---@param menu ISContextMenu
---@param it InventoryItem
function PaintMenu.Fill(player, menu, it)
    local inv = player:getInventory()
    local brush = inv:getFirstTagRecurse(ItemTag.PAINTBRUSH)
    local current = Paint.GetIndex(it)
    local any = false
    for idx, color in ipairs(Paint.COLORS) do
        local ft = "Base.Paint" .. color
        local paint = inv:getFirstEvalRecurse(function(p) return p:getFullType() == ft and p:getCurrentUsesFloat() > 0 end)
        if paint then
            any = true
            local o = menu:addOption(getItemNameFromFullType(ft), player, queuePaint, it, paint, idx)
            if not brush then
                o.notAvailable = true
                local tip = ISInventoryPaneContextMenu.addToolTip(); tip.description = getText("Tooltip_TOC_NeedBrush"); o.toolTip = tip
            elseif idx == current then
                o.notAvailable = true
            end
        end
    end
    if not any then
        local o = menu:addOption(getText("ContextMenu_TOC_NoPaint"), nil, nil); o.notAvailable = true
    end
    if current ~= 0 then menu:addOption(getText("ContextMenu_TOC_StripPaint"), player, queuePaint, it, nil, 0) end
end

---Menú suelto en la posición del ratón (botón Pintar del banco)
---@param player IsoPlayer
---@param it InventoryItem
function PaintMenu.Show(player, it)
    if not Paint.IsPaintable(it) then return end
    local menu = ISContextMenu.get(player:getPlayerNum(), getMouseX(), getMouseY())
    PaintMenu.Fill(player, menu, it)
end

return PaintMenu
