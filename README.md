# Universal D&D 5e Character Sheet

A single, self-contained, **automated** D&D 5e (2014 rules) character sheet that runs in any
web browser with **no install, no server, no internet, and no Adobe, while also functioning as a beautiful pen-and-paper sheet**. The whole app — layout, styling, automation, and a full sourcebook library — lives in one file: `index.html` (~14 MB, most of which is the baked reference data).

## Why a single HTML file?
The most universal runtime on any device (Windows, Mac, Linux, iPhone, Android, ChromeOS) is the
web browser. A self-contained `.html` with inlined CSS + JavaScript depends on nothing external,
works fully offline, and will keep working for years. It replaces MPMB's Adobe-locked automation
with the same kind of live calculation, in a runtime everyone already has.

## Use it
Two ways to run it, same file either way:
- **Download a copy and double-click it** — opens in your default browser, works fully offline forever. This is the primary way to use it. Use **Save** (see Toolbar) to keep a copy with your character baked in.
- **Open it on the web** — [`baestheorem.github.io/dnd-character-sheet`](https://baestheorem.github.io/dnd-character-sheet) (handy on a phone). It installs as a home-screen app and works offline after the first load.

Then:
1. Fill it in. Everything recalculates live:
   - ability modifiers, proficiency bonus (from level), saving throws,
   - all 18 skills (with **proficiency** and **expertise** toggles), passive perception,
   - initiative, AC (from the armor you select), hit dice, spell save DC / attack, spell slots,
     carrying capacity / encumbrance, and effective speed.
2. **Ability scores** — the Abilities card shows only the final **score** and **modifier**. Click
   **⚙ Under the hood** (hidden when printing) for everything that feeds them:
   - **Generation method** — **Manual** (type base scores), **Standard Array** (assign 15/14/13/12/10/8,
     each used once), or **Point Buy** (27-point budget, scores 8–15, with a live points counter).
   - **Bonus columns** — separate **ASI**, **Racial**, **Magical**, and **Misc** bonuses per ability,
     plus a **Notes** field. Final score = base + ASI + racial + magical + misc.
   Creating a character auto-fills the Racial column from the chosen race.
3. It **auto-saves to that browser** as you type — reopening the file restores your character. Storage is IndexedDB (character data, portraits, and thumbnails), so a large photo can't blow a storage cap.
4. **Portrait** — click the box by the name to upload one (png/jpeg/webp/heic/etc.); it's shown at a
   fixed size beside the name. Click an uploaded image for a pop-up menu: **Replace / Download original /
   Remove**. The original file is stored so the download is full resolution. HEIC is kept and
   re-downloadable but only previews in Safari.

## iPhone & iPad (iOS)
On iOS, use the web version — it installs as a real offline app:
1. Open [`baestheorem.github.io/dnd-character-sheet`](https://baestheorem.github.io/dnd-character-sheet)
   in **Safari**.
2. Tap **Share** (the square with the up arrow), then **Add to Home Screen** (the sheet shows the same
   tip in a bar at the bottom).
3. Launch it from the new home-screen icon: full screen, no browser chrome, and **fully offline** from
   then on. It updates itself automatically the next time you're online.

Notes for touch:
- The **phone layout** turns on automatically: stacked cards, bigger tap targets, a swipeable page-tab
  strip, and spell properties folded under each spell name.
- There's no double-click or Alt key on touch, so **long-press** a calculated field to pin a manual
  override; long-press, clear, and commit to revert one (see **Manual overrides** below).
- Characters auto-save to the app's own storage **on that device**. iOS keeps the home-screen app's
  storage separate from the Safari tab's, so pick one and stay in it — a character made in the Safari
  tab won't appear in the home-screen app.
- To back up a character (or move it to a computer), use **Save**: it downloads a copy of the sheet
  with the character baked in to your Files app; opening that file in any computer's browser shows
  the character.

## Pages
Tabs at the top switch pages on screen; **printing outputs every page on its own sheet**. Hide any
page you don't want via **Settings → Layout**.
1. **Core** — identity & portrait; abilities (final score + modifier, with a **⚙ Under the hood**
   generator); saving throws; 18 skills (single tri-state proficiency control on screen, both
   checkboxes on print); senses & passive perception; hit dice; and Proficiencies & Languages. The
   combat area holds Proficiency Bonus, Inspiration, a D&D-Beyond-style **HP widget** (Heal/Damage
   buttons, temp HP, death saves), AC / Initiative / Speed, a **Defenses** box (with auto-computed
   resistance/immunity/advantage chips), a **Conditions & Exhaustion** tracker, an **Attacks** table
   (with a calculated *attacks per action* from Extra Attack), a **Limited Features** tracker
   (Feature / Max / Recover / Used), and an **Action Economy** summary.
2. **Inventory** — currency (PP/GP/EP/SP/CP) with coin weight; a continuous, auto-growing item table
   (auto item weights, drag to reorder, nest items into **containers**, live total weight); Strength-based
   carrying capacity (×5/×10/×15/×30 with status); **Armor** (sets your AC, with AC-bonus item pickers)
   beside **Attuned Items**; and Extra Equipment (its own containers + drag-reorder).
3. **Features** — Features & Traits, as an editable card list. Class, subclass, racial, feat, and
   background features all land here on character creation; hand-edits to a generated card survive a
   later rebuild. For Artificers, an **Infuse Item** picker appears (level-gated, hover rules, auto-applied
   weapon/AC/focus bonuses), and an Armorer's **Arcane Armor** card. Also surfaces Ancestral-Weapon
   effects when you carry one.
4. **Spells** — pick a spellcasting class and the sheet tailors itself: cantrips-known and
   spells-known/preparable counts, the visible spell levels, and the slot tracker all scale to your
   class & level (full / half / one-third / Warlock pact). Each row is a dropdown of your class's
   spells; hovering a spell shows its full text, with a **ritual** marker, material components, and
   "at higher levels" scaling. Auto Spell Save DC and attack. Supports subclass casters (Eldritch
   Knight, Arcane Trickster, Way of Shadow monk, …). A "Can Prepare" tracker pins to the corner as you
   scroll, and unprepared spells collapse behind a per-level toggle.
5. **Companions** — animal companions, familiars, summons, and **Wild Shape** forms. Add
   multiple creature blocks, each with a searchable monster stat-block picker (load the Monster Manual
   via Source books, or author a creature in the Homebrew Studio) and a template (Find Familiar,
   Pact of the Chain, Beast Master, Wild Shape, Artificer **Steel Defender** / **Eldritch Cannon** /
   **Homunculus Servant**, …). Each creature's portrait auto-fills from its stat block and makes its
   own paper mini.
6. **Ancestral Weapons** — a dedicated sheet for each Ancestral Weapon you carry (see below): artwork,
   lore, base weapon, rarity, Spirit Points, computed stat chips, and the per-character upgrade point-buy.
7. **Background** — appearance (age/height/weight/eyes/skin/hair) + Personality / Ideals / Bonds /
   Flaws + Allies / Enemies.
8. **Backstory** — a full-page Character Backstory box.
9. **Notes** — a full-page free-text box.
10. **Mini** — print-and-fold paper minis (fold-over standees) built from the character **portrait**
    and every companion portrait: a front panel, an auto-flipped back panel (so it reads upright once
    folded over the top crease), and a cut/fold/glue guide. The page hides itself (and won't print)
    when no portrait exists. Self-contained inlined SVG art. Adapted from the open-source
    [dyslexic-charactersheets](https://github.com/dyslexic-charactersheets) "Map Minis".

## Pen & paper
A fresh sheet (before "Create Character" is used) is completely empty — no scores, no `0`/`+0`
computed values, just blank boxes — and the free-write areas are sized for handwriting. So you can
print a blank copy and fill it in by hand. Fill any value digitally and the math fills itself in.

## Toolbar
The top bar keeps a few direct buttons; the rest live under a **☰ menu**.
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
  move a character between devices (auto-save is per-browser storage, not written to the file).
- **Search** → jump to any field on any page by name.
- **Mobile** → force the phone layout on a desktop (auto-on for narrow screens).
- **☰ menu** → **Manage Characters**, **Homebrew Studio**, **Print / PDF**, and **Settings**.
  - **Manage Characters** — a card view of every character saved in this browser (portrait or name
    initials, class/level, last-edited time). Open one to switch to it in place, or create / rename /
    duplicate / delete. Simulacra nest under the character they were cast from.
  - **Print / PDF** — "Save as PDF". A dense, standardized stylesheet fits a normal character onto
    **one page** (builder UI hidden; text sections render as full-content mirrors; overflow inventory /
    limited features flow onto extra sheets).
  - **Settings** — three sections. **General**: updates, appearance (dark mode, disable animations),
    the welcome guide, clearing manual overrides, and **Export a blank sheet** (a fresh copy with your
    loaded sourcebooks baked in but no characters — good for handing someone a ready-to-use sheet).
    **Character Settings** (saved per character): theme, visible pages, portrait, variant encumbrance,
    **Item filters** (Renaissance / modern / futuristic gear), per-character **Enabled sources**, and
    Tasha's optional rules. **Advanced**: Homebrew summary and **Source books** (see below).

## Themes
Each character can carry its own **theme** — a named look chosen under **Settings → Character Settings → Theme** and saved with that character. Two ship today:
- **Universal Character Sheet** (default) — the app's own flat/sharp look. On screen it's a **landscape dashboard**: a JS layout engine relocates the Core cards into a topbar/rail/skills scaffold with a tabbed centre panel, so everything stays live-calculated. For **printing** it falls back to a clean black-and-white **portrait** sheet (one page per tab), so it prints like paper.
- **Classic (Official 5e Sheet)** — a pixel-for-pixel rebuild of the Wizards of the Coast 2014 fillable PDF: the official page art as the background, with live automated fields positioned over it. Renders the three canon pages (Core, Background, Spells) plus the paper Mini, in the official order, and prints to fit Letter. Light-only (it's a printed sheet).

**Dark mode stays universal.** It lives in **Settings → General → Appearance** as one global toggle and layers on top of the active theme (Classic is light-only). Printing always uses the light look. To add a theme: push an entry to the `THEMES` array in `index.html` and add its CSS block (gated on `body[data-theme="ID"]`).

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
- **Conditions & Exhaustion** — toggle any of the 15 conditions (with paraphrased rules) or set an
  exhaustion level, and the sheet applies the mechanical consequences: speed changes, halved Max HP at
  exhaustion 4+, ±5 passive Perception, and green-advantage / red-disadvantage badges pinned to the
  affected skill, save, initiative, and attack boxes. Feature-granted (dis)advantages (Rage, Gnome
  Cunning, armor Stealth penalties, …) feed the same badges.
- **Senses & Defenses** compute into chips from your race, feats, features, and equipped magic items,
  and update as you (un)equip and (un)attune — no stale hand-written lines.
- Race / background / feat / class **proficiencies** route to the skill checkboxes and the
  Proficiencies box.

## Ancestral Weapons
A built-in point-buy system for a growing legendary weapon (framework by Dungeon Rollers). Build one
from **Homebrew Studio → Items → + Ancestral Weapon**: spend **Spirit Points** (roughly one per
character level) on upgrades across four tiers; rarity scales with points. The result is a homebrew
weapon that gets its own **Ancestral Weapons** page (artwork, lore, computed stats, unlocked abilities)
and **auto-applies** its clean mechanical effects — the +X to hit/damage, extra-damage riders, AC,
spell attack, speed, flight — all gated behind attunement. You can also point the weapon's effects at
your **Unarmed Strike** (a focus instead of something you swing). Spirit Points and the upgrade buy are
**per-character**, so the same source weapon can be tuned differently on each character. The whole
module is a per-character toggle under **Settings → Character Settings → Enabled sources**.

## Homebrew Studio
A built-in authoring UI for homebrew content, organized into named, togglable "source books" you can
export/import as JSON. Author **spells** and **magic items** (AC / spell-attack / save-DC / attunement /
unarmed / granted-spell / limited-use / senses / action effects all auto-apply), **feats**, **races**
(and subraces), **backgrounds**, **subclasses**, and **creatures** — plus **Ancestral Weapons**. Import
also accepts homebrew **classes**. Everything you author gets **first-class mechanical support** on the
sheet, not just inert text, and each source is an independent book you can toggle on/off or share. All
homebrew bakes into the file alongside the sourcebook data, so a saved/shared copy carries it.

## Manual overrides
Every calculated value can be pinned by hand when your table's ruling, a homebrew item, or a variant
rule disagrees with the math. **Double-click** any computed field (ability scores, modifiers,
proficiency bonus, AC, initiative, passive Perception, saves, skills, spell save DC / attack /
prepared count, attack rows, Max HP, hit dice, speed, carrying capacity), type a value, and press
**Enter**. Pinned fields show a small marker and an outline; their tooltip shows the calculated value
so drift stays visible. **Override-as-source:** pinning a *source* value cascades — pin an ability
score and its modifier, saves, skills, AC and attacks all recompute from it; pin the proficiency bonus
and everything that uses it follows. **Alt-click** a pinned field to revert it to calculated, or use
**Settings → General → Manual overrides → Clear all manual overrides** to drop them all. **On a phone or tablet,
long-press** a field to edit it (there's no double-click or Alt key on touch); to revert a pinned field
on touch, long-press it, clear the value, and commit. Overrides are saved with the character and print
as plain values.

## Source books (Settings)
The build ships with the core 2014 sourcebooks already baked in. Sources split into two questions,
in two Settings sections:

**Which sources a character uses — Settings → Character Settings → Enabled sources.** Every loaded
book, homebrew source, and the Ancestral Weapons module gets a checkbox **per character**: uncheck one
to hide its content (races, spells, items, …) from the pickers and the wizard for *this* character
only — every character keeps its own choices. Toggling needs no server: unchecking applies instantly,
and re-checking a book whose data is baked into the file merges its content back in on the spot.

**Loading and managing the books themselves — Settings → Advanced → Source books:**
- **From a book file (no server).** On a sheet with no sourcebooks loaded, a "No sourcebooks loaded"
  banner opens a file picker directly — select one or more downloaded book JSON files and they load in
  a single click. The same files load any time via **Import files…**, merged into whatever's already
  loaded (never replacing it). **Export books as JSON…** produces those per-book files from your own
  loaded library, bundled in a .zip — the way to hand books to someone else.
- **From a local 5etools server** — pick any book or adventure with player content (PHB, XGE, TCE,
  **Monster Manual**, …) and click **Load**, or **Load all books** to import every available
  2014-ruleset book in one pass. The sheet fetches the raw 5etools JSON from your server (default
  `http://localhost:5050`, editable) and processes it **in the browser**. Loading the Monster Manual
  brings in every monster stat block for the **Companions** page. Loading more books **merges** them
  (dedup by name). Works fully offline as long as that local server is running. Only 2014-ruleset books
  are listed — **2024 ("One D&D") content is filtered out on purpose**; this sheet is 2014-only.
- **The loaded-sources list** shows everything loaded in this browser (books, imports, homebrew
  sources); ✕ unloads one for every character. Per-character hiding lives in Enabled sources, above.
- **Clear loaded books** — forgets anything loaded in this browser and reverts to the data baked into
  the file. Your characters aren't affected.

Loaded books are remembered per browser; the toolbar **Save** button bakes them into the downloaded
copy (making the file itself permanent and portable), and **Settings → General → Export a blank
sheet** does the same with no character data.

## Updating
The sheet self-updates without you touching code.
- **On the web / installed app** — a service worker keeps the document fresh (network-first) and a
  stale or broken cache can never strand you; you're never asked to clear anything by hand.
- **A downloaded copy** — an "update available" banner appears when a newer build ships. **Update**
  streams the new build and re-bakes your characters into it (with a real download progress bar). Your
  source data is refreshed **additively**: new/errata content is folded in, and your homebrew, imports,
  and characters are preserved. A build can also flag a **critical update** that keeps resurfacing until
  you take it.

## Scope
- **Rules:** D&D 5e **2014** ruleset only. 2024 ("One D&D") books are filtered out of the book picker
  and blocked from loading on purpose — this sheet is built for the 2014 rules.
- **Guided creation** with sourcebook data, plus live rules-math automation for any character, plus a
  full homebrew authoring layer.

## Roadmap
- **A separate 2024-compliant sheet.** The 2024 ruleset changes enough (backgrounds grant ASIs and a
  feat, weapon mastery, new spell prep, species vs. race, etc.) that it warrants its own sheet rather
  than bolting onto this one.
- In-Studio authoring forms for homebrew classes and monsters (import already handles both).
- Warlock Pact Boon, Arcane Shot, Rune Knight runes; richer natural-weapon and feature-attack coverage.

## Sourcebook data (`build-data.py`)
`build-data.py` is the offline data baker: it extracts a trimmed subset (races, backgrounds, classes +
subclasses, feats, weapons/armor, spells, monster stat blocks) from a local 5eTools copy into
`source-data.json`. The in-browser loader does the same job live from a 5etools server, so you rarely
need to run the CLI. It defaults to the **Player's Handbook (2014)**; pass a 5eTools source code to
extract a different book:

```
python3 build-data.py            # Player's Handbook (2014) — the default
python3 build-data.py XGE        # Xanathar's Guide to Everything
python3 build-data.py MM         # Monster Manual (monster stat blocks for companions)
```

`source-data.json` and any baked-data copies you make with **Save data file** are gitignored as build
artifacts (they carry copyrighted content) so the working tree stays clean.

## Versioning
The app carries **two** version numbers:
- **`APP_SEMVER`** (from the `VERSION` file) — the human-facing SemVer shown in the UI and used to name
  downloads, e.g. `2.133.1`. Hand-curated: MINOR for features, PATCH for fixes and internal changes.
- **`APP_VERSION`** (`v<N>`) — a build id the pre-commit hook auto-bumps every commit; it drives update
  detection and the service-worker cache-bust. Not hand-edited.

`.githooks/pre-commit` stamps both on every commit and bumps the service-worker cache (`CACHE` in
`sw.js`) to match, so each deploy drops the old offline cache and fresh content lands on the next load.
After cloning, activate the hook once:

```
git config core.hooksPath .githooks
```

### Changelog
The welcome guide shows a changelog (the `CHANGELOG` array in `index.html`), expanded after each
update (and it only shows the gap since the version you last saw). When you make a user-facing change,
add its bullet(s) to a `{v:"Unreleased"}` entry at the top of the array; the pre-commit hook rewrites
that tag to this commit's `vN`, so each release's notes carry the right number with no hand-editing.

### Critical updates
For a release that really needs attention (e.g. a data-correctness fix), create a one-line
**`update-note.txt`** in the repo root with the message to show. The pre-commit hook folds it into
`version.json` as `{critical:true, note:"…"}`, and the banner then renders an **Important update**
style, shows the note, and **keeps resurfacing on every load until the user updates**. It's *sticky*:
the note rides every subsequent release until you **delete `update-note.txt`**.

## Design / longevity rules
Vanilla HTML/CSS/JS only — no frameworks, no build step, no CDN, no web-fetched fonts (uses the
system font stack). Edit it with any text editor. Data model is plain JSON keyed by field id. The app
code stays free of copyrighted WotC text — all such content lives only in the baked `#source-data`
block, so the app itself stays clean.
