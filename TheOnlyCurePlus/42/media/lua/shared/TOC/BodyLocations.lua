--Based on RabenRabo's bodylocation solution from their mod "Fantasy Bodyparts" and "Fantasy Legs" sub-mod.
--Modified by GanydeBielovzki with permission for batch use for the Frockin' Splendor franchise and spin-offs.
--To copy, further modify or otherwise use this code the original creator and the modifier must be credited.
--TOC+: adds the leg locations.

local function copyBodyLocationProperties(oldGroup, oldLocID, newGroup)
	for k = 0, oldGroup:size()-1 do
		local otherLocID = oldGroup:getLocationByIndex(k):getId()
		if oldGroup:isExclusive(oldLocID, otherLocID)
		then
			newGroup:setExclusive(oldLocID, otherLocID)
		end
		if oldGroup:isHideModel(oldLocID, otherLocID)
		then
			newGroup:setHideModel(oldLocID, otherLocID)
		end
		if oldGroup:isAltModel(oldLocID, otherLocID)
		then
			newGroup:setAltModel(oldLocID, otherLocID)
		end
	end
end

local function addBodyLocationsAt(groupName, locationList)
	local results = {}

	-- get list (!!actually a view!!) of all groups and copy to array (BodyLocations.reset() will also clear the view)
	local allGroupsList = BodyLocations.getAllGroups()
	local allGroups = {}
	for i = 0, allGroupsList:size()-1 do
		allGroups[i + 1] = allGroupsList:get(i)
	end

	BodyLocations.reset()

	-- recreate all groups/bodylocations and insert new bodylocations
	for i = 1, #allGroups do
		local oldGroup = allGroups[i]
		local newGroup = BodyLocations.getGroup(oldGroup:getId())

		for j = 0, oldGroup:size()-1 do
			local oldLoc = oldGroup:getLocationByIndex(j)
			local oldLocID = oldLoc:getId()

			for _, locDef in ipairs(locationList) do
				if oldGroup:getId() == groupName then
					local newLocID = type(locDef.name) ~= "string" and locDef.name or
								   ItemBodyLocation.get(ResourceLocation.of(locDef.name))
					local refLocID = type(locDef.reference) ~= "string" and locDef.reference or
								   ResourceLocation.of(locDef.reference)
					if refLocID == oldLocID and locDef.before then
						results[locDef.name] = newGroup:getOrCreateLocation(newLocID)
					end
				end
			end

			newGroup:getOrCreateLocation(oldLocID)

			for _, locDef in ipairs(locationList) do
				if oldGroup:getId() == groupName then
					local newLocID = type(locDef.name) ~= "string" and locDef.name or
								   ItemBodyLocation.get(ResourceLocation.of(locDef.name))
					local refLocID = type(locDef.reference) ~= "string" and locDef.reference or
								   ResourceLocation.of(locDef.reference)
					if refLocID == oldLocID and not locDef.before then
						results[locDef.name] = newGroup:getOrCreateLocation(newLocID)
					end
				end
			end
		end

		for j = 0, oldGroup:size()-1 do
			local oldLocID = oldGroup:getLocationByIndex(j):getId()
			newGroup:setMultiItem(oldLocID, oldGroup:isMultiItem(oldLocID))
			copyBodyLocationProperties(oldGroup, oldLocID, newGroup)
		end
	end

	return results
end

local names = {
    "toc:Arm_L", "toc:Arm_R", "toc:ArmProst_L", "toc:ArmProst_R", "toc:ArmAccessory_L", "toc:ArmAccessory_R",
    "toc:Leg_L", "toc:Leg_R", "toc:LegProst_L", "toc:LegProst_R", "toc:LegAccessory_L", "toc:LegAccessory_R",
}
local defs = {}
for _, n in ipairs(names) do
    table.insert(defs, {name = n, reference = ItemBodyLocation.FULL_TOP, before = false})
end

local results = addBodyLocationsAt("Human", defs)

for _, n in ipairs(names) do
    if results[n] then results[n]:setMultiItem(false) end
end

-- TOC+: bajo pantalones / mangas las prótesis usan su modelo alternativo (m_AltMaleModel: sólo lo que
-- asoma por el bajo o por el puño), igual que el juego hace con las armaduras de pantorrilla y antebrazo.
local function altModels(coveringLocs, prostNames)
    local ok, err = pcall(function()
        local group = BodyLocations.getGroup("Human")
        for _, pn in ipairs(prostNames) do
            local loc = results[pn]
            if loc then
                for _, covering in ipairs(coveringLocs) do
                    if covering then group:setAltModel(covering, loc:getId()) end
                end
            end
        end
    end)
    if not ok then print("TOC+ BodyLocations: setAltModel failed: " .. tostring(err)) end
end
local BL = ItemBodyLocation
-- Sólo ubicaciones cuyas prendas vanilla son MALLA (tela de verdad que tapa la prótesis). Camisas, mallas
-- largas (Legs1), vaqueros ajustados (PantsSkinny) y vestidos largos son sólo textura sobre el cuerpo:
-- con ellas el modelo recortado dejaba el miembro vacío ("brazo invisible con camisa").
altModels({ BL.PANTS, BL.PANTS_EXTRA, BL.BOILERSUIT, BL.FULL_SUIT, BL.FULL_SUIT_HEAD, BL.BATH_ROBE, BL.FULL_ROBE },
          { "toc:LegProst_L", "toc:LegProst_R" })
altModels({ BL.JACKET_SUIT, BL.JACKET, BL.JACKET_DOWN, BL.SWEATER, BL.SWEATER_HAT, BL.JACKET_BULKY, BL.JACKET_HAT, BL.JACKET_HAT_BULKY, BL.BOILERSUIT, BL.FULL_SUIT_HEAD, BL.FULL_SUIT, BL.BATH_ROBE, BL.FULL_ROBE },
          { "toc:ArmProst_L", "toc:ArmProst_R" })
