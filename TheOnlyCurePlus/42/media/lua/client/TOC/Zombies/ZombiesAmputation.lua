require "lua_timers"
local ZombieStumps = require("TOC/Handlers/ZombieStumps")
local StaticData = require("TOC/StaticData")
local CommandsData = require("TOC/CommandsData")
-------------------------------

-- TOC+: zombies lose the limb you actually hit (B42 OnHitZombie gives the body part),
-- and a zombie that loses a leg becomes a crawler.

---@param zombie IsoZombie
---@return integer trueID
local function GetZombieID(zombie)
    -- Big love to Chuck and Sir Doggy Jvla for this code
    local pID = zombie:getPersistentOutfitID()
    local bits = string.split(string.reverse(Long.toUnsignedString(pID, 2)), "")
    while #bits < 16 do bits[#bits + 1] = 0 end
    bits[16] = 0
    return Long.parseUnsignedLong(string.reverse(table.concat(bits, "")), 2)
end

local function PredicateAmputationItems(item)
    return item:getType():contains("Amputation_")
end

local function sv(name, default)
    local v = SandboxVars.TOC and SandboxVars.TOC[name]
    if v == nil then return default end
    return v
end

---@param zombie IsoZombie
local function MakeCrawler(zombie)
    if not sv("ZombieCrawlerOnLegHit", true) then return end
    local crawling = false
    pcall(function() crawling = zombie:isCrawling() end)
    if crawling then return end
    pcall(function() zombie:toggleCrawling() end)
    if isClient() then
        pcall(function()
            sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayZombieCrawler, {zombieID = zombie:getOnlineID()})
        end)
    end
end

---@param zombie IsoZombie
---@param limbName string
local function SpawnAmputation(zombie, limbName)
    local amputationFullType = StaticData.AMPUTATION_CLOTHING_ITEM_BASE .. limbName
    ZombieStumps.Spawn(zombie, amputationFullType)

    local pID = GetZombieID(zombie)
    local zombieKey = CommandsData.GetZombieKey()
    local zombiesMD = ModData.getOrCreate(zombieKey)
    if zombiesMD[pID] == nil then zombiesMD[pID] = {} end
    local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
    zombiesMD[pID][group] = amputationFullType
    if StaticData.IsLegLimb(limbName) then
        zombiesMD[pID].crawler = true
        MakeCrawler(zombie)
    end
    ModData.add(zombieKey, zombiesMD)
    if isClient() then ModData.transmit(zombieKey) end
end

local bloodAmount = 10

---@param zombie IsoZombie
---@param wielder IsoGameCharacter
---@param bodyPartType BodyPartType
---@param weapon HandWeapon
local function OnHitZombie(zombie, wielder, bodyPartType, weapon)
    if not sv("EnableZombieAmputations", false) then return end
    if isServer() then return end
    if not zombie or not instanceof(zombie, "IsoZombie") or not wielder or not instanceof(wielder, "IsoPlayer") then return end
    if isClient() and not wielder:isLocalPlayer() then return end
    if not weapon or not weapon.getScriptItem then return end

    -- B42: Item:containsWeaponCategory(WeaponCategory.X) (getCategories() ya no existe)
    local script = weapon:getScriptItem()
    if not script or not script.containsWeaponCategory or not WeaponCategory then return end
    local ok = script:containsWeaponCategory(WeaponCategory.AXE) or script:containsWeaponCategory(WeaponCategory.LONG_BLADE)
    if not ok then return end

    local limbName = bodyPartType and StaticData.BODYLOCS_TO_LIMBS_IND_STR[BodyPartType.ToString(bodyPartType)] or nil
    if not limbName then return end

    local isCrit = false
    pcall(function() isCrit = wielder:isCriticalHit() end)
    local chance = sv("ZombieAmputationDamageChance", 25)
    local maxDmg = 1
    pcall(function() maxDmg = weapon:getMaxDamage() end)
    local threshold = sv("ZombieAmputationDamageThreshold", 1)
    if not (isCrit or (maxDmg >= threshold and ZombRand(100) < chance)) then return end

    local group = StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName]
    local pID = GetZombieID(zombie)
    local zombiesMD = ModData.getOrCreate(CommandsData.GetZombieKey())
    if zombiesMD[pID] and zombiesMD[pID][group] then return end        -- already lost that limb

    SpawnAmputation(zombie, limbName)

    pcall(function() addBloodSplat(getCell():getGridSquare(zombie:getX(), zombie:getY(), zombie:getZ()), bloodAmount) end)
    local timerName = tostring(pID) .. "_timer"
    timer:Create(timerName, 1, 8, function()
        pcall(function() addBloodSplat(getCell():getGridSquare(zombie:getX(), zombie:getY(), zombie:getZ()), bloodAmount) end)
    end)
end

Events.OnHitZombie.Add(OnHitZombie)

-----------------------------

local localOnlyZombiesMD

local function SetupZombiesModData()
    localOnlyZombiesMD = ModData.getOrCreate(CommandsData.GetZombieKey())
end

Events.OnInitGlobalModData.Add(SetupZombiesModData)

---@param zombie IsoZombie
local function ReapplyAmputation(zombie)
    if not sv("EnableZombieAmputations", false) or not localOnlyZombiesMD then return end
    local pID = GetZombieID(zombie)
    local data = localOnlyZombiesMD[pID]
    if data == nil then return end

    local zombieInv = zombie:getInventory()
    if zombieInv:containsEvalRecurse(PredicateAmputationItems) then return end
    for _, group in ipairs(StaticData.AMP_GROUPS_STR) do
        if data[group] then ZombieStumps.Spawn(zombie, data[group]) end
    end
    -- old TOC data used "L"/"R" keys for arms
    if data.L then ZombieStumps.Spawn(zombie, data.L) end
    if data.R then ZombieStumps.Spawn(zombie, data.R) end
    if data.crawler then MakeCrawler(zombie) end
    localOnlyZombiesMD[pID] = nil
end

Events.OnZombieUpdate.Add(ReapplyAmputation)
