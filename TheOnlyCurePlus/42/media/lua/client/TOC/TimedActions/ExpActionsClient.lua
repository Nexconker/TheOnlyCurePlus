local ExpActions = require("TOC/ExpActions")
local CommandsData = require("TOC/CommandsData")

local XP_PER_TICK = 0.01

-- 3.3.4 (Workshop, AlaskanTF: "sends a RelayAddXp command every frame while an amputee loots"): se acumula y se manda
-- como mucho una vez por segundo y por habilidad, en vez de un paquete por fotograma.
local pending = {}
local lastFlush = 0

local function Flush()
    for perkName, xp in pairs(pending) do
        if xp > 0 then
            sendClientCommand(CommandsData.modules.TOC_RELAY, CommandsData.server.Relay.RelayAddXp, {perkName = perkName, xp = xp})
        end
    end
    pending = {}
    lastFlush = getTimestampMs()
end

---Adds TOC XP via relay for client-side actions (MP client only and SP).
---@param action ISBaseTimedAction
local function AddTOCXpRelay(action)
    ExpActions.IterateTOCXp(action, function(_, perkName)
        pending[perkName] = (pending[perkName] or 0) + XP_PER_TICK
    end)
    if getTimestampMs() - lastFlush >= 1000 then Flush() end
end

--* These functions runs on the client, so they needs the relay exception
local og_ISInventoryTransferAction_update = ISInventoryTransferAction.update
---@diagnostic disable-next-line: duplicate-set-field
function ISInventoryTransferAction:update()
    og_ISInventoryTransferAction_update(self)
    AddTOCXpRelay(self)
end

local os_ISGrabItemAction = ISGrabItemAction.update
---@diagnostic disable-next-line: duplicate-set-field
function ISGrabItemAction:update()
    os_ISGrabItemAction(self)
    AddTOCXpRelay(self)
end