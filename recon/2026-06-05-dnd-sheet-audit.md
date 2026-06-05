# Deep Recon — D&D Character Sheet Audit

**Date:** 2026-06-05 · **Target:** `Character Sheet.html` (~4640 lines) + `build-data.py` (~820) · **Method:** 4 parallel specialist auditors (bugs, code-quality, UX, data/perf), opus.

> [!info] Process
> One round, four read-only specialist agents reading the actual source. ~533k tokens, ~5.5m wall clock. Per-agent reports: `r1-bugs.md`, `r1-code.md`, `r1-ux.md`, `r1-data.md`. Metrics: `_metrics.md`.

## Headline

The system is in good shape: **no dead JS functions** (every `et*`/`apply*`/`render*` helper has a live call site), correct rules math across the board (spell-slot tables, multiclass caster level, PB, AC incl. natural/Draconic/Warforged, carrying capacity, hit dice, prepared/known counts — all verified), the HTML↔Python extractors are **in sync** (both `DATA_VERSION=13`), `_spellIndex` invalidation is correct, and there's no malformed-data crash path. The flat/sharp aesthetic is already enforced globally.

The real opportunities are: one confirmed coverage gap (cross-book subclass content), a cluster of small correctness/feedback bugs (now fixed), a few performance hotspots on the keystroke path, and a set of high-leverage UX polish items.

## Fixed this pass (implemented + verified)

1. **Multiclass primary spell-caster** — anchored the spell sheet by *caster contribution*, not raw class level. A `Cleric 1 / Fighter 5 (Eldritch Knight)` build no longer gets Int (EK) as its spell ability over the Cleric's Wis. (`createCharacter`)
2. **Silent autosave data-loss** — `save()` swallowed a quota failure on the main key then flashed "Saved." Now it surfaces *"Out of browser storage — NOT autosaved. Use Save to download a copy."*
3. **Quantity 0 → phantom weight** — `rowQty` turned an explicit `0` into `1`; now `0` stays `0`.
4. **`loadAllBooks` O(books²) writes** — each book re-baked + re-persisted + re-rendered the whole accumulated DATA (16× full stringify/render). Now merges all, then bakes/persists/renders **once** (`finalizeSourceLoad`).
5. **Save (download copy) had no feedback** — now toasts *"Downloaded …html — a self-contained copy."* (the headline portability feature looked like a no-op).
6. **Wizard "Create" had no confirmation** — now toasts what was created and how many decisions remain.
7. **Escape closes the topmost modal/wizard** — there was no keyboard control of any modal.

## Recommended next wave (ranked)

### CRITICAL — correctness
- **Cross-book subclass augmentations are dropped.** Loading SCAG does not add its Elk/Tiger Totem-Warrior options to PHB's Totem Warrior. Two causes: `etClasses` filters subclass features by `(f.subclassSource||SRC)===SRC` (HTML ~1985, py ~360), and `mergeBook`'s `unionSubs` dedups subclasses by short name (HTML ~2259) so a second book can never *augment* an already-loaded subclass — only add brand-new ones. Fix: emit cross-book feature augmentations keyed `(className, short)` ignoring `subclassSource`; have `mergeBook` *merge* (concat features/spells/expanded, re-run the chooser/`featChoices` detection on the combined set) rather than skip. Mirror in `build-data.py`. This is the one invasive change — worth its own tested pass (verify with PHB+SCAG → Elk/Tiger appear in the Totem Spirit picker).

### HIGH — performance (keystroke path)
- **Undebounced `save()` on every `input`** — `onChange` (~3209) does `collect()` → `JSON.stringify` → synchronous `localStorage.setItem` per keystroke. Debounce ~250ms.
- **`compute()` runs ~10 full sub-renders per keystroke** — incl. `renderFeatureCards` (full `innerHTML` rebuild, ~4265) and `refreshLimitedFeatures` (O(blocks×NLIMITED) DOM lookups, ~4276). Gate these on what actually changed (e.g. only re-render feature cards when the features text changed).

### HIGH — UX
- **Armor → AC is a cross-page chain.** The wizard adds armor as an Inventory row but it isn't equipped, so AC stays unarmored. The "Equipped" box *is* revealed by `refreshEquipToggles`, but the path (Inventory → check Equipped → select under Armor) is non-obvious. **Note:** the user previously asked that armor *selection* stay a manual dropdown step, so the right move is a **nudge**, not auto-select — e.g. an on-Core hint when body armor sits in inventory unequipped/unselected, and/or a wizard equipment-step note. Confirm scope before building.
- **First-run discoverability cliff.** With no data loaded, the only hint is a disabled Create button's tooltip; loading lives three layers deep (Settings → Advanced → Source books). Add an on-sheet banner when no sources are loaded. Same for the **stale-sources** warning — promote it out of the deep sub-tab.
- **Two perpetually-pulsing orange flags** (ASI + decisions) can animate together above the abilities and compete for the same click. Consolidate into one banner (or stack with clear separation) and drop the pulsing `box-shadow` glow — it's the only shadow in an otherwise strictly flat app.
- **No wizard validation** — you can "Create" with no class/name/race and silently get a broken character. Add light guards (or at least confirm-on-empty).
- **Class-builder detail panel is cramped** (460px modal, fixed `170px 1fr`, small scroll box for a 1–20 progression) and **doesn't collapse on mobile** (no `@media` for `.wiz-build`). Widen the wizard modal; stack on narrow screens.
- **Reset confirm** omits the "Save a copy first" guidance the Settings copy promises.

### MEDIUM
- **Accessibility:** 30+ `.lbl` labels have no `for=`/wrapping (0 `for=` in the file) — clicking does nothing, AT can't pair them; no focus trap/return on modals; touch is second-class for Inventory (hover-only delete/equip, mouse-only drag-reorder), which compounds the armor path on tablets.
- **HTML↔Python drift guards.** The extractors mirror each other with no automated parity check; every schema change must be made twice. Two small live drifts: `_chooserOptions` matches `type==="refSubclassFeature"` in HTML vs the `subclassFeature` key regardless of type in Python (~233); `s1`/`s2` expanded-spell level keys both collapse to level 0 (strip the `s` prefix) in both files.
- **`Observant` +5 passive Perception is text-only** — `Alert`'s initiative bonus is applied numerically; `Observant` never adds to computed Passive Perception.
- **localStorage quota handling asymmetric** — the raw-key write (~1714) still swallows failures silently (now fixed for the main key); surface it too.

### LOW — trim & tidy (~70–90 lines removable)
- **9 dead CSS selectors** (`.acitems`, `.build-grid`, `.build-note`, `.col-lvl`, `.gen-control`, `.hood-btn`, `.spell-hidden-note`, `.chip.toggleable`, `.btn.wiz-method`) + a no-op `.combat-top` media query.
- The global `*{border-radius:0!important;box-shadow:none!important}` (line ~503) makes all the base-CSS `border-radius`/`box-shadow`/`--radius`/`--shadow` fragments dead (~35–45 lines) — but it also kills the inventory drag-drop `box-shadow:inset` feedback (~378–379), so that affordance is currently invisible; restore it via a flat outline before trimming.
- Missing helpers: a `serverBase()` (the localhost:5050 resolution is copy-pasted 5×); `ABKEYS` (~3297) duplicates `ABILITIES.map(([k])=>k)` (drift risk).
- Readability decomposition (≈0 net lines): `init()` (~248 lines, 84 inline listeners), `compute()` (~204), `createCharacter()`, `etClasses()`.

## Suspected (verify before acting)
- Legacy ASI/race-feat `source`-tag migration (~3042) may drop/duplicate a Variant-Human racial feat on very old saves.
- `asiCount`/`charLevel` are fragile against *manually typed* class strings where a subclass precedes the level or contains digits.
- `maxSpellLevel` caps visible spell sections by the primary class only, so some multiclass casters' slot grid can show a level the list hides.

> [!info] Verification
> Implemented fixes verified with headless Playwright against the live 5etools server (multiclass primary caster, create toast, Escape-close) and a clean-init JS-error check (`ERR=[]`). No web fact-check pass: this audit's claims are code line-references grounded by direct reading, not external propositions.
