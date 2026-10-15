-- Cache of derived values per username (amputated limbs, highest amputation per group, hand/leg feasibility).
-- Calculated on the authoritative side and sent to clients.
local DataController = require("TOC/Controllers/DataController")
local StaticData = require("TOC/StaticData")
---------------------------

---@class CachedDataHandler
local CachedDataHandler = {}

CachedDataHandler.amputatedLimbs = {}
CachedDataHandler.highestAmputatedLimbs = {}     -- username -> { Top_L = limbName, Bottom_R = limbName ... }
CachedDataHandler.handFeasibility = {}           -- username -> { L = bool, R = bool }
CachedDataHandler.legFeasibility = {}            -- username -> { L = bool, R = bool }

---@param username string
function CachedDataHandler.Setup(username)
    CachedDataHandler.amputatedLimbs[username] = {}
    CachedDataHandler.highestAmputatedLimbs[username] = {}
    CachedDataHandler.handFeasibility[username] = {}
    CachedDataHandler.legFeasibility[username] = {}
end

---CLIENT ONLY
---@param patientUsername string
---@param cache table
function CachedDataHandler.ApplyFromServer(patientUsername, cache)
    cache = cache or {}
    CachedDataHandler.amputatedLimbs[patientUsername] = cache.amputatedLimbs or {}
    CachedDataHandler.highestAmputatedLimbs[patientUsername] = cache.highestAmputatedLimbs or {}
    CachedDataHandler.handFeasibility[patientUsername] = cache.handFeasibility or { L = true, R = true }
    CachedDataHandler.legFeasibility[patientUsername] = cache.legFeasibility or { L = true, R = true }
    triggerEvent("OnTOCCacheUpdated", patientUsername)
end

--CLIENT ONLY
function CachedDataHandler.RequestFromServer(patientUsername, recalculate)
    local CommandsData = require("TOC/CommandsData")
    sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.SendCache,
        {patientUsername = patientUsername, recalculate = recalculate})
end

---Authoritative side: calculate everything
---@param username string
function CachedDataHandler.CalculateCacheableValues(username)
    CachedDataHandler.CalculateHighestAmputatedLimbs(username)
    for _, side in ipairs(StaticData.SIDES_STR) do
        CachedDataHandler.CalculateFeasibility(username, side)
    end
end

---SHARED
function CachedDataHandler.GetAll(username)
    return {
        amputatedLimbs = CachedDataHandler.GetAmputatedLimbs(username),
        highestAmputatedLimbs = CachedDataHandler.GetHighestAmputatedLimbs(username),
        handFeasibility = {
            L = CachedDataHandler.GetHandFeasibility("L", username),
            R = CachedDataHandler.GetHandFeasibility("R", username)
        },
        legFeasibility = {
            L = CachedDataHandler.GetLegFeasibility("L", username),
            R = CachedDataHandler.GetLegFeasibility("R", username)
        }
    }
end

--* Amputated Limbs caching *--

---@param username string
function CachedDataHandler.CalculateAmputatedLimbs(username)
    CachedDataHandler.amputatedLimbs[username] = {}
    local dcInst = DataController.GetInstance(username)
    if not dcInst then return end
    for i = 1, #StaticData.LIMBS_STR do
        local limbName = StaticData.LIMBS_STR[i]
        if dcInst:getIsCut(limbName) then
            CachedDataHandler.AddAmputatedLimb(username, limbName)
        end
    end
end

---@param username string
---@param limbName string
function CachedDataHandler.AddAmputatedLimb(username, limbName)
    CachedDataHandler.amputatedLimbs[username] = CachedDataHandler.amputatedLimbs[username] or {}
    CachedDataHandler.amputatedLimbs[username][limbName] = limbName
end

---@param username string
---@return table
function CachedDataHandler.GetAmputatedLimbs(username)
    return CachedDataHandler.amputatedLimbs[username] or {}
end

--* Highest amputated limb per group *--

---@param username string
function CachedDataHandler.CalculateHighestAmputatedLimbs(username)
    local dcInst = DataController.GetInstance(username)
    if dcInst == nil then return end
    CachedDataHandler.CalculateAmputatedLimbs(username)
    CachedDataHandler.highestAmputatedLimbs[username] = {}
    for limbName, _ in pairs(CachedDataHandler.amputatedLimbs[username] or {}) do
        if dcInst:getIsCut(limbName) and dcInst:getIsVisible(limbName) then
            local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
            CachedDataHandler.highestAmputatedLimbs[username][group] = limbName
        end
    end
end

---Returns { Top_L = limb, Top_R = limb, Bottom_L = limb, Bottom_R = limb } (missing keys = not cut).
---@param username string
---@return table?
function CachedDataHandler.GetHighestAmputatedLimbs(username)
    return CachedDataHandler.highestAmputatedLimbs[username]
end

---Highest ARM amputation of a side (old TOC API)
---@param username string
---@param side string
---@return string?
function CachedDataHandler.GetHighestArm(username, side)
    local t = CachedDataHandler.highestAmputatedLimbs[username]
    return t and t["Top_" .. side] or nil
end

---Highest LEG amputation of a side
---@param username string
---@param side string
---@return string?
function CachedDataHandler.GetHighestLeg(username, side)
    local t = CachedDataHandler.highestAmputatedLimbs[username]
    return t and t["Bottom_" .. side] or nil
end

--* Feasibility *--

---Authoritative side
---@param username string
---@param side string
function CachedDataHandler.CalculateFeasibility(username, side)
    local dcInst = DataController.GetInstance(username)
    if dcInst == nil then return end
    CachedDataHandler.handFeasibility[username] = CachedDataHandler.handFeasibility[username] or {}
    CachedDataHandler.legFeasibility[username] = CachedDataHandler.legFeasibility[username] or {}
    local hand = "Hand_" .. side
    CachedDataHandler.handFeasibility[username][side] = (not dcInst:getIsCut(hand)) or dcInst:getIsProstEquippedGroup("Top_" .. side)
    local foot = "Foot_" .. side
    CachedDataHandler.legFeasibility[username][side] = (not dcInst:getIsCut(foot)) or dcInst:getIsProstEquippedGroup("Bottom_" .. side)
end

---SHARED
---@param side string "L" or "R"
---@param username string
---@return boolean
function CachedDataHandler.GetHandFeasibility(side, username)
    local t = CachedDataHandler.handFeasibility[username]
    if t == nil or t[side] == nil then return true end     -- unknown = assume intact (never lock a player out by accident)
    return t[side]
end

---@param side string
---@param username string
---@return boolean
function CachedDataHandler.GetLegFeasibility(side, username)
    local t = CachedDataHandler.legFeasibility[username]
    if t == nil or t[side] == nil then return true end
    return t[side]
end

---At least one usable hand
---@param username string
---@return boolean
function CachedDataHandler.GetBothHandsFeasibility(username)
    return CachedDataHandler.GetHandFeasibility("L", username) or CachedDataHandler.GetHandFeasibility("R", username)
end

---Both hands usable
---@param username string
---@return boolean
function CachedDataHandler.GetHandFeasibilityBoth(username)
    return CachedDataHandler.GetHandFeasibility("L", username) and CachedDataHandler.GetHandFeasibility("R", username)
end

---CLIENT ONLY: with no hands at all the interact key is disabled
function CachedDataHandler.OverrideInteractionsKey()
    local pl = getPlayer()
    if pl == nil then return end
    local username = pl:getUsername()
    if CachedDataHandler.handFeasibility[username] == nil then return end
    local interactStr = "Interact"
    if CachedDataHandler.interactKey == nil or CachedDataHandler.interactKey == 0 then
        CachedDataHandler.interactKey = getCore():getKey(interactStr)
    end
    if not CachedDataHandler.GetBothHandsFeasibility(username) then
        getCore():addKeyBinding(interactStr, Keyboard.KEY_NONE, 0, false, false, false)
    else
        getCore():addKeyBinding(interactStr, CachedDataHandler.interactKey, 0, false, false, false)
    end
end

------------------

---Authoritative side: send the cache to a player
---@param player IsoPlayer
---@param patientUsername string
---@param recalculate boolean
function CachedDataHandler.SendCache(player, patientUsername, recalculate)
    if recalculate then
        CachedDataHandler.CalculateCacheableValues(patientUsername)
    end
    local cache = CachedDataHandler.GetAll(patientUsername)
    if isServer() then
        local CommandsData = require("TOC/CommandsData")
        sendServerCommand(player, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveCache, {
            patientUsername = patientUsername, cache = cache})
    elseif not isClient() then
        CachedDataHandler.ApplyFromServer(patientUsername, cache)
        CachedDataHandler.OverrideInteractionsKey()
    end
end

LuaEventManager.AddEvent("OnTOCCacheUpdated")   -- args: username

if isServer() then
    Events.OnServerStarted.Add(function()
        Events.OnInitTocData.Add(CachedDataHandler.SendCache)
    end)
elseif not isClient() then
    Events.OnGameStart.Add(function()
        Events.OnInitTocData.Add(CachedDataHandler.SendCache)
    end)
end

return CachedDataHandler
