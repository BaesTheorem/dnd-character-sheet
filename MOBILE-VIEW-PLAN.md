# Mobile View — plan

A mobile-friendly copy of the sheet lives in **`Character Sheet (Mobile).html`**.
It is a byte-for-byte copy of `Character Sheet.html` plus two small, clearly
fenced additions. We iterate on it here, then fold it back into the main sheet
as a built-in **Mobile View** once it feels right.

## What the copy changes (and only this)

The copy keeps the same single-file, no-build, vanilla HTML/CSS/JS philosophy.
Three minimal diffs from the original:

1. **`<title>`** — `Character Sheet · Mobile` (so you can tell the open file
   apart). Cosmetic.
2. **A `MOBILE VIEW` `@media (max-width:820px)` block** appended at the end of
   the `<style>`. Width-gated, so on a laptop the sheet renders exactly like the
   desktop original — nothing in the block applies above 820px.
3. **A small `MOBILE VIEW enhancement` `<script>`** just before `</body>`. It
   *adds* a second `#pagetabs` click listener (it does not replace the existing
   one), so on a narrow screen tapping a tab centres it in the swipeable tab bar
   and scrolls back to the top of the page.

Both code additions are wrapped in `MOBILE VIEW` banner comments so they are
trivial to locate and lift out.

### What the mobile block does

- **No zoom-on-focus** — pins `input/select/textarea` to `font-size:16px` (iOS
  zooms a focused field smaller than that).
- **Toolbar** goes static and compact; the brand takes its own row and the
  action buttons grow to ≥42px tall touch targets.
- **Page tabs** become a single **pinned, horizontally-swipeable row** (the 9+
  tabs no longer wrap). The tab bar owns the sticky top spot instead of the
  toolbar.
- **Header** stacks the portrait centered above the identity fields.
- **Two-column regions** (`.columns`, `.topblock`) stack to one column at 820px
  (the originals only collapsed at 860/640).
- **Bigger touch targets** for skill/save checkboxes and ability steppers.
- **Modals** (Create Character wizard, Settings) go near full-screen with a
  sticky header/footer and an internal scroll.
- **Settings** section nav stays a scrollable row.

Everything is additive CSS/JS — no existing rule, id, data model, autosave key,
or computation is touched, so a character saved in one file opens in the other.

## How to fold it into the main sheet (later)

Goal: one file, `Character Sheet.html`, that is responsive by width **and** has
an explicit, user-toggleable Mobile View.

1. **Copy the two fenced blocks** (the `MOBILE VIEW` `@media` block and the
   `MOBILE VIEW enhancement` `<script>`) into `Character Sheet.html`. Because the
   `@media` block is width-gated and the script is additive, this alone makes the
   main sheet responsive with zero risk to desktop rendering. This is the safe
   first merge.
2. **Add a manual toggle** (so it can be forced on a desktop/tablet, and
   remembered): add a **"Mobile view"** switch under **Settings → Layout/General**.
   The toggle adds/removes a `mobile` class on `<html>` (or `.sheet`) and persists
   it in the same per-browser settings store the other layout toggles use
   (`hiddenPages`, `hidePortrait`, …).
3. **Make the mobile rules fire on the class too**, not just the width. Change
   the block's guard from `@media (max-width:820px){ … }` to a shared selector,
   e.g. duplicate the gate:
   ```css
   @media (max-width:820px){ /* …rules… */ }
   html.mobile .toolbar, html.mobile .pagetabs, /* …mirror the same rules… */
   ```
   In practice the cleanest port is to drop the `@media` and instead scope every
   rule under `html.mobile`, then have the toggle default to *on* below 820px via
   a tiny `matchMedia` check at boot (and let the user override). That keeps a
   single source of truth for the rules.
4. **Update the mobile `<script>`** guard to honour the class as well as the
   media query (`mq.matches || document.documentElement.classList.contains('mobile')`).
5. **Print** is unaffected — the mobile block does not touch `@media print`; the
   existing print stylesheet still produces the dense one-page PDF.
6. Once merged and verified, delete `Character Sheet (Mobile).html` and this plan
   (or keep this as a short note in the README's Roadmap).

## To verify the copy

Open `Character Sheet (Mobile).html` in a browser and narrow the window below
820px (or use device emulation / a real phone):

- The page tabs become one swipeable row pinned to the top.
- Create Character / Settings open near full-screen and scroll cleanly.
- Tapping a field does not zoom the page (iOS).
- Two-column areas (abilities/combat) stack to one column.
- Above 820px the sheet looks identical to `Character Sheet.html`.
