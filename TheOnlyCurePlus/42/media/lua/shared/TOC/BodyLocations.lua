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

-- TOC+: moved = ubicaciones vanilla que se recrean en otra posición (aparecen en locationList con su nueva referencia)
local function addBodyLocationsAt(groupName, locationList, moved)
	local results = {}
	moved = moved or {}

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

			if not (oldGroup:getId() == groupName and moved[tostring(oldLocID)]) then
				newGroup:getOrCreateLocation(oldLocID)
			end

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

-- TOC+ 3.1.0: POSICIÓN de las ubicaciones. El juego aplica las máscaras de cada prenda a la textura de las que van
-- DEBAJO (ModelInstanceTextureCreator). Antes todo iba tras FULL_TOP, encima de casi toda la ropa: las máscaras de los
-- muñones se comían la pernera de los vaqueros y la manga de las chaquetas, y la prótesis (en modelo "bajo la ropa")
-- quedaba con la espinilla / el antebrazo invisibles. Ahora los muñones van por encima de la ropa PINTADA sobre el
-- cuerpo (camisetas, mallas, calcetines, faldas y vestidos de textura: tienen que quedar enmascaradas o repintarían el
-- miembro que falta) y por debajo de la ropa de MALLA que los cubre (vaqueros, jerséis, chaquetas, monos).
--   piernas: tras LONG_DRESS (la última textura de pierna), y PANTS (malla) se mueve justo detrás de ellas;
--   brazos: tras VEST_TEXTURE (la última textura con manga), antes de JERSEY / SWEATER / JACKET.
-- Si falta alguna referencia (otra versión del juego), todo vuelve a FULL_TOP como antes.
local LEG_NAMES = { "toc:Leg_L", "toc:Leg_R", "toc:LegProst_L", "toc:LegProst_R", "toc:LegAccessory_L", "toc:LegAccessory_R" }
-- 3.3: toc:ArmHead_X (cabezal de la prótesis modular) justo después de la base; sin modelo alternativo bajo la manga
-- (el cabezal asoma siempre por el puño)
local ARM_NAMES = { "toc:Arm_L", "toc:Arm_R", "toc:ArmProst_L", "toc:ArmProst_R", "toc:ArmHead_L", "toc:ArmHead_R", "toc:ArmAccessory_L", "toc:ArmAccessory_R" }
local names = {}
for _, n in ipairs(ARM_NAMES) do table.insert(names, n) end
for _, n in ipairs(LEG_NAMES) do table.insert(names, n) end

local function hasLocation(groupName, loc)
    if not loc then return false end
    local ok, found = pcall(function()
        local g = BodyLocations.getGroup(groupName)
        for k = 0, g:size() - 1 do
            if g:getLocationByIndex(k):getId() == loc then return true end
        end
        return false
    end)
    return ok and found
end

local BLV = ItemBodyLocation
local defs, moved = {}, {}
local legRef = hasLocation("Human", BLV.LONG_DRESS) and hasLocation("Human", BLV.PANTS) and BLV.LONG_DRESS or nil
local armRef = hasLocation("Human", BLV.VEST_TEXTURE) and BLV.VEST_TEXTURE or nil
for _, n in ipairs(LEG_NAMES) do table.insert(defs, {name = n, reference = legRef or BLV.FULL_TOP, before = false}) end
if legRef then
    table.insert(defs, {name = BLV.PANTS, reference = legRef, before = false})
    moved[tostring(BLV.PANTS)] = true
end
for _, n in ipairs(ARM_NAMES) do table.insert(defs, {name = n, reference = armRef or BLV.FULL_TOP, before = false}) end

local results = addBodyLocationsAt("Human", defs, moved)

-- red de seguridad: una ubicación que no se creara dejaría el ítem imposible de vestir
pcall(function()
    local group = BodyLocations.getGroup("Human")
    for _, n in ipairs(names) do
        if not results[n] then
            results[n] = group:getOrCreateLocation(ItemBodyLocation.get(ResourceLocation.of(n)))
            print("TOC+ BodyLocations: " .. n .. " creada al final (no se encontró su referencia)")
        end
    end
    if legRef and not hasLocation("Human", BLV.PANTS) then group:getOrCreateLocation(BLV.PANTS) end
end)

for _, n in ipairs(names) do
    if results[n] then results[n]:setMultiItem(false) end
end

-- TOC+: bajo pantalones / mangas las prótesis usan su modelo alternativo (m_AltMaleModel: sólo lo que
-- asoma por el bajo o por el puño), igual que el juego hace con las armaduras de pantorrilla y antebrazo.
-- Sólo ubicaciones cuyas prendas vanilla son MALLA (tela de verdad que tapa la prótesis). Camisas, mallas
-- largas (Legs1), vaqueros ajustados (PantsSkinny) y vestidos largos son sólo textura sobre el cuerpo:
-- con ellas el modelo recortado dejaba el miembro vacío ("brazo invisible con camisa").
local BL = ItemBodyLocation
local LEG_COVER = { BL.PANTS, BL.PANTS_EXTRA, BL.BOILERSUIT, BL.FULL_SUIT, BL.FULL_SUIT_HEAD, BL.BATH_ROBE, BL.FULL_ROBE }
local ARM_COVER = { BL.JERSEY, BL.JACKET_SUIT, BL.JACKET, BL.JACKET_DOWN, BL.SWEATER, BL.SWEATER_HAT, BL.JACKET_BULKY, BL.JACKET_HAT,
                    BL.JACKET_HAT_BULKY, BL.BOILERSUIT, BL.FULL_SUIT_HEAD, BL.FULL_SUIT, BL.BATH_ROBE, BL.FULL_ROBE }

local function tocId(name) return ItemBodyLocation.get(ResourceLocation.of(name)) end

---Relaciones de modelo alternativo (idempotente: setAltModel no duplica).
local function applyRelations(group)
    for _, side in ipairs({ "L", "R" }) do
        local legProst, armProst = tocId("toc:LegProst_" .. side), tocId("toc:ArmProst_" .. side)
        for _, covering in ipairs(LEG_COVER) do
            if covering and group:getLocation(covering) then group:setAltModel(covering, legProst) end
        end
        for _, covering in ipairs(ARM_COVER) do
            if covering and group:getLocation(covering) then group:setAltModel(covering, armProst) end
        end
        -- 3.1.0: con una prótesis de brazo puesta, el muñón (antebrazo / brazo) usa su modelo alternativo: el brazo
        -- cortado bajo el borde del encaje, sin piel dentro que pueda asomar al moverse (tools/make_arm_stumps.py).
        group:setAltModel(armProst, tocId("toc:Arm_" .. side))
    end
end

---Comprueba que las ubicaciones TOC siguen en el grupo y vuelve a poner las relaciones. Otros mods de ranuras
---(p. ej. Medieval Makeshiftery) recrean el grupo "Human" con BodyLocations.reset(); si alguno lo hace después que
---nosotros sin copiar las ubicaciones existentes, los ítems TOC quedarían sin ubicación y la partida no cargaría.
---Si falta alguna se añade al final (orden antiguo: funciona, sólo cambia qué ropa la tapa).
local function ensureLocations(when)
    local ok, err = pcall(function()
        local group = BodyLocations.getGroup("Human")
        local readded = {}
        for _, n in ipairs(names) do
            local id = tocId(n)
            if not group:getLocation(id) then
                group:getOrCreateLocation(id)
                table.insert(readded, n)
            end
            local loc = group:getLocation(id)
            if loc then loc:setMultiItem(false) end
        end
        applyRelations(group)
        if #readded > 0 then print("TOC+ BodyLocations (" .. when .. "): otro mod borró " .. table.concat(readded, ", ") .. "; añadidas de nuevo") end
    end)
    if not ok then print("TOC+ BodyLocations (" .. when .. "): " .. tostring(err)) end
end

ensureLocations("carga")
if Events then
    if Events.OnGameBoot then Events.OnGameBoot.Add(function() ensureLocations("OnGameBoot") end) end
    if Events.OnInitWorld then Events.OnInitWorld.Add(function() ensureLocations("OnInitWorld") end) end
end
