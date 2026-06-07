## Combat Widget / Status Strip — concrete spec

### What it is

A compact, always-on cluster of the five high-churn values — Current HP, Temp HP, Spell Slots (highest-active level only), Limited Feature uses (top row), and Death Saves — rendered as large-touch steppers or pip-rows. It is NOT a full Play/Edit mode split. It is a floating card that appears *above* the page content when the user is on any tab, and collapses when the user taps the header.

### Where it lives in the DOM

Inserted as a sibling immediately **below** `<nav class="pagetabs" id="pagetabs">` and above `<section class="page active" id="page-core">`, so the stacking order from top of screen is:

```
[ sticky .pagetabs tab row       ]   z-index:15 (existing)
[ #combat-widget (sticky)        ]   z-index:14  ← new
[ page content (scrolls under)   ]
```

The widget is `position:sticky; top: <pagetabs height>px` so it travels with the tab row but scrolls out of the way with the page if you choose to dismiss it (via a collapse chevron). Because `.pagetabs` is already `sticky top:0`, the widget pins itself to `top: 50px` (the measured height of the tab row at mobile width) so there is no gap.

### Layout — portrait (375px wide phone)

```
┌─────────────────────────────────────────────────────┐
│ ▸ Combat  [AC 16]  [Prof +3]  [Insp ★]        [∧] │  ← collapsed bar (30px tall)
└─────────────────────────────────────────────────────┘
```
Tapping anywhere on the bar expands it:
```
┌──────────────────────────────────────────────┐
│  HP  [−]  [  14 / 28  ]  [+]     TMP [  0  ]│
│  L3 slots  ● ● ○ ○   L2  ● ● ● ○           │
│  Rage  3/3  ● ● ●   Ki  4/10  ● ● ● ● ○... │
│  Death  ✓ ○ ○  ✕ ○ ○                        │
│                                   [collapse ∧]│
└──────────────────────────────────────────────┘
```
- HP row: a large centered number (`font-size:22px; font-weight:800`) flanked by 44px `−`/`+` buttons. The denominator `/ 28` is muted, not editable here (Max HP rarely changes mid-combat).
- Temp HP: a single inline number input (tap to edit, no steppers needed — it's set once per rest).
- Spell slots: one pip-row per slot level that is non-zero on the sheet. Each pip is a 20x20 tap target — filled circle = expended, hollow = available. Tapping a pip toggles `slot{N}u` (the existing `data-save` input with id `slot1u` through `slot9u`). Labels are `L1`–`L9` at 9px. Only levels with `slot{N}` > 0 are rendered.
- Limited features: first three rows from the `#limited` tbody (`lfname-0/lfmax-0/lfused-0` through `lfname-2`). Pip row capped at 10 pips; overflow shown as `+4`. Tapping a pip increments/decrements `lfused-N`.
- Death saves: the existing `#ds-success` / `#ds-fail` pip containers re-used via `innerHTML` mirroring (see mechanism below).

### Landscape behavior

At `@media (orientation:landscape) and (max-width:820px)`, display the expanded widget as a **2-column grid** (HP + Temp HP left; slots right) to use the extra width instead of tall-stacking. Height budget: 90px max, so it doesn't eat more than 30% of a 320px-tall landscape viewport.

### Lightest mechanism — no double-source-of-truth

The widget does NOT store any state of its own. Every stepper/pip directly mutates the existing `data-save` inputs by id, then calls `save()` and (for HP / slots) re-renders the widget pips from those same inputs.

Implementation sketch (pure additive JS, appended to the mobile `<script>` block):

```js
(function(){
  var mq = window.matchMedia("(max-width:820px)");
  if(!mq.matches && !mq.addListener) return; // only inject on mobile

  // Build widget markup once; wire to existing inputs.
  function buildCombatWidget(){
    var w = document.createElement("div");
    w.id = "combat-widget";
    w.className = "noprint";
    w.innerHTML = /* template — see full spec below */;
    document.getElementById("pagetabs").insertAdjacentElement("afterend", w);
    wireCombatWidget();
  }

  function wireCombatWidget(){
    // HP +/- buttons mutate #hpcur directly
    document.getElementById("cw-hp-dec").addEventListener("click", function(){
      var el = document.getElementById("hpcur");
      el.value = Math.max(0, (+el.value||0) - 1);
      el.dispatchEvent(new Event("input", {bubbles:true})); // triggers onChange→save()
    });
    document.getElementById("cw-hp-inc").addEventListener("click", function(){
      var el = document.getElementById("hpcur");
      var max = +(document.getElementById("hpmax").value||0);
      el.value = Math.min(max, (+el.value||0) + 1);
      el.dispatchEvent(new Event("input", {bubbles:true}));
    });
    // Slot pips: tapping pip i of level L increments slot{L}u up to slot{L} max
    // Death-save pips: re-render from ds-success/ds-fail innerHTML after any click on the main deathsaves widget
    // Limited feature pips: mutate lfused-N
  }

  function refreshCombatWidget(){
    // Called from applyLayout() and after any onChange that touches the relevant fields.
    // Reads hpcur, hpmax, hptmp, slot1..slot9, slot1u..slot9u, lfname-0..lfmax-0..lfused-0..
    // Rewrites only the display elements inside #combat-widget (not the source inputs).
  }

  document.addEventListener("DOMContentLoaded", function(){
    if(!mq.matches) return;
    buildCombatWidget();
    refreshCombatWidget();
    // Hook into existing onChange by observing the inputs we care about.
    ["hpcur","hpmax","hptmp"].forEach(function(id){
      var el = document.getElementById(id);
      if(el) el.addEventListener("input", refreshCombatWidget);
    });
    // Slot and limited-feature inputs are rendered dynamically, so use event delegation:
    document.getElementById("slots").addEventListener("input", refreshCombatWidget);
    document.getElementById("limited").addEventListener("input", refreshCombatWidget);
  });
})();
```

The key constraint: `el.dispatchEvent(new Event("input", {bubbles:true}))` re-uses the existing `onChange` handler from the main script (line 3470 `function onChange(e)`) so `queueSave()` and `compute()` fire exactly as they do for any direct field edit. No second data path.

### CSS (mobile-only, additive)

```css
@media (max-width:820px){
  #combat-widget{
    position:sticky;
    top:50px; /* pagetabs height — empirically correct or via JS offsetHeight */
    z-index:14;
    background:var(--bg);
    border-bottom:1px solid var(--line);
    padding:6px 10px;
    margin:0 -10px 10px;
    font-size:13px;
  }
  #combat-widget.collapsed{ padding:4px 10px; }
  #combat-widget .cw-row{ display:flex; align-items:center; gap:8px; margin:2px 0; }
  #combat-widget .cw-hp-val{ font-size:22px; font-weight:800; min-width:36px; text-align:center; }
  #combat-widget .cw-step{
    width:44px; height:44px; border:1px solid var(--line2); background:var(--field);
    font-size:22px; cursor:pointer; display:flex; align-items:center; justify-content:center;
  }
  #combat-widget .cw-pip{
    width:20px; height:20px; border-radius:0; /* flat/sharp: square pips */
    border:2px solid var(--accent); display:inline-block; cursor:pointer; flex:none;
  }
  #combat-widget .cw-pip.filled{ background:var(--accent); }
  #combat-widget .cw-lbl{
    font-size:9px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
    color:var(--muted); min-width:24px;
  }
  #combat-widget .cw-toggle{ /* collapsed bar */
    display:flex; align-items:center; gap:12px; font-size:11px; font-weight:700; cursor:pointer;
  }
  #combat-widget .cw-toggle .cw-ac{ font-size:16px; font-weight:800; }
}
@media print{ #combat-widget{ display:none !important; } }
```

Note: `border-radius:0` on pips is the flat/sharp taste signal — no rounded blobs. The existing death-save pips on the sheet are round by default; the combat widget overrides to square for visual distinction.

### Print interaction

`display:none !important` in the print block (already shown above). This is already the right move: the widget is a play-time tool, not a sheet layout element, and `#page-core` contains all the same data printed normally. No special work needed.

### Where the analogy breaks / risks

1. **`top:50px` hardcode is fragile.** The `.pagetabs` row grows taller if it wraps (e.g. with Overflow tabs). The correct fix is a one-time JS measurement: `document.getElementById('combat-widget').style.top = document.getElementById('pagetabs').offsetHeight + 'px'` on load and on resize. Without this, the widget can underlap or overlap the tab row.

2. **Slot pip rendering for multiclass / extra sheets.** `slot1u` through `slot9u` are for sheet 0 (the built-in Spells page). A multiclass character with a second spell sheet (`sx(1,'slot1u')` = `"1-slot1u"`) has separate slots not covered by this widget. The widget should only render slots for instance 0 unless explicitly extended.

3. **Limited feature rows are dynamically built** by `refreshLimitedFeatures()`. The widget must call `refreshCombatWidget()` after that function runs, not just on `input`. The cleanest hook is adding one line to the end of `refreshLimitedFeatures()`: `if(typeof refreshCombatWidget === 'function') refreshCombatWidget();`

4. **Vertical space budget.** On a 667px phone (iPhone SE), the sticky tab row + combat widget in expanded state can consume 140px+ of a 667px screen, leaving ~520px for content. That is acceptable but only if the widget defaults to collapsed on non-Core tabs (where the user has already navigated away from Combat concerns).

---

## Content-Dot Tabs — concrete spec

### What it is

A 5px colored dot rendered below the text label of a `.ptab` whose page has at least one non-empty field. Existing `.ptab.muted{opacity:.45}` already exists and is used by `applyLayout()` for structurally absent pages (no portrait, no companion). The dot is additive and separate: it marks **content presence**, not structural relevance.

### CSS

```css
@media (max-width:820px){
  .ptab{ position:relative; }  /* anchor for the dot */
  .ptab::after{
    content:"";
    position:absolute;
    bottom:4px; left:50%; transform:translateX(-50%);
    width:5px; height:5px;
    background:var(--accent);
    opacity:0; transition:opacity .15s;
  }
  .ptab.has-content::after{ opacity:1; }
  /* Active tab already stands out — optionally suppress the dot on active */
  .ptab.active::after{ opacity:.4; }
}
```

Flat/sharp: `border-radius` omitted (defaults to 0) for square dot, consistent with the combat widget pips.

### Trigger logic — which fields mark which tab

The check is "does this page have anything worth knowing?" — not "has any input been touched." Use a single function `updateContentDots()` called from `applyLayout()` (which is already the layout authority, called after every structural change and from `compute()` downstream).

```js
function updateContentDots(){
  var map = {
    inv:  function(){ return hasAnyInvRow() || !!($("equipment")&&$("equipment").value.trim()); },
    feat: function(){ return !!($("features")&&$("features").value.trim()); },
    spells: function(){
      // any spell entry, or any slot total set
      for(var l=1;l<=9;l++){ var s=$("slot"+l); if(s && +s.value > 0) return true; }
      var se = spellEntriesByInst && spellEntriesByInst[0];
      return !!(se && Object.values(se).some(function(arr){ return arr && arr.some(function(e){ return e.name && e.name.trim(); }); }));
    },
    companion: function(){ return companions && companions.length > 0; },
    bg: function(){
      return ["personality","ideals","bonds","flaws","bg-allies","bg-enemies"].some(function(id){
        var el = $(id); return el && el.value.trim();
      });
    },
    story: function(){ var el=$("backstory"); return !!(el && el.value.trim()); },
    notes: function(){ var el=$("notes"); return !!(el && el.value.trim()); },
    mini:  function(){ return false; }  // mini tab is portrait-dependent; structural mute handles it
  };
  Object.keys(map).forEach(function(key){
    var tab = document.querySelector('.ptab[data-page="'+key+'"]');
    if(tab) tab.classList.toggle("has-content", !!map[key]());
  });
}
```

`hasAnyInvRow()` already exists in spirit (the sheet knows NINV and checks `invname-N` for emptiness in several places); inline it as checking `invname-0` through `invname-19` for any non-empty value.

**Wiring:** Add one call to `updateContentDots()` at the end of `applyLayout()`. That function is called from `compute()`, which fires on every `onChange`, so dots update live as the user types.

**Core tab deliberately excluded.** The Core tab is always populated (it holds the character name etc.) and is always the landing tab; a dot there is noise, not signal.

**Spells tab on a non-caster.** A Barbarian has no spells and `slot1` through `slot9` all at 0. The check above returns false, so no dot. If the tab is also `.muted` (structurally absent), the dot is doubly suppressed.

### Where the analogy breaks / risks

1. **Inventory-row detection is O(NINV) per applyLayout call.** If NINV = 50 (the sheet supports up to 50 rows), this is 50 DOM reads every keystroke. Mitigation: cache a boolean `invHasContent` that is updated only inside the inventory-specific onChange path (when `e.target.id` matches `invname-*`).

2. **Dynamic overflow/extra spell sheets.** Overflow tabs and extra spell-sheet tabs are appended dynamically by `appendOverflowPage()` / `appendSpellSheet()`. The `updateContentDots` map above doesn't cover them. Add a second pass after the map loop that handles `overflow-N` and `N-spells` tabs using the existing `overflowPageUsed(k)` and `spellSheetUsed(i)` helper functions — they already determine if those pages have content, so re-use them rather than duplicating the logic.

3. **The dot is invisible on the active tab** (muted to 0.4 opacity in the CSS above). This is intentional — the active tab is highlighted; adding a dot creates visual noise. But a strict reading of "content present" would show it. Either choice is defensible; the muted-opacity version is the lesser noise.

4. **Does not distinguish "empty" vs "a single default value."** A Wizard who types their class name into the spellcasting class dropdown has "content" in Spells by the structural sense, but `slot1` through `slot9` might still be 0. The function above checks only slot totals and spell names, not the class/ability dropdowns, which is the right threshold — those dropdowns are setup, not play-time content.

---

## Persistent Status Strip — concrete spec (and how it relates to / merges with the combat widget)

### Relationship to the combat widget

The R1 spec proposed two separate things: (a) a *persistent* strip of static-ish values (AC, HP, Inspiration, Prof Bonus) that stays visible everywhere; and (b) a *combat widget* of high-churn editable values. In R2 these collapse into **one element with two states**: the *combat widget collapsed bar* IS the persistent status strip.

When collapsed, the widget shows: `AC [16]  HP [14/28]  Inspiration [★]  Prof [+3]` — all the values the R1 spec proposed for the "glance up-right" strip. When expanded, the same bar gains steppers, pips, and limited-feature rows. The user never sees two separate sticky elements eating two separate chunks of vertical space.

### Collapsed bar — concrete DOM and CSS

The collapsed bar is the `#combat-widget.collapsed` state defined in the Combat Widget spec above. Its layout:

```
[ ▸ Combat ]  [ AC 16 ]  [ HP 14/28 ]  [ ★ ]  [ +3 ]       [∧ expand]
  cw-toggle    cw-ac      cw-hp-sum    cw-insp  cw-prof      cw-expand
```

- `cw-ac` reads `#ac-calc` textContent (a `.calc` div populated by `compute()`). It is display-only.
- `cw-hp-sum` reads `#hpcur` and `#hpmax`. Display-only in collapsed state; becomes a stepper row when expanded.
- `cw-insp` reflects `inspState` (the boolean maintained by the main script). Tapping it calls `$("inspiration").click()` to re-use the existing toggle handler (line 5066), which handles `renderInsp()` and `save()`.
- `cw-prof` reads `#pb` textContent. Display-only (proficiency bonus is computed, not edited directly).

All four are read-only displays of values already maintained by `compute()` in the main script. The widget's `refreshCombatWidget()` function reads them with `document.getElementById("ac-calc").textContent`, etc. No new state.

### When to show/hide the collapsed bar

Default: always visible on mobile (`max-width:820px`), collapsed, for all tabs. A tiny `[∧]` / `[∨]` chevron on the right edge toggles expanded vs collapsed. State is persisted to `localStorage` under a key like `cw_expanded` so the preference survives page reload. The widget does NOT auto-expand on tab switch (that would be annoying); user intent drives expansion.

On the Core tab: the combat stats are already visible in the page content below. The strip is redundant when you can see the actual Combat card. Mitigation options:
- Option A: hide the strip when Core tab is active (via `showPage()` hook — add `combatWidgetEl.classList.toggle('cw-hidden', page === 'core')`).
- Option B: keep it always visible but make it ultra-thin (one row, 28px, opacity reduced slightly) on Core.
Option A is cleaner and saves the space.

### Portrait vs landscape

Portrait: collapsed bar = 30px, expanded = up to 140px (same as combat widget spec above).
Landscape: collapsed bar = 28px fixed. Expanded uses a 3-column grid (HP | Slots | Limited+Death) capped at 90px total, same as combat widget landscape spec.

### Print

`display:none !important` in `@media print`. The combat card on the printed Core page already contains all these values.

### Where the analogy breaks / risks

1. **AC is computed, not stored.** `#ac-calc` is set by `compute()` dynamically. The strip must re-read it after every `compute()` call, not just on `input`. Because `refreshCombatWidget()` is called from event delegation on the relevant inputs AND from `applyLayout()`, and `compute()` always runs in `onChange` → `queueSave(); compute()`, the strip's AC display will lag by one `requestAnimationFrame` at most. In practice `compute()` completes synchronously, so a simple call to `refreshCombatWidget()` at the end of `compute()` (or at the end of `onChange`) keeps it live.

2. **Proficiency bonus `#pb`** is also computed text, same caveat as AC.

3. **Inspiration toggle double-binding.** The strip calls `$("inspiration").click()` to toggle inspiration, which fires the existing click handler. That handler calls `save()` and `renderInsp()`. The strip then reads `inspState` in its own `refreshCombatWidget()`. Because `refreshCombatWidget()` is wired to fire on the `inspiration` element's click as well, this creates a call order: click → renderInsp → save → refreshCombatWidget. No infinite loop because the strip tap triggers `$("inspiration").click()` not a second `refreshCombatWidget()` directly.

4. **Vertical real estate on small screens.** A 30px collapsed bar + 50px tab row = 80px consumed before content on a 667px viewport (iPhone SE). That leaves 587px, which is fine. But if a user has expanded the widget AND is on a short landscape screen (568px height), the widget can consume 40% of the viewport. Mitigation: in landscape, cap expanded height at 90px with internal scroll for limited-feature overflow.

5. **The "glance up-right" paper-sheet reflex does not directly translate.** On paper, AC is physically top-right because the sheet has no scroll. On mobile with a sticky strip, AC is always top-center — the positional memory is different. Users learn a new reflex, not the old one. This is fine for the mobile-native experience but means the strip's value is "always visible" rather than "spatially where you expect it."

---

## Single best P1 candidate (ranked, with reason)

### Ranking

1. **Content-Dot Tabs** — P1 winner
2. **Combat Widget / Persistent Status Strip** (unified collapsed+expanded) — P2
3. No third candidate (the two above subsume all three R1 survivors into two implementable units)

### Why Content-Dot Tabs is P1

**Build cost: ~25 lines of JS + ~10 lines of CSS.** The hardest part is the field-to-tab mapping table, which is a static object written once and never maintained. There are no new DOM elements beyond a CSS `::after` pseudo-element — no new HTML, no event wiring beyond one call added to `applyLayout()`.

**Correctness risk: near zero.** The function reads existing field values; it cannot break existing functionality because it only adds a CSS class. Rolling it back is one `querySelectorAll('.ptab').forEach(t => t.classList.remove('has-content'))`. No state to migrate, no save-format change.

**User value per line of code: very high.** Every session, every player on every character benefits from seeing at a glance which tabs have content. It directly addresses the "I keep tapping Companions thinking I set one up" and "I forgot I wrote notes" failure modes. The tabbed-binder thickness analogy is the most direct translation to pixels.

**The Combat Widget is higher value per session — but higher build cost.** The expanded widget requires careful event-delegation wiring for dynamically-built limited-feature rows and spell slots, the `top` offset measurement to stay in sync with the tab row height, and the collapse/expand state persistence. It also introduces the most significant layout-regression risk (sticky elements stacking unexpectedly). It is clearly P2 once content dots ship and provide proof-of-concept for the additive mobile enhancement pattern.

---

## Disanalogies & risks (cross-cutting)

- **Tabbed-binder dot vs. a real binder.** A physical binder's "thickness" signal is proportional — a thick section is obviously thicker than a thin one. A binary dot gives only presence/absence. Two improvements sacrifice no simplicity: (a) a 3px dot for "has some content" vs 6px for "has significant content" (e.g. >5 inventory items, >10 spells); (b) omit the dot entirely for structurally excluded tabs (already handled by `.muted`). Binary presence is the right P1 form; richer signaling is a P2 enhancement if it proves insufficient.

- **Fitness-tracker cockpit → combat widget: the "glance" assumption.** Cockpit MFDs are designed for eyes that can stop and look at a dedicated panel. A D&D player's phone is on the table, they glance down, then look back up at the DM. The expanded combat widget is only useful if it fits in a single glance — meaning all five high-churn values must fit in a 90–140px band without scrolling. The design above achieves this in portrait, but ONLY if limited features are capped at 3 rows in the expanded view (with a `+N more` link to open the full page). A character with 10 limited features will overflow the widget's purpose.

- **Double-source-of-truth risk summary.** The combat widget avoids its own state entirely by treating the existing `data-save` inputs as the canonical store and the widget as a rendering skin. The only risk point is the `input` event dispatch: if any other listener responds to `hpcur`'s `input` event and re-reads the widget's pip count before the widget refreshes, there is a one-render-frame gap. This is imperceptible to users and resolves itself on the next `onChange` cycle. It is not a data-loss risk.

- **`position:sticky` inside a flex/grid container.** The `.sheet` div has `margin:0 auto 16px; padding:0 10px` on mobile. Sticky children inside a flex column work in modern iOS Safari (15+) but fail in Safari < 14 if the sticky element's parent has `overflow:hidden`. The existing `.pagetabs` already uses `position:sticky` successfully, so the precedent is established and the container is safe.

- **Print safety of both features.** Content dots are CSS `::after` pseudo-elements hidden by `display:none !important` in `@media print`... except `::after` pseudo-elements on buttons are suppressed via `display:none` on the button itself (`.ptab.muted` isn't explicitly hidden in print, but `.pagetabs{display:none !important}` hides the whole nav). No print regression. The combat widget explicitly has `display:none !important` in the print block.

---

**Timing**: Started Sun Jun  7 02:33:28 UTC 2026 · Finished Sun Jun  7 02:37:14 UTC 2026
