import re, sys, difflib
sys.path.insert(0, '/home/claude/sites/tools')
from sitegen import Site
S = Site('/home/claude/sites/tibbimarket', '/home/claude/sites/tibbimarket.data.json', 'tibbimarket.az', 'agizgenislendirici')
bad = 0
for pid, p in S.P.items():
    for lang in ('az', 'ru'):
        orig = S.rd(S.path(p['slug'], lang))
        rel = re.search(r'<section class="rel">.*?</section>', orig, re.S).group(0)
        tiles = re.search(r'<div class="tiles">.*?</div>(?=</section>)', orig, re.S).group(0)
        out = S.product_page(p, lang, rel, tiles)
        if out != orig:
            bad += 1
            if bad <= 3:
                sm = difflib.SequenceMatcher(None, orig, out, autojunk=False)
                for op, i1, i2, j1, j2 in sm.get_opcodes():
                    if op != 'equal': print(p['slug'], lang, op, repr(orig[max(0,i1-60):i2+20]), '=>', repr(out[max(0,j1-60):j2+20])); break
print('fərqli:', bad, 'cəmi:', 2 * len(S.P))

# kartlar: bölmə səhifələri
bad = 0
for slug, sec in S.S.items():
    for lang in ('az', 'ru'):
        orig = S.rd(S.path(slug, lang))
        for g in sec['groups']:
            if g['id']:
                body = re.search(r'<section class="group" id="%s"><h2>.*?<div class="grid">(.*?)</div></section>' % g['id'], orig, re.S).group(1)
            else:
                body = re.search(r'<div class="grid" style="margin-top:22px">(.*?)</div><section class="block"', orig, re.S).group(1)
            cards = re.findall(r'<article class="card">.*?</article>', body, re.S)
            for c, pid in zip(cards, g['items']):
                tag = re.search(r'<span class="tag">(.*?)</span>', c)
                mine = S.card(S.P[pid], lang, tag.group(1) if tag else '')
                if mine != c:
                    bad += 1
                    if bad < 3: print(slug, lang, '\n', c[:400], '\n', mine[:400])
print('kart fərqi:', bad)

bad = 0
import glob, os
for f in glob.glob('/home/claude/sites/tibbimarket/*.html') + glob.glob('/home/claude/sites/tibbimarket/ru/*.html'):
    o = open(f).read(); m = re.search(r'<div class="tiles">.*?</div>(?=</section>)', o, re.S)
    if not m: continue
    act = re.search(r'<a class="tile" href="(?:\.\./ru/)?([^"]+)\.html" aria-current', m.group(0))
    lang = 'ru' if '/ru/' in f else 'az'
    if S.tiles(act.group(1) if act else None, lang) != m.group(0):
        bad += 1
        if bad < 2: print(f, m.group(0)[:300], '\n', S.tiles(act.group(1) if act else None, lang)[:300])
print('plitə fərqi:', bad)
bad = 0
for slug in S.S:
    for lang in ('az', 'ru'):
        o = S.rd(S.path(slug, lang))
        if S.section_page(slug, lang, o) != o: bad += 1; print('bölmə fərqi', slug, lang)
print('bölmə səhifə fərqi:', bad)

import json
for lang, f in (('az', 'search.json'), ('ru', 'ru/search.json')):
    orig = json.load(open('/home/claude/sites/tibbimarket/' + f))
    bad = 0
    for e in orig:
        pid = int(re.search(r'img/(\d+)', e['i']).group(1))
        mine = S.search_entry(S.P[pid], lang)
        if mine != e:
            bad += 1
            if bad < 3: print(lang, {k: (e[k], mine[k]) for k in e if e[k] != mine[k]})
    print('axtarış fərqi', lang, bad, '| sıra id azalan?', [int(re.search(r'img/(\d+)', e['i']).group(1)) for e in orig][:5])
