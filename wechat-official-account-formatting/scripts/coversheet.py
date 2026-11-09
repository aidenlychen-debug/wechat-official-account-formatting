"""Cover comparison sheet: puts each cover next to its 1:1 crop, at the size readers see in the feed.

Usage:
    python3 coversheet.py 1.png 2.png 3.png 4.png -o 封面对比.png
    python3 coversheet.py 1.png 2.png:200 ...      # ":200" = left edge of the 1:1 square (default: rightmost square)

The left edge is in the coordinates of the 1915-wide canvas written in 封面生图prompt.md; when the generated image
has another width, it is scaled to match.

Each cell: the cover scaled to 358px wide (a phone feed card) and its 1:1 square scaled to the same height.
Two cells per row. Needs Pillow.
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

FEED_W = 358
GAP, PAD, LABEL_H = 16, 24, 30
BG, INK, LINE = (255, 255, 255), (20, 20, 20), (220, 220, 220)


def font(size):
    d = os.environ.get('WENKAI_DIR')
    if d and os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(('.ttf', '.otf')) and 'regular' in f.lower():
                return ImageFont.truetype(os.path.join(d, f), size)
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


CANVAS_W = 1915


def cell(spec, n, f):
    path, _, x = spec.rpartition(':')
    if not path or not os.path.exists(path):      # no offset given (or a Windows path such as C:\covers\1.png)
        path, x = spec, ''
    if x and not x.isdigit():
        raise SystemExit(f'{spec}: the 1:1 left edge must be a whole number of pixels, e.g. {path}:200')
    im = Image.open(path).convert('RGB')
    w, h = im.size
    left = round(int(x) * w / CANVAS_W) if x else w - h
    if x and abs(w - CANVAS_W) > 2:
        print(f'{path}: {w}x{h}, so the left edge {x} (1915-wide canvas) becomes {left}')
    if not 0 <= left <= w - h:
        raise SystemExit(f'{path}: 1:1 left edge {left} is outside 0..{w - h}')
    th = round(h * FEED_W / w)
    feed = im.resize((FEED_W, th), Image.LANCZOS)
    sq = im.crop((left, 0, left + h, h)).resize((th, th), Image.LANCZOS)
    c = Image.new('RGB', (FEED_W + GAP + th, LABEL_H + th), BG)
    d = ImageDraw.Draw(c)
    d.text((0, 2), f'{n}  {os.path.basename(path)}', fill=INK, font=f)
    d.text((FEED_W + GAP, 2), '1:1', fill=INK, font=f)
    c.paste(feed, (0, LABEL_H)); c.paste(sq, (FEED_W + GAP, LABEL_H))
    d.rectangle((0, LABEL_H, FEED_W - 1, LABEL_H + th - 1), outline=LINE)
    d.rectangle((FEED_W + GAP, LABEL_H, FEED_W + GAP + th - 1, LABEL_H + th - 1), outline=LINE)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('covers', nargs='+')
    ap.add_argument('-o', '--out', default='封面对比.png')
    a = ap.parse_args()
    f = font(18)
    cells = [cell(s, i + 1, f) for i, s in enumerate(a.covers)]
    cw = max(c.width for c in cells); ch = max(c.height for c in cells)
    cols = 2 if len(cells) > 1 else 1
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new('RGB', (PAD + cols * (cw + PAD * 2) - PAD, PAD + rows * (ch + PAD)), BG)
    for i, c in enumerate(cells):
        r, k = divmod(i, cols)
        sheet.paste(c, (PAD + k * (cw + PAD * 2), PAD + r * (ch + PAD)))
    sheet.save(a.out)
    print(f'saved {a.out} {sheet.size[0]}x{sheet.size[1]}')


if __name__ == '__main__':
    main()
