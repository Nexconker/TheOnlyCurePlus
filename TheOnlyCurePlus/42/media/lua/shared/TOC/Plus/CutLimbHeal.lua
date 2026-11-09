-- TOC+: what the vanilla BodyPart of an amputated limb must not keep (bites, cuts, glass, bullets, burns...).
-- Shared by the client poll (LocalPlayerController) and the server sanitizer (ServerDamageSanitizer): BOTH must clear
-- the same things. In multiplayer the server owns BodyDamage; if only the client cleaned a glass shard or a cut, the
-- server pushed its old state back and the wound reappeared, in a loop.

local CutLimbHeal = {}

---Anything left on this body part that a missing limb cannot have?
---@param bodyPart BodyPart
---@return boolean
function CutLimbHeal.HasAnything(bodyPart)
    if not bodyPart then return false end
    return bodyPart:bitten() or bodyPart:IsInfected() or bodyPart:HasInjury() or bodyPart:haveGlass()
end

-- each call on its own: one that fails (renamed in a later build) must not skip the rest
local CLEAR = {
    { "setFractureTime", 0 }, { "setScratched", false, true }, { "setScratchTime", 0 },
    { "setBleeding", false }, { "setBleedingTime", 0 }, { "SetBitten", false }, { "setBiteTime", 0 },
    { "SetInfected", false }, { "setInfectedWound", false }, { "setWoundInfectionLevel", 0 },
    { "setCut", false }, { "setCutTime", 0 }, { "setDeepWounded", false }, { "setDeepWoundTime", 0 },
    { "setHaveBullet", false, 0 }, { "setHaveGlass", false }, { "setSplint", false, 0 },
    -- B42: setBurned() takes no "false": it ROLLS A NEW BURN. A burn is cleared through its timer.
    { "setBurnTime", 0 }, { "setNeedBurnWash", false },
}

---3.3.3 (Workshop, Red: "a zombie bit my hand, I didn't get the injury but got the infection"): un mordisco que cae
---en la parte de un miembro amputado deja también la infección GENERAL del cuerpo (Knox), no sólo la de esa parte.
---Se quita, salvo que otra parte que sí existe esté mordida o infectada (entonces la infección es de verdad).
---@param bd BodyDamage
---@param dcInst DataController
---@return boolean cleared
function CutLimbHeal.ClearStrayInfection(bd, dcInst)
    if not bd or not dcInst then return false end
    local StaticData = require("TOC/StaticData")
    local parts = bd:getBodyParts()
    for i = 0, parts:size() - 1 do
        local part = parts:get(i)
        local limbName = StaticData.BODYLOCS_TO_LIMBS_IND_STR[BodyPartType.ToString(part:getType())]
        local missing = limbName ~= nil and dcInst:getIsCut(limbName)
        if not missing and (part:bitten() or part:IsInfected()) then return false end
    end
    if not bd:IsInfected() then return false end
    -- una infección que la cirugía ya dio por perdida (tarde, o mordisco en el torso) no se cura con otro mordisco
    local outcome = dcInst:plus().cureOutcome
    if outcome == "late" or outcome == "doomed" or dcInst:getIsIgnoredPartInfected() then return false end
    pcall(function()
        bd:setInfected(false)
        bd:setInfectionMortalityDuration(-1)
        bd:setInfectionTime(-1)
    end)
    pcall(function()
        local st = bd:getParentChar():getStats()
        st:set(CharacterStat.ZOMBIE_INFECTION, 0)
        st:set(CharacterStat.ZOMBIE_FEVER, 0)
    end)
    return true
end

---Clear every injury on a body part that no longer exists
---@param bodyPart BodyPart
function CutLimbHeal.Clear(bodyPart)
    if not bodyPart then return end
    for i = 1, #CLEAR do
        local c = CLEAR[i]
        local m = bodyPart[c[1]]
        -- exact argument count: Kahlua picks the Java overload by count and a trailing nil still counts
        if m then
            if c[3] ~= nil then pcall(m, bodyPart, c[2], c[3]) else pcall(m, bodyPart, c[2]) end
        end
    end
end

return CutLimbHeal
