#!/usr/bin/env python3
"""
Build a trimmed source-data subset for the character sheet from a local 5eTools copy.

Personal-use tool: it reads content from your own legal copy of a sourcebook (via a local 5eTools
data folder). The output (source-data.json) is copyrighted WotC content trimmed for personal use — do
NOT redistribute the data-bearing sheet or commit source-data.json.

Which book to extract defaults to the 2014 Player's Handbook ("PHB"); pass another 5eTools source code
to extract that book instead. The in-browser loader (Settings -> Source books) is the equivalent for
loading any book live; this is the offline/CLI baker.

Set the source folder via the FIVETOOLS_DATA env var, or it defaults to ~/My Drive/5etools/data.
Re-run this if the 5eTools data updates.  Usage:
    python3 build-data.py            # Player's Handbook (2014)
    python3 build-data.py XGE        # Xanathar's Guide to Everything
    SOURCE_BOOK=TCE python3 build-data.py
"""
import json, os, re, sys

SRC = os.environ.get("FIVETOOLS_DATA", os.path.expanduser("~/My Drive/5etools/data"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source-data.json")
# 5eTools source code of the book to extract (CLI arg wins, then env var, default 2014 PHB; 2024 book is "XPHB")
SRC_TAG = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SOURCE_BOOK", "PHB")).upper()
BOOK_NAMES = {"PHB": "Player's Handbook (2014)"}   # friendly names; others fall back to books.json then the code
DATA_VERSION = 9  # bump when the extracted data SHAPE changes; the app discards stored data of an older version
TOOL_TYPES = {"AT", "GS", "INS", "T"}  # artisan's tools, gaming sets, instruments, tools

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
            if tag in ("dice","damage","scaledamage","scaledice","d20","hit","dc","filter"):
                return parts[0]   # @filter is {display|page|filters...} — display is parts[0], not parts[2]
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
def is_src(x): return x.get("source") == SRC_TAG       # belongs to the book we're extracting
def book_name(code):                                   # friendly title for _meta.book
    if code in BOOK_NAMES: return BOOK_NAMES[code]
    try:
        for b in load("books.json").get("book", []):
            if (b.get("id") or b.get("source")) == code: return b.get("name", code)
    except Exception: pass
    return code

# ---- Races (+ subraces) ----
def _traits(entries):
    return [{"name": t.get("name",""), "text": entries_to_text(t.get("entries",[]))}
            for t in entries if isinstance(t, dict) and t.get("name")]

def _speed(r):
    sp = r.get("speed")
    return sp if isinstance(sp, int) else (sp or {}).get("walk", 30)

def race_langs(r):
    out = []
    for blk in r.get("languageProficiencies") or []:
        for k, v in blk.items():
            if v is True: out.append(k[:1].upper() + k[1:])
            elif isinstance(v, int) and v:
                kind = {"anyStandard": " (standard)", "anyExotic": " (exotic)", "any": ""}.get(k, " (" + k + ")")
                out.append(f"{v} language{'s' if v > 1 else ''} of your choice{kind}")
    return out

def feat_grants(r):                                 # number of feats a race/subrace grants (Variant Human = 1)
    n = 0
    for fg in (r.get("feats") or []):
        if isinstance(fg, dict):
            if "any" in fg: n += fg.get("any") or 1
            elif "anyFromCategory" in fg: n += (fg["anyFromCategory"].get("count") or 1)
            else: n += 1                            # specific granted feat
        elif fg: n += 1
    return n

def build_races(raw):
    out, bases, base_idx = [], {}, {}
    for r in raw.get("race", []):
        if not is_src(r): continue
        ab = list(r.get("ability") or [])
        fg = feat_grants(r)
        bases[r["name"]] = {"ability": ab, "speed": _speed(r), "traits": _traits(r.get("entries", [])), "langs": race_langs(r), "featGrants": fg}
        base_idx[r["name"]] = len(out)
        out.append({"name": r["name"], "ability": ab,
                    "size": "/".join(SIZE.get(s, s) for s in r.get("size", [])) or "Medium",
                    "speed": _speed(r), "traits": _traits(r.get("entries", [])), "langs": race_langs(r), "featGrants": fg})
    for s in raw.get("subrace", []):
        if not is_src(s): continue
        parent = s.get("raceName")
        if not s.get("name"):                       # unnamed "standard" subrace -> fold into base option
            i = base_idx.get(parent)
            if i is not None:
                out[i]["ability"] = (out[i]["ability"] or []) + (s.get("ability") or [])
                out[i]["traits"]  = (out[i]["traits"] or []) + _traits(s.get("entries", []))
                out[i]["langs"]   = (out[i].get("langs") or []) + race_langs(s)
                out[i]["featGrants"] = (out[i].get("featGrants") or 0) + feat_grants(s)
            continue
        base = bases.get(parent, {})               # named subrace -> "Race (Subrace)", base + subrace
        out.append({"name": f"{parent} ({s['name']})",
                    "ability": (base.get("ability") or []) + (s.get("ability") or []),
                    "size": "", "speed": _speed(s) if s.get("speed") is not None else base.get("speed", 30),
                    "subraceOf": parent,
                    "traits": (base.get("traits") or []) + _traits(s.get("entries", [])),
                    "langs": (base.get("langs") or []) + race_langs(s),
                    "featGrants": (base.get("featGrants") or 0) + feat_grants(s)})
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

def bg_equipment(b):                                # starting items + gold a background provides
    items, gold = [], 0.0
    for group in (b.get("startingEquipment") or []):
        if not isinstance(group, dict): continue
        entries = group["_"] if "_" in group else (next(iter(group.values())) if group else [])  # all of "_", else first choice
        for e in entries:
            if isinstance(e, str):
                nm = e.split("|")[0].strip()
                if nm: items.append({"n": nm, "q": 1})
            elif isinstance(e, dict):
                if e.get("containsValue"): gold += e["containsValue"] / 100.0   # copper → gp
                nm = (e.get("displayName") or e.get("special") or e.get("item") or "").split("|")[0].strip()
                if nm: items.append({"n": nm, "q": e.get("quantity", 1) or 1})
    return {"items": items, "gold": int(gold) if gold == int(gold) else round(gold, 2)}

def build_backgrounds(raw):
    out = []
    for b in raw.get("background", []):
        if not is_src(b): continue
        fixed, choose = skills_from(b.get("skillProficiencies"))
        feat = next((e for e in b.get("entries", []) if isinstance(e, dict)
                     and str(e.get("name","")).startswith("Feature:")), None)
        out.append({"name": b["name"], "skills": fixed, "skillChoose": choose,
                    "feature": {"name": feat["name"].replace("Feature: ","") if feat else "",
                                "text": entries_to_text(feat.get("entries",[])) if feat else ""},
                    "equip": bg_equipment(b)})
    return out

def build_classes():
    out = []
    for fn in sorted(os.listdir(os.path.join(SRC, "class"))):
        if not fn.startswith("class-") or not fn.endswith(".json"): continue
        data = load("class", fn)
        for c in data.get("class", []):
            if not is_src(c): continue
            sp = c.get("startingProficiencies", {})
            sk_fixed, sk_choose = skills_from(sp.get("skills"))
            seen, subs = set(), []
            for s in data.get("subclass", []):
                if not is_src(s) or s.get("className") != c["name"]: continue
                short = s.get("shortName", s["name"])
                if short in seen: continue
                seen.add(short); subs.append({"name": s["name"], "short": short})
            sub_lvl = None
            for f in c.get("classFeatures", []):
                if isinstance(f, dict) and f.get("gainSubclassFeature") and f.get("classFeature"):
                    parts = str(f["classFeature"]).split("|")
                    if len(parts) > 3 and str(parts[3]).isdigit(): sub_lvl = int(parts[3])
                    break
            se = c.get("startingEquipment", {}) or {}
            equip = {"items": [render_tags(x) for x in (se.get("default") or []) if isinstance(x, str)],
                     "gold": render_tags(se.get("goldAlternative", ""))}
            feats_c = [{"name": f.get("name", ""), "level": f.get("level", 1),
                        "text": entries_to_text(f.get("entries", []))}
                       for f in data.get("classFeature", [])
                       if f.get("source") == SRC_TAG and f.get("className") == c["name"]
                       and f.get("classSource", SRC_TAG) == SRC_TAG and f.get("name")]
            feats_c.sort(key=lambda x: (x["level"], x["name"]))
            out.append({"name": c["name"],
                        "hd": c.get("hd", {}).get("faces"),
                        "saves": c.get("proficiency", []),
                        "skillChoose": sk_choose, "skillsFixed": sk_fixed,
                        "armor": render_prof_list(sp.get("armor")), "weapons": render_prof_list(sp.get("weapons")),
                        "casterAbility": c.get("spellcastingAbility"),
                        "casterProgression": c.get("casterProgression"),
                        "cantrips": c.get("cantripProgression"),   # cantrips known per level (None if class has no cantrips)
                        "equip": equip, "features": feats_c,
                        "subclassTitle": c.get("subclassTitle",""), "subclassLevel": sub_lvl, "subclasses": subs})
    return out

def build_feats(raw):
    out = []
    for f in raw.get("feat", []):
        if not is_src(f): continue
        out.append({"name": f["name"], "text": entries_to_text(f.get("entries", []))})
    return out

def build_items(raw):
    weapons, armor = [], []
    for it in raw.get("baseitem", []):
        if not is_src(it): continue
        if it.get("weapon"):
            weapons.append({"name": it["name"], "cat": "martial" if it.get("weaponCategory")=="martial" else "simple",
                            "melee": it.get("type") == "M",
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
        if not re.match(rf"spells-{SRC_TAG.lower()}\.json$", fn): continue
        for s in load("spells", fn).get("spell", []):
            if not is_src(s): continue
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

# Items that grant a flat AC bonus (shield, rings/cloaks/bracers of protection, etc.) for the
# Armor section's bonus-item pickers. The PHB only has the Shield, so this pulls from the wider data.
def build_ac_items():
    out, seen = [{"n": "Shield", "b": 2}], {"Shield"}
    try: items = load("items.json").get("item", [])
    except Exception: return out
    for it in items:
        b = it.get("bonusAc")
        if not b: continue
        if (it.get("type") or "").split("|")[0] in ("LA", "MA", "HA"): continue   # body armor → Armor dropdown
        name = it.get("name", "")
        if name in seen: continue
        try: bonus = int(str(b).replace("+", "").strip())
        except Exception: continue
        seen.add(name); out.append({"n": name, "b": bonus})
    out.sort(key=lambda x: x["n"])
    return out

# Per-class spell lists (cantrips + levels 1-9) for EVERY class.
# Drives the per-row spell dropdowns (learn-spells classes) and the pre-filled list (full casters).
def build_class_spells():
    levels = {}
    for fn in os.listdir(os.path.join(SRC, "spells")):
        if not re.match(rf"spells-{SRC_TAG.lower()}\.json$", fn): continue
        for s in load("spells", fn).get("spell", []):
            if is_src(s): levels[s["name"]] = s.get("level", 0)
    try: src = load("spells", "sources.json").get(SRC_TAG, {})
    except Exception: return {}
    out = {}
    for name, info in src.items():
        lv = levels.get(name)
        if lv is None: continue                       # leveled book spells (cantrips included)
        for c in info.get("class", []):
            if c.get("source") == SRC_TAG:
                out.setdefault(c["name"], []).append({"n": name, "l": lv})
    for cn in out: out[cn].sort(key=lambda x: (x["l"], x["n"]))
    return out

def build_item_weights(items_base, items):   # {lowercased name: weight in lb} for inventory auto-weight
    w = {}
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if is_src(it) and it.get("weight") is not None and it.get("name"):
                w[it["name"].lower()] = it["weight"]
    return w

def build_packs(items):   # equipment packs → {name: [{name, qty}]} so the sheet can disambiguate contents
    out = {}
    for it in items.get("item", []):
        if not is_src(it): continue
        pc = it.get("packContents")
        if not pc: continue
        contents = []
        for e in pc:
            if isinstance(e, str): contents.append({"name": render_tags(e.split("|")[0]), "qty": 1})
            elif isinstance(e, dict):
                if e.get("special"): contents.append({"name": e["special"], "qty": e.get("quantity", 1)})
                elif e.get("item"): contents.append({"name": render_tags(e["item"].split("|")[0]), "qty": e.get("quantity", 1)})
        if contents: out[it["name"]] = contents
    return out

def build_languages():
    try: raw = load("languages.json")
    except Exception: return []
    return sorted({l["name"] for l in raw.get("language", []) if is_src(l) and l.get("name")})

def build_tools(items_base, items):   # AT/INS live in items-base.json; GS/T (thieves' tools, kits, gaming sets) live in items.json
    out = set()
    for it in items_base.get("baseitem", []):
        if is_src(it) and it.get("type", "").split("|")[0] in TOOL_TYPES: out.add(it["name"])
    for it in items.get("item", []):
        if is_src(it) and it.get("type", "").split("|")[0] in TOOL_TYPES: out.add(it["name"])
    return sorted(out)

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
        "_meta": {"book": book_name(SRC_TAG), "dataVersion": DATA_VERSION,
                  "source": f"D&D 5e {SRC_TAG} via local 5eTools — personal use, do not redistribute"},
        "races": build_races(races),
        "backgrounds": build_backgrounds(load("backgrounds.json")),
        "classes": build_classes(),
        "feats": build_feats(load("feats.json")),
        "spells": build_spells(),
        "classSpells": build_class_spells(),
        "acItems": build_ac_items(),
    }
    items_base = load("items-base.json")
    try: items = load("items.json")
    except Exception: items = {}
    weapons, armor = build_items(items_base)
    out["weapons"], out["armor"] = weapons, armor
    out["tools"] = build_tools(items_base, items)
    out["languages"] = build_languages()
    out["packs"] = build_packs(items)
    out["itemWeights"] = build_item_weights(items_base, items)
    json.dump(out, open(OUT, "w"), separators=(",", ":"), ensure_ascii=False)
    sz = os.path.getsize(OUT)
    print(f"wrote {OUT}  ({sz/1024:.0f} KB)")
    for k, v in out.items():
        if isinstance(v, list): print(f"  {k}: {len(v)}")
    build_sheet(out)
    return out

def build_sheet(data):
    """Bake the extracted data into a personal single-file copy of the sheet (gitignored)."""
    here = os.path.dirname(os.path.abspath(__file__))
    app = os.path.join(here, "Character Sheet.html")
    out = os.path.join(here, "Character Sheet (Source Data).html")
    if not os.path.exists(app):
        print("  (skip build_sheet: Character Sheet.html not found)"); return
    html = open(app).read()
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    new = re.sub(r'(<script id="source-data" type="application/json">).*?(</script>)',
                 lambda m: m.group(1) + blob + m.group(2), html, count=1, flags=re.S)
    if new == html:
        print("  (skip build_sheet: no #source-data block in Character Sheet.html yet)"); return
    open(out, "w").write(new)
    print(f"  baked -> {out}  ({os.path.getsize(out)/1024:.0f} KB)")

if __name__ == "__main__":
    main()
