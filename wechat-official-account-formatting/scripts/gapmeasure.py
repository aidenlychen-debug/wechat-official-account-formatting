"""Measure the visible (ink) gaps above and below every h2 and h3, in CSS px, from a real render."""
import os as _os
CHROME = _os.environ.get('CHROME_PATH') or ('/usr/bin/google-chrome' if _os.path.exists('/usr/bin/google-chrome') else None)  # None = Playwright's own Chromium
import asyncio, pathlib, sys
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright
HTML = pathlib.Path(sys.argv[1]).resolve()
DSF = 2
JS = """() => [...document.querySelectorAll('#article h2, #article h3')].map(h => {
  const box = el => { const r = el.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.right + scrollX, r.bottom + scrollY]; };
  return {tag: h.tagName, text: h.innerText, prev: box(h.previousElementSibling), prevTag: h.previousElementSibling.tagName,
          prevImg: !!h.previousElementSibling.querySelector('img'), self: box(h), next: box(h.nextElementSibling)};
})"""
def ink(a, b, top):
    x0, y0, x1, y1 = [int(round(v * DSF)) for v in b]
    crop = a[y0:y1, x0:x1]
    rows = np.where((crop.min(2) < 200).any(1))[0]
    return (y0 + (rows[0] if top else rows[-1])) / DSF if len(rows) else (b[1] if top else b[3])
async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg = await br.new_page(viewport={'width': 402, 'height': 900}, device_scale_factor=DSF)
        await pg.goto(HTML.as_uri()); await pg.wait_for_timeout(300)
        items = await pg.evaluate(JS)
        await pg.screenshot(path='/tmp/gm.png', full_page=True)
        await br.close()
    a = np.asarray(Image.open('/tmp/gm.png').convert('RGB')).astype(int)
    for it in items:
        if it['tag'] == 'H2':      # the bar is the visible heading; above = divider line to bar top
            above = it['self'][1] - it['prev'][3]
            below = ink(a, it['next'], True) - it['self'][3]
        else:
            above = ink(a, it['self'], True) - (it['prev'][3] if it['prevImg'] else ink(a, it['prev'], False))
            below = ink(a, it['next'], True) - ink(a, it['self'], False)
        print(f"{it['tag']} {it['text']:<14} above {above:5.1f}  below {below:5.1f}  ratio {above / below:4.2f}{'  (after image)' if it['prevImg'] else ''}")
asyncio.run(main())

# paragraph-to-paragraph gaps (the "空行") for one-line or multi-line body paragraphs
async def para_gaps():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg = await br.new_page(viewport={'width': 402, 'height': 900}, device_scale_factor=DSF)
        await pg.goto(HTML.as_uri()); await pg.wait_for_timeout(300)
        pairs = await pg.evaluate("""() => [...document.querySelectorAll('#article p.bp')].filter(p => p.nextElementSibling && p.nextElementSibling.matches('p.bp'))
          .map(p => [p, p.nextElementSibling].map(el => { const r = el.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.right + scrollX, r.bottom + scrollY]; }))""")
        await pg.screenshot(path='/tmp/gm.png', full_page=True); await br.close()
    a = np.asarray(Image.open('/tmp/gm.png').convert('RGB')).astype(int)
    g = sorted(ink(a, n, True) - ink(a, p, False) for p, n in pairs)
    print(f'paragraph gap: median {g[len(g) // 2]:.1f}  min {g[0]:.1f}  max {g[-1]:.1f}  (n={len(g)})')
asyncio.run(para_gaps())
