# Round 1 — Explorer Agent Report

## Web Findings

- [Better Form Inputs for Better Mobile UX (CSS-Tricks)](https://css-tricks.com/better-form-inputs-for-better-mobile-user-experiences/): `inputmode="decimal"` is superior to `type="number"` on iOS — it shows the number pad without desktop spinners or swipe-increment issues; the sheet's HP/coin/stat fields all use `type="number"` today and could benefit. `enterkeyhint="done"` or `"next"` sets the keyboard action button label, reducing confusion at end of field.

- [Designing for Thumb Zones (Elaris, 2025)](https://elaris.software/blog/mobile-ux-thumb-zones-2025/): Green zone = bottom third of screen, slightly toward the dominant hand — that's exactly where a **bottom navigation bar** outperforms a top tab row. Current sticky-top `.pagetabs` puts 9 tabs in the hardest-to-reach zone. Minimum touch target: 44×44pt (Apple) / 48×48dp (Android); current `min-height:42px` on `.ptab` is borderline, no minimum width set.

- [Bottom Sheets: Definition and UX Guidelines (NN/G)](https://www.nngroup.com/articles/bottom-sheet/): Bottom sheets get 25-30% higher engagement than traditional modals. Non-modal sheets let users reference background content while interacting — ideal for "quick roll a die" or "look up a spell" overlays during play. Never stack sheets; always include a visible close button, not just a grab handle.

- [Mobile Data Tables UX (Design Bootcamp, Medium)](https://medium.com/design-bootcamp/designing-user-friendly-data-tables-for-mobile-devices-c470c82403ad): Show 3-4 columns max on mobile; tap row to expand full detail. The Inventory tab's dense multi-column table (name, qty, weight, equip, attune, container) is a classic overload case — a tap-to-expand row pattern would dramatically reduce scroll fatigue.

- [Modern CSS Viewport Units (modern-css.com)](https://modern-css.com/articles/modern-css-units-you-should-know/): `dvh` dynamically follows the browser chrome height in real time; `svh` = viewport with chrome fully visible (smallest). Full-height modals should use `min-height:100dvh` not `min-height:100%` — prevents the iOS Safari toolbar cutting off modal footers.

- [Mobile UX Thumb Zones 2025 (Parachute Design)](https://parachutedesign.ca/blog/thumb-zone-ux/): Progressive disclosure is the dominant pattern for dense apps — show the skeleton, expand details on tap. The sheet's Core page puts ability scores, skills, saves, attacks, HP, defenses, and equipment all on one scroll — a single page that on a 6" phone could be 15+ scrolls tall.

## Mobile D&D Sheet Landscape (what competitors do well/badly)

- **D&D Beyond mobile web**: Users complain the card/tab layout hides too much (requested "show full sheet" on tablets) and that the app and web versions are inconsistent. It uses a **bottom navigation bar** for the main sections (Actions, Spells, Features, etc.) not a top tab row — placing primary nav in the thumb zone. Their biggest win: each sub-section is a focused card with only relevant fields, not a scrolling dump.

- **D&D Beyond known failures**: Long sync delays between app and web; theme customizations (colors, backgrounds) don't carry to mobile; users explicitly ask for "full desktop sheet on tablet" — meaning they feel information is being hidden unnecessarily on medium screens. Lesson: don't over-collapse above ~600px, only under ~430px.

- **Roll20 mobile character sheet**: Roll20 docs confirm they have a separate mobile-optimized sheet experience; the community forum shows a long-standing request (2014!) to implement a mobile character sheet viewer that was never satisfactorily addressed — Roll20's mobile story is generally poor, but their lesson is that **a responsive web sheet beats a native app** when you don't have native app resources.

- **Fight Club 5 (iOS native app)**: Users praise the per-section tab view (Actions, Spells, Inventory as separate tabs), the large-hit dice buttons styled like physical dice, and quick-roll popups that don't navigate away from the sheet. Biggest lesson: **in-context roll results** (show a bottom sheet with the roll, don't pop a full modal) is the gold standard for table play.

- **5etools**: No dedicated mobile layout — it renders at desktop width on phones. Users work around it with desktop-mode + pinch-zoom. Lesson: lack of mobile support drives users away even when content depth is unmatched.

## No-Build Techniques Worth Stealing

- **`inputmode="decimal"` on numeric fields**: Replace `type="number"` for HP, AC, coin, stat fields. Gets the number pad on mobile without the spinners. One attribute change per input; trivially addable to the existing field definitions.

- **`enterkeyhint="next"` / `"done"`**: Adds a "Next" or "Done" label to the iOS/Android soft keyboard action button. For tabular fields (attack rows, inventory rows), `enterkeyhint="next"` and `tabindex` ordering makes data entry flow feel native. Zero build requirement.

- **`min-height:100dvh` on modals**: Replace `min-height:100%` in `.modal-panel` and `min-height:100%` on the modal itself with `100dvh`. Fixes the iOS Safari chrome-overlap bug where the bottom of a modal is hidden behind the toolbar. One CSS line change.

- **Inline PWA manifest via `<link rel="manifest" href="data:application/manifest+json,...">` + blob-URL service worker**: A single-file sheet can become installable ("Add to Home Screen") and offline-capable with ~30 lines of inline JS that programmatically creates a service worker via `URL.createObjectURL(new Blob([swCode]))`. No external files, no build step. The service worker caches the file itself from localStorage or caches the page on first load.

- **CSS `:has()` for contextual UI**: Now baseline in all modern browsers. Can show/hide UI contextually without JS — e.g., `.card:has(input:focus)` to visually highlight the active card section, or `.toolbar:has(.sheet-dirty)` to pulse the Save button when unsaved. No build, one CSS rule.

- **`touch-action: manipulation`** on buttons and interactive elements: Disables the 300ms double-tap delay on older iOS without any JS library. Currently absent from the sheet — add to `.btn`, `.ptab`, `.stepper .step`, checkboxes.

- **`contenteditable` with `inputmode`**: Some number fields (like current HP during combat) would benefit from a large single-tap target that opens a numeric keyboard. A styled `contenteditable` div with `inputmode="decimal"` can be visually larger than a cramped `<input>` in a grid.

- **CSS `@layer` + container queries**: Container queries (`container-type: inline-size`) would let cards reflow based on their own width rather than viewport width — meaning sidebar cards on a large phone landscape would behave differently from the same card in a narrow column. No build required, one CSS declaration per container.

- **`<dialog>` element**: The current modals use `.modal` divs with manual show/hide JS. Native `<dialog>` with `dialog.showModal()` gets free: `Escape` key dismissal, `::backdrop` pseudo-element for the scrim, focus trapping, and accessibility roles. Drop-in for the Create Character and Settings modals.

- **`overscroll-behavior: contain`** on the `.pagetabs` and modal-body scroll containers: Prevents the tab scroll from accidentally scrolling the background page (rubber-band bleed-through on iOS). One CSS property.

## Unexpected Angles

- **Banking / budget apps on mobile**: Apps like Monarch Money and YNAB solve the "dense numbers on small screen" problem by making every number a large tappable target that opens a dedicated edit screen (full-screen number pad, confirm button). For the D&D sheet, HP and spell slots could use this pattern — a single large number, tap opens a bottom sheet with `+/-` buttons and a direct-entry field, no tiny inline input.

- **Notion / Apple Notes on mobile**: Both use a floating toolbar that appears *above* the keyboard when a text field is focused. This is `position:fixed; bottom: calc(env(keyboard-inset-height, 0px) + 8px)` using the new `keyboard-inset-height` env var (Chrome 94+ / iOS 16+, not yet universal). Relevant for the Notes and Backstory tabs where users might type extended text.

- **Landscape mode at the game table**: Most D&D apps assume portrait. But phones propped on a table stand are often landscape. The sheet has no landscape-specific rules. At 390×844 (iPhone 14) rotated, the viewport is ~844×390 — the sticky `.pagetabs` takes ~50px of that 390px, leaving ~340px of content height. A landscape-specific rule that switches to a **left sidebar nav** (like the desktop layout) would dramatically help tablet/large-phone landscape users.

- **The flat/sharp design tension**: The sheet uses `--radius:12px` and `--shadow` throughout. Alex's documented UI taste is flat/sharp (square corners, hairlines, no shadows). On mobile, border-radius 12px on cards makes them feel "Material 3 / iOS" rather than intentional. The print stylesheet already does `border-radius:0 !important; box-shadow:none !important` — consider a mobile reset that tightens to `--radius:4px` (or 0) and drops the shadow to a hairline border. This would also be consistent with the Alex-preference-documented taste.

- **Spell slot tracking as a combat-session UI**: During actual play, the Spells tab's slot checkboxes are the most-tapped element. On mobile, these could become large pill-style toggles (CSS only, no JS) — much easier to tap with a thumb under the table. The `appearance:none` + `:checked` trick makes custom-styled checkboxes trivially large with zero JS.

## Suggested Follow-ups for Round 2

1. **Bottom nav vs. top tab row deep dive**: Specifically evaluate whether replacing the sticky `.pagetabs` with a bottom nav bar (fixed, 5 primary tabs + "more" overflow) is feasible given that there are 9 tabs. What's the right 5? What goes in "more"?

2. **iOS keyboard-avoidance audit**: When the soft keyboard opens on a focused field, iOS doesn't always scroll the field into view in a `position:sticky` tab + scrollable content layout. Verify this bug exists and find the CSS/JS fix (likely `scrollIntoView` on focus, or `Visual Viewport API`).

3. **HP / slot combat-mode overlay**: Design a "Combat Quick Panel" — a bottom sheet (non-modal) containing only Current HP, Temp HP, spell slot toggles, and death saves. Accessible from any tab during play. This is the Fight Club 5 killer feature and could be built with ~50 lines of vanilla JS.

4. **Inventory table mobile collapse**: Evaluate the tap-to-expand row pattern for the Inventory tab — what columns show inline (name, qty, weight) vs. expand on tap (equip, attune, container, notes)?

5. **PWA installability**: Draft the inline service worker + manifest code for a follow-up PR. 30-line implementation in vanilla JS that lives at the bottom of the `<body>`.

6. **Landscape breakpoint**: Add a `@media (orientation:landscape) and (max-height:500px)` rule that restores a condensed sidebar-nav version of the tab bar, reducing vertical chrome consumption.

---
**Timing**: Started Sun Jun  7 02:24:27 UTC 2026 · Finished Sun Jun  7 02:25:22 UTC 2026
