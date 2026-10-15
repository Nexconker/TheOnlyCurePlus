-- TOC+ PostOp: shock, convalescence, sepsis, phantom pain. Pure rules + the one function that
-- applies body effects (ApplyEffects) which must run on the authoritative side (server or SP).
local StaticData = require("TOC/StaticData")
-----------------

local PostOp = {}

local function clamp(v, a, b) if v < a then return a elseif v > b then return b else return v end end

---Game time in hours (float)
---@return number
function PostOp.Now()
    local gt = getGameTime()
    if gt and gt.getWorldAgeHours then return gt:getWorldAgeHours() end
    return 0
end

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

---Mark the beginning of the post-op period. Call on the authoritative side right after the amputation.
---@param dcInst DataController
---@param severity number 0 clean, 1 rough, 2 botched
function PostOp.StartAfterSurgery(dcInst, severity)
    local plus = dcInst:plus()
    local now = PostOp.Now()
    local shockHours = 24 * (1 + severity * 0.5)
    plus.shockUntil = math.max(plus.shockUntil or 0, now + shockHours)
    local days = sv("ConvalescenceDays", 5)
    plus.convalescenceUntil = math.max(plus.convalescenceUntil or 0, now + days * 24 * (1 + severity * 0.4))
    plus.phantomNext = now + ZombRand(6, 30)
end

function PostOp.IsInShock(dcInst)
    local plus = dcInst and dcInst.tocData and dcInst.tocData.plus
    return plus and (plus.shockUntil or 0) > PostOp.Now() or false
end

function PostOp.IsConvalescent(dcInst)
    local plus = dcInst and dcInst.tocData and dcInst.tocData.plus
    return plus and (plus.convalescenceUntil or 0) > PostOp.Now() or false
end

---Hours left of convalescence (0 if none)
function PostOp.ConvalescenceLeft(dcInst)
    local plus = dcInst and dcInst.tocData and dcInst.tocData.plus
    if not plus then return 0 end
    return math.max(0, (plus.convalescenceUntil or 0) - PostOp.Now())
end

---Hourly sepsis rule for one limb. Pure: returns the new sepsis value and the effects to apply.
---@param dcInst DataController
---@param player IsoPlayer
---@param limbName string
---@param dirtyness number current wound dirtyness 0..1
---@return number newSepsis, table effects
function PostOp.HourlySepsis(dcInst, player, limbName, dirtyness)
    local sepsis = dcInst:getSepsis(limbName)
    local fx = {}
    if not sv("SepsisEnabled", true) then return 0, fx end
    local speed = sv("SepsisSpeed", 2)
    local antibiotics = 0
    -- sin pcall: un pcall fallido también escribe la traza en la consola. Se comprueba que el método exista.
    local bd = player and player.getBodyDamage and player:getBodyDamage() or nil
    if bd and bd.getReduceInfectionPower then
        local power = bd:getReduceInfectionPower()
        if power and power > 0 then antibiotics = 4 end
    end
    if dirtyness > 0.45 then
        sepsis = sepsis + (dirtyness - 0.35) * 10 * speed
    else
        sepsis = sepsis - 1.5
    end
    sepsis = sepsis - antibiotics
    sepsis = clamp(sepsis, 0, 100)
    if sepsis > 10 then
        fx.woundInfection = sepsis           -- vanilla wound infection on the adjacent part
    else
        fx.woundInfection = 0
    end
    if sepsis > 40 then fx.sickness = clamp((sepsis - 30) / 100, 0, 0.7) end
    if sepsis > 25 then fx.pain = 10 + sepsis * 0.3 end
    if sepsis >= 100 then fx.healthDelta = -8 end          -- dying of sepsis, needs antibiotics NOW
    fx.sepsis = sepsis
    return sepsis, fx
end

---Phantom pain roll. Returns effects or nil.
---@param dcInst DataController
---@param limbName string
function PostOp.PhantomPain(dcInst, limbName)
    local plus = dcInst:plus()
    local now = PostOp.Now()
    if (plus.phantomNext or 0) > now then return nil end
    plus.phantomNext = now + ZombRand(8, 48)
    if not sv("PhantomPain", true) then return nil end
    return { pain = ZombRand(10, 30), phantom = true }
end

---Apply effects to the player's body. AUTHORITATIVE SIDE ONLY (server in MP, anywhere in SP).
---Client Lua cannot push BodyDamage in MP, so clients send RelayPostOpApply instead.
---@param player IsoPlayer
---@param limbName string?
---@param fx table
function PostOp.ApplyEffects(player, limbName, fx)
    if not player or not fx then return end
    if isClient() then return end
    local bd = player:getBodyDamage()
    if not bd then return end
    local part = nil
    if limbName and StaticData.LIMBS_ADJACENT_IND_STR[limbName] then
        local adj = BodyPartType[StaticData.LIMBS_ADJACENT_IND_STR[limbName]]
        part = adj and bd:getBodyPart(adj) or nil
    end
    local touched = false
    if part then
        if fx.woundInfection ~= nil then
            local lvl = clamp(fx.woundInfection, 0, 100)
            pcall(function()
                part:setInfectedWound(lvl > 0)
                part:setWoundInfectionLevel(lvl)
            end)
            touched = true
        end
        if fx.pain then
            pcall(function() part:setAdditionalPain(math.min(100, part:getAdditionalPain() + fx.pain)) end)
            touched = true
        end
        if fx.alcohol then
            pcall(function() part:setAlcoholLevel(part:getAlcoholLevel() + fx.alcohol) end)
            touched = true
        end
        if fx.bleedingTime then
            pcall(function() part:setBleeding(true); part:setBleedingTime(fx.bleedingTime) end)
            touched = true
        end
        if fx.deepWound then
            pcall(function() part:setDeepWounded(true); part:setDeepWoundTime(fx.deepWound) end)
            touched = true
        end
        if fx.damage then
            pcall(function() part:AddDamage(fx.damage) end)
            touched = true
        end
    end
    if fx.sickness then
        local stats = player:getStats()
        local cur = stats:get(CharacterStat.SICKNESS) or 0
        if fx.sickness > cur then stats:set(CharacterStat.SICKNESS, fx.sickness) end
    end
    if fx.healthDelta and fx.healthDelta < 0 then
        pcall(function() bd:ReduceGeneralHealth(-fx.healthDelta) end)
    end
    if fx.panic then
        local stats = player:getStats()
        stats:set(CharacterStat.PANIC, math.max(stats:get(CharacterStat.PANIC) or 0, fx.panic))
    end
    if fx.endurance then
        local stats = player:getStats()
        stats:set(CharacterStat.ENDURANCE, clamp((stats:get(CharacterStat.ENDURANCE) or 1) + fx.endurance, 0, 1))
    end
    if touched and part and isServer() then
        pcall(function() syncBodyPart(part, 0xFFFFFFFFFFF) end)
    end
    if isServer() then pcall(function() sendPlayerEffects(player) end) end
end

---Validate a client-sent effects table before applying it server-side. Returns a clean copy.
---@param fx table
---@return table
function PostOp.SanitizeEffects(fx)
    if type(fx) ~= "table" then return {} end
    local c = {}
    local function num(k, lo, hi)
        local v = tonumber(fx[k])
        if v then c[k] = clamp(v, lo, hi) end
    end
    num("woundInfection", 0, 100); num("pain", 0, 40); num("sickness", 0, 0.8); num("healthDelta", -10, 0)
    num("alcohol", 0, 5); num("bleedingTime", 0, 60); num("deepWound", 0, 60); num("damage", 0, 40); num("panic", 0, 100); num("endurance", -0.5, 0)
    num("sepsis", 0, 100)
    return c
end

return PostOp
