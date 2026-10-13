#!/usr/bin/env python3
"""tibbimarket.az formatlı statik sayt üçün səhifə generatoru (məhsul səhifələri, kartlar, bölmə plitələri).
Şablonlar saytın öz səhifələrindən avtomatik götürülür, ona görə dizayn dəyişmir."""
import html, json, os, re, urllib.parse

class Site:
    def __init__(self, root, data_path, domain, ref_slug):
        self.root, self.domain = root, domain
        self.d = json.load(open(data_path, encoding='utf-8'))
        self.P = {int(k): v for k, v in self.d['products'].items()}
        self.S = self.d['sections']
        self.ref = self.P[next(i for i, p in self.P.items() if p['slug'] == ref_slug)]
        self.tpl = {lang: self._tokenize(lang) for lang in ('az', 'ru')}
        self.card_tpl = {lang: self._card_tpl(lang) for lang in ('az', 'ru')}

    def rd(self, rel): return open(os.path.join(self.root, rel), encoding='utf-8').read()
    def path(self, slug, lang): return f'{slug}.html' if lang == 'az' else f'ru/{slug}.html'

    # ---------- şablonlar ----------
    def _tokenize(self, lang):
        p, t = self.ref, self.rd(self.path(self.ref['slug'], lang))
        sec = self.S[p['sec']]
        def sub(rx, rep, count=1):
            nonlocal t
            t, n = re.subn(rx, lambda m: rep, t, count=count, flags=re.S)
            assert n, rx
        sub(r'<section class="rel">.*?</section>', '{{REL}}')
        sub(r'<div class="tiles">.*?</div>(?=</section>)', '{{TILES}}')
        t = re.sub(r'(<section class="desc"><h2>[^<]*</h2>).*?(</section>)', r'\1{{DESC}}\2', t, count=1, flags=re.S)
        sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "Product".*?</script>', '{{LDP}}')
        sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "BreadcrumbList".*?</script>', '{{LDB}}')
        sub(r'<title>.*?</title>', '<title>{{TITLE}}</title>')
        sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="{{TITLE}}">')
        t = t.replace(f'content="{p["md_" + lang]}"', 'content="{{MD}}"')
        t = re.sub(r'(wa\.me/994702720302\?text=)[^"]*(" target="_blank" rel="noopener"><svg[^>]*>.*?</svg>(?:WhatsApp-la soruş|Спросить в WhatsApp))', r'\1{{WA}}\2', t, count=1, flags=re.S)
        t = t.replace(f'{p["sec"]}.html#{p["grp"]}">{self._g(p, lang)}</a>', '{{WHERE}}')
        t = t.replace(f'{p["sec"]}.html">{sec["n_" + lang]}</a></li><li aria-current="page">', '{{SEC}}.html">{{SECN}}</a></li><li aria-current="page">')
        t = t.replace(f'img/{p["id"]}.webp" alt="{p["n_" + lang]}" width="{p["w"]}" height="{p["h"]}"', 'img/{{ID}}.webp" alt="{{N}}" width="{{W}}" height="{{H}}"')
        t = t.replace(f'img/{p["id"]}.webp', 'img/{{ID}}.webp').replace(f'data-add="{p["id"]}" data-name="{p["n_" + lang]}"', 'data-add="{{ID}}" data-name="{{N}}"')
        t = t.replace(f'<h1>{p["n_" + lang]}</h1>', '<h1>{{N}}</h1>').replace(f'aria-current="page">{p["n_" + lang]}</li>', 'aria-current="page">{{N}}</li>')
        t = t.replace(f'{p["slug"]}.html', '{{SLUG}}.html')
        for v in (p['n_' + lang], str(p['id']), p['slug']):
            assert v not in t, ('şablonda qalıb', lang, v)
        return t

    def _g(self, p, lang):
        if not p['grp']: return None
        return next(g['n_' + lang] for g in self.S[p['sec']]['groups'] if g['id'] == p['grp'])

    def _card_tpl(self, lang):
        s = self.rd(self.path(self.ref['slug'], lang))
        m = re.search(r'<section class="rel"><h2>[^<]*</h2><div class="grid">(<article class="card">.*?</article>)', s, re.S)
        c = m.group(1)
        q = self.P[int(re.search(r'data-add="(\d+)"', c).group(1))]
        tag = re.search(r'<span class="tag">(.*?)</span>', c).group(1)
        c = c.replace(f'<span class="tag">{tag}</span>', '<span class="tag">{{TAG}}</span>')
        c = c.replace(f'img/{q["id"]}.webp" alt="" width="{q["w"]}" height="{q["h"]}"', 'img/{{ID}}.webp" alt="" width="{{W}}" height="{{H}}"')
        c = c.replace(f'data-add="{q["id"]}" data-name="{q["n_" + lang]}"', 'data-add="{{ID}}" data-name="{{N}}"')
        c = c.replace(f'>{q["n_" + lang]}</a></h3>', '>{{N}}</a></h3>').replace(f'{q["slug"]}.html', '{{SLUG}}.html')
        assert str(q['id']) not in c and q['slug'] not in c
        return c

    @staticmethod
    def fill(t, **kw):
        for k, v in kw.items(): t = t.replace('{{' + k + '}}', str(v))
        assert '{{' not in t, re.findall(r'\{\{\w+\}\}', t)
        return t

    # ---------- hissələr ----------
    def card(self, p, lang, tag):
        return self.fill(self.card_tpl[lang], SLUG=p['slug'], ID=p['id'], W=p['w'], H=p['h'], N=p['n_' + lang], TAG=tag)

    def tag_for(self, p, lang):
        """Kartdakı etiket: qrup adı, qrup yoxdursa bölmə adı."""
        return self._g(p, lang) or self.S[p['sec']]['n_' + lang]

    def wa(self, p, lang):
        n = html.unescape(p['n_' + lang])
        msg = (f'Salam! «{n}» barədə qiymət və məlumat almaq istəyirəm. ({self.domain})' if lang == 'az'
               else f'Здравствуйте! Интересует «{n}»: цена и подробности. ({self.domain})')
        return urllib.parse.quote(msg, safe='/')

    def ld_product(self, p, lang):
        base = f'https://{self.domain}/' + ('' if lang == 'az' else 'ru/')
        o = {"@context": "https://schema.org", "@type": "Product", "name": html.unescape(p['n_' + lang]), "description": p['ld_' + lang],
             "image": f'https://{self.domain}/img/{p["id"]}.webp', "category": html.unescape(self.S[p['sec']]['n_' + lang]), "url": base + f'{p["slug"]}.html'}
        return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False) + '</script>'

    def ld_crumbs(self, p, lang):
        base = f'https://{self.domain}/' + ('' if lang == 'az' else 'ru/')
        home = 'Ana səhifə' if lang == 'az' else 'Главная'
        items = [(home, base), (html.unescape(self.S[p['sec']]['n_' + lang]), base + f'{p["sec"]}.html'), (html.unescape(p['n_' + lang]), base + f'{p["slug"]}.html')]
        o = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}
        return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False) + '</script>'

    def where(self, p, lang):
        if p['grp']: return f'{p["sec"]}.html#{p["grp"]}">{self._g(p, lang)}</a>'
        return f'{p["sec"]}.html">{self.S[p["sec"]]["n_" + lang]}</a>'

    def title(self, p, lang):
        return f'{p["n_" + lang]} — ' + ('qiymət və sifariş' if lang == 'az' else 'цена и заказ') + f' | {self.domain}'

    def product_page(self, p, lang, rel_html, tiles_html):
        t = self.tpl[lang]
        return self.fill(t, REL=rel_html, TILES=tiles_html, DESC=p['d_' + lang], LDP=self.ld_product(p, lang), LDB=self.ld_crumbs(p, lang),
                         TITLE=self.title(p, lang), MD=p['md_' + lang], WA=self.wa(p, lang), WHERE=self.where(p, lang),
                         SEC=p['sec'], SECN=self.S[p['sec']]['n_' + lang], ID=p['id'], W=p['w'], H=p['h'], N=p['n_' + lang], SLUG=p['slug'])

    # ---------- bölmə plitələri (hər səhifənin altında) ----------
    def count(self, slug):
        return sum(len(g['items']) for g in self.S[slug]['groups'])

    def tiles(self, active, lang):
        idx = self.rd('index.html' if lang == 'az' else 'ru/index.html')
        t = re.search(r'<div class="tiles">.*?</div>(?=</section>)', idx, re.S).group(0)
        word = 'məhsul' if lang == 'az' else None
        def rep(m):
            slug = m.group(2)
            cur = ' aria-current="page"' if slug == active else ''
            small = re.sub(r'\d+', str(self.count(slug)), m.group(4), count=1)
            return f'{m.group(1)}{cur}{m.group(3)}{small}'
        return re.sub(r'(<a class="tile" href="(?:\.\./ru/)?([^"]+)\.html")((?:(?!</a>).)*?<small>)([^<]*)', rep, t, flags=re.S)

    # ---------- bölmə səhifəsi: qrupların kartları və saylar ----------
    def section_page(self, slug, lang, orig):
        sec, s = self.S[slug], orig
        total = self.count(slug)
        for g in sec['groups']:
            tag = g['n_' + lang] if g['id'] else sec['n_' + lang]
            cards = ''.join(self.card(self.P[i], lang, tag) for i in g['items'])
            if g['id']:
                s = re.sub(r'(<section class="group" id="%s"><h2>.*?<span>)\d+(</span></h2><div class="grid">).*?(</div></section>)' % g['id'],
                           lambda m: f'{m.group(1)}{len(g["items"])}{m.group(2)}{cards}{m.group(3)}', s, count=1, flags=re.S)
                s = re.sub(r'(<a href="#%s">[^<]*<span>)\d+(</span>)' % g['id'], lambda m: f'{m.group(1)}{len(g["items"])}{m.group(2)}', s, count=1)
            else:
                s = re.sub(r'(<div class="grid" style="margin-top:22px">).*?(</div><section class="block")', lambda m: m.group(1) + cards + m.group(2), s, count=1, flags=re.S)
        s = re.sub(r'(<p class="intro">.*?)\d+( (?:məhsul|товар\w*)\.</p>)', lambda m: f'{m.group(1)}{total}{m.group(2)}', s, count=1, flags=re.S)
        s = re.sub(r'<div class="tiles">.*?</div>(?=</section>)', lambda m: self.tiles(slug, lang), s, count=1, flags=re.S)
        return s

    # ---------- axtarış, sitemap ----------
    TR = str.maketrans({'ə': 'e', 'ı': 'i', 'ş': 's', 'ç': 'c', 'ğ': 'g', 'ö': 'o', 'ü': 'u', 'Ə': 'e', 'I': 'i', 'İ': 'i', 'Ş': 's', 'Ç': 'c', 'Ğ': 'g', 'Ö': 'o', 'Ü': 'u'})
    def norm(self, s): return html.unescape(s).translate(self.TR).lower()
    def rnorm(self, s): return html.unescape(s).lower().replace('ё', 'е')

    def listings(self, pid):
        """Məhsulun göründüyü bütün (bölmə, qrup) cütləri, bölmə sırası ilə."""
        out = []
        prim = self.P[pid]['sec']
        for slug in [prim] + [x for x in self.d['sections_order'] if x != prim]:
            for g in self.S[slug]['groups']:
                if pid in g['items']: out.append((slug, g))
        return out

    def search_entry(self, p, lang):
        pre = '' if lang == 'az' else '../'
        hay = [self.norm(p['n_az']), self.rnorm(p['n_ru'])]
        for slug, g in self.listings(p['id']):
            hay += [self.norm(self.S[slug]['n_az']), self.rnorm(self.S[slug]['n_ru'])]
            if g['id']: hay += [self.norm(g['n_az']), self.rnorm(g['n_ru'])]
        n = html.unescape(p['n_' + lang])
        return {"u": f'{p["slug"]}.html', "i": f'{pre}img/{p["id"]}.webp', "t": n, "k": html.unescape(self.tag_for(p, lang)),
                "n": self.norm(n) if lang == 'az' else self.rnorm(n), "h": ' '.join(hay)}
