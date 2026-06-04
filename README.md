# Universal D&D 5e Character Sheet

A single, self-contained, **automated** D&D 5e (2014 rules) character sheet that runs in any
web browser with **no install, no server, no internet, and no Adobe, while also functioning as a beautiful pen-and-paper sheet**. The whole app — layout,
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
- **Create Character** → guided wizard (Race → Class/Subclass/Level → **class skill choices** →
  **starting equipment or gold** → Background → ability method → name) that fills the sheet: race
  bonuses/speed/senses, class saves/hit dice/spell list, chosen skill proficiencies, and either the
  class's starting gear (into Equipment Notes) or average starting gold (into Currency). Needs
  sourcebook data loaded (baked into the build, or loaded via Settings).
- **Save** → downloads a self-contained copy of the sheet with your character (and portrait) baked
  in. Email / AirDrop / Drive it; opening that copy anywhere shows the character. This is the way to
  move a character between devices (auto-save is per-browser localStorage, not written to the file).
- **Print / PDF** → "Save as PDF". A dense, standardized stylesheet fits a normal character onto
  **one page** (builder UI hidden; text sections render as full-content mirrors; two balanced columns).
- **Settings** → page-layout toggles (hide/show any tab) and **Source books** (see below).
- **New** → opens a fresh blank character in a new tab (current one untouched). Each tab gets its own
  storage slot via a `#slot=…` URL hash; the loaded sourcebook is shared across slots.
- **Reset** (red) → after confirmation, clears *this* sheet back to defaults (deletes the character
  and portrait in place). The loaded sourcebook is kept.

## Source books (Settings)
Open **Settings → Source books** to load D&D content. Two ways:
- **From a local 5etools server** — pick any book (PHB, XGE, TCE, …) and click **Load**. The sheet
  fetches the raw 5etools JSON from your server (default `http://localhost:5050`, editable) and
  processes it **in the browser** (a JS port of `build-data.py`). Loading more books **merges** them
  (dedup by name), so you can stack sources. Works fully offline as long as that local server is
  running — nothing is fetched from the internet.
- **Import file…** — load a pre-built `source-data.json` (made by `build-data.py`) when you don't
  want to run a server.
- **Save data file** — a browser can't overwrite the file it's opened from, so this **downloads an
  updated copy** of the sheet (`Character Sheet (Source Data).html`) with **every loaded book baked
  into the file**. Keep it / replace your sheet with it to make the books permanent and portable.
Loaded data is also remembered per browser (localStorage). It is **copyrighted WotC content for
personal use** — it lives only in your browser / your own file and is never committed; the shipped
app stays content-free.

`New` clears the character from the current browser (export first if you want to keep it).

## Scope
- **Rules:** D&D 5e **2014** ruleset only. 2024 ("One D&D") books are filtered out of the in-browser
  book picker on purpose — this sheet is built for the 2014 rules.
- **Pages:** identity, abilities, saves, skills, combat, attacks, limited-features tracker,
  proficiencies, inventory (weight/currency math + carrying capacity), features, background, backstory,
  notes, spellcasting (slots + prepared/known + auto save DC / attack), and a print-and-fold mini.
- **Guided creation** with sourcebook data, plus live rules-math automation for any character.

## Roadmap
- **A separate 2024-compliant sheet.** The 2024 ruleset changes enough (backgrounds grant ASIs and a
  feat, weapon mastery, new spell prep, species vs. race, etc.) that it warrants its own sheet rather
  than bolting onto this one. The book picker already classifies 2014 vs 2024, so the 2024 set is ready
  to feed a future sheet.
- TTS / audio readout of a character; richer multiclass spell-slot math.

## Sourcebook data (personal use)
There are two ways to get content into the sheet (see **Source books** above): load any book live
from a local 5etools server in-browser, or bake a starter file with `build-data.py`, which extracts a
trimmed subset (races, backgrounds, classes, feats, weapons/armor, spells) from a local 5eTools copy
into `source-data.json` and bakes it into `Character Sheet (Source Data).html`. It defaults to the
**Player's Handbook (2014)**; pass a 5eTools source code to extract a different book:

```
python3 build-data.py            # Player's Handbook (2014) — the default
python3 build-data.py XGE        # Xanathar's Guide to Everything
```

This is **copyrighted WotC content** included for personal use under ownership of the books. Owning a
book does not grant redistribution rights, so `source-data.json` and any sheet with data baked in
(`Character Sheet (Source Data).html`, or anything you make with **Save data file**) are
**gitignored and must not be shared/committed**. The clean app (`Character Sheet.html`) stays
content-free and remains freely shareable.

## Design / longevity rules
Vanilla HTML/CSS/JS only — no frameworks, no build step, no CDN, no web-fetched fonts (uses the
system font stack). Edit it with any text editor. Data model is plain JSON keyed by field id.
