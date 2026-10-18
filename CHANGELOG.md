# Changelog

## 3.3.1

- Fixed (multiplayer): the chainsaw and bayonet attachments kept retrying the equip animation and never worked
  (Workshop report). In Build 42 only the server creates items and equips them (`ISEquipWeaponAction:complete` runs
  there); the mounted weapon was created on the client, so the server never had it. The client now asks the server
  (`ServerItemsCommands.MountWeapon` / `UnmountWeapon`), which checks the worn attachment, creates the weapon, puts it in
  the right hand and calls `sendEquip`.
- Fixed (multiplayer): a mounted attachment did not reach the client (the server set it in `ISWearClothing:complete`
  without `apply()`), so bases counted as having no hand: no grip, no two-handed weapons. `Modular.SetupHead` now
  applies on the server.
- Fixed: if the saved state lost the right-arm base, the chainsaw/bayonet retried every 3 s. The worn base is registered
  again; if that fails it stops retrying for a while.
- Fixed: error with NPC mods (Knox Event Expanded NPC): `SharedIgnoredActions.lua` assumed every character has TOC+ data
  (reported by ShOvEl42).
- New: Merle's bayonet can use one-handed pistols and revolvers. In singleplayer the pistol shows in the left hand
  (`TOC.PistolVisual`, the real gun stays in the right hand with an invisible model) and the blade stays on the right;
  in multiplayer the pistol shows in the right hand. Rifles and shotguns still need a real hand.
- New: interactive Player Guide (`docs/TOCPlus_Guide.pdf`) linked from the Workshop description.

## 3.3.0

- New: modular arm prostheses. An arm prosthesis is now a base (`toc:ArmProst_X`, one model per amputation level) and
  an attachment (`toc:ArmHead_X`) that can be swapped without taking the base off. 5 bases (wooden, scrap, mechanical
  frame, medical, cybernetic) and 7 attachments (wooden knob, hook, mechanical, medical and cybernetic hands, chainsaw,
  bayonet). Stats come from the pair (`StaticData.CombineTier`). Some pairs do not fit: the chainsaw needs a metal base,
  the mechanical and medical hands do not go on wood, the cybernetic hand needs a tier 3 base or better. A base with no
  attachment cannot hold anything ("I need something to hold it with"). Worn 3.2 arms convert into the matching base
  and attachment on first load, keeping their condition.
- New: cybernetic tier (tier 5): frame, hand and leg in a plated sci-fi style, hard to craft (Welding 7, Electrical
  6-7, Mechanics 5-6 and rare electronics). The frame gives +1 Strength while worn (`TOC/Plus/CyberStrength.lua`, one
  point even with two arms, synced with `SyncXp`); the leg has `RunSpeedModifier` 1.1.
- New: prosthesis workbench (`TOC.ProsthesisWorkbench`, Carpentry 3), placeable furniture with its own tiles
  (`TOCPlus_bench.pack`, tiledef 7317) and 3D model, plus a Viewpoint model pack (`media/viewpoint/tocplus_bench`). Its
  window lists bases, attachments and legs, shows the character in 3D and compares stats with icons and bars.
- New: paint prostheses at the workbench with a vanilla paint can and a paintbrush: 10 colours as clothing texture
  choices (bases, attachments and legs); scrape to get the original finish back.
- New: rebuilt peg, mechanical (hollow frame) and medical (thicker fairing) legs; the knee blends with the thigh.
- New: `TOC_Compat.RegisterBase` / `RegisterHead` for third-party prostheses ([API_MODULAR.md](API_MODULAR.md)).
- Fixed: prosthetic hands sized to the character's hands, wrists no longer twist in some animations (also with the
  TombBody add-on), hands no longer curve inwards when gripping.
- Fixed: attacks while crawling never hit (the animation had no `AttackCollisionCheck`).
- Fixed: elbow pads, knee pads, watches and other items could be worn on an amputated limb and floated (Build 42 body
  locations are `base:<id>`; `StaticData.GetAffectedLimb`).
- Fixed: the wear menu offers only the amputated side when the other limb is intact.
- Fixed: a worn prosthetic leg whose saved state was lost is registered again instead of forcing you to crawl.
- TombBody fit add-on 1.1.0: modular arms and the new legs refitted to Tomb's body; female models.

## 3.2.0

- New: the mechanical and medical hands close when gripping (a Workshop request). The palm follows the hand bone,
  the fingers `Bip01_X_Finger1` and the thumb `Bip01_X_Finger0`, like the vanilla hand. Measured in the game's clips,
  `Finger1` always rotates around its own local Y axis (34-77° when gripping), so the knuckles sit exactly on that line
  and the fingers turn on them without leaving the palm; the thumb grows from a ball centred on its pivot. The wrist is
  a ball joint: centred on the real pivot for forearm and upper-arm amputations, next to the cuff for the wrist level.
  Fingers have a relaxed curl, so a grip makes a fist around the handle. Rebuilt in the TombBody add-on too.
- New: no more "ghost hand" (a Workshop report: painkillers taken with the amputated left hand). One-handed actions
  (pills, drinking, smoking, eating, the spoon and plate ones, reading a book, pouring, opening cans and bottles,
  rolling dice, painting) get mirrored animations: `tools/make_mirror_anims.py` mirrors the vanilla clips left/right
  (exactly, from the bind skeleton, with the held item bones swapped) into `media/anims_X/Bob/TOC_Mirror_*` and copies
  their animation nodes with one extra condition, `TOC_NoHandL` / `TOC_NoHandR`. Every sibling node of the same action
  is copied too, so the game's choice between them is unchanged. `TOC/Plus/GhostHand.lua` sets the variable when one
  hand is missing (amputated and without a gripping prosthesis; hooks, the wooden hand and weapon arms do not grip) and
  moves the action's item to the hand that exists. Other players' amputations are read from their worn items, so it
  also works for them in multiplayer.
- New: Merle-style bayonet arm (`TOC.Prost_KnifeArm_R`, right arm only, Welding 2: a knife, scrap metal, leather strips
  and duct tape). A makeshift scrap-metal sleeve with a bayonet in line with the forearm; its own models per amputation
  level (leather bracer, socket and shell, or full arm with elbow hinge), rusty texture. While worn the right hand holds
  `TOC.MountedBlade`, an invisible one-handed knife (stab animations, hunting-knife stats with a bit more reach); the
  arm wears out with use. Text in the 11 languages.

## 3.1.2

- Fixed: amputations made more than an hour after loading did not heal and could not turn septic until the game was
  reloaded (reported by Blakurion). The hourly update removed itself from `EveryHours` when no limb was cut, and only
  loading the character added it back; it now stays registered and does nothing while no limb is cut.
- Fixed: sprinting and running on a crutch, crawling or on a peg leg. The game rewrites the "can't sprint" flag every
  update from the moodles, and TOC+ only set it every 10 frames, so holding the key sprinted in between; it is now set
  every frame.
- Fixed: the saw sound of an amputation could loop forever when the action was removed from the queue without being
  stopped (another mod clearing the queue). A watchdog stops it once no amputation is running. The sounds are now
  named `TOC_Amputation` / `TOC_Cauterization` instead of the generic `Amputation` / `Cauterization`.
- New: improvised tourniquets. Arm (2 strips) or leg (3 strips) from ripped sheets, denim or leather strips, or from a
  belt, plus a stick, twigs, a pencil or a spoon as windlass. Hand-crafted, no recipe to learn, Doctor XP. The surgery
  window's "no tourniquet" warning now says how to make one.
- New sandbox option `HideAmputeeTraits` (off by default): the amputee traits do not appear in character creation.
  Characters that already have them keep them.
- New language: Brazilian Portuguese (PTBR), machine-assisted.
- Fixed: the three stamina sandbox options showed "( )" instead of "(%)" in several languages; written as `%%`, as
  the game does.
- The Workshop description now says it plainly: TOC+ is standalone and must not be enabled with the original The Only
  Cure.

## 3.1.1

- New: optional add-on "The Only Cure+ - TombBody fit" (mod id `TheOnlyCurePlusTombBody`), in the same Workshop item and
  made with Tomb's permission. For Tomb's Player Body: stumps cut from Tomb's body, so hips and shoulders match it,
  textured with the player's own body texture (Tomb's normal, DOLL or NUDE), and every prosthesis rebuilt on Tomb's
  measurements (the body is 2-8 mm slimmer than vanilla; the parts that replace the limb keep the vanilla centre line so
  the elbow hinge and the hand line up). Load it after The Only Cure+ and Tomb's Player Body.
- Fixed: saves did not load with mods that write item references as `base.X` in lower case (reported with Medieval
  Makeshiftery and Vanilla Outfits Expanded). The sound script inherited from the original TOC declared
  `module base`; that created a separate lower-case module, and `ScriptManager.getModule` resolved every `base.X` of
  the other mod there instead of falling back to `Base`, so their items were "not found". It is `module Base` now.
- Fixed: if another body-slot mod rebuilds the "Human" body location group after TOC+ and drops our locations, they
  are added back on `OnGameBoot` / `OnInitWorld` with their "under clothing" relations, instead of leaving TOC+ items
  without a location.
- Fixed: under a prosthesis for a missing hand, a flap of skin poked out between the cuff and the wrist unit. The hand
  stump reached the start of the palm, past the narrow end of the cuff; hand stumps now also have the trimmed
  "with prosthesis" model (cut inside the cuff), like the forearm and upper-arm ones.
- Fixed: walking on a crutch (and crawling) drained stamina per rendered frame, so at 144 FPS a character was tired
  after 7-10 steps and at 60 FPS after ~17 seconds. Stamina now drains per real second while moving: with the defaults,
  tired after about a minute on a crutch and about 40 seconds crawling.
- New sandbox options: `CrutchStaminaDrain` and `CrawlStaminaDrain` (0-300 %, default 100) and
  `AmputeeTraitStaminaDrain` (default 50 %): characters who start with a leg amputee trait already know how to use
  crutches and spend half as much.

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
