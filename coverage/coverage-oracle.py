#!/usr/bin/env python3
"""
coverage-oracle.py  --  MPMB mechanics coverage diff for the from-scratch 5e sheet.

WHY THIS EXISTS
---------------
We keep discovering, one frustrated character at a time, that some feat / item /
race / class feature isn't fully wired into the sheet's automation. MPMB's
"Character Record Sheet" already encodes the mechanical effect of (nearly) every
piece of 5e content in a documented data syntax. This tool turns that into a
finite, sortable punch-list instead of whack-a-mole:

  1. EXTRACT  the canonical mechanical vocabulary from MPMB's *syntax docs*
              (`additional content syntax/*.js`)  -> coverage/mpmb-schema.json
     and      which mechanical fields every baked entity actually uses
              (`_variables/Lists*.js`)            -> coverage/mpmb-entities.json
  2. DIFF     those against a hand-maintained capability manifest
              (coverage/capability-manifest.json) describing what THIS sheet
              already implements, seeded by a best-effort probe of index.html.
  3. REPORT   coverage/COVERAGE-REPORT.md -- capability table + entity punch-list
              ranked by how many entities each missing capability blocks.

The MPMB side is exact. The "do we implement it?" side is only as good as the
manifest, so the manifest is the source of truth: the probe just seeds guesses
you then lock in. Re-run after every build to catch regressions.

USAGE
-----
  # one-time / when MPMB updates: clone the repo, then extract
  git clone --depth 1 https://github.com/morepurplemorebetter/MPMBs-Character-Record-Sheet.git /tmp/mpmb-repo
  python3 coverage/coverage-oracle.py --extract --mpmb /tmp/mpmb-repo

  # every run after a build: regenerate the report from the committed JSON
  python3 coverage/coverage-oracle.py

Flags:
  --extract        re-parse the MPMB repo (writes mpmb-schema.json + mpmb-entities.json)
  --mpmb PATH      path to a clone of the MPMB repo (default /tmp/mpmb-repo)
  --sheet PATH     path to index.html (default ../index.html relative to this file)
  --no-probe       don't auto-probe index.html; trust the manifest as-is
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

SCHEMA_JSON = os.path.join(HERE, "mpmb-schema.json")
ENTITIES_JSON = os.path.join(HERE, "mpmb-entities.json")
MANIFEST_JSON = os.path.join(HERE, "capability-manifest.json")
REPORT_MD = os.path.join(HERE, "COVERAGE-REPORT.md")

# Syntax-doc filename  ->  entity-type label
SYNTAX_FILES = {
    "feat (FeatsList).js": "feat",
    "magic item (MagicItemsList).js": "magicitem",
    "class (ClassList)_unfinished.js": "class",
    "weapon (WeaponsList).js": "weapon",
    "armor (ArmourList).js": "armor",
    "ammunition (AmmoList).js": "ammo",
    "creature, wild shape option (CreatureList).js": "creature",
    "companion template option (CompanionList).js": "companion",
    "adventuring gear - equipment (GearList).js": "gear",
    "adventuring gear - tool (ToolsList).js": "tool",
    "_common attributes.js": "common",
    "_common spell list object.js": "spelllist",
}

# _variables list file  ->  entity-type label  (the baked content we diff against)
VARIABLE_FILES = {
    "ListsClasses.js": "class",
    "ListsRaces.js": "race",
    "ListsFeats.js": "feat",
    "ListsMagicItems.js": "magicitem",
    "ListsGear.js": "gear",
    "ListsCreatures.js": "creature",
    "ListsCompanions.js": "companion",
}

# calcChanges sub-hooks + eval-style fields = "procedural" (arbitrary JS in MPMB;
# cannot be copied, must be reimplemented as engine logic).
PROCEDURAL = {
    "calcChanges", "atkAdd", "atkCalc", "spellAdd", "spellCalc", "spellList",
    "changeeval", "eval", "removeeval", "prereqeval", "submenu", "choiceeval",
    "hp",  # calcChanges.hp
}

# Fields that carry no automation -- pure flavor/identity. Excluded from the
# mechanical coverage math (but still parsed so the schema is complete).
COSMETIC = {
    "name", "sortname", "plural", "regExpSearch", "source", "description",
    "descriptionFull", "descriptionShorter", "descriptionLong", "nameTooltip",
    "defaultExcluded", "notLegal", "addToKnown", "rarity", "type", "subtype",
    "iFileName", "RequiredSheetVersion", "SourceList", "prerequisite",
    "selfChoosing", "variant", "variants", "ammunition", "list", "age",
    "height", "weight", "heightMetric", "weightMetric", "trait", "fullname",
    "abilitiesText", "abilities", "tooltip", "spellcastingFactor",  # factor is class plumbing, not a bonus
}

# ----------------------------------------------------------------------------
# EXTRACT: parse MPMB syntax docs -> canonical field vocabulary
# ----------------------------------------------------------------------------

# A documented field looks like, on one line (note the leading "/*" comment
# opener in the header form, or an inline "name : val, // OPTIONAL //" example):
#     /*<tab>action // OPTIONAL //
#     usages : 8, // REQUIRED //
# Capture the first identifier on the line, then the REQUIRED/OPTIONAL marker.
FIELD_DOC_RE = re.compile(
    r'^\s*(?:/\*\s*)?([A-Za-z_][A-Za-z0-9_]*)\b[^/\n]*?//\s*'
    r'(REQUIRED|OPTIONAL|RECOMMENDED|EITHER)\b',
)
USE_RE = re.compile(r'^\s*USE:\s*(.+?)\s*$')
TYPE_RE = re.compile(r'^\s*TYPE:\s*(.+?)\s*$')


def extract_schema(mpmb_path):
    syntax_dir = os.path.join(mpmb_path, "additional content syntax")
    if not os.path.isdir(syntax_dir):
        sys.exit(f"!! syntax dir not found: {syntax_dir}\n   clone the MPMB repo first (see header).")

    schema = {}  # field -> {required, type, use, entity_types:set, procedural}
    for fname, etype in SYNTAX_FILES.items():
        fpath = os.path.join(syntax_dir, fname)
        if not os.path.isfile(fpath):
            print(f"   (skip, missing: {fname})", file=sys.stderr)
            continue
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines):
            m = FIELD_DOC_RE.match(line)
            if not m:
                continue
            field = m.group(1).split(".")[-1]  # calcChanges.atkAdd -> atkAdd
            req = m.group(2).strip()
            # look ahead a few lines for TYPE / USE
            ftype = use = ""
            for j in range(i + 1, min(i + 8, len(lines))):
                if not ftype:
                    mt = TYPE_RE.match(lines[j])
                    if mt:
                        ftype = mt.group(1)
                if not use:
                    mu = USE_RE.match(lines[j])
                    if mu:
                        use = mu.group(1)
                if ftype and use:
                    break
            rec = schema.setdefault(field, {
                "required": req, "type": ftype, "use": use,
                "entity_types": set(), "procedural": field in PROCEDURAL,
            })
            rec["entity_types"].add(etype)
            if not rec["use"] and use:
                rec["use"] = use
            if not rec["type"] and ftype:
                rec["type"] = ftype
            if field in PROCEDURAL:
                rec["procedural"] = True

    # serialize (sets -> sorted lists)
    out = {}
    for field, rec in sorted(schema.items()):
        out[field] = {
            "required": rec["required"],
            "type": rec["type"],
            "use": rec["use"],
            "entity_types": sorted(rec["entity_types"]),
            "procedural": rec["procedural"],
            "cosmetic": field in COSMETIC,
        }
    with open(SCHEMA_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"   wrote {SCHEMA_JSON}  ({len(out)} documented fields)")
    return out


# ----------------------------------------------------------------------------
# EXTRACT: parse _variables/Lists*.js -> per-entity mechanical field usage
# ----------------------------------------------------------------------------

def split_top_level_entries(text):
    """Yield (key, entry_text) for each top-level entity in a Lists*.js file.

    MPMB formats these uniformly: every top-level entry's key sits at the start
    of a line indented by exactly one tab, e.g.  \\t"boots of speed" : {
    We slice between consecutive such lines. This sidesteps brace-matching,
    which MPMB's embedded regex literals (`regExpSearch : /.../`) break.
    """
    lines = text.splitlines(keepends=True)
    key_re = re.compile(r'^\t"((?:[^"\\]|\\.)*)"\s*:\s*\{')
    starts = [(i, key_re.match(ln).group(1))
              for i, ln in enumerate(lines) if key_re.match(ln)]
    entries = []
    for idx, (line_no, key) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        entries.append((key, "".join(lines[line_no:end])))
    return entries


FIELD_TOKEN_RE = re.compile(r'(?:^|[\{\[,\s])([A-Za-z_][A-Za-z0-9_]*)\s*:')


def fields_used(entry_text):
    """Set of field names appearing anywhere in an entry (any nesting depth)."""
    return set(FIELD_TOKEN_RE.findall(entry_text))


def extract_entities(mpmb_path, schema):
    var_dir = os.path.join(mpmb_path, "_variables")
    if not os.path.isdir(var_dir):
        sys.exit(f"!! _variables dir not found: {var_dir}")

    mechanical_fields = {f for f, r in schema.items()
                         if not r["cosmetic"]}
    entities = []  # {name, type, fields:[...], mech_fields:[...]}
    for fname, etype in VARIABLE_FILES.items():
        fpath = os.path.join(var_dir, fname)
        if not os.path.isfile(fpath):
            print(f"   (skip, missing: {fname})", file=sys.stderr)
            continue
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for key, entry_text in split_top_level_entries(text):
            used = fields_used(entry_text)
            mech = sorted(used & mechanical_fields)
            entities.append({
                "name": key,
                "type": etype,
                "mech_fields": mech,
            })
    with open(ENTITIES_JSON, "w", encoding="utf-8") as fh:
        json.dump(entities, fh, indent=2)
    by_type = defaultdict(int)
    for e in entities:
        by_type[e["type"]] += 1
    print(f"   wrote {ENTITIES_JSON}  ({len(entities)} entities: "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_type.items())) + ")")
    return entities


# ----------------------------------------------------------------------------
# EXTRACT (full content): parse a SAVED MPMB PDF that has content imported.
#
# The repo + the stock PDF only ship SRD content. But once you import the full
# WotC/UA library into the MPMB PDF and save, ALL of it is stored (minified,
# inside escaped JS strings) in a form field named "Stringified". Mining that
# gives the *complete* entity set (all feats/races/items/subclasses), which is
# what makes the punch-list actually complete.
# ----------------------------------------------------------------------------

# List-variable name in MPMB content  ->  entity-type label
LIST_TYPES = {
    "FeatsList": "feat", "RaceList": "race", "ClassList": "class",
    "ClassSubList": "subclass", "MagicItemsList": "magicitem",
    "WeaponsList": "weapon", "ArmourList": "armor", "CreatureList": "creature",
    "CompanionList": "companion", "AmmoList": "ammo", "GearList": "gear",
    "ToolsList": "gear", "BackgroundList": "background",
}


def _resolve(o):
    from pypdf.generic import IndirectObject
    while isinstance(o, IndirectObject):
        o = o.get_object()
    return o


def get_stringified_field(pdf_path):
    """Return the (largest) 'Stringified' AcroForm field value -- MPMB's import
    store -- as text. Empty string if not present."""
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("!! pypdf required for --pdf; pip3 install pypdf")
    r = PdfReader(pdf_path)
    form = _resolve(r.trailer["/Root"].get("/AcroForm"))
    if not form:
        return ""
    best = b""

    def walk(f):
        nonlocal best
        f = _resolve(f)
        if str(f.get("/T")) == "Stringified":
            v = _resolve(f.get("/V"))
            d = v.get_data() if hasattr(v, "get_data") else str(v).encode("latin-1", "replace")
            if len(d) > len(best):
                best = d
        for k in (f.get("/Kids") or []):
            walk(k)
    for f in (form.get("/Fields") or []):
        walk(f)
    return best.decode("utf-8", "replace")


def js_double_strings(text):
    """Concatenate every double-quoted JS string value in `text`, unescaped.
    MPMB stores the content as ({'file': "<minified js>", ...})."""
    out, i, n = [], 0, len(text)
    M = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\', '/': '/',
         "'": "'", 'b': '\b', 'f': '\f'}
    while i < n:
        if text[i] == '"':
            j, buf = i + 1, []
            while j < n:
                c = text[j]
                if c == '\\':
                    nx = text[j + 1] if j + 1 < n else ''
                    if nx == 'u':
                        try:
                            buf.append(chr(int(text[j + 2:j + 6], 16)))
                        except ValueError:
                            buf.append(nx)
                        j += 6
                        continue
                    buf.append(M.get(nx, nx))
                    j += 2
                    continue
                if c == '"':
                    break
                buf.append(c)
                j += 1
            out.append("".join(buf))
            i = j + 1
        else:
            i += 1
    return "\n".join(out)


def brace_match(s, i):
    """s[i] must be '{'. Return the balanced {...} substring, correctly skipping
    string literals AND regex literals (MPMB's regExpSearch:/.../ )."""
    n, j, depth = len(s), i, 0
    in_str = esc = in_re = in_cls = False
    prev = ''
    str_q = ''
    while j < n:
        c = s[j]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == str_q:
                in_str = False
        elif in_re:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '[':
                in_cls = True
            elif c == ']':
                in_cls = False
            elif c == '/' and not in_cls:
                in_re = False
        else:
            if c in '"\'':
                in_str = True
                str_q = c
            elif c == '/' and prev in '=:,([{!&|?;~+-*%<>^':
                in_re = True
                in_cls = False
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return s[i:j + 1]
            if not c.isspace():
                prev = c
        j += 1
    return s[i:]


def parse_content_blob(content, schema):
    """Extract every entity (ListName.key={...}, ListName["key"]={...}, and
    AddSubClass("cls","sub",{...})) from the unescaped MPMB content string."""
    mechanical_fields = {f for f, r in schema.items() if not r["cosmetic"]}
    entities = []
    seen = set()

    def add(etype, name, body):
        key = (etype, name)
        if key in seen:
            return
        seen.add(key)
        used = fields_used(body)
        entities.append({
            "name": name, "type": etype,
            "mech_fields": sorted(used & mechanical_fields),
        })

    names = "|".join(map(re.escape, LIST_TYPES))
    assign = re.compile(
        r'\b(' + names + r')'
        r'(?:\.([A-Za-z_$][\w$]*)'
        r'|\[\s*"((?:[^"\\]|\\.)*)"\s*\]'
        r'|\[\s*\'((?:[^\'\\]|\\.)*)\'\s*\])'
        r'\s*=\s*\{')
    for m in assign.finditer(content):
        lname = m.group(1)
        key = m.group(2) or m.group(3) or m.group(4)
        add(LIST_TYPES[lname], key, brace_match(content, m.end() - 1))

    # subclasses: AddSubClass("class","subclass", { ...object... })
    sub = re.compile(r'AddSubClass\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*\{')
    for m in sub.finditer(content):
        cls, scl = m.group(1), m.group(2)
        add("subclass", f"{cls}: {scl}", brace_match(content, m.end() - 1))
    return entities


def extract_entities_from_pdf(pdf_path, schema):
    print(f"   mining imported content from {os.path.basename(pdf_path)} ...")
    raw = get_stringified_field(pdf_path)
    if not raw:
        sys.exit("!! no 'Stringified' field found -- did you import content and "
                 "SAVE the PDF in Acrobat first?")
    content = js_double_strings(raw)
    ents = parse_content_blob(content, schema)
    by_type = defaultdict(int)
    for e in ents:
        by_type[e["type"]] += 1
    print(f"   parsed {len(ents)} entities from PDF ("
          + ", ".join(f"{k} {v}" for k, v in sorted(by_type.items())) + ")")
    return ents


def merge_entities(base, extra):
    """Merge two entity lists, deduping by (type, name); union mech_fields."""
    by_key = {}
    for e in base + extra:
        k = (e["type"], e["name"])
        if k in by_key:
            by_key[k]["mech_fields"] = sorted(
                set(by_key[k]["mech_fields"]) | set(e["mech_fields"]))
        else:
            by_key[k] = dict(e)
    return list(by_key.values())


# ----------------------------------------------------------------------------
# IN-DATA FILTER: which MPMB entities actually exist in THIS sheet's baked data.
#
# MPMB's library is far larger than the 5etools content baked into index.html, so
# raw impact counts overstate reality (a capability used by 100 MPMB items helps
# nobody if none of those items are in the sheet). Tagging each entity with
# whether it's present in source-data.json lets the report rank by REAL impact.
# ----------------------------------------------------------------------------

def _norm_entity_name(s):
    s = str(s or "").lower().strip()
    s = re.sub(r'-ua\w*$|-motm$|-uacnm$', "", s)   # drop variant suffixes
    s = re.sub(r'\s*\([^)]*\)', "", s)             # drop parentheticals
    return re.sub(r'\s+', " ", s).strip()


def build_sheet_pools(source_data_path):
    """Return {entity_type: set(normalized names)} from the sheet's baked data."""
    with open(source_data_path, encoding="utf-8") as fh:
        d = json.load(fh)

    def names(key):
        return {_norm_entity_name(x.get("name", "")) for x in d.get(key, []) if isinstance(x, dict)}

    pools = {
        "race": names("races"),
        "background": names("backgrounds"),
        "class": names("classes"),
        "feat": names("feats"),
        "creature": names("monsters"),
        "companion": names("monsters"),
        "weapon": names("weapons"),
        "armor": names("armor"),
    }
    # magic items: the sheet keeps these as names across several lists (most empty)
    mi = set()
    for k in ("weapons", "acItems", "magicItems", "attuneItems"):
        mi |= names(k)
    it = d.get("itemText")
    if isinstance(it, dict):
        mi |= {_norm_entity_name(k) for k in it}
    pools["magicitem"] = mi
    # subclasses: nested under classes, as "class: subclass"
    subs = set()
    for c in d.get("classes", []):
        cn = _norm_entity_name(c.get("name", ""))
        for sc in (c.get("subclasses") or []):
            sn = _norm_entity_name(sc.get("name", "") if isinstance(sc, dict) else sc)
            short = _norm_entity_name(sc.get("short", "")) if isinstance(sc, dict) else ""
            subs.add(f"{cn}: {sn}")
            if short:
                subs.add(f"{cn}: {short}")
    pools["subclass"] = subs
    return pools


def tag_in_data(entities, pools):
    """Mark each entity in_data True/False by fuzzy match against the sheet pools."""
    n = 0
    for e in entities:
        pool = pools.get(e["type"], set())
        nm = _norm_entity_name(e["name"])
        if e["type"] == "subclass":
            # match "class: sub" loosely on the subclass half too
            half = nm.split(":")[-1].strip()
            hit = nm in pool or any(half and half in p for p in pool)
        else:
            hit = bool(nm) and (nm in pool or any(p and (nm in p or p in nm) for p in pool))
        e["in_data"] = hit
        n += hit
    return n


# ----------------------------------------------------------------------------
# PROBE: best-effort detection of which capabilities index.html implements
# ----------------------------------------------------------------------------
# Maps an MPMB mechanical field -> regex evidence in the sheet's own engine code.
# Conservative: a hit means "plausibly handled"; absence means "verify by hand".
# Only fields with an entry here get an auto-guess; others default to "unknown".
PROBE_MAP = {
    "scores": r"abilityScore|abilityMod|\bscores?\b",
    "speed": r"\bspeed(base|extra|penalty|s)?\b|walk|fly|swim|climb",
    "senses": r"\bsenses\b|darkvision|blindsight|tremorsense|truesight",
    "vision": r"darkvision|superior darkvision|\bvision\b",
    "dmgres": r"resist|resistance",
    "dmgimm": r"immunit",
    "dmgvuln": r"vulnerab",
    "condimm": r"condition immunit|immune to (charm|fear|poison|paralys)",
    "savetxt": r"saving throw bonus|save bonus|savetxt|advantage on .*sav",
    "saves": r"saving throw|savingthrow|\bsaves?\b",
    "skills": r"\bskill(s|prof|expertise)?\b",
    "skillstxt": r"\bskill(s|prof)?\b",
    "languageProfs": r"languag",
    "weaponProfs": r"weapon prof|weaponprof",
    "armorProfs": r"armor prof|armorprof|armour prof",
    "toolProfs": r"tool prof|toolprof|tool proficien",
    "weaponOptions": r"weaponOption|weapon option|attack option",
    "weaponsAdd": r"weaponsAdd|add weapon|addWeapon",
    "armorAdd": r"armorAdd|armourAdd|natural armor|unarmored defense",
    "extraAC": r"extraAC|extra ac|bonus to ac|ac bonus",
    "usages": r"\busages?\b|uses per|limited (use|feature)",
    "recovery": r"\brecovery\b|short rest|long rest|per rest",
    "limfeature": r"limited feature|limfeature|resource",
    "extraLimitedFeatures": r"limited feature|extraLimited",
    "action": r"\bactions?\b|bonus action|reaction",
    "spellcastingBonus": r"spellcastingBonus|bonus spell|always prepared|extra spell",
    "spellcastingExtra": r"spellcastingExtra|extra spell known|expanded spell",
    "spellChanges": r"spellChanges|spell change|alter spell",
    "addMod": r"addMod|add modifier|bonus modifier",
    "advantages": r"advantage",
    "carryingCapacity": r"carrying|encumbr|carryingCapacity",
    "atkAdd": r"atkAdd|attack.*bonus|extra damage|damage.*bonus",
    "atkCalc": r"atkCalc|to.?hit|attack roll bonus",
    "spellAdd": r"spellAdd",
    "spellCalc": r"spellCalc|spell save dc|spell attack",
    "calcChanges": r"calcChange|recalc|recompute",
    "bonus": r"\bbonus\b",
}


def load_sheet_code(sheet_path):
    """Read index.html, dropping the huge baked-data lines so the probe sees
    only the app's own engine/UI code."""
    with open(sheet_path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    DATA_LINE = 200_000  # baked source-data / template blobs are megabytes long
    code = "".join(ln for ln in lines if len(ln) < DATA_LINE)
    return code.lower()


def probe_sheet(sheet_path, schema):
    code = load_sheet_code(sheet_path)
    guesses = {}
    for field in schema:
        pat = PROBE_MAP.get(field)
        if not pat:
            guesses[field] = "unknown"
            continue
        guesses[field] = "yes" if re.search(pat, code, re.I) else "no"
    return guesses


# ----------------------------------------------------------------------------
# MANIFEST: source of truth for what the sheet implements
# ----------------------------------------------------------------------------

def load_or_seed_manifest(schema, entities, probe_guesses):
    capset = capability_fields(schema, entities)
    if os.path.isfile(MANIFEST_JSON):
        with open(MANIFEST_JSON, encoding="utf-8") as fh:
            manifest = json.load(fh)
    else:
        manifest = {"_README": (
            "Source of truth for which MPMB mechanical capabilities THIS sheet "
            "implements. supported: true|false. status 'auto-*' means the value "
            "was guessed by probing index.html -- review and set it explicitly, "
            "then it won't be overwritten. Re-run the oracle after each build."
        ), "capabilities": {}}

    caps = manifest.setdefault("capabilities", {})
    for field in sorted(capset):
        existing = caps.get(field)
        if existing and not existing.get("status", "").startswith("auto"):
            continue  # respect any human-set verdict (anything not "auto-*")
        guess = probe_guesses.get(field, "unknown")
        caps[field] = {
            "supported": (guess == "yes"),
            "status": f"auto-{guess}",
            "note": (existing or {}).get("note", ""),
        }
    with open(MANIFEST_JSON, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest


# ----------------------------------------------------------------------------
# REPORT
# ----------------------------------------------------------------------------

# Documented in _common but not a standalone "capability" you implement -- these
# are structural sub-keys of other capabilities, evaluator plumbing, or display
# tweaks. calcChanges sub-hooks (atkAdd/atkCalc/spellAdd/...) fold under the
# single `calcChanges` umbrella; the per-hook breakdown lives in the detail
# section. `hp`/`additional`/`selection`/`changes` also leak from stat blocks.
NON_CAPABILITY = {
    "additional", "selection", "changes", "hp", "eval", "changeeval",
    "removeeval", "choiceeval", "submenu", "prereqeval", "usagescalc",
    "limfeaname", "limfeaAddToExisting", "spellFirstColTitle", "toNotesPage",
    "magicItemComponents", "bonusClassExtrachoices", "spellFirstColTitle",
    "spellcastingExtraApplyNonconform", "spellcastingPreparedCantrips",
    "atkAdd", "atkCalc", "spellAdd", "spellCalc", "spellList",  # -> calcChanges
}


def capability_fields(schema, entities):
    """The set of *character-modifying* capabilities -- the things that "aren't
    fully accounted for". Defined as everything documented in MPMB's
    `_common attributes.js` (entity_type "common") plus the `calcChanges`
    umbrella, minus structural plumbing (NON_CAPABILITY). Entity-intrinsic stats
    (a weapon's range/damage, an item's ac/rarity) are excluded too: those are
    data the sheet renders, not automation it must apply."""
    caps = {"calcChanges"}
    for f, r in schema.items():
        if r.get("cosmetic"):
            continue
        if "common" in r.get("entity_types", []):
            caps.add(f)
    caps -= NON_CAPABILITY
    return caps


def build_report(schema, entities, manifest):
    caps = manifest["capabilities"]
    capset = capability_fields(schema, entities)
    mech_fields = sorted(capset)

    def srec(f):
        return schema.get(f, {
            "procedural": f in PROCEDURAL, "use": "(calcChanges hook)",
            "entity_types": ["common"],
        })
    n_intrinsic = len([f for f, r in schema.items()
                       if not r["cosmetic"] and f not in capset])

    # entity-impact: how many entities use each mechanical field
    usage = defaultdict(list)
    for e in entities:
        for f in e["mech_fields"]:
            usage[f].append(e)
    # in-data impact: only entities actually present in the sheet's baked data
    have_indata = any("in_data" in e for e in entities)
    def indata_count(f):
        return sum(1 for e in usage.get(f, []) if e.get("in_data"))

    supported = {f for f in mech_fields if caps.get(f, {}).get("supported")}
    unsupported = [f for f in mech_fields if f not in supported]
    # rank unsupported by REAL impact (in-data) when available, else raw count
    rank = indata_count if have_indata else (lambda f: len(usage.get(f, [])))
    unsupported.sort(key=lambda f: (rank(f), len(usage.get(f, []))), reverse=True)

    n_total = len(mech_fields)
    n_sup = len(supported)

    L = []
    L.append("# Sheet vs MPMB -- Mechanics Coverage Report")
    L.append("")
    L.append("> Generated by `coverage/coverage-oracle.py`. The MPMB side is "
             "exact (full WotC+UA library mined from the saved MPMB PDF). The "
             "*supported?* column is a first-pass verdict in "
             "`capability-manifest.json`; lock a row by setting its `status` to "
             "anything other than `auto-*` and the oracle won't overwrite it.")
    L.append("")
    L.append(f"**Mechanical capabilities covered: {n_sup} / {n_total} "
             f"({100*n_sup//max(n_total,1)}%)**")
    L.append("")

    # ---- punch-list: missing capabilities ranked by entity impact ----
    L.append("## Punch-list -- unsupported capabilities, ranked by impact")
    L.append("")
    L.append("Each row is a mechanical effect MPMB automates that the manifest "
             "marks unsupported, with how many baked entities rely on it."
             + (" **Ranked by *in your data* impact** — entities actually present "
                "in `source-data.json`, since MPMB's full library is far larger "
                "than what this sheet bakes." if have_indata else ""))
    L.append("")
    if have_indata:
        L.append("| capability | kind | in your data | all MPMB | what it does |")
        L.append("|---|---|---|---|---|")
        for f in unsupported:
            rec = srec(f)
            kind = "proc" if rec["procedural"] else "decl"
            use = (rec["use"] or "")[:80].replace("|", "\\|")
            L.append(f"| `{f}` | {kind} | {indata_count(f)} | {len(usage.get(f, []))} | {use} |")
    else:
        L.append("| capability | kind | entities blocked | what it does |")
        L.append("|---|---|---|---|")
        for f in unsupported:
            rec = srec(f)
            kind = "proc" if rec["procedural"] else "decl"
            use = (rec["use"] or "")[:80].replace("|", "\\|")
            L.append(f"| `{f}` | {kind} | {len(usage.get(f, []))} | {use} |")
    L.append("")

    # ---- per-capability entity lists for the high-impact misses ----
    L.append("## Who needs the top missing capabilities")
    L.append("")
    for f in unsupported:
        ents = usage.get(f, [])
        # when we know what's in-data, only the in-data entities are actionable
        if have_indata:
            ents = [e for e in ents if e.get("in_data")]
        if not ents:
            continue
        L.append(f"### `{f}`  ({len(ents)}{' in your data' if have_indata else ' entities'})")
        # group by type
        by_type = defaultdict(list)
        for e in ents:
            by_type[e["type"]].append(e["name"])
        for t in sorted(by_type):
            names = sorted(by_type[t])
            shown = ", ".join(names[:25])
            more = f"  …(+{len(names)-25} more)" if len(names) > 25 else ""
            L.append(f"- **{t}** ({len(names)}): {shown}{more}")
        L.append("")

    # ---- full capability table ----
    L.append("## Full capability table")
    L.append("")
    L.append("| capability | kind | supported | status | entities | entity types |")
    L.append("|---|---|---|---|---|---|")
    for f in sorted(mech_fields, key=lambda f: len(usage.get(f, [])), reverse=True):
        rec = srec(f)
        cap = caps.get(f, {})
        kind = "proc" if rec["procedural"] else "decl"
        sup = "✅" if cap.get("supported") else "❌"
        status = cap.get("status", "?")
        cnt = len(usage.get(f, []))
        ets = ", ".join(rec["entity_types"])
        L.append(f"| `{f}` | {kind} | {sup} | {status} | {cnt} | {ets} |")
    L.append("")

    with open(REPORT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"   wrote {REPORT_MD}")
    print(f"   coverage: {n_sup}/{n_total} mechanical capabilities; "
          f"{len(unsupported)} unsupported")
    # surface the worst offenders on the console
    print("   top unsupported by impact" + (" (in your data)" if have_indata else "") + ":")
    for f in unsupported[:8]:
        if have_indata:
            print(f"      {f:24s} {indata_count(f):4d} in-data / {len(usage.get(f, [])):4d} MPMB")
        else:
            print(f"      {f:24s} {len(usage.get(f, [])):4d} entities")


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", action="store_true",
                    help="re-parse the MPMB repo into mpmb-schema.json + mpmb-entities.json")
    ap.add_argument("--mpmb", default="/tmp/mpmb-repo",
                    help="path to a clone of the MPMB repo (for the schema)")
    ap.add_argument("--pdf", default="",
                    help="path to a SAVED MPMB PDF with full content imported; "
                         "mines its complete entity set and merges it in")
    ap.add_argument("--sheet", default=os.path.join(REPO, "index.html"),
                    help="path to index.html")
    ap.add_argument("--sheet-data", default=os.path.join(REPO, "source-data.json"),
                    help="path to the sheet's baked source-data.json; ranks the "
                         "punch-list by entities actually present in it")
    ap.add_argument("--no-probe", action="store_true",
                    help="don't auto-probe index.html; trust the manifest")
    args = ap.parse_args()

    if args.extract:
        print("[extract] parsing MPMB syntax docs + baked entities ...")
        schema = extract_schema(args.mpmb)
        entities = extract_entities(args.mpmb, schema)
        if args.pdf:
            pdf_ents = extract_entities_from_pdf(args.pdf, schema)
            entities = merge_entities(entities, pdf_ents)
            with open(ENTITIES_JSON, "w", encoding="utf-8") as fh:
                json.dump(entities, fh, indent=2)
            by_type = defaultdict(int)
            for e in entities:
                by_type[e["type"]] += 1
            print(f"   merged total {len(entities)} entities ("
                  + ", ".join(f"{k} {v}" for k, v in sorted(by_type.items())) + ")")
    else:
        if not (os.path.isfile(SCHEMA_JSON) and os.path.isfile(ENTITIES_JSON)):
            sys.exit("!! no extracted data found. Run with --extract first "
                     "(after cloning the MPMB repo). See header.")

    with open(SCHEMA_JSON, encoding="utf-8") as fh:
        schema = json.load(fh)
    with open(ENTITIES_JSON, encoding="utf-8") as fh:
        entities = json.load(fh)

    if args.sheet_data and os.path.isfile(args.sheet_data):
        pools = build_sheet_pools(args.sheet_data)
        n = tag_in_data(entities, pools)
        print(f"[in-data] {n}/{len(entities)} MPMB entities are present in "
              f"{os.path.basename(args.sheet_data)}")

    if args.no_probe:
        guesses = {}
    else:
        if not os.path.isfile(args.sheet):
            sys.exit(f"!! sheet not found: {args.sheet}")
        print("[probe] scanning index.html engine code ...")
        guesses = probe_sheet(args.sheet, schema)

    manifest = load_or_seed_manifest(schema, entities, guesses)
    print("[report] building coverage report ...")
    build_report(schema, entities, manifest)


if __name__ == "__main__":
    main()
