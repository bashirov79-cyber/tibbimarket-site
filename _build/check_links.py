#!/usr/bin/env python3
"""Qırıq daxili keçid və şəkilləri tapır. İstifadə (repo kökündən): python3 _build/check_links.py"""
import os, re, sys
bad = []
for d in ('', 'ru/', 'en/'):
    if d and not os.path.isdir(d): continue
    for f in os.listdir(d or '.'):
        if not f.endswith('.html'): continue
        s = re.sub(r'<script.*?</script>', '', open(d + f, encoding='utf-8').read(), flags=re.S)
        for h in re.findall(r'(?:href|src|srcset)="([^"]+)"', s):
            h = h.split('#')[0].split('?')[0]
            if not h or ':' in h or h.startswith('/'): continue
            p = os.path.normpath(os.path.join(d, h))
            if h.endswith('/') or h in ('.', './'): p = os.path.join(p, 'index.html')
            if not os.path.exists(p): bad.append(f'{d}{f} → {h}')
print('\n'.join(bad[:30]) if bad else 'OK: qırıq keçid yoxdur'); sys.exit(1 if bad else 0)
