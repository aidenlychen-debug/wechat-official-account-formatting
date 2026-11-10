"""Line-rule check for a built article, at every phone width a reader may have.

The rule (last line keeps at least two characters plus punctuation; no line holds only punctuation) is enforced
by build_html.py itself: the tail of every block is locked in a nowrap span. This script verifies it the hard way.
It renders the page in Chrome and sweeps phone widths 340 to 450 px one pixel at a time, with four font set-ups:
three Latin stand-ins (narrow, medium, wide) with a sans CJK font, and a serif set for Android phones
that fall back to serif. Every body paragraph, heading, quote line (each <br> segment) and reference is checked,
and so is overflow: no character may run past the right edge of its block (a long unbreakable tail would).

Usage: htmlcheck.py article.html            Needs Playwright and Chrome or Chromium (CHROME_PATH to choose one).
Without a browser, run selfcheck.py instead: it confirms the tail locks are in place."""
import os, shutil, subprocess
CHROME = os.environ.get('CHROME_PATH') or ('/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)  # None = Playwright's own Chromium
import asyncio, collections, pathlib, sys
from playwright.async_api import async_playwright

HTML = pathlib.Path(sys.argv[1]).resolve()
PHONES = list(range(340, 451))                       # screen widths in CSS px, every pixel
COMMON = [360, 375, 390, 393, 402, 412, 414, 428, 430, 440]
WECHAT_PAD = 16                                      # WeChat's own side padding
FONTS = [('narrow', 'Carlito', 'Noto Sans CJK SC'), ('medium', 'Liberation Sans', 'Noto Sans CJK SC'),
         ('wide', 'DejaVu Sans', 'Noto Sans CJK SC'), ('serif', 'Liberation Serif', 'Noto Serif CJK SC')]

def missing_fonts():
    if not shutil.which('fc-list'):
        return []
    have = subprocess.run(['fc-list', ':', 'family'], capture_output=True, text=True).stdout
    return sorted({f for _, a, b in FONTS for f in (a, b) if f not in have})

JS = r"""
(args) => {
  const [latin, cjk, widths, pad] = args;
  const art = document.getElementById('article');
  art.parentElement.style.padding = '0'; art.style.boxSizing = 'border-box';
  for (const el of art.querySelectorAll('*')) if (el.style.fontFamily) el.style.fontFamily = `'${latin}', '${cjk}', sans-serif`;
  const PUNCT = '，。、；：？！…—）」』》〉】〕］｝”’,.;:?!)]%～·「『《〈【〔［｛“‘（(["\'';   // same as TAIL_PUNCT in build_html.py
  const blocks = [...art.querySelectorAll('p, h2, h3')].filter(b => b.innerText.trim() && !b.querySelector('img'));
  const out = [];
  for (const w of widths) {
    art.style.width = (w - 2 * pad) + 'px';
    blocks.forEach((b, bi) => {
      const cs = getComputedStyle(b), edge = b.getBoundingClientRect().right - parseFloat(cs.paddingRight) - parseFloat(cs.borderRightWidth);
      let over = '';
      const segs = [[]]; const walker = document.createTreeWalker(b, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT); let node;
      while ((node = walker.nextNode())) {
        if (node.nodeType === 1) { if (node.tagName === 'BR') segs.push([]); continue; }
        for (let i = 0; i < node.length; i++) {
          const r = document.createRange(); r.setStart(node, i); r.setEnd(node, i + 1);
          const rc = r.getClientRects(); if (!rc.length) continue;
          segs[segs.length - 1].push({ c: node.data[i], top: Math.round(rc[0].top) });
          if (rc[0].right > edge + 1 && node.data[i].trim()) over += node.data[i];
        }
      }
      if (over) out.push([w, bi, 'runs past the right edge', '']);
      for (const chars of segs) {
        const lines = [];
        for (const ch of chars) { if (!lines.length || Math.abs(ch.top - lines[lines.length - 1].top) > 4) lines.push({ top: ch.top, text: '' }); lines[lines.length - 1].text += ch.c; }
        lines.forEach(l => { const core = [...l.text.replace(/\s/g, '')].filter(c => !PUNCT.includes(c)); if (!core.length && l.text.trim()) out.push([w, bi, 'punctuation-only line', l.text.trim()]); });
        if (lines.length > 1) {
          const last = lines[lines.length - 1].text.trim();
          const units = (last.match(/[A-Za-z0-9%]+|[^\sA-Za-z0-9%]/g) || []).filter(u => !PUNCT.includes(u));
          const weight = units.reduce((s, u) => s + (/^[\x00-\x7f]{3,}$/.test(u) ? 2 : 1), 0);
          if (weight < 2) out.push([w, bi, 'short last line', last]);
        }
      }
    });
  }
  return { n: blocks.length, out, texts: blocks.map(b => b.innerText.slice(0, 28)) };
}
"""

async def main():
    miss = missing_fonts()
    if miss:
        print('WARNING: fonts not installed, Chrome will substitute and the check is less reliable:', ', '.join(miss))
    hits = collections.defaultdict(set)
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        for name, latin, cjk in FONTS:
            pg = await br.new_page(viewport={'width': 1200, 'height': 1200})
            await pg.goto(HTML.as_uri())
            res = await pg.evaluate(JS, [latin, cjk, PHONES, WECHAT_PAD])
            for w, bi, kind, last in res['out']:
                hits[(bi, kind, last, res['texts'][bi])].add((w, name))
            print(f'{name:6} fonts: {res["n"]} blocks x {len(PHONES)} widths ({PHONES[0]}-{PHONES[-1]}px), '
                  f'{len({k for k, v in hits.items() if any(f == name for _, f in v)})} blocks with issues')
            await pg.close()
        await br.close()
    for (bi, kind, last, text), v in sorted(hits.items()):
        ws = sorted({w for w, _ in v}); common = [w for w in ws if w in COMMON]
        print(f'   {kind}{f" \"{last}\"" if last else ""} at {len(ws)} widths (common phones: {common or "none"}) in: {text}')
    print('TOTAL issues', len(hits))

asyncio.run(main())
