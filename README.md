# The Only Cure+ (Field Surgery)

A Build 42 fork of ZioPao's **The Only Cure** for Project Zomboid: staged field surgery with real risk,
a visible infection window, sepsis and convalescence, prostheses that fit the stump and wear out (hands that close
when gripping), one-handed actions done with the hand you have left, leg amputations with crutches and crawling, an
Ash-style chainsaw arm, a Merle-style bayonet arm, crawler zombies and severed limbs as items.

- **Steam Workshop:** https://steamcommunity.com/sharedfiles/filedetails/?id=3818733381
- **Workshop ID:** `3818733381`
- **Mod ID:** `TheOnlyCurePlus`
- **Game:** Build 42.21+, singleplayer and multiplayer
- **Languages:** EN, ES, DE, FR, IT, PL, RU, UA, TR, KO, PTBR

## Reporting a bug

Open an issue with the **Bug report** template and attach your `console.txt`
(`C:\Users\<you>\Zomboid\console.txt`), taken right after the problem happens. For visual problems,
add a screenshot and say which prosthesis and which clothing you were wearing.

## Installing without the Workshop

Copy the `TheOnlyCurePlus` folder into `Zomboid/mods/` and enable **The Only Cure+ (Field Surgery)** in the
Mods menu. Enable only one of The Only Cure / The Only Cure+: they share items and save data, and saves from
the original keep working.

## Repository layout

| Folder | Contents |
|---|---|
| `TheOnlyCurePlus/` | The mod exactly as published (`42/media`: Lua, scripts, models, textures, translations). |
| `tools/` | Python and Blender scripts that generate the models, textures, icons, translations and Workshop images. |

### Tools

The 3D assets are generated, not hand-modelled, so they can be rebuilt and checked:

- `export_fit.py` measures the real cross-sections of the vanilla body; `blender_build.py` builds every
  prosthesis in Blender on top of those sections (`blender -b -P tools/blender_build.py -- out/fit.json out/blender`);
  `blender_to_x.py` writes the skinned `.X` files the game loads.
- `diag_legs.py` checks that no point of a stump pokes through a prosthesis; `diag_winding.py` checks face
  orientation; `check_api.py` checks every Java method the Lua calls against the game's class hierarchy;
  `validate.py` checks scripts, translations and Lua syntax.
- `gen_prosthesis_items.py`, `gen_clothing_xml.py` generate item scripts, clothing XML and the GUID table.
- `i18n/` holds the translation sources and `merge_translations.py`.

The scripts were written for one machine and contain absolute paths (game install, mod folder); adjust
the constants at the top of each file. They need Python 3 with `numpy` and `Pillow`, and Blender 5.x for the
Blender steps. `pzx.py` (the `.X` reader/writer) lives in a sibling project and is imported from its path.

## Credits and license

- Original mod: **ZioPao** and the contributors of [The Only Cure](https://github.com/ZioPao/The-Only-Cure), GPL-3.0.
- Body-location registration: **RabenRabo** (Fantasy Bodyparts / Fantasy Legs), adapted with credit.
- This fork: NEXCONKER.

Licensed under the **GNU GPL v3.0**, same as the original. See `LICENSE`.
