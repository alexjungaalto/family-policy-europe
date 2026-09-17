#!/usr/bin/env python3
"""Merge extension files (labourtax / workrights policies) into docs/data/policies.json.

Each <ISO2>.json in the given dir has: headline{labourtax,workrights}, note_add,
recat[{name,cat}], policies[{rank,cat,...}]. New policies are inserted at their
`rank` position into the country's existing ranked list (others shift down), then
everything is renumbered 1..n. Idempotent: a policy with the same name is replaced.

Usage: python3 merge_ext.py <dir>
"""
import json, sys, glob, os

CATS = {'cash','leave','childcare','tax','housing','healthedu','labourtax','workrights'}
out = 'docs/data/policies.json'
data = json.load(open(out, encoding='utf-8'))
bad = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.json'))):
    iso = os.path.basename(f)[:-5].upper()
    if iso not in data:
        print(f'✗ {iso}: no base entry'); bad += 1; continue
    try:
        e = json.load(open(f, encoding='utf-8'))
    except Exception as ex:
        print(f'✗ {iso}: invalid JSON ({ex})'); bad += 1; continue
    d = data[iso]
    probs = []
    # headline
    for k in ('labourtax', 'workrights'):
        v = (e.get('headline') or {}).get(k)
        if v: d.setdefault('headline', {})[k] = v
        else: probs.append(f'no headline.{k}')
    # note
    na = (e.get('note_add') or '').strip()
    if na and na not in d.get('note', ''):
        d['note'] = (d.get('note', '').rstrip() + ' ' + na).strip()
    # recat
    for r in e.get('recat') or []:
        hit = [p for p in d['policies'] if p.get('name') == r.get('name')]
        if hit and r.get('cat') in CATS: hit[0]['cat'] = r['cat']
        else: probs.append(f"recat miss: {r.get('name')!r}")
    # policies: drop same-name duplicates, then insert by rank
    new = e.get('policies') or []
    if not new: probs.append('no new policies')
    cats = {p.get('cat') for p in new}
    if not {'labourtax','workrights'} <= (cats | {p.get('cat') for p in d['policies']}):
        probs.append(f'missing a new category (got {sorted(cats)})')
    names = {p['name'] for p in new}
    base = sorted([p for p in d['policies'] if p.get('name') not in names], key=lambda p: p.get('rank', 99))
    for p in sorted(new, key=lambda p: p.get('rank', 99)):
        if p.get('cat') not in CATS: probs.append(f"bad cat {p.get('cat')!r}")
        for k in ('name','what','value','url'):
            if not p.get(k): probs.append(f"{p.get('name')}: missing {k}")
        pos = max(0, min(len(base), int(p.get('rank', 99)) - 1))
        base.insert(pos, p)
    for i, p in enumerate(base, 1): p['rank'] = i
    d['policies'] = base
    if e.get('checked'): d['checked'] = max(d.get('checked',''), e['checked'])
    if probs: print(f'⚠ {iso}: ' + '; '.join(probs))
    print(f'✓ {iso}: +{len(new)} → {len(base)} policies')
json.dump(dict(sorted(data.items())), open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(data)} countries → {out}')
sys.exit(1 if bad else 0)
