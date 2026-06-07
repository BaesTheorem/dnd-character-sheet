# R1 — Associator: Cross-Domain Bridges for the Mobile D&D Sheet

Cognitive style: lateral. Goal: name non-obvious analogies that each suggest a concrete, implementable design move. Each analogy is accompanied by where it holds and where it cracks.

---

## Cross-Domain Bridges

- **Fitness tracker (Fitbit Charge face) ↔ mobile sheet's Core tab.**
  A fitness tracker is worn *during* activity and displays the one number you need right now (heart rate, step count) in a glanceable, non-editable view. You swipe to reach secondary screens (sleep, floors, calories). The Core tab on this sheet behaves oppositely: it is a dense form — 30+ editable fields, all simultaneously live — even though during a D&D session the only numbers that change frequently are Current HP, Temp HP, spell slots used, and limited-feature pips. The concrete move: add a **Play mode** toggle (or dedicated "Combat" tab) that renders those four live fields as large, finger-friendly steppers (+/- buttons) while keeping all other fields read-only display text. *Where the analogy breaks:* a fitness tracker can afford to be nearly write-locked because it writes via sensors, not thumbs. A character sheet needs opportunistic editing for any field (a DM might grant a stat bump mid-session). The play view should therefore not hard-lock fields — it should just promote the high-churn ones and demote the rest behind a single tap to "edit this field."

- **Fantasy-sports lineup app (DraftKings, Sleeper) ↔ the Attacks + Limited Features cards.**
  Lineup apps present a compact "active roster" of 6-8 players with a single key stat per row (projected points), designed to be skimmed and swapped fast with one thumb. That is structurally identical to what a player does during combat: scan the attacks table for the right weapon, glance at limited-feature pips to see if Rage is available. Both apps use **large stat callouts + muted labels**, not labeled form fields. The concrete move: render the Attacks table and Limited Features table in a wider-touch, condensed "combat card" style — bigger hit-bonus number, big Used/Max fraction, the label shrunk to 9-10px uppercase — instead of the current uniform-field table layout. Put a "Rest" button at the bottom of the card to reset all SR/LR features in one tap. *Where it breaks:* a lineup app's data is read-only during the contest; here the fields must still be editable (you might add an attack mid-session). The card needs to be readable *and* tappable-to-edit, not a static display.

- **Mobile banking app's "account overview" ↔ the sheet's nine tabs.**
  Banking apps (Chase, Wells Fargo mobile) solve the same "many data categories, tiny screen" problem with a bottom nav of 4-5 icons + a "More" overflow. The icons represent the *actions you take most often* (Balance, Pay, Transfer, Deposit), not an exhaustive category list. The sheet currently shows all 9 tabs equally in a single scrollable row (Core, Inventory, Features, Spells, Companions, Background, Backstory, Notes, Mini). Most play sessions only touch 2-3 of them (Core, Spells/Features, Notes). The concrete move: **pin a bottom nav of 3-4 high-frequency tabs** (Core, Spells, a configurable "Quick" slot defaulting to Features) and push the remaining 5+ tabs into a "..." overflow drawer. This shrinks the swipe target to reachable thumb distance and stops the cognitive overhead of hunting through 9 tiles. *Where it breaks:* banking nav icons are universal (everyone uses Balance); D&D players vary — a martial character never opens Spells. The pinned tabs should be user-configurable per character, probably set in the existing Settings modal.

- **Index-card / GM screen ↔ the Mini tab's paper-standee concept.**
  A GM screen is a physical object optimized for *fast reference* — key rules on the DM side, evocative art on the player side. It is used at the table, in 3D space, as a stand-alone artifact. The Mini tab already captures this spirit by generating a fold-over paper standee from the portrait. But the screen analogy suggests the back face of the standee could carry the character's most-referenced combat stats (AC, passive Perception, speed, current HP pencil-line) printed in a readable size — the equivalent of the DM's reference panel but pointed at the player. The concrete move: extend the Mini tab's SVG/CSS layout to include a **stat sidebar** on the standee back panel (the region already flipped 180° for reading when folded) with AC, Speed, and Passive Perc auto-populated from the sheet's saved values. *Where it breaks:* HP changes every fight so a printed number is stale by round 2. Limit the standee's stat panel to static values (AC, Speed, Passive Perc, Initiative modifier) and leave HP to pencil.

- **Wikipedia article in "Read" vs "Edit" mode ↔ every field on the sheet.**
  Wikipedia (and most wikis/CMSes) makes a hard binary distinction: the default state is *read* — formatted, glanceable prose — and edit is opt-in via a button that replaces the view with a raw textarea. This prevents accidental edits and reduces visual noise in the read state. The mobile sheet has no such distinction: every field is always an `<input>` or `<textarea>`, which on mobile means 16px minimum font, blue focus rings, keyboard invocations, and the constant risk of an errant thumb changing a value. For a sheet used live at the table, the read:write ratio is roughly 20:1 for most fields. The concrete move: implement a **global Play/Edit toggle** in the sticky tab bar. In Play mode, all non-high-churn fields render as `<span>` display text (preserving their values); tapping any span promotes it inline to an input for that one edit. In Edit mode, the current always-editable layout is restored. This also solves accidental-overwrite risk on a crowded table. *Where it breaks:* the inline-promote-to-edit pattern requires JS to swap span↔input per field and keep the underlying data model in sync — more complex than a simple class toggle, though not architecturally hard.

---

## Physical-Artifact Lineage

- **Paper D&D character sheet ↔ the sheet's "Core" tab layout.**
  The canonical WotC paper sheet is a dense 8.5×11 grid designed for *pencil* use: the writer's hand naturally rests below the writing point, there is no zoom-fatigue, and you can scan across the whole sheet in one glance. The mobile sheet's Core tab replicates this density because it inherits the same data model, but a phone forces vertical scroll and eliminates peripheral vision. What paper does that the mobile sheet does not: the *spatial memory* of "HP is always top-right, skills are always left column." On a scrolling phone tab, spatial memory degrades because the top-right might be off-screen. Concrete move: keep the Core tab as the edit-everything layout, but give it a fixed **"status strip"** pinned above the tab bar (AC | HP cur/max | Inspiration | Proficiency bonus) that stays visible regardless of scroll position. This replicates the "glance at the top-right" reflex from the paper sheet.

- **Tabbed binder / section dividers ↔ the 9-tab navigation.**
  A physical D&D binder has tabbed dividers (Combat, Spells, Background, etc.) and you flip to a section by feel/position after a few sessions. The phone's swipeable tab row approximates this, but binder dividers also telegraph *how full* each section is (a thin vs thick section). Nothing on the current tab row signals whether a page has content — the "Spells" tab looks identical whether the character is a Wizard with 50 spells or a Barbarian with zero. The existing `.ptab.muted{opacity:.45}` class exists but the code applies it to pages excluded by the character build, not pages with no content. Concrete move: add a **content-present dot** (2px dot below the tab label, accent color) to any tab whose page has non-empty data. This lets you see at a glance "I have spells, I have notes, companions are empty" without tapping each tab.

---

## Productive Metaphors

- "The mobile sheet is to a D&D session as a **cockpit MFD (multi-function display)** is to a flight." The pilot is not reconfiguring the plane mid-flight; they are *monitoring* a small set of live parameters and occasionally intervening. The MFD surfaces the most critical values large and prominent, buries the configuration menus, and never forces a mode switch just to read a number. This illuminates why always-editable fields are wrong for play-time: the cognitive cost of "is this field in edit or display state?" is eliminated in the cockpit because state is always display unless the pilot actively pushes a button. Design move: a persistent *play/configure distinction*, with the Play state being the dominant, lower-friction mode.

- "The spell slots grid is to spell management as a **boarding pass barcode** is to a flight." The boarding pass communicates one piece of information (gate, seat, boarding group) in a glanceable, high-contrast format to someone who is moving quickly and cannot stop to read carefully. The current spell slots grid (9 columns, each with two number inputs labeled "Total" and "Used" in 7px font in print, around 9px on screen) requires focused attention to parse. Illumination: slot *consumption* during play is the action, not slot *configuration*. Design move: render used-slots as **filled/unfilled pip rows** (like the existing death-save pips but for each spell level), reserving the numeric inputs for the Setup/Edit mode. Tapping a pip crosses it off; long-pressing opens the numeric edit.

- "The sheet's 9 tabs are to navigation as **a restaurant menu with 9 categories** is to ordering." Menus with more than 5-6 categories reliably cause decision fatigue and slower ordering. Restaurants that optimize for fast casual (Chipotle, Five Guys) solve this by flattening the menu to its essence and hiding complexity behind "customize." Design move: the tab bar should show at most 4-5 tabs at full opacity; the rest are accessible but visually subordinated (the `.ptab.muted` opacity class already exists and just needs to be applied to low-priority tabs).

---

## Strongest Connections (ranked)

1. **Play/Edit mode split** (fitness tracker + Wikipedia read/edit). Most actionable because it addresses the single biggest usability gap for live-table phone play: the always-on keyboard risk and cognitive noise of 30+ editable fields when you only need to change 3. Implementation is a class toggle + span↔input swap, feasible in the existing no-build single-file architecture. Aligns with Alex's flat/sharp aesthetic (display spans are cleaner than constant input borders).

2. **Bottom-nav / pinned high-frequency tabs** (banking app). The 9-tab horizontal scroll row is the session's main navigation burden. Pinning 3-4 high-use tabs and collapsing the rest into a "..." overflow directly reduces thumb travel and cognitive load. Fits the existing `.ptab.muted` infrastructure.

3. **Combat card as fantasy-sports roster** (DraftKings lineup). Rendering Attacks + Limited Features as high-contrast, large-number cards with a one-tap Rest button converts the most-referenced combat section from a data-entry form into an action surface. Works within the single-file constraint with only CSS/minimal JS changes.

4. **Persistent status strip** (paper sheet spatial memory + cockpit MFD). A 4-field fixed strip above the tab bar (AC, HP, Inspiration, Proficiency bonus) replicates the "glance at top-right" reflex from the paper sheet and eliminates the need to scroll back to the top of Core to check AC mid-combat.

5. **Filled-pip spell slots** (boarding pass glanceability). Replacing the 9-column numeric grid with pip rows during Play mode makes slot consumption a single tap and makes remaining slots immediately scannable. Numeric inputs retained for Edit/Setup mode.

6. **Content-dot on tabs** (tabbed binder thickness). Low-effort CSS/JS change that restores the "how full is this section" signal from physical binders. Barbarians stop seeing an empty Spells tab; Wizards get a visible cue that their spell page has data.

---

**Timing**: Started Sun Jun  7 02:24:45 UTC 2026 · Finished Sun Jun  7 02:26:15 UTC 2026
