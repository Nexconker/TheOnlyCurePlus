local StaticData = require("TOC/StaticData")
------------------------

local CommandsData = {}

CommandsData.modules = {
    TOC_DEBUG = "TOC_DEBUG",
    TOC_RELAY = "TOC_RELAY",
    TOC_ITEMS = "TOC_ITEMS"
}

-- Commands sent FROM server TO client (sendServerCommand), handled in ClientRelayCommands.lua
CommandsData.client = {
    Relay = {
        ReceiveDamageDuringAmputation = "ReceiveDamageDuringAmputation",            ---@alias receiveDamageDuringAmputationParams { limbName : string}
        ReceiveExecuteAmputationAction = "ReceiveExecuteAmputationAction",           ---@alias receiveExecuteAmputationActionParams {surgeonNum : number, limbName : string, damagePlayer : boolean}
        FinalizeAmputationAction = "FinalizeAmputationAction",

        --* APPLY *--
        ReceiveApplyFromServer = "ReceiveApplyFromServer",
        ReceiveWearAmputation = "ReceiveWearAmputation",
        ReceiveCache = "ReceiveCache",

        --* TOC+ *--
        ReceiveSurgeryResult = "ReceiveSurgeryResult",          ---@alias receiveSurgeryResultParams {limbName : string, severity : number, died : boolean?}
        ReceivePlusMessage = "ReceivePlusMessage",              ---@alias receivePlusMessageParams {text : string, bad : boolean?}
        ReceiveZombieCrawler = "ReceiveZombieCrawler",          ---@alias receiveZombieCrawlerParams {zombieID : number}

        --* ADMIN ONLY --*
        ReceiveExecuteInitialization = "ReceiveExecuteInitialization",
    }
}

-- Commands sent FROM client TO server (sendClientCommand), handled in ServerRelayCommands.lua
CommandsData.server = {
    Debug = {
        PrintTocData = "PrintTocData",
        PrintAllTocData = "PrintAllTocData"
    },

    Relay = {
        RelayRequestDataController = "RelayRequestDataController",       ---@alias relayRequestDataControllerParams {username : string, isForced : boolean}
        UpdateDataControllerFromClient = "UpdateDataControllerFromClient",

        RelayDamageDuringAmputation = "RelayDamageDuringAmputation",    ---@alias relayDamageDuringAmputationParams {patientNum : number, limbName : string}
        RelayExecuteAmputationAction = "RelayExecuteAmputationAction",  ---@alias relayExecuteAmputationActionParams {patientNum : number, limbName : string}
        SendCache = "SendCache",

        --* PERKS LEVEL UP *--
        RelayAddXp = "RelayAddXp",                                      ---@alias relayAddXpParams {perkName : string, xp : number}

        --* TRAITS *--
        RelayApplyTraitAmputation = "RelayApplyTraitAmputation",         ---@alias relayApplyTraitAmputationParams {limbName : string}

        RelayTriggerBleed = "RelayTriggerBleed",                         ---@alias relayTriggerBleedParams {patientNum : number, limbName : string, bleedingTime : number}

        --* BITE ON CUT LIMB (#279) *--
        RequestSanitizeCutLimb = "RequestSanitizeCutLimb",                 ---@alias requestSanitizeCutLimbParams {limbName : string}

        --* PROSTHESES *--
        RelayProsthesisState = "RelayProsthesisState",                   ---@alias relayProsthesisStateParams {group : string, isEquipped : boolean, prostType : string?}
        RelayProsthesisWear = "RelayProsthesisWear",                     ---@alias relayProsthesisWearParams {group : string, wear : number}

        --* TOC+ SURGERY *--
        RelayExecuteSurgery = "RelayExecuteSurgery",                     ---@alias relayExecuteSurgeryParams {patientNum : number, limbName : string, plan : table}
        RelaySurgeryBotched = "RelaySurgeryBotched",                     ---@alias relaySurgeryBotchedParams {patientNum : number, limbName : string}

        --* TOC+ POST-OP (client computed, server applied to the sender only) *--
        RelayPostOpApply = "RelayPostOpApply",                           ---@alias relayPostOpApplyParams {limbName : string?, woundInfection : number?, pain : number?, sickness : number?, healthDelta : number?, alcohol : number?, sepsis : number?}
        RelayPlusData = "RelayPlusData",                                 ---@alias relayPlusDataParams {plus : table}

        --* TOC+ ZOMBIES *--
        RelayZombieCrawler = "RelayZombieCrawler",                       ---@alias relayZombieCrawlerParams {zombieID : number}

        --* ADMIN ONLY *--
        RelayExecuteInitialization = "RelayExecuteInitialization",       ---@alias relayExecuteInitializationParams {patientNum : number}
        RelayForcedAmputation = "RelayForcedAmputation"                  ---@alias relayForcedAmputationParams {patientNum : number, limbName : string}
    }
}

---Get the correct key for that particular player to be used in the global mod data table
---@param username string
---@return string
function CommandsData.GetKey(username)
    return StaticData.MOD_NAME .. "_" .. username
end

function CommandsData.GetUsername(key)
    return string.sub(key, #StaticData.MOD_NAME + 2, #key)
end

function CommandsData.GetZombieKey()
    return StaticData.MOD_NAME .. "_ZOMBIES"
end

return CommandsData
