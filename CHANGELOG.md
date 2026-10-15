# Changelog

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
- Changed: mechanical and medical hands remodelled (hand-shaped palm, thicker fingers, light steel / light polymer).
- New sandbox options: `SleepingPillAnesthesia` (max share of sleeping pills in the anaesthesia, default 30, was 50)
  and `SelfAmputationHigh` (operate on your own upper arm or thigh, off by default, extra fail and faint risk).

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
