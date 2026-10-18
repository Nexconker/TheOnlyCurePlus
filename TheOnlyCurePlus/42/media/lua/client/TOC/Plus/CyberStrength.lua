-- TOC+ 3.3: el armazón cibernético da +1 de Fuerza mientras está puesto (2026-10-17, pedido). Un solo punto aunque
-- se lleven dos brazos cibernéticos. Se aplica con LevelPerk / LoseLevel (como hace el juego) y se apunta en
-- modData.TOCCyberStr para quitar exactamente lo que se dio; SyncXp lo manda al servidor en multijugador.
-- Si la Fuerza ya está en 10 no se da nada (y no se quita nada al soltarlo).

local Modular = require("TOC/Plus/ModularProsthesis")
local StaticData = require("TOC/StaticData")
------------------

local CyberStrength = {}

---Bonificación que corresponde a lo que lleva puesto
---@param player IsoPlayer
---@return integer
function CyberStrength.Wanted(player)
    for _, side in ipairs({ "L", "R" }) do
        local base = Modular.GetWornBase(player, side)
        local tier = base and StaticData.GetProsthesisTier(base:getFullType())
        if tier and tier.strengthBonus then return tier.strengthBonus end
    end
    return 0
end

---@param player IsoPlayer
function CyberStrength.Update(player)
    local md = player:getModData()
    local have = md.TOCCyberStr or 0
    local want = CyberStrength.Wanted(player)
    if want == have then return end
    if want > have then
        local given = 0
        for _ = 1, want - have do
            if player:getPerkLevel(Perks.Strength) >= 10 then break end
            player:LevelPerk(Perks.Strength); given = given + 1
        end
        md.TOCCyberStr = have + given
        if given == 0 and have == 0 then md.TOCCyberStr = 0; md.TOCCyberStrCapped = true; return end
    else
        for _ = 1, have - want do
            if player:getPerkLevel(Perks.Strength) > 0 then player:LoseLevel(Perks.Strength) end
        end
        md.TOCCyberStr = want
    end
    md.TOCCyberStrCapped = nil
    if isClient() then pcall(SyncXp, player) end
end

if not isServer() then
    local ticks = 0
    Events.OnPlayerUpdate.Add(function(player)
        if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
        ticks = ticks + 1
        if ticks % 60 ~= 0 then return end
        local md = player:getModData()
        if md.TOCCyberStrCapped and CyberStrength.Wanted(player) > 0 then return end     -- en 10: no reintentar cada segundo
        if md.TOCCyberStrCapped then md.TOCCyberStrCapped = nil end
        pcall(CyberStrength.Update, player)
    end)
end

return CyberStrength
