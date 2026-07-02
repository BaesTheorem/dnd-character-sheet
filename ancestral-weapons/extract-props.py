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
    "Luck Blade": "Luck Blade", "Oathbow": "Oathbow",
}
ITEMS = {"Sun Blade": "Sun Blade", "Dwarven Thrower": "Dwarven Thrower", "Mace of Disruption": "Mace of Disruption"}


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


def bonus_num(v):
    m = re.search(r'\+(\d+)', str(v or ""))
    return int(m.group(1)) if m else 0


def main():
    mv = json.load(open(os.path.join(D, "magicvariants.json"))).get("magicvariant", [])
    items = json.load(open(os.path.join(D, "items.json"))).get("item", [])
    mv_by = {e.get("name"): e for e in mv}
    it_by = {}
    for e in items:
        it_by.setdefault(e.get("name"), e)

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
