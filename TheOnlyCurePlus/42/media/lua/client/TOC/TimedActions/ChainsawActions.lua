require "TimedActions/ISBaseTimedAction"
local Messages = require("TOC/Plus/Messages")
-----------------------------

-- TOC+: actions of the chainsaw arm (TOC/Plus/ChainsawArm): pull the starter cord, and refuel the arm's tank from
-- any petrol container in the inventory. Both run on the client like the rest of TOC+'s actions.

local function Arm() return require("TOC/Plus/ChainsawArm") end

---------------- start

---@class TOCChainsawStartAction : ISBaseTimedAction
local StartAction = ISBaseTimedAction:derive("TOCChainsawStartAction")

---@param character IsoPlayer
function StartAction:new(character)
    local o = ISBaseTimedAction.new(self, character)
    o.character = character
    o.stopOnWalk = false
    o.stopOnRun = true
    o.skipTOC = true
    o.maxTime = character:isTimedActionInstant() and 1 or 45
    return o
end

function StartAction:isValid()
    local CA = Arm()
    local arm = CA.GetArm(self.character)
    return arm ~= nil and not CA.IsRunning(self.character) and CA.GetFuel(arm) > 0
end

function StartAction:start()
    self.character:setMetabolicTarget(Metabolics.LightWork)
end

function StartAction:perform()
    local CA = Arm()
    -- a two-stroke on a stump: Mechanics helps, a cold engine may need a few pulls
    local chance = math.min(0.95, 0.55 + 0.07 * self.character:getPerkLevel(Perks.Mechanics))
    if ZombRandFloat(0.0, 1.0) < chance then
        self.character:playSound("TOC_ChainsawStart")
        addSound(self.character, self.character:getX(), self.character:getY(), self.character:getZ(), CA.SWING_NOISE, CA.SWING_NOISE)
        CA.SetRunning(self.character, true, 2200)
        Messages.Say(self.character, getText("IGUI_TOC_SawStarted"), false)
    else
        self.character:playSound("TOC_ChainsawPull")
        Messages.Say(self.character, getText("IGUI_TOC_SawSputters"), true)
    end
    ISBaseTimedAction.perform(self)
end

---------------- refuel

---@class TOCChainsawRefuelAction : ISBaseTimedAction
local RefuelAction = ISBaseTimedAction:derive("TOCChainsawRefuelAction")

---@param character IsoPlayer
---@param petrol InventoryItem container with petrol
function RefuelAction:new(character, petrol)
    local o = ISBaseTimedAction.new(self, character)
    o.character = character
    o.petrol = petrol
    o.stopOnWalk = true
    o.stopOnRun = true
    o.skipTOC = true
    local need = 0.5
    local arm = Arm().GetArm(character)
    if arm then need = math.max(0.05, Arm().TANK - Arm().GetFuel(arm)) end
    o.maxTime = character:isTimedActionInstant() and 1 or math.floor(60 + need * 160)
    return o
end

function RefuelAction:isValid()
    local CA = Arm()
    local arm = CA.GetArm(self.character)
    if not arm or CA.IsRunning(self.character) then return false end
    local fc = self.petrol and self.petrol:getFluidContainer()
    return fc ~= nil and fc:contains(Fluid.Petrol) and fc:getAmount() > 0 and self.character:getInventory():containsRecursive(self.petrol)
end

function RefuelAction:start()
    self:setActionAnim("Loot")
    self.character:SetVariable("LootPosition", "Mid")
    self.petrol:setJobType(getText("IGUI_TOC_SawRefueling"))
    self.petrol:setJobDelta(0.0)
    self.sound = self.character:playSound("GeneratorAddFuel")
end

function RefuelAction:update()
    self.petrol:setJobDelta(self:getJobDelta())
    self.character:setMetabolicTarget(Metabolics.LightDomestic)
end

function RefuelAction:stop()
    if self.sound then self.character:stopOrTriggerSound(self.sound) end
    self.petrol:setJobDelta(0.0)
    ISBaseTimedAction.stop(self)
end

function RefuelAction:perform()
    if self.sound then self.character:stopOrTriggerSound(self.sound) end
    self.petrol:setJobDelta(0.0)
    local CA = Arm()
    local arm = CA.GetArm(self.character)
    local fc = self.petrol:getFluidContainer()
    if arm and fc then
        local fuel = CA.GetFuel(arm)
        local take = math.min(fc:getAmount(), CA.TANK - fuel)
        if take > 0 then
            fc:adjustAmount(fc:getAmount() - take)
            if sendItemStats then pcall(sendItemStats, self.petrol) end
            arm:getModData().TOC_SawFuel = math.min(CA.TANK, fuel + take)
            if isClient() then
                local CommandsData = require("TOC/CommandsData")
                sendClientCommand(CommandsData.modules.TOC_ITEMS, "SetSawFuel", {itemId = arm:getID(), fuel = CA.GetFuel(arm)})
            end
        end
    end
    ISBaseTimedAction.perform(self)
end

return { Start = StartAction, Refuel = RefuelAction }
