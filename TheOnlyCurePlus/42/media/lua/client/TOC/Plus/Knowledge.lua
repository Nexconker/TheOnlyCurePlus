-- TOC+ Knowledge: who knows how to do a field amputation. Doctors and nurses start with it,
-- everybody else reads the "Field Amputation Guide" (which teaches the FieldSurgery recipe).
local StaticData = require("TOC/StaticData")
local SurgeryPlan = require("TOC/Plus/SurgeryPlan")
-----------------

local Knowledge = {}

-- vanilla B42 sólo tiene doctor y nurse; el resto cubre profesiones añadidas por otros mods
local PROFESSIONS = { "doctor", "nurse", "veterinarian", "paramedic", "medic", "surgeon" }

---@param player IsoPlayer
function Knowledge.GrantProfession(player)
    if not player or not player:isLocalPlayer() then return end
    if SurgeryPlan.KnowsSurgery(player) then return end
    local desc = player:getDescriptor()
    if not desc then return end
    -- B42: SurvivorDesc:getCharacterProfession() -> CharacterProfession (registro "base:doctor"); getName() -> "doctor"
    local prof = ""
    if desc.getCharacterProfession then
        local cp = desc:getCharacterProfession()
        if cp then prof = (cp.getName and cp:getName()) or tostring(cp) or "" end
    elseif desc.getProfession then
        prof = tostring(desc:getProfession())
    end
    prof = string.lower(prof or "")
    for _, p in ipairs(PROFESSIONS) do
        if string.contains(prof, p) then
            local ok, err = pcall(function() player:getKnownRecipes():add(StaticData.SURGERY_RECIPE) end)
            if ok then
                TOC_DEBUG.print("Granted field surgery knowledge to " .. prof)
            else
                TOC_DEBUG.print("Could not grant surgery recipe: " .. tostring(err))
            end
            return
        end
    end
end

return Knowledge
