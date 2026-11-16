-- TOC+ 3.3: el armazón cibernético da +1 de Fuerza mientras está puesto (2026-10-17, pedido). Un solo punto aunque
-- se lleven dos brazos cibernéticos.
-- 3.3.8 (Workshop: "the +1 strength keeps reapplying itself", "my strength level is constantly flickering" en
-- multijugador): hasta la 3.3.7 el punto se daba con LevelPerk desde el cliente. En multijugador la experiencia la manda
-- el servidor, que devolvía la Fuerza a su nivel cada pocos segundos, y el mod la volvía a subir: parpadeo. Ahora el
-- punto se da como EXPERIENCIA (lo que mide el siguiente nivel, sin multiplicadores) por el mismo camino que usa el
-- juego: en el servidor en multijugador y en local en partidas de un jugador. Al quitarse el armazón se resta
-- exactamente lo que se dio. Cuánto se dio se guarda en los datos del mod (plus().cyberStrXp), que en multijugador
-- son del servidor: el cliente no puede tocarlo.

local Modular = require("TOC/Plus/ModularProsthesis")
local StaticData = require("TOC/StaticData")
local DataController = require("TOC/Controllers/DataController")
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

---Nivel de Fuerza que respalda la experiencia (como XpUpdate.checkForLosingLevel)
---@param player IsoPlayer
---@return integer?
local function XpLevel(player)
    local ok, lvl = pcall(function()
        local xp = player:getXp():getXP(Perks.Strength)
        local perk = PerkFactory.getPerk(Perks.Strength)
        local l = 0
        for i = 1, 10 do
            if xp >= perk:getTotalXpForLevel(i) then l = i else break end
        end
        return l
    end)
    return ok and lvl or nil
end

---Quita los niveles que no respalda la experiencia (como hace el juego), como mucho `max`
local function DropUnbacked(player, max)
    local xl = XpLevel(player)
    if not xl then return end
    for _ = 1, max do
        if player:getPerkLevel(Perks.Strength) > xl then player:LoseLevel(Perks.Strength) else return end
    end
end

local function AddStrengthXp(player, amount)
    if addXpNoMultiplier then
        addXpNoMultiplier(player, Perks.Strength, amount)
    else
        player:getXp():AddXP(Perks.Strength, amount, false, false, false)
    end
end

---@param player IsoPlayer
function CyberStrength.Update(player)
    local dc = DataController.GetReady(player:getUsername())
    if not dc then return end
    local plus = dc:plus()
    local md = player:getModData()
    -- hasta la 3.3.7: niveles dados con LevelPerk (sin experiencia). Se quitan una vez y se pasa al sistema nuevo.
    if md.TOCCyberStr ~= nil then
        local old = tonumber(md.TOCCyberStr) or 0
        md.TOCCyberStr = nil; md.TOCCyberStrCapped = nil
        if old > 0 then DropUnbacked(player, old) end
    end
    local want = CyberStrength.Wanted(player) > 0
    local given = tonumber(plus.cyberStrXp) or 0
    if want and given <= 0 then
        local lvl = player:getPerkLevel(Perks.Strength)
        if lvl >= 10 then return end
        local perk = PerkFactory.getPerk(Perks.Strength)
        local amount = perk:getTotalXpForLevel(lvl + 1) - perk:getTotalXpForLevel(lvl)
        if not amount or amount <= 0 then return end
        plus.cyberStrXp = amount                       -- antes de darla: nunca dos veces
        AddStrengthXp(player, amount)
    elseif not want and given > 0 then
        plus.cyberStrXp = nil
        local cur = player:getXp():getXP(Perks.Strength) or 0
        AddStrengthXp(player, -math.min(given, cur))
        DropUnbacked(player, 2)
    end
end

if isServer() then
    -- multijugador: el servidor, para todos los conectados
    Events.EveryOneMinute.Add(function()
        local list = getOnlinePlayers()
        for i = 0, (list and list:size() or 0) - 1 do
            local pl = list:get(i)
            if pl and not pl:isDead() then
                local ok, err = pcall(CyberStrength.Update, pl)
                if not ok then print("[TOC+] CyberStrength: " .. tostring(err)) end
            end
        end
    end)
elseif not isClient() then
    -- un jugador: en local
    local ticks = 0
    Events.OnPlayerUpdate.Add(function(player)
        if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() or player:isDead() then return end
        ticks = ticks + 1
        if ticks % 60 ~= 0 then return end
        local ok, err = pcall(CyberStrength.Update, player)
        if not ok then print("[TOC+] CyberStrength: " .. tostring(err)) end
    end)
end

return CyberStrength
