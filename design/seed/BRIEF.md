# Brief: D&D 5e character sheet, prototype redesign

Seeded 2026-10-03. This is a prototype pass: explore a better layout and visual
system for the sheet. Nothing here ships until a design is picked and handed off.

## The product

A single-file web app (one `index.html`, offline, no framework) that replaces
the official fillable 5e (2014 rules) PDF sheet. It builds a character from
sourcebook data, then runs as a live play surface at the table: it computes
every derived number, tracks HP, conditions, spell slots and limited-use
features, and rolls dice. It is a tool for one player during a session, so the
most common action is a glance, then a tap.

## Who uses it

One player at a table, on a laptop in landscape most of the time, sometimes on a
phone. Experienced with 5e. They know what every box means; they want to find
it without looking for it.

## What to fix (the current sheet is in `current/`)

- The Core page reads as a form. Large empty boxes and labels in small caps get
  equal weight, so the numbers that matter in combat (AC, HP, initiative, save
  DCs, attack bonuses) do not stand out.
- Hit points are a small box in a big panel. HP is the number that changes most.
- Combat data is spread over three rows (abilities, combat, then saves and
  skills under the fold). The play loop needs it on one screen.
- The tab strip (Actions, Spells, Inventory, Features, Background, Notes,
  Backstory, Extras, Mini) wraps to two lines and has no clear order.
- The dice rail floats on the right edge with its own visual language.

## Screens to design

1. **Core, desktop (1440 wide, landscape).** Identity, six abilities, AC, HP,
   initiative, speed, proficiency, inspiration, saves, skills, conditions, and
   the tabbed detail area. Everything for a combat turn above the fold.
2. **Actions tab.** Attacks (name, to-hit, damage, type), action economy
   (action, bonus action, reaction), limited-use features with pips.
3. **Spells tab.** Spellcasting stats, slot pips per level, prepared spells
   grouped by level, concentration marker.
4. **Inventory tab.** Equipped and attuned items, weight, currency.
5. **Core, phone (390 wide).** Same data, one column, the combat numbers first.
6. **Dice rail.** d4 to d100, multiplier, roll log. Part of the sheet, not
   floating over it.

## States each screen needs

- Blank sheet (first open, nothing built yet): a clear path to "Create
  Character", not a wall of empty boxes.
- Built character at rest.
- In combat: HP below half, one or more conditions active, concentration on.
- Down: 0 HP with death-save pips.
- Light and dark mode (dark is a toggle on top of any theme).

## Constraints (hard)

- Flat and sharp: corner radius 0, no drop shadows. Hairline borders and
  tonal surfaces separate layers.
- System fonts only, no bundled font or image assets. Icons are inline SVG.
- Gold accent stays the identity color of this theme (see `tokens.css`).
  Contrast for body text at least WCAG AA in both modes.
- Reduced motion is the default rendering. Any motion is an enhancement.
- Print stays portrait US Letter and is a separate layout; this pass is screen
  only.
- No rules text from the sourcebooks in the design. Use placeholder copy
  ("Feature description") or invented names for sample content.

## Sample character for the mockups

Invented, so there is no copyrighted text: "Vessa Thornwick", Half-Elf Ranger 5,
Outlander. STR 12, DEX 18, CON 14, INT 10, WIS 15, CHA 8. AC 16, HP 38/44,
initiative +4, speed 35 ft, proficiency +3. Longbow +7 (1d8+4 piercing),
shortswords +7 (1d6+4). Spell save DC 13, slots 4 first-level and 2
second-level, concentrating on a level-2 spell.

## References

- [Dribbble: character sheet](https://dribbble.com/search/character-sheet):
  how others put six abilities and derived stats into one strip.
- [Dribbble: game stats dashboard](https://dribbble.com/search/game-stats-dashboard):
  dense numeric dashboards with one dominant number per card, for the HP and
  combat block.
- [Awwwards: games and entertainment](https://www.awwwards.com/websites/games-entertainment/):
  type and texture that feel like a game without fantasy clichés.

## Files in this seed

- `BRIEF.md`: this file.
- `tokens.css`: the current color, radius and font tokens (light and dark).
- `current/`: screenshots of the current sheet (blank character), desktop light,
  desktop dark, phone.
