# R1 — Data Extraction & Performance Audit

Auditor: data-extraction & performance. Read-only review of `Character Sheet.html`
(the in-browser `et*` extractors + `mergeBook` + `compute`/render loop) and `build-data.py`
(the Python mirror). Claims confirmed against the local 5etools data copy and the live
server at `localhost:5050` unless labeled SUSPECTED.

---

## Extraction correctness & coverage gaps

### 1. CRITICAL — Cross-book subclass *additions* are silently dropped (the known limitation, confirmed and worse than "subclasses")
- **File/lines:** HTML `etClasses` `Character Sheet.html:1984-1985` (the `rawFeats` filter) and `mergeBook` `:1983` + `:2256-2269` (`unionSubs`); Python `build-data.py:360-362`.
- **Confirmed shape (real data):** In `class/class-barbarian.json`, SCAG ships:
  - a *new* subclass `Path of the Battlerager` (`source:SCAG`, shortName `Battlerager`) — handled fine; and
  - *additional features* `Elk` and `Tiger` (totem options) carrying `source:"SCAG"` but `subclassSource:"PHB"`, `subclassShortName:"Totem Warrior"`. The Totem Warrior **subclass entry itself exists only in PHB**.
- **The bug, two layers:**
  1. `etClasses` collects `subclassFeature`s with `f.subclassShortName === short && (f.subclassSource||SRC) === SRC`. When SRC=SCAG, the Elk/Tiger features have `subclassSource="PHB" !== "SCAG"`, so they are **filtered out** and never enter SCAG's `subclasses` map. There is no SCAG `subclass` entry for Totem Warrior either, so SCAG contributes *nothing* for Totem Warrior.
  2. Even if they were collected, `mergeBook`'s `unionSubs` dedups by `short` (`:2259`, `shorts.has(s.short)`), so a second "Totem Warrior" payload from another book would be discarded wholesale — it does not merge feature/featChoices arrays into the already-loaded PHB subclass.
- **Net effect:** A user who loads PHB + SCAG and builds a Totem Warrior Barbarian gets only the PHB totems (Bear/Eagle/Wolf); SCAG's Elk and Tiger are missing from `featChoices` and from the feature text. Same class of bug for any book that *extends* an existing subclass (SCAG → several PHB subclasses; XGE invocation/eldritch additions; TCE optional class features attached to existing subclasses).
- **Severity:** High for completeness; the Battlerager (new subclass) path proves the *new*-subclass case works, so this is specifically the *augmentation* case.
- **Fix (concrete):**
  1. In `etClasses`, when scanning `subclassFeature`s for a subclass, match on `(className, subclassShortName)` **regardless of `subclassSource`/`source`** but still gated on the *book being loaded* (i.e. accept any feature whose `source === SRC`, even when its `subclassSource` points at another book). Emit them keyed by `(className, short)` into `subMap` even when no `subclass` entry for that short exists in this book.
  2. In `mergeBook`/`unionSubs`, change the merge from "skip if short already present" to "merge feature lists + featChoices by feature name (overwrite-or-append), union spells/expanded". That makes a second book's additions land on the already-attached subclass.
  - Mirror the same change in `build-data.py:360-362` and the subclass loop. Bump `DATA_VERSION` (both files) so stale stored data is flagged.

### 2. MEDIUM — `featChoices` only keeps options whose per-option feature physically loaded
- **File/lines:** HTML `:1997-1999` (`present = c => c.options.filter(n => rawFeats.some(f => f.name === n))`); Python `build-data.py:378-384` (`present`).
- **Issue:** This is intentional (don't offer an option you have no text for), but it compounds finding #1: because the Elk/Tiger *features* never load when SRC=SCAG, even a corrected chooser would drop them. Once #1 is fixed (features collected cross-source), `present()` will correctly surface them. Flagging because the two must be fixed together.
- **Severity:** Medium (dependent on #1).

### 3. LOW — `expanded`/leveled `additionalSpells` keys of the form `s1`/`s2` collapse to spell level 0
- **File/lines:** HTML `etClasses` `:2002-2008`; Python `build-data.py:386-395`.
- **Confirmed:** Warlock Archfey `additionalSpells[].expanded = {"s1":["faerie fire"], "s2":["calm emotions"]}`. The loop does `l: parseInt(lv,10)||0` (HTML) / `int(lv) if str(lv).isdigit() else 0` (Python). `"s1"` is not a digit → both yield **level 0**. So expanded/always-prepared spells get tagged as cantrips.
- **Impact:** The "expanded spells" reminder lists names correctly (level is only used for the `l` field), and for full-list casters the prepared flag is set by name, so gameplay impact is small — but any UI that buckets these by `l` will misplace them at level 0. The `s`-prefixed key is the *spell level*; strip the leading `s` before parsing.
- **Fix:** `const m = String(lv).match(/\d+/); const l = m ? +m[0] : 0;` in both files.
- **Severity:** Low (cosmetic/bucketing; both files agree so no drift).

### 4. LOW — `additionalSpells` `choose`/filter directives: handling is correct (positive finding)
- **Confirmed against data:** `Elf known {"1":{"_":[{"choose":"level=0|class=Druid"}]}}`, `Kobold known {"_":[{"choose":"level=0|class=Sorcerer","count":1}]}`. `_collectSpellNames` (HTML `:1945-1949`, Python `:333-342`) skips the `choose`/`all` keys and skips `"="`-containing strings, so no `"level=0|class=Druid"` junk leaks into the racial-spell reminder. Working as intended in both.

### 5. LOW — natural armor / alternate speeds / race ability blocks: correct
- **Natural armor** is handled in `compute()` (`NATURAL_ARMOR` table, `:2834-2838`) not in the extractor, so it does not depend on book data — Tortle (fixed 17), Loxodon (12+Con), Lizardfolk (13+Dex) covered. Warforged Integrated Protection (+1) and Draconic/Dragon Hide handled. Fine, but SUSPECTED gap: this is a hardcoded table, so a *newly loaded* race with natural armor (from a book) won't get it — acceptable for a 2014-PHB-centric sheet, worth a code comment.
- **Alternate speeds** `etSpeedExtra`/`_speed_extra` correctly emit fly/swim/climb/burrow, with `true` → walk speed. In sync.
- **Race ability blocks** fixed (`{str:2}`), `choose` (`{choose:{from,count}}`) via `feat_ability`/`etFeatAbility`, and free-assign (`any`) handled. Subrace folding (unnamed → merge into base; named → "Race (Subrace)") matches between files.

### 6. LOW — multiclass `mcReq`/`mcProf` and `skillToolLanguageProficiencies`: in sync, correct
- `etClasses` `:2028-2030` and `build_classes` `:412-415` build `mcReq` from `multiclassing.requirements` and `mcProf` from `proficienciesGained` identically. `prof_block`/`etProfBlock` both route `skillToolLanguageProficiencies` → `other`. Good.

---

## HTML↔Python sync drift

Overall the two are remarkably close — same tag table, same `_clean`/`_titlecase`/`_pretty`, same prof normalization, same monster pipeline. Drifts found:

### D1. MEDIUM — `_chooserOptions` matches on different fields
- **HTML `:1965-1966`** requires `o.type === "refSubclassFeature"` (then reads `o.subclassFeature`) / `o.type === "refOptionalfeature"` (reads `o.optionalfeature`).
- **Python `:233`** ignores `type` and reads `o.get("subclassFeature") or o.get("optionalfeature")` on any dict.
- **Real data** uses `{"type":"refSubclassFeature","subclassFeature":"Bear|..."}`, so for PHB Totem both agree. **Drift risk:** an `options` entry that carries the `subclassFeature` key *without* the matching `type` (or a different type string) would be caught by Python but missed by HTML — producing different `featChoices` between the baked file and a live-loaded book. Align: make HTML read the key regardless of `type` (match Python), or make Python assert the `type` (match HTML). Prefer the Python (key-based) behavior for robustness.

### D2. LOW — class-spell file discovery
- **HTML `fetch5etoolsBook`** finds the spell file via `spells/index.json[srcCode]` (`:2223`) — authoritative.
- **Python `build_class_spells`/`build_spells`** glob/regex-match `spells-{SRC_TAG.lower()}.json` (`:466`, `:645`). For PHB both → `spells-phb.json` (confirmed via index.json). **Drift:** a book whose spell file is named differently from `spells-{code}.json` would be found by HTML (index lookup) but missed by Python (regex). Low impact for core books; align Python to read `spells/index.json` too.

### D3. LOW — subclassFeature aggregation scope
- **HTML** aggregates `classFeature`/`subclassFeature` from **all** `class/*.json` into one `classAll` before `etClasses` (`:2226-2228`) — necessary because features live in per-class files.
- **Python** processes one class file at a time (`build_classes` loops files, `:346-349`), reading `data.get("subclassFeature")` from that same file. Since each class's features live in its own file, this is equivalent in practice. SUSPECTED edge: a feature defined in a *different* file than its class (rare) would be seen by HTML but not Python. Low.

### D4. INFO — `feat_grants`/`etFeatGrants` `anyFromCategory`
- Both count `anyFromCategory.count`. In sync. (No drift; noting because it's an easy place to drift later.)

No drift found in: `etTags`/`render_tags` (identical tag set incl. `@filter` display=p[0], `@h`, `@atk`, `@recharge`), `etText`/`entries_to_text` (list/table/named-entry handling identical), monster pipeline (`etMonsters`/`build_monsters` field-for-field), item extractors (weights/names/containers/attune/magic/packs/tools/toolCats), `damage_resist`, `feat_saves`.

---

## Performance hotspots

### P1. HIGH — `save()` runs a full `collect()` + `JSON.stringify` + synchronous `localStorage.setItem` on **every keystroke**, undebounced
- **File/lines:** `onChange` `:3209` (`save(); compute();`) fires on every `document` `input`/`change` (`:4415-4416`). `save()` `:3132-3141` calls `collect()` `:2979-3017`.
- **Cost per keystroke:** `collect()` walks **all `[data-save]` elements** (`querySelectorAll` + per-element read), plus ~10 `for(i<NINV)` / `for(i<NATTACKS)` / `for(i<NLIMITED)` loops each doing `$()` id lookups, then `JSON.stringify`s the whole character and writes to `localStorage` (synchronous, can block on disk). On a maxed sheet (multiple overflow pages → large NINV/NLIMITED, multiple spell sheets) this is a few-ms hit on **every character typed** in any textarea (e.g. the Features box, backstory).
- **Fix:** Debounce `save()` (e.g. 250–400 ms trailing) — keep an immediate-save on `change`/blur and on structural events (add row, create character), but debounce the high-frequency `input` path. `compute()` can stay synchronous (it's cheaper and drives live totals) or be `requestAnimationFrame`-coalesced.
- **Severity:** High (this is the dominant per-keystroke cost).

### P2. MEDIUM — `compute()` does ~10 full sub-renders every keystroke, several rebuilding `innerHTML`
- **File/lines:** `compute()` tail `:2964-2975` unconditionally calls `updateGenStatus, updateStepStates, updateAsiFlag, updateDecisionsFlag, refreshAtkRows, refreshEquipToggles, refreshEquippedPickers, renderAcItems, renderContainers, refreshLimitedFeatures, renderFeatureCards`.
- **`renderFeatureCards` `:4265-4272`** does `wrap.innerHTML = cards.map(...).join("")` — a **full DOM teardown/rebuild of the Features page** on every keystroke, even when the keystroke was in an unrelated field (e.g. editing HP, or typing in the Features box itself → rebuilds the card list on each character). `featureCards()`/`featureBlocks()` also re-split the whole Features text with regex each call.
- **`refreshLimitedFeatures` `:4276-4296`** calls `featureBlocks()` then for each block calls `lfIndexByName` (`:4274`) which is `O(NLIMITED)` `$()` id lookups — i.e. O(blocks × NLIMITED) DOM reads every keystroke. Plus a `for(i<NINV)` equipped-item scan.
- **`refreshEquippedPickers` + `renderAcItems` + `renderContainers`** also touch/rewrite DOM each call.
- **Severity:** Medium. No O(n²) over *book* data, but O(blocks×rows) DOM churn + full innerHTML rebuilds per keystroke = layout thrash on large sheets.
- **Fix:** Gate the expensive renders on what actually changed. `onChange` already knows `e.target`; pass a hint into `compute()` (or split `compute()` into `computeNumbers()` always + `computeStructure()` only when a structural input changed — armor select, equip checkbox, class/level, Features textarea, inventory rows). At minimum, only call `renderFeatureCards` when the Features textarea (or feature-affecting field) changed, and build a name→row index once for `refreshLimitedFeatures` instead of `lfIndexByName` per block.

### P3. LOW — `findBy` is linear and called inside the per-spell-sheet loop in `compute()`
- **File/lines:** `findBy` `:3307` (`arr.find`); used at `:2948` inside `for(inst<spellSheets)` in `compute()`. With few classes (~13) and few sheets this is negligible, but it is an avoidable linear scan on the hot path. Low; a `Map` by class name (built once when DATA changes) would remove it.

### P4. INFO — `mergeBook` is O(items) per book with `Map` indexes (good); `loadAllBooks` is the real cost
- `mergeBook` (`:2244-2302`) builds `Map`s for each category and overwrites/append — O(n) per category, fine. But `loadAllBooks` (`:2372-2390`) calls `doLoadBook` per book, and **each** `doLoadBook` (`:2339-2341`) does `bakeSourceData()` (full `JSON.stringify(DATA)` into the DOM) + `persistSources()` (another stringify + 2 localStorage writes) + `refreshAfterData()` (the full re-render of every section incl. monster list, wizard, armor, spell sheets, `compute()`). Loading 16 books = 16× full stringify + 16× full re-render. **Fix:** in the loop, defer `bakeSourceData`/`persistSources`/`refreshAfterData` to *after* the loop (do them once at the end), like `reloadAllBooks` already does (`:2366`). Severity Low-Medium depending on how often "Load all" is used.

---

## localStorage & data handling

### L1. MEDIUM — `persistSources` double-serializes and writes the merged DATA every load; `bakeSourceData` adds a third full serialize
- **File/lines:** `persistSources` `:1708-1716` (`JSON.stringify(DATA)` for `SOURCES_KEY` + `JSON.stringify(raw)` for `SOURCES_RAW_KEY`); `bakeSourceData` `:2391` (`JSON.stringify(DATA)` into the `#source-data` `<script>` DOM node). `doLoadBook` calls **both** every load (`:2339-2340`).
- **Issue:** With 16 books loaded, `DATA` (merged, lean) + `raw` (per-book, the bulkier of the two) are each multi-MB. Every single book load re-stringifies the *entire accumulated* DATA and the *entire* raw map, and writes both — that's the O(books²) total-bytes-written behavior of `loadAllBooks` (P4). The split into `SOURCES_KEY` (lean) + `SOURCES_RAW_KEY` (raw) is a sound design (quota failure on the big raw key can't lose the merged copy — see the `finally` that restores `_meta.raw` at `:1713`), but the *frequency* is the problem.
- **Fix:** Coalesce persist to once-per-batch (ties into P4). Optionally store `raw` per-book under separate keys so a single book's update doesn't rewrite the whole raw blob.

### L2. MEDIUM — Quota handling is partial / asymmetric
- **File/lines:** `persistSources` `:1712` wraps the merged-key write in try/catch and returns `false` on failure (surfaced as "too large to save — stays this session" at `:2340`). **But** the raw-key write `:1714` swallows its error silently. And `save()` (the *character* save, `:3135`) wraps the main write in try/catch but **does nothing** on failure (silent) except for the portrait branch.
- **Issue:** If the *raw* per-book data exceeds quota it's dropped with no signal, which then breaks `hasAllRaw()` → book filtering silently degrades into a full re-fetch (`toggleBook` `:1738-1739`). If a large character `save()` fails, the user gets no warning that their edits aren't persisted.
- **Fix:** Report failure on both the raw-key write and the main `save()` write (the latter already has a `flashStatus` path only for portrait — extend it to the main write).

### L3. LOW — `bakeSourceData` keeps a full JSON copy of DATA inside the live DOM
- `#source-data` holds `JSON.stringify(DATA)` (`:2391`) so "Save copy (HTML)" can carry books. This is intentional, but it means a maxed 16-book DATA lives **twice** in memory (object + DOM-text copy) and is re-stringified into the DOM on every load. With the deferral fix (P4) this is acceptable; flagging the memory duplication as something to keep in mind for very large book sets.

### L4. INFO — Version gating is correct
- `init` `:4395-4398`: `srcComplete` + `sameVer` check discards stored data built by an older `dataVersion` in favor of the baked copy. `sourcesAreStale()` (`:1683`) warns when loaded books predate `DATA_VERSION`. This is the right mechanism; just remember to bump `DATA_VERSION` in **both** files when fixing #1/#3 (they're currently both 13, in sync — `build-data.py:26`, HTML `:1209`).

---

## Caches & invalidation

### C1. `_spellIndex` — correct invalidation (positive finding)
- **File/lines:** declared `:2587`, lazily built `:2589`, consumed via `spellData` `:2592`.
- Invalidated at **all three** DATA-mutation points: `rebuildFromRaw` `:1706`, `doLoadBook` after merge `:2338`, `clearLoadedBooks` `:2405`. `mergeBook` itself never leaves a stale index reachable (its only callers null `_spellIndex` afterward: `doLoadBook`, and `rebuildFromRaw`/`reloadAllBooks` which null after). **No stale-cache bug found.**

### C2. SUSPECTED — no cache on `findBy(DATA.classes,…)` / `CASTERS` lookups
- Not a correctness issue, but `findBy` (C/P3) and repeated `(DATA.classes||[])` scans aren't memoized. Since DATA changes rarely (only on book load/filter), a `Map`-by-name cache invalidated alongside `_spellIndex` would remove the linear scans from the `compute()` hot path. Low priority.

### C3. INFO — `featureBlocks()`/`featureCards()` recompute (no cache)
- These re-parse the Features textarea on every `compute()` (P2). They're pure functions of the textarea value; could be memoized on the textarea value, but the bigger win is gating *when* they run (P2). Noting as the cache that doesn't exist but could.

---

## Robustness to malformed/partial book data
- `fetch5etoolsBook` (`:2215-2243`) wraps every fetch in `.catch(()=>({}))`, so a missing `items.json`/`bestiary`/`fluff` degrades gracefully to empty arrays — good. Python mirrors this with `try/except` around optional loads (`:781`, `:648`, `:731`, `:594`).
- Extractors universally guard with `(x||[])`, `typeof === "object"` checks, and `||""` defaults; a feature/subclass/spell missing `name`/`entries` is skipped, not crashed.
- **One gap:** `etClasses` assumes `c.hd` may be absent (`(c.hd||{}).faces` → `undefined` HD) — fine — but `crNum`/`_speed` etc. are solid. No malformed-data crash path found.
