"""Semi-automatic layout for the common diagram types: give the type and the words, get every coordinate.

It measures the real fonts (LXGW WenKai, ink boxes after rendering), sizes the shapes around the text, keeps the
fixed 64px margins, checks the clearances from references/images.md, and prints the coordinate table and the
text table for 生图prompt.md, plus a grey sketch PNG for image-to-image (reference only, never delivered).

Usage: diagram.py spec.json [out_dir]        (fonts: WENKAI_DIR, see wireframe.py)

spec.json examples:
  {"type": "ring", "name": "loop", "title": ["先开枪，", "再瞄准"], "steps": ["先拿出产品", "试着卖", "客户的反应", "改进"]}
      a cycle: ring centred on the canvas, the title inside, numbered dots, each step label outside next to its dot.
      A label may hold "|" for a second line.
  {"type": "flow", "name": "route", "title": "排版的两条路",
   "rows": [{"boxes": ["文档", "转换工具", "公众号"], "note": "样式被改"},
            {"boxes": ["AI直接生成HTML", "公众号"], "accent": true, "note": "样式原样", "note_emph": true}]}
      rows of boxes joined by arrows, left to right; the last box of every row lines up on the right,
      a row with fewer boxes stretches its first box; the note goes under the last box.
  {"type": "container", "name": "skill", "title": "一个Skill里有什么",
   "items": [["规则", "排版和配图"], ["参考配图", "定稿配图"], ["脚本", "排版和检查"], ["检查清单", "交付前逐项查"]],
   "footer": "每一条修改意见，都写进规则"}
      one big box holding items in two columns, each with a dot, a label and a sub-label; an optional footer
      under the box with an arrow pointing up into it."""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

W, M = 1080, 64
WK = os.environ.get('WENKAI_DIR', 'fonts/lxgw-wenkai-v1.501').rstrip('/') + '/'
SIZE = {'title': 72, 'main': 58, 'sub': 46}
INK, SUB, EMPH, ORANGE, BG = (20, 20, 20), (111, 106, 99), (180, 80, 47), (216, 116, 88), (248, 248, 244)
PH, PHD = (189, 182, 171), (226, 207, 195)
CLEAR_LINE, CLEAR_DOT, LABEL_GAP, GROUP_GAP, BOX_H, BOX_PAD_X = 36, 20, 24, 58, 128, 40
RING_CAP = 280          # largest ring radius: with very short labels a bigger ring only looks empty

def font(kind):
    return ImageFont.truetype(WK + ('LXGWWenKai-Medium.ttf' if kind in ('title', 'main') else 'LXGWWenKai-Regular.ttf'), SIZE[kind])

def ink(text, kind):
    """real ink box of rendered text, relative to the drawing origin"""
    f = font(kind); im = Image.new('L', (len(text) * f.size * 2 + 40, f.size * 3), 0)
    ImageDraw.Draw(im).text((20, f.size), text, font=f, fill=255); b = im.getbbox()
    return b[0] - 20, b[1] - f.size, b[2] - 20, b[3] - f.size

def iw(t, k): b = ink(t, k); return b[2] - b[0]
def ih(t, k): b = ink(t, k); return b[3] - b[1]

class Sheet:
    def __init__(self):
        self.shapes, self.texts, self.inks = [], [], []
    def text(self, t, x, y, kind, color=INK, anchor='l'):
        """place text by its ink box: (x, y) is the ink's top-left / top-centre / top-right"""
        w, h = iw(t, kind), ih(t, kind)
        x0 = {'l': x, 'c': x - w / 2, 'r': x - w}[anchor]
        box = (x0, y, x0 + w, y + h); self.texts.append((t, kind, color, box, anchor, x, y)); self.inks.append(box); return box
    def shape(self, kind, box, **kw):
        self.shapes.append((kind, box, kw)); self.inks.append(box)

def clearance(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0); dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)

def finish(sh, name, out, problems, coords, extra_rows=(), note=None):
    x0 = min(b[0] for b in sh.inks); y0 = min(b[1] for b in sh.inks); x1 = max(b[2] for b in sh.inks); y1 = max(b[3] for b in sh.inks)
    H = round(y1 + M)
    margins = dict(left=round(x0), top=round(y0), right=round(W - x1), bottom=round(H - y1))
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    for kind, b, kw in sh.shapes:
        col = ORANGE if kw.get('accent') else PH
        if kind == 'box': d.rounded_rectangle(b, radius=26, outline=col, width=6)              # PIL strokes inwards: outer edge = box
        if kind == 'dot': d.ellipse(b, fill=ORANGE if kw.get('accent') else PHD)
        if kind == 'ring': d.ellipse(b, outline=PH, width=6)                                   # box is R+3, stroke R-3..R+3
        if kind == 'arrow':
            (ax, ay), (bx, by) = kw['a'], kw['b']; d.line([kw['a'], kw['b']], fill=col, width=6); ang = math.atan2(by - ay, bx - ax)
            for s in (1, -1): d.line([(bx, by), (bx - 22 * math.cos(ang + s * .5), by - 22 * math.sin(ang + s * .5))], fill=col, width=6)
    for t, kind, color, b, *_ in sh.texts:
        f = font(kind); ib = ink(t, kind); d.text((b[0] - ib[0], b[1] - ib[1]), t, font=f, fill=color)
    os.makedirs(out, exist_ok=True); path = os.path.join(out, f'草图_{name}.png'); im.save(path)
    print(f'## {name}: canvas {W} x {H}; ink margins L {margins["left"]} T {margins["top"]} R {margins["right"]} B {margins["bottom"]}; sketch {path}\n')
    print('| 元素 | 位置（单位 px，原点在左上角） |\n|---|---|')
    for k, v in coords: print(f'| {k} | {v} |')
    print('\n| 文字 | 字体 / 字号 | 颜色 | 笔画外框 |\n|---|---|---|---|')
    names = {INK: '墨色', SUB: '辅助灰', EMPH: '强调色 #B4502F'}
    fname = {'title': '霞鹜文楷 Medium 72px', 'main': '霞鹜文楷 Medium 58px', 'sub': '霞鹜文楷 Regular 46px'}
    for t, kind, color, b, anchor, x, y in sh.texts:
        pos = {'l': f'左上 ({round(x)}, {round(y)})', 'c': f'居中 x {round(x)}，上沿 y {round(y)}', 'r': f'右边对齐 x {round(x)}，上沿 y {round(y)}'}[anchor]
        print(f'| {t} | {fname[kind]} | {names.get(color, "墨色")} | {pos}（x {round(b[0])}–{round(b[2])}，y {round(b[1])}–{round(b[3])}） |')
    for row in extra_rows: print(row)
    side = [m for k, m in margins.items() if k in ('top', 'bottom')]
    if any(abs(m - M) > 4 for m in side):
        problems.append(f'top/bottom margin not {M}: {margins}')
    if min(margins['left'], margins['right']) < M - 4:
        problems.append(f'content runs into the side margin: {margins}')
    elif min(margins['left'], margins['right']) > M + 4 and not note:
        problems.append(f'the wider side should sit {M}px from the edge: {margins}')
    if note:
        print('note:', note)
    print('\nchecks:', 'all pass' if not problems else '')
    for p in problems: print('  PROBLEM', p)
    return not problems

def ring(spec, out):
    sh, problems, coords = Sheet(), [], []
    steps = spec['steps']; n = len(steps); D = 84; r = D / 2; cx = W / 2
    tlines = spec['title'] if isinstance(spec['title'], list) else [spec['title']]
    th = ih('先开枪再瞄准', 'title'); tgap = 22
    core = [t.rstrip('，。、：；？！') for t in tlines]                 # trailing punctuation hangs outside
    t_half_h = (th * len(tlines) + tgap * (len(tlines) - 1)) / 2
    # title line boxes relative to the ring centre, exactly as placed below (centred by the characters, mark hanging right)
    tboxes = [(-iw(c, 'title') / 2, -t_half_h + k * (th + tgap), -iw(c, 'title') / 2 + iw(t, 'title'), -t_half_h + k * (th + tgap) + th)
              for k, (t, c) in enumerate(zip(tlines, core))]
    angles = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    def fits_inside(R):
        for b in tboxes:
            for a in angles:
                x, y = R * math.cos(a), R * math.sin(a)
                if clearance(b, (x - r, y - r, x + r, y + r)) < CLEAR_DOT: return False
            if R - max(math.hypot(px, py) for px in (b[0], b[2]) for py in (b[1], b[3])) - 3 < CLEAR_LINE: return False
        return True
    r_min = next(R for R in range(40, 2000) if fits_inside(R))
    def lab(i): return steps[i].split('|')
    def lab_w(i): return max(iw(s, 'main') for s in lab(i))
    side = lambda a: abs(math.cos(a)) > abs(math.sin(a)) + 1e-9      # label beside the dot; otherwise above / below it
    # the largest radius that keeps every label, dot and the ring line inside the 64px side margins
    limits = [(W / 2 - M - 3, None)]
    for i, a in enumerate(angles):
        c = abs(math.cos(a))
        if c < 1e-9:
            continue
        limits.append(((W / 2 - M - r) / c, None))
        if side(a):
            limits.append(((W / 2 - M - LABEL_GAP - r - lab_w(i)) / c, i))
        elif c >= 0.2:                                   # diagonal label runs outwards from the dot's inner edge
            limits.append(((W / 2 - M + r - lab_w(i)) / c, i))
    r_max, tight = min(limits, key=lambda t: t[0])
    for i, a in enumerate(angles):
        if not side(a) and abs(math.cos(a)) < 0.2 and lab_w(i) > W - 2 * M:
            print(f'PROBLEM: label "{steps[i]}" is wider than the canvas; split it with "|" or shorten it.'); return False
    if r_max < r_min:
        advice = []
        if len(tlines) < 2: advice.append('split the title inside the ring into two lines')
        else: advice.append('shorten the title inside the ring')
        if tight is not None:
            advice.append(f'shorten the label "{steps[tight]}"' if '|' in steps[tight] else f'split the label "{steps[tight]}" with "|" or shorten it')
        print(f'PROBLEM: a centred ring with the title inside does not fit (need R >= {r_min}, room for R <= {r_max:.0f}). '
              f'Try: {"; or ".join(advice)}, keeping the meaning.')
        return False
    def place(R):
        sh, problems, coords = Sheet(), [], []
        lh = ih('先拿出产品', 'main'); top_lab = len(lab(0)) * lh + (len(lab(0)) - 1) * 14
        cy = M + top_lab + LABEL_GAP + r + R
        sh.shape('ring', (cx - R - 3, cy - R - 3, cx + R + 3, cy + R + 3))
        coords.append(('圆环', f'圆心 ({cx:.0f}, {cy:.0f})，半径 {R}，手绘墨线约 6px'))
        dots = []
        for i, a in enumerate(angles):
            x, y = cx + R * math.cos(a), cy + R * math.sin(a); dots.append((x, y))
            sh.shape('dot', (x - r, y - r, x + r, y + r))
        coords.append(('圆点', f'Ø{D}，哑光陶土，压在圆环上，顺时针从正上方开始：' + '、'.join(f'({x:.0f}, {y:.0f})' for x, y in dots)))
        coords.append(('箭头', '每段弧的末端一个手绘箭头，箭头尖停在下一个圆点前约 10px，顺时针；最后一段（回到第一个圆点）用陶土橙，线宽约 8px'))
        boxes, owner = [], []
        for i, ((x, y), a) in enumerate(zip(dots, angles)):
            start = len(boxes)
            lines = lab(i); h = len(lines) * lh + (len(lines) - 1) * 14
            if not side(a):                                    # mostly above / below: centred over / under the dot
                y0 = y - r - LABEL_GAP - h if math.sin(a) < 0 else y + r + LABEL_GAP
                if abs(math.cos(a)) < 0.2:                     # straight up / down: centred
                    for k, s in enumerate(lines): boxes.append(sh.text(s, x, y0 + k * (lh + 14), 'main', INK, 'c'))
                else:                                          # diagonal: start at the dot's inner edge and run outwards
                    for k, s in enumerate(lines):
                        boxes.append(sh.text(s, x - r if math.cos(a) > 0 else x + r, y0 + k * (lh + 14), 'main', INK, 'l' if math.cos(a) > 0 else 'r'))
            else:                                              # left or right side: vertically centred on the dot
                y0 = y - h / 2
                for k, s in enumerate(lines):
                    boxes.append(sh.text(s, x + r + LABEL_GAP if math.cos(a) > 0 else x - r - LABEL_GAP, y0 + k * (lh + 14), 'main', INK, 'l' if math.cos(a) > 0 else 'r'))
            owner += [i] * (len(boxes) - start)
        ty = cy - t_half_h
        for k, (t, c) in enumerate(zip(tlines, core)):
            x0 = cx - iw(c, 'title') / 2                        # centre by the characters; the hanging mark sits to the right
            boxes.append(sh.text(t, x0, ty + k * (th + tgap), 'title', INK, 'l')); owner.append('title')
        coords.append(('文字区（留空）', '圆环正中放标题；每个圆点外侧放它的步骤标签，见文字表'))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if owner[i] == owner[j]: continue              # lines of the same label or of the title
                if clearance(boxes[i], boxes[j]) < CLEAR_DOT - 0.5 and abs(boxes[i][1] - boxes[j][1]) > 1 or (clearance(boxes[i], boxes[j]) < 30 and abs(boxes[i][1] - boxes[j][1]) <= 1):
                    problems.append(f'labels too close: {tuple(round(v) for v in boxes[i])} and {tuple(round(v) for v in boxes[j])}')
        for b in boxes:
            for (x, y) in dots:
                c = clearance(b, (x - r, y - r, x + r, y + r))
                if c < CLEAR_DOT - 0.5: problems.append(f'text {b} only {c:.0f}px from a dot')
            dmin = math.hypot(max(b[0] - cx, 0, cx - b[2]), max(b[1] - cy, 0, cy - b[3]))      # centre to nearest point
            dmax = max(math.hypot(px - cx, py - cy) for px in (b[0], b[2]) for py in (b[1], b[3]))
            gap = 0 if dmin <= R <= dmax else (R - dmax if dmax < R else dmin - R)
            if gap - 3 < CLEAR_LINE - 0.5: problems.append(f'text {tuple(round(v) for v in b)} only {gap - 3:.0f}px from the ring line')
        nums = [f'| {i + 1:02d} | Caveat SemiBold 52px | 墨色 | 圆点正中 ({x:.0f}, {y:.0f}) |' for i, (x, y) in enumerate(dots)]
        return sh, problems, coords, nums
    # as large as the margins allow (wider side 64px), up to the cap; shrink while a label sits too close to the ring
    top = max(math.floor(min(r_max, RING_CAP)), r_min)   # a big title may need more than the cap
    first = None
    for R in range(top, r_min - 1, -1):
        sh, problems, coords, nums = place(R)
        first = first or (sh, problems, coords, nums)
        if not problems:
            break
    else:
        sh, problems, coords, nums = first
        R = top
        problems.append('no radius between the minimum and the maximum clears every label; shorten or split the labels named above')
    note = None if R >= math.floor(r_max) else (f'ring radius {R} is below the {r_max:.0f} the side margins allow '
        f'({"capped at " + str(RING_CAP) if r_max > RING_CAP and R == RING_CAP else "labels need room from the ring line"}), so both sides are wider than {M}px (allowed)')
    return finish(sh, spec.get('name', 'ring'), out, problems, coords, nums, note=note)

def flow(spec, out):
    sh, problems, coords = Sheet(), [], []
    T = sh.text(spec['title'], M, M, 'title') if spec.get('title') else (M, M, M, M - GROUP_GAP)
    y = T[3] + GROUP_GAP; rows = spec['rows']
    widths = [[max(iw(b, 'main') + 2 * BOX_PAD_X, 194) for b in row['boxes']] for row in rows]
    longest = max(rows, key=lambda r: len(r['boxes'])); k = rows.index(longest)
    gap = (W - 2 * M - sum(widths[k])) / max(len(longest['boxes']) - 1, 1)
    if gap < 84: problems.append(f'arrows shorter than 48px (gap {gap:.0f}); shorten box labels')
    right_w = max(w[-1] for w in widths)
    for ri, (row, ws) in enumerate(zip(rows, widths)):
        ws[-1] = right_w
        if len(ws) < len(longest['boxes']):                 # stretch the first box so the last one lines up on the right
            ws[0] = W - 2 * M - sum(ws[1:]) - gap * (len(ws) - 1)
        x = M; prev = None; acc = row.get('accent', False)
        for bi, (label, w) in enumerate(zip(row['boxes'], ws)):
            box = (x, y, x + w, y + BOX_H); sh.shape('box', box, accent=acc)
            t = sh.text(label, x + w / 2, y + (BOX_H - ih(label, 'main')) / 2, 'main', INK, 'c')
            if t[0] - x < BOX_PAD_X or x + w - t[2] < BOX_PAD_X: problems.append(f'"{label}" too close to its box sides')
            coords.append((f'第 {ri + 1} 行第 {bi + 1} 个框', f'{"陶土橙" if acc else "墨线"}，外缘 x {x:.0f}–{x + w:.0f}，y {y:.0f}–{y + BOX_H:.0f}'))
            if prev:
                a, b = (prev[2] + 18, y + BOX_H / 2), (x - 18, y + BOX_H / 2); sh.shape('arrow', (a[0], a[1] - 12, b[0], b[1] + 12), a=a, b=b, accent=acc)
                coords.append((f'第 {ri + 1} 行箭头', f'{"陶土橙" if acc else "墨线"}，y {a[1]:.0f}：x {a[0]:.0f}→{b[0]:.0f}'))
            prev = box; x += w + gap
        ny = y + BOX_H
        if row.get('note'):
            nb = sh.text(row['note'], (prev[0] + prev[2]) / 2, y + BOX_H + LABEL_GAP, 'sub', EMPH if row.get('note_emph') else SUB, 'c'); ny = nb[3]
        y = ny + GROUP_GAP
    return finish(sh, spec.get('name', 'flow'), out, problems, coords)

def container(spec, out):
    sh, problems, coords = Sheet(), [], []
    T = sh.text(spec['title'], M, M, 'title') if spec.get('title') else (M, M, M, M - GROUP_GAP)
    y0 = T[3] + GROUP_GAP; pad, colgap, dot = 48, 40, 52
    lh = max(ih(a, 'main') for a, _ in spec['items']); sh_ = max(ih(b, 'sub') for _, b in spec['items'])
    cell_w = (W - 2 * M - 2 * pad - colgap) / 2; cell_h = lh + 16 + sh_
    rows = math.ceil(len(spec['items']) / 2); y1 = y0 + 2 * pad + rows * cell_h + (rows - 1) * 48
    sh.shape('box', (M, y0, W - M, y1)); coords.append(('大框', f'墨线，外缘 x {M}–{W - M}，y {y0:.0f}–{y1:.0f}'))
    for i, (a, b) in enumerate(spec['items']):
        cx0 = M + pad + (i % 2) * (cell_w + colgap); cy0 = y0 + pad + (i // 2) * (cell_h + 48)
        sh.shape('dot', (cx0, cy0 + lh / 2 - dot / 2, cx0 + dot, cy0 + lh / 2 + dot / 2))
        coords.append((f'圆点 {i + 1}', f'Ø{dot}，圆心 ({cx0 + dot / 2:.0f}, {cy0 + lh / 2:.0f})'))
        t1 = sh.text(a, cx0 + dot + LABEL_GAP, cy0, 'main'); t2 = sh.text(b, cx0 + dot + LABEL_GAP, cy0 + lh + 16, 'sub', SUB)
        if max(t1[2], t2[2]) > cx0 + cell_w: problems.append(f'item "{a} / {b}" wider than its cell')
    if spec.get('footer'):
        fy = y1 + LABEL_GAP + 72 + LABEL_GAP
        fb = sh.text(spec['footer'], W / 2, fy, 'sub', EMPH, 'c')
        a, b = (W / 2, fb[1] - LABEL_GAP), (W / 2, y1 + 14); sh.shape('arrow', (W / 2 - 12, b[1], W / 2 + 12, a[1]), a=a, b=b, accent=True)
        coords.append(('向上箭头', f'陶土橙，约 7px，x {W / 2:.0f}，从 y {a[1]:.0f} 向上，箭头尖停在 y {b[1]:.0f}'))
    return finish(sh, spec.get('name', 'container'), out, problems, coords)

if __name__ == '__main__':
    spec = json.load(open(sys.argv[1], encoding='utf8'))
    out = sys.argv[2] if len(sys.argv) > 2 else 'layout'
    ok = {'ring': ring, 'flow': flow, 'container': container}[spec['type']](spec, out)
    sys.exit(0 if ok else 1)
