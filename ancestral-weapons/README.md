# Ancestral Weapons — upgrade catalog (build tooling)

Source data for the in-sheet **Ancestral Weapons builder** (the Spirit-Points
point-buy weapon creator), from *Ancestral Weapons v1.2* by Matt Vaughan /
Dungeon Rollers.

- `extract.py` — reproducible parser. De-interleaves the PDF's two columns and
  pulls every upgrade's name / tier / cost / `limited` / requirement / text.
  Run: `python3 extract.py [path-to-pdf]` (defaults to `~/Downloads/Ancestral_Weapons_Final_v1.2.pdf`).
  Needs `pdfplumber` (`python3 -m pip install --break-system-packages pdfplumber`).
- `upgrades.json` — the generated catalog. **Gitignored** because the upgrade
  *descriptions* are third-party copyrighted text. Only the non-copyrightable
  mechanics (names/costs/tiers/tags/requirements) ship in the app's JS; the text
  bakes into the local `#source-data` layer, exactly like the 5etools data.

Verified: 134 upgrades, 36/45/28/25 per tier (matches the book's own summary).
Regenerate with `extract.py` rather than hand-editing.
