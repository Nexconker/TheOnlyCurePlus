-- TOC+ LegMobility: what a leg amputee can do. Runs for the local player only.
--  NONE   -> a leg is missing and there is no crutch / prosthesis: cannot move
--  CRAWL  -> both legs missing and no prosthesis: crawls on the ground (animation variable TOC_Crawl
--            selects the zombie crawler clips added in media/AnimSets/player/*/TOC_Crawl*.xml)
--  CRUTCH -> crutch in a hand: walk only, no running, stamina drains while moving
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

local CRUTCH_TYPE = "TOC.Crutch"

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
        return LegMobility.HasCrutch(player) and StaticData.MOBILITY.CRUTCH or StaticData.MOBILITY.NONE
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
            if player:isPlayerMoving() and not inVehicle then
                local stats = player:getStats()
                stats:set(CharacterStat.ENDURANCE, math.max(0, (stats:get(CharacterStat.ENDURANCE) or 1) - 0.004))
            end
        end)
        local now = getTimestampMs and getTimestampMs() or 0
        if not inVehicle and now - LegMobility.lastHint > 20000 then
            LegMobility.lastHint = now
            Messages.Say(player, getText("IGUI_TOC_Crawling"), true)
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
            if player:isPlayerMoving() and not inVehicle then
                local stats = player:getStats()
                stats:set(CharacterStat.ENDURANCE, math.max(0, (stats:get(CharacterStat.ENDURANCE) or 1) - 0.0025))
            end
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
    if not player or not player:isLocalPlayer() then return end
    LegMobility.tick = LegMobility.tick + 1
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
