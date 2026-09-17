#!/usr/bin/env python3
"""Merge per-country research JSON files (one <ISO2>.json each) into
site/data/policies.json, keyed by ISO2. Validates the schema lightly.

Usage: python3 merge_research.py <dir-with-ISO2.json-files>
"""
import json, sys, glob, os

CATS = {'cash','leave','childcare','tax','housing','healthedu'}
src = sys.argv[1]
out = 'site/data/policies.json'
data = json.load(open(out)) if os.path.exists(out) else {}
bad = 0
for f in sorted(glob.glob(os.path.join(src, '*.json'))):
    iso = os.path.basename(f)[:-5].upper()
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print(f'✗ {iso}: invalid JSON ({e})'); bad += 1; continue
    probs = []
    if d.get('iso','').upper() != iso: probs.append('iso mismatch')
    pols = d.get('policies') or []
    if not 3 <= len(pols) <= 5: probs.append(f'{len(pols)} policies (want 3–5)')
    for p in pols:
        if p.get('cat') not in CATS: probs.append(f"bad cat {p.get('cat')!r}")
        for k in ('name','what','value','url'):
            if not p.get(k): probs.append(f"policy {p.get('rank')} missing {k}")
    for k in ('country','note','headline'):
        if not d.get(k): probs.append(f'missing {k}')
    if probs:
        print(f'⚠ {iso}: ' + '; '.join(probs))
    d['iso'] = iso
    data[iso] = d
    print(f'✓ {iso} {d.get("country")}: {len(pols)} policies')
json.dump(dict(sorted(data.items())), open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(data)} countries → {out}')
sys.exit(1 if bad else 0)
