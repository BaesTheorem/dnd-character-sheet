"""Landing page tests: what a visitor to the web address gets, per device and per state.
Hosted cases run against tests/serve.py (a gzip stand-in for GitHub Pages), started here on :8765.
Needs `pip install playwright` and `playwright install chromium webkit firefox`.
Usage: python3 tests/test_landing.py [test names...]   (no names = all; names are the keys of TESTS)"""
import asyncio, hashlib, os, re, shutil, socket, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = str(Path(__file__).resolve().parents[1])
OUT = ROOT + "/tmp/test-out"   # tmp/ is gitignored
os.makedirs(OUT, exist_ok=True)
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}/"
FILE = "file://" + ROOT + "/index.html"
SRC_SHA = hashlib.sha256(open(ROOT + "/index.html", "rb").read()).hexdigest()

UA = {
  "iphone27": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/27.0 Mobile/15E148 Safari/604.1",
  "iphone26": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1",
  "iphone18": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
  "ipad27":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/27.0 Safari/605.1.15",
  "crios":    "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/131.0.6778.73 Mobile/15E148 Safari/604.1",
  "inapp":    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/480.0]",
  "android":  "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
  "mac":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}
IPAD_INIT = "Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'}); Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5});"
MAC_INIT = "Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'}); Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});"
MOCK_PICK = """() => { window.__pick = { calls: 0, written: null, name: null };
  window.showSaveFilePicker = async (opts) => { window.__pick.calls++; const name = 'My party.html';
    return { name, kind: 'file', createWritable: async () => { let buf = []; return { write: async (b) => { buf.push(await b.text()); }, close: async () => { window.__pick.written = buf.join(''); window.__pick.name = name; } }; } }; }; }"""
VIS = """(sel) => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
  return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0 && !!e.closest('#landing') === true; }).map(e => e.textContent.replace(/\\s+/g, ' ').trim())"""
STATE = """() => { const de = document.documentElement, L = document.getElementById('landing');
  return { cls: de.className.split(/\\s+/).filter(Boolean).sort(), gate: getComputedStyle(L).display, compute: typeof compute,
    toolbar: getComputedStyle(document.querySelector('.toolbar')).visibility, flag: localStorage.getItem('dnd-sheet-web') }; }"""

fails = []
def check(label, cond, extra=None):
    print(("PASS " if cond else "FAIL ") + label + ((" :: " + str(extra)[:400]) if (extra is not None and not cond) else ""))
    if not cond: fails.append(label)

async def open_page(pw, url, engine="chromium", ua=None, vw=1300, vh=800, init=None, sw="block", mobile=False, wait=True, **kw):
    b = await getattr(pw, engine).launch(headless=True)
    opts: dict = dict(viewport={"width": vw, "height": vh}, accept_downloads=True, service_workers=sw, **kw)
    if ua: opts["user_agent"] = ua
    if mobile and engine != "firefox": opts.update(is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx = await b.new_context(**opts)
    if init: await ctx.add_init_script(init)
    page = await ctx.new_page()
    page.errs = []; page.failed = []
    page.on("pageerror", lambda e: page.errs.append(str(e)[:300]))
    page.on("requestfailed", lambda r: page.failed.append(r.url[-70:]))
    await page.goto(url, wait_until="load", timeout=180000)
    if wait: await ready(page)
    return b, ctx, page

async def ready(page):
    await page.wait_for_function("typeof compute === 'function' && typeof _initDone !== 'undefined' && _initDone === true", timeout=120000)
    await page.wait_for_timeout(1200)

# ------------------------------------------------------------------------------------------------ tests
async def t_desktop_fresh(pw):
    b, ctx, page = await open_page(pw, BASE, ua=UA["mac"], init=MAC_INIT)
    st = await page.evaluate(STATE)
    check("fresh desktop: gate on, no platform or returning classes", st["cls"] == ["landing", "lp-ready"] and st["gate"] == "block", st)
    check("fresh desktop: the sheet under it is hidden but still laid out", st["toolbar"] == "hidden" and await page.evaluate("document.querySelector('.toolbar').getBoundingClientRect().width > 300"))
    a = await page.evaluate("""() => { const a = document.querySelector('#landing .lp-unless-has a.lp-get'), im = document.querySelector('#landing .lp-shot img');
        return { href: a.href, dl: a.download, text: a.textContent.replace(/\\s+/g,' ').trim(), sem: APP_SEMVER, file: versionedFileName(),
                 img: im ? [im.naturalWidth, im.naturalHeight, im.getAttribute('src'), im.complete] : null,
                 links: [...document.head.querySelectorAll('link[rel=manifest], link[rel=apple-touch-icon]')].map(l => l.getAttribute('href') + '|' + l.dataset.transient),
                 h1: [...document.querySelectorAll('#landing h1')].filter(h => h.getBoundingClientRect().height > 0).map(h => h.textContent) }; }""")
    check("fresh desktop: one headline, the desktop one", a["h1"] == ["The sheet is a file. Start by downloading it."], a["h1"])
    check("fresh desktop: link points at this page and carries the versioned file name", a["href"] == BASE and a["dl"] == a["file"] and a["dl"] == "Character Sheet v" + a["sem"] + ".html", a)
    check("fresh desktop: button text has the size", a["text"].startswith("Download the file") and a["text"].endswith(" MB"), a["text"])
    check("fresh desktop: product picture loaded", a["img"] and a["img"][0] == 1040 and a["img"][1] == 656 and a["img"][2] == "landing-shot-light.png", a["img"])
    check("fresh desktop: manifest and touch icon linked once, marked transient", a["links"] == ["manifest.webmanifest|1", "icon-180.png|1"], a["links"])
    vis = await page.evaluate(VIS, "#landing .lp-if")
    check("fresh desktop: no conditional copy shows", vis == [], vis)
    # keyboard never leaves the page
    seen = []
    for _ in range(8):
        await page.keyboard.press("Tab")
        seen.append(await page.evaluate("(() => { const e = document.activeElement; if(!e || e === document.body) return 'body'; return (e.closest('#landing') ? 'in:' : 'OUT:') + (e.className || e.tagName); })()"))
    check("fresh desktop: Tab stays inside the landing page", all(s.startswith("in:") or s == "body" for s in seen) and any("lp-dl" in s for s in seen) and any("lp-skip" in s for s in seen), seen)
    # the download itself
    async with page.expect_download(timeout=90000) as di:
        await page.click("#landing .lp-unless-has a.lp-get")
    d = await di.value; got = open(await d.path(), "rb").read()
    check("fresh desktop: download is byte-identical to the published file", hashlib.sha256(got).hexdigest() == SRC_SHA and d.suggested_filename == a["dl"], (d.suggested_filename, len(got)))
    after = await page.evaluate("""() => ({ got: document.documentElement.classList.contains('lp-got'), msg: document.querySelector('#landing .lp-desk .lp-done').textContent,
        next: getComputedStyle(document.querySelector('#landing .lp-desk li.lp-next'), '::before').backgroundColor })""")
    check("fresh desktop: after the click, a next-step message and step 2 marked", after["got"] and after["msg"].startswith("Downloading.") and after["next"] == "rgb(138, 109, 34)", after)
    check("fresh desktop: no page errors, no failed requests", not page.errs and not page.failed, (page.errs, page.failed))
    await page.screenshot(path=f"{OUT}/t-desktop-after-click.png")
    await b.close()

async def t_early_paint(pw):
    b = await pw.chromium.launch(headless=True)
    ctx = await b.new_context(viewport={"width": 1300, "height": 800}, service_workers="block", user_agent=UA["mac"])
    page = await ctx.new_page(); cdp = await ctx.new_cdp_session(page)
    await cdp.send("Network.enable")
    await cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150, "downloadThroughput": 1_600_000 / 8, "uploadThroughput": 750_000 / 8})
    t0 = time.time()
    await page.goto(BASE, wait_until="commit")
    snap = None
    for _ in range(40):
        await asyncio.sleep(0.25)
        try:
            snap = await page.evaluate("""() => { const L = document.getElementById('landing'); if(!L) return null; const a = L.querySelector('.lp-unless-has a.lp-get');
                const f = performance.getEntriesByName('first-contentful-paint')[0];
                return { disp: getComputedStyle(L).display, ver: (L.querySelector('.lp-semver')||{}).textContent, dl: a && a.download, href: a && a.href,
                         main: typeof compute, state: document.readyState, fcp: f ? Math.round(f.startTime) : null, h1: !!L.querySelector('h1') }; }""")
        except Exception: snap = None
        if snap and snap["disp"] == "block" and snap["fcp"]: break
    el = round(time.time() - t0, 2)
    check("slow link (1.6 Mbps): the page is up and filled in while the file still downloads", bool(snap) and snap["disp"] == "block" and snap["ver"] and snap["dl"].startswith("Character Sheet v") and snap["main"] == "undefined" and snap["state"] == "loading", (el, snap))
    print(f"   first paint {snap and snap['fcp']} ms; observed usable at {el}s; main script not loaded yet = {snap and snap['main'] == 'undefined'}")
    # leave before the main script exists, then let it load: one guide, one tip bar
    await page.click("#landing .lp-desk .lp-skip")
    mid = await page.evaluate(STATE.replace("compute: typeof compute,", "compute: typeof compute,").replace("getComputedStyle(document.querySelector('.toolbar')).visibility", "(document.querySelector('.toolbar') ? getComputedStyle(document.querySelector('.toolbar')).visibility : null)"))
    check("slow link: leaving early uncovers the sheet at once and stores the choice", "landing" not in mid["cls"] and mid["flag"] == "1" and mid["toolbar"] == "visible", mid)
    await cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
    await ready(page)
    end = await page.evaluate("({ intro: !document.getElementById('intro-overlay').hidden, hints: document.querySelectorAll('.install-hint').length, cls: document.documentElement.className })")
    check("slow link: after it loads, exactly one welcome guide and one Save tip", end["intro"] and end["hints"] == 1 and "landing" not in end["cls"], end)
    await b.close()

async def t_bypass(pw):
    b, ctx, page = await open_page(pw, BASE, ua=UA["mac"], init=MAC_INIT)
    await page.click("#landing .lp-desk .lp-skip"); await page.wait_for_timeout(500)
    st = await page.evaluate(STATE)
    more = await page.evaluate("({ intro: !document.getElementById('intro-overlay').hidden, hints: document.querySelectorAll('.install-hint').length, btnHidden: document.getElementById('btn-showlanding').hidden, hintHidden: document.getElementById('showlanding-hint').hidden, y: scrollY })")
    check("leave: gate classes gone, choice stored, sheet visible", st["cls"] in (["overlay-open"], []) and st["gate"] == "none" and st["flag"] == "1" and st["toolbar"] == "visible", st)
    check("leave: welcome guide and Save tip appear, Settings gains the way back", more["intro"] and more["hints"] == 1 and not more["btnHidden"] and not more["hintHidden"], more)
    await page.reload(wait_until="load"); await ready(page)
    st = await page.evaluate(STATE)
    check("leave: the choice holds on the next visit", "landing" not in st["cls"] and st["gate"] == "none", st)
    await page.evaluate("dismissIntro()")
    await page.evaluate("document.getElementById('btn-settings').click()"); await page.wait_for_timeout(400)
    await page.evaluate("document.getElementById('btn-showlanding').click()")
    await page.wait_for_load_state("load"); await ready(page)
    st = await page.evaluate(STATE)
    check("way back: Settings button clears the choice and the page returns", "landing" in st["cls"] and st["flag"] is None and st["gate"] == "block", st)
    check("leave: no page errors", not page.errs, page.errs)
    await b.close()
    b, ctx, page = await open_page(pw, BASE + "?web", ua=UA["mac"], init=MAC_INIT)
    st = await page.evaluate(STATE)
    check("?web: no gate for this load and nothing stored", "landing" not in st["cls"] and st["flag"] is None and st["toolbar"] == "visible", st)
    await b.close()

async def seed_character(page, name="Test Hero"):
    await page.evaluate("dismissIntro()")
    await page.evaluate("""(n) => { const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); };
        set('charname', n); set('classlevel', 'Fighter 3'); flushSave(); }""", name)
    await page.wait_for_timeout(1200)
    await page.evaluate("flushSave()")
    return await page.evaluate("characterSlots().filter(s => s.name || s.sub).map(s => s.name + (s.unsaved ? ' (unsaved)' : ''))")

async def t_returning(pw):
    b, ctx, page = await open_page(pw, BASE + "?web", ua=UA["mac"], init=MAC_INIT)
    names = await seed_character(page)
    check("returning: seeded one saved character on the web origin", names == ["Test Hero"], names)
    await page.goto(BASE, wait_until="commit")
    first = await page.evaluate("document.documentElement.className")
    check("returning: flagged as a returning visitor before anything loads", "lp-back" in first and "landing" in first, first)
    await page.wait_for_load_state("load"); await ready(page)
    st = await page.evaluate(STATE)
    check("returning: characters found", "lp-has" in st["cls"] and "lp-ready" in st["cls"], st)
    vis = await page.evaluate(VIS, "#landing .lp-desk .lp-dl, #landing .lp-desk .lp-note")
    check("returning: the main button offers the file with the characters; plain download is the small link", any(v == "Download the file with my 1 character" for v in vis) and not any(v.startswith("Download the file 1") for v in vis) and any("Download an empty copy instead" in v for v in vis), vis)
    await page.screenshot(path=f"{OUT}/t-returning.png")
    await page.evaluate(MOCK_PICK)
    await page.click("#landing .lp-desk .lp-save"); await page.wait_for_function("window.__pick.written !== null", timeout=90000)
    res = await page.evaluate("""() => { const w = window.__pick.written, tag = /<html[^>]*>/.exec(w)[0], doc = new DOMParser().parseFromString(w, 'text/html');
        return { tag, hero: w.includes('Test Hero'), transient: doc.querySelectorAll('[data-transient]').length > 0, shot: !!doc.querySelector('#landing .lp-shot img'), manifestLink: !!doc.querySelector('link[rel=manifest], link[rel=apple-touch-icon]'),
                 doneLeft: [...doc.querySelectorAll('#landing .lp-done')].some(e => e.textContent), msg: document.querySelector('#landing .lp-desk .lp-done').textContent, len: w.length }; }""")
    check("returning: the saved file holds the character", res["hero"] and res["len"] > 10_000_000, res["len"])
    check("returning: the saved file carries no landing state (classes, picture, manifest link, messages)", "landing" not in res["tag"] and "lp-" not in res["tag"] and not res["transient"] and not res["shot"] and not res["manifestLink"] and not res["doneLeft"], res)
    check("returning: the page says what was saved and what to do next", res["msg"] == "Saved “My party.html” with 1 character inside. Open that file from now on.", res["msg"])
    saved = f"{OUT}/t-returning-saved.html"
    open(saved, "w", encoding="utf-8").write(await page.evaluate("window.__pick.written"))
    check("returning: no page errors", not page.errs, page.errs)
    await b.close()
    # the saved file opened from disk: no gate, the character is there, nothing external requested
    b, ctx, page = await open_page(pw, "file://" + saved)
    r = await page.evaluate("({ cls: document.documentElement.className, gate: getComputedStyle(document.getElementById('landing')).display, name: document.getElementById('charname').value, slots: characterSlots().filter(s => s.name).length, wayback: document.getElementById('btn-showlanding').hidden })")
    check("saved file from disk: no gate, character present, no way-back button, no failed requests", r["gate"] == "none" and "landing" not in r["cls"] and r["name"] == "Test Hero" and r["slots"] == 1 and r["wayback"] and not page.failed and not page.errs, (r, page.failed, page.errs))
    await b.close()
    # the same saved file put back on a web server: the page comes up clean and counts the baked character
    os.makedirs(OUT + "/rehost", exist_ok=True); shutil.copy(saved, OUT + "/rehost/index.html")
    for f in ("manifest.webmanifest", "icon-180.png", "landing-shot-light.png", "sw.js", "version.json"): shutil.copy(ROOT + "/" + f, OUT + "/rehost/" + f)
    b, ctx, page = await open_page(pw, BASE + "tmp/test-out/rehost/", ua=UA["mac"], init=MAC_INIT)
    r = await page.evaluate("""() => ({ cls: document.documentElement.className.split(/\\s+/).sort(), done: [...document.querySelectorAll('#landing .lp-done')].map(e => e.textContent).join('|'),
        busy: document.querySelectorAll('#landing .lp-busy').length, img: !!document.querySelector('#landing .lp-shot img'), count: document.querySelector('#landing .lp-desk .lp-count').textContent })""")
    check("saved file re-hosted: gate recomputed, no stale message, picture back, baked character counted", "landing" in r["cls"] and "lp-has" in r["cls"] and r["done"].replace("|", "") == "" and r["busy"] == 0 and r["img"] and r["count"] == "1 character", r)
    await b.close()
    shutil.rmtree(OUT + "/rehost", ignore_errors=True); os.remove(saved)

async def t_returning_namebox(pw, engine):
    b, ctx, page = await open_page(pw, BASE + "?web", engine=engine)
    await seed_character(page, "Box Hero")
    await page.goto(BASE, wait_until="load"); await ready(page)
    await page.click("#landing .lp-desk .lp-save"); await page.wait_for_selector("#saveas-modal.open #saveas-name", timeout=10000)
    top = await page.evaluate("""() => { const i = document.getElementById('saveas-name'), r = i.getBoundingClientRect(), el = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
        return { vis: getComputedStyle(i).visibility, onTop: el === i, z: getComputedStyle(document.getElementById('saveas-modal')).zIndex, focused: document.activeElement === i }; }""")
    check(f"{engine}: the name box shows above the landing page", top["vis"] == "visible" and top["onTop"] and top["z"] == "12100" and top["focused"], top)
    await page.screenshot(path=f"{OUT}/t-namebox-over-gate-{engine}.png")
    await page.fill("#saveas-name", "Friday game")
    async with page.expect_download(timeout=120000) as di:
        await page.keyboard.press("Enter")
    d = await di.value; html = open(await d.path(), encoding="utf-8").read()
    msg = await page.evaluate("document.querySelector('#landing .lp-desk .lp-done').textContent")
    check(f"{engine}: file named as typed, holds the character, message shown", d.suggested_filename == "Friday game.html" and "Box Hero" in html and msg.startswith("Downloaded “Friday game.html” with 1 character inside."), (d.suggested_filename, msg))
    check(f"{engine}: no page errors", not page.errs, page.errs)
    await b.close()

async def t_file(pw):
    b, ctx, page = await open_page(pw, FILE)
    r = await page.evaluate("""() => ({ cls: document.documentElement.className, gate: getComputedStyle(document.getElementById('landing')).display, toolbar: getComputedStyle(document.querySelector('.toolbar')).visibility,
        intro: !document.getElementById('intro-overlay').hidden, wayback: document.getElementById('btn-showlanding').hidden, img: !!document.querySelector('#landing img'), links: document.head.querySelectorAll('link[rel=manifest]').length })""")
    check("file from disk: no gate, sheet and welcome guide as before, nothing hosted is referenced", r["gate"] == "none" and "landing" not in r["cls"] and "lp-" not in r["cls"] and r["toolbar"] == "visible" and r["intro"] and r["wayback"] and not r["img"] and r["links"] == 0 and not page.failed and not page.errs, (r, page.failed, page.errs))
    await b.close()

async def t_ios(pw):
    cases = [("iphone27", None, ["lp-ios", "lp-iphone", "lp-ios-27", "lp-ios-webapp"], "in Safari, then Share", "Make sure Open as Web App is on", "iPhone"),
             ("iphone26", None, ["lp-ios", "lp-iphone", "lp-ios-26", "lp-ios-webapp"], "in Safari, then Share", "Make sure Open as Web App is on", "iPhone"),
             ("iphone18", None, ["lp-ios", "lp-iphone", "lp-ios-share"], "Tap Share in your browser's toolbar.", "Tap Add. The sheet is now", "iPhone"),
             ("ipad27", IPAD_INIT, ["lp-ios", "lp-ipad", "lp-ios-share", "lp-ios-webapp"], "Tap Share in your browser's toolbar.", "Make sure Open as Web App is on", "iPad"),
             ("crios", None, ["lp-ios", "lp-iphone", "lp-ios-share", "lp-ios-webapp"], "Tap Share in your browser's toolbar.", "Make sure Open as Web App is on", "iPhone"),
             ("inapp", None, ["lp-ios", "lp-iphone", "lp-ios-share", "lp-inapp"], "Tap Share in your browser's toolbar.", "Tap Add. The sheet is now", "iPhone")]
    for name, init, want, step1, step3, dev in cases:
        b, ctx, page = await open_page(pw, BASE, engine="webkit", ua=UA[name], vw=(820 if name == "ipad27" else 390), vh=(1180 if name == "ipad27" else 844), init=init, mobile=True)
        r = await page.evaluate("""() => { const vis = e => { const cs = getComputedStyle(e); return cs.display !== 'none' && e.getBoundingClientRect().height > 0; };
            const A = document.querySelector('#landing .lp-apple'), steps = [...A.querySelectorAll('.lp-steps > li')];
            return { cls: document.documentElement.className.split(/\\s+/).filter(c => c.indexOf('lp-') === 0 && c !== 'lp-ready').sort(),
              s1: [...steps[0].querySelectorAll('p')].filter(vis).map(p => p.textContent.replace(/\\s+/g,' ').trim()), s3: [...steps[2].querySelectorAll('p')].filter(vis).map(p => p.textContent.replace(/\\s+/g,' ').trim()),
              h1: [...document.querySelectorAll('#landing h1')].filter(vis).map(h => h.textContent), nsteps: steps.length, glyphs: steps[0].querySelectorAll('p:not([hidden]) .lp-key').length,
              warn: [...A.querySelectorAll('.lp-warn')].filter(vis).map(w => w.textContent.replace(/\\s+/g,' ').trim().slice(0, 40)),
              desk: getComputedStyle(document.querySelector('#landing .lp-desk')).display, over: document.getElementById('landing').scrollWidth > document.getElementById('landing').clientWidth,
              small: [...A.querySelectorAll('.lp-link, .lp-dl')].filter(vis).map(e => Math.round(e.getBoundingClientRect().height)).filter(h => h < 44) }; }""")
        ok = (r["cls"] == sorted(want) and len(r["s1"]) == 1 and step1 in r["s1"][0].replace(" .", ".").replace("  ", " ") and len(r["s3"]) == 1 and r["s3"][0].startswith(step3)
              and r["h1"] == [f"On {dev}, add the sheet to your Home Screen."] and r["nsteps"] == 4 and r["desk"] == "none" and not r["over"] and not r["small"]
              and (bool(r["warn"]) == (name == "inapp")) and not page.errs)
        check(f"iOS {name}: classes, step wording, device word, 44px targets, no overflow", ok, (r, page.errs))
        if name in ("iphone27", "ipad27", "inapp"): await page.screenshot(path=f"{OUT}/t-ios-{name}.png", full_page=False)
        if name == "iphone27":
            await page.evaluate("document.getElementById('landing').scrollTo(0, 99999)"); await page.wait_for_timeout(200); await page.screenshot(path=f"{OUT}/t-ios-iphone27-bottom.png")
            await page.evaluate("navigator.clipboard.writeText = async (t) => { window.__copied = t; }")
            await page.evaluate("document.querySelector('#landing .lp-apple .lp-alt .lp-copy').click()"); await page.wait_for_timeout(300)
            c = await page.evaluate("({ copied: window.__copied, label: document.querySelector('#landing .lp-apple .lp-alt .lp-copy').textContent })")
            check("iOS: Copy the link copies this page's address and says so", c["copied"] == BASE and c["label"] == "Link copied", c)
        await b.close()
    # installed web app: straight to the sheet
    b, ctx, page = await open_page(pw, BASE, engine="webkit", ua=UA["iphone27"], vw=390, vh=844, mobile=True, init="Object.defineProperty(navigator, 'standalone', {get: () => true});")
    st = await page.evaluate(STATE)
    check("iOS Home Screen app: no gate", "landing" not in st["cls"] and st["gate"] == "none" and st["toolbar"] == "visible", st)
    await b.close()
    # characters already in the Safari tab: told to save them first
    b, ctx, page = await open_page(pw, BASE + "?web", engine="webkit", ua=UA["iphone27"], vw=390, vh=844, mobile=True)
    await seed_character(page, "Tab Hero")
    await page.goto(BASE, wait_until="load"); await ready(page)
    r = await page.evaluate("""() => { const w = document.querySelector('#landing .lp-apple .lp-on-has'); return { shown: getComputedStyle(w).display, text: w.textContent.replace(/\\s+/g,' ').trim() }; }""")
    check("iOS with characters in the tab: asks to save them to a file first, with the count", r["shown"] == "block" and r["text"].startswith("You have 1 character saved in this browser tab.") and "Save my 1 character to a file" in r["text"], r)
    await page.screenshot(path=f"{OUT}/t-ios-has.png")
    await b.close()

async def t_android(pw):
    b, ctx, page = await open_page(pw, BASE, ua=UA["android"], vw=412, vh=915, mobile=True)
    r = await page.evaluate("""() => { const vis = e => getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().height > 0;
        return { cls: document.documentElement.className.split(/\\s+/).filter(c => c.indexOf('lp-') === 0 && c !== 'lp-ready').sort(), h1: [...document.querySelectorAll('#landing h1')].filter(vis).map(h => h.textContent),
          btn: vis(document.querySelector('#landing .lp-install')), manual: getComputedStyle(document.querySelector('#landing .lp-manual')).fontSize,
          over: document.getElementById('landing').scrollWidth > document.getElementById('landing').clientWidth, get: document.querySelector('#landing .lp-droid a.lp-get').download }; }""")
    check("Android: install variant, manual steps at body size, no install button until the browser offers one", r["cls"] == ["lp-android"] and r["h1"] == ["On Android, install the sheet as an app."] and not r["btn"] and r["manual"] in ("15px", "16px") and not r["over"] and r["get"].startswith("Character Sheet v"), r)
    await page.evaluate("""() => { window.__prompts = 0; const e = new Event('beforeinstallprompt', {cancelable: true}); e.prompt = () => { window.__prompts++; return Promise.resolve(); }; window.dispatchEvent(e); window.__prevented = e.defaultPrevented; }""")
    r = await page.evaluate("({ can: document.documentElement.classList.contains('lp-can-install'), prevented: window.__prevented, btn: getComputedStyle(document.querySelector('#landing .lp-on-install')).display })")
    check("Android: the browser's install offer is held and the button appears", r["can"] and r["prevented"] and r["btn"] == "block", r)
    await page.screenshot(path=f"{OUT}/t-android-install.png")
    await page.click("#landing .lp-install"); await page.wait_for_timeout(200)
    r = await page.evaluate("({ n: window.__prompts, can: document.documentElement.classList.contains('lp-can-install') })")
    check("Android: the button fires the install prompt once", r["n"] == 1 and not r["can"], r)
    await page.evaluate("window.dispatchEvent(new Event('appinstalled'))")
    check("Android: after install, the page says where to find it", (await page.evaluate("document.querySelector('#landing .lp-droid .lp-done').textContent")).startswith("Installed."))
    check("Android: no page errors", not page.errs, page.errs)
    await b.close()
    # installed app (display-mode: standalone): straight to the sheet
    # (CDP cannot emulate display-mode here, so the media query is answered by a stub: this checks our logic, not the browser's)
    standalone = "const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q) ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} } : mm(q);"
    b, ctx, page = await open_page(pw, BASE, ua=UA["android"], vw=412, vh=915, mobile=True, init=standalone)
    st = await page.evaluate(STATE)
    check("Android installed app (display-mode: standalone): no gate", "landing" not in st["cls"] and st["gate"] == "none" and st["toolbar"] == "visible", st)
    await b.close()

async def t_layout(pw):
    b = await pw.chromium.launch(headless=True)
    for vw, vh in ((320, 640), (390, 844), (768, 1024), (901, 700), (1024, 768), (1300, 800), (1920, 1080)):
        ctx = await b.new_context(viewport={"width": vw, "height": vh}, service_workers="block", user_agent=UA["mac"]); await ctx.add_init_script(MAC_INIT)
        page = await ctx.new_page(); await page.goto(BASE, wait_until="load"); await ready(page)
        r = await page.evaluate("""() => { const L = document.getElementById('landing'), a = L.querySelector('.lp-unless-has a.lp-get').getBoundingClientRect(), s = L.querySelector('.lp-shot');
            return { over: L.scrollWidth > L.clientWidth, btnTop: Math.round(a.top), btnH: Math.round(a.height), btnW: Math.round(a.width), shot: getComputedStyle(s).display, cols: getComputedStyle(L.querySelector('.lp-desk')).gridTemplateColumns.split(' ').length,
                     clipped: [...L.querySelectorAll('h1, h2, p, a, button')].filter(e => e.getBoundingClientRect().width > 0 && e.scrollWidth > e.clientWidth + 1).length }; }""")
        ok = not r["over"] and r["btnH"] >= 56 and r["btnTop"] < vh and r["clipped"] == 0 and ((r["cols"] == 2 and r["shot"] == "block") if vw > 900 else (r["cols"] == 1 and r["shot"] == "none"))
        check(f"layout {vw}x{vh}: no overflow or clipping, download button above the fold, picture only on wide screens", ok, r)
        if vw in (320, 768, 1920): await page.screenshot(path=f"{OUT}/t-layout-{vw}.png")
        await ctx.close()
    # colours by computed value, both modes
    for mode, want in (("light", ("rgb(138, 109, 34)", "rgb(255, 255, 255)", "rgb(233, 234, 236)")), ("dark", ("rgb(226, 196, 119)", "rgb(20, 20, 20)", "rgb(12, 13, 15)"))):
        ctx = await b.new_context(viewport={"width": 1300, "height": 800}, service_workers="block", user_agent=UA["mac"]); await ctx.add_init_script(MAC_INIT)
        if mode == "dark": await ctx.add_init_script("try{ localStorage.setItem('dnd-sheet-dark', '1'); }catch(e){}")
        page = await ctx.new_page(); await page.goto(BASE, wait_until="load"); await ready(page)
        r = await page.evaluate("""() => { const L = document.getElementById('landing'), a = L.querySelector('.lp-unless-has a.lp-get'), cs = getComputedStyle(a);
            return [cs.backgroundColor, cs.color, getComputedStyle(L).backgroundColor, getComputedStyle(a).borderRadius, getComputedStyle(L.querySelector('.lp-steps')).boxShadow, L.querySelector('.lp-shot img').getAttribute('src')]; }""")
        check(f"{mode}: button fill, ink and page colour match the palette; square corners; no shadow; matching picture", tuple(r[:3]) == want and r[3] == "0px" and r[4] == "none" and r[5] == f"landing-shot-{mode}.png", r)
        await page.screenshot(path=f"{OUT}/t-final-desktop-{mode}.png")
        await ctx.close()
    await b.close()

async def t_print(pw):
    b = await pw.chromium.launch(headless=True)
    counts = {}
    for name, url in (("gated", BASE), ("ungated", BASE + "?web")):
        ctx = await b.new_context(viewport={"width": 1300, "height": 900}, service_workers="block", user_agent=UA["mac"]); await ctx.add_init_script(MAC_INIT)
        page = await ctx.new_page(); await page.goto(url, wait_until="load"); await ready(page)
        if name == "ungated": await page.evaluate("dismissIntro()")
        pdf = await page.pdf(format="Letter", print_background=True)
        counts[name] = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
        if name == "gated":
            await page.emulate_media(media="print")
            counts["gate_display_in_print"] = await page.evaluate("getComputedStyle(document.getElementById('landing')).display")
            counts["toolbar_vis_in_print"] = await page.evaluate("getComputedStyle(document.querySelector('.card')).visibility")
        await ctx.close()
    check("print: the landing page never prints, and the sheet prints the same page count either way", counts["gated"] == counts["ungated"] and counts["gated"] >= 1 and counts["gate_display_in_print"] == "none" and counts["toolbar_vis_in_print"] == "visible", counts)
    print("   PDF pages:", counts)
    await b.close()

async def t_sw(pw):
    b, ctx, page = await open_page(pw, BASE, ua=UA["mac"], init=MAC_INIT, sw="allow")
    await page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.getRegistration().then(r => !!(r && r.active))", timeout=30000)
    await page.reload(wait_until="load"); await ready(page)
    ctl = await page.evaluate("!!navigator.serviceWorker.controller")
    st = await page.evaluate(STATE)
    async with page.expect_download(timeout=90000) as di:
        await page.click("#landing .lp-unless-has a.lp-get")
    d = await di.value; got = open(await d.path(), "rb").read()
    check("service worker in control: gate still right and the download is still byte-identical", ctl and "landing" in st["cls"] and hashlib.sha256(got).hexdigest() == SRC_SHA, (ctl, st, len(got)))
    await b.close()

async def t_firefox(pw):
    b, ctx, page = await open_page(pw, BASE, engine="firefox")
    st = await page.evaluate(STATE)
    async with page.expect_download(timeout=90000) as di:
        await page.click("#landing .lp-unless-has a.lp-get")
    d = await di.value; got = open(await d.path(), "rb").read()
    check("Firefox desktop: gate on and the download is byte-identical", "landing" in st["cls"] and hashlib.sha256(got).hexdigest() == SRC_SHA and d.suggested_filename.startswith("Character Sheet v") and not page.errs, (st, d.suggested_filename, page.errs))
    await page.screenshot(path=f"{OUT}/t-firefox.png")
    await b.close()

async def t_classic(pw):
    b, ctx, page = await open_page(pw, BASE + "?web", ua=UA["mac"], init=MAC_INIT)
    await page.evaluate("dismissIntro()")
    await page.evaluate("""() => { const s = document.getElementById('set-theme'); document.getElementById('btn-settings').click(); renderThemeOptions(); s.value = 'classic'; s.dispatchEvent(new Event('change', {bubbles:true})); flushSave(); }""")
    await page.wait_for_timeout(1500)
    th = await page.evaluate("document.body.dataset.theme")
    await page.goto(BASE, wait_until="load"); await ready(page)
    r = await page.evaluate("""() => { const L = document.getElementById('landing'); return { theme: document.body.dataset.theme, gate: getComputedStyle(L).display, bg: getComputedStyle(L).backgroundColor,
        btn: getComputedStyle(L.querySelector('.lp-dl')).backgroundColor, over: L.scrollWidth > L.clientWidth, top: document.elementFromPoint(650, 300).closest('#landing') !== null }; }""")
    check("Classic theme underneath: the landing page looks the same and stays on top", th == "classic" and r["theme"] == "classic" and r["gate"] == "block" and r["bg"] == "rgb(233, 234, 236)" and r["btn"] == "rgb(138, 109, 34)" and r["top"] and not r["over"], (th, r))
    await page.screenshot(path=f"{OUT}/t-classic.png")
    await b.close()

async def t_fullscreen(pw):
    # A desktop browser window in full screen can match (display-mode: fullscreen). That is not an install,
    # so the gate must still show (2.171.3: it used to open the sheet).
    fs = "const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*fullscreen/.test(q) ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} } : mm(q);"
    b, ctx, page = await open_page(pw, BASE, ua=UA["mac"], init=MAC_INIT + fs, wait=False)
    await page.wait_for_timeout(1500)
    r = await page.evaluate(STATE)
    check("Desktop in full screen: the download page shows", "landing" in r["cls"] and r["gate"] == "block", r)
    await b.close()

TESTS = {"desktop": t_desktop_fresh, "early": t_early_paint, "bypass": t_bypass, "returning": t_returning,
         "namebox_webkit": lambda pw: t_returning_namebox(pw, "webkit"), "namebox_firefox": lambda pw: t_returning_namebox(pw, "firefox"),
         "file": t_file, "ios": t_ios, "android": t_android, "layout": t_layout, "print": t_print, "sw": t_sw, "firefox": t_firefox, "classic": t_classic, "fullscreen": t_fullscreen}

def port_open():
    with socket.socket() as k:
        k.settimeout(0.5)
        return k.connect_ex(("127.0.0.1", PORT)) == 0

async def main():
    names = sys.argv[1:] or list(TESTS)
    server = None
    if not port_open():   # reuse a server that is already up, else run our own for the length of the tests
        server = subprocess.Popen([sys.executable, str(Path(__file__).with_name("serve.py")), "--root", ROOT, "--port", str(PORT)])
        for _ in range(40):
            if port_open(): break
            time.sleep(0.25)
    try:
        async with async_playwright() as pw:
            for n in names:
                print(f"--- {n}")
                try: await TESTS[n](pw)
                except Exception as e:
                    import traceback
                    traceback.print_exc(limit=3)
                    check(f"{n}: ran to completion", False, repr(e)[:300])
    finally:
        if server: server.terminate()
    print("\nFAILED:" if fails else "\nALL PASS", fails if fails else "")
    sys.exit(1 if fails else 0)
asyncio.run(main())
