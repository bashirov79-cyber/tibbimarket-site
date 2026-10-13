#!/usr/bin/env python3
"""Saytı data.json-dan yeniləyir (tibbimarket.az formatı).
İstifadə: python3 build.py <sayt_qovluğu> <data.json> <domain> <istinad_slug> [changes.json]

changes.json (hamısı istəyə bağlı):
{ "upsert": [ {"id":1, "slug":"...", "sec":"ilk-yardim", "grp":"canta" | null, "w":300, "h":300,
               "n_az","n_ru","d_az","d_ru"  (HTML, saytda olduğu kimi),  "md_az","md_ru","ld_az","ld_ru" (verilməsə yaradılır)} ],
  "remove": [ id, ... ],
  "images": { "id": "<şəkil faylının yolu (webp)>" } }
Yeni məhsul bölmə/qrupa id-yə görə azalan sırada əlavə olunur. Dəyişən məhsulun bölməsi dəyişibsə, köçürülür.
Heç bir dəyişiklik olmadan işə salınsa, saytı olduğu kimi yenidən yazır (yoxlama üçün)."""
import html, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sitegen import Site

root, data_path, domain, ref = sys.argv[1:5]
changes = json.load(open(sys.argv[5], encoding='utf-8')) if len(sys.argv) > 5 else {}
S = Site(root, data_path, domain, ref)

def plain(h): return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))).strip()
def cut(s, n):
    if len(s) <= n: return s
    return s[:n].rsplit(' ', 1)[0].rstrip(' ,.;:') + '…'

# ---------- 1. məlumatı dəyiş ----------
removed = set(changes.get('remove', []))
touched = set()
for pid in removed:
    p = S.P.pop(pid, None)
    for sec in S.S.values():
        for g in sec['groups']:
            if pid in g['items']: g['items'].remove(pid)
    if p:
        for lang in ('az', 'ru'):
            f = os.path.join(root, S.path(p['slug'], lang))
            if os.path.exists(f): os.remove(f)
for u in changes.get('upsert', []):
    pid = u['id']; old = S.P.get(pid, {})
    p = {**old, **u}
    for lang in ('az', 'ru'):
        pl = plain(p['d_' + lang])
        p.setdefault('ld_' + lang, cut(pl, 300))
        if 'md_' + lang not in u and ('d_' + lang in u or 'n_' + lang in u or not old):
            n = html.unescape(p['n_' + lang])
            p['md_' + lang] = html.escape(
                (f'{n} sifarişi {domain}-da. ' + cut(pl, max(20, 150 - len(n))) + ' Qiymət və mövcudluq WhatsApp və ya zənglə, Bakı.') if lang == 'az' else
                (f'Заказать {n} на {domain}. ' + cut(pl, max(20, 150 - len(n))) + ' Цена и наличие — в WhatsApp или по телефону, Баку.'), quote=True)
    if old and (old['sec'], old['grp']) != (p['sec'], p['grp']):
        for g in S.S[old['sec']]['groups']:
            if pid in g['items'] and g['id'] == old['grp']: g['items'].remove(pid)
    grp = next(g for g in S.S[p['sec']]['groups'] if g['id'] == p['grp'])
    if pid not in grp['items']:
        grp['items'].append(pid); grp['items'].sort(reverse=True)
    S.P[pid] = p; touched.add(pid)
    if str(pid) in changes.get('images', {}):
        shutil.copy(changes['images'][str(pid)], os.path.join(root, 'img', f'{pid}.webp'))

# ---------- 2. məhsul səhifələri ----------
def rel_ids(p, current):
    ids = [i for i in current if i in S.P and i != p['id']]
    if len(ids) < 4:
        grp = next(g for g in S.S[p['sec']]['groups'] if g['id'] == p['grp'])
        cand = sorted((i for i in grp['items'] if i != p['id'] and i not in ids), key=lambda i: abs(i - p['id']))
        ids += cand[:4 - len(ids)]
    return ids[:4]

def rel_block(p, lang, ids, head):
    tagged = [S.card(S.P[i], lang, S.tag_for(S.P[i], lang) if S.P[i]['sec'] == p['sec'] else S.tag_for(S.P[i], lang)) for i in ids]
    return f'<section class="rel"><h2>{head}</h2><div class="grid">' + ''.join(tagged) + '</div></section>'

REL_HEAD = {'az': 'Oxşar məhsullar', 'ru': 'Похожие товары'}
for pid, p in S.P.items():
    for lang in ('az', 'ru'):
        f = os.path.join(root, S.path(p['slug'], lang))
        old = open(f, encoding='utf-8').read() if os.path.exists(f) else None
        cur = [int(x) for x in re.findall(r'data-add="(\d+)"', re.search(r'<section class="rel">.*?</section>', old, re.S).group(0))] if old else []
        ids = rel_ids(p, cur)
        if old and ids == cur and pid not in touched and not (set(cur) & touched):
            rel = re.search(r'<section class="rel">.*?</section>', old, re.S).group(0)      # dəyişməyib — olduğu kimi
        else:
            # kartların etiketi: mövcud səhifədəki kimi qrup/bölmə adı
            rel = f'<section class="rel"><h2>{REL_HEAD[lang]}</h2><div class="grid">' + ''.join(S.card(S.P[i], lang, S.tag_for(S.P[i], lang)) for i in ids) + '</div></section>'
        out = S.product_page(p, lang, rel, S.tiles(p['sec'], lang))
        if out != old: open(f, 'w', encoding='utf-8').write(out)

# ---------- 3. bölmə səhifələri, plitələr, ana səhifə ----------
def retile(s):
    def rep(m):
        slug = m.group(2)
        return m.group(1) + re.sub(r'\d+', str(S.count(slug)), m.group(3), count=1) if slug in S.S else m.group(0)
    return re.sub(r'(<a class="tile" href="(?:/|\.\./ru/|/ru/)?([^"]+)\.html"(?:(?!</a>).)*?<small>)([^<]*)', rep, s, flags=re.S)

total = len(S.P)
for dirpath in (root, os.path.join(root, 'ru')):
    lang = 'az' if dirpath == root else 'ru'
    for f in os.listdir(dirpath):
        if not f.endswith('.html'): continue
        fp = os.path.join(dirpath, f); s = open(fp, encoding='utf-8').read(); o = s
        slug = f[:-5]
        if slug in S.S: s = S.section_page(slug, lang, s)
        elif '<div class="prod">' not in s: s = retile(s)
        if slug == 'index':
            s = re.sub(r'<li>\d+ (məhsul|товар\w*)</li>', lambda m: f'<li>{total} {m.group(1)}</li>', s, count=1)
        if s != o: open(fp, 'w', encoding='utf-8').write(s)

# ---------- 4. axtarış, sitemap, llms.txt ----------
order = sorted(S.P, reverse=True)
for lang, f in (('az', 'search.json'), ('ru', 'ru/search.json')):
    json.dump([S.search_entry(S.P[i], lang) for i in order], open(os.path.join(root, f), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
smp = os.path.join(root, 'sitemap.xml')
prev = re.findall(r'<loc>([^<]+)</loc>', open(smp, encoding='utf-8').read())
valid = {f'https://{domain}/{pre}{x}' for pre in ('', 'ru/') for x in [''] + [f'{s}.html' for s in S.d['sections_order']] + [f'{S.P[i]["slug"]}.html' for i in S.P]}
locs = [u for u in prev if u in valid]
for pre in ('', 'ru/'):
    new = [f'https://{domain}/{pre}{S.P[i]["slug"]}.html' for i in order if f'https://{domain}/{pre}{S.P[i]["slug"]}.html' not in locs]
    pos = (locs.index(f'https://{domain}/ru/') if pre == '' else len(locs))
    locs[pos:pos] = new
sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{u}</loc></url>' for u in locs) + '</urlset>\n'
open(smp, 'w', encoding='utf-8').write(sm)
lp = os.path.join(root, 'llms.txt'); l = open(lp, encoding='utf-8').read()
open(lp, 'w', encoding='utf-8').write(re.sub(r'Məhsul sayı: \d+', f'Məhsul sayı: {total}', l))

# ---------- 5. məlumatı saxla ----------
S.d['products'] = {str(k): v for k, v in S.P.items()}
json.dump(S.d, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'OK: {total} məhsul; dəyişən: {sorted(touched)}; silinən: {sorted(removed)}')
