# Phone layout for play

Direction B from the 2026-10-27 phone audit, picked the same day. The phone view becomes a play surface: the numbers a player gets asked for at the table are on screen, or one tap away, on every tab.

## Why

Players at a real table could not find things on their phones. In four recorded sessions, the DM had to give spoken directions to attacks and damage (5 times), the spell save DC (3), spell slots (2), ability checks and skills (2), hit points (1), darkvision (1) and a spell's rules text (1).

The audit rendered two real characters at iPhone 13 size (390 × 664 visible) and measured how far each of those values sat from the opening view, in screens of 664 px:

| Value | Where it was | Distance |
|---|---|---|
| Attacks | Core, Attacks card, collapsed | 3.9 screens + 1 tap |
| Hit points | Core, Combat card | 2.6 screens |
| Armor Class | Core, Combat card (blank when no armor was selected) | 2.7 screens |
| Saving throws, skills | Core, collapsed | 3.7 to 3.8 screens + 1 tap |
| Senses, passive Perception | Core, collapsed | 4.1 screens + 1 tap |
| Spell save DC | Spells tab | 1 tap |
| Feature text | Features tab, after a 2,160 px invocation picker | 1 tap + up to 11 screens |

Other findings: app chrome filled 35 to 66 percent of the first screen, followed by 553 px of identity fields. Search matched text inside fields but never the name of a box. Only 4 of 9 tabs fit on screen.

## Release 1 (shipped 2.169.0)

- Search knows box names and synonyms, shows the live value, and opens a collapsed card when it jumps.
- Phone play cards start open, and each card remembers its open or closed state on the device.
- No armor selected computes as unarmored AC, with a link to the armor picker.
- Spell names get the first line with Cast only. Edit and delete move to the second line.
- On phones, the character's own features come before the pickers.
- The cluster layout no longer opens collapsed on phones.

## Release 2

1. A stats bar on every tab, phones only: HP with temp HP, AC, Initiative, Speed, Spell DC, and a badge for active conditions or concentration. A tap on HP opens heal and damage. A tap on any value goes to its card.
2. A bottom tab bar in thumb reach: Play, Spells, Features, Gear, More. Background, Backstory, Notes, Companions, Mini, Settings, Save and Print go under More. The dice button moves into this bar, because the dice rail owns the bottom edge on phones.
3. One slim top row: name, class and level, Search, Menu. Edit Character, Save and the rest buttons move to More. Each banner becomes one line.
4. Core in turn order: abilities and saves as one 3 × 2 grid (tap to roll), then Actions (attacks, damage cantrips, bonus actions, reactions), Resources (slots, limited uses, hit dice), Skills in two columns with passive scores and senses on one line, then Proficiencies, then identity, collapsed.
5. Attack and Limited Features names are cut off at phone width today. The Actions rework gives each name the full row.

Constraints: element ids, compute and print do not change. Relocation follows the cluster-layout pattern (move by id, send home on deactivate, print-guarded). The visual language stays: system fonts, the UCS gold tokens, square corners, no shadows. A static mockup of the phone Core page comes before any release 2 code.

## How to judge it

The judge is the players, not the people who built it.

- A six-task test on each player's own phone, from a freshly opened sheet. Record found or not, seconds, and help needed. Run it once on 2.169.0 (the baseline) and again after release 2.
  1. What is your Armor Class?
  2. Make a Dexterity saving throw.
  3. What is your spell save DC? (Non-casters: how many uses of your main limited feature are left?)
  4. Attack with your best ranged weapon or cantrip. What do you add to the d20, and what damage do you roll?
  5. You take 7 damage. Update your sheet.
  6. Read me what one of your features does.
- Two held-out tasks for the re-test only, so the design cannot be tuned to them: "Do you have darkvision, and how far?" and "How much gold do you have?"
- Over time, the number of spoken DM directions to the sheet per recorded session.
- In code, a phone-emulation check that fails when a top-task value sits more than 1 tap and 1 screen from the opening view.
