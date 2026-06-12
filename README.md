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
   - initiative, AC (from the armor you select), hit dice, spell save DC / attack, spell slots,
     carrying capacity / encumbrance, and effective speed.
3. **Ability scores** — the Abilities card shows only the final **score** and **modifier**. Click
   **⚙ Under the hood** (hidden when printing) for everything that feeds them:
   - **Generation method** — **Manual** (type base scores), **Standard Array** (assign 15/14/13/12/10/8,
     each used once), or **Point Buy** (27-point budget, scores 8–15, with a live points counter).
   - **Bonus columns** — separate **ASI**, **Racial**, **Magical**, and **Misc** bonuses per ability,
     plus a **Notes** field. Final score = base + ASI + racial + magical + misc.
   Creating a character auto-fills the Racial column from the chosen race.
4. It **auto-saves to that browser** as you type — reopening the file restores your character.
5. **Portrait** — click the box by the name to upload one (png/jpeg/webp/heic/etc.); it's shown at a
   fixed size beside the name. Click an uploaded image for a pop-up menu: **Replace / Download original /
   Remove**. The original file is stored so the download is full resolution. HEIC is kept and
   re-downloadable but only previews in Safari. The image is saved under its own key so a large photo
   can't break the rest of autosave (very large images may not persist locally — use Save to keep them).

## Pages
Tabs at the top switch pages on screen; **printing outputs every page on its own sheet**. Hide any
page you don't want via **Settings → Layout**.
1. **Core** — identity & portrait; abilities (final score + modifier, with a **⚙ Under the hood**
   generator); saving throws; 18 skills; senses & passive perception; hit dice; and Proficiencies &
   Languages. The combat area holds Proficiency Bonus, Inspiration, AC / Initiative / Speed / HP /
   Death Saves, a free-form **Resistances / Immunities / Defenses** box, an **Attacks** table (with a
   calculated *attacks per action* from Extra Attack), and a **Limited Features** tracker
   (Feature / Max / Recover / Used).
2. **Inventory** — currency (PP/GP/EP/SP/CP) with coin weight; a 34-row item table (auto item weights,
   drag to reorder, live total weight); Strength-based carrying capacity (×5/×10/×15/×30 with status);
   **Armor** (sets your AC, with AC-bonus item pickers) beside **Attuned Items**; and Equipment Notes.
3. **Features** — Features & Traits. Class, subclass, racial, feat, and background features all land
   here on character creation. For Artificers, an **Infusions** tracker also appears: pick from the
   Artificer Infusions list (level-gated, with hover rules text), tick which are currently infused,
   track Infusions Known / Items Infused / attunement against your level's limits, and Enhanced Defense
   / Enhanced Arcane Focus auto-apply to your AC and spell attack.
4. **Spells** — pick a spellcasting class and the sheet tailors itself: cantrips-known and
   spells-known/preparable counts, the visible spell levels, and the slot tracker all scale to your
   class & level (full / half / one-third / Warlock pact). Each row is a dropdown of your class's
   spells; hovering a spell shows its full text, with a **ritual** marker, material components, and
   "at higher levels" scaling. Auto Spell Save DC and attack. Supports subclass casters (Eldritch
   Knight, Arcane Trickster, Way of Shadow monk).
5. **Companions & Forms** — animal companions, familiars, summons, and **Wild Shape** forms. Add
   multiple creature blocks, each with a searchable monster stat-block picker (load the Monster Manual
   via Source books) and a template (Find Familiar, Pact of the Chain, Beast Master, Wild Shape,
   Artificer **Steel Defender** / **Eldritch Cannon** / **Homunculus Servant**, …). Each creature's
   portrait also makes its own paper mini.
6. **Background** — appearance (age/height/weight/eyes/skin/hair) + Personality / Ideals / Bonds /
   Flaws + Allies / Enemies.
7. **Backstory** — a full-page Character Backstory box.
8. **Notes** — a full-page free-text box.
9. **Mini** — print-and-fold paper minis (fold-over standees) built from the character **portrait**
   and every companion portrait: a front panel, an auto-flipped back panel (so it reads upright once
   folded over the top crease), and a cut/fold/glue guide. The page hides itself (and won't print)
   when no portrait exists. Self-contained inlined SVG art. Adapted from the open-source
   [dyslexic-charactersheets](https://github.com/dyslexic-charactersheets) "Map Minis".

## Pen & paper
A fresh sheet (before "Create Character" is used) is completely empty — no scores, no `0`/`+0`
computed values, just blank boxes — and the free-write areas are sized for handwriting. So you can
print a blank copy and fill it in by hand. Fill any value digitally and the math fills itself in.

## Toolbar
- **Create Character** → guided wizard (Race → Ability Scores → **Class builder** → **class skill
  choices** → **starting equipment or gold** → Background → name) that fills the sheet from the loaded
  sourcebook data: race ability bonuses / speed / senses / damage resistances / languages; class saves,
  hit dice, and spellcasting; **all proficiencies** (skills checked, weapons/armor/tools/languages
  listed); class **and** subclass **features**, plus a subclass's always-prepared spells; **limited-use
  resources** (Rage, Ki, Sorcery Points, Channel Divinity, …) into the Limited Features tracker with
  hover descriptions; and either the class's starting gear (resolved into Inventory, with
  choice/category/pack prompts) or average starting gold. Backgrounds deposit their items + gold too.
  Needs sourcebook data loaded (baked into the build, or loaded via Settings).
  - **Class builder (multiclass).** The Class step is a list of every class in your loaded sources;
    click one to read its full level 1–20 progression (hit die, saves, proficiencies, spellcasting, and
    every feature inline) and **Add** it. Your first class is your **initial class** (full proficiencies
    + starting equipment); add more for **multiclassing**. A second class you don't meet the multiclass
    **prerequisite** for (e.g. Wizard needs Int 13) can't be added, with the requirement shown. Multiclass
    spell slots auto-fill from the **combined** caster level (full = level, half = ÷2, Artificer = ÷2 up,
    Eldritch Knight / Arcane Trickster = ÷3; Warlock pact magic stays its own pool). Secondary classes
    grant only the limited **multiclass proficiencies**, never extra saving throws.
  - **Pending decisions.** The builder lists due/overdue choices — subclass, subclass options
    (e.g. Totem Spirit), ASIs/feats, and spell selection — and lets you resolve subclass/option/ASI
    right there. You can **proceed without** them; anything left unmade keeps alerting on the main sheet
    (a class-decisions banner beside the ASI banner; spell selection points to the Spells page). Click
    the banner to reopen the builder.
- **Save** → downloads a self-contained copy of the sheet with your character (and portrait) baked
  in. Email / AirDrop / Drive it; opening that copy anywhere shows the character. This is the way to
  move a character between devices (auto-save is per-browser localStorage, not written to the file).
- **Print / PDF** → "Save as PDF". A dense, standardized stylesheet fits a normal character onto
  **one page** (builder UI hidden; text sections render as full-content mirrors; two balanced columns).
- **Settings** → page-layout toggles (hide/show any tab) and **Source books** (see below).
- **Manage Characters** → a card view of every character saved in this browser (portrait or name
  initials, class/level, last-edited time). Open one to switch to it in place, or create / rename /
  duplicate / delete. Each character is a storage slot keyed by a `#slot=…` URL hash; optional rules
  and page visibility are per-character, while the loaded sourcebook library is shared across slots.
- **Reset** (red) → after confirmation, clears *this* sheet back to defaults (deletes the character
  and portrait in place). The loaded sourcebook is kept.

## Automation highlights
Beyond character creation, the sheet keeps these live as you edit:
- **Ability Score Improvements & feats** — a flag tracks every ASI you're owed (by class & level,
  including Fighter/Rogue extras and race-granted feats like Variant Human) and won't clear until you
  pick an ASI or a feat for each. Half-feats apply their ability bump, save/skill proficiencies, etc.
- **Attacks** — toggle a weapon's **Atk** box in Inventory to add it to the Attacks table with an
  auto-computed attack bonus and damage; ability substitutions are handled (Monk Martial Arts → Dex,
  Hexblade → Cha, Battle Smith → Int). A calculated *attacks per action* reflects Extra Attack.
- **Spell slots** auto-fill (and lock) for any known single-class caster (full / half / one-third /
  Warlock pact); multiclass and "Other" stay manual and writable.
- Race / background / feat / class **proficiencies** route to the skill checkboxes and the
  Proficiencies box; the **Observant** feat also adds its line to Senses.

## Manual overrides
Every calculated value can be pinned by hand when your table's ruling, a homebrew item, or a variant
rule disagrees with the math. **Double-click** any computed field (ability scores, modifiers,
proficiency bonus, AC, initiative, passive Perception, saves, skills, spell save DC / attack /
prepared count, attack rows, Max HP, hit dice, speed, carrying capacity), type a value, and press
**Enter**. Pinned fields show a small marker and an outline; their tooltip shows the calculated value
so drift stays visible. **Override-as-source:** pinning a *source* value cascades — pin an ability
score and its modifier, saves, skills, AC and attacks all recompute from it; pin the proficiency bonus
and everything that uses it follows. **Alt-click** a pinned field to revert it to calculated, or use
**Settings → Manual overrides → Clear all manual overrides** to drop them all. **On a phone or tablet,
long-press** a field to edit it (there's no double-click or Alt key on touch); to revert a pinned field
on touch, long-press it, clear the value, and commit. Overrides are saved with the character and print
as plain values.

## Source books (Settings)
Open **Settings → Source books** to load D&D content. Two ways:
- **From a local 5etools server** — pick any book (PHB, XGE, TCE, **Monster Manual**, …) and click
  **Load**, or click **Load all books** to import every available 2014-ruleset book in one pass. The
  sheet fetches the raw 5etools JSON from your server (default `http://localhost:5050`, editable) and
  processes it **in the browser** (a JS port of `build-data.py`). Loading the Monster Manual brings in
  every monster stat block for the **Companions & Forms** page. Loading more books **merges** them
  (dedup by name), so you can stack sources. Works fully offline as long as that local server is
  running — nothing is fetched from the internet. Only 2014-ruleset books are listed (2024 books are
  filtered out); already-loaded books drop out of the picker.
- **Loaded sources (filter)** — every loaded book gets a checkbox under **Loaded sources**. Uncheck one
  to **hide its content** (races, classes/subclasses, feats, spells, monsters, …) from the pickers and
  the wizard without unloading it; re-check to bring it back. The sheet keeps each book's processed data
  separately so toggling is instant (the first toggle after opening an older sheet re-fetches once from
  your server to populate that per-book data).
- **Import file…** — load a pre-built `source-data.json` (made by `build-data.py`) when you don't
  want to run a server.
- **Save data file** — a browser can't overwrite the file it's opened from, so this **downloads an
  updated copy** of the sheet (`Character Sheet (Source Data).html`) with **every loaded book baked
  into the file**. Keep it / replace your sheet with it to make the books permanent and portable.
- **Clear loaded books** — forgets anything loaded in this browser and reverts to the data baked into
  the file (use it to re-load a book with refreshed data). Your character isn't affected.
Loaded data is also remembered per browser (localStorage).

## Scope
- **Rules:** D&D 5e **2014** ruleset only. 2024 ("One D&D") books are filtered out of the in-browser
  book picker on purpose — this sheet is built for the 2014 rules.
- **Pages:** Core (abilities/saves/skills/senses/combat/resistances/attacks/limited features/
  proficiencies), Inventory (weight & currency math, carrying capacity, armor, attunement),
  Features, Spells (slots + prepared/known + auto save DC / attack), Companions & Forms, Background,
  Backstory, Notes, and a print-and-fold Mini.
- **Guided creation** with sourcebook data, plus live rules-math automation for any character.

## Roadmap
- **A separate 2024-compliant sheet.** The 2024 ruleset changes enough (backgrounds grant ASIs and a
  feat, weapon mastery, new spell prep, species vs. race, etc.) that it warrants its own sheet rather
  than bolting onto this one. The book picker already classifies 2014 vs 2024, so the 2024 set is ready
  to feed a future sheet.
- TTS / audio readout of a character; richer multiclass spell-slot math.

## Sourcebook data
There are two ways to get content into the sheet (see **Source books** above): load any book live
from a local 5etools server in-browser, or bake a starter file with `build-data.py`, which extracts a
trimmed subset (races, backgrounds, classes + subclasses, feats, weapons/armor, spells, and monster
stat blocks) from a local 5eTools copy into `source-data.json` and bakes it into
`Character Sheet (Source Data).html`. It defaults to the **Player's Handbook (2014)**; pass a 5eTools
source code to extract a different book:

```
python3 build-data.py            # Player's Handbook (2014) — the default
python3 build-data.py XGE        # Xanathar's Guide to Everything
python3 build-data.py MM         # Monster Manual (monster stat blocks for companions)
```

`source-data.json` and the generated baked-data copies (`Character Sheet (Source Data).html`, or
anything you make with **Save data file**) are gitignored as build artifacts so the working tree stays
clean; regenerate them any time with `build-data.py`.

## Versioning
The app stamps itself with a version tied to git history. `APP_VERSION` in `index.html` reads
`v<N> (YYYY-MM-DD)`, where `N` is the commit number. It shows under **Settings -> Update**, and
both the **Save** button and the offline **Update** (download) name their file with it, e.g.
`Character Sheet v170 (2026-06-11).html`, so every backup says which build it came from.

The stamp is written automatically by `.githooks/pre-commit` on every commit, so a change can't ship
without a fresh version. The same hook bumps the service-worker cache (`CACHE` in `sw.js`) to match,
so each deploy drops the old offline cache and fresh content lands on the next load — no "reload
twice." After cloning, activate the hook once:

```
git config core.hooksPath .githooks
```

## Design / longevity rules
Vanilla HTML/CSS/JS only — no frameworks, no build step, no CDN, no web-fetched fonts (uses the
system font stack). Edit it with any text editor. Data model is plain JSON keyed by field id.
