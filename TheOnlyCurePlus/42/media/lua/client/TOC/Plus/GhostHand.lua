-- TOC+ 3.2.0: "mano fantasma" (comentario del Workshop: "when I took some painkillers, they did it with their ghost
-- left hand"). Las acciones de una mano (pastillas, beber, fumar, comer, leer, verter...) tienen copias de sus nodos de
-- animación (media/AnimSets/player/actions/TOC_NoHand*, tools/make_mirror_anims.py) con el clip espejado que el juego
-- elige cuando TOC_NoHandL / TOC_NoHandR es "true". Aquí:
--  1) esas variables, en todos los jugadores que ve este cliente (los remotos también: se deduce de la ropa que llevan,
--     que el juego ya sincroniza), y
--  2) el objeto de la acción nunca se pinta en la mano que falta: pasa a la otra (los clips espejados mueven Prop1 y
--     Prop2 como su mano).
-- Una mano "falta" si está amputada y no lleva una prótesis que agarre (mecánica o médica; gancho, mano de madera y
-- motosierra no). Con las dos manos amputadas no se espeja nada.

local StaticData = require("TOC/StaticData")

local GhostHand = {}
local LEVELS = { "Hand", "ForeArm", "UpperArm" }

---@param player IsoPlayer
---@return string? "L" o "R": la mano que falta (sólo si la otra está)
function GhostHand.Missing(player)
    local cut, grip = { L = false, R = false }, { L = false, R = false }
    local worn = player:getWornItems()
    if not worn then return nil end
    for i = 0, worn:size() - 1 do
        local it = worn:get(i):getItem()
        local ft = it and it:getFullType()
        if ft then
            for _, lv in ipairs(LEVELS) do
                for _, s in ipairs({ "L", "R" }) do
                    if ft == StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. lv .. "_" .. s then cut[s] = true end
                end
            end
            local base, side = StaticData.GetProsthesisBase(ft)
            local tier = base and StaticData.PROSTHESIS_TIERS[base]
            if tier and tier.group == "Top" and not tier.hookLike then grip[side] = true end
        end
    end
    local l = not cut.L or grip.L
    local r = not cut.R or grip.R
    if l and not r then return "R" end
    if r and not l then return "L" end
    return nil
end

local function apply(player)
    local ok, miss = pcall(GhostHand.Missing, player)
    if not ok then return end
    player:setVariable("TOC_NoHandL", miss == "L" and "true" or "false")
    player:setVariable("TOC_NoHandR", miss == "R" and "true" or "false")
end

local tick = 0
Events.OnTick.Add(function()
    tick = tick + 1
    if tick % 30 ~= 0 then return end
    local players = IsoPlayer.getPlayers()
    for i = 0, players:size() - 1 do
        local p = players:get(i)
        if p and not p:isDead() then apply(p) end
    end
    if isClient() then
        local online = getOnlinePlayers()
        for i = 0, (online and online:size() or 0) - 1 do
            local p = online:get(i)
            if p and not p:isLocalPlayer() then apply(p) end
        end
    end
end)

-- el objeto de la acción, a la mano que existe
local function redirect(self, primary, secondary)
    local chr = self and self.character
    if not chr or not instanceof(chr, "IsoPlayer") then return primary, secondary end
    local ok, miss = pcall(GhostHand.Missing, chr)
    if not ok then return primary, secondary end
    -- sin la derecha: lo de la derecha pasa a la izquierda (las acciones de dos objetos, cuchara y lata, abrelatas y
    -- lata..., son de la mano derecha y se espejan: queda el objeto principal)
    if miss == "R" and primary ~= nil then return nil, primary end
    if miss == "L" and secondary ~= nil then
        if primary ~= nil then return primary, nil end      -- acción de la derecha con dos objetos: no se espeja
        return secondary, nil                                -- pastillas, bebidas, cigarro...: pasan a la derecha
    end
    return primary, secondary
end

local origObject = ISBaseTimedAction.setOverrideHandModels
function ISBaseTimedAction:setOverrideHandModels(primary, secondary, resetModel)
    primary, secondary = redirect(self, primary, secondary)
    return origObject(self, primary, secondary, resetModel)
end

local origString = ISBaseTimedAction.setOverrideHandModelsString
function ISBaseTimedAction:setOverrideHandModelsString(primary, secondary, resetModel)
    primary, secondary = redirect(self, primary, secondary)
    return origString(self, primary, secondary, resetModel)
end

return GhostHand
