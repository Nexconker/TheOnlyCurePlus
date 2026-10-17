-- TOC+ LegMobility: what a leg amputee can do. Runs for the local player only.
--  NONE   -> no longer produced (kept for API users): a missing leg without crutch now crawls
--  CRAWL  -> a leg missing with no crutch, or both legs with no prosthesis: crawls on the ground (animation variable TOC_Crawl
--            selects the zombie crawler clips added in media/AnimSets/player/*/TOC_Crawl*.xml)
--  CRUTCH -> crutch in a hand: walk only, no running, stamina drains while moving (per second, sandbox CrutchStaminaDrain)
--  PEG    -> peg leg: run but never sprint
--  FULL   -> mechanical / medical leg or no leg amputation at all
local DataController = require("TOC/Controllers/DataController")
local StaticData = require("TOC/StaticData")
local Messages = require("TOC/Plus/Messages")
-----------------

local LegMobility = {}
LegMobility.applied = { blocked = false, cantSprint = false, crawl = false, crutch = false, crutchSide = nil }
LegMobility.CRUTCH_VARS = { "TOC_Crutch1", "TOC_Crutch2", "TOC_Crutch3", "TOC_Crutch4", "TOC_Crutch5", "TOC_Crutch6", "TOC_Crutch7" }
LegMobility.missingSide = "L"
LegMobility.CRAWL_VARS = { "TOC_Crawl", "TOC_Crawl2", "TOC_Crawl3", "TOC_Crawl4", "TOC_Crawl5", "TOC_Crawl6", "TOC_Crawl7" }
LegMobility.tick = 0
LegMobility.lastHint = 0
LegMobility.current = StaticData.MOBILITY.FULL
LegMobility.oneLeg = false     -- crawling with one leg left: the hint asks for a crutch

local CRUTCH_TYPE = "TOC.Crutch"

-- Resistencia (3.1.1): antes se restaban 0.0025 (muleta) / 0.004 (arrastre) cada 10 actualizaciones del jugador, es decir,
-- por FOTOGRAMA: a 60 fps cansado en ~17 s con muleta, a 144 fps en ~7 ("cansado tras 7-10 pasos", comentario del Workshop).
-- Ahora es por segundo real mientras se mueve, con opciones de sandbox. 100 % = moodle de cansancio tras ~1 min con muleta y
-- ~40 s arrastrándose; los rasgos de pierna amputada (ya sabe usar muletas) gastan el % de AmputeeTraitStaminaDrain.
local DRAIN_PER_SECOND = { crutch = 0.004, crawl = 0.006 }
local LEG_TRAITS = { "Amputee_Foot", "Amputee_LowerLeg", "Amputee_Foot_R", "Amputee_LowerLeg_R" }
LegMobility.dt = 0

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

local function isPractised(player)
    local reg = _TOCRegistries and _TOCRegistries.traits
    if not reg then return false end
    for _, k in ipairs(LEG_TRAITS) do
        if reg[k] and player:hasTrait(reg[k]) then return true end
    end
    return false
end

---Resta la resistencia de dt segundos moviéndose con muleta ("crutch") o arrastrándose ("crawl").
local function drainEndurance(player, kind, dt)
    if dt <= 0 then return end
    local pct = sv(kind == "crutch" and "CrutchStaminaDrain" or "CrawlStaminaDrain", 100)
    if isPractised(player) then pct = pct * sv("AmputeeTraitStaminaDrain", 50) / 100 end
    local amount = DRAIN_PER_SECOND[kind] * dt * pct / 100
    if amount <= 0 then return end
    local stats = player:getStats()
    stats:set(CharacterStat.ENDURANCE, math.max(0, (stats:get(CharacterStat.ENDURANCE) or 1) - amount))
end

---@param player IsoPlayer
---@return boolean
function LegMobility.HasCrutch(player)
    local p = player:getPrimaryHandItem()
    local s = player:getSecondaryHandItem()
    return (p ~= nil and p:getFullType() == CRUTCH_TYPE) or (s ~= nil and s:getFullType() == CRUTCH_TYPE)
end

---@param player IsoPlayer
---@return string mobility
function LegMobility.Evaluate(player)
    local dc = DataController.GetReady(player:getUsername())
    if not dc or not dc:getIsAnyLimbCut() then return StaticData.MOBILITY.FULL end
    local missing, pegs = 0, 0
    LegMobility.oneLeg = false
    for _, side in ipairs(StaticData.SIDES_STR) do
        if dc:getIsCut("Foot_" .. side) then
            local t = dc:getProstType("Bottom_" .. side)
            local tier = t and StaticData.GetProsthesisTier(t) or nil
            if not dc:getIsProstEquippedGroup("Bottom_" .. side) then
                missing = missing + 1
                LegMobility.missingSide = side
            elseif tier and tier.sprint == false then
                pegs = pegs + 1
            end
        end
    end
    if missing >= 2 then return StaticData.MOBILITY.CRAWL end
    if missing == 1 then
        if LegMobility.HasCrutch(player) then return StaticData.MOBILITY.CRUTCH end
        -- one leg and nothing to lean on: crawl. It used to be NONE (frozen in place), and a character created with
        -- a leg amputee trait had no way to move at all.
        LegMobility.oneLeg = true
        return StaticData.MOBILITY.CRAWL
    end
    if pegs > 0 then return StaticData.MOBILITY.PEG end
    return StaticData.MOBILITY.FULL
end

local function setBlocked(player, blocked)
    if LegMobility.applied.blocked == blocked then return end
    pcall(function() player:setBlockMovement(blocked) end)
    LegMobility.applied.blocked = blocked
end

local function setCantSprint(player, cant)
    if LegMobility.applied.cantSprint == cant then return end
    pcall(function() player:setMoodleCantSprint(cant) end)
    LegMobility.applied.cantSprint = cant
end

local function setCrutchAnim(player, on)
    if LegMobility.applied.crutch == on and (not on or LegMobility.applied.crutchSide == LegMobility.missingSide) then return end
    pcall(function()
        for _, v in ipairs(LegMobility.CRUTCH_VARS) do player:setVariable(v, on and "true" or "false") end
        player:setVariable("TOC_CrutchSide", LegMobility.missingSide)
    end)
    LegMobility.applied.crutch = on; LegMobility.applied.crutchSide = LegMobility.missingSide
end

local function setCrawl(player, crawl)
    if LegMobility.applied.crawl == crawl then return end
    pcall(function()
        -- 7 variables iguales: el juego prefiere el nodo con más condiciones cumplidas (ver patch_crawl2.py)
        for _, v in ipairs(LegMobility.CRAWL_VARS) do player:setVariable(v, crawl and "true" or "false") end
        if crawl then
            if player:isSneaking() then player:setSneaking(false) end
            -- cae al suelo: tras la caída vanilla el estado idle ya elige el nodo de arrastre
            if not player:isKnockedDown() then player:setKnockedDown(true) end
        end
    end)
    LegMobility.applied.crawl = crawl
end

---@param player IsoPlayer
function LegMobility.Apply(player)
    local dt = math.min(LegMobility.dt, 1.0)        -- segundos reales desde la última vez (tope por pausas)
    LegMobility.dt = 0
    local m = LegMobility.Evaluate(player)
    LegMobility.current = m
    local inVehicle = player:getVehicle() ~= nil
    if m ~= StaticData.MOBILITY.CRAWL then setCrawl(player, false) end
    setCrutchAnim(player, m == StaticData.MOBILITY.CRUTCH and not inVehicle)
    if m == StaticData.MOBILITY.CRAWL then
        -- se arrastra: libre de moverse pero a ras de suelo, sin correr ni sigilo, gastando resistencia
        setBlocked(player, false)
        setCantSprint(player, true)
        setCrawl(player, not inVehicle)
        pcall(function()
            if player:isRunning() then player:setRunning(false) end
            if player:isSprinting() then player:setSprinting(false) end
            if player:isSneaking() then player:setSneaking(false) end
            if player:isPlayerMoving() and not inVehicle then drainEndurance(player, "crawl", dt) end
        end)
        local now = getTimestampMs and getTimestampMs() or 0
        if not inVehicle and now - LegMobility.lastHint > 20000 then
            LegMobility.lastHint = now
            Messages.Say(player, getText(LegMobility.oneLeg and "IGUI_TOC_NeedCrutch" or "IGUI_TOC_Crawling"), true)
        end
    elseif m == StaticData.MOBILITY.NONE then
        setBlocked(player, not inVehicle)
        setCantSprint(player, true)
        local now = getTimestampMs and getTimestampMs() or 0
        if not inVehicle and now - LegMobility.lastHint > 12000 then
            LegMobility.lastHint = now
            Messages.Say(player, getText("IGUI_TOC_NeedCrutch"), true)
        end
    elseif m == StaticData.MOBILITY.CRUTCH then
        setBlocked(player, false)
        setCantSprint(player, true)
        pcall(function()
            if player:isRunning() then player:setRunning(false) end
            if player:isSprinting() then player:setSprinting(false) end
            if player:isPlayerMoving() and not inVehicle then drainEndurance(player, "crutch", dt) end
        end)
    elseif m == StaticData.MOBILITY.PEG then
        setBlocked(player, false)
        setCantSprint(player, true)
        pcall(function() if player:isSprinting() then player:setSprinting(false) end end)
    else
        setBlocked(player, false)
        setCantSprint(player, false)
    end
end

---@param player IsoPlayer
function LegMobility.Reset(player)
    if not player then return end
    pcall(function()
        if LegMobility.applied.blocked then player:setBlockMovement(false) end
        if LegMobility.applied.cantSprint then player:setMoodleCantSprint(false) end
        if LegMobility.applied.crawl then
            for _, v in ipairs(LegMobility.CRAWL_VARS) do player:setVariable(v, "false") end
        end
        if LegMobility.applied.crutch then
            for _, v in ipairs(LegMobility.CRUTCH_VARS) do player:setVariable(v, "false") end
        end
    end)
    LegMobility.applied = { blocked = false, cantSprint = false, crawl = false, crutch = false, crutchSide = nil }
end

local function OnPlayerUpdate(player)
    if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
    LegMobility.tick = LegMobility.tick + 1
    local gt = getGameTime and getGameTime()
    if gt and gt.getRealworldSecondsSinceLastUpdate then
        local speed = (getGameSpeed and getGameSpeed()) or 1
        LegMobility.dt = LegMobility.dt + math.min(gt:getRealworldSecondsSinceLastUpdate(), 0.25) * math.max(1, speed)
    end
    -- 3.1.2: el juego reescribe la marca "no puede esprintar" en cada actualización (sistema de moodles) y Apply sólo corre
    -- cada 10 fotogramas: con la tecla pulsada se volvía a esprintar entre medias ("con muleta esprinto como si nada").
    -- Se impone en CADA fotograma.
    local m = LegMobility.current
    if m == StaticData.MOBILITY.CRUTCH or m == StaticData.MOBILITY.CRAWL or m == StaticData.MOBILITY.PEG then
        pcall(function()
            player:setMoodleCantSprint(true)
            if player:isSprinting() then player:setSprinting(false) end
            if m ~= StaticData.MOBILITY.PEG and player:isRunning() then player:setRunning(false) end
        end)
    end
    if LegMobility.tick % 10 ~= 0 then return end
    local ok, err = pcall(LegMobility.Apply, player)
    if not ok then TOC_DEBUG.print("LegMobility error: " .. tostring(err)) end
end

Events.OnPlayerUpdate.Add(OnPlayerUpdate)
Events.OnTOCCacheUpdated.Add(function(username)
    local pl = getPlayer()
    if pl and pl:getUsername() == username then pcall(LegMobility.Apply, pl) end
end)

return LegMobility
