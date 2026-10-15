-- TOC+ Symptoms: the infection speaks before the health panel does. Also the hourly cost of
-- convalescence. Local player only.
local DataController = require("TOC/Controllers/DataController")
local PostOp = require("TOC/Plus/PostOp")
local Messages = require("TOC/Plus/Messages")
-----------------

local Symptoms = {}

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

function Symptoms.Hourly()
    local pl = getPlayer()
    if not pl or pl:isDead() then return end
    local stats = pl:getStats()

    --* Knox infection symptoms
    if sv("ShowSymptoms", true) then
        local bd = pl:getBodyDamage()
        local infected = false
        pcall(function() infected = bd:isInfected() end)
        if infected then
            local level = stats:get(CharacterStat.ZOMBIE_INFECTION) or 0
            local window = sv("CureWindow", 20)
            local chance, key
            if level < window * 0.5 then
                chance, key = 0.15, "IGUI_TOC_Symptom_1"
            elseif level < window then
                chance, key = 0.35, "IGUI_TOC_Symptom_2"
            elseif level < window * 2 then
                chance, key = 0.5, "IGUI_TOC_Symptom_3"
            else
                chance, key = 0.6, "IGUI_TOC_Symptom_4"
            end
            if ZombRandFloat(0.0, 1.0) < chance then
                Messages.Say(pl, getText(key), true)
            end
        end
    end

    --* Convalescence: tired, hungry, thirsty
    local dc = DataController.GetReady(pl:getUsername())
    if dc and PostOp.IsConvalescent(dc) then
        pcall(function()
            stats:set(CharacterStat.FATIGUE, math.min(1, (stats:get(CharacterStat.FATIGUE) or 0) + 0.012))
            stats:set(CharacterStat.HUNGER, math.min(1, (stats:get(CharacterStat.HUNGER) or 0) + 0.01))
            stats:set(CharacterStat.THIRST, math.min(1, (stats:get(CharacterStat.THIRST) or 0) + 0.01))
        end)
        if ZombRand(6) == 0 then Messages.Say(pl, getText("IGUI_TOC_Convalescent"), false) end
    end
    if dc and PostOp.IsInShock(dc) then
        pcall(function()
            stats:set(CharacterStat.ENDURANCE, math.min(stats:get(CharacterStat.ENDURANCE) or 1, 0.6))
        end)
    end
end

Events.EveryHours.Add(function() pcall(Symptoms.Hourly) end)

return Symptoms
