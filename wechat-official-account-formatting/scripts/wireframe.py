"""Layout references for the four article images: final text at final size, rough placeholder shapes,
fixed 64px margin on every side (canvas height follows the content). Output: deliver/版式参考_*.png"""
import math, os
from PIL import Image, ImageDraw, ImageFont

F = os.environ.get('WENKAI_DIR', 'fonts/lxgw-wenkai-v1.501') + '/'   # folder with LXGWWenKai-Medium.ttf / -Regular.ttf
CAV = os.environ.get('CAVEAT_FILE', 'fonts/caveat-latin-600-normal.woff')   # Caveat SemiBold
W, M = 1080, 64
SIZE = dict(title=72, main=58, sub=46, en=48, num=52)
INK, SUBC, CLAYT, CLAY, DOT, BG = '#141414', '#6F6A63', '#B4502F', '#D87458', '#C89884', '#F8F8F4'
PH, PH_DOT, GUIDE = '#BDB6AB', '#E2CFC3', '#7FB3E0'          # placeholder line / dot, margin guide

def font(kind):
    if kind in ('en', 'num'):
        return ImageFont.truetype(CAV, SIZE[kind])
    return ImageFont.truetype(F + ('LXGWWenKai-Medium.ttf' if kind in ('title', 'main') else 'LXGWWenKai-Regular.ttf'), SIZE[kind])

class Canvas:
    def __init__(self, h=1800, bg=BG):
        self.bg = bg
        self.im = Image.new('RGB', (W, h), bg)
        self.d = ImageDraw.Draw(self.im)
        self.ink = [W, h, 0, 0]               # union of all drawn ink, to check the margins

    def grow(self, box):
        x0, y0, x1, y1 = box
        self.ink = [min(self.ink[0], x0), min(self.ink[1], y0), max(self.ink[2], x1), max(self.ink[3], y1)]

    def text(self, s, x, y, kind, color, align='l', spacing=0):
        """Place text so that its INK box starts at y (top) and x (left / centre / right)."""
        f = font(kind)
        widths = [self.d.textlength(c, font=f) for c in s]
        total = sum(widths) + spacing * (len(s) - 1)
        x0 = {'l': x, 'c': x - total / 2, 'r': x - total}[align]
        top = min(self.d.textbbox((0, 0), c, font=f)[1] for c in s if c.strip())
        cx = x0
        for c, w in zip(s, widths):
            self.d.text((cx, y - top), c, font=f, fill=color)
            cx += w + spacing
        bb = self.d.textbbox((x0, y - top), s, font=f) if not spacing else (x0, y, x0 + total, y + SIZE[kind])
        self.grow(bb)
        return bb

    def vtext(self, s, x, yc, kind, color, gap=8):
        """Vertical text centred on yc, left edge x."""
        f = font(kind); h = SIZE[kind]
        total = len(s) * h + (len(s) - 1) * gap
        y = yc - total / 2
        for c in s:
            bb = self.d.textbbox((0, 0), c, font=f)
            self.d.text((x + (h - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1]), c, font=f, fill=color)
            y += h + gap
        self.grow((x, yc - total / 2, x + h, yc + total / 2))

    def dot(self, cx, cy, d, fill=PH_DOT):
        r = d / 2; self.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill); self.grow((cx - r, cy - r, cx + r, cy + r))

    def line(self, pts, w=4, fill=PH):
        self.d.line(pts, fill=fill, width=w, joint='curve')
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]; self.grow((min(xs) - w / 2, min(ys) - w / 2, max(xs) + w / 2, max(ys) + w / 2))

    def arrow(self, x0, y0, x1, y1, w=4, fill=PH, head=16):
        self.line([(x0, y0), (x1, y1)], w, fill)
        a = math.atan2(y1 - y0, x1 - x0)
        for s in (1, -1):
            self.line([(x1, y1), (x1 - head * math.cos(a + s * 0.5), y1 - head * math.sin(a + s * 0.5))], w, fill)

    def box(self, x0, y0, x1, y1, outline=PH, fill=None, w=4):
        self.d.rounded_rectangle((x0, y0, x1, y1), radius=22, outline=outline, fill=fill, width=w); self.grow((x0, y0, x1, y1))

    def dashed(self, pts, fill, w=5, dash=18, gap=12):
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            L = math.hypot(xb - xa, yb - ya); n = 0.0
            while n < L:
                e = min(n + dash, L)
                self.line([(xa + (xb - xa) * n / L, ya + (yb - ya) * n / L), (xa + (xb - xa) * e / L, ya + (yb - ya) * e / L)], w, fill)
                n += dash + gap

    def finish(self, name):
        h = int(round(self.ink[3])) + M
        im = self.im.crop((0, 0, W, h))
        g = ImageDraw.Draw(im)
        for i in range(M, W - M, 24):                                   # dashed margin guide
            g.line([(i, M), (min(i + 12, W - M), M)], fill=GUIDE, width=2); g.line([(i, h - M), (min(i + 12, W - M), h - M)], fill=GUIDE, width=2)
        for j in range(M, h - M, 24):
            g.line([(M, j), (M, min(j + 12, h - M))], fill=GUIDE, width=2); g.line([(W - M, j), (W - M, min(j + 12, h - M))], fill=GUIDE, width=2)
        os.makedirs('deliver', exist_ok=True)
        im.save(f'deliver/版式参考_{name}.png')
        x0, y0, x1, y1 = self.ink
        print(f'{name}: {W}x{h}  ink margins  left {x0:.0f}  top {y0:.0f}  right {W - x1:.0f}  bottom {h - y1:.0f}')
        return im

# ---------- 图 1 头图 (terracotta) ----------
def head():
    c = Canvas(bg=CLAY)
    ivory85 = '#F2D9CF'          # ivory at about 85% over the terracotta
    c.text('AI-NATIVE COMPANY', M, M, 'en', ivory85, spacing=4)
    gy = 300
    for (x, y, d) in [(84, 250, 40), (170, 330, 52), (120, 410, 34), (262, 230, 30), (300, 360, 46), (380, 270, 38), (392, 430, 30)]:
        c.dot(x, y, d, fill='#EAD3C8')
    c.arrow(450, gy, 600, gy, w=7, fill='#2A1E1A', head=26)
    pts = [(700, 250), (790, 205), (880, 260), (840, 360), (740, 395), (930, 400), (800, 290)]
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (3, 5), (2, 6), (6, 4), (6, 0)]:
        c.line([pts[a], pts[b]], 4, '#2A1E1A')
    for x, y in pts:
        c.dot(x, y, 44, fill='#EAD3C8')
    c.d.arc((650, 150, 1016, 460), 200, 520, fill='#2A1E1A', width=6); c.grow((650, 150, 1016, 460))
    c.text('个人经验', 238, 500, 'main', BG, 'c')
    c.text('组织能力', 833, 500, 'main', BG, 'c')
    return c.finish('图1_头图')

# ---------- 图 2 传统公司树状结构 ----------
def tree():
    c = Canvas()
    t = c.text('传统公司', M, M, 'title', INK)
    c.text('· 像一棵树', t[2] + 22, t[3] - SIZE['sub'] + 2, 'sub', SUBC)
    rows = {'top': 260, 'mid': 410, 'bot': 560}
    bx = [340 + 80 * k for k in range(6)]; mx = [380, 540, 700]
    for i, x in enumerate(mx):
        c.line([(540, rows['top']), (x, rows['mid'])])
        for k in (2 * i, 2 * i + 1):
            c.line([(x, rows['mid']), (bx[k], rows['bot'])])
    c.dot(540, rows['top'], 76)
    for x in mx: c.dot(x, rows['mid'], 64)
    for k, x in enumerate(bx):
        c.dot(x, rows['bot'], 60 if k == 3 else 52, fill=CLAY if k == 3 else PH_DOT)
    c.dashed([(bx[3] + 46 * math.cos(a / 20 * 2 * math.pi), rows['bot'] + 46 * math.sin(a / 20 * 2 * math.pi)) for a in range(21)], PH, w=3, dash=10, gap=8)
    for name, y in (('管理层', rows['top']), ('部门', rows['mid']), ('一线员工', rows['bot'])):
        c.text(name, M, y - SIZE['sub'] / 2, 'sub', SUBC)
    c.vtext('向上汇报', 802, 410, 'sub', SUBC); c.arrow(880, 570, 880, 250, w=5)
    c.vtext('层层传达', 926, 410, 'sub', SUBC); c.arrow(1006, 250, 1006, 570, w=5)
    c.text('经验留在个人', bx[3], rows['bot'] + 46 + 28, 'main', CLAYT, 'c')
    return c.finish('图2_传统公司树状结构')

# ---------- 图 3 五个层次（循环） ----------
def loop():
    c = Canvas()
    t = c.text('五个层次', M, M, 'title', INK)
    c.text('· 结果反馈给系统', t[2] + 22, t[3] - SIZE['sub'] + 2, 'sub', SUBC)
    layers = [('01', '信息感知', '看见业务'), ('02', '规则判断', '划清边界'), ('03', '工具执行', '动手做事'),
              ('04', '质量把关', '检查结果'), ('05', '反馈学习', '持续改进')]
    y0, pitch, d = 262, 148, 92
    for i, (n, name, desc) in enumerate(layers):
        y = y0 + i * pitch
        c.dot(M + d / 2, y, d)
        c.text(n, M + d / 2, y - 18, 'num', INK, 'c')
        c.text(name, 196, y - SIZE['main'] / 2, 'main', INK)
        c.text(desc, 196 + 4 * SIZE['main'] + 44, y - SIZE['sub'] / 2 + 4, 'sub', SUBC)
        if i < 4:
            c.arrow(M + d / 2, y + d / 2 + 10, M + d / 2, y + pitch - d / 2 - 10, w=4)
    yl = y0 + 4 * pitch
    c.line([(700, yl), (960, yl)], 7, CLAY)
    c.d.arc((904, yl - 112, 1016, yl), 0, 90, fill=CLAY, width=7)
    c.line([(1013, yl - 56), (1013, y0 + 56)], 7, CLAY)
    c.d.arc((904, y0, 1016, y0 + 112), 270, 360, fill=CLAY, width=7); c.grow((904, y0, 1016, yl))
    c.arrow(960, y0, 708, y0, w=7, fill=CLAY, head=24)
    return c.finish('图3_五个层次')

# ---------- 图 4 订单流程 ----------
def flow():
    c = Canvas()
    t = c.text('订单处理', M, M, 'title', INK)
    c.text('· 先选一条流程', t[2] + 22, t[3] - SIZE['sub'] + 2, 'sub', SUBC)
    CX = 444
    def single(y, w, s, color=INK):
        c.box(CX - w / 2, y, CX + w / 2, y + 130); c.text(s, CX, y + 36, 'main', color, 'c'); return y + 130
    def double(x0, x1, y, main, sub, mc=INK, outline=PH, fill=None):
        c.box(x0, y, x1, y + 188, outline=outline, fill=fill)
        m = c.text(main, (x0 + x1) / 2, y + 36, 'main', mc, 'c'); c.text(sub, (x0 + x1) / 2, m[3] + 16, 'sub', SUBC, 'c'); return y + 188
    y = single(200, 360, '收到订单')
    c.arrow(CX, y + 8, CX, y + 56); y += 64
    b2 = y; y = double(CX - 230, CX + 230, y, 'AI 自动核对', '库存 · 交期 · 发货')
    L, R = (64 + 420) / 2, (468 + 824) / 2
    c.line([(CX, y + 4), (CX, y + 30)]); c.line([(L, y + 30), (R, y + 30)]); c.arrow(L, y + 30, L, y + 60); c.arrow(R, y + 30, R, y + 60)
    y += 64
    double(64, 420, y, '符合规则', '进入后续处理')
    y = double(468, 824, y, '异常情况', '交给负责人', mc=CLAYT, outline=CLAY, fill='#F6E3DA')
    c.line([(L, y + 4), (L, y + 30)]); c.line([(R, y + 4), (R, y + 30)]); c.line([(L, y + 30), (R, y + 30)]); c.arrow(CX, y + 30, CX, y + 60)
    y += 64
    y = single(y, 428, '跟踪交付结果')
    c.arrow(CX, y + 8, CX, y + 56); y += 64
    b5 = y; y = single(y, 428, '记录常见问题')
    c.dashed([(CX + 214, b5 + 65), (936, b5 + 65), (936, b2 + 94), (CX + 238, b2 + 94)], CLAY)
    c.arrow(CX + 262, b2 + 94, CX + 236, b2 + 94, w=5, fill=CLAY, head=20)
    c.vtext('改进依据', W - M - SIZE['sub'], (b2 + 94 + b5 + 65) / 2, 'sub', CLAYT)
    y += 56; c.line([(M + 2, y), (W - M - 2, y)], 3); y += 40
    for i, (top, bottom, arrow) in enumerate([('处理时间', '缩短', '↓'), ('错误率', '下降', '↓'), ('交付', '更准时', '↑')]):
        cx = M + (W - 2 * M) / 6 * (2 * i + 1)
        c.text(top, cx, y, 'sub', SUBC, 'c')
        b = c.text(bottom, cx - 18, y + SIZE['sub'] + 22, 'main', INK, 'c')
        c.text(arrow, b[2] + 10, y + SIZE['sub'] + 26, 'main', CLAYT)
    return c.finish('图4_订单流程')

if __name__ == '__main__':
    head(); tree(); loop(); flow()
