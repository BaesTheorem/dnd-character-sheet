# r1-critic.md — Critic Agent, Round 1

## Prior Art

**iOS Safari localStorage eviction (ITP):** Apple's Intelligent Tracking Prevention,
introduced in Safari 13.1 (iOS 13.4, 2020), caps all script-writable storage at a
rolling 7-day window of non-use. If the user does not open the page within any 7-day
period — say, between sessions 7 days apart — Safari silently wipes localStorage,
IndexedDB, Service Worker registrations, and media keys. This is not a bug; it is
intentional privacy policy. It has not been removed or softened since introduction.
WebKit bug 209563 is marked WONTFIX. Beyond ITP, Safari also applies LRU eviction
under storage pressure — a phone with low free space will drop the least-recently-used
origin's data first. Combined quota limit is up to 20% of total disk for embedded apps.

**Service workers and `file://`:** The Fetch and Service Worker specs both require a
secure context (HTTPS or `localhost`). A page opened from the filesystem via
`file://` cannot register a service worker — the registration call returns a rejected
promise immediately. This is documented by MDN, confirmed by every browser vendor, and
has never changed. A single HTML file opened from Files.app, emailed, or AirDropped is
a `file://` document. There is no workaround short of serving it from a local HTTP
server, which defeats the "no build, no server" constraint.

**Mobile D&D sheet prior art and complaints:** The dominant pain points cited across
D&D Beyond forums, Roll20 community posts, and third-party app reviews (2024-2025)
cluster around: (a) sync failures between mobile and desktop losing live-game edits;
(b) tab/section navigation being cumbersome on phone-sized screens; (c) apps that
haven't caught up to 2024 rules. The one complaint that does NOT appear: players
frustrated by inability to _edit_ fields mid-combat. The frustration is navigation and
data loss — not read-mode friction. This is a relevant prior-art signal for the
Play/Edit mode proposal.

---

## Assumptions Under Examination

**Proposal 1 — Play/Edit mode split**
- *Assumes* most fields are static during play (set once, never changed mid-session).
- *Assumes* users will correctly learn which mode to be in, and won't be confused when
  a field appears non-interactive.
- *Assumes* this can be implemented as a lightweight CSS/JS toggle without restructuring
  the save/load pipeline.
- *Assumes* Print/PDF behavior is unaffected, since print is mode-agnostic.

**Proposal 2 — Bottom nav bar replacing swipe-tabs**
- *Assumes* 3-4 tabs cover the high-frequency access pattern (likely Core + Spells +
  maybe Inventory; the others are session-infrequent).
- *Assumes* overflow "..." is low-friction for the minority tabs.
- *Assumes* a bottom bar works visually and spatially in the 820px-gated additive block
  without disturbing the desktop layout.

**Proposal 3 — Combat Quick Panel / persistent status strip**
- *Assumes* HP, slots, AC, and death saves together are worth the vertical real estate
  of a persistent strip.
- *Assumes* the strip can be purely read-display (no editing there) without confusing
  users about where edits actually happen.

**Proposal 4 — PWA / inline manifest**
- *Assumes* a blob-URL or data-URI approach can host a service worker.
- *Assumes* "installable" is achievable from a self-contained HTML file.
- *Assumes* offline-first is a meaningful improvement over the current model (the sheet
  already works offline — it's a static HTML file).

**Proposal 5 — Progressive disclosure (cards/rows expand on tap)**
- *Assumes* the Core page density is the primary pain point, not its organization.
- *Assumes* collapsed-by-default rows don't hide data the user needs at a glance during
  play.

**Proposals 6 & 7 — Quick wins / visual polish**
- *Assumes* `dvh`, `touch-action:manipulation`, `overscroll-behavior`, and flat/sharp
  radius changes are safe-area-neutral and print-safe.

---

## Strongest Objections

### Objection A — localStorage is not a safe character store on iOS; the "Save HTML" escape hatch is worse than it sounds

iOS Safari will silently delete any localStorage-backed character if the user hasn't
opened the sheet for 7 days. For a player who runs a campaign roughly bi-weekly, this
means a 50% chance of data loss after every other session if they rely solely on
autosave. Under storage pressure it can happen sooner. The proposed PWA / service
worker approach does _not_ solve this: service worker registration is itself a form of
script-writable storage and is subject to the same 7-day ITP sweep (WebKit confirmed
this in the same policy announcement). The escape hatch — "Save to HTML file" — is
real, but on iOS the workflow is: tap Save → Safari presents a download dialog → file
lands in iCloud Drive or Downloads → user must understand they need to re-open _that
specific file_ next time, not the bookmark. In practice, most casual users will bookmark
the most recently-opened version, not navigate to the downloaded file. The result is a
class of data loss that feels random from the user's perspective ("my character
disappeared") because the 7-day counter resets silently and gives no warning. Proposing
PWA as a mitigation is not just insufficient — it actively misleads the designer into
believing the problem is solved when it is not. The _only_ robust mitigations are either
persistent export guidance (auto-download after every session-end, with an explicit
"your character lives in this file" onboarding), or switching the primary save target to
a format that isn't subject to ITP (e.g., the downloaded HTML file _is_ the source of
truth, opened fresh each session).

### Objection B — Play/Edit mode split is a framework-sized feature hiding behind "just a CSS toggle"

The framing as a simple mode switch understates what vanilla-JS dual-state actually
requires. Every editable `<input>` or `<textarea>` that must become a display `<span>`
in Play mode needs: (1) a display element alongside or replacing it, (2) logic to keep
the display in sync with the live input value (the sheet already uses a
debounced-autosave pattern, but syncing to a display span is a different concern — it
must update on every keystroke or become stale), (3) re-entry logic when toggling back
to Edit mode, (4) care around computed fields (ability modifiers, spell save DC, passive
perception) that are already `<span>` outputs from `compute()` — those work fine, but
the raw input values backing them (base scores, proficiency bonus overrides) also need
display treatment. Multiply by 25+ distinct field types across 9 tabs plus modals. This
is not a sprint; it's a refactor of the HTML skeleton. Furthermore, it directly fights
the "additive-only" constraint that allows the mobile CSS block to lift cleanly into the
desktop sheet: adding dual-state HTML can't be done in a `@media` block — it changes the
DOM. The print stylesheet, which currently relies on `textarea { display:none }` and
`.ta-print { display:block }` pairs (an already-fragile dual-element pattern), would
need a third state. Any mistake — a field that doesn't sync on mode transition, a
computed span that diverges from the input on partial edit — introduces silent data
corruption that only surfaces when the player exports the HTML or reopens the sheet.
The Wikipedia read/edit analogy flatters the proposal; Wikipedia's edit mode touches one
field at a time in isolation. This sheet has ~200 interdependent fields with live
computed cross-dependencies.

### Objection C — Bottom nav hides 5 of 9 sections and the 5 hidden ones include gameplay-critical content

The proposal pins Core, Spells, and 1-2 more to a bottom bar and puts the rest behind
"...". But Inventory (tracking equipment/weight), Features (class abilities, limited-use
tracking), and Companions are all consulted during active play — arguably more so than
Background or Backstory, which are the obvious overflow candidates. Any choice of 4
pinned tabs either leaves a gameplay-critical tab in overflow (bad) or makes the
distinction arbitrary enough that users will need to hunt. The current swipe-tab row
already addresses the thumb-reach problem adequately for a 9-tab set: it is sticky,
horizontally scrollable, and the active tab auto-scrolls to center. The incremental
ergonomic gain of a bottom bar is real but modest. The cost — hiding tabs, restructuring
the tab DOM to support two visual representations (top swipe on desktop, bottom bar on
mobile) — is non-trivial and risks confusing desktop users if the 820px boundary isn't
perfectly maintained. D&D Beyond's bottom nav is also frequently criticized for hiding
content; it is not obviously a success that validates the pattern for a 9-section sheet.

### Objection D — The visual tension (flat/sharp vs. 12px radius + shadows) is a real debt, but fixing it globally is a print regression risk

The sheet currently uses `--radius:12px` and `--shadow:0 1px 2px ... / 0 4px 16px ...`
everywhere. Alex's flat/sharp taste calls for 0 radius and no shadows. The print
stylesheet already strips shadows via `:root{ --shadow:none }` and doesn't care about
radius. Changing radius and shadow variables in the root is safe for print. However, if
the fix is implemented as a mobile-only override in the `@media (max-width:820px)` block
— which is the additive-only approach — it means the desktop sheet retains the old look
indefinitely, creating a visual divergence between the two files that will need to be
reconciled when the mobile block is eventually folded in. If it's fixed globally (root
variables), it changes the desktop sheet now. Neither path is free. The right move is
probably to fix it globally in both files at once, but that is explicitly not a "mobile
polish" task — it's a design system change that should be deliberate and reviewed.

---

## Vulnerabilities

| Idea | Core weakness | Cheapest mitigation |
|---|---|---|
| Play/Edit mode | Every field needs dual-state in vanilla JS; breaks additive-only rule | Scope to HP/slots/conditions only (3-5 steppers); leave all other fields always-editable |
| Bottom nav bar | 5 tabs in overflow including gameplay-critical ones | Don't do a bottom bar; improve swipe-tab with larger min-width tabs and a subtle scroll-shadow fade hint |
| Combat Quick Panel | Persistent strip eats vertical space; duplicates Core tab data | Implement as a slide-up bottom sheet (hidden by default, tapped up from a persistent handle), not always-visible |
| PWA/manifest | Service workers cannot register from `file://`; ITP wipes SW registration anyway | Skip. Add explicit "save HTML after each session" prompt with localStorage last-save timestamp as trigger |
| Progressive disclosure | Collapsed-by-default hides data needed at-a-glance during play | Use expand-on-tap only for rarely-consulted sub-sections (companion stat blocks, spell descriptions, feat full text), never for live-combat fields |
| Quick wins (dvh, touch-action, etc.) | `100dvh` can cause content to be obscured by browser chrome on some Android browsers; needs testing | Use `100svh` (small viewport) as safer fallback; `touch-action:manipulation` is safe everywhere |
| Flat/sharp visual fix | Global change alters desktop sheet; mobile-only change creates divergence | Fix globally, do it once deliberately, get it behind you before adding further mobile features |

---

## What Survives Scrutiny

1. **`inputmode`/`enterkeyhint`** — pure additive attributes, zero risk, immediate
   benefit on every form field. No print impact. Zero complexity.

2. **`touch-action:manipulation`** — disables double-tap zoom on interactive elements
   without changing font sizes or layout. Safe for print (ignored). One CSS line per
   button/input selector.

3. **`overscroll-behavior:contain`** on the pagetabs row and modals — prevents accidental
   page navigation when swiping. Already scoped to the mobile block pattern.

4. **`100svh` / `100dvh` for modals** — the sheet already uses `min-height:100%` on
   modal panels inside a full-viewport overlay. Switching the overlay to `100dvh` is
   likely harmless but should be tested on Android Chrome specifically; fall back to
   `100svh` if bottom chrome obscures content.

5. **Scoped "big stepper" HP/slots UI in Play mode** — not the full mode split, but
   a dedicated HP-stepper widget and spell-slot trackers (which may already exist in
   some form given `stepper .step` in the mobile CSS) are high-value for live play and
   low-complexity if scoped to those 5-6 fields only.

6. **Flat/sharp global cleanup** — safe for print (shadow already removed in `@media
   print`; radius doesn't affect print output). High visual payoff for Alex's taste
   with minimal code change. Best done as a deliberate one-time pass.

7. **Persistent localStorage warning + export nudge** — not a visual feature, but
   critical for data safety. Add a one-time banner (or session-end reminder) that reads
   the last-save timestamp and warns if it's been >5 days since the user downloaded
   an HTML copy.

---

## Cheapest 80%

**High value / low risk — do these:**

1. `inputmode="numeric"` / `enterkeyhint="done"` on number fields and textarea fields.
   One pass through the HTML. No JS. No print impact. (1-2 hours)

2. `touch-action:manipulation` on `.btn`, `.ptab`, checkboxes, steppers. One CSS
   addition in the mobile block. (30 minutes)

3. `overscroll-behavior:contain` on `.pagetabs` and `.modal`. One CSS addition. (15
   minutes)

4. Flat/sharp global fix: `--radius:0` (or 2-3px for legibility), `--shadow:none`.
   Change two root variables. Test print. Done. (1 hour)

5. **localStorage safety UX**: on load, check if `localStorage.getItem(KEY)` timestamp
   is older than 5 days since last HTML export (store export timestamp separately).
   Show a non-blocking banner: "Last backup: N days ago — tap Save to download a copy."
   This is the single highest-stakes feature for data integrity. (2-3 hours)

**Medium value / medium risk — do these second:**

6. HP/slot stepper widget: visible from Core tab on mobile only, large tap targets,
   directly modifies the existing save fields. Scope tightly. (4-6 hours)

7. Progressive disclosure for spell descriptions and feat full-text (which are already
   long and overflow on mobile). Expand-on-tap detail panels on existing rows. (3-4
   hours per section)

**Avoid for now:**

- Full Play/Edit mode split (months of work; fights additive-only rule)
- Bottom nav replacing swipe-tabs (modest ergonomic gain; hides content)
- PWA/service worker (technically blocked by `file://`; ITP voids the benefit)
- Combat Quick Panel as always-visible strip (eats screen space; defer until after
  stepper widget validates the pattern)

---

## Unanswered Objections

**Objection 1 — There is no safe-without-UX-change way to store a character on iOS.**

localStorage on iOS is not a reliable primary store for a character someone has built
over weeks. The only reliable store is the downloaded HTML file itself. But the current
UX asks the user to click "Save" and then _remember_ to re-open the downloaded file
rather than the bookmarked URL next time. This is an architecture problem, not a CSS
problem. No amount of mobile polish addresses it. The objection has no clean mitigation
within the current "single file, no server" constraint — the user either accepts data
loss risk, changes their workflow (open from file every time), or the sheet ships a
server component. None of these are answered by the current proposal set.

**Objection 2 — The print stylesheet is a load-bearing second application inside the same HTML, and every structural mobile enhancement risks breaking it.**

The `@media print` block is 120+ lines of overrides that reconstruct a dense one-page
layout from the interactive sheet — restoring two-column grids, hiding nav chrome,
replacing textareas with `.ta-print` spans, sizing boxes to 19px to match ability
score display, and so on. It is already fragile: it depends on specific class names,
element ordering, and the absence of extra wrapper elements. Any structural change to
support Play/Edit mode (new wrapper divs, new span-mirror elements), any bottom bar
that adds a fixed-position element, or any progressive-disclosure wrapper around
inventory rows will require corresponding print-stylesheet surgery. There is no way to
assess the full print impact of proposals 1-5 without actually printing after each
change. The proposals treat print as a pass-through concern. It is not.

---

**Timing**: Started Sun Jun 7 02:27:36 UTC 2026 · Finished Sun Jun 7 02:30:12 UTC 2026
