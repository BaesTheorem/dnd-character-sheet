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
DATA_VERSION = 11  # bump when the extracted data SHAPE changes; the app discards stored data of an older version
TOOL_TYPES = {"AT", "GS", "INS", "T"}  # artisan's tools, gaming sets, instruments, tools

SCHOOL = {"A":"Abjuration","C":"Conjuration","D":"Divination","E":"Enchantment",
          "V":"Evocation","I":"Illusion","N":"Necromancy","T":"Transmutation"}
DMG = {"S":"slashing","P":"piercing","B":"bludgeoning","R":"radiant","F":"fire",
       "C":"cold","L":"lightning","A":"acid","O":"force","Y":"psychic","T":"thunder","N":"necrotic"}
SIZE = {"T":"Tiny","S":"Small","M":"Medium","L":"Large","H":"Huge","G":"Gargantuan"}
WPROP = {"A":"ammunition","F":"finesse","H":"heavy","L":"light","LD":"loading","R":"reach",
         "S":"special","T":"thrown","2H":"two-handed","V":"versatile"}

# ---- 5eTools {@tag ...} markup -> plain text ----
_tag = re.compile(r"\{@(\w+)(?: ([^{}]*))?\}")
_ATK = {"mw":"Melee Weapon Attack","rw":"Ranged Weapon Attack","mw,rw":"Melee or Ranged Weapon Attack",
        "ms":"Melee Spell Attack","rs":"Ranged Spell Attack","ms,rs":"Melee or Ranged Spell Attack"}
def render_tags(s):
    if not isinstance(s, str): return s
    prev = None
    while prev != s:
        prev = s
        def repl(m):
            tag, body = m.group(1), m.group(2) or ""
            parts = body.split("|")
            if tag == "h": return "Hit: "                                  # monster damage-line marker
            if tag == "atk": return (_ATK.get(body.strip(), body)) + ":"
            if tag == "hit": return parts[0] if parts[0][:1] in "+-" else "+" + parts[0]
            if tag == "dc": return "DC " + parts[0]
            if tag == "recharge": return f"(Recharge {parts[0]}-6)" if parts[0] else "(Recharge 6)"
            if tag in ("dice","damage","scaledamage","scaledice","d20","filter"):
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

def _merge_prof(a, b):   # union two prof blocks (base race + subrace), preserving order, dedup
    out = {}
    for k in ("skills", "tools", "languages", "weapons", "armor", "other"):
        merged = list((a or {}).get(k, [])) + list((b or {}).get(k, []))
        if merged: out[k] = list(dict.fromkeys(merged))
    ch = (a or {}).get("skillChoose") or (b or {}).get("skillChoose")
    if ch: out["skillChoose"] = ch
    return out

def build_races(raw):
    out, bases, base_idx = [], {}, {}
    for r in raw.get("race", []):
        if not is_src(r): continue
        ab = list(r.get("ability") or [])
        fg = feat_grants(r); pf = prof_block(r); rs = damage_resist(r)
        bases[r["name"]] = {"ability": ab, "speed": _speed(r), "traits": _traits(r.get("entries", [])), "featGrants": fg, "prof": pf, "resist": rs}
        base_idx[r["name"]] = len(out)
        out.append({"name": r["name"], "ability": ab,
                    "size": "/".join(SIZE.get(s, s) for s in r.get("size", [])) or "Medium",
                    "speed": _speed(r), "traits": _traits(r.get("entries", [])), "featGrants": fg, "prof": pf, "resist": rs})
    for s in raw.get("subrace", []):
        if not is_src(s): continue
        parent = s.get("raceName")
        if not s.get("name"):                       # unnamed "standard" subrace -> fold into base option
            i = base_idx.get(parent)
            if i is not None:
                out[i]["ability"] = (out[i]["ability"] or []) + (s.get("ability") or [])
                out[i]["traits"]  = (out[i]["traits"] or []) + _traits(s.get("entries", []))
                out[i]["featGrants"] = (out[i].get("featGrants") or 0) + feat_grants(s)
                out[i]["prof"]    = _merge_prof(out[i].get("prof"), prof_block(s))
                out[i]["resist"]  = (out[i].get("resist") or []) + damage_resist(s)
            continue
        base = bases.get(parent, {})               # named subrace -> "Race (Subrace)", base + subrace
        out.append({"name": f"{parent} ({s['name']})",
                    "ability": (base.get("ability") or []) + (s.get("ability") or []),
                    "size": "", "speed": _speed(s) if s.get("speed") is not None else base.get("speed", 30),
                    "subraceOf": parent,
                    "traits": (base.get("traits") or []) + _traits(s.get("entries", [])),
                    "featGrants": (base.get("featGrants") or 0) + feat_grants(s),
                    "prof": _merge_prof(base.get("prof"), prof_block(s)),
                    "resist": (base.get("resist") or []) + damage_resist(s)})
    return out

def skills_from(spo):
    fixed, choose = [], None
    for blk in spo or []:
        for k, v in blk.items():
            if k == "choose" and isinstance(v, dict):
                choose = {"from": v.get("from", []), "count": v.get("count", 1)}
            elif v is True:
                fixed.append(k)
            elif k == "any" and isinstance(v, int):
                choose = {"from": [], "count": v}
    return fixed, choose

# ---- Shared proficiency normalization (races / backgrounds / feats / classes) ----
def _clean(s):           # strip 5eTools {@item ...|...} markup and the |source suffix
    return render_tags(str(s)).split("|")[0].strip()
def _titlecase(s):
    return " ".join((w[:1].upper() + w[1:]) if w else w for w in str(s).split(" "))
_ANY_LABELS = {"any": "of your choice", "anyStandard": "standard language of your choice",
    "anyExotic": "exotic language of your choice", "anyArtisansTool": "artisan's tools of your choice",
    "anyTool": "tools of your choice", "anyMusicalInstrument": "musical instrument of your choice",
    "anyGamingSet": "gaming set of your choice", "anyInstrument": "instrument of your choice",
    "anySkill": "skill of your choice"}
def _pretty(tok):        # render a 5eTools proficiency token readably ("anyGamingSet" -> "any gaming set")
    t = str(tok)
    if t in _ANY_LABELS: return _ANY_LABELS[t]
    if t.startswith("any"): return "any " + " ".join(w.lower() for w in re.findall(r"[A-Z][a-z]*|[a-z]+", t[3:]))
    return _titlecase(_clean(t))
def _norm_prof(arr):     # -> list of display strings: fixed proficiencies + "choose N (...)" phrases
    out = []
    for blk in arr or []:
        if isinstance(blk, str): out.append(_titlecase(_clean(blk))); continue
        if not isinstance(blk, dict): continue
        for k, v in blk.items():
            if k == "choose":
                for ch in (v if isinstance(v, list) else [v]):
                    if not isinstance(ch, dict): continue
                    cnt = ch.get("count", ch.get("amount", 1))
                    frm = [_pretty(x) for x in ch.get("from", [])]
                    out.append(f"choose {cnt} ({', '.join(frm)})" if frm else f"choose {cnt}")
            elif v is True: out.append(_titlecase(_clean(k)))
            elif isinstance(v, int) and v: out.append(f"{v} {_ANY_LABELS.get(k, _pretty(k))}")
    return out
def prof_block(obj):     # structured skills (for checkboxes) + display lists for the Proficiencies box
    sk_fixed, sk_choose = skills_from(obj.get("skillProficiencies"))
    out = {}
    if sk_fixed: out["skills"] = sk_fixed
    if sk_choose: out["skillChoose"] = sk_choose
    for key, dest in (("toolProficiencies", "tools"), ("languageProficiencies", "languages"),
                      ("weaponProficiencies", "weapons"), ("armorProficiencies", "armor")):
        v = _norm_prof(obj.get(key))
        if v: out[dest] = v
    stl = _norm_prof(obj.get("skillToolLanguageProficiencies"))
    if stl: out["other"] = stl
    return out
def feat_ability(arr):   # {fixed:{abbr:n}, choose:{from,amount}} | None
    fixed, choose = {}, None
    for blk in arr or []:
        if not isinstance(blk, dict): continue
        if isinstance(blk.get("choose"), dict):
            choose = {"from": blk["choose"].get("from", []), "amount": blk["choose"].get("amount", 1)}
        else:
            for k, v in blk.items():
                if isinstance(v, int): fixed[k] = fixed.get(k, 0) + v
    return {"fixed": fixed, "choose": choose} if (fixed or choose) else None
def feat_saves(arr):     # {fixed:[abbr], choose:{from}} | None  (e.g. Resilient)
    fixed, choose = [], None
    for blk in arr or []:
        if not isinstance(blk, dict): continue
        if isinstance(blk.get("choose"), dict): choose = {"from": blk["choose"].get("from", [])}
        else:
            for k, v in blk.items():
                if v is True: fixed.append(k)
    return {"fixed": fixed, "choose": choose} if (fixed or choose) else None
def damage_resist(obj):  # damage resistances as display strings (e.g. Dwarf poison, Tiefling fire)
    out = []
    for r in obj.get("resist") or []:
        if isinstance(r, str): out.append(_titlecase(r))
        elif isinstance(r, dict):
            if isinstance(r.get("choose"), dict):
                frm = [_titlecase(x) for x in r["choose"].get("from", [])]
                out.append(f"choose {r['choose'].get('count',1)} ({', '.join(frm)})")
            elif r.get("resist"): out.append(_titlecase(", ".join(r["resist"]) if isinstance(r["resist"], list) else str(r["resist"])))
    return out

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
        out.append({"name": b["name"], "skills": fixed, "skillChoose": choose, "prof": prof_block(b),
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
            cls_prof = prof_block({"toolProficiencies": sp.get("tools"), "armorProficiencies": sp.get("armor"), "weaponProficiencies": sp.get("weapons")})
            seen, subs = set(), []
            for s in data.get("subclass", []):
                if not is_src(s) or s.get("className") != c["name"]: continue
                short = s.get("shortName", s["name"])
                if short in seen: continue
                seen.add(short)
                sfeats = [{"name": f.get("name",""), "level": f.get("level",1), "text": entries_to_text(f.get("entries",[]))}
                          for f in data.get("subclassFeature", [])
                          if is_src(f) and f.get("className")==c["name"] and f.get("subclassShortName")==short
                          and f.get("classSource", SRC_TAG)==SRC_TAG and f.get("name")]
                sfeats.sort(key=lambda x: (x["level"], x["name"]))
                sspells = []
                for blk in s.get("additionalSpells") or []:
                    prep = blk.get("prepared") or blk.get("known") or blk.get("innate") or {}
                    for lv, names in prep.items():
                        for nm in (names or []):
                            if isinstance(nm, str): sspells.append({"n": _titlecase(_clean(nm)), "l": int(lv) if str(lv).isdigit() else 0})
                subs.append({"name": s["name"], "short": short, "features": sfeats, "spells": sspells})
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
                        "skillChoose": sk_choose, "skillsFixed": sk_fixed, "prof": cls_prof,
                        "armor": render_prof_list(sp.get("armor")), "weapons": render_prof_list(sp.get("weapons")),
                        "casterAbility": c.get("spellcastingAbility"),
                        "casterProgression": c.get("casterProgression"),
                        "cantrips": c.get("cantripProgression"),   # cantrips known per level (None if class has no cantrips)
                        "spellsKnown": c.get("spellsKnownProgression"),   # spells-known per level for known casters
                        "equip": equip, "features": feats_c,
                        "subclassTitle": c.get("subclassTitle",""), "subclassLevel": sub_lvl, "subclasses": subs})
    return out

def build_feats(raw):
    out = []
    for f in raw.get("feat", []):
        if not is_src(f): continue
        out.append({"name": f["name"], "text": entries_to_text(f.get("entries", [])),
                    "ability": feat_ability(f.get("ability")), "saves": feat_saves(f.get("savingThrowProficiencies")),
                    "prof": prof_block(f)})
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
            mat = comp["m"].get("text", "") if isinstance(comp.get("m"), dict) else ""
            dur0 = (s.get("duration") or [{}])[0]
            spells.append({"name": s["name"], "level": s.get("level", 0),
                           "school": SCHOOL.get(s.get("school",""), s.get("school","")),
                           "time": entries_to_text(s.get("time", [])) if isinstance(s.get("time"), str) else
                                   "; ".join(f"{t.get('number','')} {t.get('unit','')}" for t in s.get("time", [])),
                           "range": render_range(s.get("range", {})),
                           "components": "".join(k.upper() for k in ("v","s","m") if comp.get(k)),
                           "duration": render_duration(s.get("duration", [])),
                           "text": entries_to_text(s.get("entries", [])),
                           "higher": entries_to_text(s.get("entriesHigherLevel", [])),
                           "ritual": bool(s.get("meta", {}).get("ritual")),
                           "conc": bool(dur0.get("concentration")), "material": mat})
    spells.sort(key=lambda x: (x["level"], x["name"]))
    return spells

# ---- Bestiary (monster stat blocks for the Companions & Forms page) ----
ALIGN = {"L":"lawful","N":"neutral","C":"chaotic","G":"good","E":"evil","U":"unaligned","A":"any alignment"}
def _mon_size(s):
    sizes = s if isinstance(s, list) else [s]
    return "/".join(SIZE.get(x, x) for x in sizes) or "Medium"
def _mon_type(t):
    if isinstance(t, str): return t
    if isinstance(t, dict):
        base = t.get("type", "")
        tags = t.get("tags", [])
        tg = ", ".join(x if isinstance(x, str) else x.get("tag","") for x in tags)
        return base + (f" ({tg})" if tg else "")
    return ""
def _is_beast(t):
    return (t == "beast") or (isinstance(t, dict) and t.get("type") == "beast")
def _mon_align(a):
    if not a: return ""
    out = []
    def add(x):
        if isinstance(x, str): out.append(ALIGN.get(x, x))
        elif isinstance(x, list): [add(y) for y in x]
        elif isinstance(x, dict):
            if x.get("special"): out.append(x["special"])
            elif x.get("alignment"): add(x["alignment"])
    add(a)
    return " ".join(p for p in out if p)
def _mon_ac(ac):
    if not ac: return None, ""
    a = ac[0]
    if isinstance(a, dict): return a.get("ac"), ", ".join(a.get("from", []) or [])
    return a, ""
def _spd1(v):
    if isinstance(v, dict): return f"{v.get('number','')} ft." + (f" {v['condition']}" if v.get("condition") else "")
    return f"{v} ft."
def _mon_speed(sp):
    if isinstance(sp, (int, float)): return f"{sp} ft."
    if not isinstance(sp, dict): return ""
    parts = []
    if "walk" in sp: parts.append(_spd1(sp["walk"]))
    for k in ("burrow","climb","fly","swim"):
        if k in sp: parts.append(f"{k} " + _spd1(sp[k]))
    return ", ".join(parts)
def _mon_kv(d):                                # {"dex":"+6","con":"+13"} -> "Dex +6, Con +13"
    if not isinstance(d, dict): return ""
    return ", ".join(f"{k[:1].upper()+k[1:]} {v}" for k, v in d.items())
def _mon_dmg(arr):                             # resist / immune / vulnerable lists (strings or {resist:[],note})
    out = []
    for x in arr or []:
        if isinstance(x, str): out.append(x)
        elif isinstance(x, dict):
            key = next((k for k in ("resist","immune","vulnerable") if k in x), None)
            names = ", ".join(i for i in (x.get(key) or []) if isinstance(i, str)) if key else ""
            note = x.get("note", "")
            out.append((names + (" " + note if note else "")).strip())
    return "; ".join(p for p in out if p)
def _mon_senses(senses, passive):
    parts = list(senses or [])
    if passive is not None: parts.append(f"passive Perception {passive}")
    return ", ".join(parts)
def cr_num(cr):
    if isinstance(cr, dict): cr = cr.get("cr", "0")
    if isinstance(cr, (int, float)): return float(cr)
    s = str(cr)
    if "/" in s:
        try: a, b = s.split("/"); return float(a) / float(b)
        except Exception: return 0.0
    try: return float(s)
    except Exception: return 0.0
def cr_pb(n):
    import math
    return 2 if n < 5 else 2 + math.floor((n - 1) / 4)
def _mon_block(arr):                           # trait/action/reaction/legendary -> [{name,text}]
    out = []
    for e in arr or []:
        if not isinstance(e, dict): continue
        out.append({"name": e.get("name", ""), "text": entries_to_text(e.get("entries", []))})
    return out
def _mon_spellcasting(sc):
    if not sc: return ""
    chunks = []
    for blk in sc:
        chunks.append(entries_to_text(blk.get("headerEntries", [])))
        for grp in ("will","daily","spells"):
            g = blk.get(grp)
            if isinstance(g, list): chunks.append("At will: " + ", ".join(render_tags(x) for x in g))
            elif isinstance(g, dict):
                for lvl, info in g.items():
                    sp = info.get("spells", info) if isinstance(info, dict) else info
                    names = ", ".join(render_tags(x) for x in (sp or []))
                    chunks.append(f"{lvl}: {names}")
        chunks.append(entries_to_text(blk.get("footerEntries", [])))
    return "\n".join(c for c in chunks if c)
def build_monsters():
    fn = os.path.join(SRC, "bestiary", f"bestiary-{SRC_TAG.lower()}.json")
    if not os.path.exists(fn): return []
    out = []
    for m in json.load(open(fn)).get("monster", []):
        if not is_src(m) or m.get("_copy"): continue
        ac, acnote = _mon_ac(m.get("ac"))
        hp = m.get("hp", {}) or {}
        crn = cr_num(m.get("cr", 0))
        out.append({"name": m["name"], "size": _mon_size(m.get("size","M")), "type": _mon_type(m.get("type","")),
            "beast": _is_beast(m.get("type","")), "align": _mon_align(m.get("alignment")),
            "ac": ac, "acNote": acnote, "hp": hp.get("average"), "hpFormula": hp.get("formula",""),
            "speed": _mon_speed(m.get("speed", {})),
            "str": m.get("str"), "dex": m.get("dex"), "con": m.get("con"),
            "int": m.get("int"), "wis": m.get("wis"), "cha": m.get("cha"),
            "save": _mon_kv(m.get("save")), "skill": _mon_kv(m.get("skill")),
            "senses": _mon_senses(m.get("senses"), m.get("passive")),
            "resist": _mon_dmg(m.get("resist")), "immune": _mon_dmg(m.get("immune")),
            "vuln": _mon_dmg(m.get("vulnerable")), "condImmune": ", ".join(x for x in (m.get("conditionImmune") or []) if isinstance(x,str)),
            "languages": ", ".join(m.get("languages", []) or []),
            "cr": str(m.get("cr","")) if not isinstance(m.get("cr"), dict) else str(m["cr"].get("cr","")), "crNum": crn, "pb": cr_pb(crn),
            "traits": _mon_block(m.get("trait")), "actions": _mon_block(m.get("action")),
            "reactions": _mon_block(m.get("reaction")), "legendary": _mon_block(m.get("legendary")),
            "spellcasting": _mon_spellcasting(m.get("spellcasting"))})
    out.sort(key=lambda x: x["name"])
    return out

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
        "monsters": build_monsters(),
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
