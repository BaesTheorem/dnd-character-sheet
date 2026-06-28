# coverage/ — MPMB mechanics coverage oracle

Turns "some feat/item/race/class isn't wired into the automation" from a
whack-a-mole into a finite, sortable punch-list, by diffing the sheet against
MPMB's encoded rules.

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
3. **REPORT** — rank unsupported capabilities by how many entities they block,
   and list the exact feats/items/races/subclasses behind each.

The MPMB side is exact. The *supported?* column is only as good as the manifest:
it's seeded by a first-pass review, and you lock a verdict by setting that row's
`status` to anything other than `auto-*` (then re-runs won't overwrite it).

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

The saved MPMB PDF is **not** committed (it's a personal Acrobat file); only the
extracted JSON metadata is. Re-mine from your own saved PDF when MPMB updates.

## Caveats

- Entity names include UA variants (`...-ua`); filter if you only want published.
- Per-entity field detection is token-based, so a few structural sub-fields
  (`text`, `note`, `adv_vs`) leak in as low-value rows — each shows its purpose.
- `calcChanges` is procedural (arbitrary JS in MPMB): you can't copy it, only
  reimplement the intent. The report flags it `proc`.
