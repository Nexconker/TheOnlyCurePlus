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
