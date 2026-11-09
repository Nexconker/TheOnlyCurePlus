-- TOC+ 3.3.5 (Workshop, varios: "two cybernetic arms and I still can't use two-handed weapons", "can't use weapons even
-- though I have cybernetic prosthetics"): los datos del mod (base y cabezal de cada brazo) podían dejar de coincidir con
-- lo que el personaje lleva puesto: partidas de antes de 3.3.4 con dos piezas en el mismo lado, multijugador, cambios de
-- versión... Sin el cabezal en los datos la base cuenta como "sin mano". Cada pocos segundos se comparan los datos con lo
-- puesto y se corrigen (como LegMobility hace con las piernas). Sólo el jugador local; en MP las correcciones viajan con
-- los comandos de siempre (RelayProsthesisState / RelayProsthesisHead).

local DataController = require("TOC/Controllers/DataController")
local ProsthesisHandler = require("TOC/Handlers/ProsthesisHandler")
local Modular = require("TOC/Plus/ModularProsthesis")
local CommandsData = require("TOC/CommandsData")
------------------

local ProsthesisResync = {}

---@param player IsoPlayer
function ProsthesisResync.Check(player)
    local dc = DataController.GetReady(player:getUsername())
    if not dc then return end
    for _, side in ipairs({ "L", "R" }) do
        local group = "Top_" .. side
        local base = Modular.GetWornBase(player, side)
        if base and dc:getIsCut("Hand_" .. side) then
            if not dc:getIsProstEquippedGroup(group) or dc:getProstType(group) ~= base:getFullType() then
                ProsthesisHandler.SearchAndSetupProsthesis(player, base, true)
            end
            local head = Modular.GetWornHead(player, side)
            local want = head and head:getFullType() or nil
            if dc:getProstHead(group) ~= want then
                if head then
                    Modular.SetupHead(player, head, true)
                else
                    dc:setProstHead(group, nil)
                    if isClient() then
                        sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayProsthesisHead, {group = group, headType = nil})
                    end
                end
            end
        end
    end
end

if not isServer() then
    local ticks = 0
    Events.OnPlayerUpdate.Add(function(player)
        if not player or not instanceof(player, "IsoPlayer") or not player:isLocalPlayer() then return end
        ticks = ticks + 1
        if ticks % 300 ~= 0 then return end
        local ok, err = pcall(ProsthesisResync.Check, player)
        if not ok then print("[TOC+] ProsthesisResync: " .. tostring(err)) end
    end)
end

return ProsthesisResync
