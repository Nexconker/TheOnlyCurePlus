-- TOC+ Messages: one place to show text to a player, from client or server.
local Messages = {}

---@param player IsoPlayer
---@param text string
---@param bad boolean?
function Messages.Say(player, text, bad)
    if not player or not text or text == "" then return end
    if isServer() then
        local CommandsData = require("TOC/CommandsData")
        sendServerCommand(player, CommandsData.modules.TOC_RELAY, CommandsData.client.Relay.ReceivePlusMessage, {text = text, bad = bad})
        return
    end
    if isClient() and not player:isLocalPlayer() then return end
    local ok = pcall(function()
        if bad then HaloTextHelper.addBadText(player, text) else HaloTextHelper.addText(player, text) end
    end)
    if not ok then pcall(function() player:Say(text) end) end
end

---@param player IsoPlayer
---@param limbName string
---@param severity number
---@param cure string? only when the sandbox reveals the outcome
function Messages.SurgeryResult(player, limbName, severity, cure)
    local key = "IGUI_TOC_Surgery_Result_" .. tostring(severity or 0)
    local text = getText(key, getText("ContextMenu_Limb_" .. limbName))
    Messages.Say(player, text, severity and severity > 0)
    if cure then
        local ckey = "IGUI_TOC_Cure_" .. cure
        Messages.Say(player, getText(ckey), cure ~= "cured")
    end
end

return Messages
