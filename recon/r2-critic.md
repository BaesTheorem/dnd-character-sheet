# R2 Critic — Mobile Sheet Improvement Plan Stress-Test

## Print-Regression Pass (per-item verdict)

**`inputmode` / `enterkeyhint` on number fields** — SAFE.
These are HTML attributes on `<input>` elements. The `@media print` block hides all interactivity chrome; these attributes have no CSS surface and no rendering impact in print context. Zero risk.

**`touch-action:manipulation` on tap targets** — SAFE.
`touch-action` is a pointer/touch event hint; it has no effect in print rendering. The print block doesn't reference it. SAFE.

**`overscroll-behavior:contain` on `.pagetabs` and modal bodies** — SAFE with one observation.
The `.pagetabs` is already `display:none !important` in the `@media print` block (line 562), so any scroll containment on it is moot in print. Modal overlays are also not present during print. The `overscroll-behavior` property is strictly a scroll-behavior hint and doesn't alter layout geometry. SAFE.

**`dvh` / `svh` for modal height** — NEEDS A PRINT GUARD (minor).
Modal panels currently use `min-height:100%` on `.modal-panel` (line 727). If `dvh`/`svh` is applied to the modal or its body, it should be fine in practice because modals aren't present during a print (no user opens a modal and then prints). However, `dvh` units are not universally overridden by the print block — if a `min-height:100dvh` somehow survives into print context it could force a page to be at minimum the full viewport height. The print block doesn't zero out modal panel heights. Verdict: NEEDS A PRINT GUARD — add `@media print { .modal, .modal-panel, .settings-panel { display:none !important; } }` (this may already be covered by the `.noprint` exclusion for the modal overlay, but the current print block only explicitly hides `.toolbar,.noprint,.gen-status`; modal panels lack `.noprint`). Verify that `.modal` is suppressed before shipping `dvh` on modal heights.

**Flat/sharp via `--radius:0` and `--shadow:none` globally** — NEEDS A PRINT GUARD (cosmetic, low severity).
The `@media print` block already overrides `--shadow:none` at line 555, so the shadow change is safe regardless. However, `--radius` is NOT reset in the print block. Currently `--radius:12px` and the print block doesn't touch it. The `.card` rule at line 65 uses `border-radius:var(--radius)`. If `--radius` is set to `0` globally, the printed sheet will have square-cornered cards. Whether that's a regression depends on taste — the print sheet is already fairly minimal — but it is a visual change to the printed output. Verdict: NEEDS A PRINT GUARD — add `--radius:4px` (or whatever small softness is desired) inside the `@media print :root` block at line 555 to decouple the on-screen flat/sharp toggle from the printed appearance, or explicitly document that the printed sheet will also go square-cornered.

**Sticky combat status strip (P1)** — RISKY.
The print block forces `.pagetabs { display:none !important }` but it does NOT have a generic rule suppressing arbitrary sticky elements. A new sticky strip not marked `.noprint` would print on every page — once inline in its original position in the DOM flow (Core page) and potentially as a visual artifact across other pages depending on browser handling of `position:sticky` in paginated print. Verdict: RISKY — any sticky strip MUST get `.noprint` on its element, or be guarded with `@media print { .combat-strip { display:none !important } }`. The combat data already prints correctly via the `.hp-grid`, `.deathsaves`, and `.lftable` on the Core page; a duplicate strip printing would be pure noise.

---

## Autosave-Regression Pass

**How `data-save` works (lines 3274-3322):** `collect()` iterates `document.querySelectorAll("[data-save]")` and writes `data[el.id] = value`. `applyFields()` iterates the same selector and restores by `el.id`. The system is **id-keyed**: if an element has `data-save` but no `id`, it silently contributes nothing (its value is read as `data[undefined]`, overwriting the previous one). If two elements share an `id`, the second one wins on collect and neither gets correctly restored.

**The mirror problem for the combat strip:** If the strip is implemented by creating NEW elements that mirror `#hpcur`, `#hptmp`, `#lfused-0..N`, spell slot ids, and death save checkboxes, there are two sub-cases:

1. **Mirror gets `data-save`**: BROKEN. `collect()` will find both the original and the mirror. They share the same `id` (or they have different ids and `applyFields` restores only the original, leaving the mirror stale on load). If they have the SAME id (DOM duplication), `querySelectorAll` returns both and the last one in document order wins the write — which is non-deterministic with dynamic insertion order. `applyFields` similarly restores the first match only. **Safe rule: mirrors MUST NOT have `data-save`.** Period.

2. **Mirror has NO `data-save`, synced via JS**: Safe for persistence. The risk shifts to drift (see Combat Strip Failure Modes). The save/restore cycle will correctly round-trip through the canonical inputs; the mirror is view-only.

**Export (Save copy HTML, line 5141-5143):** The export calls `collect()` and writes into `#embedded-data`. If the strip has no `data-save`, the export is clean. If it accidentally gets `data-save` with a novel id, a future load would see an unknown key and silently ignore it (the `if(!(el.id in data)) return` guard at line 3319) — safe for forward compatibility, but the novel id would sit permanently in the localStorage blob as dead weight.

**Overflow pages and dynamic ids:** The pattern `lfused-${i}`, `slot${l}u`, `dss-${i}`, `dsf-${i}` are all built during `initStaticHTML()` / `slotsHTML()`. Any mirror that reads from these must do so AFTER `initStaticHTML()` runs (it's called from `init()` which fires on DOMContentLoaded). The strip's sync handler must be wired after init, not at parse time.

**Safe rule summary:** Mirror inputs carry NO `data-save`. Canonical inputs remain the single source of truth. The strip reads from canonical inputs on every `compute()` call (or listens on `input` events), never the reverse. Write path is one-directional: user edits canonical → strip reflects → localStorage sees only canonical.

---

## Combat-Strip Failure Modes

**Two-source-of-truth drift (highest risk).**
If the strip contains editable inputs (not read-only mirrors), the user can edit the strip value AND the canonical input independently. Without a two-way sync handler, they diverge immediately. A one-way sync (canonical → strip on every `compute()`) solves read-only display but requires the strip to be visually non-editable — which defeats the "quick at-table tap" use case. Making it truly two-way requires either (a) moving focus between fields, which fights the browser's native input-focus model, or (b) making the strip inputs the canonical inputs (CSS reposition, not duplication), which is the only architecturally clean version but requires restructuring the DOM or using CSS `order` in a flexbox/grid, which only works if the strip and the Core tab's combat block share a flex container — they don't.

**Vertical space theft on small phones.**
The `.pagetabs` is already sticky at `top:0` (line 698) with `z-index:15`. A strip sticky below it (e.g., `top:42px`) would consume additional space on every tab, not just Core. On an iPhone SE (375x667) that's 42px tabs + ~56px strip = ~100px of pinned chrome before any content. The Core tab's combat section is already on-screen — the strip only helps on other tabs. The tradeoff is: non-Core tabs lose ~56px of usable height for a strip that saves one tab-switch per combat round. On portrait small phones, this is a meaningful cost for infrequent non-HP edits (limited feature uses are typically toggled once per encounter, not per round).

**Focus and scroll fights with the sticky tab bar.**
When the user taps a strip input on a non-Core tab, the iOS virtual keyboard raises the viewport. The `.pagetabs` is `position:sticky; top:0` — it stays visible. The strip, also sticky, would either stay pinned (eating more visible space above the keyboard) or be scrolled under the keyboard depending on where `top` is set relative to `position:sticky` context. On iOS Safari, `position:sticky` elements inside a scrollable container with `dvh`/`svh` heights can jump unexpectedly when the keyboard appears because the viewport height changes. This is a known iOS pain point and would require testing on-device. There's no purely CSS fix; a JS `visualViewport` resize listener may be needed.

**Landscape behavior.**
In landscape on a phone, total viewport height is ~375px. Sticky toolbar (gone — it's `position:static` in mobile, line 690) is not pinned. But `.pagetabs` at 42px and a strip at ~56px consume ~98px, leaving ~277px for content. Most `.card` blocks have fixed minimum heights; the user would need to scroll to see HP AND the strip simultaneously in some landscape layouts. The strip concept was predicated on vertical scroll saving; in landscape, the tab bar already fits more tabs and the scroll is mostly horizontal. The strip is more valuable in portrait.

**Empty state for non-spellcasters.**
The 5 high-churn fields for a Fighter with no spellcasting are: Current HP, Temp HP, limited feature uses, death saves. Spell slots are not present. The strip must conditionally hide the slot cluster or it shows 9 empty boxes. The `.slots` card already handles this via `applyLayout()` toggling `excluded` (line 2654 area). The strip would need to mirror that exclusion logic. If it doesn't, a non-caster sees a strip full of `0/0` or blank slot inputs — confusing.

**Limited features count is variable.**
`NLIMITED` rows exist, some blank. The strip would either show all N rows (noisy for characters using 2 out of 8 slots) or dynamically detect filled rows (requires reading `lfname-${i}` values and filtering). Neither is trivial. Showing only "used vs max" totals collapses the per-feature granularity the player needs.

---

## Durability UX — Least-Bad Option + Honest Limits

**`navigator.storage.persist()` on iOS Safari:**
As of Safari 17/iOS 17, `navigator.storage.persist()` is technically supported but the browser's response is effectively useless: it returns `false` by default on iOS unless the site is added to the Home Screen as a PWA. Even as a Home Screen app, Safari caps site storage at ~50MB and may still evict under extreme memory pressure. The API call does not raise a permission dialog on iOS (unlike Chrome on Android); it silently returns a boolean. Calling it is not security theater for desktop browsers (Chrome/Firefox will prompt the user), but for iOS — the highest-risk platform for localStorage eviction — it provides no real protection. Honest limit: `navigator.storage.persist()` is worth calling (cheap, helps on Chrome/Android) but should not be presented to the user as "your data is safe" on iOS.

**"Last saved" banner / staleness indicator:**
A small banner showing "Saved 2 min ago" is reassuring during active use and alarming only if it shows a long gap. The current `flashStatus()` system (line 3433) already shows "Saved" transiently (1500ms). The gap is that after the flash disappears the user has no persistent confirmation. A persistent "last saved at HH:MM" in the status area would require a timestamp stored alongside the save — a one-liner addition to the `save()` function. The honest limit: this reassures the user that the session's autosave is working, but does nothing about inter-session eviction. The banner cannot warn "localStorage was cleared since last visit" because the data is gone.

**Auto-export-on-change:**
Spamming Downloads is a non-starter on mobile — iOS Safari's download behavior requires user gesture (tapping the download link in the share sheet) and cannot be automated without a gesture. On desktop it would create a new file on every change event (400ms debounce = dozens of files per session). This idea is not viable in any form.

**Least-bad option: On-pagehide / on-visibilitychange download prompt + periodic reminder.**
The sheet already flushes saves on `pagehide` and `visibilitychange` (lines 4954-4955). The least-disruptive durability improvement is:
1. After each `save()`, write a timestamp to a separate localStorage key.
2. On load, if the timestamp is older than N days (e.g., 7), show a persistent banner: "No backup file saved in 7 days — tap Save to download a copy." This matches the existing "Save" button UX and requires no new user-facing concepts.
3. Honest limit: the user still loses data if they never tap Save and localStorage is evicted. The sheet is already half-PWA (self-contained HTML file); the "Save" download IS the backup, and the reminder nudges toward using it. No mechanism short of a server or sync API can guarantee durability without user action on iOS.

---

## Scope-Creep / Mislabeled Items

**Genuinely P0 (additive, ~1 day, no regressions):**
- `inputmode="numeric"` and `enterkeyhint="done"` on `type=number` inputs: a one-line template search-and-replace. Confirmed additive.
- `touch-action:manipulation` on buttons and tap targets: 2-3 CSS rules appended to the existing `@media (max-width:820px)` block. Additive.
- `overscroll-behavior:contain` on `.pagetabs`: one CSS property. Additive.
- Flat/sharp via `--radius:0` (or `4px`) and `--shadow:none` in `:root` override: two variable changes. **Requires the print guard noted above** (add `--radius` to the print `:root` block) — 3 lines total. Still P0 if the print guard is included.

**P0 but needs the print guard explicitly scoped as part of the ticket:**
- `dvh`/`svh` for modal heights: requires verifying modals are suppressed in print (see above). The change itself is 1-2 CSS lines but the regression check is non-trivial on Safari. Classify as P0 with a mandatory iOS Safari print test before merge.

**Mislabeled P0 — actually P1:**
- **"Last saved" timestamp banner / `navigator.storage.persist()` call**: Looks like a one-liner but requires: (a) adding a timestamp to `save()`, (b) adding a load-time check + banner UI element, (c) deciding where the banner lives without fighting the existing `#status` element, (d) testing that `navigator.storage.persist()` call doesn't throw on Safari private browsing. Minimum 0.5 days of careful work. Call it P1.

**Mislabeled P0 — actually P1 or P2:**
- **Content-dot tabs (`.ptab.muted` reuse for "this tab has data"):** The `.ptab.muted` class (line 385) currently means `opacity:.45` — it is used for tabs that are present but hidden (excluded pages). Reusing it to mean "has data" would conflict with the existing semantic. A new modifier class is needed. That requires: (a) auditing all places `muted` is applied (line 2654 area), (b) defining what "has data" means per tab (non-trivial: Spells tab is "has data" if any slot is used; Inventory if any row is non-empty; Features if the textarea is non-empty; etc.), (c) hooking into `compute()` to update dots after every change. This is not additive — it changes existing class semantics and requires per-tab data-detection logic. This is P1 minimum.

---

## What Survives (Cleared for the Roadmap)

1. `inputmode` / `enterkeyhint` on number inputs — P0, ship it.
2. `touch-action:manipulation` on interactive elements — P0, ship it.
3. `overscroll-behavior:contain` on `.pagetabs` — P0, ship it.
4. Flat/sharp (`--radius`, `--shadow`) with a print guard adding `--radius` to the `@media print :root` block — P0 with one extra line.
5. "Last saved N days ago" banner with `navigator.storage.persist()` call — P1, not P0.
6. Combat strip via CSS repositioning of canonical inputs (not mirroring) — P1, with the `.noprint` guard as a hard requirement.
7. Content-dot tabs — P1, requires a new class name (not `.muted`) and per-tab data-presence heuristics.

---

## Unanswered Objections (2, no rebuttal)

**1. The sticky strip's value proposition evaporates in the one case that matters most: dying.**
Death saves appear at the bottom of the Core tab's Combat card (lines 852-857). They are checkboxes (`dss-0..2`, `dsf-0..2`) rendered inside `#ds-success` and `#ds-fail` spans, styled with `.pips` (line 251). When a character drops to 0 HP the player is almost certainly on the Core tab already — that's where HP is edited. The strip would show HP (0), temp HP (0), and death saves — all of which are already visible on Core without any scrolling. The strip saves a tab-switch for players who wander to Spells or Inventory mid-combat, but the "I need to track this urgently" case (death saves) already doesn't require a tab-switch. The strip's real user is the player who goes to check a spell while also tracking resources — a real use case, but narrower than the P1 framing implies. This narrowness may not justify the vertical-space cost and the two-source-of-truth complexity.

**2. The `save()` function's 400ms debounce (line 3518) combined with `pagehide` flush (line 4954) is the ONLY durability guarantee for in-session data — and it is already there. Every proposed durability improvement (timestamp banner, `persist()` call) addresses a problem (inter-session eviction) that is structurally unsolvable without user action, while doing nothing to improve the existing in-session guarantee. The real durability gap is that users don't know the "Save" button exists or what it does.** The sheet's toolbar button reads "Save" (line 747) with a tooltip "Save this character to a self-contained HTML file" — but on mobile the toolbar is `position:static` and scrolls off-screen. There is no persistent affordance to remind the user that localStorage is ephemeral. A more direct fix — making the Save button sticky on mobile, or adding a one-time onboarding callout — would address the actual UX gap without any of the `navigator.storage.persist()` theater. This alternative is not in the current P1 plan and goes unaddressed.

---

**Timing**: Started Sun Jun  7 02:33:49 UTC 2026 · Finished Sun Jun  7 02:35:13 UTC 2026
