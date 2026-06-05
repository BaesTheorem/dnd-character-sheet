# R1 — UX Audit: Universal D&D 5e Character Sheet

Scope: actual felt user experience traced through markup, CSS, and JS handlers in
`/Users/alexhedtke/Documents/dnd-character-sheet/Character Sheet.html` (~4640 lines) against
`README.md`. Read-only. UX is the priority dimension.

Note on aesthetic: the flat/sharp theme is already enforced globally at lines 502–520
(`*{border-radius:0 !important; box-shadow:none !important}` plus hairline overrides). The
`border-radius`/`box-shadow`/`--shadow` declarations in the base CSS (lines 19–20, 48, 65, 126,
177, 372, 378–379, 392, etc.) are dead/overridden, not visible violations. The real consistency
issues are subtler (see that section).

---

## Top UX wins (ranked)

1. **Armor → AC is a silent dead-end after character creation (HIGH).**
   The wizard's Starting Equipment step adds armor as a plain Inventory row
   (`createCharacter`, lines 4355–4359 → `addInvItem`). It never ticks the row's **Equip**
   checkbox and never sets `armorsel`. The Armor dropdown that actually drives AC
   (`refreshEquippedPickers`, lines 3759–3768) lists **only equipped** body armor, and the per-row
   Equip checkbox is `style="display:none"` (line 1240), revealed only on filled/hovered rows on a
   *different* page (Inventory). So a freshly-built Fighter with chain mail shows **unarmored AC**
   with zero feedback, and the fix requires a three-step chain the user has no way to discover:
   go to Inventory → reveal+tick the armor row's Equip box → return to Armor card → pick it from
   the dropdown. **Fix:** when the wizard adds a recognized armor item, auto-equip it and pre-select
   it in `armorsel`; failing that, surface a one-line nudge on the Core combat card ("Equip armor in
   Inventory to set AC") whenever the character has unequipped armor in inventory.

2. **The wizard does zero validation and "Create" silently produces a broken character (HIGH).**
   `wiz-next` just increments `wizStep`; the final click calls `createCharacter()` unconditionally
   (line 4612). There is no per-step gate. You can advance past Race with nothing selected, reach
   step 2 and **add no class at all**, skip the name, and still click **Create** — the function runs
   to completion with empty class/saves/HP and silently closes the modal (lines 4297–4388). There is
   no success confirmation either (`createCharacter` never calls `flashStatus`). **Fix:** block
   "Next"/"Create" (or at least warn) when the current step is incomplete — minimally require an
   initial class before leaving step 2; on success, flash "Character created" so the user knows it
   took.

3. **"Save" (download a self-contained copy) gives no feedback (HIGH).**
   `btn-savecopy` (lines 4588–4593) builds the clone and calls `download(...)` with no
   `flashStatus`. Compared to autosave, which flashes "Saved" (line 3140), the explicit Save —
   the *only* way to move a character between devices and the headline portability feature — appears
   to do nothing (browsers drop the file straight to ~/Downloads with no dialog). Users will click
   it repeatedly or assume it failed. **Fix:** `flashStatus("Saved a copy to your downloads")` after
   `download(...)`.

4. **First-run is a discoverability cliff (HIGH).**
   With no sourcebook loaded, the only signal that you must load data is a *disabled* Create button
   with a `title` tooltip (lines 3310–3311) — invisible on touch and easy to miss. The instructions
   to fix it live three layers deep (Settings → Advanced → Source books). **Fix:** when `DATA` is
   null, show a dismissible banner on the Core page ("To use guided creation, load a sourcebook:
   Settings → Source books") — reuse the existing flag-banner styling.

5. **The class-builder detail panel is painfully cramped (MEDIUM-HIGH).**
   `.modal-panel` is `max-width:460px` (line 273) and the builder is a fixed `170px 1fr` grid
   (`.wiz-build`, line 306) inside `padding:18px`. The level 1–20 progression panel — which the
   README sells as "read its full progression" — renders in ~230px with a `max-height:300px` inner
   scroll (line 317). Reading 20 levels of feature text in a 230×300px box is rough. The wizard panel
   should be materially wider than the other modals (e.g. `max-width:720px` for the wizard only).

6. **`for=`-less labels: 30+ inputs have unclickable, unassociated labels (MEDIUM).**
   Every standalone `<label class="lbl">` (Class & Level, Background, Race, coins, appearance fields,
   spell pickers, etc.) is a *sibling* of its input, with no `for=` and not wrapping it (0 `for=`
   attributes in the file). Clicking the label does nothing and screen readers don't pair them. The
   checkbox labels (14 wrapping labels) are fine. **Fix:** wrap each input in its label, or add
   `for=`/`id` pairs — small, mechanical, high-coverage.

7. **No keyboard escape from any modal; no focus management (MEDIUM).**
   The only `keydown` handler in the app is the inventory item-search (lines 3814–3819). The wizard,
   ASI picker, tool picker, and Settings modals can be closed only by clicking ✕ or the backdrop —
   **Escape does nothing**, focus is never moved into the modal on open, never trapped, and never
   restored on close. **Fix:** a single document-level Escape handler closing the topmost open modal,
   plus focusing the first control on open.

8. **The stale-sources warning is buried (MEDIUM).**
   `sourcesAreStale()` produces a real, actionable warning ("Processed by an older version — click
   Reload all loaded sources…", line 1690) but only inside `#sourcebook-status`, which lives in
   **Settings → Advanced**. A user who never opens that sub-tab silently builds characters missing
   newer features (e.g. subclass choices). **Fix:** when sources are stale, also show it where the
   user already is — a one-line note near the Create button or a toast on load.

---

## Wizard & class builder

- **No step validation / no success toast** — see Top win #2. The `wiz-dots` ("Step N of 7", line
  3693) is the only progress affordance; there's no indication of which steps are required vs.
  optional, and the dots aren't clickable to jump.
- **"Create" vs "Save" label flip is subtle (LOW-MEDIUM).** On re-entry (Edit), the final button
  reads "Save" (line 3692) and re-runs `createCharacter`, which *re-applies* proficiencies, features,
  and limited resources. The function clears saves/skills first (line 4301) but **appends** features
  and adds inventory/gold again (lines 4351, 4355–4359, 4377) — editing an existing character can
  duplicate feature text, re-add starting gear, and re-stack gold. From the user's view, "Edit →
  Save" is lossy/duplicative, not an idempotent edit. This is a correctness-adjacent UX trap worth
  flagging to the logic reviewer; for UX, at minimum the button should warn that re-saving re-applies
  starting equipment.
- **Class detail panel cramped** — Top win #5.
- **Pending-decisions concept is reasonably legible.** The "(you can proceed without these)" header
  (line 3418) and the orange `.wiz-pend-row` styling read clearly, and inline subclass/option/ASI
  pickers resolve in place. Good. But **spell selection** pending rows are inert text ("on the Spells
  page", line 3417) with no link — unlike the subclass rows which are actionable. Consider making it
  a button that closes the wizard and switches to the Spells tab.
- **Multiclass prereq feedback is clear** (`renderClassDetail` shows "Requires Str 13 …" and disables
  Add, lines 3360–3363). Good. Minor: a *blocked* class still shows a disabled "Add" button rather
  than explaining inline above the fold — the error text is there (`.wiz-cd-err`) so this is fine.
- **Equipment step lets you pick "Equipment" but the chosen armor never becomes AC** — the root of
  Top win #1 surfaces here: the step's hint says items "expand into your Inventory" (line 4024) but
  never warns that armor still needs equipping to affect AC.
- **Race step "free assign" copy is a little confusing (LOW).** For ability-block-less races the hint
  says "(Or take three +1s instead — set them in the Ability Scores step's Racial column.)"
  (line 4123) — asking the user to remember to do something two steps later, by hand, in a different
  column, is fragile.

## Main sheet & flags

- **Two stacked pulsing orange banners (ASI flag + decisions flag, lines 698–699) can both be on at
  once (MEDIUM).** Both use the same `asi-flag` style with an infinite pulse animation (lines
  174–180). A new multiclass character with unspent ASIs *and* unchosen subclasses shows two large
  pulsing red-orange boxes simultaneously above the abilities — visually alarming and competing for
  the same click. `prefers-reduced-motion` is respected (line 181), good, but for everyone else two
  perpetual pulses is a lot. Consider merging into one banner with a count, or pulsing only the
  newest.
- **Flags are clear and actionable individually.** ASI flag → opens the ASI modal; decisions flag →
  reopens the builder at step 2 (line 4474). Good wiring. The ASI flag copy ("Click to choose an ASI
  (+2/+1+1) or a Feat for each", line 1504) is genuinely helpful.
- **`flashStatus` is the only transient feedback channel and it's tiny + brief.** 12px muted text in
  the toolbar, cleared after 1500ms (lines 3128–3130). Critical messages (portrait too large to
  autosave, line 3139; load failures) flash and vanish in 1.5s with no persistence — easy to miss.
  Consider longer timeouts or a dismissible variant for error-class messages.
- **Speed field click-to-edit-base is non-obvious (LOW).** `#speed` shows effective speed and on
  focus swaps to the editable base (lines 4463–4464); the only hint is a `title` tooltip (line 744).
  Users may not realize the displayed number is computed and the box is editable.

## Settings & source loading

- **Loading states are handled well.** Load/Load-all/Reload buttons disable themselves and show
  "Loading…/Reloading…" and restore on finally (lines 2331, 2344, 2356, 2370, 2375, 2389). Failures
  flash actionable messages ("…is your 5etools server running at <url>?"). This is the most polished
  part of the app.
- **Source loading is buried two tabs deep (MEDIUM).** The single most important setup action lives
  in Settings → **Advanced**, below Spell-sheet toggles. For a content-free shipped app where loading
  a book is step zero, this is the wrong altitude. Consider promoting Source books to its own
  top-level Settings tab (or the General tab) and/or the first-run banner (Top win #4).
- **Stale warning buried** — Top win #8.
- **Reset confirm is weaker than the surrounding copy promises (LOW-MEDIUM).** The Settings text says
  "This can't be undone, so Save a copy first if you want to keep this character" (line 1162), but the
  actual `confirm()` is just "Are you sure? This will delete your character." (line 4601) — it drops
  the "save first" guidance at the exact moment it matters. Mirror the richer warning into the confirm
  dialog.
- **"Clear loaded books" confirm is good** (line 2400) — explains the consequence and reassures the
  character is unaffected.

## Print & pen-and-paper

- **The print stylesheet is the standout feature** (lines 522–639): genuinely careful — every page on
  its own sheet, builder chrome hidden, textareas swapped for `.ta-print` content mirrors, blank
  write-in rows for armor/features, dropdown arrows stripped, placeholder text hidden. This is
  excellent and clearly hand-tuned.
- **Blank-sheet pen-and-paper mode works as advertised** — fresh sheet has no `0`/`+0` noise and
  write-in min-heights are sized for handwriting. Good.
- **Risk: "fits on one page" depends on content length (LOW-MEDIUM).** Core/Inventory are forced to
  `min-height:261mm` single sheets (lines 537, 542) with avid `break-inside:avoid` cards; a character
  with a long Proficiencies/Languages list, many attacks, or a big Resistances box can overflow the
  fixed Core layout. There's no on-screen print preview or warning. Acceptable, but worth noting the
  one-page promise is best-effort.
- **No print affordance beyond the toolbar button** — "Print / PDF" is clear enough; fine.

## Consistency & aesthetic

- **Flat/sharp adherence is good in practice.** The global override (lines 502–520) neutralizes all
  radius/shadow and converts tinted badges to hairline-bordered white. The leftover rounded/shadow
  declarations in base CSS are harmless but are dead code that could mislead a future editor into
  thinking the app is rounded — worth a comment or cleanup so the aesthetic intent is legible.
- **One genuine motion inconsistency:** the pulsing `box-shadow` animation on the flags (lines
  177–180) is the *only* place a shadow/glow exists, directly against the "no shadows/shading" rule.
  It's intentional attention-grabbing, but it's an aesthetic outlier; a flat alternative (solid
  border-color flash or a static solid-accent bar) would be more on-brand.
- **Terminology is consistent** (Initial class, Multiclass req, Limited Features, Under the hood).
  Toolbar button correctly flips Create ↔ Edit (line 3701).
- **Button-style sprawl via inline styles (LOW).** Many buttons carry ad-hoc inline
  `style="font-size:11px; padding:4px 10px"` (lines 952, 959, 1179–1180, etc.) instead of a `.btn.sm`
  modifier — minor maintainability/consistency smell, not user-visible.
- **Hit targets:** checkboxes are 16px (line 220), shrinking to 10px in print (fine). The inventory
  delete ✕ and container caret are tiny (lines 362, 365–366) and only appear on hover — discoverable
  only with a mouse; on touch they're nearly impossible to hit.

## Accessibility

- **No label associations** — Top win #6 (0 `for=` attributes; standalone `.lbl` are siblings).
- **No keyboard modal control / focus management** — Top win #7.
- **Color-only state encoding (MEDIUM).** Toggle-on chips/stats (Inspiration, death-save pips,
  proficiency) communicate state purely via accent-fill color (lines 207–208, 243–244, 517–520).
  Inspiration does add a ★/○ glyph (line 3145) — good — but the equip/toggle stats rely on color
  alone.
- **Page tabs are `<button>`s without `role="tab"`/`aria-selected`** (lines 656–664); functional but
  not announced as a tab set. The active page isn't communicated to AT beyond visual styling.
- **Generic alt text** — portrait `alt="portrait"` (line 672); fine but could be the character name.
- **Icon-only controls rely on `title` only** — ✕ close buttons, the ⚙ "Under the hood" button, inv
  ✕/caret. `title` isn't reliably exposed to screen readers or touch; `aria-label`s would help.
- **Focus styles exist** (`:focus{outline:2px solid …}`, line 86; flattened to border-color in the
  flat theme, line 506) — the flat theme replaces the outline with only a border-color change, which
  is a weaker, lower-contrast focus indicator. Keep a visible outline for keyboard users.

## Mobile/responsive

- **Wizard class builder doesn't collapse on narrow screens (MEDIUM).** `.wiz-build` stays a
  `170px 1fr` two-column grid at all widths (line 306) with no `@media` collapse, inside a 460px modal
  that on a phone becomes ~full-width-minus-32px. The class list + detail panel get badly squeezed;
  unlike Settings, which *does* stack its nav on `max-width:560px` (lines 288–293). Add a stacked
  layout for `.wiz-build` on narrow viewports.
- **Main layout responsiveness is otherwise solid** — `.columns`, `.combat-top`, `.coins`, `.encgrid`,
  `.meta-grid`, `.armor-attune`, `.inv-cols`, `.topblock`, `.settings-wrap` all have sensible
  breakpoints (lines 73, 113, 230, 259, 288–293, 358, 416, 481, 483).
- **Drag-to-reorder inventory + hover-only delete/equip controls are mouse-only (MEDIUM).** Inventory
  reordering uses HTML5 drag (lines 4437–4460) and the delete ✕ / equip box appear on `:hover`
  (lines 362–364, 1240) — none of this is reachable on touch. Equip in particular is load-bearing
  (it's how armor reaches AC), so touch users hit the Top-win-#1 dead-end with no escape at all.
- **Modal padding `48px 16px` (line 271)** on small phones eats vertical space; the wizard's inner
  scroll regions help, but the doubled stacked flags + cramped builder compound on small screens.

---

## Summary — highest-leverage UX improvements

- Fix the **armor→AC silent dead-end**: auto-equip and auto-select armor the wizard adds, or surface
  an on-sheet nudge — today a freshly-built armored character shows wrong AC with no clue why, and the
  fix is an undiscoverable 3-step cross-page chain (the Equip checkbox is even `display:none`).
- Add **wizard step validation + a success toast**: "Create" currently builds a class-less, nameless,
  broken character silently and closes the modal with no confirmation.
- Give **"Save" (download copy) visible feedback** — the headline portability feature currently
  appears to do nothing (no flashStatus, no dialog).
- Solve **first-run discoverability**: replace the disabled-button-tooltip-only signal with an on-sheet
  banner pointing to Settings → Source books when no data is loaded.
- **Promote Source loading** out of Settings → Advanced (two tabs deep) and **surface the stale-sources
  warning** where the user already is, not buried in the same deep tab.
- **Widen the wizard modal and collapse the class builder on mobile** — reading a 1–20 progression in a
  ~230×300px box, two-column even on phones, is the worst flow in the app.
- **Merge or de-stack the two perpetually-pulsing orange flags**; two simultaneous infinite pulses
  above the abilities is alarming and they compete for the same click.
- **Make modals keyboard-usable**: add an Escape-to-close handler and basic focus management (none
  exists except in the item search).
- **Associate the 30+ standalone labels** with their inputs (`for=`/wrapping) — clicking a label does
  nothing and AT can't pair them today; mechanical, high coverage.
- **Make touch a first-class citizen** for Inventory: hover-only delete/equip and drag-reorder are
  mouse-only, and equip is load-bearing for AC.
- **Mirror the "Save a copy first" guidance into the Reset confirm dialog**, which currently drops it
  at the one moment it matters.
- **Retire the lone pulsing box-shadow** (the only shadow/glow in an otherwise strictly flat app) in
  favor of a flat attention treatment, and clean up the dead rounded/shadow base CSS so the flat
  intent stays legible to future editors.
