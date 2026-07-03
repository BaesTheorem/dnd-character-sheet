#!/usr/bin/env python3
"""
Build a trimmed source-data subset for the character sheet from a local 5eTools copy.

It reads content from a local 5eTools data folder and writes a trimmed source-data.json that the sheet
consumes.

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
DATA_VERSION = 33  # bump when the extracted data SHAPE changes; the app discards stored data of an older version
# v13: subclass featChoices + opt/optGroup, class mcReq/mcProf. v14: subclass `choosers`. v15: `futuristic` list. v16: tool/instrument lists exclude magic items. v17: `modern` list. v18: race `flavor` (lore) from fluff-races.json. v19/v20 (spellBonusItems etc.) were applied to the committed sheet WITHOUT a build-data.py rebuild — this script is BEHIND the baked #source-data on those fields; do NOT run a full rebuild without reconciling them first. v21/v22: race `ancestry` = {kind, choices:[{dragon,dmgType,shape,save}], breath:{die,scale}} (Draconic Ancestry → breath weapon + resistance; v22 added the breath progression + Fizban Chromatic/Gem/Metallic variants). v23: race `naturalWeapons`=[{name,die,dmgType,ability}] (claws/horns/bite → feature-attack rows). NOTE: subclass/feat attacks (Soulknife, Armorer, Sun Soul, Polearm Master…) are NOT data — they live in the FEATURE_ATTACKS registry in index.html's app JS. v24: `magicWeapons` {name:{base,bonus,rider}} (equipped named magic weapon → Attacks row) + itemText now also fed for charged magic items (Limited Features). v25 (itemText charged-item expansion) and v26 (per-spell `dmg` field) were ALSO applied to the baked sheet WITHOUT a build-data.py rebuild — same "BEHIND" caveat as v19/v20. v27: `itemSpells` {name:[{n,u}]} = magic-item spell grants (from 5etools `attachedSpells`) → the "Granted Spells" table; build_item_spells() mirrors it here, but the script is still behind on the v19–v26 reconciliation, so do NOT run a full rebuild without reconciling. v28: `attackSpells` [names] = every spell needing an attack roll (5etools `spellAttack`) → the Spell Sniper attack-cantrip filter; build_attack_spells() mirrors it (same BEHIND caveat). v29: `spellUpcast` {name:{up,at}} = per-slot-level damage scaling (from 5etools `@scaledamage`) → the Granted Spells upcast picker; build_spell_upcast() mirrors it. v30: `itemAdvText` {name:text} = a magic item's (dis)advantage sentences → the live "From equipped items" Defenses line (scanned at runtime by scanDefenses); build_item_adv_text() mirrors it (same BEHIND caveat). v31: the in-browser loader (index.html etBook) now ALSO extracts magicWeapons/itemSpells/attackSpells/spellUpcast/itemAdvText (ports of build_magic_weapons/build_variant_weapons/build_item_spells/build_attack_spells/build_spell_upcast/build_item_adv_text) — so a live source load reaches parity with this script. Note the loader is per-source (it filters magicWeapons/attackSpells by the loaded book), whereas this script extracts some of them globally across all 5etools files, so this script's output is a superset for a single book. v32: loader also extracts race `ancestry` (Draconic Ancestry breath weapon, dragon_ancestry port) + `naturalWeapons` (claws/horns/bite, natural_weapons port) — loader↔build-data.py parity now COMPLETE. v33: `optionalFeatures` {name:text} = de-baked invocation/maneuver/metamagic/fighting-style rules text (from optionalfeatures.json EI/MV:B/MM/FS:*); the JS loader (etOptionalFeatures) produces it so the verbatim WotC text lives in the DATA layer, not app code (OPTIONAL_FEATURES + FIGHTING_STYLES consts are now mechanics-only). build_optional_features() mirrors it here (per-source, like the loader). Mirror HTML's DATA_VERSION.
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
# Known 2024 ("One D&D") source codes (mirror index.html's RULESET_2024). Belt-and-suspenders next to the date rule.
_R2024 = {"XPHB", "XDMG", "XMM", "XSCREEN", "XSAC", "ABH", "FRAIF", "FRHOF", "NF", "LFL", "EFA"}
_pub_cache = None
def _published(code):                                  # 5eTools publish date for a source code, from books.json + adventures.json
    global _pub_cache
    if _pub_cache is None:
        _pub_cache = {}
        for fn in ("books.json", "adventures.json"):
            try: data = load(fn)
            except Exception: continue
            for b in data.get("book", []) + data.get("adventure", []):
                c = b.get("id") or b.get("source")
                if c: _pub_cache[c] = b.get("published", "")
    return _pub_cache.get(code, "") or _pub_cache.get((code or "").upper(), "")
def is_2024(x):                                        # XPHB/XDMG/2024 entry — out of scope for this 2014-rules sheet
    # NOTE: 5eTools leaves `edition` UNSET on many 2024 reprints (e.g. XDMG's "Bag of Tricks"), so the old edition-only
    # check silently missed them and their 2024 text overwrote the 2014 version on a name collision. Also key on the
    # source code + publish date (the 2024 PHB launch), mirroring index.html's isBook2024, so the guard actually fires.
    ed = (x.get("edition") or "").lower()
    if ed: return ed == "one" or "2024" in ed
    src = x.get("source") or ""
    if src.upper() in _R2024: return True
    return _published(src) >= "2024-09-01"
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

_NW_DMG = "acid|bludgeoning|cold|fire|force|lightning|necrotic|piercing|poison|psychic|radiant|slashing|thunder"
_NW_AB = {"strength":"str","dexterity":"dex","constitution":"con","wisdom":"wis","intelligence":"int","charisma":"cha"}
_NW_WORD = r"claws?|bite|horns?|hoo(?:f|ves)|talons?|fangs?|maw|ram|tail|tusks?|gore|beak"
def natural_weapons(traits):
    """Racial natural-weapon attacks [{name,die,dmgType,ability}] parsed from trait prose
    ("you can use your claws to make unarmed strikes… 1d6 + your Strength modifier slashing").
    Name = trait name if it's a body-part word, else the body part from the sentence."""
    out = {}
    for t in traits:
        nm, tx = t.get("name", ""), t.get("text", "")
        if not re.search(r"unarmed strike|natural weapon|simple melee weapon", tx, re.I):
            continue
        for sent in re.split(r'(?<=[.;])\s+', tx):
            m = re.search(r'(\d+d\d+)', sent)
            ty = re.search(r'\b(' + _NW_DMG + r')\s+damage', sent, re.I)
            if not (m and ty and re.search(r'unarmed strike|natural weapon|on a hit|with (?:it|them|this)', sent, re.I)):
                continue
            ab = re.search(r'your\s+(Strength|Dexterity|Constitution|Wisdom|Intelligence|Charisma)\s+modifier', tx, re.I)
            name = nm if re.search(_NW_WORD, nm, re.I) else None
            if not name:
                bw = re.search(_NW_WORD, sent, re.I) or re.search(_NW_WORD, tx, re.I)
                name = bw.group(0).title() if bw else nm
            out.setdefault(name, {"name": name, "die": m.group(1), "dmgType": ty.group(1).lower(),
                                  "ability": _NW_AB.get((ab.group(1).lower() if ab else "strength"), "str")})
            break
    return list(out.values())

def _speed(r):
    sp = r.get("speed")
    return sp if isinstance(sp, int) else (sp or {}).get("walk", 30)

def _speed_extra(r):     # non-walk movement modes (fly/swim/climb/burrow); True = equal to walking speed
    sp = r.get("speed")
    if not isinstance(sp, dict): return ""
    walk, out = sp.get("walk", 30), []
    for mode in ("fly", "swim", "climb", "burrow"):
        v = sp.get(mode)
        if v is None or v is False: continue
        out.append(f"{mode} {walk if v is True else v} ft.")
    return ", ".join(out)

def _race_spell_names(r):   # concrete cantrip/innate spell names a race grants (for the Racial Spells reminder)
    names = []
    for blk in r.get("additionalSpells") or []:
        for k in ("known", "innate", "prepared"):
            if blk.get(k): _collect_spell_names(blk[k], names)
    seen, out = set(), []
    for n in (_titlecase(_clean(x)) for x in names):
        if n and n not in seen: seen.add(n); out.append(n)
    return out

def race_langs(r):
    out = []
    for blk in r.get("languageProficiencies") or []:
        for k, v in blk.items():
            if v is True: out.append(k[:1].upper() + k[1:])
            elif isinstance(v, int) and v:
                kind = {"anyStandard": " (standard)", "anyExotic": " (exotic)", "any": ""}.get(k, " (" + k + ")")
                out.append(f"{v} language{'s' if v > 1 else ''} of your choice{kind}")
    return out

def lang_choose(r):                                 # number of free language choices a race grants
    n = 0
    for blk in r.get("languageProficiencies") or []:
        if not isinstance(blk, dict): continue
        for k, v in blk.items():
            if k in ("any", "anyStandard", "anyExotic") and isinstance(v, int): n += v
            elif k == "choose" and isinstance(v, dict): n += v.get("count", 1)
    return n

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

def _race_fluff(entries):
    """Flatten a race's fluff lore into [{name,text}] sections (loose intro paragraphs collapse into one leading "" section)."""
    out, intro = [], []
    def walk(lst):
        for e in (lst if isinstance(lst, list) else [lst]):
            if isinstance(e, str):
                t = render_tags(e)
                if t: intro.append(t)
            elif isinstance(e, dict):
                if e.get("type") == "quote": continue
                if e.get("name") and e.get("entries"):
                    t = entries_to_text(e["entries"])
                    if t: out.append({"name": e["name"], "text": t})
                elif e.get("entries"):
                    walk(e["entries"])
    walk(entries)
    if intro: out.insert(0, {"name": "", "text": "\n\n".join(intro)})
    return out

def _race_flavor_map():
    """name -> [{name,text}] flavor sections, from the book's fluff-races file (if present)."""
    try: fl = load("fluff-races.json")
    except Exception: return {}
    return {f["name"]: _race_fluff(f.get("entries", []))
            for f in fl.get("raceFluff", []) if f.get("source") == SRC_TAG and f.get("entries")}

def build_races(raw):
    out, bases, base_idx = [], {}, {}
    flavor = _race_flavor_map()
    for r in raw.get("race", []):
        if is_2024(r): continue   # never ingest XPHB/2024 races: they share races.json with 2014 and, keyed by name, would overwrite the base and leak (e.g. Elf -> "Elven Lineage")
        ab = list(r.get("ability") or [])
        fg = feat_grants(r); pf = prof_block(r); rs = damage_resist(r)
        dv, lc = r.get("darkvision") or 0, lang_choose(r)
        rsp = _race_spell_names(r); rsx = _speed_extra(r); fl = flavor.get(r["name"], []); rexp = _extract_spells(r)[1]
        anc = dragon_ancestry(r)   # Dragonborn: structured draconic ancestry choices (breath weapon + resistance)
        bases[r["name"]] = {"ability": ab, "size": "/".join(SIZE.get(s, s) for s in r.get("size", [])) or "Medium", "speed": _speed(r), "speedExtra": rsx, "traits": _traits(r.get("entries", [])), "featGrants": fg, "prof": pf, "resist": rs, "darkvision": dv, "langChoose": lc, "spells": rsp, "expanded": rexp, "flavor": fl, "ancestry": anc}
        if not is_src(r): continue    # keep EVERY race in `bases` (any book) so a cross-book subrace inherits its parent; only output THIS book's races
        base_idx[r["name"]] = len(out)
        ro = {"name": r["name"], "ability": ab,
              "size": "/".join(SIZE.get(s, s) for s in r.get("size", [])) or "Medium",
              "speed": _speed(r), "speedExtra": rsx, "traits": _traits(r.get("entries", [])), "featGrants": fg, "prof": pf, "resist": rs,
              "darkvision": dv, "langChoose": lc, "spells": rsp, "flavor": fl}
        if rexp: ro["expanded"] = rexp   # e.g. dragonmark "Spells of the Mark"
        if anc: ro["ancestry"] = anc   # full {kind, choices, breath} — drives the ancestry picker + breath-weapon attack
        nw = natural_weapons(ro["traits"])   # claws/horns/bite… → feature-attack rows
        if nw: ro["naturalWeapons"] = nw
        out.append(ro)
    for s in raw.get("subrace", []):
        if not is_src(s) or is_2024(s): continue
        parent = s.get("raceName")
        sdv, slc = s.get("darkvision") or 0, lang_choose(s)
        if not s.get("name"):                       # unnamed "standard" subrace -> fold into base option
            i = base_idx.get(parent)
            if i is not None:
                out[i]["ability"] = (out[i]["ability"] or []) + (s.get("ability") or [])
                out[i]["traits"]  = (out[i]["traits"] or []) + _traits(s.get("entries", []))
                out[i]["featGrants"] = (out[i].get("featGrants") or 0) + feat_grants(s)
                out[i]["prof"]    = _merge_prof(out[i].get("prof"), prof_block(s))
                out[i]["resist"]  = (out[i].get("resist") or []) + damage_resist(s)
                out[i]["darkvision"] = max(out[i].get("darkvision") or 0, sdv)
                out[i]["langChoose"] = (out[i].get("langChoose") or 0) + slc
                out[i]["spells"] = (out[i].get("spells") or []) + _race_spell_names(s)
            continue
        base = bases.get(parent, {})               # named subrace -> "Race (Subrace)", base + subrace
        sexp = (base.get("expanded") or []) + _extract_spells(s)[1]   # dragonmark subraces add a "Spells of the Mark" expanded list
        so = {"name": f"{parent} ({s['name']})",
              "ability": (base.get("ability") or []) + (s.get("ability") or []),
              "size": base.get("size", ""), "speed": _speed(s) if s.get("speed") is not None else base.get("speed", 30),
              "speedExtra": _speed_extra(s) if s.get("speed") is not None else base.get("speedExtra", ""),
              "subraceOf": parent,
              "traits": (base.get("traits") or []) + _traits(s.get("entries", [])),
              "featGrants": (base.get("featGrants") or 0) + feat_grants(s),
              "prof": _merge_prof(base.get("prof"), prof_block(s)),
              "resist": (base.get("resist") or []) + damage_resist(s),
              "darkvision": max(base.get("darkvision") or 0, sdv), "langChoose": (base.get("langChoose") or 0) + slc,
              "spells": (base.get("spells") or []) + _race_spell_names(s),
              "flavor": flavor.get(f"{parent} ({s['name']})", base.get("flavor", []))}
        if sexp: so["expanded"] = sexp
        sanc = dragon_ancestry(s) or base.get("ancestry")   # Draconblood/Ravenite inherit draconic ancestry from base Dragonborn
        if sanc: so["ancestry"] = sanc
        snw = natural_weapons(so["traits"])
        if snw: so["naturalWeapons"] = snw
        out.append(so)
    for o in out:
        if "custom lineage" in o["name"].lower(): o["variableSkillDarkvision"] = True   # TCE: skill OR darkvision
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
def _clean(s):           # strip 5eTools {@item ...|...} markup, the |source suffix, and #level tags
    return render_tags(str(s)).split("|")[0].split("#")[0].strip()
def _titlecase(s):
    return " ".join((w[:1].upper() + w[1:]) if w else w for w in str(s).split(" "))
def _chooser_option_blocks(entries):   # every `options` block referencing sub-features → (options, count). The caller decides which are real "choose one" choosers (see build_classes).
    out = []
    def walk(e):
        if isinstance(e, list):
            for x in e: walk(x)
        elif isinstance(e, dict):
            if e.get("type") == "options":
                refs = []
                for o in e.get("entries", []) or []:
                    if isinstance(o, dict):
                        ref = (o.get("subclassFeature") if o.get("type") == "refSubclassFeature"
                               else o.get("optionalfeature") if o.get("type") == "refOptionalfeature" else None)   # match JS: only typed refs
                        if ref: refs.append(str(ref).split("|")[0].strip())
                if refs: out.append((refs, e.get("count")))
            for x in e.get("entries", []) or []: walk(x)
    walk(entries)
    return out
def normalize_subclass(sub):   # mirror of JS normalizeSubclass: derive opt/optGroup tags + featChoices from features + choosers
    feats, choosers = sub.get("features", []), sub.get("choosers", [])
    ref_names = set()
    for c in choosers:
        for n in c.get("options", []): ref_names.add(n)
    for f in feats:
        if f.get("name") in ref_names:
            f["opt"] = f["name"]
            g = next((c for c in choosers if c["level"] == f.get("level", 1)), None)
            f["optGroup"] = g["name"] if g else f.get("optGroup", "")
        else:
            f.pop("opt", None); f.pop("optGroup", None)
    present = lambda c: [n for n in c.get("options", []) if any(f.get("name") == n for f in feats)]
    groups = {}
    for c in sorted(choosers, key=lambda c: c["level"]):
        groups.setdefault("|".join(sorted(present(c))), []).append(c)
    fc = []
    for g in groups.values():
        opts = present(g[0])
        if opts: fc.append({"label": g[0]["name"], "options": opts, "levels": [c["level"] for c in g]})
    sub["featChoices"] = fc
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
# Class starting tools come from the human-readable `tools` prose (not the structured toolProficiencies): only the
# prose preserves "X or Y" either/or choices, which the structured form flattens into two independent grants. Emits
# canonical tokens the sheet's tool-picker resolves:
#   "Herbalism Kit"                                            (concrete)
#   "3 musical instrument of your choice"                      (single kind, N picks)
#   "1 artisan's tools or musical instrument of your choice"   (either/or — ONE pick spanning both kinds)
_TOOL_NUMWORD = {"a": 1, "an": 1, "any": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
def _tool_kind(phrase):
    p = phrase.lower()
    if "artisan" in p: return "artisan's tools"
    if "instrument" in p: return "musical instrument"
    return None
def _tool_count(phrase):
    for w in re.findall(r"\d+|[a-z]+", phrase.lower()):
        if w.isdigit(): return int(w)
        if w in _TOOL_NUMWORD: return _TOOL_NUMWORD[w]
    return 1
def _norm_class_tools(lst):
    out = []
    for raw in lst or []:
        s = _clean(raw); low = s.lower()
        if "artisan" not in low and "instrument" not in low and "of your choice" not in low:
            out.append(_titlecase(s)); continue                       # concrete tool (Herbalism Kit, Thieves' Tools)
        kinds = []
        for part in re.split(r"\bor\b", s, flags=re.I):               # "X or Y" → choice across kinds
            k = _tool_kind(part)
            if k and k not in kinds: kinds.append(k)
        if len(kinds) >= 2: out.append("1 " + " or ".join(kinds) + " of your choice")   # either/or = one pick
        elif len(kinds) == 1: out.append(f"{_tool_count(s)} {kinds[0]} of your choice")
        else: out.append(_titlecase(s))
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

def _anc_find(pred, o):
    if isinstance(o, dict):
        if pred(o): return o
        for v in o.values():
            t = _anc_find(pred, v)
            if t: return t
    elif isinstance(o, list):
        for x in o:
            t = _anc_find(pred, x)
            if t: return t
    return None

def _breath_progression(txt):   # base dice + die size + scaling thresholds from the Breath Weapon prose
    m = re.search(r'(\d+)d(\d+)', txt or "")
    if not m: return None
    base, die = int(m.group(1)), int(m.group(2))
    levels = [int(x) for x in re.findall(r'(\d+)(?:st|nd|rd|th)\s+level', txt or "") if int(x) > 1][:3]
    return {"die": die, "scale": [[1, base]] + [[L, base + 1 + i] for i, L in enumerate(levels)]}

def _breath_shape_save(txt):    # shape + save from prose (Fizban variants: uniform across ancestries)
    sm = re.search(r'(\d+)[- ]?foot\s+(line|cone)', txt or "", re.I)
    shape = f"{sm.group(1)} ft. {sm.group(2).lower()}" if sm else ""
    sv = re.search(r'(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving throw', txt or "", re.I)
    return shape, (sv.group(1)[:3].title() if sv else "Dex")

def dragon_ancestry(r):
    """Full Draconic Ancestry object {kind, choices:[{dragon,dmgType,shape,save}], breath:{die,scale}}
    so the sheet can offer an ancestry picker and derive the breath-weapon attack + resistance.
    Handles PHB (3-col table → shape+save per row; 2d6 @1/6/11/16) AND Fizban Chromatic/Gem/Metallic
    (2-col table + uniform shape/save from the Breath Weapon prose; 1d10 @1/5/11/17). None if no table."""
    entries = r.get("entries", [])
    tbl = _anc_find(lambda o: o.get("type") == "table" and "ancestry" in str(o.get("caption", "")).lower(), entries)
    if not tbl: return None
    bw = _anc_find(lambda o: o.get("name") == "Breath Weapon" and o.get("entries"), entries)
    bw_txt = entries_to_text(bw.get("entries", [])) if bw else ""
    breath = _breath_progression(bw_txt) or {"die": 6, "scale": [[1, 2], [6, 3], [11, 4], [16, 5]]}
    cols = len(tbl.get("colLabels") or [])
    choices = []
    if cols >= 3:                                                          # PHB: Dragon | Damage Type | Breath Weapon
        for row in tbl.get("rows", []):
            if len(row) < 3: continue
            dragon, dmg, cell = _clean(str(row[0])).strip(), _titlecase(_clean(str(row[1])).strip()), _clean(str(row[2])).strip()
            m = re.search(r'\(([A-Za-z]+)\.?\s*save\)', cell)
            save = (m.group(1)[:3].title() if m else "Dex")
            shape = re.sub(r'\s*\([^)]*\)\s*$', '', cell).strip()
            if dragon and dmg: choices.append({"dragon": dragon, "dmgType": dmg, "shape": shape, "save": save})
    else:                                                                  # Fizban: Dragon | Damage Type (shape+save from prose)
        sh, sv = _breath_shape_save(bw_txt)
        for row in tbl.get("rows", []):
            if len(row) < 2: continue
            dragon, dmg = _clean(str(row[0])).strip(), _titlecase(_clean(str(row[1])).strip())
            if dragon and dmg: choices.append({"dragon": dragon, "dmgType": dmg, "shape": sh, "save": sv})
    return {"kind": "draconic", "choices": choices, "breath": breath} if choices else None

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
        bg = {"name": b["name"], "skills": fixed, "skillChoose": choose, "prof": prof_block(b),
              "feature": {"name": feat["name"].replace("Feature: ","") if feat else "",
                          "text": entries_to_text(feat.get("entries",[])) if feat else ""},
              "equip": bg_equipment(b)}
        sp, exp = _extract_spells(b)   # Ravnica guild backgrounds grant a guild-spells list via additionalSpells.expanded
        if sp: bg["spells"] = sp
        if exp: bg["expanded"] = exp
        out.append(bg)
    return out

def _collect_spell_names(v, out):
    # additionalSpells value may be a string, array, or nested object (Sun Soul: {resource:{"2":[...]}}); skip choose/filter directives
    if isinstance(v, str):
        if "=" not in v: out.append(v)
    elif isinstance(v, list):
        for x in v: _collect_spell_names(x, out)
    elif isinstance(v, dict):
        for k, val in v.items():
            if k in ("choose", "all"): continue
            _collect_spell_names(val, out)

def _extract_spells(obj):
    # Parse an entity's additionalSpells into (spells, expanded), mirroring the subclass logic:
    # prepared/known/innate = always-granted ("#c" marks a cantrip → level 0); expanded = added-to-your-list.
    _lvl = lambda lv, nm: 0 if "#c" in str(nm).lower() else (int(str(lv).lstrip("sS")) if str(lv).lstrip("sS").isdigit() else 0)
    spells, expanded, seen = [], [], set()
    for blk in obj.get("additionalSpells") or []:
        for grp in ("prepared", "known", "innate"):
            for lv, val in (blk.get(grp) or {}).items():
                names = []; _collect_spell_names(val, names)
                for nm in names:
                    n = _titlecase(_clean(nm)); spl = _lvl(lv, nm); key = (n.lower(), spl)
                    if key in seen: continue
                    seen.add(key); spells.append({"n": n, "l": spl})
        for lv, val in (blk.get("expanded") or {}).items():
            names = []; _collect_spell_names(val, names)
            for nm in names:
                expanded.append({"n": _titlecase(_clean(nm)), "l": _lvl(lv, nm)})
    return spells, expanded

def build_classes():
    out = []
    for fn in sorted(os.listdir(os.path.join(SRC, "class"))):
        if not fn.startswith("class-") or not fn.endswith(".json"): continue
        data = load("class", fn)
        for c in data.get("class", []):
            if not is_src(c): continue
            sp = c.get("startingProficiencies", {})
            sk_fixed, sk_choose = skills_from(sp.get("skills"))
            cls_prof = prof_block({"armorProficiencies": sp.get("armor"), "weaponProficiencies": sp.get("weapons")})
            ct = _norm_class_tools(sp.get("tools"))   # canonical tool tokens (preserves "artisan's tools OR instrument")
            if ct: cls_prof["tools"] = ct
            seen, subs = set(), []
            for s in data.get("subclass", []):
                if not is_src(s) or s.get("className") != c["name"]: continue
                short = s.get("shortName", s["name"])
                if short in seen: continue
                seen.add(short)
                # NOT filtered by subclassSource — same as JS — so a same-book subclass keeps all its features.
                raw_feats = [f for f in data.get("subclassFeature", [])
                          if is_src(f) and f.get("className")==c["name"] and f.get("subclassShortName")==short and f.get("name")]
                choosers = []                                   # features offering a "choose one" set (Totem Spirit, …)
                _raw_ch = []                                     # (name, level, options, count) for every options block
                for cf in raw_feats:
                    for refs, cnt in _chooser_option_blocks(cf.get("entries", [])):
                        _raw_ch.append((cf.get("name"), cf.get("level",1), refs, cnt))
                _set_count = {}                                  # a set spanning 2+ features is a PERSISTENT choose-one (e.g. Storm Herald's Desert/Sea/Tundra across Storm Aura/Soul/Raging Storm)
                for _,_,refs,_c in _raw_ch:
                    k = tuple(sorted(refs)); _set_count[k] = _set_count.get(k,0)+1
                for nm, lv, refs, cnt in _raw_ch:
                    firm = cnt is not None and cnt < len(refs)              # explicit "choose N of M" (Totem Spirit, Maneuvers)
                    persistent = _set_count[tuple(sorted(refs))] >= 2      # same option-set recurs → one-time choice that carries forward
                    # no count and referenced by a single feature = "gain ALL of these" (e.g. Soulknife's Psionic Power / Soul Blades) → NOT a chooser
                    if firm or persistent: choosers.append({"name": nm, "level": lv, "options": refs})
                sfeats = [{"name": f.get("name",""), "level": f.get("level",1), "text": entries_to_text(f.get("entries",[]))} for f in raw_feats]
                sfeats.sort(key=lambda x: (x["level"], x["name"]))
                _lvl = lambda lv: int(str(lv).lstrip("sS")) if str(lv).lstrip("sS").isdigit() else 0   # "s1"→1 (expanded-spell level keys)
                sspells = []; sexpanded = []; _seen_sp = set()
                for blk in s.get("additionalSpells") or []:
                    for grp in ("prepared", "known", "innate"):   # merge ALL grant types — one block can grant a prepared spell AND a known cantrip (e.g. Star Map: Guiding Bolt + Guidance), so never short-circuit between them
                        for lv, val in (blk.get(grp) or {}).items():
                            names = []; _collect_spell_names(val, names)   # val may be array or nested object (e.g. Sun Soul resource:{2:[...]})
                            for nm in names:
                                n = _titlecase(_clean(nm))
                                spl = 0 if "#c" in str(nm).lower() else _lvl(lv)   # the level key is the ACQUISITION level, not the spell level; the "#c" marker flags a cantrip (spell level 0)
                                key = (n.lower(), spl)
                                if key in _seen_sp: continue
                                _seen_sp.add(key); sspells.append({"n": n, "l": spl})
                    for lv, val in (blk.get("expanded") or {}).items():   # Warlock patron expanded lists
                        names = []; _collect_spell_names(val, names)
                        for nm in names:
                            sexpanded.append({"n": _titlecase(_clean(nm)), "l": _lvl(lv)})
                sub = {"name": s["name"], "short": short, "features": sfeats, "choosers": choosers, "spells": sspells, "expanded": sexpanded, "featChoices": []}
                normalize_subclass(sub)
                subs.append(sub)
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
            mc = c.get("multiclassing", {}) or {}              # multiclass prereq + limited proficiencies gained when multiclassing in
            pg = mc.get("proficienciesGained")
            mc_prof = prof_block({"armorProficiencies": pg.get("armor"), "weaponProficiencies": pg.get("weapons"),
                                  "toolProficiencies": pg.get("tools"), "skillProficiencies": pg.get("skills")}) if pg else None
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
                        "mcReq": mc.get("requirements"), "mcProf": mc_prof,
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

def build_items(raw, items=None):
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
    # named magic armors (Elven Chain, Dwarven Plate, ...) live in items.json, not baseitem
    for it in (items or {}).get("item", []):
        if not is_src(it): continue
        ty = (it.get("type") or "").split("|")[0]
        if ty in ("LA","MA","HA") and it.get("ac") is not None:
            ba = it.get("bonusAc")
            bonus = int(str(ba).replace("+","")) if ba else 0   # e.g. Elven Chain ac 13 + bonusAc +1 -> base 14
            armor.append({"name": it["name"], "ac": it.get("ac") + bonus, "type": ty,
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

def build_attack_spells():   # names of every spell that requires a spell attack roll (5etools spellAttack) → Spell Sniper cantrip filter
    names = set()
    for fn in os.listdir(os.path.join(SRC, "spells")):
        if not re.match(r"spells-[a-z0-9]+\.json$", fn): continue
        for s in load("spells", fn).get("spell", []):
            if s.get("spellAttack") and s.get("name"): names.add(s["name"])
    return sorted(names)

def build_optional_features():   # v33: {name: text} for invocations/maneuvers/metamagic/fighting-styles — de-baked WotC rules text lives in the DATA layer, not app code (mirror of the JS etOptionalFeatures loader)
    out = {}
    try: ofs = load("optionalfeatures.json").get("optionalfeature", [])
    except Exception: return out
    for o in ofs:
        if not is_src(o) or not o.get("name"): continue
        txt = entries_to_text(o.get("entries", []))
        if txt: out[o["name"]] = txt
    return out

_SCALEDAMAGE = re.compile(r"\{@scaledamage\s+([^|]+)\|([^|]+)\|([^}]+)\}")
def build_spell_upcast(spell_names):   # {name: {up: per-slot-level dice, at: base level}} from 5etools @scaledamage → upcast damage picker
    out = {}
    keep = set(spell_names)
    for fn in os.listdir(os.path.join(SRC, "spells")):
        if not re.match(r"spells-[a-z0-9]+\.json$", fn): continue
        for s in load("spells", fn).get("spell", []):
            nm = s.get("name")
            if nm not in keep or nm in out: continue
            m = _SCALEDAMAGE.search(json.dumps(s.get("entriesHigherLevel") or ""))
            if not m: continue
            rng = m.group(2).strip()
            at = int(rng.split("-")[0]) if "-" in rng else (s.get("level") or 1)
            out[nm] = {"up": m.group(3).strip(), "at": at}
    return out

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
def _monster_img_map():
    # name(lower) -> first internal art path (relative to /img/), from the bestiary fluff file.
    fn = os.path.join(SRC, "bestiary", f"fluff-bestiary-{SRC_TAG.lower()}.json")
    if not os.path.exists(fn): return {}
    out = {}
    for fl in json.load(open(fn)).get("monsterFluff", []):
        if fl.get("source") != SRC_TAG: continue
        for im in fl.get("images", []) or []:
            h = im.get("href") or {}
            if h.get("type") == "internal" and h.get("path"):
                out[fl["name"].lower()] = h["path"]; break
    return out

def build_monsters():
    fn = os.path.join(SRC, "bestiary", f"bestiary-{SRC_TAG.lower()}.json")
    if not os.path.exists(fn): return []
    imgs = _monster_img_map()
    out = []
    for m in json.load(open(fn)).get("monster", []):
        if not is_src(m) or m.get("_copy"): continue
        ac, acnote = _mon_ac(m.get("ac"))
        hp = m.get("hp", {}) or {}
        crn = cr_num(m.get("cr", 0))
        img = imgs.get(m["name"].lower())
        rec = ({"img": img} if img else {})
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
            "spellcasting": _mon_spellcasting(m.get("spellcasting")), **rec})
    out.sort(key=lambda x: x["name"])
    return out

# Items that grant a flat AC bonus (shield, rings/cloaks/bracers of protection, etc.) for the
# Armor section's bonus-item pickers. The PHB only has the Shield, so this pulls from the wider data.
def build_ac_items():
    out, seen = [{"n": "Shield", "b": 2}], {"Shield"}
    try: items = load("items.json").get("item", [])
    except Exception: return out
    for it in items:
        if is_2024(it): continue                       # skip 2024 reprints/originals — this is a 2014-rules sheet
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
            # c["source"] is the book that GRANTED access, not the spell's book — don't filter on it (e.g. TCE grants PHB spells to Artificer)
            out.setdefault(c["name"], []).append({"n": name, "l": lv})
        # classVariant = this book adds an existing-class spell (e.g. XGE adds Toll the Dead to Cleric/Wizard/Warlock)
        for c in info.get("classVariant", []):
            out.setdefault(c["name"], []).append({"n": name, "l": lv})
    for cn in out:
        seen = set(); out[cn] = [x for x in out[cn] if not (x["n"] in seen or seen.add(x["n"]))]
        out[cn].sort(key=lambda x: (x["l"], x["n"]))
    return out

def build_item_weights(items_base, items):   # {lowercased name: weight in lb} for inventory auto-weight
    w = {}
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if is_src(it) and it.get("weight") is not None and it.get("name"):
                w[it["name"].lower()] = it["weight"]
    return w

def build_item_names(items_base, items):   # every item name (base + magic) for the inventory autocomplete
    names = set()
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if is_src(it) and it.get("name"): names.add(it["name"])
    return sorted(names)
def build_by_age(items_base, items, age):   # item names tagged with a given tech age → filtered out unless that age is enabled
    names = set()
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if is_src(it) and it.get("name") and it.get("age") == age: names.add(it["name"])
    return sorted(names)

def build_futuristic(items_base, items):   # laser/antimatter weapons, powered armor
    return build_by_age(items_base, items, "futuristic")

def build_modern(items_base, items):       # pistols/rifles/shotguns/dynamite
    return build_by_age(items_base, items, "modern")

LIMITED_SIGNAL = re.compile(r"\brest\b|\bdawn\b|\bcharges\b|\bper day\b|\bexpend", re.I)
def build_item_text(items_base, items):   # descriptions of magic items that look like they have limited daily uses (Bag of Tricks, etc.)
    out = {}
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if not is_src(it) or not it.get("name"): continue
            if not (it.get("rarity") in MAGIC_RARITY or it.get("wondrous") or it.get("reqAttune")): continue
            txt = entries_to_text(it.get("entries", []))
            if txt and LIMITED_SIGNAL.search(txt): out[it["name"]] = txt[:1600]   # keep enough to reach a late "regains charges at dawn" clause
    return out

_ADV_SIGNAL = re.compile(r"\b(?:advantage|disadvantage)\b", re.I)
def build_item_adv_text(items_base, items):   # v30: just the (dis)advantage sentences from a magic item's text → the live "From equipped items" Defenses line
    out = {}
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if not is_src(it) or not it.get("name") or it["name"] in out: continue
            if not (it.get("rarity") in MAGIC_RARITY or it.get("wondrous") or it.get("reqAttune")): continue
            txt = entries_to_text(it.get("entries", []))
            sents = [s.strip() for s in re.split(r"(?<=[.;])\s+", txt) if _ADV_SIGNAL.search(s)]
            if sents: out[it["name"]] = " ".join(sents)[:600]
    return out

def build_containers(items_base, items):   # weightless containers (Bag of Holding, Heward's Handy Haversack, ...)
    out = set()
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            cc = it.get("containerCapacity")
            if is_src(it) and it.get("name") and cc and cc.get("weightless"): out.add(it["name"])
    return sorted(out)

def build_attune_items(items_base, items):   # items that require attunement, for the Attuned Items picker
    out = set()
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if is_src(it) and it.get("name") and it.get("reqAttune"): out.add(it["name"])
    return sorted(out)

MAGIC_RARITY = {"common", "uncommon", "rare", "very rare", "legendary", "artifact", "unknown (magic)"}
def build_magic_items(items_base, items):   # magic items (rarity / wondrous / attunement), so the Equipped box can appear on them
    out = set()
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if not is_src(it) or not it.get("name"): continue
            if it.get("rarity") in MAGIC_RARITY or it.get("wondrous") or it.get("reqAttune"): out.add(it["name"])
    return sorted(out)

def _itemspell_clean(s):   # 5etools spell ref → display Title Case
    s = str(s).split("|")[0].split("#")[0].strip()
    s = re.sub(r"\s*\(.*?\)\s*$", "", s)
    if not s: return ""
    small = {"of","the","a","an","and","to","from","with","in","on"}
    return " ".join(w.capitalize() if (i == 0 or w.lower() not in small) else w.lower() for i, w in enumerate(s.split()))

def _itemspell_use(bucket, key):
    m = re.match(r"\d+", str(key)); n = int(m.group()) if m else 1
    if bucket == "charges": return "1 charge" if n == 1 else f"{n} charges"
    if bucket == "daily":   return f"{n}/day"
    if bucket == "rest":    return f"{n}/rest"
    if bucket == "limited": return f"{n} uses"
    return ""

def _parse_attached_spells(att):   # 5etools attachedSpells → [{"n": SpellName, "u": useLabel}]
    out, seen = [], set()
    def add(name, u):
        nm = _itemspell_clean(name)
        if not nm: return
        k = (nm.lower(), u)
        if k in seen: return
        seen.add(k); out.append({"n": nm, "u": u})
    if isinstance(att, list):
        for s in att: add(s, "")
    elif isinstance(att, dict):
        for s in (att.get("will") or []):   add(s, "at will")
        for s in (att.get("ritual") or []): add(s, "ritual")
        for bucket in ("charges", "daily", "rest", "limited"):
            blk = att.get(bucket) or {}
            if isinstance(blk, dict):
                for key, arr in blk.items():
                    for s in (arr or []): add(s, _itemspell_use(bucket, key))
        res = att.get("resource") or {}
        if isinstance(res, dict):
            for arr in res.values():
                for s in (arr or []): add(s, "")
    return out

def build_item_spells(items_base, items):   # magic items that let you cast a spell → {name: [{n,u}]} (from 5etools attachedSpells)
    out = {}
    for coll, key in ((items_base, "baseitem"), (items, "item")):
        for it in coll.get(key, []):
            if not is_src(it) or not it.get("name") or not it.get("attachedSpells"): continue
            if not (it.get("rarity") in MAGIC_RARITY or it.get("wondrous") or it.get("reqAttune")): continue   # same universe as the magic-item picker
            rows = _parse_attached_spells(it["attachedSpells"])
            if rows: out[it["name"]] = rows
    return out

def build_magic_weapons(items):   # named magic weapons → {name_lc: {base, bonus, rider}} so an equipped one becomes an Attacks row
    out = {}
    for it in items.get("item", []):
        if is_2024(it): continue                       # skip 2024 reprints/originals — this is a 2014-rules sheet
        nm, bi = it.get("name"), it.get("baseItem")
        if not nm or not bi or it.get("type") not in ("M", "R"): continue
        m = re.search(r'\+(\d+)', str(it.get("bonusWeapon") or "")); bonus = int(m.group(1)) if m else 0
        txt = entries_to_text(it.get("entries", []))
        rid = re.search(r'extra (\d+d\d+)\s+([a-z]+) damage', txt, re.I)   # damage rider (Mace of Disruption → +2d6 radiant)
        out[nm.lower()] = {"base": re.sub(r'\|.*$', '', str(bi)).strip().title(), "bonus": bonus,
                           "rider": (f"+{rid.group(1)} {rid.group(2).lower()}" if rid else "")}
    return out

def _variant_rider(entries):
    rid = re.search(r'extra (\d+d\d+)\s+([A-Za-z]+) damage', entries_to_text(entries) or "", re.I)
    return f"+{rid.group(1)} {rid.group(2).lower()}" if rid else ""
def _variant_matches(cond, b):
    for k, val in cond.items():
        bv = b.get(k)
        if k == "type":
            if str(bv).split("|")[0] != str(val).split("|")[0]: return False
        elif k == "name":
            if b.get("name") != val: return False
        elif bv != val: return False
    return True
def build_variant_weapons(items_base):   # magic-variant templates × base weapons → named magic weapons (Flame Tongue Longsword, Vicious Greataxe, …)
    try: mv = load("magicvariants.json").get("magicvariant", [])
    except Exception: return {}
    bases = [b for b in items_base.get("baseitem", []) if is_src(b) and b.get("weapon")]
    out = {}
    for v in mv:
        inh = v.get("inherits", {}); pre, suf = inh.get("namePrefix"), inh.get("nameSuffix")
        m = re.search(r'\+(\d+)', str(inh.get("bonusWeapon") or "")); bonus = int(m.group(1)) if m else 0
        rider = _variant_rider(inh.get("entries", []))
        if bonus == 0 and not rider and not (pre or suf): continue
        for b in bases:
            req = v.get("requires") or []
            if not any(_variant_matches(c, b) for c in req): continue
            exc = v.get("excludes")
            if exc and _variant_matches(exc, b): continue
            full = (pre + b["name"]) if pre else (b["name"] + suf) if suf else b["name"]
            out.setdefault(full.lower(), {"base": b["name"], "bonus": bonus, "rider": rider})
    return out

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

def is_mundane_tool(it):   # a real tool/instrument you can be proficient with — not a magic item (+N/wondrous/attunement) sharing a tool type
    nm = it.get("name", "")
    if not nm or it.get("wondrous") or it.get("reqAttune") or it.get("rarity") in MAGIC_RARITY or it.get("bonusWeapon") or it.get("bonusAc") or it.get("bonusSpellAttack"): return False
    if re.match(r"^\+\d", nm): return False   # "+1 Rhythm-Maker's Drum"
    return True

def build_tools(items_base, items):   # AT/INS live in items-base.json; GS/T (thieves' tools, kits, gaming sets) live in items.json
    out = set()
    for it in list(items_base.get("baseitem", [])) + list(items.get("item", [])):
        if is_src(it) and it.get("type", "").split("|")[0] in TOOL_TYPES and is_mundane_tool(it): out.add(it["name"])
    return sorted(out)

def build_tool_cats(items_base, items):   # tools split by category so a generic "of your choice" grant can offer concrete picks
    artisan, instrument = set(), set()
    for it in list(items_base.get("baseitem", [])) + list(items.get("item", [])):
        if not is_src(it) or not is_mundane_tool(it): continue
        t = it.get("type", "").split("|")[0]
        if t == "AT": artisan.add(it["name"])
        elif t == "INS": instrument.add(it["name"])
    return {"artisan": sorted(artisan), "instrument": sorted(instrument)}

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
    weapons, armor = build_items(items_base, items)
    out["weapons"], out["armor"] = weapons, armor
    out["tools"] = build_tools(items_base, items)
    out["toolCats"] = build_tool_cats(items_base, items)
    out["languages"] = build_languages()
    out["packs"] = build_packs(items)
    out["itemWeights"] = build_item_weights(items_base, items)
    out["itemNames"] = build_item_names(items_base, items)
    out["futuristic"] = build_futuristic(items_base, items)
    out["modern"] = build_modern(items_base, items)
    out["containers"] = build_containers(items_base, items)
    out["attuneItems"] = build_attune_items(items_base, items)
    out["magicItems"] = build_magic_items(items_base, items)
    out["itemText"] = build_item_text(items_base, items)
    out["itemSpells"] = build_item_spells(items_base, items)   # v27: magic-item spell grants → "Granted Spells" table
    out["attackSpells"] = build_attack_spells()                # v28: spell-attack-roll names → Spell Sniper cantrip filter
    out["spellUpcast"] = build_spell_upcast([s["name"] for s in out["spells"]])   # v29: per-slot-level damage scaling → upcast picker
    out["itemAdvText"] = build_item_adv_text(items_base, items)   # v30: item (dis)advantage sentences → live Defenses item line
    out["magicWeapons"] = {**build_variant_weapons(items_base), **build_magic_weapons(items)}   # variant templates (Flame Tongue ×bases) + concrete named magic weapons → Attacks rows
    out["optionalFeatures"] = build_optional_features()        # v33: de-baked invocation/maneuver/metamagic/fighting-style rules text → DATA layer
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
