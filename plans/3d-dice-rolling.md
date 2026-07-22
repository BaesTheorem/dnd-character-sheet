# 3D Dice Rolling — Planning Document

Status: **planned, not started** · Target versions: 2.134.0 (Phase A) / 2.135.0 (Phase B) / 2.136.0 (Phase C)

## Goal

Click a stat and 3D dice tumble across a full-screen transparent overlay on top of the sheet (D&D Beyond style — dice roll over the whole page, not in a tray), settle, and show a result card. Requirements:

- Rollable targets: ability score modifiers, skill totals, saving throws, initiative, attack rows (including the ammo-expending fire button), and the Cast button on damage-dealing spells.
- A **plain-dice sidebar**: a slim rail of virtual dice (d4 d6 d8 d10 d12 d20 d100) that can be rolled manually with **no modifiers** — just the raw dice, for any ad-hoc roll the sheet doesn't wire.
- Multiple dice materials: plastic, glass, opalescent, metal (plus a color picker).
- A roll log of the past ~50 rolls.
- Advantage/disadvantage auto-applied when the sheet already knows it.

## Key decisions

- **Rendering:** vendor **three.js r147 UMD** (~605KB, the last non-module build) + **cannon.js 0.6.2 UMD** (~130KB), both MIT, inlined as new `<script>` blocks. Off-the-shelf dice libraries (`@3d-dice/dice-box` etc.) require external wasm/texture assets, which fights the single-file offline architecture. Dice geometry, number faces (runtime `CanvasTexture`), and all materials are **procedural — zero binary assets**. Net file growth ~780KB (~5.5%).
- **Fairness/determinism:** results are computed FIRST via the existing crypto rejection-sampled `rollDie(sides)` (~line 4383); the physics sim runs freely; on settle, the die's face materials are remapped so the landed face shows the true value (the proven dice-box trick).
- **Ammo marriage:** the fire button becomes "attack" — **one click = expend ammo + roll to-hit** (result card notes remaining ammo). Clicking the Bonus cell / injected d20 button rolls to-hit **without** expending; the Damage cell rolls damage. `fireAmmo()` itself is unchanged.
- **Adv/disadv:** rides the same `resolveAdv(gatherAdvSources(), keys)` API that paints the on-sheet A/D badges, so the roll always agrees with the badge. 2d20 keep-high/low, dropped die dimmed, the situational note shown on card + log.
- **Crit:** nat 20 on a to-hit → gold card + "Roll damage (crit)" (doubles dice count, not modifiers, RAW). Nat 1 → red card, no damage button.
- **Roll log:** global across characters (each entry records the character name), localStorage key `dnd-sheet-rolllog`, capped at 50. NOT in `collect()`/character data — never bloats exports or shared copies.
- **Dice theme:** app-level pref like dark mode — localStorage `dnd-sheet-dice` = `{theme, color, threeD}`; picker in Settings → General → Appearance.
- **Instant fallback** (no 3D, immediate result card) when any of: 3D pref off, `no-animations` on, `prefers-reduced-motion`, WebGL unavailable / context lost, or >10 dice in one roll.

## Architecture

Three `<script>` blocks appended after the last mobile IIFE (~line 16121, before `</body>`): three.js vendor, cannon vendor, then a **dice module IIFE** exposing `window.DiceRoller` (`roll(spec)`, `rollDamage({formula,…})`, `rollSpell(name, castLevel, inst)`, prefs) plus a test seam `window.__diceTest` (`instant`, `last`, RNG swap, `engineActive()`).

- Vendor splices via verified Python byte-splice (the Edit tool can't handle blocks that size on this file); anchor on `</body>`. Keep the MIT license header comment on each vendored block.
- The module registers **one document-level delegated click listener in the CAPTURE phase** (so an `.atk-fire` click can read the row + ammo badge before `fireAmmo()`'s `compute()` rebuilds those nodes; it never calls preventDefault/stopPropagation). Guards: bail on `e.altKey` (pin revert), `e.detail > 1` (dblclick pin editor), and `e.target.closest('.sk-tri')`.
- It also wraps `window.compute` (the Classic-engine precedent) to run an idempotent `renderAtkRollButtons()` pass.
- New damage parser `parseDamageParts(str)` — do NOT touch `_parseDice` (~8171), which feeds upcast math. Splits on `;`/`,`, extracts dice groups + signed flat mods per segment, tags damage type + segment label, ignores range text ("range 30/120" yields no dice → skipped). Handles strings like `"1d8+3 slashing, range 30/120; Sneak Attack +2d6"`.
- Overlay: lazy `canvas#dice-canvas` — `position:fixed; inset:0; pointer-events:none; z-index:55`, `.noprint`, `data-transient="1"`; devicePixelRatio capped at 1.5, low-power preference; disposed after 60s idle; `webglcontextlost` → instant card (results are pre-computed, nothing is lost).
- Result card `#dice-card` (transient, noprint, z-60, flat/sharp per app taste, `var(--card)` + dark twin): label, adv chip (reuse `advIconSvg`), big total, per-die chips with the dropped die struck through, per-part damage subtotals, contextual "Roll damage" button, auto-dismiss ~6s.
- Roll log modal: lazy builder using the `.modal` pattern + `data-transient` + the `_live` corpse-heal idiom; opened from a new **static** `#btn-rolllog` menu item in `#app-menu` (~line 2064, between Print and Settings).

## Plain-dice sidebar

A fixed slim rail on the right edge of the viewport (`#dice-rail`, built once at init, `data-transient="1"`, `.noprint`, z-index below modals): one button per die — d4, d6, d8, d10, d12, d20, d100 — each drawn as a small inline SVG polygon (no emoji, per app taste) with the die name beneath. Clicking a die rolls it **immediately with zero modifiers** through the same `DiceRoller.roll` path (so it gets the 3D tumble when enabled, the result card, and a log entry labeled e.g. "d20"). A small count stepper at the top of the rail (`1×`–`9×`, default 1, sticky) makes the next click roll `N` of that die (e.g. `3×` + d6 → 3d6, summed on the card with per-die chips). No modifier field — by design; wired sheet stats already carry their own modifiers, and this rail is the "just let me roll dice" escape hatch.

- Collapse/expand: a small dice-icon tab pinned to the rail's edge toggles it; collapsed state persists in the dice pref (`rail:0|1`). Collapsed by default on mobile (`html.mobile`), where the expanded rail overlays content; desktop default open.
- Rail buttons are ≥44px tall on mobile.
- The rail renders under UCS, canonical, and mobile layouts (it's a body-level fixed element, unaffected by page relocation); hidden in Classic print and all print via `.noprint`.
- Multi-die rolls (count > 1) show each die as a chip on the result card and the sum as the total — same rendering as damage rolls, no adv/disadv logic.

## Wiring map

| Target | Trigger | Mod source | advKeys |
|---|---|---|---|
| Ability check | click `#mod-<k>` | `modOf(k)` | `['check']` |
| Skill | click `#sktot-<key>` | parse textContent (inherits pins/expertise) | `['check','skill:<key>']` |
| Save | click `#savetot-<k>` | parse textContent | `['save','save:<k>']` |
| Initiative | click `#init` / its `.stat` | parse textContent | `['check']` |
| Attack to-hit | click readOnly `#atkbonus-i` or injected `.atk-roll` d20 button (bonus td; 44px min on mobile) | `atkbonus-i` value; non-numeric (e.g. "Dex save DC 15" feature rows) → no d20, damage-only card showing the DC | `['attack']` |
| Attack damage | click readOnly `#atkdmg-i` or card button | `parseDamageParts` | — |
| Fire button | `.atk-fire` (capture phase, before `fireAmmo`) | row's bonus | `['attack']` |

When parsing displayed totals, strip the `.advmark` badge child first.

## Cast flow (the only main-script edits)

All in the 12404–12427 / 13974–13978 / 8674 / 8298+8324 neighborhoods:

1. `onCastClick` (12409): resolve the spell name (reuse the `spellNameFromEl` logic; strip a trailing `" (R)"`) + sheet instance; the single-slot path becomes `expendSlot(L); if(window.DiceRoller) DiceRoller.rollSpell(name, L, inst)`.
2. `openCastPop` (12417): stamp `pop.dataset.spell`/`inst`; the `.cast-pop-lvl` route (13977) reads them **before** `closeCastPop()`, then rolls AFTER the level choice, at that level (upcast dice via `spellDamage(d, castLevel)`).
3. `rollSpell`: `dmg = spellDamage(d, castLevel)`; empty string → non-damage spell → roll nothing (behavior unchanged). `DATA.attackSpells.has(name)` → to-hit first (mod parsed from `#spellatk`/`__inst` textContent), damage offered on the card; save spells → damage immediately, card subtitled with `#spelldc`.
4. Cantrips (no Cast button today): at render sites 8298 + 8324, emit a `.sp-cast` variant with `data-roll="1"` for level-0 spells that have `d.dmg`; the delegated route skips slot logic → `rollSpell(name, 0, inst)`. Keep the button AFTER the name text node (`refreshSpellDamageCells` reads `firstChild`).
5. Scrolls: end of `castScroll` (8674) success path → damage-only roll labeled "(scroll)" (v1 simplification).

Every call is guarded `window.DiceRoller && …` — if the dice block ever fails to parse, casting behaves exactly as today.

## Materials (Phase C)

Shared factory + procedural PMREM env map (`RoomEnvironment` isn't in the UMD build — hand-build ~6 emissive boxes + lights):

- plastic: `MeshStandardMaterial {color, roughness:.35}`
- glass: `MeshPhysicalMaterial {transmission:.85, ior:1.5, roughness:.08, transparent, opacity:~.65}` (a transparent overlay canvas has nothing behind the die to refract — blend opacity for the see-through read; pips opaque)
- opal: `MeshPhysicalMaterial {iridescence:1, iridescenceIOR:1.35, sheen:.6, clearcoat:.6, roughness:.25}` (iridescence exists since r139 — verify `grep -c iridescence` in the downloaded build BEFORE splicing)
- metal: `MeshPhysicalMaterial {metalness:1, roughness:.22}` + env map (mandatory or it renders black)

Number textures cached per (theme, die, face); 6/9 underlined.

## Phases (each ships a fully working sheet; bump VERSION + `{v:"Unreleased"}` changelog entry per phase)

- **A — Roll engine, all click wiring, result card, roll log. No 3D yet (instant results). → 2.134.0.** ~500-line module + the cast edits + settings block + the `rollDie` de-collision (rename line 4344's HP-oriented `rollDie(die)` → `rollHpDie` + its `regenHp` call site; the crypto one at 4383 stays the canonical roller). Delivers rolls/log/adv immediately; the risky vendoring lands only after the feature is already useful.
- **B — 3D overlay + physics, plastic theme only. → 2.135.0.** Vendor splices, engine, settle-remap, disposal, context-loss handling, perf caps, no-anim/reduced-motion gating.
- **C — Glass/opal/metal themes + color picker fully live. → 2.136.0.**

## Risks

- File +~780KB → accepted; the pre-commit hook restamps `version.json` size automatically.
- Print: everything noprint + transient; the engine's resize handler must **no-op while `matchMedia('print').matches`** (the documented mid-print-mutation bug class).
- Saved-copy corpses: card/canvas/log-modal all carry `data-transient`; the log modal uses the `_live` heal idiom; the menu item + settings controls are static HTML (safe to serialize).
- Never grep-print the data blob line; verify every edit by Playwright load (`pageerror` + `typeof compute === 'function'`) — node syntax-check is unreliable on this file.
- Classic theme: the dice listeners are inert on `.cl-slot` clicks (out of scope, must not error).

## Verification (Playwright, Python package; click `#intro-skip` first)

- **A:** zero pageerrors; `#sktot-stealth` click → `__diceTest.last` total = die + parsed bonus; Blinded condition → attack rolls 2d20 disadvantage, kept = min; cantrip cast → damage card, no slot spent; Fireball at 5 via cast-pop → `slot5u` +1 AND a 10d6 formula; a non-damage spell → slot spent, no card; `.atk-fire` → ammo qty −1 + a to-hit result, `.atk-roll` → roll only, qty unchanged; a DC-type feature row → no d20; 55 pushed rolls → log length 50, survives reload; print emulation hides all dice DOM; a save-copy clone contains no `[data-transient]`; dblclick pin editor + Alt-revert + HP "Rolled" mode still work.
- **B:** SwiftShader roll → canvas exists, settled faces == pre-computed kept values; `__diceTest.instant` → no canvas; reduced-motion → instant; forced `WEBGL_lose_context` mid-roll → correct card, no error; idle disposal + recreate; `page.pdf()` at a 1300px viewport — page count/baseline unchanged.
- **C:** theme change persists in localStorage; material param asserts (`metalness===1`); element-screenshot sanity check (computed values / rendered pixels, never inline styles).

## Vendor sources

- `https://unpkg.com/three@0.147.0/build/three.min.js` (MIT)
- `https://cdnjs.cloudflare.com/ajax/libs/cannon.js/0.6.2/cannon.min.js` (MIT)
