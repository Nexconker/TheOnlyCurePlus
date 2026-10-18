-- TOC+ 3.3: el submenú "Ponerse" de las prótesis (lado izquierdo / lado derecho, que arma el juego con los
-- ClothingItemExtra del ítem) sólo ofrece el lado amputado cuando la otra extremidad está entera
-- (2026-10-17: "que sólo me aparezca la opción de ponérmelo en un solo brazo si mi otra extremidad no está cortada").
-- Con las dos extremidades amputadas, o con ninguna, se deja como está.

local StaticData = require("TOC/StaticData")
local DataController = require("TOC/Controllers/DataController")
------------------

---Grupo de la pieza ("Top" brazos, "Bottom" piernas) y su lado, o nil si no es una prótesis de TOC
local function groupAndSide(fullType)
    if type(fullType) ~= "string" then return nil end
    local tier, side = StaticData.GetProsthesisTier(fullType), nil
    local _, s = StaticData.GetProsthesisBase(fullType)
    side = s
    if tier then return tier.group, side end
    if StaticData.GetHeadTier(fullType) then return "Top", side end
    return nil
end

local og_doClothingItemExtraMenu = ISInventoryPaneContextMenu.doClothingItemExtraMenu
ISInventoryPaneContextMenu.doClothingItemExtraMenu = function(context, clothingItemExtra, playerObj)
    local n0 = context.numOptions or 0
    og_doClothingItemExtraMenu(context, clothingItemExtra, playerObj)
    local ok, err = pcall(function()
        local group = groupAndSide(clothingItemExtra:getFullType())
        if not group or not playerObj then return end
        local dc = DataController.GetReady(playerObj:getUsername())
        if not dc then return end
        local limb = group == "Top" and "Hand_" or "Foot_"
        local cutL, cutR = dc:getIsCut(limb .. "L"), dc:getIsCut(limb .. "R")
        if cutL == cutR then return end                       -- las dos o ninguna: sin cambios
        local keep = cutL and "L" or "R"
        -- la opción "Ponerse" recién añadida y su submenú
        for i = (context.numOptions or 1) - 1, math.max(1, n0), -1 do
            local opt = context.options[i]
            if opt and opt.subOption then
                local sub = context:getSubMenu(opt.subOption)
                if sub then
                    local drop = {}
                    for _, o in ipairs(sub.options) do
                        local _, side = groupAndSide(o.param1)
                        if side and side ~= keep then drop[#drop + 1] = o.name end
                    end
                    for _, name in ipairs(drop) do sub:removeOptionByName(name) end
                end
                break
            end
        end
    end)
    if not ok then print("[TOC+] ProsthesisSideMenu: " .. tostring(err)) end
end
