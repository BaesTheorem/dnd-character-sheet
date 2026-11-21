"""Make the landing page's product pictures: landing-shot-light.png and landing-shot-dark.png.
Builds an invented sample character (Vessa Thornwick, from design/seed/BRIEF.md) through the sheet's own
wizard code, so the numbers are computed by the sheet, then captures the top of the Core page.
Run it again after a visual change to the Core page:  python3 design/landing-shot.py
Needs `pip install playwright pillow` and `playwright install chromium`; `brew install pngquant` for small files."""
import asyncio, json, os, shutil, subprocess
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
ROOT = str(Path(__file__).resolve().parents[1])
URL = "file://" + ROOT + "/index.html"
OUT = ROOT + "/tmp/test-out"   # raw captures; tmp/ is gitignored
os.makedirs(OUT, exist_ok=True)

BUILD = """async () => {
  const log = [];
  dismissIntro();
  openWizard();
  // race: a fixed-bonus race keeps the scripted build free of choice pickers
  const raceSel = $("wiz-race");
  const want = [...raceSel.options].map(o => o.value).find(v => /^Elf \\(Wood\\)$|^Wood Elf$/i.test(v)) || "Human";
  raceSel.value = want; raceSel.dispatchEvent(new Event("change", {bubbles:true})); log.push("race=" + want);
  genMode = "manual"; manualScores = {str:"12", dex:"16", con:"14", int:"10", wis:"14", cha:"8"};
  wizClasses = [{name:"Ranger", level:5, sub:"Hunter", subOpts:{"Hunter's Prey":"Colossus Slayer"}, fightingStyles:["Archery"], classChoices:{deftCanny:"Stealth"}}];
  wizFocus = "Ranger"; syncBuildToSheet(); renderBuilder();
  try{ hpMode = "average"; regenHp("average", wizClasses, true); }catch(e){ log.push("hp:" + e.message); }
  $("wiz-bg").value = "Outlander"; $("wiz-bg").dispatchEvent(new Event("change", {bubbles:true}));
  $("wiz-name").value = "Vessa Thornwick";
  // class skill picks, if the step has rendered its checkboxes
  try{ wizStep = 3; renderWizStep(); }catch(e){ log.push("step3:" + e.message); }
  const cbs = [...document.querySelectorAll(".wiz-skill-cb")]; ["stealth","perception","survival"].forEach(k => { const c = cbs.find(x => x.value === k); if(c) c.checked = true; });
  log.push("skillcbs=" + cbs.length);
  createCharacter();
  await new Promise(r => setTimeout(r, 800));
  const td = $("tool-done"); if(td && $("toolmodal").classList.contains("open")) td.click();
  await new Promise(r => setTimeout(r, 300));
  // proper catalog gear (the scripted wizard leaves the starting-equipment choices as raw text), equipped so AC and attacks compute
  [["Studded Leather Armor",1],["Longbow",1],["Shortsword",2],["Arrows (20)",1]].forEach(([n,q]) => addInvItem(n, q));
  await new Promise(r => setTimeout(r, 300));
  for(let i = 0; i < NINV; i++){ const nm = ($("invname-"+i)||{}).value || ""; const cb = $("invequip-"+i);
    if(cb && /^(Studded Leather Armor|Longbow|Shortsword)$/.test(nm) && !cb.checked){ cb.checked = true; cb.dispatchEvent(new Event("change", {bubbles:true})); } }
  await new Promise(r => setTimeout(r, 300));
  const as = $("armorsel"); if([...as.options].some(o => o.value === "Studded Leather Armor")){ as.value = "Studded Leather Armor"; as.dispatchEvent(new Event("change", {bubbles:true})); }
  if(asiChoices[0]){ asiChoices[0].type = "asi"; asiChoices[0].ab1 = "dex"; asiChoices[0].ab2 = "dex"; try{ applyAsiBonuses(); updateAsiFlag(); }catch(e){ log.push("asi:" + e.message); } }
  $("alignment").value = "Neutral Good"; $("player").value = "Sam"; $("campaign").value = "The Long Road";
  $("alignment").dispatchEvent(new Event("input", {bubbles:true}));
  compute();
  const mx = parseInt($("hpmax").value, 10) || 0; if(mx){ $("hpcur").value = String(Math.max(1, mx - 6)); $("hpcur").dispatchEvent(new Event("input", {bubbles:true})); }
  compute();
  // what got built, so a run that drifted (a renamed race, a new pending choice) is visible in the output
  return { log, name: $("charname").value, cls: $("classlevel").value, race: $("race").value, bg: $("background").value,
           hp: $("hpcur").value + "/" + $("hpmax").value, scores: ABKEYS.map(k => k + "=" + finalScore(k)).join(" "),
           attacks: [...document.querySelectorAll(".attacks tbody tr")].map(tr => (tr.querySelector("input")||{}).value).filter(Boolean).slice(0,5),
           armor: $("armorsel").value, openModals: [...document.querySelectorAll(".modal.open")].map(m => m.id) };
}"""

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True)
        for mode in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 1300, "height": 820}, device_scale_factor=2)
            page = await ctx.new_page(); errs = []
            page.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:300]))
            if mode == "dark": await ctx.add_init_script("try{ localStorage.setItem('dnd-sheet-dark','1'); }catch(e){}")
            await page.goto(URL, wait_until="load", timeout=180000)
            await page.wait_for_function("typeof compute === 'function'", timeout=120000)
            await page.wait_for_timeout(3000)
            info = await page.evaluate(BUILD)
            await page.wait_for_timeout(1200)
            await page.evaluate("window.scrollTo(0,0)")
            print(mode, json.dumps(info)[:900], "errs:", errs[:3])
            await page.screenshot(path=f"{OUT}/shot-raw-{mode}.png")
            await ctx.close()
        await b.close()
asyncio.run(main())
# 1040 px wide = 2x the widest slot the page gives it. pngquant keeps the flat greys exact at about a third
# of the full-colour size (Pillow's own quantizers tint them); without pngquant the full-colour file ships.
for mode in ("light", "dark"):
    im = Image.open(f"{OUT}/shot-raw-{mode}.png").convert("RGB")
    w = 1040; im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    out = f"{ROOT}/landing-shot-{mode}.png"; im.save(out, "PNG", optimize=True)
    if shutil.which("pngquant"):
        subprocess.run(["pngquant", "--force", "--speed", "1", "--strip", "--nofs", "--quality", "85-100", "256", out, "-o", out], check=True)
    print(mode, im.size, os.path.getsize(out), "bytes")
