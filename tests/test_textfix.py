"""Rules-text correction tests: the shipped data, and the repair of copies made before the fix.
The "before" build is read from git (BASE, the last release with the old tag renderer), so this needs the repo's
history. Needs `pip install playwright` and `playwright install chromium`.
Usage: python3 tests/test_textfix.py [shipped] [parity] [character] [update] [stored]"""
import asyncio, json, re, socket, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp" / "test-out"; OUT.mkdir(parents=True, exist_ok=True)   # tmp/ is gitignored
BASE = "c41768e"   # 2.171.0
PORT = 8765
LIVE = "https://baestheorem.github.io/dnd-character-sheet/"
WRONG = ("increases by 4d6 for each slot level above 1st", "ignore 3 and 3", "area into 3.", "roll an additional 5d8")

fails = []
def check(label, cond, extra=None):
    print(("PASS " if cond else "FAIL ") + label + ((" :: " + str(extra)[:500]) if (extra is not None and not cond) else ""))
    if not cond: fails.append(label)

def blob_of(html):
    m = re.search(r'<script[^>]*id="source-data"[^>]*>', html)
    assert m, "no #source-data block"
    a = m.end()
    return html[a:html.index("</script>", a)]

def old_html():
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:index.html"], capture_output=True, check=True).stdout.decode("utf-8")

def strip(d):   # leave only what the text repair is responsible for: no table, no revision, no spell tables (test_tags.py judges those)
    d = dict(d); d.pop("textFixes", None); d.pop("spellUpcast", None); d.pop("attackSpells", None)
    d["_meta"] = {k: v for k, v in d["_meta"].items() if k not in ("textRev", "dropped2024")}
    d["spells"] = [{k: v for k, v in sp.items() if k != "dmg"} for sp in d["spells"]]
    return d

async def boot(ctx, url, wait="typeof _initDone !== 'undefined' && _initDone === true"):
    page = await ctx.new_page(); page.errs = []
    page.on("pageerror", lambda e: page.errs.append(str(e)[:300]))
    await page.goto(url, wait_until="load", timeout=180000)
    await page.wait_for_function(wait, timeout=120000); await page.wait_for_timeout(1500)
    return page

async def t_shipped(pw, new, old):
    b = await pw.chromium.launch(headless=True); page = await boot(await b.new_context(), (ROOT / "index.html").as_uri())
    r = await page.evaluate("""() => { const gb = spellData("Guiding Bolt"), f = (DATA.feats || []).find(x => x.name === "Sharpshooter"), en = spellData("Entangle"), sl = spellData("Sleep");
        return { higher: gb.higher, d1: spellDamage(gb, 1), d2: spellDamage(gb, 2), d4: spellDamage(gb, 4), up: DATA.spellUpcast["Guiding Bolt"], sharp: f.text, entangle: en.text, sleep: sl.higher,
                 rev: DATA._meta.textRev, want: TEXT_REV, pass: healSourceText(), table: textFixMap() ? textFixMap().size : 0 }; }""")
    check("shipped: Guiding Bolt's text says 1d6 per slot level", "the damage increases by 1d6 for each slot level above 1st" in r["higher"], r["higher"])
    check("shipped: the rolled damage adds 1d6 per slot level (4d6, 5d6, 7d6)", (r["d1"], r["d2"], r["d4"]) == ("4d6 radiant", "5d6 radiant", "7d6 radiant") and r["up"] == {"up": "1d6", "at": 1}, r)
    check("shipped: Sharpshooter, Entangle and Sleep read correctly", "ignore half cover and three-quarters cover." in r["sharp"] and "into difficult terrain." in r["entangle"] and "roll an additional 2d8" in r["sleep"], (r["sharp"][:200], r["entangle"][:160], r["sleep"]))
    check("shipped: the data is at the current text revision, so no repair pass runs", r["rev"] == r["want"] == 1 and r["pass"] is False and r["table"] > 200 and not page.errs, r)
    want = {"Spiritual Weapon": "1d8 1d8 2d8 2d8 3d8 3d8 4d8 4d8", "Flame Blade": "3d6 3d6 4d6 4d6 5d6 5d6 6d6 6d6",        # one die more for every TWO slot levels
            "Spirit Shroud": "1d8 1d8 2d8 2d8 3d8 3d8 4d8", "Elemental Weapon": "1d4 1d4 2d4 2d4 3d4 3d4 3d4",             # ...and fixed tiers at 5th and 7th
            "Guiding Bolt": "4d6 5d6 6d6 7d6 8d6 9d6 10d6 11d6 12d6", "Fireball": "8d6 9d6 10d6 11d6 12d6 13d6 14d6"}
    dice = """(names) => Object.fromEntries(names.map(n => { const d = spellData(n), up = DATA.spellUpcast[n], out = [];
        for(let L = d.level; L <= 9; L++) out.push(L > up.at ? upcastAt(d.dmg.dice, up, L, d) : d.dmg.dice); return [n, out.join(" ")]; }))"""
    got = await page.evaluate(dice, list(want))
    check("shipped: dice at every slot level, for per-level, per-two-levels and fixed-tier spells", got == want, got)
    stale = await page.evaluate("""(names) => { const keep = JSON.stringify(DATA.spellUpcast);
        ["Spiritual Weapon", "Flame Blade", "Spirit Shroud"].forEach(n => { delete DATA.spellUpcast[n].step; }); DATA.spellUpcast["Elemental Weapon"] = {up: "2d4", at: 3};   // the entries as builds before 2.171.1 wrote them
        const out = (""" + dice + """)(names); DATA.spellUpcast = JSON.parse(keep); return out; }""", list(want))
    check("shipped: the same dice from data extracted before the fix (the rule's own wording fills in)", stale == want, stale)
    r14 = await page.evaluate("""() => ({ inflict: spellDamage(spellData("Inflict Wounds"), 1), circle: spellDamage(spellData("Circle of Death"), 6), chill: spellData("Chill Touch").dmg.scale["1"],
        conjure: spellData("Conjure Animals").dmg || null, hadar: DATA.spellUpcast["Hunger of Hadar"] || null, poison: DATA.attackSpells.includes("Poison Spray"), firebolt: DATA.attackSpells.includes("Fire Bolt") })""")
    check("shipped: 2014 damage, not 2024 (Inflict Wounds 3d10, Circle of Death 8d6, Chill Touch 1d8; no dice for Conjure Animals; Poison Spray is a save)",
          r14 == {"inflict": "3d10 necrotic", "circle": "8d6 necrotic", "chill": "1d8", "conjure": None, "hadar": None, "poison": False, "firebolt": True}, r14)
    raw = blob_of(new); table = json.dumps(json.loads(raw)["textFixes"], ensure_ascii=False, separators=(",", ":"))
    left = {w: raw.replace(table, "").count(w) for w in WRONG}; had = {w: blob_of(old).count(w) for w in WRONG}
    check("shipped: the known wrong sentences are gone from every copy in the data (control: the old build had them)", not any(left.values()) and all(had.values()), (left, had))
    await b.close()

async def t_parity(pw, new, old):
    b = await pw.chromium.launch(headless=True); page = await boot(await b.new_context(), (ROOT / "index.html").as_uri())
    res = await page.evaluate("""(oldJson) => { const keep = DATA; let out, ms, again;
        try { DATA = JSON.parse(oldJson); const t = performance.now(); const ran = healSourceText(); ms = performance.now() - t; out = JSON.stringify(DATA); again = healSourceText(true); again = JSON.stringify(DATA) === out; }
        finally { DATA = keep; }
        return { out, ms, again }; }""", blob_of(old))
    healed = json.loads(res["out"]); want = strip(json.loads(blob_of(new)))
    check("repair: every string of the old build's data, repaired in the page, equals the shipped data", strip(healed) == want and healed["_meta"].get("textRev") == 1)
    check(f"repair: a second pass changes nothing; one pass took {res['ms']:.0f} ms", res["again"] and res["ms"] < 1500, res["ms"])
    await b.close()

async def t_character(pw, new, old):
    O, N = json.loads(blob_of(old)), json.loads(blob_of(new))
    def feat(D, n): return next(x for x in D["feats"] if x["name"] == n)["text"]
    def cfeat(D, cls, n): return next(f for c in D["classes"] if c["name"] == cls for f in c["features"] if f["name"] == n)
    # the first creature trait the fix changes
    mi, tj = next((i, j) for i, m in enumerate(O["monsters"]) for j, t in enumerate(m.get("traits") or []) if t["text"] != N["monsters"][i]["traits"][j]["text"])
    mon = O["monsters"][mi]["name"]; tn = O["monsters"][mi]["traits"][tj]["name"]
    ls_o, ls_n = cfeat(O, "Ranger", "Land's Stride"), cfeat(N, "Ranger", "Land's Stride")
    blocks_old = [f"Sharpshooter. {feat(O, 'Sharpshooter')}", f"Land's Stride (Ranger {ls_o['level']}). {ls_o['text']}", "House rule. We split the loot into 3. No exceptions."]
    blocks_new = [f"Sharpshooter. {feat(N, 'Sharpshooter')}", f"Land's Stride (Ranger {ls_n['level']}). {ls_n['text']}", blocks_old[2]]
    data = {"charname": "Frozen", "features": "\n\n".join(blocks_old), "genFeatures": blocks_old[:2], "notes": "Remember: into 3. and ignore 3 and 3.",
            "companions": [{"name": "Pet", "monster": mon, "traits": f"{tn}. {O['monsters'][mi]['traits'][tj]['text']}", "actions": ""}],
            "lfname-0": "Land's Stride", "lfDesc": [ls_o["text"]]}
    check("character (control): the old build's feat and feature text really was wrong", blocks_old[0] != blocks_new[0] and blocks_old[1] != blocks_new[1] and "ignore 3 and 3" in blocks_old[0])
    b = await pw.chromium.launch(headless=True); page = await boot(await b.new_context(), (ROOT / "index.html").as_uri())
    r = await page.evaluate("(d) => { const rev = healCharacterText(d); const once = JSON.stringify(d); const rev2 = healCharacterText(d); return { d, rev, same: JSON.stringify(d) === once, rev2 }; }", data)
    d = r["d"]
    check("character: feature cards are corrected and a player's own block is left alone", d["features"] == "\n\n".join(blocks_new), d["features"][:300])
    check("character: the generated-block list still matches the cards, so Edit Character replaces them", d["genFeatures"] == blocks_new[:2])
    check("character: a companion's stat block and a limited-feature tooltip are corrected", d["companions"][0]["traits"] == f"{tn}. {N['monsters'][mi]['traits'][tj]['text']}" and d["lfDesc"][0] == ls_n["text"], (mon, tn))
    check("character: free text is never touched, and the repair runs once", d["notes"] == data["notes"] and r["rev"] == 1 and r["rev2"] == 1 and r["same"] and d["textRev"] == 1)
    await b.close()

async def t_update(pw, new, old):
    """A 2.171.0 copy updates itself (its own, older, merge code writes the new file). The new file must open correct."""
    work = OUT / "textfix"; work.mkdir(exist_ok=True); (work / "old.html").write_text(old, encoding="utf-8")
    O = json.loads(blob_of(old)); sharp = next(x for x in O["feats"] if x["name"] == "Sharpshooter")["text"]
    b = await pw.chromium.launch(headless=True)
    ctx = await b.new_context(accept_downloads=True)
    body = (ROOT / "index.html").read_bytes()
    async def serve(route):
        u = route.request.url
        if "version.json" in u: await route.fulfill(status=200, content_type="application/json", headers={"access-control-allow-origin": "*"}, body=json.dumps({"version": "v9999 (2026-11-22)", "semver": "9.9.9", "size": len(body)}))
        elif u.split("?")[0].endswith("index.html"): await route.fulfill(status=200, content_type="text/html; charset=utf-8", headers={"access-control-allow-origin": "*"}, body=body)
        else: await route.abort()
    await ctx.route("https://baestheorem.github.io/**", serve); await ctx.route("https://raw.githubusercontent.com/**", serve)
    page = await boot(ctx, (work / "old.html").as_uri(), wait="typeof compute === 'function'")
    page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
    await page.evaluate("dismissIntro()")
    await page.evaluate("""(block) => { const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); };
        set('charname', 'Old Copy Hero'); set('classlevel', 'Fighter 4'); set('features', block); genFeatures = [block]; flushSave(); }""", f"Sharpshooter. {sharp}")
    await page.wait_for_timeout(1200); await page.evaluate("flushSave()")
    async with page.expect_download(timeout=300000) as di:
        await page.evaluate("updateApp()")
    d = await di.value; upd = work / "updated.html"; await d.save_as(str(upd))
    made = json.loads(blob_of(upd.read_text(encoding="utf-8")))
    stale_raw = sum(1 for bk in (made["_meta"].get("raw") or {}).values() for x in bk.get("spells", []) if "increases by 4d6 for each slot level above 1st" in (x.get("higher") or ""))
    check("update (control): the older build's merge leaves the per-book copies stale and carries the table along", stale_raw >= 1 and "textFixes" in made and "textRev" not in made["_meta"], (stale_raw, "textFixes" in made, made["_meta"].get("textRev")))
    await ctx.close()
    ctx = await b.new_context(); page = await boot(ctx, upd.as_uri())
    r = await page.evaluate("""() => { const raw = DATA._meta.raw || {}; let rawGb = null, stale = 0;
        for(const bk in raw) (raw[bk].spells || []).forEach(x => { if(x.name === "Guiding Bolt") rawGb = x.higher; if(/increases by 4d6 for each slot level above 1st/.test(x.higher || "")) stale++; });
        return { ver: APP_SEMVER, higher: spellData("Guiding Bolt").higher, rawGb, stale, rev: DATA._meta.textRev, inflict: spellData("Inflict Wounds").dmg.dice, hadar: DATA.spellUpcast["Hunger of Hadar"] || null, poison: DATA.attackSpells.includes("Poison Spray"),
                 sw: [2, 3, 4].map(L => upcastAt("1d8", DATA.spellUpcast["Spiritual Weapon"], L, spellData("Spiritual Weapon"))).join(" "), features: document.getElementById("features").value, name: document.getElementById("charname").value,
                 gen: genFeatures, crev: charTextRev, saved: JSON.parse(csGet(KEY) || "{}").textRev, sharp: DATA.feats.find(x => x.name === "Sharpshooter").text }; }""")
    check("update: the new file opens with the spell text right in the main data AND in the per-book copy", "increases by 1d6" in r["higher"] and r["rawGb"] and "increases by 1d6" in r["rawGb"] and r["stale"] == 0 and r["rev"] == 1, (r["higher"], r["rawGb"], r["stale"]))
    check("update: 2014 spell damage reaches the new file through the older build's merge (Inflict Wounds 3d10, no 2024 upcast or attack flag, Spiritual Weapon per two levels)",
          r["inflict"] == "3d10" and r["hadar"] is None and r["poison"] is False and r["sw"] == "1d8 1d8 2d8", (r["inflict"], r["hadar"], r["poison"], r["sw"]))
    check("update: the character's frozen feat card is corrected, still matches its generated block, and the repair is saved", r["name"] == "Old Copy Hero" and r["features"] == f"Sharpshooter. {r['sharp']}" and r["gen"] == [r["features"]] and "ignore half cover and three-quarters cover" in r["features"] and r["crev"] == 1 and r["saved"] == 1, (r["features"][:200], r["crev"], r["saved"]))
    check("update: no page errors", not page.errs, page.errs)
    await b.close()
    for f in work.iterdir(): f.unlink()
    work.rmdir()

async def t_stored(pw, new, old):
    """A browser that stored source data before the fix (same data version, so the stored copy wins at boot)."""
    O = json.loads(blob_of(old)); lean = {k: v for k, v in O.items() if k != "monsters"}; lean["_meta"] = {k: v for k, v in O["_meta"].items() if k != "raw"}
    lean["spells"] = lean["spells"] + [{"name": "Zz Player's Own Spell", "level": 1, "school": "Evocation", "time": "1 action", "range": "Self", "components": "V", "duration": "instant", "text": "Mine.", "higher": "", "ritual": False, "conc": False, "material": ""}]
    payload = json.dumps(lean, ensure_ascii=False, separators=(",", ":"))
    server = None
    with socket.socket() as k:
        k.settimeout(0.5); up = k.connect_ex(("127.0.0.1", PORT)) == 0
    if not up:
        server = subprocess.Popen([sys.executable, str(ROOT / "tests" / "serve.py"), "--root", str(ROOT), "--port", str(PORT)]); time.sleep(1.5)
    try:
        b = await pw.chromium.launch(headless=True); ctx = await b.new_context(service_workers="block")
        page = await ctx.new_page(); await page.goto(f"http://127.0.0.1:{PORT}/version.json")
        fit = await page.evaluate("(p) => { try { localStorage.setItem('dnd-sheet-sources', p); return true; } catch (e) { return String(e.name); } }", payload)
        if fit is not True:
            print(f"SKIP stored: the old data ({len(payload):,} chars) does not fit this browser's storage ({fit}), which is also why few real browsers hold a stored copy"); await b.close(); return
        page = await boot(ctx, f"http://127.0.0.1:{PORT}/?web")
        r = await page.evaluate("""() => { const st = JSON.parse(localStorage.getItem('dnd-sheet-sources') || 'null');
            return { own: !!spellData("Zz Player's Own Spell"), higher: spellData("Guiding Bolt").higher, inflict: spellData("Inflict Wounds").dmg.dice, hadar: DATA.spellUpcast["Hunger of Hadar"] || null,
                     rev: DATA._meta.textRev, storedRev: st && st._meta && st._meta.textRev, storedHigher: st && (st.spells.find(x => x.name === "Guiding Bolt") || {}).higher,
                     storedOwn: !!(st && st.spells.find(x => x.name === "Zz Player's Own Spell")), storedInflict: st && st.spells.find(x => x.name === "Inflict Wounds").dmg.dice }; }""")
        check("stored data: the build's corrections are folded in on open (text and 2014 damage) and the player's own entry stays",
              r["own"] and "increases by 1d6" in r["higher"] and r["inflict"] == "3d10" and r["hadar"] is None and r["rev"] == 1 and not page.errs, (r, page.errs))
        check("stored data: the corrected copy is written back, so this runs once", r["storedRev"] == 1 and "increases by 1d6" in (r["storedHigher"] or "") and r["storedOwn"] and r["storedInflict"] == "3d10", r)
        await b.close()
    finally:
        if server: server.terminate()

TESTS = {"shipped": t_shipped, "parity": t_parity, "character": t_character, "update": t_update, "stored": t_stored}

async def main():
    names = sys.argv[1:] or list(TESTS)
    new = (ROOT / "index.html").read_text(encoding="utf-8"); old = old_html()
    async with async_playwright() as pw:
        for n in names:
            print(f"--- {n}")
            try: await TESTS[n](pw, new, old)
            except Exception as e:
                import traceback
                traceback.print_exc(limit=3); check(f"{n}: ran to completion", False, repr(e)[:300])
    print("\nFAILED:" if fails else "\nALL PASS", fails if fails else "")
    sys.exit(1 if fails else 0)
asyncio.run(main())
