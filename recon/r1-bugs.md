# R1 — Bug & Correctness Audit (Character Sheet.html + build-data.py)

Scope: traced the JS in `Character Sheet.html` (compute, spell-slots, multiclass, ASI, persistence, parsing) and cross-checked against `build-data.py`. File line numbers refer to `Character Sheet.html` unless noted.

---

## Confirmed bugs (severity-ordered)

### HIGH — `refreshSpellSlots` mis-detects single-class with a multi-word class name as multiclass
- **File/lines:** 2569 (`refreshSpellSlots`), compare with 4322–4324.
- **Bug:** The "is this a multiclass?" test counts matches of `/[A-Za-z'’][A-Za-z'’\- ]*?\s+\d+/g` in the `#classlevel` string and treats `>1` as multiclass. This regex is *non-greedy on a single token* and will also fire on a number that appears inside the parenthetical, but more importantly it does not distinguish a real second class from stray digits. More concretely, the multi-detection and `multiclassCasterLevel()` only credit slots for the recognized PHB caster classes — but the slot *class dropdown* (`spellclass`) for sheet 0 is set in `createCharacter` to the class with the highest raw `w.level` (line 4322–4323), NOT the highest caster level.
- **Scenario:** Build `Cleric 1, Fighter 5 (Eldritch Knight)`. `primary` is chosen by `w.level` → Fighter(EK) at level 5 beats Cleric at level 1, so sheet 0's Spellcasting Class is set to "Fighter (Eldritch Knight)" and the spell ability to **Int**, even though the Cleric (Wis) is the stronger/primary caster. The combined slots from `mcSlots()` are correct, but the DC/attack ability and pre-filled list are wrong for the build.
- **Fix:** Select `primary` by *caster contribution* (full=level, half=floor/2, third=floor/3, with a tiebreak preferring full casters), not by raw class level. Or let the user pick which class anchors sheet 0.

### MEDIUM — Medium-armor Dex cap uses `Math.min` against a possibly-null Dex
- **File/lines:** 2826.
- **Bug:** `dexAdd = (mods.dex == null) ? null : Math.min(mods.dex, 2)` is fine, but at line 2843 `acBase = (needDex && mods.dex == null) ? null : base + (needDex ? dexAdd : 0)`. For medium armor with a *defined* Dex this is correct; the guard is only on `mods.dex == null`. This is actually handled. **Reclassified to non-bug after tracing** — see "false-positive checks" note below. (Kept here to record it was verified.)

### MEDIUM — `save()` skips the "Saved" status and silently continues after a portrait-quota failure
- **File/lines:** 3132–3141.
- **Bug:** The main character JSON is written first (line 3135) inside a `try/catch` that **swallows quota errors silently** — if the *main* `localStorage.setItem(KEY, …)` throws (quota exceeded), the user gets no warning at all and believes the sheet is saved. Only the *portrait* failure surfaces a message.
- **Scenario:** A large sheet (many loaded books baked, big features text) pushes the slot's main key over quota. `setItem` throws, the empty `catch(e){}` eats it, then the portrait save succeeds and `flashStatus("Saved")` runs — the user sees "Saved" but the character was NOT persisted. Next reload loses recent edits.
- **Fix:** In the first `try/catch`, on failure call `flashStatus("Couldn't autosave — storage full; use Save copy (HTML)")` (and ideally `return`), rather than silently continuing.

### MEDIUM — `rowQty` treats quantity 0 as 1 for weight
- **File/lines:** 3729 (`rowQty`), used at 2878.
- **Bug:** `return qv === "" ? 1 : (num(qv,1) || 1)`. A user who sets qty `0` gets `num("0",1)=0`, then `0 || 1 = 1`. So an item explicitly set to quantity 0 is counted as 1 for carried weight.
- **Scenario:** Set an item's qty to 0 (e.g. "0 spare arrows") → it still adds one unit-weight to carried total.
- **Fix:** `const n = num(qv,1); return qv === "" ? 1 : (n < 0 ? 0 : n);` (allow an explicit 0).

### LOW — Observant's +5 passive Perception/Investigation is text-only, not added to the Passive Perception number
- **File/lines:** 1480 (`FEAT_SENSES.Observant`), 2792–2800 (`compute` passive calc).
- **Bug:** Alert's initiative bonus IS applied numerically (`featInitBonus()` at 2802), but Observant's +5 to passive Perception is only emitted as a Senses *text line*. The computed `Passive Perception` value (line 2800) never adds it.
- **Scenario:** Character with Observant shows passive Perception 10+WIS+prof, missing the +5 the feat grants.
- **Fix:** Add an Observant check to the passive computation (parallel to `featInitBonus`), e.g. `+ (hasFeat("Observant") ? 5 : 0)`.

---

## Suspected issues (need verification)

### SUSPECTED HIGH — ASI/race-feat slot migration can duplicate or drop a racial feat on legacy loads
- **File/lines:** 3042–3046 (`applyAll`), 1432–1441 (`syncAsiSlots`).
- **Concern:** On restore, every saved `asiChoices` entry without a `source` is defaulted to `source:"class"` (line 3043). `syncAsiSlots` then partitions by `source`, trims `classSlots` to `nClass = asiCount()`, and *separately* pushes `nRace` race slots. If a legacy save stored a race feat in the (untagged → "class") bucket, `syncAsiSlots` may (a) trim it off as an excess class slot, losing the feat choice, and/or (b) add a fresh empty race slot, so the player must re-pick. Needs a repro with a Variant-Human save made before `source` tagging existed.
- **Suggested check:** Load an old save (pre-source-tag) for a Variant Human and confirm the racial feat survives.

### SUSPECTED MEDIUM — `asiCount` undercounts ASIs when a class name is mis-typed or contains digits
- **File/lines:** 1405–1411.
- **Concern:** `asiCount` parses `#classlevel` with `/([A-Za-z'’][A-Za-z'’\- ]*?)\s+(\d+)/g`. The builder always emits clean `Name N` segments, so this is fine for built characters. But for a *manually typed* field like `Fighter (Battle Master) 7` (subclass before the number) the regex captures `"Fighter (Battle Master"`? No — `(` is not in the class-name char class, so it stops at "Fighter", matches "Fighter" + … actually the `\s+\d+` requires the number to follow the name token; here the number follows the paren, so the first match would fail to find a number adjacent and the whole segment may be skipped → 0 ASIs counted. Needs a manual-entry repro to confirm exact behavior.
- **Suggested check:** Type `Fighter (Battle Master) 7` directly into Class & Level and see whether the ASI flag shows the expected 2 improvements (L4, L6).

### SUSPECTED MEDIUM — `charLevel()` sums *every* number in the field, including digits inside a subclass name
- **File/lines:** 2768–2772.
- **Concern:** `($("classlevel").value||"").match(/\d+/g)` then sums all. The builder's strings never contain digits in subclass names, but a manual entry like `Wizard 5 (War Magic 2024)` would sum 5+2024 → clamped to 20, but a value like `Cleric 3 (Order 1)` → 4. Any subclass label containing a number corrupts the level. Low real-world likelihood but possible with homebrew labels.
- **Suggested check:** Decide whether to parse via `parseClassLevels` (which correctly isolates the `Name N` level) instead of summing all digits.

### SUSPECTED LOW — `maxSpellLevel` for a multiclass caps the spell-list sections by the primary class only, not combined caster level
- **File/lines:** 2517–2527, 2682.
- **Concern:** `spellMaxByInst[inst] = maxSpellLevel(cls, sheetLevel)` uses the single selected class and the *character* level. For e.g. `Cleric 3 / Wizard 3` (combined caster level 6 → up to 3rd-level slots), with spellclass=Wizard and charLevel=6, `maxSpellLevel(Wizard,6)=ceil(6/2)=3`. Happens to match here. But `Paladin 6 / Sorcerer 4`: charLevel=10, spellclass picked as Paladin (raw level 6) → `maxSpellLevel(Paladin,10)=floor(10/4)+1=3`, while combined caster level is 3+4=7 → 4th-level slots exist (`mcSlots` would show them) but the spell *list* sections cap at 3. Slots and list sections can disagree. Verify whether the slot grid showing L4 while the list hides L4 is acceptable.

---

## Edge cases & robustness

- **Level 0 / blank class:** `charLevel()` returns `null` when no digits; `compute()` guards most outputs on `null`. Verified PB, saves, skills, AC, carrying all blank-safe. Good.
- **No DATA loaded:** `populateWizard` disables the Create button (3311); `classSpellList`/`classSpellNamesAt` null-guard DATA; `armorByName` guards. `compute()` does not depend on DATA except via item/AC pickers which all `|| []`. Robust.
- **Overflow page minimum:** `setOverflowPages(0)` still creates 1 page (`Math.max(1, n||1)`). Confirmed intentional — no static overflow page exists in markup, and the page is print-excluded unless `overflowPageUsed`. Not a bug.
- **`esc()` does not escape `>`** (3303) — only `&`, `<`, `"`. Since `<` is escaped, an injected lone `>` cannot open a tag, so this is not an injection vector for the data it handles (5etools content + user field values). Acceptable, but note it for any future `innerHTML` use that relies on full escaping.
- **`num(qv,1) || 1` pattern** (rowQty) — see Confirmed MEDIUM above; same `|| fallback` anti-pattern would bite anywhere a legit 0 is meaningful.
- **Spell-slot `tot.readOnly` toggle (2576–2577):** switching from auto to manual clears the stale value and unlocks — correct. Switching class away from a caster leaves the unlock path; verified it reverts cleanly.
- **`autoSlots` Warlock single-class** (2536): cnt/level table matches PHB Pact Magic (1→1, 2→2, 11→3, 17→4 slots; slot level = min(5, ceil(L/2))). Correct.
- **`SLOTS_FULL`/`SLOTS_HALF`/`SLOTS_THIRD`/`SLOTS_ARTIFICER` tables** (2529–2532): spot-checked against PHB/Tasha's — full at L20 `[4,3,3,3,3,2,2,1,1]` correct; half-caster (Paladin/Ranger) and Artificer (slots from L1) correct; one-third (EK/AT) correct.
- **Carrying capacity:** STR×15 carry, ×30 push/drag, coins/50 lb — all PHB-correct (2868–2900).
- **Proficiency bonus:** `2 + Math.floor((level-1)/4)` (2776) — correct for L1–20.
- **Medium armor Dex cap, heavy armor no-Dex, light armor full Dex** (2823–2827): correct. Heavy-armor STR-requirement −10ft speed penalty (2916–2924) correct; mithral removes it.
- **Monk Unarmored Movement** (2925–2933): `Math.min(30, floor((mlvl-2)/4)*5 + 10)` for L2+ unarmored/no-shield → +10 at L2, +15 at L6, … +30 at L18. Correct.

---

## Rules-correctness notes

- **Multiclass spell slots (`multiclassCasterLevel` + `mcSlots`)** — math is correct: full casters add full level, Paladin/Ranger floor(L/2), Artificer ceil(L/2), EK/AT floor(L/3), Warlock excluded (separate Pact pool). Combined level indexes `SLOTS_FULL`. This matches the PHB multiclass spellcaster table. The only weakness is *which class anchors sheet 0* (HIGH bug above) and the *list-section cap* (SUSPECTED LOW above), not the slot counts themselves.
- **Warlock multiclass** — handled separately and correctly: a multiclass sheet with `spellclass=Warlock` shows only the pact pool (`autoSlots("Warlock", warlockLevel)`); full-caster slots must live on a second spell sheet. This is a UX limitation (one sheet can't show both pools simultaneously), not a math error.
- **ASI levels (`classAsiLevels`)** — Fighter `[4,6,8,12,14,16,19]`, Rogue `[4,8,10,12,16,19]`, others `[4,8,12,16,19]`. Correct for 2014 rules.
- **Half-caster prepared count** — `mods[sa] + floor(level/2)` for Paladin/Artificer, `mods[sa] + level` for full prepared casters (2957–2959), min 1. Correct.
- **Spell save DC / attack** — `8 + pb + mod` and `pb + mod` (2942–2943). Correct.
- **Saving-throw proficiencies from initial class only** (4314) and **multiclass proficiency subset via `mcProf`** (4319) — correct per PHB multiclassing rules.
- **Hit dice** — single class shows `1dX+CON` heal die; multiclass shows mixed pools as text and leaves `#hitdice` alone (4315–4318). Correct; available = total − used (2856–2860).
- **build-data.py / in-browser parity** — `DATA_VERSION = 13` in both (HTML 1209, py 26). The `et*` functions mirror the Python `*` functions for races/classes/feats/prof blocks; staleness check (`sourcesAreStale`, `init` ver compare at 4396–4398) correctly discards stored data built by an older extractor when a newer baked version exists. No divergence found that would corrupt numbers.
