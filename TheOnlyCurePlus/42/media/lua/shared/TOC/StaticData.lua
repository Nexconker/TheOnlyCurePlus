---@alias partDataType { isCut : boolean?, isInfected : boolean?, isOperated : boolean?, isCicatrized : boolean?, isCauterized : boolean?, isVisible : boolean?, woundDirtyness : number, cicatrizationTime : number, sepsis : number?, cicatrizationMax : number? }
---@alias limbsTable table<string, partDataType>
---@alias prosthesisData {isProstEquipped : boolean, prostFactor : number, prostType : string?, wear : number? }
---@alias prosthesesTable {Top_L : prosthesisData, Top_R : prosthesisData, Bottom_L : prosthesisData, Bottom_R : prosthesisData }
---@alias plusDataType { shockUntil : number, convalescenceUntil : number, phantomNext : number, lastDiagnosis : table, botched : table<string, number>, cureOutcome : string?, knowsSurgery : boolean? }
---@alias tocModDataType { limbs : limbsTable, prostheses : prosthesesTable, isIgnoredPartInfected : boolean, isAnyLimbCut : boolean, plus : plusDataType? }
---------------------------

-- TOC+ : StaticData now covers arms AND legs. Everything is still generated from
-- PARTS so that the rest of the mod can loop over StaticData.LIMBS_STR without caring.
--
-- _STR = Only strings, no index
-- _IND_STR =  indexed Strings
-- _IND_BPT = Indexed BodyPartType
--
-- PART = Single part, could be hand, forearm, etc
-- LIMB = Part + side
-- BODYLOCS = Body Locations

local StaticData = {}

---Mod name, used to setup Global Mod Data and various stuff. Kept as "TOC" so that
---saves made with the original mod keep working after switching to TOC+.
StaticData.MOD_NAME = "TOC"
StaticData.PLUS_VERSION = "3.1.2"

StaticData.COMPAT_42 = luautils.stringStarts(getGameVersion(), "42")

-------------------------
--* Base

StaticData.SIDES_IND_STR = { R = "R", L = "L" }
StaticData.SIDES_STR = { "R", "L" }

-- Order matters: it is the order used in menus. Arms first (original), legs after.
StaticData.PARTS_STR = { "Hand", "ForeArm", "UpperArm", "Foot", "LowerLeg", "UpperLeg" }
StaticData.PARTS_IND_STR = {}
for i = 1, #StaticData.PARTS_STR do StaticData.PARTS_IND_STR[StaticData.PARTS_STR[i]] = StaticData.PARTS_STR[i] end

StaticData.ARM_PARTS_IND_STR = { Hand = true, ForeArm = true, UpperArm = true }
StaticData.LEG_PARTS_IND_STR = { Foot = true, LowerLeg = true, UpperLeg = true }

-- Body parts where a bite means certain death (nothing to cut).
StaticData.IGNORED_BODYLOCS_BPT = {
    BodyPartType.Groin, BodyPartType.Head, BodyPartType.Neck, BodyPartType.Torso_Lower, BodyPartType.Torso_Upper
}

-- Assembled BodyParts string
StaticData.LIMBS_STR = {}
StaticData.LIMBS_IND_STR = {}
StaticData.LIMBS_DEPENDENCIES_IND_STR = {}
StaticData.LIMBS_ADJACENT_IND_STR = {}
StaticData.LIMBS_CICATRIZATION_TIME_IND_NUM = {}
StaticData.LIMBS_BASE_DAMAGE_IND_NUM = {}
StaticData.LIMBS_TIME_MULTIPLIER_IND_NUM = {}
StaticData.LIMBS_SURGERY_BASE_RISK_IND_NUM = {}      -- base failure chance (0..1) of the surgery, before modifiers
StaticData.LIMBS_SEVERED_ITEM_IND_STR = {}           -- limbName -> full type of the severed limb item

StaticData.LIMBS_TO_BODYLOCS_IND_BPT = {}            -- {limbName = bodyLoc}
StaticData.BODYLOCS_TO_LIMBS_IND_STR = {}            -- {bodyLoc = limbName}

local PART_DATA = {
    --              dmg  cicHours timeMult risk  dependencies           adjacent          severed
    Hand     = { 60,  120, 2.0, 0.08, {},                    "ForeArm_%s",     "TOC.SeveredHand" },
    ForeArm  = { 80,  144, 3.0, 0.12, {"Hand"},              "UpperArm_%s",    "TOC.SeveredForeArm" },
    UpperArm = { 100, 192, 4.0, 0.20, {"Hand", "ForeArm"},   "Torso_Upper",    "TOC.SeveredUpperArm" },
    Foot     = { 70,  150, 1.15, 0.10, {},                   "LowerLeg_%s",    "TOC.SeveredFoot" },
    LowerLeg = { 90,  180, 1.25, 0.16, {"Foot"},             "UpperLeg_%s",    "TOC.SeveredLowerLeg" },
    UpperLeg = { 110, 240, 1.4, 0.26, {"Foot", "LowerLeg"},  "Torso_Lower",    "TOC.SeveredUpperLeg" },
}

for _, side in ipairs(StaticData.SIDES_STR) do
    for _, part in ipairs(StaticData.PARTS_STR) do
        local assembledName = part .. "_" .. side
        table.insert(StaticData.LIMBS_STR, assembledName)
        StaticData.LIMBS_IND_STR[assembledName] = assembledName

        ---@type BodyPartType
        local bptType = BodyPartType[assembledName]
        local bptString = BodyPartType.ToString(bptType)
        StaticData.LIMBS_TO_BODYLOCS_IND_BPT[assembledName] = bptType
        StaticData.BODYLOCS_TO_LIMBS_IND_STR[bptString] = assembledName

        local d = PART_DATA[part]
        StaticData.LIMBS_BASE_DAMAGE_IND_NUM[assembledName] = d[1]
        StaticData.LIMBS_CICATRIZATION_TIME_IND_NUM[assembledName] = d[2]
        StaticData.LIMBS_TIME_MULTIPLIER_IND_NUM[assembledName] = d[3]
        StaticData.LIMBS_SURGERY_BASE_RISK_IND_NUM[assembledName] = d[4]
        local deps = {}
        for _, depPart in ipairs(d[5]) do table.insert(deps, depPart .. "_" .. side) end
        StaticData.LIMBS_DEPENDENCIES_IND_STR[assembledName] = deps
        StaticData.LIMBS_ADJACENT_IND_STR[assembledName] = string.format(d[6], side)
        StaticData.LIMBS_SEVERED_ITEM_IND_STR[assembledName] = d[7]
    end
end

---@param limbName string
---@return boolean
function StaticData.IsLegLimb(limbName)
    local part = string.match(limbName, "^(%a+)_")
    return StaticData.LEG_PARTS_IND_STR[part] == true
end

---@param limbName string
---@return boolean
function StaticData.IsArmLimb(limbName)
    local part = string.match(limbName, "^(%a+)_")
    return StaticData.ARM_PARTS_IND_STR[part] == true
end

-----------------
--* Amputation Groups

StaticData.AMP_GROUPS_BASE_IND_STR = { Top = "Top", Bottom = "Bottom" }
StaticData.AMP_GROUPS_IND_STR = {}
StaticData.AMP_GROUPS_STR = {}

for _, side in ipairs(StaticData.SIDES_STR) do
    for _, group in ipairs({ "Top", "Bottom" }) do
        local sidedGroup = group .. "_" .. side
        StaticData.AMP_GROUPS_IND_STR[sidedGroup] = sidedGroup
        table.insert(StaticData.AMP_GROUPS_STR, sidedGroup)
    end
end

StaticData.AMP_GROUP_TO_LIMBS_MATCH_IND_STR = {}
StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR = {}

for _, side in ipairs(StaticData.SIDES_STR) do
    for _, part in ipairs(StaticData.PARTS_STR) do
        local limbName = part .. "_" .. side
        local group = StaticData.ARM_PARTS_IND_STR[part] and "Top" or "Bottom"
        local sidedGroup = group .. "_" .. side
        StaticData.AMP_GROUP_TO_LIMBS_MATCH_IND_STR[sidedGroup] = StaticData.AMP_GROUP_TO_LIMBS_MATCH_IND_STR[sidedGroup] or {}
        table.insert(StaticData.AMP_GROUP_TO_LIMBS_MATCH_IND_STR[sidedGroup], limbName)
        StaticData.LIMBS_TO_AMP_GROUPS_MATCH_IND_STR[limbName] = sidedGroup
    end
end

-- Highest part of each group where no prosthesis can be fitted. Legs have an above-knee prosthesis (thigh socket +
-- articulated knee) and, since 3.1.0, arms have an above-elbow one (upper-arm socket + elbow hinge): none left.
StaticData.NO_PROSTHESIS_PARTS_IND_STR = {}
-- Parts a surgeon cannot amputate on themselves.
StaticData.NO_SELF_SURGERY_PARTS_IND_STR = { UpperArm = true, UpperLeg = true }

-- Tourniquets: item type prefix per group base
StaticData.TOURNIQUET_TYPE_PREFIX = { Top = "Surg_Arm_Tourniquet_", Bottom = "Surg_Leg_Tourniquet_" }

StaticData.AFFECTED_BODYLOCS_TO_LIMBS_IND_STR = {}

local handsBodyLocs = {"Hands%s", "%s_MiddleFinger", "%s_RingFinger"}
local foreArmBodyLocs = {"%sWrist"}

for _, side in ipairs(StaticData.SIDES_STR) do
    local sideFull = side == "R" and "Right" or "Left"
    for i = 1, #handsBodyLocs do
        StaticData.AFFECTED_BODYLOCS_TO_LIMBS_IND_STR[string.format(handsBodyLocs[i], sideFull)] = "Hand_" .. side
    end
    for i = 1, #foreArmBodyLocs do
        StaticData.AFFECTED_BODYLOCS_TO_LIMBS_IND_STR[string.format(foreArmBodyLocs[i], sideFull)] = "ForeArm_" .. side
    end
end

-----------------
--* Traits

-- Link a trait to a specific body part (TOC+: both sides, arms and lower legs)
StaticData.TRAITS_BP = {
    Amputee_Hand = "Hand_L",
    Amputee_ForeArm = "ForeArm_L",
    Amputee_UpperArm = "UpperArm_L",
    Amputee_Hand_R = "Hand_R",
    Amputee_ForeArm_R = "ForeArm_R",
    Amputee_UpperArm_R = "UpperArm_R",
    Amputee_Foot = "Foot_L",
    Amputee_LowerLeg = "LowerLeg_L",
    Amputee_Foot_R = "Foot_R",
    Amputee_LowerLeg_R = "LowerLeg_R",
}

-----------------
--* Visuals and clothing

StaticData.HEALTH_PANEL_TEXTURES = { Female = {}, Male = {}, ProstArm = {}, ProstLeg = {} }
for _, sex in ipairs({ "Female", "Male" }) do
    for i = 1, #StaticData.LIMBS_STR do
        local limbName = StaticData.LIMBS_STR[i]
        StaticData.HEALTH_PANEL_TEXTURES[sex][limbName] = getTexture("media/ui/" .. sex .. "/" .. limbName .. ".png")
    end
end
for _, side in ipairs(StaticData.SIDES_STR) do
    StaticData.HEALTH_PANEL_TEXTURES.ProstArm[side] = getTexture("media/ui/ProstArm_" .. side .. ".png")
    StaticData.HEALTH_PANEL_TEXTURES.ProstLeg[side] = getTexture("media/ui/ProstLeg_" .. side .. ".png")
end

StaticData.AMPUTATION_CLOTHING_ITEM_BASE = "TOC.Amputation_"

------------------
--* Surgery tools (TOC+)

-- Tier 0 = purpose-made surgical saw ... 3 = crude chopping tool. Lower is better.
StaticData.SAWS_TYPES = {
    ["TOC.BoneSaw"] = 0,
    ["TOC.SurgicalKit"] = 0,
    ["Base.Saw"] = 1,
    ["Base.GardenSaw"] = 2,
    ["Base.Plank_Saw"] = 2,
    ["Base.SmallSaw"] = 2,
    ["Base.Machete"] = 3,
    ["Base.MacheteForged"] = 3,
    ["Base.Hatchet"] = 3,
    ["Base.HandAxe_Old"] = 3,
    ["Base.HandAxe"] = 3,
    ["Base.MeatCleaver"] = 3,
}
StaticData.SAW_TIER_NAMES = { [0] = "Surgical", [1] = "Fine", [2] = "Coarse", [3] = "Crude" }
-- Extra failure risk and damage multiplier per tool tier
StaticData.SAW_TIER_RISK = { [0] = 0.0, [1] = 0.05, [2] = 0.12, [3] = 0.25 }
StaticData.SAW_TIER_DAMAGE = { [0] = 0.7, [1] = 0.85, [2] = 1.0, [3] = 1.3 }

-- Blades for the incision step. Lower is better.
StaticData.BLADE_TYPES = {
    ["Base.Scalpel"] = 0,
    ["TOC.SurgicalKit"] = 0,
    ["Base.HuntingKnife"] = 1,
    ["Base.KitchenKnife"] = 1,
    ["Base.SmallKnife"] = 1,
    ["Base.FlintKnife"] = 2,
    ["Base.BreadKnife"] = 2,
    ["Base.Machete"] = 2,
    ["Base.MeatCleaver"] = 2,
    ["Base.ButterKnife"] = 3,
    ["Base.Scissors"] = 3,
}
StaticData.BLADE_TIER_RISK = { [0] = 0.0, [1] = 0.03, [2] = 0.06, [3] = 0.10 }

StaticData.DISINFECTANT_TYPES = {
    ["Base.Disinfectant"] = 1.0,
    ["Base.AlcoholWipes"] = 0.8,
    ["Base.AlcoholBandage"] = 0.6,
    ["Base.AlcoholRippedSheets"] = 0.5,
    ["Base.Whiskey"] = 0.5,
    ["Base.Vodka"] = 0.5,
}

StaticData.SURGERY_RECIPE = "TOC.FieldSurgery"      -- recipe name used as "knowledge" flag
StaticData.CRUTCH_TAG = "toc:crutch"

------------------
--* Prostheses (TOC+ tiers)

-- Keyed by item type WITHOUT the _L/_R suffix.
-- tier: 1 wood, 2 hook, 3 mechanical, 4 medical.
-- timeBonus: perk levels "granted" for action speed; sprint/run: legs; twoHanded: allows
-- two-handed weapons / long firearms with it (arms); wearPerAction: wear points per timed action.
StaticData.PROSTHESIS_TIERS = {
    Prost_PegArm     = { tier = 1, group = "Top",    timeBonus = 0, twoHanded = false, combatMod = 0.80, wearPerAction = 1.0, hookLike = true },
    Prost_HookArm    = { tier = 2, group = "Top",    timeBonus = 1, twoHanded = false, combatMod = 0.90, wearPerAction = 0.6, hookLike = true },
    Prost_NormalArm  = { tier = 3, group = "Top",    timeBonus = 2, twoHanded = true,  combatMod = 0.95, wearPerAction = 0.4 },
    Prost_MedicalArm = { tier = 4, group = "Top",    timeBonus = 4, twoHanded = true,  combatMod = 1.00, wearPerAction = 0.2 },
    -- Ash-style chainsaw arm (right only): the right hand is the saw (TOC.MountedChainsaw), see TOC/Plus/ChainsawArm
    Prost_ChainsawArm = { tier = 3, group = "Top",   timeBonus = 0, twoHanded = false, combatMod = 0.90, wearPerAction = 0.6, hookLike = true, chainsaw = true },
    Prost_PegLeg     = { tier = 1, group = "Bottom", timeBonus = 0, sprint = false, run = true,  wearPerAction = 0.8 },
    Prost_MechLeg    = { tier = 3, group = "Bottom", timeBonus = 2, sprint = true,  run = true,  wearPerAction = 0.4 },
    Prost_MedicalLeg = { tier = 4, group = "Bottom", timeBonus = 4, sprint = true,  run = true,  wearPerAction = 0.2 },
}
StaticData.PROSTHESIS_WEAR_PER_CONDITION = 40      -- wear points that cost one condition point

-- Every tier exists in model variants per amputation level (same name, icon and stats; only the
-- worn model differs): item name = base .. suffix .. _side, e.g. Prost_HookArmWrist_L.
StaticData.PROSTHESIS_LEVEL_SUFFIX = { Hand = "Wrist", ForeArm = "", UpperArm = "Upper", Foot = "Ankle", LowerLeg = "", UpperLeg = "Thigh" }
local LEVEL_SUFFIXES = { "Wrist", "Upper", "Ankle", "Thigh" }

---@param fullType string e.g. "TOC.Prost_HookArmWrist_L"
---@return string? base e.g. "Prost_HookArm" (level suffix removed), string? side
function StaticData.GetProsthesisBase(fullType)
    if type(fullType) ~= "string" then return nil end
    local base, side = string.match(fullType, "^TOC%.(Prost_%a+)_([LR])$")
    if not base then return nil end
    for _, suf in ipairs(LEVEL_SUFFIXES) do
        if #base > #suf and string.sub(base, -#suf) == suf then
            base = string.sub(base, 1, #base - #suf)
            break
        end
    end
    return base, side
end

---@param fullType string e.g. "TOC.Prost_HookArm_L"
---@return table? tierData
function StaticData.GetProsthesisTier(fullType)
    local base = StaticData.GetProsthesisBase(fullType)
    if not base then return nil end
    return StaticData.PROSTHESIS_TIERS[base]
end

---Item type of the variant modelled for a stump level
---@param fullType string any variant of the prosthesis
---@param part string highest amputated part, e.g. "Hand", "LowerLeg"
---@return string? fullType
function StaticData.GetProsthesisTypeForPart(fullType, part)
    local base, side = StaticData.GetProsthesisBase(fullType)
    local suf = StaticData.PROSTHESIS_LEVEL_SUFFIX[part]
    if not base or suf == nil then return nil end
    return "TOC." .. base .. suf .. "_" .. side
end

------------------
--* Mobility (legs)

StaticData.MOBILITY = {
    NONE = "NONE",          -- one leg missing, no crutch: can't walk
    CRAWL = "CRAWL",        -- both legs missing, no prostheses: crawling only (zombie crawler animation)
    CRUTCH = "CRUTCH",      -- walking with a crutch: no running
    PEG = "PEG",            -- peg leg: run but no sprint
    FULL = "FULL",          -- mechanical/medical leg or no leg amputation
}

return StaticData
