-- TOC+ 3.3.8 (Workshop: "I can't get the blood off what's left of that arm"): el muñón es una prenda que no se puede
-- quitar, así que lavarse no le llegaba (el juego sólo limpia la piel; la ropa se lava quitándola). Al lavarse se limpian
-- también la sangre y la suciedad de los muñones puestos. complete() corre en el servidor en multijugador.

local StaticData = require("TOC/StaticData")
------------------

local function CleanStumps(character)
    local worn = character:getWornItems()
    local changed = false
    for i = 0, (worn and worn:size() or 0) - 1 do
        local item = worn:get(i):getItem()
        if item and string.find(item:getFullType(), StaticData.AMPUTATION_CLOTHING_ITEM_BASE, 1, true) == 1 then
            local v = item:getVisual()
            if v then
                v:removeBlood(); v:removeDirt()
                pcall(function() item:setBloodLevel(0) end)
                pcall(function() item:setDirtyness(0) end)
                if isServer() and sendClothing then pcall(sendClothing, character, item:getBodyLocation(), item) end
                changed = true
            end
        end
    end
    if changed then character:resetModelNextFrame() end
end

if ISWashYourself then
    local og_ISWashYourself_complete = ISWashYourself.complete
    ---@diagnostic disable-next-line: duplicate-set-field
    function ISWashYourself:complete()
        local result = og_ISWashYourself_complete(self)
        if self.character and instanceof(self.character, "IsoPlayer") then pcall(CleanStumps, self.character) end
        return result
    end
end
