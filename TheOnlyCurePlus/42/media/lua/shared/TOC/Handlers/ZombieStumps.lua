-- TOC+ ZombieStumps: stump visuals on zombies. Shared so that MP clients (which do not load
-- media/lua/server) can use it from ZombiesAmputation.
local ZombieStumps = {}

---@param zombie IsoZombie
---@return number texture choice index (20..31)
function ZombieStumps.GetTextureIndex(zombie)
    local x = "M_ZedBody01_level1"
    pcall(function() x = zombie:getHumanVisual():getSkinTexture() or x end)
    local matchedIndex = (tonumber(x:match("ZedBody0(%d)")) or 1) - 1
    if matchedIndex < 0 or matchedIndex > 3 then matchedIndex = 0 end
    local level = (tonumber(x:match("%d$")) or 1) - 1
    if level < 0 or level > 2 then level = 0 end
    return 30 + matchedIndex * 3 + level      -- tras 20 masculinas + 10 femeninas (piernas)
end

---@param zombie IsoZombie
---@param amputationFullType string
function ZombieStumps.Spawn(zombie, amputationFullType)
    local texId = ZombieStumps.GetTextureIndex(zombie)
    local ok, err = pcall(function()
        local zombieVisuals = zombie:getItemVisuals()
        local itemVisual = ItemVisual:new()
        itemVisual:setItemType(amputationFullType)
        itemVisual:setTextureChoice(texId)
        if zombieVisuals then zombieVisuals:add(itemVisual) end
        zombie:resetModelNextFrame()
        zombie:getInventory():AddItem(amputationFullType)
    end)
    if not ok then TOC_DEBUG.print("ZombieStumps.Spawn failed: " .. tostring(err)) end
end

return ZombieStumps
