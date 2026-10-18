-- TOC+ 3.3: modelo 3D de la mesa del banco de prótesis para el mod Viewpoint (vista 3D / primera persona). Viewpoint no
-- usa el spriteModels.txt del juego: cada mod registra su "model pack" (media/viewpoint/<pack>.properties + OBJ) con
-- Viewpoint.ModelPacks.register. Sin Viewpoint activo no hace nada. El resultado se escribe en console.txt.

local PACK = "media/viewpoint/tocplus_bench.properties"
local MOD_IDS = { "TheOnlyCurePlus", "TheOnlyCurePlusDev" }
local done = false

local function tryRegister()
    if done then return end
    local VP = rawget(_G, "Viewpoint")
    local MP = VP and VP.ModelPacks
    if not MP or not MP.register then return end
    for _, id in ipairs(MOD_IDS) do
        local active = getActivatedMods and (getActivatedMods():contains(id) or getActivatedMods():contains("\\" .. id))
        if active then
            local ok, res = pcall(MP.register, id, PACK)
            if not (ok and res) then ok, res = pcall(MP.register, PACK, id) end
            print("[TOC+] Viewpoint model pack (" .. id .. "): " .. tostring(ok and res or res))
            done = ok and res == true
            if done then return end
        end
    end
end

tryRegister()
Events.OnGameBoot.Add(tryRegister)
Events.OnGameStart.Add(tryRegister)
