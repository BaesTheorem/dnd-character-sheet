#!/usr/bin/env python3
"""Extract the Ancestral Weapons upgrade catalog from the source PDF into upgrades.json.

The upgrade DESCRIPTIONS are third-party copyrighted text (Ancestral Weapons by
Matt Vaughan / Dungeon Rollers), so upgrades.json is gitignored — it's a local
artifact, regenerated from the PDF, never committed. Only the NON-copyrightable
mechanics (names/costs/tiers/tags/requirements) ship in the app's JS; the text is
baked into the local #source-data / homebrew layer, same as the 5etools data.

Usage: python3 extract.py /path/to/Ancestral_Weapons_Final_v1.2.pdf
Needs: pip install --break-system-packages pdfplumber

Notes: the PDF is two-column with font-kerning-mangled headers, so we (1) split
each page into columns by word x-position to de-interleave, (2) anchor upgrades on
the clean "N Spirit point(s)" cost lines, (3) recover the case-only-mangled names
via title-case + "of the" reconstruction. Verified: 134 upgrades, 36/45/28/25 per
tier (matches the book's own summary). Source quirks fixed: 'Spell Storing (level
4)' in tier 4 actually grants a level-5 spell -> renamed '(level 5)'; 'Spellhunter'
is reused for two different upgrades (T2 + T3) -> the T3 one is disambiguated.
"""
import re, json, sys
from collections import Counter
import pdfplumber

PDF = sys.argv[1] if len(sys.argv) > 1 else __import__("os").path.expanduser("~/Downloads/Ancestral_Weapons_Final_v1.2.pdf")
CLASSES = ["barbarian","bard","cleric","druid","fighter","monk","paladin","ranger","rogue","sorcerer","warlock","wizard"]

def col_lines(page):
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    mid = page.width/2; out=[]
    for col in (0,1):
        cw=[w for w in words if (w['x0']<mid)==(col==0)]
        cw.sort(key=lambda w:(round(w['top']/3), w['x0']))
        lines={}
        for w in cw: lines.setdefault(round(w['top']/3),[]).append(w)
        for k in sorted(lines): out.append(" ".join(x['text'] for x in sorted(lines[k],key=lambda w:w['x0'])))
        out.append("@@COL@@")
    return out

pdf = pdfplumber.open(PDF)
lines=[]
for i in range(7,19):
    lines.append(f"##### PDF PAGE {i+1} #####"); lines += col_lines(pdf.pages[i])
end=next(i for i,l in enumerate(lines) if 'Chapter 3: Ancestral Traits' in l)
start=next(i for i,l in enumerate(lines) if "pgrAde escriptions" in l)
body=lines[start+1:end]

TIER_RE=re.compile(r'^T\s*\d+:\s*L'); TIER2_RE=re.compile(r'^ier\s+eveL')
COST_RE=re.compile(r'^\s*(\d+)\s+Spirit points?',re.I)
FURN=re.compile(r'^(ANCESTRAL WEAPONS|@@COL@@|#####|\d+\s*$|U\s+d\s*$|pgrAde escriptions|T\s+d\s*$)')
def is_tier(l): return bool(TIER_RE.match(l.strip()) or TIER2_RE.match(l.strip()))
def clean_name(parts):
    raw=re.sub(r'\s+',' '," ".join(parts)).strip()
    if 'of the' in raw.lower():
        words=[t for t in raw.split(' ') if t.lower() not in ('of','the')]
        if len(words)>=2: raw=words[0]+" of the "+" ".join(words[1:])
    n=raw.title().replace("(Level ","(level ")
    n=re.sub(r'\bOf The\b','of the',n)
    return re.sub(r"([’'])S\b", lambda m:m.group(1)+"s", n)
def parse_cost(l):
    m=COST_RE.match(l); cost=int(m.group(1)); rest=l[m.end():].strip().lower().lstrip(',').strip()
    quals=[q.strip() for q in re.split(r'[;,]',rest) if q.strip()]
    limited=any(q=='limited' for q in quals)
    reqs=[q for q in quals if q!='limited' and not re.match(r'^\d+ spirit',q)]
    reqstr=", ".join(reqs)
    return (cost, limited, reqstr or None,
            sorted({c for c in CLASSES if c in reqstr}),
            'spellcaster' in reqstr,
            'melee' if 'melee' in reqstr else 'ranged' if 'ranged' in reqstr else 'heavy' if 'heavy' in reqstr else None)

items=[]; cur=1; i=0; pend=[]
while i<len(body):
    l=body[i]; s=l.strip()
    if not s or FURN.match(s): i+=1; continue
    if is_tier(l):
        m=re.search(r'T\s*(\d+)',s)
        if m and TIER_RE.match(s): cur=int(m.group(1))
        pend=[]; i+=1; continue
    if COST_RE.match(l):
        name=clean_name(pend) if pend else "??"
        cost,lim,reqstr,rc,rcast,rw=parse_cost(l); desc=[]; j=i+1
        while j<len(body):
            lj=body[j]; sj=lj.strip()
            if COST_RE.match(lj) or is_tier(lj): break
            if not sj or FURN.match(sj): j+=1; continue
            desc.append(sj); j+=1
        nxt=[]
        if j<len(body) and COST_RE.match(body[j]) and desc:
            nxt=[desc.pop()]
            if desc and re.match(r'(?i)^of the$',nxt[0]): nxt.insert(0,desc.pop())
        pend=nxt
        items.append({"name":name,"tier":cur,"cost":cost,"limited":lim,"requires":reqstr,
                      "reqClass":rc,"reqCaster":rcast,"reqWeapon":rw,
                      "text":re.sub(r'\s+',' '," ".join(desc)).strip()})
        i=j; continue
    pend.append(s); i+=1

for it in items:
    if it['name']=="Spell Storing (level 4)" and it['tier']==4 and "level 5 spell" in it['text']: it['name']="Spell Storing (level 5)"
    if it['name']=="Spellhunter" and it['tier']==3:
        it['name']="Spellhunter (Anticoncentration)"
        it['_sourceQuirk']="PDF names two different upgrades 'Spellhunter' (T2 dmg + T3 concentration); T3 disambiguated"

json.dump(items, open(__import__("os").path.join(__import__("os").path.dirname(__file__) or ".","upgrades.json"),"w"), indent=1, ensure_ascii=False)
print("wrote", len(items), "upgrades | per tier:", dict(sorted(Counter(it['tier'] for it in items).items())))
print("dups:", [n for n,c in Counter(it['name'] for it in items).items() if c>1] or "none")
print("requirements:", sum(1 for it in items if it['requires']), "| limited:", sum(1 for it in items if it['limited']))
