local DataController = require("TOC/Controllers/DataController")
local CommonMethods = require("TOC/CommonMethods")
local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
local CommandsData = require("TOC/CommandsData")
local StaticData = require("TOC/StaticData")
local PostOp = require("TOC/Plus/PostOp")
local Messages = require("TOC/Plus/Messages")
require("TOC/Events")
local TOC_REG = require("TOC/Registries")
-----------

-- Handles ONLY the local client's player

---@class LocalPlayerController
local LocalPlayerController = {}

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

--* Initialization

---@param isForced boolean?
function LocalPlayerController.InitializePlayer(isForced)
    local playerObj = getPlayer()
    if not playerObj then return end
    local username = playerObj:getUsername()
    TOC_DEBUG.print("Initializing local player: " .. username)

    LocalPlayerController.playerObj = playerObj
    LocalPlayerController.username = username

    local ClientDataController = require("TOC/Controllers/ClientDataController")
    ClientDataController.Request(username, isForced, playerObj)

    DataController.WhenReady(username, function(_dcInst)
        -- SP never receives OnReceiveGlobalModData, so the health panel override was never armed (issue #278)
        if SetHealthPanelTOC then SetHealthPanelTOC() end
        LocalPlayerController.ToggleUpdateAmputations()
        LocalPlayerController.ManageTraits()
        LocalPlayerController.ApplyCarryPenalty()
        LocalPlayerController.EnsureStumpItems()
    end)

    if isForced then
        sendClientCommand(CommandsData.modules.TOC_ITEMS, "DeleteAllOldAmputationItems", {patientNum = playerObj:getOnlineID()})
    end
end

---Starting traits
function LocalPlayerController.ManageTraits()
    local playerObj = getPlayer()
    local dcInst = DataController.GetReady(playerObj:getUsername())
    if not dcInst then return end
    for k, v in pairs(StaticData.TRAITS_BP) do
        local trait = TOC_REG.traits[k]
        if trait and playerObj:hasTrait(trait) and not dcInst:getIsCut(v) then
            TOC_DEBUG.print("Player has amputation trait " .. k .. ", applying it for limb " .. v)
            if isClient() then
                sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayApplyTraitAmputation, {limbName = v})
            else
                local ServerRelayCommands = require("TOC/ServerRelayCommands")
                ServerRelayCommands.RelayApplyTraitAmputation(playerObj, {limbName = v})
            end
        end
    end
end

----------------------------------------------------------
--* Health *--

---Clear every injury on a body part that no longer exists (same list as the server sanitizer: TOC/Plus/CutLimbHeal)
---@param bodyPart BodyPart
function LocalPlayerController.HealArea(bodyPart)
    require("TOC/Plus/CutLimbHeal").Clear(bodyPart)
end

---@param bodyDamage BodyDamage
---@param limbName string
---@param dcInst DataController
function LocalPlayerController.HealZombieInfection(bodyDamage, limbName, dcInst)
    if bodyDamage:isInfected() == false then return end
    bodyDamage:setInfected(false)
    bodyDamage:setInfectionMortalityDuration(-1)
    bodyDamage:setInfectionTime(-1)
    dcInst:setIsInfected(limbName, false)
end

-------------------------
--* Damage handling  *--
LocalPlayerController.hasBeenDamaged = false

---@param character IsoPlayer|IsoGameCharacter
function LocalPlayerController.HandleDamage(character)
    if character ~= getPlayer() then
        LocalPlayerController.hasBeenDamaged = false
        return
    end
    local dcInst = DataController.GetReady(character:getUsername())
    if not dcInst then
        LocalPlayerController.hasBeenDamaged = false
        return
    end

    local bd = character:getBodyDamage()
    for i = 1, #StaticData.LIMBS_STR do
        local modDataNeedsUpdate = false
        local limbName = StaticData.LIMBS_STR[i]
        local bptEnum = StaticData.LIMBS_TO_BODYLOCS_IND_BPT[limbName]
        local bodyPart = bd:getBodyPart(bptEnum)
        if dcInst:getIsCut(limbName) then
            if bodyPart:HasInjury() then
                LocalPlayerController.HealArea(bodyPart)
            end
            if bodyPart:bitten() or bodyPart:IsInfected() then
                LocalPlayerController.HealZombieInfection(bd, limbName, dcInst)
                modDataNeedsUpdate = true
            elseif dcInst:getIsInfected(limbName) then
                dcInst:setIsInfected(limbName, false)
                modDataNeedsUpdate = true
            end
        else
            if (bodyPart:bitten() or bodyPart:IsInfected()) and not dcInst:getIsInfected(limbName) then
                dcInst:setIsInfected(limbName, true)
                modDataNeedsUpdate = true
            end
        end
        if modDataNeedsUpdate then
            dcInst:updateAmputationsFromClient(limbName)
        end
    end

    -- Bites on parts that cannot be cut: nothing will save this one
    if not dcInst:getIsIgnoredPartInfected() then
        for i = 1, #StaticData.IGNORED_BODYLOCS_BPT do
            local bodyPart = bd:getBodyPart(StaticData.IGNORED_BODYLOCS_BPT[i])
            if bodyPart and (bodyPart:bitten() or bodyPart:IsInfected()) then
                dcInst:setIsIgnoredPartInfected(true)
                dcInst:updateIsIgnoredPartInfectedFromClient()
            end
        end
    end
    LocalPlayerController.hasBeenDamaged = false
end

---@param character IsoPlayer|IsoGameCharacter
function LocalPlayerController.OnGetDamage(character, damageType, damageAmount)
    if LocalPlayerController.hasBeenDamaged == false then
        LocalPlayerController.hasBeenDamaged = true
        local ok, err = pcall(LocalPlayerController.HandleDamage, character)
        if not ok then
            LocalPlayerController.hasBeenDamaged = false
            TOC_DEBUG.print("HandleDamage error: " .. tostring(err))
        end
    end
end

Events.OnPlayerGetDamage.Add(LocalPlayerController.OnGetDamage)

--* Bite-on-cut-limb polling (issue #279): MP zombie hits never fire OnPlayerGetDamage on the victim *--
LocalPlayerController.sanitizePollInterval = 60
LocalPlayerController.sanitizeRequestCooldown = 600
LocalPlayerController.sanitizePollTick = 0
LocalPlayerController.sanitizeLastRequestTick = {}

---@param character IsoPlayer|IsoGameCharacter
function LocalPlayerController.PollCutLimbsForBites(character)
    if character ~= getPlayer() then return end
    LocalPlayerController.sanitizePollTick = LocalPlayerController.sanitizePollTick + 1
    if LocalPlayerController.sanitizePollTick % LocalPlayerController.sanitizePollInterval ~= 0 then return end

    local playerObj = getPlayer()
    local dcInst = DataController.GetReady(playerObj:getUsername())
    if not dcInst or not dcInst:getIsAnyLimbCut() then return end
    local bd = playerObj:getBodyDamage()
    if not bd then return end

    for i = 1, #StaticData.LIMBS_STR do
        local limbName = StaticData.LIMBS_STR[i]
        if dcInst:getIsCut(limbName) then
            local bptEnum = StaticData.LIMBS_TO_BODYLOCS_IND_BPT[limbName]
            local bodyPart = bptEnum and bd:getBodyPart(bptEnum) or nil
            if bodyPart and require("TOC/Plus/CutLimbHeal").HasAnything(bodyPart) then
                LocalPlayerController.HealArea(bodyPart)
                if isClient() then
                    local lastReq = LocalPlayerController.sanitizeLastRequestTick[limbName] or -LocalPlayerController.sanitizeRequestCooldown
                    if LocalPlayerController.sanitizePollTick - lastReq >= LocalPlayerController.sanitizeRequestCooldown then
                        LocalPlayerController.sanitizeLastRequestTick[limbName] = LocalPlayerController.sanitizePollTick
                        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RequestSanitizeCutLimb, {limbName = limbName})
                    end
                end
            end
        end
    end
end

Events.OnPlayerUpdate.Add(LocalPlayerController.PollCutLimbsForBites)

--* Hourly loop: cicatrization, dirt, sepsis, phantom pain *--

---@param fx table
---@param limbName string?
local function ApplyFx(playerObj, limbName, fx)
    if not fx then return end
    local empty = true
    for _ in pairs(fx) do empty = false; break end      -- Kahlua no tiene next()
    if empty then return end
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayPostOpApply, {limbName = limbName, fx = fx})
    else
        PostOp.ApplyEffects(playerObj, limbName, fx)
    end
end

function LocalPlayerController.UpdateAmputations()
    local pl = getPlayer()
    if not pl then return end
    local dcInst = DataController.GetReady(pl:getUsername())
    if not dcInst or not dcInst:getIsAnyLimbCut() then
        Events.EveryHours.Remove(LocalPlayerController.UpdateAmputations)
        return
    end
    LocalPlayerController.playerObj = pl
    local visual = pl:getHumanVisual()
    local amputatedLimbs = CachedDataHandler.GetAmputatedLimbs(pl:getUsername())

    for limbName, _ in pairs(amputatedLimbs) do
        if dcInst:getIsCut(limbName) and dcInst:getIsVisible(limbName) then
            local isCicatrized = dcInst:getIsCicatrized(limbName)
            if not isCicatrized then
                local cicTime = dcInst:getCicatrizationTime(limbName)
                --* Dirt of the wound
                local bbptEnum = BloodBodyPartType[limbName]
                local modifier = 0.01 * sv("WoundDirtynessMultiplier", 1)
                local dirtynessVis = 0
                if bbptEnum then dirtynessVis = (visual:getDirt(bbptEnum) + visual:getBlood(bbptEnum)) * 0.5 end
                local dirtyness = math.max(0, dcInst:getWoundDirtyness(limbName)) + modifier + dirtynessVis * 0.1
                -- a bandage on the stump keeps it clean
                local adj = StaticData.LIMBS_ADJACENT_IND_STR[limbName]
                local adjPart = adj and pl:getBodyDamage():getBodyPart(BodyPartType[adj]) or nil
                if adjPart and adjPart:bandaged() and not adjPart:isBandageDirty() then dirtyness = dirtyness - 0.02 end
                dirtyness = math.max(0, math.min(1, dirtyness))
                dcInst:setWoundDirtyness(limbName, dirtyness)

                --* Cicatrization
                local cicDec = sv("CicatrizationSpeed", 1) - dirtyness
                if cicDec <= 0 then cicDec = 0.1 end
                cicTime = cicTime - cicDec
                if cicTime <= 0 then
                    LocalPlayerController.HandleSetCicatrization(dcInst, pl, limbName)
                else
                    dcInst:setCicatrizationTime(limbName, cicTime)
                end

                --* Sepsis
                local newSepsis, fx = PostOp.HourlySepsis(dcInst, pl, limbName, dirtyness)
                local wasSepsis = dcInst:getSepsis(limbName)
                dcInst:setSepsis(limbName, newSepsis)
                if newSepsis > 25 and wasSepsis <= 25 then Messages.Say(pl, getText("IGUI_TOC_Sepsis_Start"), true) end
                if newSepsis > 60 and wasSepsis <= 60 then Messages.Say(pl, getText("IGUI_TOC_Sepsis_Bad"), true) end
                if newSepsis >= 100 then Messages.Say(pl, getText("IGUI_TOC_Sepsis_Dying"), true) end
                ApplyFx(pl, limbName, fx)
            else
                -- closed stump: sepsis fades
                if dcInst:getSepsis(limbName) > 0 then
                    dcInst:setSepsis(limbName, dcInst:getSepsis(limbName) - 5)
                    ApplyFx(pl, limbName, { woundInfection = dcInst:getSepsis(limbName) > 10 and dcInst:getSepsis(limbName) or 0 })
                end
            end
            dcInst:updateAmputationsFromClient(limbName)

            --* Phantom pain
            local ph = PostOp.PhantomPain(dcInst, limbName)
            if ph then
                Messages.Say(pl, getText("IGUI_TOC_PhantomPain"), true)
                ApplyFx(pl, limbName, { pain = ph.pain })
            end
        end
    end
    dcInst:updatePlusFromClient()
    LocalPlayerController.EnsureStumpItems()
end

function LocalPlayerController.ToggleUpdateAmputations()
    CommonMethods.SafeStartEvent("EveryHours", LocalPlayerController.UpdateAmputations)
end

--* Cicatrization visuals *--

---@param dcInst DataController
---@param playerObj IsoPlayer
---@param limbName string
function LocalPlayerController.HandleSetCicatrization(dcInst, playerObj, limbName)
    dcInst:setIsCicatrized(limbName, true)
    dcInst:setCicatrizationTime(limbName, 0)
    Messages.Say(playerObj, getText("IGUI_TOC_Cicatrized", getText("ContextMenu_Limb_" .. limbName)), false)
    if isClient() then
        sendClientCommand(CommandsData.modules.TOC_ITEMS, "OverrideAmputationItemVisuals",
            {patientNum = playerObj:getOnlineID(), limbName = limbName, isCicatrized = true})
    else
        local ItemsController = require("TOC/Controllers/ItemsController")
        ItemsController.Player.OverrideAmputationItemVisuals(playerObj, limbName, true)
    end
end

--* Stump item integrity (issue #288 "regrowing limbs"): make sure the stump clothing is worn *--

function LocalPlayerController.EnsureStumpItems()
    local pl = getPlayer()
    if not pl then return end
    local dcInst = DataController.GetReady(pl:getUsername())
    if not dcInst or not dcInst:getIsAnyLimbCut() then return end
    local highest = CachedDataHandler.GetHighestAmputatedLimbs(pl:getUsername())
    if not highest then return end
    local worn = {}
    local wornItems = pl:getWornItems()
    for i = 1, wornItems:size() do
        local it = wornItems:get(i - 1)
        if it and it:getItem() then worn[it:getItem():getFullType()] = true end
    end
    for _, limbName in pairs(highest) do
        local fullType = StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. limbName
        if not worn[fullType] then
            local item = pl:getInventory():FindAndReturn(fullType)
            if item then
                pl:setWornItem(item:getBodyLocation(), item)
                pl:resetModelNextFrame()
            else
                TOC_DEBUG.print("Stump item missing for " .. limbName .. ", asking for a respawn")
                if isClient() then
                    sendClientCommand(CommandsData.modules.TOC_ITEMS, "RespawnAmputationItem", {patientNum = pl:getOnlineID(), limbName = limbName})
                else
                    local ItemsController = require("TOC/Controllers/ItemsController")
                    ItemsController.Player.SpawnAmputationItem(pl, limbName)
                    ItemsController.Player.OverrideAmputationItemVisuals(pl, limbName, dcInst:getIsCicatrized(limbName))
                end
            end
        end
    end
end

Events.OnClothingUpdated.Add(function(playerObj)
    if playerObj and playerObj == getPlayer() then
        pcall(LocalPlayerController.EnsureStumpItems)
    end
end)

--* Carry penalty: a missing hand without prosthesis carries less *--

function LocalPlayerController.ApplyCarryPenalty()
    local pl = getPlayer()
    if not pl then return end
    local dcInst = DataController.GetReady(pl:getUsername())
    if not dcInst then return end
    if not sv("CarryPenalty", true) then return end
    local penalty = 0
    for _, side in ipairs(StaticData.SIDES_STR) do
        if dcInst:getIsCut("Hand_" .. side) and not dcInst:getIsProstEquippedGroup("Top_" .. side) then
            penalty = penalty + 2
        end
    end
    local plus = dcInst:plus()
    if plus.carryApplied == penalty then return end
    pcall(function()
        local base = plus.carryDelta
        if base == nil then
            base = pl:getMaxWeightDelta()
            plus.carryDelta = base
        end
        pl:setMaxWeightDelta(base - penalty)
        plus.carryApplied = penalty
    end)
end

Events.OnTOCCacheUpdated.Add(function(username)
    local pl = getPlayer()
    if pl and pl:getUsername() == username then
        pcall(LocalPlayerController.ApplyCarryPenalty)
        pcall(LocalPlayerController.EnsureStumpItems)
    end
end)

---@param itemObj InventoryItem
---@param limbName string
function LocalPlayerController.CanItemBeEquipped(itemObj, limbName)
    local bl = itemObj:getBodyLocation()
    local side = CommonMethods.GetSide(limbName)
    local sideStr = CommonMethods.GetSideFull(side)
    if string.contains(limbName, "Hand_") and (bl == sideStr .. "_MiddleFinger" or bl == sideStr .. "_RingFinger") then return false end
    if string.contains(limbName, "ForeArm_") and (bl == sideStr .. "Wrist") then return false end
    return true
end

return LocalPlayerController
