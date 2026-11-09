local CommonMethods = require("TOC/CommonMethods")
local CommandsData = require("TOC/CommandsData")
local StaticData = require("TOC/StaticData")
require("TOC/Events")
------------------

---@class Main
local Main = {
    _version = StaticData.PLUS_VERSION
}

-- Mods that only exist for Build 41: their compat handlers are kept but a note goes to the console.
local B41_ONLY = { "FancyHandwork", "BrutalHandwork" }

function Main.Start()
    TOC_DEBUG.print("Starting The Only Cure+ version " .. tostring(Main._version))
    local active = getActivatedMods()
    for _, id in ipairs(B41_ONLY) do
        if active:contains(id) then
            print("[TOC+] WARNING: mod '" .. id .. "' is active but has no Build 42 release; its compatibility layer is best-effort.")
        end
    end
end

function Main.InitializePlayer()
    local function TryToInitialize()
        local pl = getPlayer()
        if not pl then return end
        if pl:getUsername() == "Bob" then return end
        local LocalPlayerController = require("TOC/Controllers/LocalPlayerController")
        -- 3.3.5: personaje recién creado en MP: se piden datos limpios antes de cargarlos (por si el borrado al morir no
        -- llegó al servidor; si no, el nuevo personaje heredaría las amputaciones del anterior)
        if isClient() then
            local fresh = false
            pcall(function() fresh = pl:getHoursSurvived() < 0.05 end)
            if fresh then sendClientCommand(CommandsData.modules.TOC_RELAY, "WipeOwnData", {}) end
        end
        local ok, err = pcall(LocalPlayerController.InitializePlayer, false)
        if not ok then
            print("[TOC+] InitializePlayer error: " .. tostring(err))
        end
        local Knowledge = require("TOC/Plus/Knowledge")
        pcall(Knowledge.GrantProfession, pl)
        Events.OnTick.Remove(TryToInitialize)
    end
    CommonMethods.SafeStartEvent("OnTick", TryToInitialize)
end

---Clean the TOC table for that player, to prevent it from clogging ModData up
---@param player IsoPlayer
function Main.WipeData(player)
    if not player then return end
    local username = player:getUsername()
    TOC_DEBUG.print("Wiping data after death: " .. tostring(username))
    local key = CommandsData.GetKey(username)
    if not isClient() then
        ModData.remove(key)
    else
        ModData.add(key, {})
        sendClientCommand(CommandsData.modules.TOC_RELAY, "WipeOwnData", {})      -- 3.3.5: el servidor lo valida
    end
    -- 3.3.5 (revisión): la caché de manos y piernas del personaje muerto bloqueaba al nuevo hasta que llegaban datos
    pcall(function() require("TOC/Handlers/CachedDataHandler").Setup(username) end)
    local LegMobility = require("TOC/Plus/LegMobility")
    pcall(LegMobility.Reset, player)
end

--* Events *--

Events.OnGameStart.Add(Main.Start)
Events.OnCreatePlayer.Add(Main.InitializePlayer)
Events.OnPlayerDeath.Add(Main.WipeData)
