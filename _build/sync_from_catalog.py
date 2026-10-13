#!/usr/bin/env python3
"""Kataloqdan (medishop-kataloq/catalog.json) sayta dəyişiklikləri hazırlayır — tibbimarket.az və tibbiavadanliq.az üçün.

  python3 _build/sync_from_catalog.py <catalog_repo> report              → nə dəyişib + yeni məhsullar üçün yerləşdirmə təklifi (JSON)
  python3 _build/sync_from_catalog.py <catalog_repo> make [placement.json] → _build/changes.json yaradır və data.json-da "src" izini yeniləyir
  python3 _build/sync_from_catalog.py <catalog_repo> init                → indiki vəziyyəti baza kimi qeyd edir (bir dəfəlik)

placement.json (yalnız yeni məhsullar üçün, Ruslanın təsdiqindən sonra):
  { "<id>": {"sec": "ilk-yardim", "grp": "canta"|null, "fits": ["tibb-menteqesi", ...], "also": [["tibbi-mebel","xerek"]]} }
  "fits" yalnız tibbiavadanliq.az üçündür; "also" istəyə bağlıdır.
Repo kökündən işə salınır. Sonra: build (README-də) → yoxlama → commit/push → Deploy HEAD Commit."""
import collections, hashlib, html, json, os, re, shutil, sys

cat_repo, mode = sys.argv[1], sys.argv[2]
DATA = '_build/data.json'
d = json.load(open(DATA, encoding='utf-8'))
C = {p['id']: p for p in json.load(open(os.path.join(cat_repo, 'catalog.json'), encoding='utf-8'))['products']}
P = {int(k): v for k, v in d['products'].items()}
has_inst = 'insts' in d
TR = str.maketrans({'ə': 'e', 'ı': 'i', 'ş': 's', 'ç': 'c', 'ğ': 'g', 'ö': 'o', 'ü': 'u', 'Ə': 'e', 'I': 'i', 'İ': 'i', 'Ş': 's', 'Ç': 'c', 'Ğ': 'g', 'Ö': 'o', 'Ü': 'u'})

def src(p): return hashlib.sha1(json.dumps([p[k] for k in ('n', 'nr', 'd', 'dr', 'c', 'v')], ensure_ascii=False).encode()).hexdigest()[:10]
def clean(h): return re.sub(r'^<h3>.*?</h3>(?:<br>)?', '', h.strip())
def slug(n):
    s = re.sub(r'[^a-z0-9]+', '-', html.unescape(n).translate(TR).lower()).strip('-')[:64].rstrip('-')
    used = {p['slug'] for p in P.values()}; base, i = s, 2
    while s in used: s = f'{base}-{i}'; i += 1
    return s

if mode == 'init':
    d['src'] = {str(i): src(C[i]) for i in P if i in C}
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(print(f'baza qeyd olundu: {len(d["src"])} məhsul'))

S = d.get('src', {})
new = sorted(i for i in C if i not in P)
removed = sorted(i for i in P if i not in C)
changed = sorted(i for i in P if i in C and S.get(str(i)) != src(C[i]))

def what(i):
    c, p, f = C[i], P[i], []
    if c['n'] != html.unescape(p['n_az']) and c['n'] != p['n_az']: f.append('ad AZ')
    if c['nr'] != html.unescape(p['n_ru']) and c['nr'] != p['n_ru']: f.append('ad RU')
    if clean(c['d']) != p['d_az']: f.append('təsvir AZ')
    if clean(c['dr']) != p['d_ru']: f.append('təsvir RU')
    if not filecmp(i): f.append('şəkil')
    return f

def filecmp(i):
    a, b = os.path.join(cat_repo, 'img', f'{i}.webp'), os.path.join('img', f'{i}.webp')
    return os.path.exists(a) and os.path.exists(b) and open(a, 'rb').read() == open(b, 'rb').read()

def propose(i):
    """Eyni kateqoriyalı mövcud məhsullara görə ən çox rast gələn yerləşdirmələr."""
    cs = set(C[i]['c']); score = collections.Counter(); fits = collections.Counter(); peers = 0
    for j, p in P.items():
        if j not in C: continue
        ov = len(cs & set(C[j]['c']))
        if not ov: continue
        w = ov * 10 + (ov == len(cs) == len(C[j]['c'])) * 100
        score[(p['sec'], p['grp'])] += w
        if has_inst and ov == len(cs): fits[tuple(p.get('fits', []))] += 1; peers += 1
    groups = {s: [f"{g['id']}={g['n_az']}" for g in d['sections'][s]['groups'] if g['id']] for s in d['sections_order']}
    out = {'id': i, 'n': C[i]['n'], 'kateqoriyalar': C[i]['c'], 'namizədlər': [[s, g] for (s, g), _ in score.most_common(4)]}
    if has_inst: out['fits_namizəd'] = [list(f) for f, _ in fits.most_common(2)]
    return out, groups

if mode == 'report':
    groups = None; props = []
    for i in new:
        o, groups = propose(i); props.append(o)
    print(json.dumps({'yeni': props, 'dəyişən': [{'id': i, 'n': C[i]['n'], 'nə': what(i)} for i in changed],
                      'silinən': [{'id': i, 'n': P[i]['n_az']} for i in removed],
                      'bölmələr': groups if new else None,
                      'müəssisələr': d.get('insts_order') if new and has_inst else None}, ensure_ascii=False, indent=0))
    sys.exit()

# ---- make ----
pl = json.load(open(sys.argv[3], encoding='utf-8')) if len(sys.argv) > 3 else {}
miss = [i for i in new if str(i) not in pl]
if miss: sys.exit(f'XƏTA: yeni məhsullar üçün yerləşdirmə yoxdur: {miss}')
W, H = collections.Counter((p['w'], p['h']) for p in P.values()).most_common(1)[0][0]   # saytın sabit ölçüsü
up, images = [], {}
for i in changed:
    c, p, u = C[i], P[i], {'id': i}
    for k_c, k_s, fn in (('n', 'n_az', None), ('nr', 'n_ru', None), ('d', 'd_az', clean), ('dr', 'd_ru', clean)):
        v = fn(c[k_c]) if fn else c[k_c]
        if v != p[k_s] and not (fn is None and html.unescape(p[k_s]) == v): u[k_s] = html.escape(v, quote=False) if fn is None else v
    if not filecmp(i): images[str(i)] = os.path.abspath(os.path.join(cat_repo, 'img', f'{i}.webp'))
    if len(u) > 1: up.append(u)
for i in new:
    c, x = C[i], pl[str(i)]
    u = {'id': i, 'slug': slug(c['n']), 'sec': x['sec'], 'grp': x.get('grp'), 'w': W, 'h': H,
         'n_az': html.escape(c['n'], quote=False), 'n_ru': html.escape(c['nr'], quote=False), 'd_az': clean(c['d']), 'd_ru': clean(c['dr'])}
    if has_inst: u['fits'] = x.get('fits', [])
    if x.get('also'): u['also'] = x['also']
    if has_inst is False and x.get('also'): u.pop('also')
    up.append(u); images[str(i)] = os.path.abspath(os.path.join(cat_repo, 'img', f'{i}.webp'))
    P[i] = {'slug': u['slug']}   # slug toqquşmasın
ch = {'upsert': up, 'remove': removed, 'images': images}
json.dump(ch, open('_build/changes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# silinən səhifələr serverdən də silinsin
gone = [f'{pre}{d["products"][str(i)]["slug"]}.html' for i in removed for pre in ('', 'ru/')] + \
       [f'{dd}/{i}.webp' for i in removed for dd in ('img', 't') if os.path.exists(f'{dd}/{i}.webp')]
if gone:
    keep = {f'{pre}{u["slug"]}.html' for u in up if 'slug' in u for pre in ('', 'ru/')} | {f'{dd}/{i}.webp' for i in new for dd in ('img', 't')}
    old = [l for l in open('.deploy-remove.txt', encoding='utf-8').read().split('\n') if l and l not in keep]
    open('.deploy-remove.txt', 'w', encoding='utf-8').write('\n'.join(dict.fromkeys(old + gone)) + '\n')
d['src'] = {**S, **{str(i): src(C[i]) for i in changed + new}}
for i in removed: d['src'].pop(str(i), None)
json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'changes.json: {len(new)} yeni, {len(up) - len(new)} dəyişən, {len(removed)} silinən, {len(images)} şəkil')
