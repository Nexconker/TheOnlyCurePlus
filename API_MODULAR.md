# The Only Cure+ — Modular prosthesis API (3.3)

Since 3.3 an arm prosthesis is two worn items: a **base** (socket + frame, one model per amputation level) and an
**attachment** (the "head": hand, hook, blade...) that mounts on it. Other mods can add their own bases and attachments.

## 1. Items

Put the items in the `TOC` module (your mod can add items to it) and follow the naming used by TOC+:

| Piece | Item types | Body location |
|---|---|---|
| Attachment | `TOC.Prost_Head<Name>_L`, `TOC.Prost_Head<Name>_R` | `toc:ArmHead_L` / `toc:ArmHead_R` |
| Base | `TOC.Prost_Base<Name>_L/_R` (forearm), `..Wrist_L/_R` (hand), `..Upper_L/_R` (upper arm) | `toc:ArmProst_L` / `toc:ArmProst_R` |

`<Name>` is letters only and must not end in `Wrist`, `Upper`, `Ankle` or `Thigh`. Copy one of TOC+'s item blocks
(`scripts/TOC_prosthesis_items.txt`, e.g. `Prost_HeadHook_L`) as a template.

## 2. Register the stats (shared Lua)

```lua
-- media/lua/shared/MyMod_TOCHeads.lua
if getActivatedMods():contains("\\TheOnlyCurePlus") then
    require("TOC/Plus/ModularAPI")
    TOC_Modular.RegisterHead("Prost_HeadClaw", {
        hookLike = false,     -- true = cannot hold items (like the hook)
        twoHanded = true,     -- allows two-handed weapons (ignored when hookLike)
        combatMod = 0.98,     -- multiplies the base's combat speed (0.5 - 1.05)
        timeBonus = 1,        -- added to the base's action bonus (0 - 2)
        wearMul = 1.0,        -- multiplies the base's wear per action (0.5 - 3)
        side = nil,           -- "L" / "R" to restrict to one arm
        metalBase = false,    -- needs a metal base (scrap, mechanical, cybernetic)
        minBaseTier = 2,      -- minimum base tier (1 wood ... 5 cybernetic)
        paintable = false,    -- see section 4
    })
    TOC_Modular.RegisterBase("Prost_BaseBone", {
        tier = 2, timeBonus = 1, twoHanded = true, combatMod = 0.92, wearPerAction = 0.6, material = "wood",
    })
end
```

Values are clamped so a single mod cannot make prostheses better than TOC+'s own tier 5. The client compatibility
table exposes the same functions (`TOC_Compat.RegisterHead`, `TOC_Compat.RegisterBase`, `TOC_Compat.CombineProsthesis`).
`TOC_Modular.Combine(baseFullType, headFullType)` returns the combined stats the game uses.

## 3. Models

All bases end at the **standard mount**, so one attachment model fits every base and every amputation level:

- on the forearm axis, at `forearm length + 0.009` (game units) past the elbow joint, i.e. just past the wrist;
- a round flange of radius `0.0175` facing down the arm.

Easiest path: open one of TOC+'s attachment models (`models_X/Prosthesis/headHook_R_M.X` for a rigid one,
`headMechHand_R_M.X` for a hand) and replace the geometry, keeping the skeleton and the mount position.
- Parts rigid to the arm: weight them to `Bip01_X_Forearm`.
- Hands that close on grip: palm on `Bip01_X_Hand`, fingers on `Bip01_X_Finger1`, thumb on `Bip01_X_Finger0`.
- Male and female models (`_M` / `_F`), left and right.

Clothing XML: same as TOC+'s (`clothing/clothingItems/Prost_HeadHook_L.xml`), with `<m_MasksFolder>none</m_MasksFolder>`
and your own GUID in `fileGuidTable.xml`.

## 4. Paint (optional)

TOC+ parts can be painted with vanilla paint cans and a paintbrush. To opt in, set `paintable = true` and give the
clothing XML **11** `textureChoices` in this order: original, black, white, grey, red, orange, yellow, green, blue,
purple, pink. (`tools/make_paint_variants.py` in the TOC+ repo generates them from your atlas.)

## 5. Events

- `OnTOCProsthesisHeadChanged(character, group, headFullType)` — an attachment was mounted (`headFullType`) or removed (`nil`); `group` is `"Top_L"` or `"Top_R"`.
