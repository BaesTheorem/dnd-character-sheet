#!/usr/bin/env python3
"""
Build a trimmed PHB (2014) data subset for the character sheet from a local 5eTools copy.

Personal-use tool: it reads content from your own legal copy of the PHB (via a local 5eTools data
folder). The output (phb-data.json) is copyrighted WotC content trimmed for personal use — do NOT
redistribute the data-bearing sheet or commit phb-data.json.

Set the source folder via the FIVETOOLS_DATA env var, or it defaults to ~/My Drive/5etools/data.
Re-run this if the 5eTools data updates.  Usage:  python3 build-data.py
"""
import json, os, re

SRC = os.environ.get("FIVETOOLS_DATA", os.path.expanduser("~/My Drive/5etools/data"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phb-data.json")
PHB = "PHB"  # 2014 Player's Handbook source tag (2024 book is "XPHB")

SCHOOL = {"A":"Abjuration","C":"Conjuration","D":"Divination","E":"Enchantment",
          "V":"Evocation","I":"Illusion","N":"Necromancy","T":"Transmutation"}
DMG = {"S":"slashing","P":"piercing","B":"bludgeoning","R":"radiant","F":"fire",
       "C":"cold","L":"lightning","A":"acid","O":"force","Y":"psychic","T":"thunder","N":"necrotic"}
SIZE = {"T":"Tiny","S":"Small","M":"Medium","L":"Large","H":"Huge","G":"Gargantuan"}
WPROP = {"A":"ammunition","F":"finesse","H":"heavy","L":"light","LD":"loading","R":"reach",
         "S":"special","T":"thrown","2H":"two-handed","V":"versatile"}

# ---- 5eTools {@tag ...} markup -> plain text ----
_tag = re.compile(r"\{@(\w+) ([^{}]*)\}")
def render_tags(s):
    if not isinstance(s, str): return s
    prev = None
    while prev != s:
        prev = s
        def repl(m):
            tag, body = m.group(1), m.group(2)
            parts = body.split("|")
            if tag in ("dice","damage","scaledamage","scaledice","d20","hit","dc"):
                return parts[0]
            if len(parts) >= 3 and parts[2].strip():   # explicit display text
                return parts[2]
            return parts[0]
        s = _tag.sub(repl, s)
    return s

def entries_to_text(e):
    if isinstance(e, str): return render_tags(e)
    if isinstance(e, list): return "\n".join(t for t in (entries_to_text(x) for x in e) if t)
    if isinstance(e, dict):
        t = e.get("type")
        if t == "list":
            return "\n".join("• " + entries_to_text(i) for i in e.get("items", []))
        if t == "table": return ""
        inner = entries_to_text(e.get("entries", []))
        name = e.get("name")
        if name and inner: return f"{name}. {inner}"
        return name or inner
    return ""

def render_prof_list(lst):
    out = []
    for x in lst or []:
        out.append(render_tags(x) if isinstance(x, str) else render_tags(x.get("proficiency", "")) or "")
    return [x for x in out if x]

def load(*parts):
    return json.load(open(os.path.join(SRC, *parts)))
def is_phb(x): return x.get("source") == PHB

# ---- Races (+ PHB subraces) ----
def _traits(entries):
    return [{"name": t.get("name",""), "text": entries_to_text(t.get("entries",[]))}
            for t in entries if isinstance(t, dict) and t.get("name")]

def _speed(r):
    sp = r.get("speed")
    return sp if isinstance(sp, int) else (sp or {}).get("walk", 30)

def build_races(raw):
    out, bases, base_idx = [], {}, {}
    for r in raw.get("race", []):
        if not is_phb(r): continue
        ab = list(r.get("ability") or [])
        bases[r["name"]] = {"ability": ab, "speed": _speed(r), "traits": _traits(r.get("entries", []))}
        base_idx[r["name"]] = len(out)
        out.append({"name": r["name"], "ability": ab,
                    "size": "/".join(SIZE.get(s, s) for s in r.get("size", [])) or "Medium",
                    "speed": _speed(r), "traits": _traits(r.get("entries", []))})
    for s in raw.get("subrace", []):
        if not is_phb(s): continue
        parent = s.get("raceName")
        if not s.get("name"):                       # unnamed "standard" subrace -> fold into base option
            i = base_idx.get(parent)
            if i is not None:
                out[i]["ability"] = (out[i]["ability"] or []) + (s.get("ability") or [])
                out[i]["traits"]  = (out[i]["traits"] or []) + _traits(s.get("entries", []))
            continue
        base = bases.get(parent, {})               # named subrace -> "Race (Subrace)", base + subrace
        out.append({"name": f"{parent} ({s['name']})",
                    "ability": (base.get("ability") or []) + (s.get("ability") or []),
                    "size": "", "speed": base.get("speed", 30), "subraceOf": parent,
                    "traits": (base.get("traits") or []) + _traits(s.get("entries", []))})
    return out

def skills_from(spo):
    fixed, choose = [], None
    for blk in spo or []:
        for k, v in blk.items():
            if k == "choose" and isinstance(v, dict):
                choose = {"from": v.get("from", []), "count": v.get("count", 1)}
            elif v is True:
                fixed.append(k)
    return fixed, choose

def build_backgrounds(raw):
    out = []
    for b in raw.get("background", []):
        if not is_phb(b): continue
        fixed, choose = skills_from(b.get("skillProficiencies"))
        feat = next((e for e in b.get("entries", []) if isinstance(e, dict)
                     and str(e.get("name","")).startswith("Feature:")), None)
        out.append({"name": b["name"], "skills": fixed, "skillChoose": choose,
                    "feature": {"name": feat["name"].replace("Feature: ","") if feat else "",
                                "text": entries_to_text(feat.get("entries",[])) if feat else ""}})
    return out

def build_classes():
    out = []
    for fn in sorted(os.listdir(os.path.join(SRC, "class"))):
        if not fn.startswith("class-") or not fn.endswith(".json"): continue
        data = load("class", fn)
        for c in data.get("class", []):
            if not is_phb(c): continue
            sp = c.get("startingProficiencies", {})
            sk_fixed, sk_choose = skills_from(sp.get("skills"))
            seen, subs = set(), []
            for s in data.get("subclass", []):
                if not is_phb(s) or s.get("className") != c["name"]: continue
                short = s.get("shortName", s["name"])
                if short in seen: continue
                seen.add(short); subs.append({"name": s["name"], "short": short})
            out.append({"name": c["name"],
                        "hd": c.get("hd", {}).get("faces"),
                        "saves": c.get("proficiency", []),
                        "skillChoose": sk_choose, "skillsFixed": sk_fixed,
                        "armor": render_prof_list(sp.get("armor")), "weapons": render_prof_list(sp.get("weapons")),
                        "casterAbility": c.get("spellcastingAbility"),
                        "casterProgression": c.get("casterProgression"),
                        "subclassTitle": c.get("subclassTitle",""), "subclasses": subs})
    return out

def build_feats(raw):
    out = []
    for f in raw.get("feat", []):
        if not is_phb(f): continue
        out.append({"name": f["name"], "text": entries_to_text(f.get("entries", []))})
    return out

def build_items(raw):
    weapons, armor = [], []
    for it in raw.get("baseitem", []):
        if not is_phb(it): continue
        if it.get("weapon"):
            weapons.append({"name": it["name"], "cat": "martial" if it.get("weaponCategory")=="martial" else "simple",
                            "dmg": it.get("dmg1",""), "dmgType": DMG.get(it.get("dmgType",""), it.get("dmgType","")),
                            "versatile": it.get("dmg2",""),
                            "props": [WPROP.get(p, p) for p in (it.get("property") or [])],
                            "range": it.get("range","")})
        elif it.get("armor") or it.get("type","") in ("LA","MA","HA","S"):
            armor.append({"name": it["name"], "ac": it.get("ac"), "type": it.get("type",""),
                          "stealth": bool(it.get("stealth")), "strength": it.get("strength")})
    return weapons, armor

def build_spells():
    spells = []
    for fn in os.listdir(os.path.join(SRC, "spells")):
        if not re.match(r"spells-phb\.json$", fn): continue
        for s in load("spells", fn).get("spell", []):
            if not is_phb(s): continue
            comp = s.get("components", {})
            spells.append({"name": s["name"], "level": s.get("level", 0),
                           "school": SCHOOL.get(s.get("school",""), s.get("school","")),
                           "time": entries_to_text(s.get("time", [])) if isinstance(s.get("time"), str) else
                                   "; ".join(f"{t.get('number','')} {t.get('unit','')}" for t in s.get("time", [])),
                           "range": render_range(s.get("range", {})),
                           "components": "".join(k.upper() for k in ("v","s","m") if comp.get(k)),
                           "duration": render_duration(s.get("duration", [])),
                           "text": entries_to_text(s.get("entries", [])),
                           "higher": entries_to_text(s.get("entriesHigherLevel", []))})
    spells.sort(key=lambda x: (x["level"], x["name"]))
    return spells

# Per-class PHB spell lists (levels 1-9) for classes that prepare from their whole list.
def build_class_spells():
    levels = {}
    for fn in os.listdir(os.path.join(SRC, "spells")):
        if not re.match(r"spells-phb\.json$", fn): continue
        for s in load("spells", fn).get("spell", []):
            if is_phb(s): levels[s["name"]] = s.get("level", 0)
    try: src = load("spells", "sources.json").get("PHB", {})
    except Exception: return {}
    FULL = {"Cleric", "Druid", "Paladin", "Artificer"}
    out = {}
    for name, info in src.items():
        lv = levels.get(name)
        if lv is None or lv == 0: continue            # PHB, leveled spells only (cantrips go in their own box)
        for c in info.get("class", []):
            if c.get("source") == PHB and c.get("name") in FULL:
                out.setdefault(c["name"], []).append({"n": name, "l": lv})
    for cn in out: out[cn].sort(key=lambda x: (x["l"], x["n"]))
    return out

def render_range(r):
    if not isinstance(r, dict): return str(r)
    d = r.get("distance", {})
    if r.get("type") == "point" and d: return f"{d.get('amount','')} {d.get('type','')}".strip()
    return r.get("type", "")

def render_duration(d):
    if not d: return ""
    x = d[0]
    if x.get("type") == "timed":
        dur = x.get("duration", {})
        return f"{'Concentration, up to ' if x.get('concentration') else ''}{dur.get('amount','')} {dur.get('type','')}"
    return x.get("type", "")

def main():
    races = load("races.json")
    out = {
        "_meta": {"source": "D&D 5e PHB (2014) via local 5eTools — personal use, do not redistribute"},
        "races": build_races(races),
        "backgrounds": build_backgrounds(load("backgrounds.json")),
        "classes": build_classes(),
        "feats": build_feats(load("feats.json")),
        "spells": build_spells(),
        "classSpells": build_class_spells(),
    }
    weapons, armor = build_items(load("items-base.json"))
    out["weapons"], out["armor"] = weapons, armor
    json.dump(out, open(OUT, "w"), separators=(",", ":"), ensure_ascii=False)
    sz = os.path.getsize(OUT)
    print(f"wrote {OUT}  ({sz/1024:.0f} KB)")
    for k, v in out.items():
        if isinstance(v, list): print(f"  {k}: {len(v)}")
    build_sheet(out)
    return out

def build_sheet(data):
    """Bake the PHB data into a personal single-file copy of the sheet (gitignored)."""
    here = os.path.dirname(os.path.abspath(__file__))
    app = os.path.join(here, "Character Sheet.html")
    out = os.path.join(here, "Character Sheet (PHB).html")
    if not os.path.exists(app):
        print("  (skip build_sheet: Character Sheet.html not found)"); return
    html = open(app).read()
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    new = re.sub(r'(<script id="phb-data" type="application/json">).*?(</script>)',
                 lambda m: m.group(1) + blob + m.group(2), html, count=1, flags=re.S)
    if new == html:
        print("  (skip build_sheet: no #phb-data block in Character Sheet.html yet)"); return
    open(out, "w").write(new)
    print(f"  baked -> {out}  ({os.path.getsize(out)/1024:.0f} KB)")

if __name__ == "__main__":
    main()
