#!/usr/bin/env python3
"""Extract the curated magic-weapon PROPERTY catalog for the Ancestral Weapons builder's
"Additional properties" autofill.

Output (stdout / --json): {catalog:[{n,bonus}], text:{name:rulesText}} where
  - catalog = NAMES + mechanics (the always-on attack&damage bonus). NON-copyrightable →
    lives in app JS as the AW_PROPS const in index.html.
  - text    = each property's rules text (COPYRIGHTABLE WotC) → injected into the baked
    #source-data `awText` map in index.html (same home as the AW upgrade text), read at
    runtime via awText(name). Never hardcode this text into app JS.

Source: local 5etools data (FIVETOOLS_DATA, default ~/My Drive/5etools/data) —
magicvariants.json (generic weapon enchantments) + items.json (named magic weapons).
Regenerate, then merge `text` into the #source-data awText object with a Python
string-splice (the Edit tool fights the 13MB blob) and paste `catalog` into AW_PROPS.

The extra-damage rider is deliberately NOT extracted: most property riders are conditional
(vs a creature type, on a crit, only while lit), so auto-applying them to every hit would
over-buff. The rules text explains the real behavior; AW_PROPS carries only the flat +N.
"""
import json, os, re, sys

D = os.environ.get("FIVETOOLS_DATA", os.path.expanduser("~/My Drive/5etools/data"))

# property display name -> source entry name (magicvariant, then item fallback)
VARIANTS = {
    "Vorpal": "Vorpal Sword", "Flame Tongue": "Flame Tongue", "Frost Brand": "Frost Brand",
    "Sword of Sharpness": "Sword of Sharpness", "Vicious": "Vicious Weapon", "Dancing": "Dancing Sword",
    "Defender": "Defender", "Dragon Slayer": "Dragon Slayer", "Giant Slayer": "Giant Slayer",
    "Holy Avenger": "Holy Avenger", "Berserker": "Berserker Axe", "Nine Lives Stealer": "Nine Lives Stealer",
    "Luck Blade": "Luck Blade",
}
# Named weapons that aren't generic enchantments, plus Oathbow — 2024 reworked it into a variant, but the
# 2014 version we want is a plain item.
ITEMS = {"Sun Blade": "Sun Blade", "Dwarven Thrower": "Dwarven Thrower", "Mace of Disruption": "Mace of Disruption",
         "Oathbow": "Oathbow"}


def strip(s):
    if isinstance(s, list):
        return "\n".join(strip(x) for x in s)
    if isinstance(s, dict):
        return strip(s.get("entries") or s.get("items") or "")
    s = str(s)
    s = re.sub(r'\{@(?:damage|dice|scaledamage|scaledice)\s+([^}|]+)(?:\|[^}]*)?\}', r'\1', s)
    s = re.sub(r'\{@dc\s+([^}]+)\}', r'DC \1', s)
    s = re.sub(r'\{@[a-zA-Z]+\s+([^}|]+)(?:\|[^}]*)?\}', r'\1', s)
    s = re.sub(r'\{@[a-zA-Z]+\}', '', s)
    return s


RULESET_2024 = {"XPHB", "XDMG", "XMM", "XSCREEN", "XSAC"}


def is_2024(e):
    """True for a One D&D / 2024 entry. `edition` marks 2014 as "classic" on the variants;
    the source code is the reliable signal everywhere else."""
    inh = e.get("inherits") or {}
    ed = e.get("edition") or inh.get("edition")
    if ed:
        return str(ed).lower() in ("one", "2024")
    return str(e.get("source") or inh.get("source") or "").upper() in RULESET_2024


def bonus_num(v):
    m = re.search(r'\+(\d+)', str(v or ""))
    return int(m.group(1)) if m else 0


def main():
    mv = json.load(open(os.path.join(D, "magicvariants.json"))).get("magicvariant", [])
    items = json.load(open(os.path.join(D, "items.json"))).get("item", [])
    # The data ships a 2014 AND a 2024 entry under the same name; take the 2014 one. Keeping the
    # first match is not enough for magicvariants (2024 entries come later and a plain dict
    # comprehension kept them), so filter on the edition/source markers before falling back.
    mv_by, it_by = {}, {}
    for bag, e in [(mv_by, e) for e in mv] + [(it_by, e) for e in items]:
        n = e.get("name")
        if is_2024(e):
            bag.setdefault(n, e)   # only ever a fallback, never overwrites a 2014 entry
            continue
        if n not in bag or is_2024(bag[n]):
            bag[n] = e

    catalog, text = [], {}
    for disp, src in VARIANTS.items():
        e = mv_by.get(src)
        if not e:
            print("MISS variant", src, file=sys.stderr); continue
        inh = e.get("inherits", {})
        catalog.append({"n": disp, "bonus": bonus_num(inh.get("bonusWeapon"))})
        text[disp] = strip(inh.get("entries"))
    for disp, src in ITEMS.items():
        e = it_by.get(src)
        if not e:
            print("MISS item", src, file=sys.stderr); continue
        catalog.append({"n": disp, "bonus": bonus_num(e.get("bonusWeapon"))})
        text[disp] = strip(e.get("entries"))

    out = {"catalog": catalog, "text": text}
    if "--json" in sys.argv:
        print(json.dumps(out, indent=2))
    else:
        print("AW_PROPS = [" + ",".join('{n:%s,b:%d}' % (json.dumps(c["n"]), c["bonus"]) for c in catalog) + "];")
        print("\n%d properties, %d text entries" % (len(catalog), len(text)), file=sys.stderr)


if __name__ == "__main__":
    main()
