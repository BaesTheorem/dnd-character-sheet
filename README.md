# Universal D&D 5e Character Sheet

A single, self-contained, **automated** D&D 5e (2014 rules) character sheet that runs in any
web browser with **no install, no server, no internet, and no Adobe**. The whole app — layout,
styling, and automation — lives in one file: `Character Sheet.html`.

## Why a single HTML file?
The most universal runtime on any device (Windows, Mac, Linux, iPhone, Android, ChromeOS) is the
web browser. A self-contained `.html` with inlined CSS + JavaScript depends on nothing external,
works fully offline, and will keep working for years. It replaces MPMB's Adobe-locked automation
with the same kind of live calculation, in a runtime everyone already has.

## Use it
1. Double-click `Character Sheet.html` (opens in your default browser).
2. Fill it in. Everything recalculates live:
   - ability modifiers, proficiency bonus (from level), saving throws,
   - all 18 skills (with **proficiency** and **expertise** toggles), passive perception,
   - initiative, and a "10 + Dex" helper for AC.
3. **Ability scores** — pick a method at the top of the Abilities card:
   - **Manual** — type final scores directly.
   - **Standard Array** — assign 15/14/13/12/10/8, each used once (a `+race` field adds racial bonuses).
   - **Point Buy** — 27-point budget (scores 8–15) with steppers and a live points counter (plus `+race`).
   In Standard Array / Point Buy the final score = base + racial bonus.
3. It **auto-saves to that browser** as you type — reopening the file restores your character.
4. **Portrait** — click the box by the name to upload one (png/jpeg/webp/heic/etc.). The original
   file is stored so you can re-download it at full resolution (↓). HEIC is kept and re-downloadable
   but only previews in Safari. The image is saved under its own key so a large photo can't break
   the rest of autosave (very large images may not persist locally — use Save copy (HTML) to keep them).

## Toolbar
- **Create Character** → guided wizard (Race → Class/Subclass/Level → Background → ability method →
  name) that fills the sheet. Needs sourcebook data loaded (baked into the `(PHB)` build, or imported).
- **Import Sourcebook** → load `phb-data.json` (made by `build-data.py`) to enable creation. This is
  how the content-free shareable app gets PHB data; the imported data is remembered in that browser.
- **Save** → downloads a self-contained copy of the sheet with your character (and portrait) baked
  in. Email / AirDrop / Drive it; opening that copy anywhere shows the character. This is the way to
  move a character between devices (auto-save is per-browser localStorage, not written to the file).
- **Print / PDF** → "Save as PDF". A dense, standardized stylesheet fits a normal character onto
  **one page** (builder UI hidden; text sections render as full-content mirrors; two balanced columns).
- **New** → opens a fresh blank character in a new tab (current one untouched). Each tab gets its own
  storage slot via a `#slot=…` URL hash; the imported sourcebook is shared across slots.

`New` clears the character from the current browser (export first if you want to keep it).

## Scope (v1)
- **Rules:** D&D 5e (2014).
- **Core single page:** identity, abilities, saves, skills, combat stats, attacks, and free-text
  features / proficiencies / equipment.
- **Class-agnostic:** it automates the *rules math*, not a content database. Spells, class features,
  and items are entered as text — so it works for any character.
- **Not yet (v2 ideas):** spellcasting block (slots + prepared spells, auto save DC / attack),
  inventory with weight/currency math, a full background/bio page.

## PHB data (personal use)
`build-data.py` extracts a trimmed D&D 5e **PHB (2014)** subset (races, backgrounds, classes,
feats, weapons/armor, all 361 spells) from a local 5eTools copy into `phb-data.json`, with the
content auto-filling pickers in the sheet. Re-run with `python3 build-data.py`.

This is **copyrighted WotC content** included for personal use under ownership of the book. Owning
the PHB does not grant redistribution rights, so `phb-data.json` and any sheet with the data baked
in are **gitignored and must not be shared/committed**. The clean app (`Character Sheet.html`)
stays content-free and remains freely shareable; the SRD route stays available for a distributable
build.

## Design / longevity rules
Vanilla HTML/CSS/JS only — no frameworks, no build step, no CDN, no web-fetched fonts (uses the
system font stack). Edit it with any text editor. Data model is plain JSON keyed by field id.
