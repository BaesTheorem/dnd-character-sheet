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
3. **Ability scores** — the Abilities card shows only the final **score** and **modifier**. Click
   **⚙ Under the hood** (hidden when printing) for everything that feeds them:
   - **Generation method** — **Manual** (type base scores), **Standard Array** (assign 15/14/13/12/10/8,
     each used once), or **Point Buy** (27-point budget, scores 8–15, with a live points counter).
   - **Bonus columns** — separate **ASI**, **Racial**, **Magical**, and **Misc** bonuses per ability,
     plus a **Notes** field. Final score = base + ASI + racial + magical + misc.
   Creating a character auto-fills the Racial column from the chosen race.
3. It **auto-saves to that browser** as you type — reopening the file restores your character.
4. **Portrait** — click the empty box by the name to upload one (png/jpeg/webp/heic/etc.); it fits
   to the header height. Click an uploaded image for a pop-up menu: **Replace / Download original /
   Remove**. The original file is stored so the download is full resolution. HEIC is kept and
   re-downloadable but only previews in Safari. The image is saved under its own key so a large photo
   can't break the rest of autosave (very large images may not persist locally — use Save to keep them).

## Pages
Tabs at the top switch pages on screen; **printing outputs every page on its own sheet**.
1. **Core** — identity, abilities, saves, skills (left), combat, attacks, a Limited Features
   tracker (Feature / Max / Recover LR·SR·Dawn / Used), and Proficiencies & Languages (right).
2. **Inventory** — currency (PP/GP/EP/SP/CP) with coin weight, an item table with total weight, and
   Strength-based carrying capacity (Encumbered ×5, Heavily ×10, Max Carry ×15, Push/Drag/Lift ×30)
   with a live status, plus an Equipment & Notes box.
3. **Features** — Features & Traits (background features land here).
3b. **Background** — appearance (age/height/weight/eyes/skin/hair) + Personality / Ideals / Bonds / Flaws.
3c. **Backstory** — Character Backstory, Allies & Organizations, Notes.
4. **Spells** — pick a spellcasting class and the spell list adapts along two axes:
   - **Pre-populates the full class list** (Cleric/Druid/Paladin) — every class spell is listed with a
     Prep checkbox; others (Wizard/Bard/Sorcerer/Warlock/Ranger) are blank rows you write into.
   - **Shows a Prep column** for classes that prepare daily (Wizard + the full-list classes); known
     casters (Bard/Sorcerer/Warlock/Ranger) just list their spells (always ready).
   Auto Spell Save DC (8 + prof + mod) and attack bonus, slot totals (1–9), and cantrips. The
   "include spell sheet" checkbox (for non-casters) never prints.
5. **Mini** — auto-builds a print-and-fold paper mini (fold-over standee) from the character
   **portrait**: a front panel, an auto-flipped back panel (so it reads upright once folded over the
   top crease), and a 3-step cut/fold/glue instruction guide. Needs a portrait; the page hides itself
   (and won't print) when there's none, or uncheck "Include paper mini" to skip it. Self-contained —
   the fold-guide and instruction art are inlined SVGs, no internet needed. Adapted from the
   open-source [dyslexic-charactersheets](https://github.com/dyslexic-charactersheets) "Map Minis".

## Pen & paper
A fresh sheet (before "Create Character" is used) is completely empty — no scores, no `0`/`+0`
computed values, just blank boxes — and the free-write areas are sized for handwriting. So you can
print a blank copy and fill it in by hand. Fill any value digitally and the math fills itself in.

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
- **Reset** (red) → after confirmation, clears *this* sheet back to defaults (deletes the character
  and portrait in place). The imported sourcebook is kept.

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
