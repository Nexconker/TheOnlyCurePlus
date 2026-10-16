# Changelog

## 3.1.1

- Fixed: saves did not load with mods that write item references as `base.X` in lower case (reported with Medieval
  Makeshiftery and Vanilla Outfits Expanded). The sound script inherited from the original TOC declared
  `module base`; that created a separate lower-case module, and `ScriptManager.getModule` resolved every `base.X` of
  the other mod there instead of falling back to `Base`, so their items were "not found". It is `module Base` now.
- Fixed: if another body-slot mod rebuilds the "Human" body location group after TOC+ and drops our locations, they
  are added back on `OnGameBoot` / `OnInitWorld` with their "under clothing" relations, instead of leaving TOC+ items
  without a location.

## 3.1.0

- New: Ash-style chainsaw arm (`TOC.Prost_ChainsawArm_R`, right arm only). The vanilla `Chainsaw.X` mesh (no
  item uses it in 42.21) without its handles, bolted to the stump with the bar in line with the forearm; its own
  models for hand amputations (leather bracer with steel splints) and forearm amputations (socket and steel shell).
- While worn, the right hand holds `TOC.MountedChainsaw`, a one-handed weapon with an invisible model, so the left
  hand stays free. Engine started with the pull cord (Mechanics helps), 0.5 L petrol tank in the prosthesis's mod
  data, refuel from any petrol container, noise that draws zombies. Off, it is a heavy club.
- Synthesized engine sounds (`tools/make_chainsaw_sounds.py`); recipe at Welding 5 / Mechanics 4; repairs; icon;
  text in the 10 languages.
- Fixed: console errors with Bandits. Its NPCs (IsoZombie) fire `OnEquipPrimary/Secondary` and `GuardEquip` called
  `isLocalPlayer()` on them; every hook that takes a character now checks `instanceof(x, "IsoPlayer")` first.
- Fixed: glass shards and cuts on an amputated limb came back in multiplayer. The client cleaned them but the server
  sanitizer only cleared bites, so the server pushed the wound back. Both now use `TOC/Plus/CutLimbHeal`. Also
  removed `setBurned(false)`: in Build 42 `setBurned()` takes no argument and rolls a new burn.
- Fixed: a character created with a leg amputee trait could not move. Leg traits now give a crutch, and one leg
  without a crutch crawls instead of freezing in place.
- Fixed: prostheses from recipes and loot are left-side items and could not be worn on a right stump. They now go on
  the amputated side automatically (`ProsthesisHandler.ResolveSide`).
- Fixed: a dark stripe around the shoulder after an arm amputation. The arm mask hides everything from the neck to
  the hand, and the original FBX stumps rebuilt the shoulder with their own mesh and normals. Arm stumps are now cut
  from the vanilla body (`tools/make_arm_stumps.py`): exactly the faces the mask hides, with the body's normals and
  the same body-copy textures as the leg stumps. Women get their own stump textures on arms. Old FBX stumps removed.
- Fixed: zombie arm stumps asked for texture 30+ in a list of 32 entries. Arms now use the 42-entry list of the legs.
- New: above-elbow prostheses (level suffix `Upper`, e.g. `TOC.Prost_NormalArmUpper_L`) for every arm tier and the
  chainsaw arm. Upper-arm socket and elbow hinge on `Bip01_X_UpperArm`, prosthetic forearm on the forearm bone so it
  bends with the animations (`blender_build.build_upper_section`, fit data in `export_fit.upper_arm`).
- Changed: mechanical and medical hands remodelled (hand-shaped palm, thicker fingers, light steel / light polymer)
  and sized like the vanilla hand with fingers (0.13 x 0.079 x 0.054): before they were 30 % shorter and thinner.
- Changed: arm prostheses no longer look bigger than the healthy arm. Shells that replace the limb match its size
  (`ARM_SHELL`), sockets keep 2.5 mm over the skin (`ARM_CL`) with tight subdivision, arm fit rings use a +-7 mm
  band instead of +-14 mm (sockets flared at the elbow and wrist). Measure with `tools/diag_arm_size.py`.
- Fixed: skin showing through arm prostheses. While an arm prosthesis is worn, forearm and upper-arm stumps switch
  to an alternative model cut 5 mm under the socket rim (`setAltModel(toc:ArmProst_X, toc:Arm_X)`), so there is no
  skin inside the socket to poke out in any animation. Hand amputations keep the body forearm (long-sleeve shirts
  are painted on it) and get 1.5 mm more room at the wrist end of the cuff.
- Changed: the hook curves inwards, towards the body (palm side).
- New sandbox options: `SleepingPillAnesthesia` (max share of sleeping pills in the anaesthesia, default 30, was 50)
  and `SelfAmputationHigh` (operate on your own upper arm or thigh, off by default, extra fail and faint risk).
- Fixed: arm prostheses lost most of their socket and shell when the legs were amputated (62 % of the chainsaw arm,
  23-48 % of the others). The game applies the body masks of every clothing item worn above (the leg stumps hide the
  legs) to the textures of the items below, as if they were laid out like the body. Prostheses and tourniquets have
  their own texture atlas, so they now declare `<m_MasksFolder>none</m_MasksFolder>`, like vanilla bags and belts.
- Fixed: a see-through gap at the shoulder seam of arm stumps. The game hides the arm skin texel by texel and the
  stump took a face only if its centre was hidden, so about 20 half-hidden faces were drawn by neither. Stumps now
  take every face with a hidden texel, and the stump textures are transparent where the body still shows (a shirt
  painted on the body stays visible up to the mask edge).
- Fixed: trousers lost the leg from mid-thigh down over a leg stump (and jackets the sleeve and shoulder over an
  arm stump), and a prosthesis under them showed only its foot or hand with nothing above. All TOC locations sat
  after `FULL_TOP`, above almost all clothing, so the stump masks were applied to the clothes. Stumps and
  prostheses now sit above the clothing painted on the body (shirts, long johns, socks, texture skirts and dresses,
  which must stay masked) and below the mesh clothing that covers them: legs after `LONG_DRESS` with vanilla `PANTS`
  moved right after them, arms after `VEST_TEXTURE` (before jerseys, sweaters and jackets). Jerseys now also use
  the "under the sleeve" arm prosthesis model.
- Fixed: the wound on the end of a stump lost 19 % of its disc under any clothing with masks, and 69 % on the left
  leg when both legs were amputated. The wound texture sat in a free UV area partly inside the leg masks; each stump
  cap now maps to a spot inside the hand or foot of its own side, which is only hidden when that limb is covered.
- Changed: amputee trait icons redrawn in the vanilla style (outlined pixel art, shirt or shorts, bandaged stump)
  instead of flat red silhouettes and plain bars (`tools/make_trait_icons.py`).

## 3.0.1

- Fixed: invisible arm or leg when wearing shirts, long johns, skinny jeans or long dresses. Those are body
  textures, not meshes; prostheses are now only trimmed under real clothing meshes (jackets, sweaters,
  trousers, suits).
- Fixed: doctors and nurses did not start with field surgery knowledge (`Knowledge.lua` used a pre-B42 method).
- Fixed: console error when right-clicking a stove or fireplace (cauterize menu).
- Fixed: zombie limb amputations never triggered (Build 42 weapon category check).
- All text translated to the 10 supported languages.

## 3.0.0

First release of the fork: staged field surgery, infection window and diagnosis, sepsis and convalescence,
prosthesis tiers with wear and per-level models, leg amputations with crutches, crawling and above-knee
prostheses, crawler zombies, severed limbs as items, new models and icons, multiplayer hardening.
