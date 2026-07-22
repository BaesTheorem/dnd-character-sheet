# Roadmap

The forward-looking work list for the sheet. Shipped work lives in the in-app changelog; deep design notes for bigger items live in `plans/`. Items here are roughly ordered by intent, not commitment.

## Planned

### 3D dice rolling — SHIPPED 2.138.0–2.140.0 (phases A/B/C, 2026-07-22)
All three phases live: roll engine + click wiring + roll log + plain-dice sidebar (2.138.0), 3D physics overlay with instant fallback under Disable animations / reduced motion / no WebGL (2.139.0), materials + color picker (2.140.0). Plan retained at [`plans/3d-dice-rolling.md`](plans/3d-dice-rolling.md) for the architecture notes. Possible follow-ups if asked: orient face digits upright on settle, d100 as paired d10s in 3D, roll-log entries tap-to-reroll. Ships in three phases (roll engine + log first, 3D second, materials third), each leaving the sheet fully working.

### Per-book source loading pipeline (MPMB-style, no server) — consumer shipped 2.132.0
The stripped-file front door is live: an empty `#source-data` shows the sources flag in `mode="load"`, one click opens the native picker, per-book `source-data.json` files merge additively. **Do NOT strip the real `#source-data` until the owner has tested end-to-end and signed off.** Remaining polish once approved:
- Host the 50 per-book JSON files as GitHub Release assets (the community-index equivalent) so recipients of a stripped file have somewhere to download from.
- Decide whether the empty-state flag should also link that download URL.
- 6 adventures have no per-book raw in the shipped bake (Waterdeep DH/DotMM, ToA, IDRotF, WBtW, Kwalish) — they still need a 5etools-server reload to split out.

### Homebrew Studio: authoring forms for classes + monsters
Import already covers all 8 content types (spells/items/feats/races/backgrounds/subclasses/classes/monsters) and creatures gained an in-Studio form in 2.123.0; classes still lack an authoring form (import-only). Full monster combat automation is out of scope (stat blocks are display + Companions-picker only).

### "Recreate existing character" wizard path
Enter final ability scores + max HP directly (for porting a character built elsewhere), parking the unexplained delta in a misc bucket instead of forcing a level-by-level rebuild. Awaiting owner go-ahead.

## Backlog (smaller mechanics)

Empty — file new items here. (The 2026-07-17 audit shipped or retired the prior three: Arcane Archer Arcane Shot + Rune Knight rune pickers with save DCs, subclass limited-use resources, rune passives, and Pact of the Talisman shipped in 2.134.0–2.134.3; the `weaponOptions` item was retired because that field doesn't exist in the 5etools schema and Polearm Master was already handled in `FEATURE_ATTACKS`; the natural-weapons/feature-attack-subclasses item had already shipped — Tabaxi/Lizardfolk/etc. bake with structured `naturalWeapons`, and `FEATURE_ATTACKS` covers Soulknife, Armorer, Path of the Beast and more.)

## Shelved (design done, deliberately not building yet)

### Save-in-place (self-overwriting HTML file)
Feasibility confirmed: the File System Access API (`showSaveFilePicker` + `createWritable()` atomic temp-file swap) works from `file://` in Chrome — the TiddlyWiki saver model. Design when picked up: progressive enhancement (Chromium desktop only; the download flow stays as the fallback), a "Save to this file" item in the ☰ menu, reusing the `btn-savecopy` serializer + `stripTransientChrome`. Constraints: the page cannot auto-obtain a handle to its own file (picker once → cache the handle in the file://-origin IndexedDB; Chrome ~122+ can persist it); sanity-check name/size on `handle.getFile()` before writing; BASE_KEY churn per save is safe (baked roster loads regardless of partition). Playwright can't drive the native picker — verify headed or by mocking the handle. Est. 60–80 lines.
