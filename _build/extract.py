#!/usr/bin/env python3
"""Mövcud statik saytdan (tibbimarket.az formatı) məlumat çıxarır: data.json.
İstifadə: python3 extract.py <sayt_qovluğu>"""
import html, json, os, re, sys

ROOT = sys.argv[1]
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def one(rx, s, flags=re.S):
    m = re.search(rx, s, flags); return m.group(1) if m else None

pages = sorted(f for f in os.listdir(ROOT) if f.endswith('.html'))
products, sections = {}, {}
for f in pages:
    s = rd(f)
    if '<div class="prod">' in s:
        p = {'slug': f[:-5]}
        p['id'] = int(one(r'<div class="plate"><img src="img/(\d+)\.webp"', s))
        p['w'], p['h'] = map(int, re.search(r'<div class="plate"><img src="img/\d+\.webp" alt="[^"]*" width="(\d+)" height="(\d+)"', s).groups())
        p['sec'] = one(r'<ol class="crumbs"><li><a href="\./">[^<]*</a></li><li><a href="([^"]+)\.html">', s)
        p['grp'] = one(r'<a class="where" href="[^"#]+#([^"]+)">', s)
        for lang, src in (('az', s), ('ru', rd('ru/' + f))):
            p['n_' + lang] = one(r'<h1>(.*?)</h1>', src)
            p['md_' + lang] = one(r'<meta name="description" content="([^"]*)">', src)
            p['d_' + lang] = one(r'<section class="desc"><h2>[^<]*</h2>(.*?)</section>', src)
            p['ld_' + lang] = json.loads(one(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "Product".*?)</script>', src))['description']
        products[p['id']] = p
    elif '<h1 class="ph1">' in s:
        sec = {'slug': f[:-5]}
        for lang, src in (('az', s), ('ru', rd('ru/' + f))):
            sec['n_' + lang] = one(r'<h1 class="ph1">(.*?)</h1>', src)
            sec['intro_' + lang] = one(r'<p class="intro">(.*?)</p>', src)
            sec['md_' + lang] = one(r'<meta name="description" content="([^"]*)">', src)
            sec['title_' + lang] = one(r'<title>(.*?)</title>', src)
            groups = []
            for gid, gname, body in re.findall(r'<section class="group" id="([^"]+)"><h2>(.*?)<span>\d+</span></h2><div class="grid">(.*?)</div></section>', src, re.S):
                ids = [int(x) for x in re.findall(r'<article class="card"><a class="ph" href="[^"]+" tabindex="-1" aria-hidden="true"><img src="(?:\.\./)?img/(\d+)\.webp"', body)]
                groups.append({'id': gid, 'n_' + lang: gname, 'items': ids})
            if not groups:   # qrupsuz bölmə: tək grid
                body = one(r'<div class="grid" style="margin-top:22px">(.*?)</div><section class="block"', src)
                ids = [int(x) for x in re.findall(r'<article class="card"><a class="ph" href="[^"]+" tabindex="-1" aria-hidden="true"><img src="(?:\.\./)?img/(\d+)\.webp"', body)]
                groups = [{'id': None, 'n_' + lang: None, 'items': ids}]
            if lang == 'az': sec['groups'] = groups
            else:
                for g, gr in zip(sec['groups'], groups):
                    assert g['id'] == gr['id'] and g['items'] == gr['items'], (f, g['id'])
                    g['n_ru'] = gr['n_ru']
        sections[sec['slug']] = sec

# bölmələrin sırası (tiles)
s = rd('index.html')
order = re.findall(r'<a class="tile" href="([^"]+)\.html"', s)
json.dump({'sections_order': order, 'sections': sections, 'products': products},
          open(os.path.join(ROOT, '..', os.path.basename(ROOT.rstrip('/')) + '.data.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(products), 'məhsul;', len(sections), 'bölmə;', 'sıra:', order)
