"""Check a built article on the phones the user named.

For each phone width in CSS px (default: 402, the small screen the preview is built for, and 440, a large one)
the page is rendered at that width minus WeChat's side padding, with Liberation Sans + Noto Sans CJK SC standing
in for the phone fonts.
It reports:
  split   nowrap spans (proper nouns and locked tails) that ended up on two lines; must be empty
  short   paragraphs whose last line has fewer than two characters (punctuation not counted); must be empty
  uneven  lines whose characters sit visibly farther apart than on the other lines: justification spreads
          the room left at the end of a line over the gaps between characters, so a line that ends a
          character early (a name moved whole to the next line, a closing mark that may not start a line, a
          locked tail) is looser than the rest. Flagged when the extra space per gap between two Chinese
          characters is more than 0.75px above the median line; must be empty for even spacing.

Usage: phonecheck.py article.html [width ...]      default widths: 402 440"""
import os, sys, asyncio, pathlib
from playwright.async_api import async_playwright

CHROME = os.environ.get('CHROME_PATH') or ('/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
HTML = pathlib.Path(sys.argv[1]).resolve()
WIDTHS = [int(w) for w in sys.argv[2:]] or [402, 440]
WECHAT_PAD = 16

JS = r"""
([w, pad]) => {
  const art = document.getElementById('article');
  art.parentElement.style.padding = '0'; art.style.boxSizing = 'border-box'; art.style.width = (w - 2 * pad) + 'px';
  for (const el of art.querySelectorAll('*')) if (el.style.fontFamily) el.style.fontFamily = "'Liberation Sans', 'Noto Sans CJK SC', sans-serif";
  const PUNCT = '，。、；：？！…—）」』》〉】〕］｝”’,.;:?!)]%～·「『《〈【〔［｛“‘（(["\'';
  const CJK = /[㐀-鿿]/;
  const res = {split: [], short: [], loose: []};
  for (const sp of art.querySelectorAll('span[style*="nowrap"]'))
    if (new Set([...sp.getClientRects()].map(r => Math.round(r.top))).size > 1) res.split.push(sp.innerText);
  for (const b of art.querySelectorAll('p, h2, h3')) {
    if (!b.innerText.trim() || b.querySelector('img')) continue;
    const cs = getComputedStyle(b), adv = parseFloat(cs.fontSize) + (parseFloat(cs.letterSpacing) || 0);
    const segs = [[]]; const tw = document.createTreeWalker(b, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT); let n;
    while ((n = tw.nextNode())) {
      if (n.nodeType === 1) { if (n.tagName === 'BR') segs.push([]); continue; }
      for (let i = 0; i < n.length; i++) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const rc = r.getClientRects(); if (rc.length) segs[segs.length - 1].push({c: n.data[i], top: Math.round(rc[0].top), l: rc[0].left}); }
    }
    for (const chars of segs) {
      const lines = []; for (const ch of chars) { if (!lines.length || Math.abs(ch.top - lines[lines.length - 1][0].top) > 4) lines.push([]); lines[lines.length - 1].push(ch); }
      if (lines.length > 1) { const last = lines[lines.length - 1].map(x => x.c).join('').trim(); if ([...last.replace(/\s/g, '')].filter(c => !PUNCT.includes(c)).length < 2) res.short.push(last); }
      lines.slice(0, -1).forEach(L => {
        const ex = []; for (let i = 1; i < L.length; i++) if (CJK.test(L[i - 1].c) && CJK.test(L[i].c)) ex.push(L[i].l - L[i - 1].l - adv);
        if (ex.length) res.loose.push([Math.round(ex.reduce((s, x) => s + x, 0) / ex.length * 10) / 10, L.map(x => x.c).join('')]);
      });
    }
  }
  const xs = res.loose.map(x => x[0]).sort((a, b) => a - b), med = xs.length ? xs[Math.floor(xs.length / 2)] : 0;
  res.uneven = res.loose.filter(x => x[0] > med + 0.75).sort((a, b) => b[0] - a[0]);
  return res;
}"""

async def main():
    bad = 0
    async with async_playwright() as p:
        b = await p.chromium.launch(**({'executable_path': CHROME} if CHROME else {}), args=['--no-sandbox'])
        for w in WIDTHS:
            pg = await b.new_page(viewport={'width': 1000, 'height': 1200})
            await pg.goto(HTML.as_uri()); r = await pg.evaluate(JS, [w, WECHAT_PAD]); await pg.close()
            bad += len(r['split']) + len(r['short']) + len(r['uneven'])
            print(f'{w}px screen: split {r["split"] or "none"}; short last lines {r["short"] or "none"}; uneven lines {len(r["uneven"]) or "none"}')
            for ex, line in r['uneven']:
                print(f'   uneven {ex:>4}px  {line}')
        await b.close()
    print('PASS' if not bad else f'{bad} problem(s)')
    sys.exit(1 if bad else 0)

asyncio.run(main())
