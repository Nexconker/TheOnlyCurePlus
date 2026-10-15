-- TOC+ SurgeryPlan: gathers what the surgeon has, what the patient is like, and turns it into a risk.
-- Pure data; usable on client (preview) and on server (authoritative roll).
local StaticData = require("TOC/StaticData")
local TourniquetController = require("TOC/Controllers/TourniquetController")
-----------------

local SurgeryPlan = {}

local function clamp(v, a, b) if v < a then return a elseif v > b then return b else return v end end

---@param inv ItemContainer
---@param types table<string, number>
---@return InventoryItem?, number? best item and its tier (lowest tier wins)
local function FindBestOfTypes(inv, types)
    local best, bestTier = nil, 99
    for fullType, tier in pairs(types) do
        if tier < bestTier then
            local item = inv:FindAndReturn(fullType)
            if item then
                local empty = false
                if instanceof(item, "DrainableComboItem") and item:getCurrentUsesFloat() <= 0 then
                    empty = true        -- empty wipes / bottle
                else
                    local okc, isEmpty = pcall(function()
                        return item:hasComponent(ComponentType.FluidContainer) and item:getFluidContainer():getAmount() < 0.15
                    end)
                    if okc and isEmpty then empty = true end    -- empty whiskey
                end
                if not empty then
                    best, bestTier = item, tier
                end
            end
        end
    end
    return best, bestTier
end

---@param player IsoPlayer
---@return InventoryItem?
function SurgeryPlan.GetBandageItem(player)
    local inv = player:getInventory()
    return inv:FindAndReturn("Base.AlcoholBandage") or inv:FindAndReturn("Base.Bandage") or inv:FindAndReturn("Base.AlcoholRippedSheets") or inv:FindAndReturn("Base.RippedSheets")
end

---Suture needle, or thread (only if there is a needle too)
---@param player IsoPlayer
---@return InventoryItem?
function SurgeryPlan.GetStitchesItem(player)
    local inv = player:getInventory()
    local sutureNeedle = inv:FindAndReturn("Base.SutureNeedle")
    if sutureNeedle then return sutureNeedle end
    local needle = inv:FindAndReturn("Base.Needle")
    if not needle then return nil end
    local thread = inv:FindAndReturn("Base.Thread")
    if thread and thread:getUseDelta() > 0 then return thread end
    return nil
end

---@param player IsoPlayer
---@return boolean
function SurgeryPlan.KnowsSurgery(player)
    if not player then return false end
    local ok, known = pcall(function() return player:isRecipeKnown(StaticData.SURGERY_RECIPE) end)
    if ok and known then return true end
    ok, known = pcall(function() return player:getKnownRecipes():contains(StaticData.SURGERY_RECIPE) end)
    return ok and known == true
end

---Anaesthesia level of the patient (0 none .. 1 knocked out) from vanilla stats: painkillers, alcohol, sleeping pills.
---@param patient IsoPlayer
---@return number
function SurgeryPlan.GetAnesthesia(patient)
    local level = 0
    local bd = patient:getBodyDamage()
    local ok, meds = pcall(function() return bd:getPainReductionFromMeds() end)
    if ok and meds then level = level + clamp(meds / 100, 0, 0.6) end
    local ok2, intox = pcall(function() return patient:getStats():get(CharacterStat.INTOXICATION) end)
    if ok2 and intox then level = level + clamp(intox / 100, 0, 0.5) end
    -- sleeping pills: at most SleepingPillAnesthesia % (sandbox, default 30; 0 = they do not count). Was a flat 50.
    local pillCap = ((SandboxVars.TOC and SandboxVars.TOC.SleepingPillAnesthesia) or 30) / 100
    local ok3, pills = pcall(function() return patient:getSleepingTabletEffect() end)
    if ok3 and pills and pillCap > 0 then level = level + clamp(pills / 100, 0, pillCap) end
    return clamp(level, 0, 1)
end

---Build the plan. toolItem may be nil (the UI then shows the limb as not operable).
---@param surgeon IsoPlayer
---@param patient IsoPlayer
---@param limbName string
---@param toolItem InventoryItem?
---@return table plan
function SurgeryPlan.Gather(surgeon, patient, limbName, toolItem)
    local inv = surgeon:getInventory()
    local plan = {}
    plan.limbName = limbName
    plan.isLeg = StaticData.IsLegLimb(limbName)
    plan.selfOp = (surgeon == patient)
    -- above the elbow / knee on yourself: only with the sandbox option SelfAmputationHigh, and much riskier
    plan.selfHigh = plan.selfOp and StaticData.NO_SELF_SURGERY_PARTS_IND_STR[string.match(limbName, "^(%a+)_") or ""] == true
    plan.toolItem = toolItem or FindBestOfTypes(inv, StaticData.SAWS_TYPES)
    plan.toolType = plan.toolItem and plan.toolItem:getFullType() or nil
    plan.toolTier = plan.toolType and StaticData.SAWS_TYPES[plan.toolType] or nil
    plan.bladeItem, plan.bladeTier = FindBestOfTypes(inv, StaticData.BLADE_TYPES)
    plan.bladeType = plan.bladeItem and plan.bladeItem:getFullType() or nil
    plan.disinfectItem = FindBestOfTypes(inv, StaticData.DISINFECTANT_TYPES)
    plan.disinfectType = plan.disinfectItem and plan.disinfectItem:getFullType() or nil
    plan.stitchesItem = SurgeryPlan.GetStitchesItem(surgeon)
    plan.bandageItem = SurgeryPlan.GetBandageItem(surgeon)
    plan.hasTourniquet = TourniquetController.CheckTourniquetOnLimb(patient, limbName)
    plan.anesthesia = SurgeryPlan.GetAnesthesia(patient)
    plan.knows = SurgeryPlan.KnowsSurgery(surgeon)
    plan.doctorLevel = surgeon:getPerkLevel(Perks.Doctor)
    local stats = surgeon:getStats()
    plan.fatigue = clamp(stats:get(CharacterStat.FATIGUE) or 0, 0, 1)
    plan.panic = clamp((stats:get(CharacterStat.PANIC) or 0) / 100, 0, 1)
    local okd, drunk = pcall(function() return stats:get(CharacterStat.INTOXICATION) end)
    plan.drunk = okd and clamp((drunk or 0) / 100, 0, 1) or 0
    plan.hemophobic = surgeon:hasTrait(CharacterTrait.HEMOPHOBIC)
    plan.surgeonOneHanded = false
    local CachedDataHandler = require("TOC/Handlers/CachedDataHandler")
    local okc, both = pcall(CachedDataHandler.GetHandFeasibilityBoth, surgeon:getUsername())
    if okc and both == false then plan.surgeonOneHanded = true end
    return plan
end

---Serializable summary to send over the network (the server re-gathers items from its own copy
---of the surgeon's inventory; only the choices travel).
---@param plan table
---@return table
function SurgeryPlan.Pack(plan)
    return { toolType = plan.toolType, bladeType = plan.bladeType, disinfectType = plan.disinfectType }
end

---Risk model. Returns probabilities and multipliers.
---@param plan table
---@return table risk
function SurgeryPlan.Risk(plan)
    local r = {}
    local base = StaticData.LIMBS_SURGERY_BASE_RISK_IND_NUM[plan.limbName] or 0.15
    local fail = base
    fail = fail + (plan.toolTier and StaticData.SAW_TIER_RISK[plan.toolTier] or 0.5)
    fail = fail + (plan.bladeTier and StaticData.BLADE_TIER_RISK[plan.bladeTier] or 0.08)
    if not plan.hasTourniquet then fail = fail + 0.15 end
    if not plan.disinfectItem then fail = fail + 0.04 end
    if not plan.stitchesItem then fail = fail + 0.10 end
    if plan.knows then fail = fail - 0.08 end
    fail = fail - plan.doctorLevel * 0.025
    if plan.selfOp then fail = fail + 0.12 end
    if plan.selfHigh then fail = fail + 0.15 end
    if plan.surgeonOneHanded then fail = fail + 0.10 end
    fail = fail + plan.fatigue * 0.15 + plan.panic * 0.15 + plan.drunk * 0.20
    if plan.hemophobic then fail = fail + 0.10 end
    local mult = (SandboxVars.TOC and SandboxVars.TOC.SurgeryRiskMultiplier) or 1.0
    r.fail = clamp(fail * mult, 0.01, 0.95)
    r.severe = clamp(r.fail * 0.35, 0.005, 0.6)

    -- pain / noise / fainting
    r.painLevel = clamp(1 - plan.anesthesia, 0, 1)
    local screamRadius = (SandboxVars.TOC and SandboxVars.TOC.ScreamRadius) or 25
    r.noiseRadius = math.floor(screamRadius * r.painLevel)
    local faint = 0.25 * r.painLevel
    if plan.selfOp then faint = faint + 0.12 * r.painLevel end
    if plan.selfHigh then faint = faint + 0.15 * r.painLevel end
    if plan.hasTourniquet then faint = faint * 0.8 end
    r.faintChance = clamp(faint, 0, plan.selfHigh and 0.75 or 0.6)

    -- consequences of a clean surgery
    r.cicMult = plan.toolTier == 0 and 0.85 or 1.0
    if plan.knows then r.cicMult = r.cicMult * 0.9 end
    r.dirt0 = plan.disinfectItem and 0.05 or 0.25
    r.bleedMult = plan.hasTourniquet and 0.6 or 1.0
    if not plan.stitchesItem then r.bleedMult = r.bleedMult * 1.5 end
    r.damageMult = plan.toolTier and StaticData.SAW_TIER_DAMAGE[plan.toolTier] or 1.3
    return r
end

---Human-readable bracket for the risk (used by the UI). Returns key suffix and the number.
---@param risk table
---@return string bracket Low|Medium|High|VeryHigh
function SurgeryPlan.Bracket(risk)
    if risk.fail < 0.15 then return "Low" elseif risk.fail < 0.35 then return "Medium" elseif risk.fail < 0.6 then return "High" end
    return "VeryHigh"
end

---Roll the outcome. Call on the authoritative side.
---@param plan table
---@param risk table?
---@return table outcome {severity=0|1|2, cicMult, dirt0, bleedMult, extraDamage, damageMult}
function SurgeryPlan.Roll(plan, risk)
    risk = risk or SurgeryPlan.Risk(plan)
    local roll = ZombRandFloat(0.0, 1.0)
    local o = { severity = 0, cicMult = risk.cicMult, dirt0 = risk.dirt0, bleedMult = risk.bleedMult, extraDamage = 0, damageMult = risk.damageMult, roll = roll }
    if roll < risk.severe then
        o.severity = 2
        o.cicMult = risk.cicMult * 1.8
        o.dirt0 = math.max(risk.dirt0, 0.6)
        o.bleedMult = risk.bleedMult * 3.0
        o.extraDamage = 30
    elseif roll < risk.fail then
        o.severity = 1
        o.cicMult = risk.cicMult * 1.4
        o.dirt0 = math.max(risk.dirt0, 0.35)
        o.bleedMult = risk.bleedMult * 1.6
        o.extraDamage = 15
    end
    return o
end

---Steps shown in the window: {key, ok, item}
---@param plan table
---@return table[]
function SurgeryPlan.Steps(plan)
    local steps = {}
    table.insert(steps, { key = "Tourniquet", ok = plan.hasTourniquet })
    table.insert(steps, { key = "Disinfect", ok = plan.disinfectItem ~= nil, item = plan.disinfectItem })
    table.insert(steps, { key = "Anesthesia", ok = plan.anesthesia >= 0.5, partial = plan.anesthesia > 0 and plan.anesthesia < 0.5 })
    table.insert(steps, { key = "Incision", ok = plan.bladeItem ~= nil, item = plan.bladeItem })
    table.insert(steps, { key = "Bone", ok = plan.toolItem ~= nil, item = plan.toolItem, tier = plan.toolTier })
    table.insert(steps, { key = "Stitches", ok = plan.stitchesItem ~= nil, item = plan.stitchesItem })
    table.insert(steps, { key = "Bandage", ok = plan.bandageItem ~= nil, item = plan.bandageItem })
    return steps
end

return SurgeryPlan
