# coverage/ — MPMB mechanics coverage oracle

Turns "some feat/item/race/class isn't wired into the automation" from a
whack-a-mole into a finite, sortable punch-list, by diffing the sheet against
MPMB's encoded rules.

**Current coverage: 45 / 65 mechanical capabilities** (see `COVERAGE-REPORT.md`).
983 of MPMB's 1908 entities are present in this sheet's baked data.

## Files

| file | what it is |
|---|---|
| `coverage-oracle.py` | the tool (stdlib only, except `pypdf` for `--pdf`) |
| `mpmb-schema.json` | canonical mechanical-field vocabulary, parsed from MPMB's syntax docs |
| `mpmb-entities.json` | every MPMB entity → which mechanical fields it uses (the full WotC+UA library) |
| `capability-manifest.json` | **source of truth** for what THIS sheet implements; hand-editable |
| `COVERAGE-REPORT.md` | the generated punch-list (capability table + who-needs-what) |

## How it works

1. **EXTRACT** — parse MPMB's `additional content syntax/*.js` for the canonical
   set of character-modifying capabilities (the 58 fields in `_common
   attributes.js` + the `calcChanges` hooks), and parse every entity to see
   which capabilities each one relies on.
2. **DIFF** — compare against `capability-manifest.json` (what we implement).
3. **REPORT** — rank unsupported capabilities by how many *in-your-data* entities
   they block, and list the exact feats/items/races/subclasses behind each.

The MPMB side is exact. The *supported?* column is only as good as the manifest:
each row was verified by reading the actual engine code and locked with
`status: "verified"` + a code-evidence note. A row whose `status` starts with
`auto-` is an unreviewed guess; set it to anything else to lock it (re-runs
won't overwrite locked rows).

## Getting the full content

The stock MPMB PDF and the GitHub repo only ship **SRD** content. To diff
against the **entire** WotC+UA library, open the MPMB PDF in Acrobat, import the
full content, **save**, then point the oracle at it — the content lives in a form
field named `Stringified` and gets mined automatically.

## Usage

```bash
# refresh the schema from a repo clone, AND mine the full library from a saved PDF:
git clone --depth 1 https://github.com/morepurplemorebetter/MPMBs-Character-Record-Sheet.git /tmp/mpmb-repo
python3 coverage/coverage-oracle.py --extract --mpmb /tmp/mpmb-repo \
    --pdf "/path/to/saved/MPMB ... .pdf"

# regenerate the report after a build (uses committed JSON; no clone needed):
python3 coverage/coverage-oracle.py --no-probe
```

## In-data ranking (important)

MPMB's library (1908 entities) is far larger than the 5etools content this sheet
bakes (~983 entities). Raw impact counts overstate reality: a capability used by
100 MPMB items helps nobody if none of those items are in the sheet. The oracle
reads the sheet's **runtime data** and **ranks the punch-list by *in your data*
impact** — and the per-capability "who needs this" lists show only entities you
actually have.

`--sheet-data` defaults to **`index.html`**, whose `#source-data` block is the
authoritative runtime data. (It also accepts a `source-data.json`, but that file
is a stale build artifact — don't rank against it. An earlier version of this
oracle did, and badly undercounted, wrongly reporting loaded content like Armorer
and tabaxi as absent.)

Caveat: *in-data* means the entity's name exists in the sheet's data, not that
every nuance is automatable. Magic-weapon special **save** riders (e.g. Dagger of
Venom's poison DC) aren't auto-applied — but the weapon's attack/bonus, damage
riders (Flame Tongue +2d6 fire), and charges (Wand of … → Limited Features) now
are.

The saved MPMB PDF is **not** committed (it's a personal Acrobat file); only the
extracted JSON metadata is. Re-mine from your own saved PDF when MPMB updates.

## What's been wired up (the supported side)

Highlights of capabilities implemented since this oracle started (all `verified`
in the manifest):

- **Dragonborn breath weapon** — ancestry picker → save-based attack row (DC &
  dice scale with Con/level) + damage resistance; all 6 lineages (PHB 2d6 +
  Fizban Chromatic/Gem/Metallic 1d10).
- **Save (dis)advantages** (`savetxt`/`adv_vs`) — `scanDefenses` pulls "advantage
  on saving throws vs X" from race/feature prose into the Defenses box.
- **Racial natural weapons** (`weaponOptions`) — claws/horns/bite/etc. as attack
  rows (data-driven from trait prose).
- **Subclass/feat attacks** — Soulknife, Armorer, Battlerager, Beast, Sun Soul,
  Astral Self, Fathomless, Polearm Master, Dragon Hide (FEATURE_ATTACKS registry
  in the app JS, not data).
- **Magic weapons** — 1603 named + variant weapons (Flame Tongue, Frost Brand,
  Vicious, `+N <weapon>`…) → attack rows with bonus + damage rider.
- **Half-feat ability boosts** — own "Feat" column in the ability hood.

The big remaining gaps (by in-data impact): `action` (a structured Actions list;
feature text already renders), `calcChanges` (procedural recalc hooks — the real
source of one-off surprises), `spellChanges`, `skillstxt`, `fixedDC`.

## Caveats

- Entity names include UA variants (`...-ua`); filter if you only want published.
- Per-entity field detection is token-based, so a few structural sub-fields
  (`text`, `note`, `adv_vs`) leak in as low-value rows — each shows its purpose.
- `calcChanges` is procedural (arbitrary JS in MPMB): you can't copy it, only
  reimplement the intent. The report flags it `proc`.
- **Build pipeline drift:** `build-data.py` is behind the committed `#source-data`
  on some fields (v19/v20), so a full rebuild would regress. New data (ancestry,
  natural weapons, magic weapons, charged itemText) was injected surgically into
  `index.html`'s `#source-data` instead. Reconcile the drift before ever running
  a full `build-data.py` rebuild.
