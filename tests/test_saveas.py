"""Save As tests, run on the sheet opened from disk.
Chromium: the native save dialog, mocked (Playwright cannot drive the real one). WebKit and Firefox: the
sheet's own name box. Needs `pip install playwright` and `playwright install chromium webkit firefox`.
Usage: python3 tests/test_saveas.py [unit] [chromium] [webkit] [firefox]"""
import asyncio, os, sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT = str(Path(__file__).resolve().parents[1])
URL = "file://" + ROOT + "/index.html"
OUT = ROOT + "/tmp/test-out"   # tmp/ is gitignored
os.makedirs(OUT, exist_ok=True)
fails = []
def check(label, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + label + ((" :: " + str(extra)) if extra and not cond else ""))
    if not cond: fails.append(label)

async def boot(browser, **ctx_opts):
    ctx = await browser.new_context(viewport={"width": 1300, "height": 850}, accept_downloads=True, **ctx_opts)
    page = await ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)[:300]))
    await page.goto(URL, wait_until="load", timeout=180000)
    await page.wait_for_function("typeof compute === 'function' && typeof saveSheetAs === 'function'", timeout=120000)
    await page.wait_for_timeout(2500)
    await page.evaluate("dismissIntro()")
    return ctx, page, errs

MOCK = """(mode) => {
  window.__pick = { calls: [], written: null, name: null };
  window.showSaveFilePicker = async (opts) => {
    window.__pick.calls.push(JSON.parse(JSON.stringify(opts)));
    if(mode === 'abort') throw new DOMException('The user aborted a request.', 'AbortError');
    if(mode === 'security') throw new DOMException('Must be handling a user gesture to show a file picker.', 'SecurityError');
    const name = mode === 'rename' ? 'Thorin Oakenshield.html' : opts.suggestedName;
    return { name, kind: 'file', createWritable: async () => {
      if(mode === 'writefail') throw new DOMException('nope', 'NotAllowedError');
      let buf = [];
      return { write: async (b) => { buf.push(await (b.text ? b.text() : String(b))); }, close: async () => { window.__pick.written = buf.join(''); window.__pick.name = name; } }; } };
  }; }"""

async def chromium_tests(pw):
    b = await pw.chromium.launch(headless=True)
    ctx, page, errs = await boot(b)
    info = await page.evaluate("({ secure: isSecureContext, native: typeof showSaveFilePicker, sem: (typeof APP_SEMVER !== 'undefined' ? APP_SEMVER : null), def: versionedFileName(), sug: suggestedSaveName() })")
    print("chromium file:// ->", info)
    check("chromium: default suggestion is the versioned name", info["sug"] == info["def"] and info["def"].startswith("Character Sheet v"))
    # 1. picker, accept suggested name
    await page.evaluate(MOCK, "ok")
    await page.click("#btn-savecopy"); await page.wait_for_function("window.__pick.written !== null", timeout=60000)
    r = await page.evaluate("({ calls: window.__pick.calls, len: window.__pick.written.length, head: window.__pick.written.slice(0,15), hasRoster: /id=\\\"embedded-roster\\\"/.test(window.__pick.written), hasModal: /id=\\\"saveas-modal\\\"/.test(window.__pick.written), status: document.getElementById('status').textContent, stored: localStorage.getItem(SAVE_NAME_KEY), modal: !!document.getElementById('saveas-modal') })")
    check("chromium: picker called once with the suggested name, .html type, id and startIn", len(r["calls"]) == 1 and r["calls"][0]["suggestedName"] == info["def"] and r["calls"][0]["types"][0]["accept"] == {"text/html": [".html"]} and r["calls"][0]["id"] == "dnd-sheet" and r["calls"][0]["startIn"] == "downloads", r["calls"])
    check("chromium: wrote a full sheet (doctype, roster, >10 MB)", r["head"] == "<!DOCTYPE html>" and r["hasRoster"] and r["len"] > 10_000_000, (r["head"], r["len"]))
    check("chromium: no name box was shown or serialized", not r["modal"] and not r["hasModal"])
    check("chromium: status says Saved with the name", r["status"].startswith("Saved “" + info["def"] + "”: all 1 character"), r["status"])
    check("chromium: the default name is not remembered", r["stored"] is None, r["stored"])
    # 2. picker, user renames in the dialog
    await page.evaluate(MOCK, "rename")
    await page.click("#btn-savecopy"); await page.wait_for_function("window.__pick.written !== null", timeout=60000)
    r = await page.evaluate("({ status: document.getElementById('status').textContent, stored: localStorage.getItem(SAVE_NAME_KEY), sug: suggestedSaveName() })")
    check("chromium: a chosen name is reported and remembered", "Thorin Oakenshield.html" in r["status"] and r["stored"] == "Thorin Oakenshield.html" and r["sug"] == "Thorin Oakenshield.html", r)
    # 3. abort = silent cancel
    await page.evaluate("flashStatus('')"); await page.evaluate(MOCK, "abort")
    await page.click("#btn-savecopy"); await page.wait_for_timeout(1200)
    r = await page.evaluate("({ calls: window.__pick.calls.length, written: window.__pick.written, modal: !!document.getElementById('saveas-modal'), sug: window.__pick.calls[0].suggestedName })")
    check("chromium: closing the dialog cancels with no file and no name box", r["calls"] == 1 and r["written"] is None and not r["modal"], r)
    check("chromium: the remembered name is suggested next time", r["sug"] == "Thorin Oakenshield.html", r["sug"])
    # 4. picker refuses (no gesture) -> falls back to the name box -> ordinary download
    await page.evaluate(MOCK, "security")
    await page.click("#btn-savecopy"); await page.wait_for_selector("#saveas-modal.open #saveas-name", timeout=10000)
    val = await page.input_value("#saveas-name")
    check("chromium: a refused picker falls back to the name box, prefilled without .html", val == "Thorin Oakenshield", val)
    async with page.expect_download(timeout=90000) as di:
        await page.keyboard.press("Enter")
    d = await di.value
    check("chromium: fallback download carries the name", d.suggested_filename == "Thorin Oakenshield.html", d.suggested_filename)
    # 5. write fails after a pick -> ordinary download under the picked name
    await page.evaluate(MOCK, "writefail")
    async with page.expect_download(timeout=90000) as di:
        await page.click("#btn-savecopy")
    d = await di.value
    st = await page.evaluate("document.getElementById('status').textContent")
    check("chromium: a failed write becomes a download", d.suggested_filename == "Thorin Oakenshield.html" and st.startswith("Downloaded “"), (d.suggested_filename, st))
    # 6. double click = one dialog
    await page.evaluate("""() => { window.__n = 0; window.showSaveFilePicker = async (o) => { window.__n++; await new Promise(r => setTimeout(r, 600)); throw new DOMException('x','AbortError'); }; }""")
    await page.evaluate("document.getElementById('btn-savecopy').click(); document.getElementById('btn-savecopy').click();")
    await page.wait_for_timeout(1500)
    check("chromium: two fast clicks open one dialog", await page.evaluate("window.__n") == 1)
    check("chromium: no page errors", not errs, errs)
    await b.close()

async def namebox_tests(pw, engine):
    b = await getattr(pw, engine).launch(headless=True)
    ctx, page, errs = await boot(b)
    native = await page.evaluate("typeof window.showSaveFilePicker")
    check(f"{engine}: no native picker here", native == "undefined", native)
    default = await page.evaluate("versionedFileName()")
    # open, check prefill + focus + selection
    await page.click("#btn-savecopy"); await page.wait_for_selector("#saveas-modal.open #saveas-name", timeout=10000)
    st = await page.evaluate("""() => { const i = document.getElementById('saveas-name'); return { val: i.value, focused: document.activeElement === i, sel: [i.selectionStart, i.selectionEnd],
        lock: document.documentElement.classList.contains('overlay-open'), ext: document.querySelector('.saveas-ext').textContent,
        z: getComputedStyle(document.getElementById('saveas-modal')).display, fs: getComputedStyle(i).fontSize }; }""")
    check(f"{engine}: name box open, prefilled, focused, all selected", st["val"] == default[:-5] and st["focused"] and st["sel"] == [0, len(st["val"])] and st["ext"] == ".html" and st["lock"], st)
    await page.screenshot(path=f"{OUT}/saveas-{engine}.png")
    # Escape cancels
    await page.keyboard.press("Escape"); await page.wait_for_timeout(300)
    check(f"{engine}: Escape closes the box and unlocks the page", await page.evaluate("!document.getElementById('saveas-modal') && !document.documentElement.classList.contains('overlay-open')"))
    # Cancel button
    await page.click("#btn-savecopy"); await page.wait_for_selector("#saveas-modal.open"); await page.click("#saveas-cancel"); await page.wait_for_timeout(200)
    check(f"{engine}: Cancel closes the box", await page.evaluate("!document.getElementById('saveas-modal')"))
    # backdrop
    await page.click("#btn-savecopy"); await page.wait_for_selector("#saveas-modal.open"); await page.mouse.click(8, 8); await page.wait_for_timeout(200)
    check(f"{engine}: a click on the backdrop closes the box", await page.evaluate("!document.getElementById('saveas-modal')"))
    # empty name is refused
    await page.click("#btn-savecopy"); await page.wait_for_selector("#saveas-modal.open #saveas-name")
    await page.fill("#saveas-name", "  ..  "); await page.keyboard.press("Enter"); await page.wait_for_timeout(300)
    check(f"{engine}: an empty name keeps the box open", await page.evaluate("!!document.getElementById('saveas-modal')"))
    # typing must not reach the sheet's global input handler (no autosave churn)
    await page.evaluate("window.__ic = 0; document.addEventListener('input', () => window.__ic++);")
    await page.fill("#saveas-name", ""); await page.type("#saveas-name", "Thorin: the/bold? ")
    check(f"{engine}: typing a name does not reach the global input handler", await page.evaluate("window.__ic") == 0, await page.evaluate("window.__ic"))
    async with page.expect_download(timeout=120000) as di:
        await page.click("#saveas-ok")
    d = await di.value
    path = await d.path(); html = open(path, encoding="utf-8").read()
    check(f"{engine}: the download uses the cleaned name", d.suggested_filename == "Thorin the bold.html", d.suggested_filename)
    check(f"{engine}: the file is a full sheet without the name box", html.startswith("<!DOCTYPE html>") and 'id="embedded-roster"' in html and 'id="saveas-modal"' not in html and len(html) > 10_000_000, len(html))
    check(f"{engine}: no modal is serialized open", 'class="modal open' not in html)
    st = await page.evaluate("({ status: document.getElementById('status').textContent, stored: localStorage.getItem(SAVE_NAME_KEY), box: !!document.getElementById('saveas-modal') })")
    check(f"{engine}: status and remembered name", st["status"].startswith("Downloaded “Thorin the bold.html”: all 1 character") and st["stored"] == "Thorin the bold.html" and not st["box"], st)
    # next save suggests the remembered name
    await page.click("#btn-savecopy"); await page.wait_for_selector("#saveas-modal.open #saveas-name")
    check(f"{engine}: next Save suggests the remembered name", await page.input_value("#saveas-name") == "Thorin the bold")
    await page.keyboard.press("Escape")
    check(f"{engine}: no page errors", not errs, errs)
    # the saved file opens clean
    saved = f"{OUT}/saved-{engine}.html"; await d.save_as(saved)
    ctx2 = await b.new_context(viewport={"width": 1300, "height": 850}); p2 = await ctx2.new_page(); e2 = []
    p2.on("pageerror", lambda e: e2.append(str(e)[:300]))
    await p2.goto("file://" + saved, wait_until="load", timeout=180000)
    await p2.wait_for_function("typeof compute === 'function'", timeout=120000); await p2.wait_for_timeout(2500)
    r = await p2.evaluate("({ modals: document.querySelectorAll('.modal.open').length, box: !!document.getElementById('saveas-modal'), saveFn: typeof saveSheetAs })")
    check(f"{engine}: the saved file opens with no open modal and a working Save", r["modals"] == 0 and not r["box"] and r["saveFn"] == "function" and not e2, (r, e2))
    await b.close(); os.remove(saved)

async def unit(pw):
    b = await pw.chromium.launch(headless=True); ctx, page, errs = await boot(b)
    cases = { "Thorin": "Thorin.html", "  my sheet.HTML ": "my sheet.html", "a/b\\c:d*e?f\"g<h>i|j": "a b c d e f g h i j.html", "..hidden": "hidden.html",
              "trailing. . ": "trailing.html", "con": "con sheet.html", "": "", "   ": "", ".html": "", "x.htm": "x.html", "Ærøskøbing 日本": "Ærøskøbing 日本.html", "tab\there": "tab here.html" }
    got = await page.evaluate("(cs) => Object.fromEntries(Object.keys(cs).map(k => [k, cleanFileName(k)]))", cases)
    for k, v in cases.items(): check(f"cleanFileName({k!r}) -> {v!r}", got[k] == v, got[k])
    check("cleanFileName caps the length", len(await page.evaluate("cleanFileName('x'.repeat(400))")) == 125)
    await b.close()

async def main():
    async with async_playwright() as pw:
        which = sys.argv[1:] or ["unit", "chromium", "webkit", "firefox"]
        if "unit" in which: await unit(pw)
        if "chromium" in which: await chromium_tests(pw)
        for e in ("webkit", "firefox"):
            if e in which: await namebox_tests(pw, e)
    print("\nFAILED:" if fails else "\nALL PASS", fails if fails else "")
asyncio.run(main())
