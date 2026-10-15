---@class Compat
---@field handlers table<string, {fun : function, isActive : boolean}>
local Compat = {
    handlers = {}
}

-- Fancy Handwork and Brutal Handwork only exist for Build 41 (no B42 release as of Oct 2026).
-- The handlers stay, wrapped in pcall, so a future port keeps working without touching this file.

function Compat.BrutalHandwork()
    BrutalHands = BrutalHands or {}
    BrutalHands.TOC = require("TOC/API")
end

function Compat.FancyHandwork()
    require("TimedActions/FHSwapHandsAction")
    if not FHSwapHandsAction then return end
    local og_FHSwapHandsAction_isValid = FHSwapHandsAction.isValid
    function FHSwapHandsAction:isValid()
        local tocApi = require("TOC/API")
        if tocApi.hasBothHands(self.character) then
            return og_FHSwapHandsAction_isValid(self)
        end
        return false
    end
end

function Compat.iMeds()
    require("Component/Interface/Service/ContextMenu/Menu/HealthPanel/HealthPanelMenuInitializer")
end

------------------------------

Compat.handlers = {
    ["BrutalHandwork"] = { fun = Compat.BrutalHandwork, isActive = false },
    ["FancyHandwork"] = { fun = Compat.FancyHandwork, isActive = false },
    ["iMeds"] = { fun = Compat.iMeds, isActive = false },
    ["iMedsFixed"] = { fun = Compat.iMeds, isActive = false },
}

function Compat.RunModCompatibility()
    local activatedMods = getActivatedMods()
    for k, modCompatHandler in pairs(Compat.handlers) do
        if activatedMods:contains(k) then
            local ok, err = pcall(modCompatHandler.fun)
            if ok then
                modCompatHandler.isActive = true
                TOC_DEBUG.print("Compat handler active: " .. k)
            else
                print("[TOC+] compat handler for '" .. k .. "' failed (mod probably not ported to B42): " .. tostring(err))
            end
        end
    end
end

Events.OnGameStart.Add(Compat.RunModCompatibility)

return Compat
