"""Tag rendering tests: the plain text the sheet shows for a 5etools {@tag}.
Three judges, strongest first:
1. 5etools' own renderer (Renderer.stripTags), run in a sandboxed headless page with the network blocked.
   Needs a local 5etools mirror (FIVETOOLS_ROOT, default ~/My Drive/5etools); skipped when there is none.
2. Parity: build-data.py render_tags (Python) and index.html etTags (JavaScript) must agree on every tag.
3. A fixed list of tags with the expected text, which runs anywhere.
Needs `pip install playwright` and `playwright install chromium`.
Usage: python3 tests/test_tags.py"""
import asyncio, collections, glob, importlib.util, json, os, re, sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
ET = Path(os.path.expanduser(os.environ.get("FIVETOOLS_ROOT", "~/My Drive/5etools")))
_argv, sys.argv = sys.argv, ["build-data.py"]
_spec = importlib.util.spec_from_file_location("build_data", ROOT / "build-data.py")
bd = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(bd)
sys.argv = _argv
LEAF = re.compile(r"\{@(\w+)(?: ([^{}]*))?\}")

FIXED = {   # the tag -> what a reader must see
    "{@scaledamage 4d6|1-9|1d6}": "1d6",                      # Guiding Bolt: the dice ADDED per slot level, not the base
    "{@scaledamage 8d6|3-9|1d6}": "1d6",
    "{@scaledice 5d8|1-9|2d8}": "2d8",                        # Sleep
    "{@scaledice 2d6|1,3,5,7,9|1d6|psi|extra amount}": "extra amount",
    "{@damage 4d6}": "4d6", "{@dice 1d20+5|+5}": "+5", "{@damage 2d6;3d6}": "2d6/3d6",
    "{@quickref difficult terrain||3}": "difficult terrain", "{@quickref Cover||3||half cover}": "half cover",
    "{@quickref Vision and Light|PHB|2||heavily obscured}": "heavily obscured",
    "{@book tool|phb|5|tools}": "tool", "{@adventure \"Diseases,\"|ToA|2}": "\"Diseases,\"",
    "{@classFeature Divine Sense|Paladin||1}": "Divine Sense", "{@classFeature Action Surge|Fighter|PHB|2|PHB|a surge}": "a surge",
    "{@subclassFeature Arcane Ward|Wizard|PHB|Abjuration|PHB|2|PHB|ward}": "ward", "{@subclass Alchemist|Artificer|TCE|TCE}": "Alchemist",
    "{@deity Azuth|Forgotten Realms|SCAG}": "Azuth", "{@card Fool|Deck of Many Things|DMG}": "Fool",
    "{@item longsword|phb|a sword}": "a sword", "{@item longsword|phb}": "longsword", "{@spell fireball}": "fireball",
    "{@creature goblin||goblins}": "goblins", "{@condition blinded}": "blinded", "{@filter Warlock Spells|spells|level=1;2|class=Warlock}": "Warlock Spells",
    "{@chance 50}": "50 percent", "{@chance 10|10 percent chance}": "10 percent chance",
    "{@hit 5}": "+5", "{@hit -1}": "-1", "{@hit +3}": "+3", "{@d20 8}": "+8", "{@dc 15}": "DC 15",
    "{@atk mw}": "Melee Weapon Attack:", "{@atk rs}": "Ranged Spell Attack:", "{@atk mw,rw}": "Melee or Ranged Weapon Attack:", "{@atk ms,rs}": "Melee or Ranged Spell Attack:",
    "{@recharge 5}": "(Recharge 5-6)", "{@recharge 6}": "(Recharge 6)", "{@recharge}": "(Recharge 6)",
    "{@h}8 ({@damage 1d8 + 4}) piercing damage": "Hit: 8 (1d8 + 4) piercing damage",
    "{@hitYourSpellAttack} to hit": "your spell attack modifier to hit", "{@dcYourSpellSave}": "your spell save DC",
    "{@b {@dice 1d6}} extra": "1d6 extra", "{@note see {@spell wish}}": "see wish", "{@skill Stealth}": "Stealth", "{@sense darkvision}": "darkvision",
}
DELIBERATE = (   # where the sheet differs from 5etools on purpose: (tag names, how to bring 5etools' text to the sheet's form)
    ({"recharge"}, lambda s: s.replace("–6)", "-6)")),      # a plain hyphen, as in every stat block already baked
    ({"atk", "atkr"}, lambda s: " ".join(s.split())),            # 5etools prints "Melee  or Ranged" with two spaces
)

fails = []
def check(label, cond, extra=None):
    print(("PASS " if cond else "FAIL ") + label + ((" :: " + str(extra)[:600]) if (extra is not None and not cond) else ""))
    if not cond: fails.append(label)

def data_tags():
    seen = collections.Counter()
    for path in glob.glob(str(ET / "data" / "**" / "*.json"), recursive=True):
        if "/generated/" in path: continue
        try: txt = open(path, encoding="utf-8").read()
        except OSError: continue
        if "{@" not in txt: continue
        try: stack = [json.loads(txt)]
        except ValueError: continue
        while stack:
            x = stack.pop()
            if isinstance(x, str):
                if "{@" in x:
                    for m in LEAF.finditer(x): seen[m.group(0)] += 1
            elif isinstance(x, list): stack.extend(x)
            elif isinstance(x, dict): stack.extend(x.values())
    return seen

async def in_chunks(page, expr, items, size=5000):
    out = []
    for i in range(0, len(items), size): out.extend(await page.evaluate(expr, items[i:i + size]))
    return out

def dice_sum(expr):   # "4d6+1d6" / "2d8 + 1d6" -> {6: 5} / {8: 2, 6: 1}: enough to compare two dice expressions
    out = collections.Counter()
    for n, d in re.findall(r"(\d+)d(\d+)", expr): out[int(d)] += int(n)
    return dict(out)

async def upcast_table(browser, oracle):
    """Every baked spell with a scaling tag: the sheet's dice at each slot level against 5etools' own scaling prompt."""
    src = collections.defaultdict(list)
    for path in sorted(glob.glob(str(ET / "data" / "spells" / "spells-*.json"))):
        for sp in json.load(open(path, encoding="utf-8")).get("spell", []):
            m = re.search(r"(?:\b(\w+) )?\{@scaledamage ([^{}]*)\}", json.dumps(sp.get("entriesHigherLevel") or ""))
            if m and m.group(1) != "to": src[sp["name"]].append(m.group(2))   # "increases TO" spells are fixed tiers: judged in test_textfix.py
    page = await browser.new_page()
    await page.goto((ROOT / "index.html").as_uri(), wait_until="load", timeout=180000)
    await page.wait_for_function("typeof _initDone !== 'undefined' && _initDone === true", timeout=120000)
    mine = await page.evaluate("""(names) => { const out = {}; names.forEach(n => { const d = spellData(n), up = (DATA.spellUpcast || {})[n];
        if(!d || !d.dmg || !d.dmg.dice || d.dmg.scale || !up) return; const row = {};
        for(let L = d.level; L <= 9; L++) row[L] = L > up.at ? upcastAt(d.dmg.dice, up, L, d) : d.dmg.dice; out[n] = { base: d.dmg.dice, level: d.level, row }; }); return out; }""", sorted(src))
    await page.close()
    bodies = sorted({b for bs in src.values() for b in bs})
    opts = dict(zip(bodies, await oracle.evaluate("(bs) => bs.map(b => Renderer.parseScaleDice('@scaledamage', b).prompt.options)", bodies), strict=True))
    wrong = []
    for name, m in mine.items():
        ok = False
        for body in src[name]:   # a reprint can tag the rule differently: any source that agrees is enough
            o = {int(k): v for k, v in opts[body].items()}; base = body.split("|")[0]
            if dice_sum(base) != dice_sum(m["base"]): continue   # this tag scales another of the spell's damage lines
            def extra(lvl, o=o): ks = [k for k in o if k <= lvl]; return o[max(ks)] if ks else ""
            if all(dice_sum(m["row"][str(lvl)]) == dice_sum(m["base"] + "+" + extra(lvl)) for lvl in range(max(m["level"], min(o)), 10)): ok = True; break
        if not ok and any(dice_sum(b.split("|")[0]) == dice_sum(m["base"]) for b in src[name]): wrong.append((name, m["row"], src[name]))
    check(f"rolled upcast damage matches 5etools at every slot level ({len(mine)} spells)", not wrong and len(mine) > 60, wrong[:4])

async def spell_tables(browser):
    """2014 rules only: every baked spell's damage, upcast entry and attack-roll flag against its 2014 source entry."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script[^>]*id="source-data"[^>]*>', html)
    assert m, "no #source-data block"
    D = json.loads(html[m.end():html.index("</script>", m.end())])
    src = collections.defaultdict(list)
    for path in sorted(glob.glob(str(ET / "data" / "spells" / "spells-*.json"))):
        for sp in json.load(open(path, encoding="utf-8")).get("spell", []):
            if not bd.is_2024(sp): src[sp["name"]].append(sp)
    chosen = {}
    for bsp in D["spells"]:   # the baked spell's own source entry: the 2014 one whose text it carries
        c = src.get(bsp["name"], [])
        same = [x for x in c if bd.entries_to_text(x.get("entries", [])) == bsp["text"]]
        if same or len(c) == 1: chosen[bsp["name"]] = (same or c)[0]
    names = sorted(chosen)
    check(f"every baked spell is found in a 2014 source ({len(names)} of {len(D['spells'])})", len(names) == len(D["spells"]), [x["name"] for x in D["spells"] if x["name"] not in chosen][:6])
    page = await browser.new_page()
    await page.goto((ROOT / "index.html").as_uri(), wait_until="load", timeout=180000)
    await page.wait_for_function("typeof etSpellDmg === 'function'", timeout=120000)
    js = dict(zip(names, await page.evaluate("(sps) => sps.map(sp => ({ dmg: etSpellDmg(sp), up: etSpellUpcastOf(sp), atk: !!sp.spellAttack }))", [chosen[n] for n in names]), strict=True))
    await page.close()
    drift = [(n, js[n]["dmg"], bd.spell_dmg(chosen[n])) for n in names if js[n]["dmg"] != bd.spell_dmg(chosen[n])] + [(n, js[n]["up"], bd.spell_upcast(chosen[n])) for n in names if js[n]["up"] != bd.spell_upcast(chosen[n])]
    check("spell damage and upcast extractors: Python and JavaScript agree on every 2014 spell", not drift, drift[:4])
    top = {x["name"]: x for x in D["spells"]}
    def lag(old, new):   # the loader drops a cantrip tier that has no dice (Green-Flame Blade at level 1): the baked value keeps it
        return bool(old and new and old.get("scale") and new.get("scale") and all(old["scale"].get(k) == v for k, v in new["scale"].items()))
    bad = [(n, top[n].get("dmg"), js[n]["dmg"]) for n in names if top[n].get("dmg") != js[n]["dmg"] and not lag(top[n].get("dmg"), js[n]["dmg"])]
    check("baked spell damage is the 2014 value for every spell", not bad, bad[:5])
    up = {n: js[n]["up"] for n in names if js[n]["up"]}
    check("baked upcast table is exactly the 2014 one", D["spellUpcast"] == up, (sorted(set(D["spellUpcast"]) ^ set(up))[:8], [(n, D["spellUpcast"][n], up[n]) for n in up if n in D["spellUpcast"] and D["spellUpcast"][n] != up[n]][:4]))
    atk = sorted(n for n in names if js[n]["atk"])
    check("baked attack-roll list is exactly the 2014 one", sorted(D["attackSpells"]) == atk, sorted(set(D["attackSpells"]) ^ set(atk))[:8])

async def main():
    have_mirror = (ET / "js" / "render.js").is_file()
    seen = data_tags() if have_mirror else collections.Counter()
    tags = sorted(set(seen) | set(FIXED))
    print(f"tags under test: {len(tags)}" + (f" ({sum(seen.values())} uses in the 5etools data)" if have_mirror else " (no 5etools mirror: the fixed list only)"))
    py = {t: bd.render_tags(t) for t in tags}
    bad = {t: (py[t], want) for t, want in FIXED.items() if py[t] != want}
    check("Python: the fixed list renders as expected", not bad, bad)

    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True)
        page = await b.new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)[:200]))
        await page.goto((ROOT / "index.html").as_uri(), wait_until="load", timeout=180000)
        await page.wait_for_function("typeof etTags === 'function'", timeout=120000)
        js = dict(zip(tags, await in_chunks(page, "(ts) => ts.map(t => etTags(t))", tags), strict=True))
        bad = {t: (js[t], want) for t, want in FIXED.items() if js[t] != want}
        check("JavaScript: the fixed list renders as expected", not bad and not errs, (bad, errs))
        diff = [(t, py[t], js[t]) for t in tags if py[t] != js[t]]
        check(f"Python and JavaScript agree on all {len(tags)} tags", not diff, diff[:5])
        cases = [{"name": "A", "level": 5, "source": "T", "entriesHigherLevel": ["increases by {@scaledamage 6d6|5-7|1d6|psi} for each"]},
                 {"name": "B", "level": 2, "source": "T", "entriesHigherLevel": ["increases by {@scaledamage 1d8|2,4,6,8|1d8} for every two slot levels above 2nd."]},
                 {"name": "C", "level": 3, "source": "T", "entriesHigherLevel": ["using a spell slot of 5th or 6th level, the bonus increases to +2 and the extra damage increases to {@scaledamage 1d4|3-9|2d4}. When you use a spell slot of 7th level or higher, the extra damage increases to {@scaledamage 1d4|3-9|3d4}."]},
                 {"name": "D", "level": 1, "source": "T", "entriesHigherLevel": ["no dice here"]}]
        want = {"A": {"up": "1d6", "at": 5}, "B": {"up": "1d8", "at": 2, "step": 2}, "C": {"at": 3, "tiers": [[5, "2d4"], [7, "3d4"]]}}
        jsup = await page.evaluate("(sp) => etSpellUpcast({spell: sp}, 'T')", cases)
        pyup = {c["name"]: u for c in cases if (u := bd.spell_upcast(c))}
        check("upcast extractor: per level, per two levels and fixed tiers, the same in JavaScript and Python", jsup == want == pyup, (jsup, pyup))
        await page.close()

        if have_mirror:
            ctx = await b.new_context(); await ctx.route("**/*", lambda r: r.abort())   # the mirror's scripts get no network
            page = await ctx.new_page(); await page.set_content("<!doctype html><title>oracle</title>")
            for f in ("parser.js", "utils.js", "render.js"):
                await page.add_script_tag(content=(ET / "js" / f).read_text(encoding="utf-8"))
            ref = dict(zip(tags, await in_chunks(page, "(ts) => ts.map(t => { try { return Renderer.stripTags(t); } catch (e) { return '\\u0000' + e.message; } })", tags), strict=True))
            def expected(t):
                name = LEAF.match(t).group(1); s = ref[t]
                for names, fix in DELIBERATE:
                    if name in names: s = fix(s)
                return s
            wrong = collections.defaultdict(list)
            for t in tags:
                if "{@" in t[2:] and not LEAF.fullmatch(t): continue   # the fixed list has a few multi-tag strings: judged above
                if py[t] != expected(t): wrong[LEAF.match(t).group(1)].append((t, py[t], expected(t)))
            check(f"matches 5etools' own renderer on every tag in the data ({len(seen)} distinct, {len({LEAF.match(t).group(1) for t in seen})} kinds)",
                  not wrong, {k: v[:2] for k, v in list(wrong.items())[:6]})
            await upcast_table(b, page)
            await spell_tables(b)
            ctl = bd.render_tags("{@scaledamage 4d6|1-9|1d6}") == ref.get("{@scaledamage 4d6|1-9|1d6}") == "1d6"
            check("control: the oracle itself answers 1d6 for Guiding Bolt's tag", ctl, ref.get("{@scaledamage 4d6|1-9|1d6}"))
        await b.close()
    print("\nFAILED:" if fails else "\nALL PASS", fails if fails else "")
    sys.exit(1 if fails else 0)
asyncio.run(main())
