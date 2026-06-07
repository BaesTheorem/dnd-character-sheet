---
created: 2026-06-06
type: recon
topic: Improving the mobile version of the D&D 5e character sheet
mode: autonomous
intention: focus
source: "Character Sheet (Mobile).html"
---
# Mobile Character Sheet: A P0/P1/P2 Improvement Plan

> [!info] Process Log
> Multi-agent deep recon, 2 rounds plus a final synthesis. Four agent roles (Explorer, Associator, Critic, Synthesizer) working over web research and the actual source file, with the Critic reading the code directly (`collect()`/`applyFields()`, the `@media print` block, the `data-save` pipeline, the sticky tab chrome). Round 1 mapped the space and surfaced the central tension. Round 2 grounded the survivors in paste-ready code and stress-tested them for print and autosave regressions. This document is the FOCUS-mode synthesis: an argument and a roadmap, not an open map.
>
> Metrics. Session start 2026-06-06 21:22. Round 1: Explorer ~38k tokens / 2.4m, Associator ~41k / 2.2m, Critic ~44k / 2.8m, Synthesizer ~49k / 1.6m. Round 2: Explorer ~52k / 4.4m, Associator ~62k / 4.5m, Critic ~59k / 3.7m. Final synthesis: ~87k / 2.4m. Cumulative ~432k tokens across 8 agent runs, 2 rounds plus final synthesis.

## The Argument

The instinct, when you stare at a dense character sheet on a phone, is to want a Play mode. Lock the fields, fatten the live ones, strip the input chrome so a stray thumb under the table cannot overwrite your Wisdom score. Two of the agents built an elaborate case for exactly that, by analogy to fitness trackers and Wikipedia's read/edit split. It is a seductive idea and it is the wrong first move. The prior art does not support it. Across D&D Beyond, Roll20, and the third-party app reviews, the complaints that actually recur are data loss and clumsy navigation. The complaint that never shows up is "I couldn't edit a field mid-combat." Nobody is asking for read mode. They are asking not to lose their character and not to fight the tab bar.

So the spine of this plan is durability plus cheap ergonomics, not an editability rewrite. A full Play/Edit split is framework-scale work in a file that has no framework. It means dual-state HTML for roughly 200 interdependent fields with live computed cross-dependencies, which cannot live in a `@media` block because it changes the DOM, which means it fights the additive-only rule, which means it adds a third state to an already-fragile `textarea`-to-`.ta-print` print pattern. The failure mode is silent data corruption that only surfaces when you export or reopen. That is a bad trade against a problem nobody reported. Cut it.

What we ship instead is boring and high-leverage. A batch of attribute and CSS one-liners that fix the iOS keyboard, kill the tap delay, stop the rubber-band scroll bleed, and size the modals to the real viewport. The flat/sharp aesthetic Alex has wanted all along, finally honored at the root instead of fighted at every component. And the single most valuable durability fix in the whole session, which is almost embarrassingly mundane: the Save button is `position:static` on mobile and scrolls off the screen. The thing that writes your backup file is the thing you cannot find. Fix that and you have done more for real durability than any banner.

Two rails govern everything. The file stays single, self-contained, no build, no CDN, runs in any phone browser, autosaves to localStorage, and exports a self-contained HTML copy on Save. And the print stylesheet, that ~120 lines of class-name-dependent overrides that reconstruct a dense one-page sheet, is a load-bearing second application living inside the same file. Every change below is graded against both. Where a change touches print, the document says so out loud rather than burying it.

## The Roadmap

### P0 — Ship this week

Cheap, additive, mostly print-neutral, roughly one day of work. These go in the `@media (max-width:820px)` block or as attributes, with one deliberate global change for the aesthetic.

**1. `inputmode` + `enterkeyhint` on number fields.**
- *What.* The sheet already uses `type="number"` everywhere (HP, coins, slots, ability scores, inventory qty, hit dice). On iOS that shows a modified QWERTY with a number row, not the real numpad. Adding `inputmode="numeric"` (integers) or `inputmode="decimal"` (weights) forces the true number pad. `enterkeyhint` labels the keyboard action key (`"done"` to close, `"next"` to advance).
- *Why.* This is the single most-felt friction in live data entry on iOS. `type="number"` alone is unreliable there (iOS often renders a punctuation-heavy keyboard rather than the big numpad), so `inputmode` is the lever that actually summons the numeric keypad. Adding it to the existing fields is harmless: it changes only the keyboard, not validation or spinners, so nothing regresses. Add `pattern="[0-9]*"` to reinforce the numpad on older iOS. If a specific field still misbehaves, the fully reliable form is `inputmode` on a `type="text"` field, but treat that as a per-field fallback, not a blanket change.
- *How.* CSS cannot set HTML attributes, so a short JS pass inside the existing mobile script (guarded by `mq.matches`) selects `#hpcur,#hpmax,#hptmp,#hd-total,#hd-used,#pp,#gp,#ep,#sp,#cp,#speed,.ab-score,.ab-bonus,.hp-roll,[id^="invqty-"],[id^="slot"]` for `numeric`, and `[id^="invwt-"]` for `decimal`. Never use `type="tel"` as a shortcut; it shows a dialpad with no minus sign.
- *Print-safe?* Yes, no CSS surface in print. *Autosave-safe?* Yes, attributes only. *Effort:* 1-2 hours.

**2. `touch-action: manipulation`.**
- *What / why.* Kills the legacy ~300ms double-tap-to-zoom delay on tap targets without any JS library. Keeps pinch-zoom. The correct standards-based replacement for the old fastclick hack.
- *How.* One rule inside the media query: `*, *::before, *::after { touch-action: manipulation; }`. Covers every button, tab, checkbox, death-save pip, and stepper at once. Do not use `touch-action: none` (it breaks scrolling).
- *Print-safe?* Yes, ignored in print. *Autosave-safe?* Yes. *Effort:* 30 min.

**3. `overscroll-behavior: contain` on `.pagetabs` and `.modal-body`.**
- *What / why.* Without it, swiping past the end of the tab row or the bottom of a modal rubber-bands the page behind it. `contain` stops scroll chaining at the element boundary.
- *How.* `overscroll-behavior-x: contain` on `.pagetabs` (it scrolls horizontally), `overscroll-behavior: contain` on `.modal-body`. Supported Safari 16+; on older iOS it is silently ignored, so the degradation is cosmetic and no `@supports` guard is needed.
- *Print-safe?* Yes (`.pagetabs` is already `display:none !important` in print per the recon). *Autosave-safe?* Yes. *Effort:* 15 min.

**4. `svh` modal height, `@supports`-guarded.**
- *What / why.* Modals use `min-height:100%` resolved from a `position:fixed; inset:0` container sized to `100vh`. On iOS `100vh` resolves to the large viewport (the height with the address bar hidden), so when the address bar IS visible the container runs taller than the visible area and the modal footer clips behind the browser chrome. `svh` (small viewport, chrome visible) always fits. Use `svh`, not `dvh`: `dvh` recalculates as the address bar hides and shows, which makes a full-screen modal resize mid-scroll. `svh` is the conservative "always fits" choice for modals.
- *How.* Keep the existing `min-height:100%` as fallback, then `@supports (height: 1svh) { .modal, .modal-panel, #wizard .modal-panel, .settings-panel { min-height: 100svh; } }`. Supported Safari 15.4+, covering nearly all active devices.
- *Print-safe?* Needs one guard. The print block does not currently zero out modal heights and modals lack `.noprint`. Per the R2 Critic, add `@media print { .modal, .modal-panel, .settings-panel { display:none !important; } }` before shipping, so a stray `100svh` can never force a full-viewport print page. Cheap, do it as part of this ticket. *Autosave-safe?* Yes. *Effort:* 30 min including the guard.

**5. Flat/sharp at the root.**
- *What / why.* Current `:root` has `--radius:12px` and a two-layer `--shadow`. Alex's documented taste is flat/sharp: square corners, no shadows, hairlines. Set `--radius` to 0 (or 2px for an anti-aliasing hairline, designer call) and `--shadow: none`. Do it globally in `:root`, not as a mobile-only override, because a mobile-only override creates a permanent desktop/mobile visual divergence that someone has to reconcile later. One change, consistent everywhere.
- *How.* Edit the two `:root` variables. Add `*, *::before, *::after { border-radius: 0 !important; }` inside the media query to knock out the handful of hard-coded `border-radius` values that bypass the variable (the recon notes several).
- *Print-safe?* This is the honest flag. `--shadow:none` is ALREADY in the print `:root` block, so shadows are safe. But `--radius` is NOT reset in print. The `.card` rule uses `border-radius:var(--radius)`, so making it global squares the *printed* cards too. That is a change to printed output. Per the R2 Critic, either (a) accept square-cornered print (Alex likes flat/sharp, so this is probably fine), or (b) decouple by adding `--radius:4px` to the `@media print :root` block. **This is Alex's call, flagged here rather than buried.** Recommendation: accept the square print, it matches the taste, but make the decision consciously. *Autosave-safe?* Yes. *Effort:* 1 hour with a print test.

**6. Make Save always reachable.**
- *What / why.* This is the highest-value durability item in the session and it has nothing to do with banners or storage APIs. The "Save" button (tooltip: "Save this character to a self-contained HTML file") is the actual backup mechanism, and on mobile the toolbar is `position:static` (per the recon, the `.toolbar` rule) and scrolls off the top of the page. The thing that writes your durable file is invisible most of the time. The mental model is already correct ("your data lives in the exported HTML file"); the affordance is just missing.
- *How.* On mobile, make Save reachable at all times: either a sticky/pinned Save affordance, or a small fixed Save button in a corner. Keep it `.noprint`. This is the cheapest real durability win and it should ship in the first batch, not wait behind the nudge banner.
- *Print-safe?* Yes if `.noprint`. *Autosave-safe?* Yes, it triggers the existing export path. *Effort:* 1-2 hours.

### P1 — Worth the wiring

Real features with real wiring, scoped to stay additive and print-safe.

**7. Content-dot tabs.**
- *What.* A small accent dot under any tab whose page has actual content. The physical analogy is binder-divider thickness: you can see at a glance that you have spells, you have notes, companions are empty, without tapping into each tab.
- *Why.* This is the Associator's ranked P1 winner and the Critic agrees it survives. Roughly 25 lines of JS plus 10 of CSS, near-zero correctness risk, because it only toggles a CSS class based on reading existing field values. Rollback is one line. Every player on every character benefits every session. It directly kills the "I keep tapping Companions thinking I set one up" and "I forgot I wrote notes" failure modes.
- *How.* A `::after` pseudo-element on `.ptab`, shown when the tab carries a new `.has-content` class. **Do NOT reuse `.ptab.muted`** (per the R2 Critic, `muted` already means `opacity:.45` for structurally excluded pages; overloading it breaks that semantic). Use a fresh class. A single `updateContentDots()` function with a per-tab content heuristic (Spells if any slot total > 0 or any spell named; Inventory if any row non-empty; Features/Notes/Backstory if the textarea is non-empty; Companions if any exist), called from `applyLayout()`, which already runs downstream of `compute()` on every change, so dots stay live. Exclude Core (always populated, always the landing tab; a dot there is noise). For the inventory scan, cache a boolean rather than re-reading up to 50 rows on every keystroke. Reuse the existing `overflowPageUsed(k)` / `spellSheetUsed(i)` helpers (per the recon) for dynamic overflow and extra spell-sheet tabs.
- *Print-safe?* Yes; the whole `.pagetabs` nav is `display:none !important` in print. *Autosave-safe?* Yes; reads only, adds no `data-save`. *Effort:* ~0.5 day.

**8. Durability nudge banner.**
- *What.* A dismissible, `.noprint` banner above the tab row that appears when it has been more than N days since the last *exported* backup (not just the last localStorage autosave), with an "Export file" button wired to the existing Save path and a dismiss.
- *Why.* Honest framing first: this does not make iOS storage durable. `navigator.storage.persist()` gives no usable guarantee in an iOS Safari tab (it gates on notification permission, and a normal browser tab stays subject to the 7-day ITP sweep regardless). The one path that IS exempt from the 7-day eviction is installing the page to the Home Screen, but that is a manual user step the page cannot invoke. `showSaveFilePicker` does not exist on iOS; auto-export-on-change is not viable on iOS because downloads require a user gesture and on desktop it would spew dozens of files per session. Inter-session localStorage eviction is structurally unsolvable without user action or a server, and the no-server law stands. So durability is three things: (a) keep "your data lives in the exported HTML file" as the model, (b) make Save always reachable (P0 item 6, the real fix), and (c) this banner as the nudge that points a forgetful bi-weekly player back at Save before the 7-day ITP sweep takes their character.
- *How.* Track a `lastExported` timestamp in a separate localStorage key, updated inside the existing Save (`btn-savecopy`) handler. On load, if a character exists and `lastExported` is older than the threshold, reveal the banner. The banner's button clicks the existing Save button and updates the timestamp. The recon's Explorer has paste-ready markup, CSS, and a `checkStaleness()` function for this.
- *Print-safe?* Yes if `.noprint`. *Autosave-safe?* Yes; the timestamp lives in its own key, never touches the `data-save` blob. *Effort:* ~0.5 day (it is not the one-liner it looks like: load-time check, banner element placement that does not fight the existing status element, and a private-browsing try/catch).

**9. A minimal combat/status strip. The judgment call.**
This is the live disagreement in the recon, and it deserves a straight answer rather than a hedge. The Explorer leaned toward a light read-only strip. The Associator ranked it P2, below content dots. The Critic is openly skeptical and left two objections standing.

The skeptic's case is strong and I am going to honor it. The strip's glance value partly evaporates in the single highest-urgency moment. When you are making death saves at 0 HP, you are already on the Core tab, because that is where you just edited HP down to zero, and death saves plus HP are already on screen there with no scrolling. So the strip does not earn its keep in the crisis. It earns its keep for the *between*-turn glance: you wandered to Spells to read a spell, or to Inventory to check a weight, and you want to see current HP and remaining slots without a tab-switch back. That is a real but narrower use case than the P1 framing first implied. Against it, there is a real cost: a sticky strip below the already-sticky tab bar eats roughly 80 to 100px of pinned chrome on a small phone (iPhone SE, 375x667), on every tab, not just the ones where it helps.

Recommendation: **build the lightest viable form, or defer.** If it ships, it must be the Explorer's read-only strip, not the Associator's full expand/collapse widget with steppers and pip rows. Concretely:
- *What.* A thin, always-visible, read-only strip below `.pagetabs` mirroring current HP, temp HP, and death-save state. Tapping it scrolls to Core. No editing in the strip.
- *Why this form.* The full editable widget reopens the two-source-of-truth problem the Critic flagged: an editable strip plus an editable canonical input diverge the moment a user edits one without the other, and true two-way sync fights the browser focus model. The read-only strip sidesteps that entirely.
- *How, with the hard constraints baked in (per the R2 Critic):*
  - The strip carries **NO `data-save`**. `collect()`/`applyFields()` are id-keyed; a mirror with `data-save` either duplicates an id (non-deterministic last-write-wins on collect, only the first restored) or adds dead keys to the blob. Never a second source of truth.
  - The strip is **`.noprint`** (or guarded by `@media print { ... display:none !important }`). The print block has no generic sticky-suppression rule, so an unguarded sticky strip would print as noise on every page. The combat data already prints correctly from the Core page.
  - It is a **read-only mirror**: it reads `#hpcur` / `#hpmax` / `#hptmp` and the death-save pips, and re-renders from those canonical inputs on every `compute()`. The clean alternative if you ever want it interactive is CSS-repositioning the canonical inputs (not duplicating them), or a mirror whose steppers `dispatchEvent(new Event("input",{bubbles:true}))` on the canonical inputs so the existing `onChange` path fires once. Never write a parallel store.
  - Sync after `init()`/`initStaticHTML()`, since the pip and slot ids are built dynamically. Confirm the death-save pip selector against the actual `pips()` render (per the recon, around line 1512) before wiring; the strip query must match whatever `pips()` emits.
  - The `top` offset (sitting below the tab row) should be measured from `pagetabs.offsetHeight` rather than hardcoded, or it underlaps when the tab row wraps.
- *Print-safe?* Yes with the `.noprint` guard (mandatory). *Autosave-safe?* Yes with no `data-save` (mandatory). *Effort:* ~0.5 day for the read-only form.

If the pinned-chrome cost feels too high on a small phone when this gets built, defer it. Content dots and the durability work are the surer P1 wins.

### P2 — Deferred and explicitly cut

**Full Play/Edit mode split. CUT.** Framework-scale in a no-framework file. Dual-state HTML for ~200 interdependent computed fields, cannot live in a `@media` block (it changes the DOM, breaking additive-only), adds a third state to the fragile print `textarea`-to-`.ta-print` pattern, fails toward silent data corruption surfaced only on export/reopen. And it solves a problem nobody reported. Revisit only if a future scoped widget proves it cannot deliver play-glanceability without DOM changes, which would reopen this tension.

**Bottom-nav replacement for the swipe-tab row. CUT.** With 9 tabs, any pinned set of 4-5 forces gameplay-relevant tabs (Inventory, Features, Companions) into an overflow drawer or makes the split arbitrary enough that users hunt. The existing sticky, auto-centering, horizontally-scrolling tab row already handles thumb reach adequately, and D&D Beyond's own bottom nav is frequently criticized for hiding content. The salvageable residue (larger min-width tabs, the content dots above) is captured in P1. The full replacement is not worth the DOM restructuring and the desktop-regression risk at the 820px boundary.

**PWA / service-worker offline. CUT.** Impossible on this architecture, on two independent grounds. Browsers block service-worker registration on the `file://` scheme: a file opened via file:// (AirDropped, emailed, opened from Files) returns a rejected registration promise. (file:// is technically a secure context, so this is an explicit browser policy rather than a secure-context failure, but the outcome is the same and is not going to change.) And even if served over HTTPS, the SW registration is itself script-writable storage subject to the same 7-day ITP sweep, so it would not even help durability. The sheet already works offline as static HTML. There is no PWA win here, only the illusion of one, which is worse because it misleads the designer into thinking durability is solved.

**Full editable combat widget (expand/collapse, steppers, slot pips, limited-feature rows). DEFERRED to P2** as the heavier sibling of the P1 strip. If the read-only strip ships and the table proves it wants tap-to-consume slot pips and HP steppers from any tab, the Associator's spec is the blueprint: one element with a collapsed status-bar state and an expanded widget state, every control dispatching `input` on the canonical inputs, capped limited-feature rows, measured `top` offset, `.noprint`, no `data-save`. It carries the most layout-regression risk (sticky stacking, keyboard-vs-sticky focus fights on iOS that may need a `visualViewport` listener) and the most wiring (event delegation for dynamically-built slot and feature rows). Earn it with the strip first.

**Landscape-at-table breakpoint. DEFERRED (low priority).** No `@media (orientation:landscape)` rule exists today, and the recon's reality-check concluded the existing layout already works acceptably when a phone is propped or flat. A `@media (max-height:480px) and (orientation:landscape)` pass to reclaim vertical chrome is plausible but P3-ish, only if a player actually asks.

**Web Share API CTA, Mini-tab standee stat panel.** Niche, additive, low-risk, low-frequency. Park them. The Share CTA (`navigator.share({files})`, iOS 15+) could one day augment the durability banner's button for users who want to push the HTML into Files or AirDrop, but it is an enhancement, not a need.

## Tensions (kept live)

**The combat strip is a genuine judgment call, not a settled item.** I came down on "lightest viable read-only form, or defer," but the disagreement is real and worth preserving: the Critic's death-saves objection (the strip is weakest exactly when stakes are highest) is not fully answered, only narrowed to a between-turns use case. If Alex finds he rarely wanders off Core mid-combat, the strip earns nothing and the pinned-chrome cost is pure loss. This is a "try it and rip it out if it does not pull its weight" feature, not a confident win.

**Pinned-chrome budget.** Every sticky element above the fold is rent. The tab row is already sticky. A strip below it stacks another ~50-80px on a phone that only has ~667px to begin with, on every tab regardless of whether the strip helps there. The durability banner, when shown, eats more. None of these are free, and on the smallest phones they compound. Prefer reaching for content (Save reachable, content dots) over consuming the top of the viewport.

**Global flat/sharp versus the print-squaring side effect.** Going flat/sharp at the root is the honest fix and matches the taste, but `--radius` is not reset in the print block, so the printed cards go square too. That is a real change to printed output. It is almost certainly fine (flat/sharp is the whole point), but it is a decision to make on purpose, not a side effect to discover later. Flagged, not buried.

**Durability is structurally unsolvable across sessions without user action.** This is the uncomfortable floor. On iOS, localStorage can be silently wiped after 7 days of non-use, the export file is the only real store, `persist()` does not help in the browser, and no-server is law. Everything we can do (Save reachable, the nudge banner, the "the file is your character" model) reduces the probability of loss for a forgetful player. None of it eliminates it. We are buying odds, not guarantees, and the plan should not pretend otherwise.

## Open Questions

- Is square-cornered *print* actually desired, or only square-cornered *screen*? If the former, set `--radius:0` globally and leave print alone. If the latter, the print `:root` block needs `--radius:4px` to decouple them. This is purely Alex's eye on a printed page.
- Would Alex rather invest the durability effort in a tiny export-to-cloud path (a one-tap Share into Drive, or a thin sync endpoint) than keep fighting local durability with nudges? That would cross the no-server line, so it is a frame-renegotiation question, not a roadmap item, but it may be the only thing that actually closes the inter-session gap.
- Does landscape-at-table deserve its own breakpoint, or is "propped phone in portrait, glance and tap" the real usage pattern? The answer depends on how Alex actually holds the phone at the table, which only he can report.
- Is the between-turns glance frequent enough to justify the combat strip at all, or does Alex mostly stay on Core during combat? This decides item 9.

## Sources

Web findings (Round 1 and 2 Explorer):
- Better Form Inputs for Better Mobile UX — https://css-tricks.com/better-form-inputs-for-better-mobile-user-experiences/
- Designing for Thumb Zones (2025) — https://elaris.software/blog/mobile-ux-thumb-zones-2025/
- Bottom Sheets UX Guidelines (NN/G) — https://www.nngroup.com/articles/bottom-sheet/
- Designing User-Friendly Data Tables for Mobile — https://medium.com/design-bootcamp/designing-user-friendly-data-tables-for-mobile-devices-c470c82403ad
- Modern CSS Viewport Units — https://modern-css.com/articles/modern-css-units-you-should-know/
- Mobile UX Thumb Zones (Parachute Design) — https://parachutedesign.ca/blog/thumb-zone-ux/

Technical constraints (Round 1 and 2 Critic, verified): iOS Safari ITP 7-day storage eviction (WebKit bug 209563, WONTFIX); browsers block service-worker registration on the `file://` scheme (MDN); `navigator.storage.persist()` gives no usable guarantee in an iOS Safari tab, with Home-Screen installs the only ITP-exempt path; `showSaveFilePicker` absent on iOS Safari. Verification pass confirmed the load-bearing claims and corrected four phrasings (the `100vh` direction, the `type=number`-vs-`inputmode` relationship, the `persist()`/Home-Screen exemption, and the `file://` block being browser policy rather than a secure-context failure).

Agent reports (all under `/Users/alexhedtke/Documents/dnd-character-sheet/recon/`): `r1-explorer.md`, `r1-associator.md`, `r1-critic.md`, `r1-synthesizer.md`, `r2-explorer.md`, `r2-associator.md`, `r2-critic.md`. Source file: `/Users/alexhedtke/Documents/dnd-character-sheet/Character Sheet (Mobile).html`. Line numbers and function names referenced above (`pips()` ~1512, `applyLayout()`, `overflowPageUsed(k)`, `spellSheetUsed(i)`, `collect()`/`applyFields()`, `#hpcur`/`#hpmax`/`#hptmp`) are per the recon and not independently re-verified line by line in this synthesis.
