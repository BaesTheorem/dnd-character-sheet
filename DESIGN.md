# Design rules

The rules for any new screen in the sheet. The Universal Character Sheet theme (`ucs`) is the default and the reference. Classic is a separate, pixel-faithful rebuild of the official PDF and does not follow these rules.

## Type

- The system font stack only: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`. No bundled or web fonts.
- Numbers that change in play use `font-variant-numeric: tabular-nums`.
- Section headings: 11px, weight 800, uppercase, letter-spacing .13em, in `--ucs-gold` (`#a07d22` light, `#c6a458` dark).
- On phones, every input is at least 16px, so iOS does not zoom when it gets focus.

## Palette

Five named tokens, light and dark. Each one is a CSS variable already in `index.html`.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--card` | `#ffffff` | `#16181c` | Surfaces: cards, bars, menus |
| `--ink` | `#1d1f23` | `#e4e5e8` | Body text and labels you read |
| `--muted` | `#6a6f78` | `#8a8f98` | Sublabels, hints, inactive tabs |
| `--accent` | `#8a6d22` | `#e2c477` | Gold. Computed values, active states, links, filled pips |
| `--ucs-hp` | `#9e2b25` | `#d4534a` | Hit points only |

The neutrals behind them (`--bg`, `--field`, `--line`) and the heading gold (`--ucs-gold`, also `--line2` for gold rules) are in the same blocks. On a dark accent fill, ink is near-black (`#141414`), because white on the light gold fails contrast. Every tinted state class needs a `body.dark` twin.

## Space and shape

- Spacing on an 8px scale: 8, 16, 24, 32, with 4 as the half step inside dense controls.
- One border radius: 0. Square corners everywhere (the flat/sharp block enforces it).
- No gradients and no shadows. Hairline borders (`1px var(--line)`) and tonal surfaces separate layers. The one exception is the shadow under the 3D dice, which is part of the dice scene, not the interface.
- Icons are inline SVG with `currentColor`, stroke width 1.4 to 1.6. No emoji as icons.
- On phones, every tap target is at least 44 × 44 px, including pips and small buttons (pad the hit area if the mark is smaller).

## Phone layout

The phone view is a play surface: the numbers a player gets asked for at the table are on screen or one tap away, on every tab. The spec, the evidence behind it and the player test that judges it are in [`plans/phone-play-layout.md`](plans/phone-play-layout.md). The release 2 mockup is [`design/drafts/phone-play-r2-v1.html`](design/drafts/phone-play-r2-v1.html).
