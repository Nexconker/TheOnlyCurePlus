-- TOC+ 3.1.2: opción de sandbox HideAmputeeTraits (petición del Workshop: "is there a way to remove the traits from
-- character creation?"). Con ella activa, los rasgos de amputado no salen en la creación de personaje. Se engancha a
-- CharacterCreationProfession:isTraitEnabled, que el juego consulta para cada rasgo al llenar las listas (y la lista
-- filtrada es la que usa también el botón de rasgos aleatorios). Los personajes ya creados no cambian.

local function isAmputeeTrait(trait)
    local reg = _TOCRegistries and _TOCRegistries.traits
    if not reg or not trait or not trait.getType then return false end
    local t = trait:getType()
    for _, v in pairs(reg) do
        if v == t then return true end
    end
    return false
end

local function patch()
    if not CharacterCreationProfession or CharacterCreationProfession.TOC_hideTraitsPatched then return end
    local orig = CharacterCreationProfession.isTraitEnabled
    CharacterCreationProfession.isTraitEnabled = function(self, trait)
        if SandboxVars and SandboxVars.TOC and SandboxVars.TOC.HideAmputeeTraits and isAmputeeTrait(trait) then return false end
        if orig then return orig(self, trait) end
        return true
    end
    CharacterCreationProfession.TOC_hideTraitsPatched = true
end

patch()
Events.OnGameBoot.Add(patch)
