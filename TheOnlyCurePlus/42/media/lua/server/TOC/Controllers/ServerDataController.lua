local DataController = require("TOC/Controllers/DataController")
local CommandsData = require("TOC/CommandsData")
local StaticData = require("TOC/StaticData")

---Owns the ModData lifecycle for TOC. The only place that populates tocData.
---@class ServerDataController
local ServerDataController = {}

---@private
local function createDefaultData()
    local tocData = {
        isIgnoredPartInfected = false,
        isAnyLimbCut = false,
        limbs = {},
        prostheses = {},
        plus = DataController.DefaultPlus(),
    }
    for i = 1, #StaticData.LIMBS_STR do
        tocData.limbs[StaticData.LIMBS_STR[i]] = DataController.DefaultLimb()
    end
    for i = 1, #StaticData.AMP_GROUPS_STR do
        tocData.prostheses[StaticData.AMP_GROUPS_STR[i]] = DataController.DefaultProsthesis()
    end
    return tocData
end

---Initialize or reset a DataController for a player. The only authoritative way to create DC instances.
---@param username string
---@param isResetForced boolean?
---@param playerObj IsoPlayer?
---@return DataController
function ServerDataController.Initialize(username, isResetForced, playerObj)
    local key = CommandsData.GetKey(username)

    local dcInst = DataController.instances[username]
    if not dcInst or isResetForced then
        dcInst = DataController:new(username, isResetForced)
    end

    local data
    if not isResetForced then
        data = ModData.get(key)
    end

    if data and data.limbs then
        DataController.Migrate(data)        -- saves from the original TOC: add legs, Bottom groups, plus block
        dcInst.tocData = data
        TOC_DEBUG.print("ServerDataController: loaded existing data for " .. username)
    else
        TOC_DEBUG.print("ServerDataController: creating default data for " .. username)
        ModData.remove(key)
        dcInst.tocData = createDefaultData()
        ModData.add(key, dcInst.tocData)
    end

    dcInst:setIsResetForced(false)
    dcInst:setIsDataReady(true)

    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    CachedDataHandler.CalculateCacheableValues(username)

    if playerObj then
        dcInst:apply(playerObj)
    end
    return dcInst
end

---@param username string
---@param playerObj IsoPlayer?
---@return DataController
function ServerDataController.GetOrCreate(username, playerObj)
    local inst = DataController.GetInstance(username)
    if inst and inst.isDataReady and inst.tocData then
        return inst
    end
    return ServerDataController.Initialize(username, false, playerObj)
end

return ServerDataController
