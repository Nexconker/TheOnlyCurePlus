-- DataController: pure data model. Server-side lifecycle is handled by ServerDataController.
-- Client-side async load is handled by ClientDataController.
-- TOC+: legs, prosthesis tiers/wear, sepsis and the "plus" block (shock, convalescence, diagnosis...).

local CommandsData = require("TOC/CommandsData")
local StaticData = require("TOC/StaticData")
require("TOC/Events")
----------------

---@class DataController
---@field username string
---@field tocData tocModDataType
---@field isDataReady boolean
---@field isResetForced boolean
local DataController = {}
DataController.instances = {}
DataController._readyCallbacks = {}

---Default data for one limb
---@return partDataType
function DataController.DefaultLimb()
    return { isCut = false, isInfected = false, isOperated = false, isCicatrized = false, isCauterized = false,
             woundDirtyness = -1, cicatrizationTime = 0, isVisible = false, sepsis = 0, cicatrizationMax = 0 }
end

---@return prosthesisData
function DataController.DefaultProsthesis()
    return { isProstEquipped = false, prostFactor = 0, prostType = nil, wear = 0 }
end

---@return plusDataType
function DataController.DefaultPlus()
    return { shockUntil = 0, convalescenceUntil = 0, phantomNext = 0, lastDiagnosis = {}, botched = {}, cureOutcome = nil, carryDelta = nil }
end

---Fill anything missing in a tocData table (saves made with the original TOC lack legs,
---Bottom groups, sepsis and the plus block). Safe to call repeatedly.
---@param tocData table
---@return table tocData
function DataController.Migrate(tocData)
    if type(tocData) ~= "table" then return tocData end
    tocData.limbs = tocData.limbs or {}
    tocData.prostheses = tocData.prostheses or {}
    if tocData.isIgnoredPartInfected == nil then tocData.isIgnoredPartInfected = false end
    if tocData.isAnyLimbCut == nil then tocData.isAnyLimbCut = false end
    for i = 1, #StaticData.LIMBS_STR do
        local limbName = StaticData.LIMBS_STR[i]
        local l = tocData.limbs[limbName]
        if type(l) ~= "table" then
            tocData.limbs[limbName] = DataController.DefaultLimb()
        else
            for k, v in pairs(DataController.DefaultLimb()) do
                if l[k] == nil then l[k] = v end
            end
        end
    end
    for i = 1, #StaticData.AMP_GROUPS_STR do
        local group = StaticData.AMP_GROUPS_STR[i]
        local p = tocData.prostheses[group]
        if type(p) ~= "table" then
            tocData.prostheses[group] = DataController.DefaultProsthesis()
        else
            if p.isProstEquipped == nil then p.isProstEquipped = false end
            if p.prostFactor == nil then p.prostFactor = 0 end
            if p.wear == nil then p.wear = 0 end
        end
    end
    if type(tocData.plus) ~= "table" then
        tocData.plus = DataController.DefaultPlus()
    else
        for k, v in pairs(DataController.DefaultPlus()) do
            if tocData.plus[k] == nil and v ~= nil then tocData.plus[k] = v end
        end
        tocData.plus.lastDiagnosis = tocData.plus.lastDiagnosis or {}
        tocData.plus.botched = tocData.plus.botched or {}
    end
    return tocData
end

---Create a new shell instance of DataController. Does NOT initialize tocData.
---@param username string
---@param isResetForced boolean?
---@return DataController
function DataController:new(username, isResetForced)
    ---@type DataController
    ---@diagnostic disable-next-line: missing-fields
    local o = {}
    setmetatable(o, self)
    self.__index = self

    o.username = username
    o.isDataReady = false
    o.isResetForced = isResetForced or false
    TOC_DEBUG.print("Creating new shell instance of DataController for " .. tostring(o.username))

    DataController.instances[o.username] = o
    return o
end

---Register a callback to run when DC data is ready for a username.
---@param username string
---@param callback fun(dcInst: DataController)
function DataController.WhenReady(username, callback)
    local inst = DataController.instances[username]
    if inst and inst.isDataReady then
        callback(inst)
        return
    end
    if not DataController._readyCallbacks[username] then
        DataController._readyCallbacks[username] = {}
    end
    table.insert(DataController._readyCallbacks[username], callback)
end

---Called by ClientDataController.OnDataReceived when the server data arrives.
---@param tocData tocModDataType
function DataController:save(tocData)
    if not tocData or not tocData.limbs then
        TOC_DEBUG.print("Received invalid tocData")
        return
    end
    DataController.Migrate(tocData)
    local key = CommandsData.GetKey(self.username)
    ModData.add(key, tocData)
    self.tocData = tocData
    self:setIsResetForced(false)
    self:setIsDataReady(true)
end

-----------------
--* Setters *--

---@param isDataReady boolean
function DataController:setIsDataReady(isDataReady)
    self.isDataReady = isDataReady
    if isDataReady then
        triggerEvent("OnTOCDataReady", self.username)
    end
end

---@param username string
function DataController.OnDataReady(username)
    local callbacks = DataController._readyCallbacks[username]
    if not callbacks then return end
    DataController._readyCallbacks[username] = nil
    local inst = DataController.instances[username]
    for _, cb in ipairs(callbacks) do
        local ok, err = pcall(cb, inst)
        if not ok then TOC_DEBUG.print("WhenReady callback error: " .. tostring(err)) end
    end
end

Events.OnTOCDataReady.Add(DataController.OnDataReady)

---@param isResetForced boolean
function DataController:setIsResetForced(isResetForced)
    self.isResetForced = isResetForced
end

---@param isAnyLimbCut boolean
function DataController:setIsAnyLimbCut(isAnyLimbCut)
    self.tocData.isAnyLimbCut = isAnyLimbCut
end

---@param isIgnoredPartInfected boolean
function DataController:setIsIgnoredPartInfected(isIgnoredPartInfected)
    self.tocData.isIgnoredPartInfected = isIgnoredPartInfected
end

---@param limbName string
---@return partDataType
function DataController:limb(limbName)
    local l = self.tocData.limbs[limbName]
    if not l then
        l = DataController.DefaultLimb()
        self.tocData.limbs[limbName] = l
    end
    return l
end

function DataController:setIsCut(limbName, isCut) self:limb(limbName).isCut = isCut end
function DataController:setIsInfected(limbName, isInfected) self:limb(limbName).isInfected = isInfected end
function DataController:setIsCicatrized(limbName, isCicatrized) self:limb(limbName).isCicatrized = isCicatrized end
function DataController:setIsCauterized(limbName, isCauterized) self:limb(limbName).isCauterized = isCauterized end
function DataController:setWoundDirtyness(limbName, woundDirtyness) self:limb(limbName).woundDirtyness = woundDirtyness end
function DataController:setCicatrizationTime(limbName, cicatrizationTime) self:limb(limbName).cicatrizationTime = cicatrizationTime end
function DataController:setSepsis(limbName, sepsis) self:limb(limbName).sepsis = math.max(0, math.min(100, sepsis or 0)) end

---@param group string
---@return prosthesisData
function DataController:prost(group)
    local p = self.tocData.prostheses[group]
    if not p then
        p = DataController.DefaultProsthesis()
        self.tocData.prostheses[group] = p
    end
    return p
end

function DataController:setIsProstEquipped(group, isProstEquipped) self:prost(group).isProstEquipped = isProstEquipped end
function DataController:setProstFactor(group, prostFactor) self:prost(group).prostFactor = prostFactor end
function DataController:setProstType(group, prostType) self:prost(group).prostType = prostType end
function DataController:setProstWear(group, wear) self:prost(group).wear = math.max(0, wear or 0) end

---@return plusDataType
function DataController:plus()
    if not self.tocData.plus then self.tocData.plus = DataController.DefaultPlus() end
    return self.tocData.plus
end

-----------------
--* Getters *--

function DataController:getIsDataReady() return self.isDataReady end

function DataController:getIsAnyLimbCut()
    if not self.isDataReady or not self.tocData then return false end
    return self.tocData.isAnyLimbCut == true
end

function DataController:getIsIgnoredPartInfected()
    if not self.isDataReady or not self.tocData then return false end
    return self.tocData.isIgnoredPartInfected == true
end

function DataController:getIsCut(limbName)
    if not self.isDataReady or not self.tocData or not self.tocData.limbs then return false end
    local l = self.tocData.limbs[limbName]
    return l and l.isCut == true or false
end

function DataController:getIsVisible(limbName)
    if not self.isDataReady or not self.tocData then return false end
    local l = self.tocData.limbs[limbName]
    return l and l.isVisible == true or false
end

function DataController:getIsCicatrized(limbName)
    if not self.isDataReady or not self.tocData then return false end
    local l = self.tocData.limbs[limbName]
    return l and l.isCicatrized == true or false
end

function DataController:getIsCauterized(limbName)
    if not self.isDataReady or not self.tocData then return false end
    local l = self.tocData.limbs[limbName]
    return l and l.isCauterized == true or false
end

function DataController:getIsInfected(limbName)
    if not self.tocData then return false end
    local l = self.tocData.limbs[limbName]
    return l and l.isInfected == true or false
end

function DataController:getWoundDirtyness(limbName)
    if not self.isDataReady then return -1 end
    local l = self.tocData.limbs[limbName]
    return l and l.woundDirtyness or -1
end

function DataController:getCicatrizationTime(limbName)
    if not self.isDataReady then return -1 end
    local l = self.tocData.limbs[limbName]
    return l and l.cicatrizationTime or -1
end

---Maximum cicatrization time assigned at surgery (for the % display). Falls back to the static value.
function DataController:getCicatrizationMax(limbName)
    local l = self.isDataReady and self.tocData.limbs[limbName] or nil
    if l and l.cicatrizationMax and l.cicatrizationMax > 0 then return l.cicatrizationMax end
    return StaticData.LIMBS_CICATRIZATION_TIME_IND_NUM[limbName] or 1
end

function DataController:getSepsis(limbName)
    if not self.isDataReady then return 0 end
    local l = self.tocData.limbs[limbName]
    return l and l.sepsis or 0
end

---@param limbName string
---@return boolean
function DataController:getIsProstEquipped(limbName)
    if not self.isDataReady or not self.tocData then return false end
    local prostGroup = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
    local p = prostGroup and self.tocData.prostheses[prostGroup]
    return p and p.isProstEquipped == true or false
end

---@param group string
---@return boolean
function DataController:getIsProstEquippedGroup(group)
    if not self.isDataReady or not self.tocData then return false end
    local p = self.tocData.prostheses[group]
    return p and p.isProstEquipped == true or false
end

function DataController:getProstFactor(group)
    local p = self.tocData and self.tocData.prostheses[group]
    return p and p.prostFactor or 0
end

---@param group string
---@return string? fullType of the equipped prosthesis
function DataController:getProstType(group)
    if not self.isDataReady or not self.tocData then return nil end
    local p = self.tocData.prostheses[group]
    if p and p.isProstEquipped then return p.prostType end
    return nil
end

function DataController:getProstWear(group)
    local p = self.tocData and self.tocData.prostheses[group]
    return p and p.wear or 0
end

--* Limbs data handling *--

---Set a limb and its dependend limbs as cut
---@param limbName string
---@param isOperated boolean
---@param isCicatrized boolean
---@param isCauterized boolean
---@param surgeonFactor number?
---@param cicMult number? multiplier on the cicatrization time (surgery outcome)
---@param dirt0 number? initial wound dirtyness
function DataController:setCutLimb(limbName, isOperated, isCicatrized, isCauterized, surgeonFactor, cicMult, dirt0)
    local cicatrizationTime = 0
    if isCicatrized == false or isCauterized == false then
        cicatrizationTime = math.max(12, (StaticData.LIMBS_CICATRIZATION_TIME_IND_NUM[limbName] - (surgeonFactor or 0)) * (cicMult or 1))
    end

    ---@type partDataType
    local params = {isCut = true, isInfected = false, isOperated = isOperated, isCicatrized = isCicatrized, isCauterized = isCauterized,
                    woundDirtyness = dirt0 or 0, isVisible = true, sepsis = 0, cicatrizationMax = cicatrizationTime}
    self:setLimbParams(limbName, params, cicatrizationTime)

    for i = 1, #StaticData.LIMBS_DEPENDENCIES_IND_STR[limbName] do
        local dependedLimbName = StaticData.LIMBS_DEPENDENCIES_IND_STR[limbName][i]
        self:setLimbParams(dependedLimbName, {isCut = true, isInfected = false, isVisible = false, isCicatrized = true, sepsis = 0}, 0)
    end

    self:setIsAnyLimbCut(true)
end

---@param limbName string
---@param ampStatus partDataType
---@param cicatrizationTime integer?
function DataController:setLimbParams(limbName, ampStatus, cicatrizationTime)
    local limbData = self:limb(limbName)
    for k, v in pairs(ampStatus) do
        if v ~= nil then limbData[k] = v end
    end
    if cicatrizationTime ~= nil then limbData.cicatrizationTime = cicatrizationTime end
end

---@param limbName string
function DataController:decreaseCicatrizationTime(limbName)
    local l = self:limb(limbName)
    l.cicatrizationTime = l.cicatrizationTime - 1
end

--* Specific updates from Client

---Sends only the necessary data to update one limb to the server, while being already ok on the client
---@param limbName string
function DataController:updateAmputationsFromClient(limbName)
    if not self:getIsDataReady() then return end
    if not isClient() then return end       -- SP: same Lua state, nothing to relay
    sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.UpdateDataControllerFromClient, {
        limbName = limbName,
        cicTime = self:getCicatrizationTime(limbName),
        dirtyness = self:getWoundDirtyness(limbName),
        isInfected = self:getIsInfected(limbName),
        isCauterized = self:getIsCauterized(limbName),
        isCicatrized = self:getIsCicatrized(limbName),
        sepsis = self:getSepsis(limbName),
    })
end

function DataController:updateIsIgnoredPartInfectedFromClient()
    if not isClient() then return end
    sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.UpdateDataControllerFromClient, {
        isIgnoredPartInfected = self:getIsIgnoredPartInfected()})
end

---Push the whole plus block to the server (client only; cheap, it is a tiny table)
function DataController:updatePlusFromClient()
    if not isClient() or not self:getIsDataReady() then return end
    sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayPlusData, {plus = self:plus()})
end

--* Global Mod Data Handling *--

---SERVER: push current state to a specific client (MP) or fire OnInitTocData (SP/server)
---@param player IsoPlayer
function DataController:apply(player)
    if isClient() then return end

    if isServer() then
        sendServerCommand(player, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceiveApplyFromServer,
            {patientUsername = self.username})
    end

    triggerEvent("OnInitTocData", player, self.username, true)
end

-----------------

---@param username string
---@return DataController?
function DataController.GetInstance(username)
    return DataController.instances[username]
end

---Shortcut: ready instance or nil
---@param username string
---@return DataController?
function DataController.GetReady(username)
    local inst = DataController.instances[username]
    if inst and inst.isDataReady and inst.tocData then return inst end
    return nil
end

function DataController.DestroyInstance(username)
    DataController.instances[username] = nil
    DataController._readyCallbacks[username] = nil
end

return DataController
