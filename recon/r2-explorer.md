## P0 Quick Wins — paste-ready

### 1. `inputmode` + `enterkeyhint` on numeric fields

**What and why.** The sheet already uses `type="number"` on all numeric inputs (HP, coins, spell slots, ability scores, inventory qty, hit dice). `type="number"` on iOS shows a modified QWERTY keyboard with a number row — not the dedicated numpad. Adding `inputmode="numeric"` (integers) or `inputmode="decimal"` (weights, fractional values) forces the true number-pad. Critically, `inputmode` does NOT disable non-numeric character entry or trigger spinner arrows in Chrome, so it is strictly additive and safe. The `pattern="[0-9]*"` attribute amplifies the effect on older iOS/Android.

`enterkeyhint` sets the action-key label on the software keyboard (`"done"` closes the keyboard, `"next"` jumps to the next field). For isolated stat fields like HP, `done` is correct; for fields in a row (coin denominations, ability scores), `next` keeps the flow.

**Which fields get which:**

| Fields | inputmode | enterkeyhint |
|---|---|---|
| `#hpmax`, `#hpcur`, `#hptmp`, `#hd-total`, `#hd-used` | `numeric` | `done` |
| `#pp`, `#gp`, `#ep`, `#sp`, `#cp` | `numeric` | `next` |
| `#slot1` through `#slot9`, `#slot1u` through `#slot9u` | `numeric` | `next` |
| `#invqty-N` | `numeric` | `next` |
| `#invwt-N` (weight, can be fractional) | `decimal` | `next` |
| `.ab-score`, `.ab-bonus` (ability scores/bonuses) | `numeric` | `next` |
| `.hp-roll` (HP by level, wizard modal) | `numeric` | `next` |
| `#speed` (text input, but numeric content) | `numeric` | `done` |

**Exact CSS/HTML approach** — add to the `@media (max-width:820px)` block (keeps desktop untouched):

```css
/* @media (max-width:820px) block — append after existing rules */
input[type="number"],
input[id="speed"] {
  inputmode: numeric;         /* CSS form of the attribute — ignored by browsers; use JS below */
}
```

CSS cannot set HTML attributes, so use a 3-line JS snippet in the mobile `<script>` block (the one already guarded by `mq.matches`):

```js
// Add inside the existing (function(){ ... DOMContentLoaded ... })() mobile script:
if (mq.matches) {
  // Integer fields
  document.querySelectorAll(
    '#hpmax,#hpcur,#hptmp,#hd-total,#hd-used,' +
    '#pp,#gp,#ep,#sp,#cp,#speed,' +
    '.ab-score,.ab-bonus,.hp-roll,' +
    '[id^="invqty-"],[id^="slot"]'
  ).forEach(function(el) {
    var isDecimal = el.id && el.id.startsWith('invwt');
    el.setAttribute('inputmode', isDecimal ? 'decimal' : 'numeric');
    el.setAttribute('pattern', '[0-9]*');
    el.setAttribute('enterkeyhint', 'done');
  });
  // Weight fields (decimal)
  document.querySelectorAll('[id^="invwt-"]').forEach(function(el) {
    el.setAttribute('inputmode', 'decimal');
    el.setAttribute('enterkeyhint', 'next');
  });
}
```

**iOS caveat.** `inputmode="decimal"` on iOS shows a numpad WITH a decimal point. `inputmode="numeric"` shows a numpad WITHOUT a decimal point. On Android, `numeric` shows 0-9 with no sign or separator; `decimal` adds "." and "-". Never use `type="tel"` as a workaround — it shows a phone dialpad without a minus sign and breaks negative values.

The existing `input[type=number]{appearance:textfield}` rule already suppresses spinner arrows on desktop. No conflict.

---

### 2. `touch-action: manipulation` — kill 300ms tap delay

**What.** Browsers inject a ~300ms delay on tap to check for double-tap-to-zoom. `touch-action: manipulation` disables double-tap zoom (but keeps pinch-zoom), eliminating the delay. It is the correct, standards-based fix — faster than the old `fastclick.js` hack and no JS required.

**Where to scope it.** Apply broadly but inside the media query so it doesn't affect a desktop mouse (no functional harm there, but unnecessary):

```css
/* Inside @media (max-width:820px) */
*, *::before, *::after {
  touch-action: manipulation;
}
```

This covers all buttons, tabs, checkboxes, pips (death saves), and stepper buttons in one rule.

**iOS caveat.** iOS Safari 13+ respects this. On iOS, `touch-action: none` would break scrolling; `manipulation` is the safe choice. If the sheet ever adds a canvas or drag-to-reorder it may need `touch-action: pan-y` on those elements specifically, but for the current sheet this is unambiguous.

---

### 3. `overscroll-behavior: contain` on `.pagetabs` and modal bodies

**What.** Without this, a finger-swipe that reaches the end of the tab row (or the bottom of a modal's scrollable body) triggers rubber-band scrolling on the underlying page — the whole page bounces behind the modal. `overscroll-behavior: contain` stops scroll chaining at that element's boundary.

**Exact additions to the `@media (max-width:820px)` block:**

```css
/* After the existing .pagetabs rules */
.pagetabs {
  overscroll-behavior-x: contain;   /* tab row scrolls horizontally; chain-stop at both ends */
}

/* After the existing .modal-body rules */
.modal-body {
  overscroll-behavior: contain;
}
```

**iOS caveat.** `overscroll-behavior` is supported in Safari 16+ (iOS 16+, released September 2022). For Safari 15 and below (a small tail of iOS 15 devices) the property is silently ignored — the rubber-banding happens but nothing breaks. No `@supports` guard needed; degradation is cosmetic.

---

### 4. `dvh`/`svh` units for modals

**What.** The existing mobile modal rule is:

```css
.modal-panel, #wizard .modal-panel, .settings-panel {
  max-width: none;
  min-height: 100%;   /* ← this is the problem line */
  border: 0;
}
```

`min-height: 100%` resolves to 100% of the fixed `.modal` container (which is `position:fixed; inset:0`), so it works — but the container itself is sized to `100vh`, which on iOS Safari is computed to the full viewport height EXCLUDING the browser chrome (address bar). When the address bar is visible, a `100vh` element is taller than the usable area and the bottom is clipped. `svh` (small viewport height = viewport with chrome fully visible) guarantees the sheet never underlaps the address bar.

**Exact CSS change inside `@media (max-width:820px)`:**

```css
/* Replace the existing modal mobile rule */
.modal {
  padding: 0;
  align-items: stretch;
}
/* Use @supports to upgrade to svh where available (Safari 15.4+, all modern mobile) */
.modal-panel,
#wizard .modal-panel,
.settings-panel {
  max-width: none;
  min-height: 100%;       /* fallback: resolves from the fixed container */
  border: 0;
}
@supports (height: 1svh) {
  .modal,
  .modal-panel,
  #wizard .modal-panel,
  .settings-panel {
    min-height: 100svh;   /* svh: viewport with address bar visible — always fits */
  }
}
```

**Why `svh` not `dvh` here.** `dvh` is dynamic — it recalculates as the address bar hides/shows and can cause the modal to resize mid-scroll, which is jarring. `svh` is the conservative "always fits" unit, correct for a full-screen modal overlay.

**iOS caveat.** `svh`/`dvh`/`lvh` are supported in Safari 15.4+ (iOS 15.4+, April 2022). This covers virtually all active iOS devices. The `@supports (height: 1svh)` guard handles the rare iOS 15.0-15.3 tail gracefully, falling back to the existing `100%` behavior.

---

### 5. Flat/sharp visual direction — exact CSS variable change

**The current values (lines 19-20):**
```css
--radius: 12px;
--shadow: 0 1px 2px rgba(16,24,40,.04), 0 4px 16px rgba(16,24,40,.05);
```

**The flat/sharp target:**
```css
--radius: 0px;    /* or 2px for a hairline softness — strictly designer call */
--shadow: none;
```

The print stylesheet at line 534 already has `*{border-radius:0 !important; box-shadow:none !important}` — so print is already flat. The question is whether to gate the screen change behind `html.mobile` / `@media` or go global.

**Recommendation: make it global, not mobile-only.**

Rationale: the print stylesheet already demonstrates that the visual direction looks right without radius/shadow. On desktop the round-cornered cards with a soft shadow are fine but not load-bearing — they don't affect print. Making it global means one change, no media query gymnastics, and the result is visually consistent across all screen sizes. The flat/sharp aesthetic reads well at any resolution.

**Exact change — edit the `:root` block (lines 19-20):**

```css
:root {
  /* ... existing vars ... */
  --radius: 2px;   /* near-zero; keeps a hairline for anti-aliasing; use 0px for pure square */
  --shadow: none;
  /* ... */
}
```

Also add to `@media (max-width:820px)` to knock out any hard-coded `border-radius:8px` values that bypass the variable (there are several at lines 48, 65, 84, 121, etc.):

```css
/* @media (max-width:820px) — override all hard-coded radii */
*, *::before, *::after {
  border-radius: 0 !important;
}
```

**iOS caveat.** None. CSS variables are safe everywhere. The `!important` override in the media query is the same pattern the print stylesheet already uses.

---

## Durability (high-stakes) — options + recommended

### The threat model (confirmed by research)

localStorage and IndexedDB on iOS Safari are subject to the same eviction unit — when an origin is evicted, ALL its storage is wiped together. The ITP 7-day rule (Safari deletes all scripted data for an origin with no user interaction in 7 days of browser use) applies to BOTH localStorage and IndexedDB equally. `navigator.storage.persist()` is approved by WebKit only for Home Screen Web Apps (saved PWAs) and even then the 7-day rule still applies in some configurations. `showSaveFilePicker` does not exist on iOS Safari at all (WebKit ships only the Origin Private File System). There is no purely in-browser solution that achieves true file-system durability on iOS.

**Summary of options:**

| Option | Durability | Complexity | iOS status |
|---|---|---|---|
| Status quo (localStorage autosave) | Evictable, ITP-7-day | 0 | Works, lossy |
| IndexedDB instead of localStorage | Identical eviction behavior | Medium refactor | Same risk, no gain |
| `navigator.storage.persist()` | Partial (H-S apps only); 7-day still applies | Low | Safari 17+ only; auto-denied in browser |
| `showSaveFilePicker` auto-save | True file durability | Medium | Not supported on iOS |
| On-change auto-download (blob URL) | True file durability | Low | Works everywhere |
| Web Share API (`navigator.share({files})`) | User-initiated copy to Files | Low | iOS 15+ for file sharing |
| Stale-data banner + "Export now" nudge | Soft durability (user-prompted) | Very low | Works everywhere |

### Recommended: two-layer approach

**Layer 1 (mandatory, ~30 min): Last-saved staleness banner**

Track when the character was last exported (not just autosaved to localStorage). On init, if the character exists in localStorage but has no `lastExported` timestamp — or if `lastExported` is more than 24 hours ago — show a dismissible banner above `.pagetabs`:

```html
<!-- Insert in the HTML, right before <nav class="pagetabs"> -->
<div id="stale-banner" class="stale-banner noprint" hidden>
  ⚠ Not backed up in <span id="stale-age"></span> — <button id="stale-export" class="btn">Export file</button> <button id="stale-dismiss" class="btn ghost">×</button>
</div>
```

```css
/* In @media (max-width:820px) */
.stale-banner {
  position: sticky;
  top: 0;
  z-index: 16;       /* above .pagetabs (z-index:15) */
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 13px;
  background: #fef3c7;
  border-bottom: 1px solid #f59e0b;
  color: #92400e;
}
```

```js
// In the mobile script block:
var EXPORT_KEY = KEY + '_lastExported';
function checkStaleness() {
  var charData = null;
  try { charData = localStorage.getItem(KEY); } catch(e) {}
  if (!charData) return;                           // no character, no banner
  var lastExported = 0;
  try { lastExported = parseInt(localStorage.getItem(EXPORT_KEY) || '0', 10); } catch(e) {}
  var age = Date.now() - lastExported;
  var threshold = 24 * 60 * 60 * 1000;            // 24 hours
  var banner = document.getElementById('stale-banner');
  if (!banner) return;
  if (age > threshold) {
    var ageHours = Math.round(age / 3600000);
    var ageStr = ageHours < 48 ? ageHours + 'h' : Math.round(ageHours / 24) + ' days';
    document.getElementById('stale-age').textContent = ageStr;
    banner.hidden = false;
  }
  document.getElementById('stale-export').addEventListener('click', function() {
    document.getElementById('btn-savecopy').click();  // reuse existing Save export
    localStorage.setItem(EXPORT_KEY, String(Date.now()));
    banner.hidden = true;
  });
  document.getElementById('stale-dismiss').addEventListener('click', function() {
    banner.hidden = true;
  });
}
// Call after DOMContentLoaded + init:
checkStaleness();
```

Also update `lastExported` in the existing `btn-savecopy` click handler (line 5139):
```js
// After the existing download() call in btn-savecopy handler:
try { localStorage.setItem(KEY + '_lastExported', String(Date.now())); } catch(e) {}
```

**Layer 2 (optional enhancement, ~15 min): auto-download after N minutes of changes**

For players who forget to manually save, a background timer that triggers a silent download after N minutes of unsaved changes (e.g., 15 min) is a realistic last resort. iOS Safari WILL fire an automatic `<a download>` trigger from a setTimeout if the user previously interacted with the page — it is not treated as a popup. The risk is annoying users with unexpected downloads. Gate it behind a user preference in Settings (off by default).

```js
var _autoExportTimer = null;
var _autoExportEnabled = false;  // wire to a Settings toggle
var AUTO_EXPORT_DELAY = 15 * 60 * 1000;

function scheduleAutoExport() {
  if (!_autoExportEnabled) return;
  clearTimeout(_autoExportTimer);
  _autoExportTimer = setTimeout(function() {
    document.getElementById('btn-savecopy').click();
    try { localStorage.setItem(KEY + '_lastExported', String(Date.now())); } catch(e) {}
  }, AUTO_EXPORT_DELAY);
}
// Call scheduleAutoExport() from queueSave() or from any field change handler
```

### iOS Safari specifics — hard limits

- `navigator.storage.persist()`: Silently auto-denied in Safari browser. Only auto-approved for Home Screen Web Apps (saved to home screen). Even then, ITP 7-day proactive eviction still fires under some configurations. **Do not rely on this.**
- `showSaveFilePicker`: Not implemented on iOS/iPadOS at all. Chrome and Firefox mobile also lack it. **Dead on mobile.**
- Web Share API (`navigator.share({files: [blob]})`): Works on iOS 15+ for sharing a file to Files app, Mail, AirDrop, etc. This is a valid "save to a real location" option but is purely user-initiated and requires a tap. Could replace or augment the staleness banner CTA.
- Auto-download via blob URL + `<a download>`: Works on iOS Safari, but iOS may route the download to the Files app "Downloads" folder rather than prompting. This is fine — it is persistent storage. The user sees it in Files. **This is the most reliable durability mechanism available on iOS without a server.**

### Bottom line

The single-file "your data lives in the downloaded HTML" pattern is already architecturally correct. The gap is that users don't download often enough. The staleness banner (Layer 1) is the highest-leverage, lowest-risk P0 addition. The auto-export timer (Layer 2) is a good P1 opt-in.

---

## Reality Check

### Minimal combat-glance affordance — lightest viable option

The constraint: additive-only, no mode-split, print-safe, currently on ANY tab.

**Option A (recommended): pinned compact status strip**

A narrow, always-visible strip below `.pagetabs` that mirrors HP/Temp HP/death-save pips from the DOM — read-only display, tapping it scrolls to the Core tab. It is purely presentational (no new data-save fields), is `noprint`, and requires ~25 lines of CSS + ~20 lines of JS.

```css
/* @media (max-width:820px) */
.combat-strip {
  position: sticky;
  top: 42px;         /* below the ~42px pagetabs row */
  z-index: 14;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 5px 12px;
  font-size: 13px;
  font-weight: 600;
  background: var(--card);
  border-bottom: 1px solid var(--line);
  cursor: pointer;   /* tap navigates to Core tab */
}
.combat-strip .cs-hp   { color: var(--accent); }
.combat-strip .cs-ds   { font-size: 11px; color: var(--muted); letter-spacing: .05em; }
```

```js
// In the mobile script, after DOMContentLoaded:
function buildCombatStrip() {
  if (!mq.matches) return;
  var strip = document.createElement('div');
  strip.className = 'combat-strip noprint';
  strip.id = 'combat-strip';
  strip.setAttribute('title', 'Tap to go to Core');
  strip.innerHTML =
    '<span class="cs-hp" id="cs-hp">HP —</span>' +
    '<span class="cs-tmp" id="cs-tmp"></span>' +
    '<span class="cs-ds" id="cs-ds"></span>';
  strip.addEventListener('click', function() {
    var coreTab = document.querySelector('.ptab[data-page="core"]');
    if (coreTab) coreTab.click();
  });
  var pagetabs = document.getElementById('pagetabs');
  if (pagetabs) pagetabs.after(strip);
  updateCombatStrip();
}

function updateCombatStrip() {
  var cs = document.getElementById('combat-strip');
  if (!cs) return;
  var cur  = document.getElementById('hpcur');
  var max  = document.getElementById('hpmax');
  var tmp  = document.getElementById('hptmp');
  var hpStr = (cur && cur.value ? cur.value : '—') + ' / ' + (max && max.value ? max.value : '—');
  document.getElementById('cs-hp').textContent = 'HP ' + hpStr;
  var tmpEl = document.getElementById('cs-tmp');
  tmpEl.textContent = (tmp && tmp.value) ? ('THP ' + tmp.value) : '';
  // Death saves: count filled pips (class 'on')
  var successes = document.querySelectorAll('[data-save-id^="dss"].pip.on').length;
  var failures  = document.querySelectorAll('[data-save-id^="dsf"].pip.on').length;
  var dsEl = document.getElementById('cs-ds');
  if (successes || failures) {
    dsEl.textContent = 'DS ' + '●'.repeat(successes) + '○'.repeat(3 - successes) +
      ' / ' + '●'.repeat(failures) + '○'.repeat(3 - failures);
  } else {
    dsEl.textContent = '';
  }
}

// Hook updateCombatStrip into the existing queueSave / input change path:
// Simplest: add a MutationObserver on #hpcur, #hptmp, or just call it from the existing
// save() function (it runs after every field change anyway):
//   In save() → at the end: updateCombatStrip();
```

**Note on death-save pip selectors:** the exact class structure for `.pip.on` needs to match the rendered pip HTML (line 1512-1515). Adjust the selector to `#ds-success .pip.on` and `#ds-fail .pip.on` once confirmed.

**Why not a "Combat" bottom sheet?** A bottom sheet requires a collapse/expand toggle and some kind of state (open/closed), is another thing to accidentally tap, and still requires reading all 9 tabs' worth of screen at the same time. The strip is zero-decision-surface — it just shows the 3 values and lets the player keep working in any tab.

**Why not promoting the existing HP/slot widgets?** They are already large on mobile (52px min-height `stat` boxes, `font-size:16px`). The problem is they are only visible on the Core/Spells tab. The strip solves cross-tab visibility without duplicating controls.

**Print safety.** The strip carries `.noprint` which is already excluded from `@media print` via `display:none !important` at line 562. Zero print impact.

---

### Landscape at the table

No landscape `@media (orientation: landscape)` exists in the file. The current `@media (max-width:820px)` block fires for a phone in landscape at 812px wide (iPhone Pro) — barely under the breakpoint — but at 844px (iPhone 13 Pro) the phone in landscape exits the mobile block entirely and gets the full desktop layout, which is probably fine (plenty of pixels).

The practical at-table landscape scenario is the phone lying flat or propped in a stand. Two real issues:

1. **Sticky pagetabs eat vertical space.** In landscape, the tab bar is ~42px and the combat strip another ~32px, leaving maybe 320px of usable content height. This is already acceptable for the Core stat fields (HP/AC/slots are compact). No action required — it just works.

2. **Sticky toolbar is currently `position:static` on mobile** (line 690: `.toolbar{ position:static; ... }`). In landscape the toolbar flows above the pagetabs and scrolls off. That is the right call — landscape real estate is vertical, not horizontal. No change needed.

3. **Phone-on-stand (portrait, propped).** The strip + tabs sticky-row consumes ~80px at the top. The rest of the page is one continuous scroll. This is exactly the intended use pattern — the player glances at the strip without touching the phone, then taps to Core when they need to update HP. No additional accommodation needed.

**Recommendation.** Skip a landscape-specific media query. The existing layout works. If in a future pass there is budget, a `@media (max-height: 480px) and (orientation: landscape)` could hide the strip (since the Core tab is more likely to be active in a purposeful landscape session), but this is P3 at best.

---

## Suggested specifics for the final plan

**P0 (~1 day, additive-only, zero print/desktop risk):**
1. `inputmode` + `pattern` + `enterkeyhint` — 3-line JS snippet inside mobile `<script>` block
2. `touch-action: manipulation` — 3-line CSS inside `@media (max-width:820px)`
3. `overscroll-behavior: contain` on `.pagetabs` and `.modal-body`
4. `svh` modal height with `@supports` fallback
5. Flat/sharp CSS variable edit to `:root` (`--radius: 2px; --shadow: none`) + `border-radius: 0 !important` inside media query
6. Staleness banner + `lastExported` tracking hooked into existing `btn-savecopy` handler

**P1 (~0.5 days each):**
7. Pinned combat-status strip (`#combat-strip`, `noprint`, taps to Core, mirrors HP/THP/death saves)
8. Auto-export timer (off by default, Settings toggle, 15-min of unsaved changes triggers silent download)

**P2 (future, needs design time):**
9. Web Share API CTA in the staleness banner for iOS users (share the HTML file to Files/AirDrop)
10. Landscape `@media (max-height:480px)` pass if player demand warrants it

**One clarification needed before P0 ships:**
- The death-save pip selector for `updateCombatStrip()` — confirm exact class name on `.pip.on` rendered by the pips() function (line 1512). The pip function at line 1512-1515 renders `<button>` or `<input type="checkbox">` — whichever it is, the strip query needs to match. Read that 3-line pips() block before wiring.

---

**Timing**: Started Sun Jun  7 02:33:19 UTC 2026 · Finished Sun Jun  7 02:35:30 UTC 2026
