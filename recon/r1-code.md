# r1 — Code Quality / Redundancy / Trim Audit

Scope: `/Users/alexhedtke/Documents/dnd-character-sheet/Character Sheet.html` (4643 lines) and `/Users/alexhedtke/Documents/dnd-character-sheet/build-data.py` (820 lines). Read-only audit. Line numbers are from the source files as read.

Headline: the single biggest maintenance hazard is **not** dead code — the file is remarkably lean for what it does. It is the **full duplication of the entire 5eTools extraction layer** across two languages (the in-browser `et*` / `_mon*` functions vs. build-data.py's `build_*` / `_*` functions). That is ~30 mirrored functions, intentional, currently in sync, but structurally a permanent 2x maintenance tax. Second is a sizable block of **dead CSS** (an entire flat-theme override nullifies every rounded-corner and shadow rule in the file).

---

## Dead/unused code

### CSS classes never applied (verified: 0 references in body HTML or JS templates)
All confirmed by grepping the entire non-`<style>` region (lines 641–4643) for the bare class token.

| Selector | Line(s) | Note |
|---|---|---|
| `.acitems input,.acitems select` / `.acitems td:nth-child(2)` | 404–405 | No element ever gets class `acitems`. Likely renamed to `.ac-items-auto` (which IS used). ~2 lines. |
| `.build-grid` | 116 | Source-data build picker grid; markup uses other classes. ~1 line. |
| `.build-note` / `.build-note b` | 117–118 | `.build-note` is hidden in print (line 529) but never emitted in markup. ~2 lines + remove from the print `display:none` list. |
| `.spelltable .col-lvl` / `.col-lvl input` | 490–491 | The spell table renders `col-prep`, `col-name`, `col-comp`, etc. but never a `col-lvl` cell. Truly dead. ~2 lines. |
| `.gen-control` / `.gen-control select` | 148–149 | No `gen-control` element exists; the array/pointbuy UI is built as `.stepper` / `.hood-row`. ~2 lines. |
| `.hood-btn` / `.hood-btn:hover` | 160–162 | "Under the hood" trigger; the actual control is a different element. ~3 lines. |
| `.chip.toggleable` | 206 | Inspiration chip uses `.stat.toggle-stat` (line 242, used at 736); toggle chips elsewhere use `.chip.on` directly. ~1 line. |
| `.spell-hidden-note` | 426, 428 | Two rules reference it (`display:none` / `.excluded` reveal) but markup never emits the element. The `#page-spells.excluded #spellbody` rule (427) is real; the note element is not. ~2 lines. |
| `.btn.wiz-method.active` | 297 (partial) | The wizard buttons use class `wiz-equip` (used at 1068–69, 4016, 4634), not `wiz-method`. Only `.wiz-equip` half of the combined selector is live; the `.btn.wiz-method.active,` prefix is dead and can be dropped. |

Total dead CSS classes: **~17 lines** removable outright, plus pruning the `.build-note` token from the print hide-list (529).

### Functions
No JS functions are dead. Every `et*`, `_mon*`, `build*`, `apply*`, `render*` helper was grep-verified to have at least one live call site (including the ones that looked suspicious: `applyRaceAbilityOnly` → called from `renderWizStep` 3695; `featInitBonus` → `compute` 2802; `overflowPageUsed` → `applyLayout` 2422; `classMaxSpellLevel` → `maxSpellLevel` 2518; `featureBlocks` → `refreshLimitedFeatures` 4277; `detectWeaponSlots` → `renderEquipSub` 3988). This is a genuinely tight surface — note it as a positive.

### Vestigial / overridden styling (dead because globally clobbered — see CSS section)
~30+ `border-radius:Npx` declarations and the `--radius`/`--shadow` custom properties are computed but never visible — line 503 nullifies them all. Counted under CSS below.

---

## Duplication (incl. HTML ↔ Python mirror assessment)

### THE BIG ONE: HTML `et*` extractors ↔ build-data.py `build_*` — full 2x port
The in-browser sourcebook loader (`fetch5etoolsBook` + ~30 `et*`/`_mon*` helpers, HTML lines ~1751–2243) and build-data.py (~30 `build_*`/`_*` functions, lines 42–765) are **the same extraction logic implemented twice** — once in JS for live "Settings → Source books" loading, once in Python for the offline `build-data.py` baker. The code even labels the relationship ("mirror of build-data.py" appears at HTML 1789, 2070; "must mirror the HTML's DATA_VERSION" at py 27).

Function-for-function parity (HTML name → py name), all confirmed line-by-line equivalent:

| Logic | HTML | build-data.py |
|---|---|---|
| tag markup → text | `etTags` 1751 | `render_tags` 42 |
| entries → text | `etText` 1769 | `entries_to_text` 63 |
| prof list render | `etProfList` 1780 | `render_prof_list` 77 |
| skills parse | `etSkills` 1781 | `skills_from` 207 |
| token prettify | `_pretty` 1795 | `_pretty` 243 |
| clean/titlecase | `_clean`/`_titlecase` 1793–94 | `_clean`/`_titlecase` 220–223 |
| norm prof | `etNormProf` 1801 | `_norm_prof` 248 |
| prof block | `etProfBlock` 1818 | `prof_block` 263 |
| merge prof | `etMergeProf` 1829 | `_merge_prof` 152 |
| feat ability/saves | `etFeatAbility`/`etFeatSaves` 1838/1845 | `feat_ability`/`feat_saves` 275/285 |
| damage resist | `etDamageResist` 1852 | `damage_resist` 294 |
| traits/speed/langs/feats | `etTraits`/`etSpeed`/`etRaceLangs`/`etFeatGrants` 1863–1890 | `_traits`/`_speed`/`race_langs`/`feat_grants` 95–150 |
| chooser options | `_chooserOptions` 1958 | `_chooser_options` 224 |
| races/backgrounds/classes/feats/spells | `etRaces`/`etBackgrounds`/`etClasses`/`etFeats`/`etSpells` | `build_races`/`build_backgrounds`/`build_classes`/`build_feats`/`build_spells` |
| classSpells | `etClassSpells` 2056 | `build_class_spells` 642 |
| entire bestiary block | `_monSize`…`etMonsters` 2072–2104 | `_mon_size`…`build_monsters` 489–620 |
| items / acItems / tools / packs / weights / names / containers / attune / magic / itemText | `etItems`…`etItemText` 2115–2184 | `build_items`…`build_item_text` 439–728 |
| range/duration | `etRange`/`etDuration` 2039–40 | `render_range`/`render_duration` 752–764 |

**Assessment:** The duplication is *necessary* given the design constraints — the browser cannot run Python, and the CLI baker cannot run the browser's `fetch`. They serve genuinely different runtime contexts (live load vs. offline pre-bake). It is *currently accurate and in sync* (both at `DATA_VERSION = 13`, identical edge-case comments, identical field names in output objects — spot-checked races, classes, monsters, all match key-for-key). **But it is a standing maintenance hazard**: every schema tweak must be made in two languages and the `DATA_VERSION` bumped in two places (HTML 1209, py 26), with no automated check that the two outputs match. Recommended mitigations (all within the vanilla constraint):
- Add a tiny parity guard: a comment block or a test that runs build-data.py against a fixture and diffs against what the JS loader produces (could be a one-off dev script, not shipped). Lowest-effort, highest-value.
- At minimum, keep a single "shape changelog" comment (py 27 already does this for v13 — mirror that discipline in the HTML next to `DATA_VERSION`).
- Do NOT try to collapse them into one — that would require a build step, which is out of scope. The duplication is the right call; just make drift detectable.

Severity: **HIGH** (as an ongoing tax / drift risk), but explicitly *not* a "delete one" recommendation.

### `featureBlocks` (4243) vs `featureCards` (4253) — near-duplicate parser
Both split `$("features").value` on `/\n\s*\n+/`, both `.replace(/^Feat:\s*/i,"")`, both find the `". "` / `" ("` cut point — then diverge only in what they return (`{name,text}` for limited-use detection vs `{title,body}` for card rendering). The split + cut-point logic (~6 lines) is duplicated. The 4252 comment explains *why* they're separate, but the shared front half (split, trim, strip "Feat:", locate cut) could be a single `parseFeatureBlocks()` helper returning rich objects that both callers project from. Severity: **LOW**. ~5 lines saveable.

### `server-url` base resolution — 5x copy-paste
`const base = ($("server-url").value || "").trim() || "http://localhost:5050";` appears verbatim at lines **2316, 2329, 2354, 2373, 3608**. Extract `function serverBase(){ return ($("server-url").value||"").trim() || "http://localhost:5050"; }`. Removes 4 duplicated literals and centralizes the default port (currently a magic string repeated 6x total incl. comments). Severity: **LOW–MED** (one place to change the default). ~4 lines + de-magics the port.

### `[[itemsBase,"baseitem"],[itemsData,"item"]]` iteration — 6x
This exact two-collection iteration pattern is repeated in `etItemWeights` (2149), `etItemNames` (2156), `etContainers` (2161), `etAttuneItems` (2166), `etMagicItems` (2172), `etItemText` (2178). Each is a `.forEach` over both collections filtering `it.source === SRC`. A shared `function eachSrcItem(itemsBase,itemsData,SRC,fn)` iterator would collapse the boilerplate. (build-data.py has the identical 6x pattern at 665–713 via `for coll,key in ((items_base,"baseitem"),(items,"item"))`.) Severity: **LOW**. ~6–10 lines across both files.

### `applyAll` legacy-migration ladder (3028–3126)
Heavy with backward-compat branches: legacy `racialVals` (3040), legacy flat `manualSpells` bucketing (3058–3061), legacy `score-*`/`invwt-*`/`hitdice`/`speed`/`spell-include` migrations (3037, 3076, 3079, 3084–3086, 3096). Each branch is individually justified, but collectively this is ~30 lines of one-time migration that will never shrink. Not removable now (old saved sheets still in localStorage), but worth a dated comment so a future cleanup can drop pre-vN migrations. Severity: **LOW** (note only).

---

## Over-complex functions

| Function | Lines | Span | Assessment |
|---|---|---|---|
| `init()` | ~248 | 4390–4638 | **Largest function in the file.** Wires up ~84 `addEventListener` calls inline. Hard to navigate but low-risk; could be decomposed into `wireToolbar()`, `wireInventoryDnd()`, `wirePortrait()`, `wireSettings()`, `wireWizard()` for readability. Severity LOW (it's setup, not logic). |
| `compute()` | ~204 | 2773–2976 | Does everything: ability mods, saves, skills, passive, init, the entire AC engine (2804–2854, the densest sub-block — armor type / natural armor / unarmored defense / magic bonus / warforged), encumbrance + speed penalties (2867–2936), per-sheet spellcasting (2938–2962), then 11 downstream `refresh*`/`render*` calls (2964–2975). The AC block and the encumbrance/speed block are each self-contained enough to extract (`computeAC()`, `computeCarry()`); doing so would cut compute() roughly in half and make each testable. Severity MED. |
| `createCharacter()` | ~92 | 4297–4388 | Long but linear (race → classes → features → spells → equipment → background → ASIs). The class-loop body (4326–4350) nests feature/subclass/spell/limited-feature handling 3 deep. Extracting `applyClassFeatures(w, sInfo, featLines)` would flatten it. Severity LOW–MED. |
| `etClasses()` | ~62 | 1975–2037 | The single densest extractor: subclass grouping + chooser-option detection + featChoices collapsing + additionalSpells (prepared/expanded) + multiclass prof — all in one function with the same logic mirrored in `build_classes` (py 344–428, also the densest there). Inherent complexity; decomposing into `extractSubclass(s)` would help both copies. Severity MED (it's the hardest part to keep the two ports in sync). |
| `renderAsiList()` | ~47 | 1526–1572 | Big template builder with branching for race-feat vs class-ASI vs class-feat slots. Reasonable; the inline IIFE for `lvlPlan` (1528–1534) could be a named helper. Severity LOW. |
| `mergeBook()` | (starts 2244) | 2244–~2303 | Union/dedup of every DATA array + subclass attach. Reasonable for what it does. Severity LOW. |

---

## Repeated patterns / missing helpers

- **`($("classlevel").value || "").toLowerCase()` — 8x** (compute 2830, 2927; weaponAtkAbility 2906; and others). A `classLevelStr()` accessor (lowercased) would dedupe. LOW.
- **`($("race").value || "").toLowerCase()` — 4x** in compute() alone (2833, 2852, plus race AC checks). Compute it once at the top of compute() into a local. LOW.
- **`http://localhost:5050` magic string — 6x.** See server-url dedup above. Should be a single `const DEFAULT_5ET_SERVER`.
- **Two ability-key constants:** `ABILITIES` (1214, array of `[key,name]`) and `ABKEYS` (3297, `["str","dex",...]`). `ABKEYS` is exactly `ABILITIES.map(([k])=>k)` — a redundant second source of truth used 8x (3500, 3501, 3512, 3546, 4100, 4116, 4121–22, 4314). Define `const ABKEYS = ABILITIES.map(([k])=>k);` instead of re-listing the strings. LOW (correctness: two lists could drift).
- **`(m >= 0 ? "+"+m : m)` inline sign formatting** in renderAsiList (1538) re-implements the existing `sgn()` helper (1286). Use `sgn(m)`. Trivial.
- **`finalScore`/`modOf` recomputation:** compute() builds a `mods{}` map (2780) but renderAsiList (1537) and others call `finalScore`/`modOf` again independently. Acceptable (different call contexts), note only.
- **Per-collection item iteration** (the `[[itemsBase,...],[itemsData,...]]` pattern) — see Duplication.

---

## CSS

### HIGH: flat-theme block makes all rounded corners + shadows dead (lines 503–520)
```
*{border-radius:0 !important; box-shadow:none !important}
```
This single universal `!important` rule nullifies **every** `border-radius` and `box-shadow` declaration in the stylesheet. Affected (all dead values, computed but never rendered):
- `--radius:12px` (19) and its 2 uses (`.card` 65, `.asi-flag` 175).
- `--shadow:...` (20) and its 3 uses (`.card` 65, `.mode-btn.active` 126, `.item-results` 392). Note line 524 even sets `--shadow:none` again in print — belt-and-suspenders on an already-dead var.
- ~30+ literal `border-radius:Npx` declarations scattered through the file (8px on `.btn` 48, inputs 84, `.mode-btn` 124, `.ability .mod` 146, `.stepper .step` 152, badges, chips, stats, etc.).
- The `box-shadow:inset ...` drag-drop feedback at `.invtable tr.drop-target td` (378) and `.invtable tr.drop-into td` (379) — these are **also killed** by the `!important` override, so the visual feedback for dragging inventory rows onto containers is currently invisible. (Flagging as a likely *unintended* casualty — the `*{box-shadow:none !important}` is broader than the flat-theme intent, which was about elevation, not drag affordances. Worth confirming with whoever owns the UX before trimming.)

**Trim:** Since flat/sharp is the chosen aesthetic (matches Alex's documented UI taste: square corners, no shadows), the cleanest move is to *delete* `--radius`, `--shadow`, all `border-radius:Npx`/`box-shadow:` declarations, and the now-pointless `*{...!important}` neutralizer — replacing the two drag-feedback insets with a flat alternative (e.g. `outline`/`border` or `background`). Estimated **~35–45 lines** of CSS removable (the override line, the two var defs, the print `--shadow:none`, plus stripping `border-radius`/`box-shadow` fragments from ~30 rules — most are fragments within otherwise-live rules, so this is editing not whole-line deletion). If the team prefers to keep the values "documented," at least delete the dead `.mode-btn.active{box-shadow:var(--shadow)}` (126) and `.item-results{box-shadow:var(--shadow)}` (392) declarations which are pure no-ops.

### Other CSS
- Dead selectors: see Dead-code section (~17 lines).
- `.combat-top` media query at 230 (`@media (max-width:560px){ .combat-top{grid-template-columns:repeat(3,1fr)} }`) restates the default `repeat(3,1fr)` from line 229 — a **no-op media query**. Remove. ~1 line.
- Print box sizing: `width:19px; height:19px` repeated 4x (lines 576, 577, 587, 594) with "match the ability boxes" comments. Could be a shared `.print-box` class applied to `.ability .mod, .score-out, .row .total, .passive .v`, but the current inline approach is readable and print-scoped. LOW / optional.
- Two large embedded base64 SVGs (lines 434, 439: paper-mini standee template + fold instructions, ~16.6KB + ~8.5KB = ~25KB / 2 lines). These are legitimate self-contained assets, NOT dead — keep. Noted only so a future reader doesn't mistake them for cruft.

---

## Trim summary (estimated removable)

| Category | Est. lines | Confidence |
|---|---|---|
| Dead CSS classes (9 selectors) | ~17 | HIGH (grep-verified 0 refs) |
| Dead rounded-corner / shadow CSS (incl. `--radius`/`--shadow` + override) | ~35–45 | HIGH (universal override proves they're invisible); pending UX sign-off on drag-feedback insets |
| No-op `.combat-top` media query | ~1 | HIGH |
| `serverBase()` helper (dedupe 5 copies + magic port) | ~4 net | HIGH |
| `ABKEYS` → derive from `ABILITIES` | ~0 net (correctness win) | HIGH |
| `featureBlocks`/`featureCards` shared front-half | ~5 | MED |
| `eachSrcItem` iterator (HTML + py, 6 sites each) | ~6–10 | MED |
| `compute()` / `createCharacter()` / `etClasses()` decomposition | ~0 net (readability, not line count) | MED |
| **Net deletable** | **~70–90 lines of CSS+JS** | — |

The HTML↔Python mirror (~600 lines of duplicated extraction logic across both files) is the dominant *conceptual* redundancy but is **not** recommended for deletion — it's an intentional, in-sync, dual-runtime port. The actionable ask there is drift *detection*, not removal.
