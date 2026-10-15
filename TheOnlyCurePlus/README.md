# The Only Cure+ (Field Surgery) — Build 42

Fork of **The Only Cure** by ZioPao (GPL-3.0). Enable **only one** of the two mods: they share the item
module `TOC`, the save data and the Lua paths, so a save made with the original keeps working after
switching to TOC+ (legs, sepsis and the rest get added on first load).

## What changed

**Surgery is a procedure, not a progress bar.** Right-click a saw (or a body part in the health panel)
and a checklist opens: tourniquet, disinfectant, anaesthesia (painkillers, alcohol or sleeping pills
already in the patient), a blade for the incision, the bone tool, needle and thread, bandage. Each
missing step raises the risk. The window shows the estimated risk only if the surgeon has First Aid 3+
or has read the **Field Amputation Guide** (doctors and nurses know it from the start).

- Tools matter: bone saw / surgery kit < saw < garden or small saw < hatchet, machete, cleaver.
- Without anaesthesia the patient screams (configurable radius, zombies come) and may faint.
  Fainting while operating on yourself leaves the limb half cut: deep wound, bleeding, no amputation.
- Outcome rolled on the server: clean, rough (longer healing, dirty wound) or botched (heavy bleeding).
- The severed limb drops on the floor and rots.

**The infection window is visible.** Sandbox `Cure window` (default 20 %) and `Late gamble window`
(default 40 %): between both the cure is a worsening gamble. Symptoms (chills, sweat, fever) appear as
the infection advances. **Examine wound** on a bite or scratch gives a fallible opinion that improves
with First Aid and with time.

**After the surgery:** shock for a day, convalescence for days (hunger, fatigue, slower actions),
phantom pain, and **sepsis** if the stump stays dirty: it becomes a vanilla wound infection with fever,
treated with antibiotics and by cleaning the stump with alcohol, wipes, disinfectant or spirits.
A missing hand without prosthesis reduces carry weight.

**Prostheses adapt to the stump:** the same item is modelled for a missing hand or a missing forearm, and for a missing foot, calf or whole leg (thigh socket with an articulated knee). **Prostheses have tiers and wear out:** wooden arm (Carpentry 2) < hook (Welding 2) < mechanical arm
(Welding 4) < medical arm (hospital loot). Hooks cannot hold two-handed weapons or long guns. Repair
with wood glue, duct tape, welding rods or screws; a prosthesis at condition 0 falls off.

**Legs.** Foot, lower leg and thigh can be amputated (stumps for both sexes). A survivor missing a leg
cannot move without a **crutch** in hand (walk only, stamina drains) or a prosthetic leg: **peg leg**
(Carpentry 3, no sprint), **mechanical leg** (Welding 4) or **medical leg** (loot). Nothing fits on a
thigh amputation. Leg tourniquets exist.

**Zombies** lose the limb you hit (axes and long blades, sandbox); a zombie that loses a leg becomes a
crawler.

**Fixes over the original:** amputee traits for both sides and legs, equip guard for hotbar / belt
shortcuts, cauterising at any lit fire (stove, fireplace, barbecue, campfire), stump cleaning consumes
the bandage, health panel works in single player, stump item re-worn if it ever disappears, right
upper-arm hairy textures, endurance no longer set to a nonsense value after surgery.

## Multiplayer

All body changes are applied by the server; clients only request them. Every relay command validates
its arguments and only acts on the sender or on a patient standing next to it. Admin commands check
the role. Fancy Handwork and Brutal Handwork have no Build 42 release: their compatibility layer is kept
but guarded, and a warning is printed if they are active.

## Credits and licence

Original mod, models, textures and architecture: ZioPao and contributors (see CREDITS.md). GPL-3.0.
