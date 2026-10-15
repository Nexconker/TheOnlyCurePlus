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
