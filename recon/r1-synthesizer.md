# R1 Synthesizer — Mid-Brainstorm Integration

Mode: autonomous + FOCUS. Deliverable target: a prioritized, actionable mobile-improvement plan.
This is the Round 1 mid-brainstorm synthesis, NOT the final document.

## Emergent Themes

1. **The real enemy is navigation + data durability, not read-mode friction.** The Explorer and Associator both built elaborate cases for a Play/Edit mode split (always-editable fields are "noise" / "accidental-overwrite risk"). The Critic surfaced the load-bearing counter-signal: across D&D Beyond, Roll20, and app-review prior art, the dominant complaints are (a) sync/data loss and (b) cumbersome navigation — and the one complaint that does *not* appear is players frustrated they can't edit mid-combat. This reframes the whole session: the highest-value problems are durability (iOS ITP eviction) and reaching the right tab fast, not eliminating input chrome.

2. **A small set of "high-churn" fields carries almost all live-play interaction.** Independently, all three agents converge on the same 4-6 fields: Current HP, Temp HP, spell slots used, limited-feature pips, death saves. The Associator framed these via fitness-tracker / cockpit-MFD glanceability; the Explorer via a Combat Quick Panel; the Critic endorsed a *scoped* "big stepper" widget for exactly these. This is the session's strongest convergence and the seed of the P0/P1 core: build great affordances for the 5% of fields that actually change at the table, leave the other 95% alone.

3. **"Additive over desktop" and "the print stylesheet is a second app" are the two hard rails every structural idea hits.** The Critic establishes that the `@media print` block (120+ lines, class-name- and element-order-dependent, with a fragile `textarea`↔`.ta-print` dual-element pattern) plus the additive-only constraint together veto any move that changes the DOM skeleton. Anything that only adds CSS in the `@media (max-width:820px)` block is cheap and safe; anything that adds wrapper divs or span-mirror elements is expensive and print-risky. This is the master filter for prioritization.

4. **The cheapest 80% is genuinely cheap, additive, and print-neutral — and it's mostly attributes/CSS one-liners.** `inputmode`/`enterkeyhint`, `touch-action:manipulation`, `overscroll-behavior:contain`, `dvh`/`svh` modal heights, and the flat/sharp variable change are all low-risk, fast, and align with Alex's documented UI taste. There is broad agreement these ship first. The only nuance: `dvh` needs an Android-chrome test (use `svh` as fallback), and the flat/sharp fix is better done *globally in both files* than as a mobile-only override (else it creates desktop/mobile divergence).

5. **Offline-installability is a mirage on this architecture; durability must be solved with UX, not PWA.** The Explorer's PWA/inline-service-worker idea is decisively killed by the Critic on two independent grounds: service workers cannot register from `file://` (rejected promise, spec-level, never changing), and even if served, SW registration is itself script-writable storage subject to the same 7-day ITP sweep. The sheet already works offline as static HTML. The genuine durability problem (ITP silently wiping localStorage after 7 days of non-use) is unsolved by any proposal except an export-nudge / "the file is the source of truth" UX shift.

## Productive Tensions

- **Ambition (full Play/Edit mode split) vs. additive-only + print-fragility.** Associator ranks the mode split #1 and calls it "a class toggle + span↔input swap, not architecturally hard." Critic's Objection B is the direct rebuttal: ~200 interdependent fields with live computed cross-dependencies, requiring dual-state HTML that can't live in a `@media` block (it changes the DOM), plus a *third* state on the already-fragile print dual-element pattern, with silent-data-corruption failure modes. **Keep this tension live into R2** — but the productive resolution is almost certainly the Critic's scoping: get the *value* of the mode split (glanceable, fat-finger-safe live fields) by building steppers/pips for the 5-6 high-churn fields only, and explicitly NOT touching the other 195 fields. R2 should test whether that scoped version captures most of the benefit.

- **Offline-installable PWA vs. ITP/`file://` reality.** Fully resolved against the PWA by the Critic — but the underlying *need* (durable character storage) survives and is arguably the single highest-stakes item in the whole session (Critic's Unanswered Objection 1). Tension to preserve: is the right answer a soft UX nudge (export-reminder banner keyed to a last-backup timestamp) or a harder architectural shift ("open from the downloaded file every session; the file is the source of truth")? R2 should pin down the minimal-viable durability UX that doesn't require a server.

- **Play-glanceability vs. always-editable fields.** Associator/Explorer want display-mode read states (spans) to reduce noise and accidental edits; Critic's prior-art finding says nobody actually complains about mid-combat editability, so the accidental-overwrite risk may be overstated. Resolution path: a *status strip / quick panel* that is read-glanceable for the few key numbers, layered over an otherwise always-editable sheet — get glanceability without paying for a global read mode.

- **Bottom nav vs. the existing swipe-tab row.** Explorer + Associator push bottom nav (thumb-zone ergonomics, banking-app analogy). Critic's Objection C: pinning 4 of 9 tabs forces gameplay-critical tabs (Inventory, Features, Companions) into overflow or makes the split arbitrary, the current sticky auto-centering swipe row already handles thumb-reach "adequately," and D&D Beyond's bottom nav is itself criticized for hiding content. **This tension should mostly resolve toward "don't replace the tab row"** — but the cheap residue (larger min-width tabs, `touch-action`, a scroll-shadow fade hint, and the Associator's content-present dot) is worth keeping.

- **Flat/sharp vs. current 12px radius + shadows.** No disagreement on direction (everyone wants flat/sharp; it matches Alex's documented taste and the print stylesheet already strips shadows). The only tension is *scope*: mobile-only override (additive, but creates desktop/mobile divergence) vs. global root-variable change (touches desktop now, but is the honest fix). Critic's recommendation — do it globally, once, deliberately, before adding more mobile features — is the cleanest read.

## Duplicates / Collapsed

- **Combat Quick Panel (Explorer) = Play-mode high-churn steppers (Associator) = scoped "big stepper" widget (Critic).** Three names, one move: large +/- touch targets for HP/Temp HP/slots/pips/death-saves. Collapse into a single P0/P1 candidate. The live sub-question is *form factor*: always-visible status strip vs. slide-up bottom sheet (Critic prefers hidden-by-default slide-up to avoid eating vertical space and duplicating Core data) vs. inline-on-Core steppers.

- **Persistent status strip (Associator) ⊂ the same combat-panel cluster.** The strip (AC | HP | Inspiration | Prof bonus) is the read-only glance face of the same idea; the steppers are its write face. Treat as one feature with a read-zone and a write-zone, not two features.

- **Filled-pip spell slots (Associator) = part of the spell-slot stepper inside the combat panel.** Same move (tap-to-consume instead of numeric entry), just the spell-slot-specific rendering of the high-churn-field treatment.

- **Bottom nav (Explorer) ≈ pinned high-frequency tabs (Associator).** Same banking-app-derived move; collapse into one "tab navigation" question, which mostly resolves toward "improve the existing swipe row, don't replace it."

- **Content-present dot (Associator) ≈ binder-thickness signal ≈ restaurant-menu opacity-subordination.** All the "telegraph which tabs have content / matter" idea; one cheap CSS/JS feature.

- **`inputmode`/`enterkeyhint`, `touch-action`, `overscroll-behavior`, `dvh`/`svh`** appear in both Explorer and Critic with identical intent — already a consensus bucket, not duplicates to debate.

## Preliminary Priority Read

**P0 — ship now (cheap, additive, print-neutral, consensus):**
- `inputmode="decimal"` (Explorer) / `"numeric"` + `enterkeyhint` on number + textarea fields.
- `touch-action:manipulation` on `.btn`, `.ptab`, steppers, checkboxes.
- `overscroll-behavior:contain` on `.pagetabs` and modals.
- Modal heights → `dvh` with `svh` fallback (flag: Android-chrome test required).
- Flat/sharp global cleanup (`--radius:0`–`3px`, `--shadow:none`) — *do globally in both files, deliberately, print-tested.* (Borderline P0/P1 because it's a design-system change, not pure mobile polish — but it's a prerequisite the Critic wants "behind us" before more mobile work.)
- **localStorage durability UX** (export-nudge banner keyed to last-backup timestamp). *Highest-stakes item in the session.* P0 on importance; the exact UX is still uncertain (nudge vs. file-is-source-of-truth), so R2 must finalize the minimal-viable form.

**P1 — high value, scoped, moderate risk:**
- **Scoped combat-field widget** (HP / Temp HP / slots-as-pips / death saves) — the collapsed Combat-Panel/stepper/status-strip cluster. Form factor (slide-up bottom sheet vs. inline-on-Core vs. read-strip + write-panel) is UNCERTAIN and is the prime R2 design question. Critic leans slide-up bottom sheet, hidden by default.
- **Content-present dot on tabs** + larger min-width swipe tabs + scroll-fade hint (the salvaged residue of the bottom-nav idea).
- **Progressive disclosure for genuinely overflowing long-text only** (spell descriptions, feat/feature full text) — never for live-combat fields. Print impact must be checked.

**P2 — bigger bets / deferred / likely-cut:**
- Full Play/Edit mode split — DEFER/likely CUT (framework-scale, fights additive-only + print). Re-evaluate only if the scoped P1 widget proves insufficient.
- Bottom nav replacing swipe-tabs — likely CUT (modest gain, hides gameplay-critical tabs).
- PWA / service worker — CUT (technically impossible on `file://`; ITP voids benefit).
- Landscape-at-table sidebar nav (Explorer) — UNCERTAIN, under-examined by Critic; cheap-ish `@media (orientation:landscape)` experiment, worth an R2 reality-check.
- Mini-tab standee stat sidebar (Associator) — niche, additive, low-risk but low-frequency; P2 nice-to-have.
- Banking-app-style full-screen number-pad edit per field — collapses into the combat widget; don't build separately.

## Recommended Focus for Round 2

- **Explorer should** (gap-fill + reality-check):
  - Produce concrete, paste-ready code for the cheapest-80% P0 batch (exact selectors/attributes), so the Critic can audit it directly for print/autosave regressions.
  - Research how the *best* real mobile sheets (Fight Club 5, D&D Beyond) actually handle **data durability/backup** — is there a pattern for "the file is the source of truth" or auto-export that we can adapt within single-file/no-server constraints? This is the open durability question.
  - Specify a **minimal-viable glance/combat affordance that does NOT require a full mode split** — i.e., the scoped HP/slots/death-saves widget. Pin the form factor decision with a recommendation (inline-on-Core vs. slide-up bottom sheet vs. read-strip+write-panel) and rough vanilla-JS line count.
  - Reality-check the **landscape-at-table** breakpoint: does a condensed sidebar nav in `@media (orientation:landscape)` actually help, and is it additive/print-safe?

- **Associator should** (deepen the 1-2 strongest connections into concrete UI specs):
  - Turn the **combat-field widget** (fitness-tracker glance + cockpit-MFD + boarding-pass pips) into a concrete UI spec: exact fields, read-zone vs. write-zone layout, pip-tap vs. long-press-for-numeric interaction, and how it reads the existing save fields without a DOM refactor.
  - Spec the **content-present dot + tab-prioritization** treatment concretely (which tabs, what signal, how it reuses the existing `.ptab.muted` class), as the salvaged alternative to bottom nav.
  - Explicitly address the Critic's scoping rebuttal: show how the *value* of Play/Edit is captured by the scoped widget WITHOUT the 200-field dual-state refactor.

- **Critic should** (verify the cheap subset; find failure modes of the survivors):
  - Verify the cheapest-80% P0 subset (Explorer's concrete code) has **no print or autosave regressions** — actually reason through the `@media print` overrides and the `textarea`↔`.ta-print` pattern against each change.
  - Find the failure modes of the **scoped combat widget / status strip / slide-up panel**: stale-sync risk, print impact of any new fixed-position or wrapper element, and whether a hidden-by-default bottom sheet introduces its own discoverability/`dvh` issues.
  - Pressure-test the **durability UX** options (export-nudge banner vs. file-as-source-of-truth onboarding): which actually prevents the silent 7-day data loss for a bi-weekly player, and what's the cheapest version that isn't misleading.
  - Confirm whether the **flat/sharp global change** is truly print-neutral when applied to both files (radius/shadow on every component, not just the variables).

## Round 3 needed? (yes/no + why)

**Likely no — one more round (R2) should be enough to close to a P0/P1/P2 roadmap.** The session has already converged hard: the cheap-80% batch is consensus, the PWA and full-mode-split are effectively decided (cut/defer), and the remaining open questions are narrow and concrete — (1) the exact form factor of the scoped combat widget, (2) the minimal-viable durability UX, and (3) a print/autosave regression pass on the P0 code. Those are R2-closeable. Trigger an R3 only if R2 reveals that the scoped combat widget *cannot* capture the play-glanceability benefit without DOM-level changes (reopening the mode-split tension) or if the durability UX has no acceptable single-file answer and the no-server constraint itself needs renegotiation with Alex.

---
**Timing**: Started Sun Jun 7 02:31:01 UTC 2026 · Finished Sun Jun 7 02:31:01 UTC 2026
