require "TimedActions/ISBaseTimedAction"
local DataController = require("TOC/Controllers/DataController")
local CommandsData = require("TOC/CommandsData")
local PostOp = require("TOC/Plus/PostOp")
---------------

-- TOC+: cauterize at any lit heat source (stove, fireplace, barbecue, campfire, fire) or with a
-- blade heated in one of them.
---@class CauterizeAction : ISBaseTimedAction
---@field character IsoPlayer
---@field heatObj IsoObject?
---@field limbName string
local CauterizeAction = ISBaseTimedAction:derive("CauterizeAction")

---@param character IsoPlayer
---@param limbName string
---@param heatObj IsoObject?
---@return CauterizeAction
function CauterizeAction:new(character, limbName, heatObj)
    local o = ISBaseTimedAction.new(self, character)
    o.character = character
    o.heatObj = heatObj
    o.limbName = limbName
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = o:getDuration()
    if o.character:isTimedActionInstant() then o.maxTime = 1 end
    return o
end

function CauterizeAction:getDuration()
    local baseTime = 500
    local strengthLevel = self.character:getPerkLevel(Perks.Strength)
    return math.max(150, baseTime - strengthLevel * 50)
end

function CauterizeAction:isValid()
    return true
end

function CauterizeAction:waitToStart()
    if self.heatObj then
        self.character:faceThisObject(self.heatObj)
        return self.character:shouldBeTurning()
    end
    return false
end

function CauterizeAction:start()
    self:setActionAnim("Loot")
    self.character:SetVariable("LootPosition", "Mid")
    self.sound = self.character:getEmitter():playSound("Cauterization")
    addSound(self.character, self.character:getX(), self.character:getY(), self.character:getZ(), 5, 5)
    local snd = self.character:isFemale() and "TOC_ScreamFemale" or "TOC_ScreamMale"
    if not pcall(function() self.character:playerVoiceSound("PainFromBite") end) then pcall(function() self.character:getEmitter():playSound(snd) end) end
    local radius = math.floor(((SandboxVars.TOC and SandboxVars.TOC.ScreamRadius) or 25) * 0.6)
    addSound(self.character, self.character:getX(), self.character:getY(), self.character:getZ(), radius, radius)
end

function CauterizeAction:update()
    self.character:setMetabolicTarget(Metabolics.HeavyWork)
end

function CauterizeAction:stopSound()
    if self.sound then
        self.character:getEmitter():stopSound(self.sound)
        self.sound = nil
    end
end

function CauterizeAction:stop()
    self:stopSound()
    ISBaseTimedAction.stop(self)
end

function CauterizeAction:perform()
    self:stopSound()
    local dcInst = DataController.GetReady(self.character:getUsername())
    if dcInst then
        dcInst:setCicatrizationTime(self.limbName, 0)
        dcInst:setIsCauterized(self.limbName, true)
        dcInst:setSepsis(self.limbName, dcInst:getSepsis(self.limbName) * 0.3)
        local LocalPlayerController = require("TOC/Controllers/LocalPlayerController")
        LocalPlayerController.HandleSetCicatrization(dcInst, self.character, self.limbName)
        dcInst:updateAmputationsFromClient(self.limbName)
    end
    -- burn pain and panic
    local fx = { pain = 35, panic = 80, endurance = -0.2 }
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayPostOpApply, {limbName = self.limbName, fx = fx})
    else
        PostOp.ApplyEffects(self.character, self.limbName, fx)
    end
    ISBaseTimedAction.perform(self)
end

return CauterizeAction
