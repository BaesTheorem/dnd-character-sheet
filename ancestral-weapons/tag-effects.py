#!/usr/bin/env python3
"""Read upgrades.json -> emit (1) aw-upgrades-mech.json (mechanics + auto-apply effect tags,
destined for app JS, non-copyrightable) and (2) aw-text.json (copyrighted descriptions, for the
gitignored #aw-data bake). Effect tags are derived by matching the rules text; everything not
matched is reminder-only (fx:{}). Re-run after extract.py."""
import json, re, os
here=os.path.dirname(__file__) or "."
items=json.load(open(os.path.join(here,"upgrades.json")))
DT={"acid","cold","fire","force","lightning","necrotic","poison","psychic","radiant","thunder","slashing","piercing","bludgeoning"}
def effects(it):
    t=it["text"]; fx={}
    m=re.search(r'\+(\d+)\s+bonus to attack and damage',t,re.I)
    if m: fx["atkDmg"]=int(m.group(1))
    m=re.search(r'\+(\d+)\s+bonus to spell attack',t,re.I)
    if m: fx["spellAtk"]=int(m.group(1))
    m=re.search(r'\+(\d+)\s+bonus to AC',t,re.I)
    if m: fx["ac"]=int(m.group(1))
    # extra damage on this weapon's attacks: "additional NdM TYPE damage" or "deal 2d6 additional damage ... of this type"
    m=re.search(r'additional\s+(\d*d\d+)\s+([a-z]+)\s+damage',t,re.I)
    if m and m.group(2).lower() in DT: fx["extraDmg"]={"dice":m.group(1),"type":m.group(2).lower()}
    elif re.search(r'(\d*d\d+)\s+additional damage',t,re.I):
        d=re.search(r'(\d*d\d+)\s+additional damage',t,re.I).group(1)
        fx["extraDmg"]={"dice":d,"type":"(chosen)" if "choose" in t.lower() else ""}
    elif re.search(r'additional\s+(\d*d\d+)\s+damage',t,re.I):
        fx["extraDmg"]={"dice":re.search(r'additional\s+(\d*d\d+)\s+damage',t,re.I).group(1),"type":"(chosen)" if "choose a damage type" in t.lower() else ""}
    m=re.search(r'additional level (\d+) spell slot',t,re.I)
    if m: fx["slot"]=int(m.group(1))
    if re.search(r'\bdarkvision\b',t,re.I): fx["darkvision"]=60
    if re.search(r'flying speed',t,re.I): fx["fly"]=True
    m=re.search(r'speed (?:is )?increased by (\d+)',t,re.I)
    if m: fx["speed"]=int(m.group(1))
    m=re.search(r'proficiency in (\d+|a|an|two|one)',t,re.I)
    if m: fx["prof"]={"1":1,"2":2,"a":1,"an":1,"one":1,"two":2}.get(m.group(1).lower(),1)
    m=re.search(r'resistance to ([a-z]+) damage',t,re.I)
    if m and m.group(1).lower() in DT: fx["resist"]=m.group(1).lower()
    if re.search(r'counts as a spellcasting focus',t,re.I): fx["focus"]=True
    return fx
mech=[]; text={}
for it in items:
    fx=effects(it)
    mech.append({"n":it["name"],"t":it["tier"],"c":it["cost"],"lim":it["limited"],
                 "req":it["requires"],"rc":it["reqClass"],"rcast":it["reqCaster"],"rw":it["reqWeapon"],
                 **({"fx":fx} if fx else {})})
    text[it["name"]]=it["text"]
json.dump(mech,open(os.path.join(here,"aw-upgrades-mech.json"),"w"),ensure_ascii=False,separators=(",",":"))
json.dump(text,open(os.path.join(here,"aw-text.json"),"w"),ensure_ascii=False,separators=(",",":"))
auto=[m for m in mech if m.get("fx")]
print(f"{len(mech)} upgrades; {len(auto)} have auto-apply effects")
from collections import Counter
print("effect coverage:",dict(Counter(k for m in auto for k in m["fx"])))
print("\nAuto-applying upgrades:")
for m in auto: print(f"  {m['n']}: {m['fx']}")
