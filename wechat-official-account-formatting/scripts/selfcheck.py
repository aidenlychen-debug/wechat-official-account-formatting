"""Structural check of a built article that needs only Python 3 (no browser, no extra packages).

Use it everywhere, and on its own when Playwright or Chrome is not available (for example in Claude's web app).
It confirms what build_html.py promises; htmlcheck.py then measures real lines when a browser is available.

Usage: selfcheck.py article.html [marked.txt]
Checks:
  1. the copy area (#article) uses inline styles only: no <style>, <link>, <script>, no class other than "bp"
  2. mandatory left visual alignment with the article title: #article has zero horizontal padding (padding:0)
     and dividers (<hr>) have zero horizontal margin so title, headings, body, quotes, and images share one left axis
  3. every text block (paragraph, heading, quote line, reference) ends in a locked tail: a white-space:nowrap span
     holding at least two characters, so its last line can never be a single character or bare punctuation.
     Counting as in build_html.py: punctuation does not count; a run of Latin letters or digits counts as one
     character with 1 or 2 of them ("AI") and as two with 3 or more ("GitHub"). A locked tail that adds more
     than 12 unbreakable characters fails too (a Latin word that cannot break anyway is not counted).
  4. images are embedded (data URIs); dashed placeholder boxes still waiting for an image are listed
  5. the page shows a version label ("第 N 版")
  6. no em dash (——) in the article text
  7. editorial de-numbering check: H2/H3 headings must not carry leading numeric/ordinal prefixes (01｜, 一、, 1., 第一，),
     and body paragraphs must not carry stiff ordinal numbering (leading 一、/第一， or paired 第一…第二… chains)
  8. with marked.txt: the article text is exactly the marked text (markup and markers ignored)
Exit code 0 when everything passes, 1 otherwise."""
import html, re, sys
from html.parser import HTMLParser

PUNCT = set('，。、；：？！…—）」』》〉】〕］｝”’,.;:?!)]%～·「『《〈【〔［｛“‘（(["\' ')          # same as TAIL_PUNCT in build_html.py, plus space
MAX_TAIL = 12

def latin(c):
    return c.isascii() and c.isalnum()

def units(seg):
    """[(weight, locked)] for the characters that count, in order"""
    out, i = [], 0
    while i < len(seg):
        c, lk = seg[i]
        if latin(c):
            j = i
            while j < len(seg) and latin(seg[j][0]):
                j += 1
            out.append((2 if j - i >= 3 else 1, all(l for _, l in seg[i:j]))); i = j; continue
        if c not in PUNCT and not c.isspace():
            out.append((1, lk))
        i += 1
    return out
SRC = open(sys.argv[1], encoding='utf8').read()
start = SRC.find('<section id="article"')
if start < 0:
    sys.exit('FAIL: no <section id="article"> in the page')
end = SRC.rfind('</section>\n  </div>')
ART = SRC[start:end if end > start else len(SRC)]

class Blocks(HTMLParser):
    """Collect text blocks; for each, the text of every segment between <br> and whether it ends inside a nowrap span."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.blocks, self.cur, self.bad_tags, self.classes, self.imgs = [], [], None, [], set(), []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('style', 'link', 'script'):
            self.bad_tags.append(tag)
        if a.get('class'):
            self.classes.add(a['class'])
        if tag == 'img':
            self.imgs.append(a.get('src', '')[:30])
            if self.cur is not None:
                self.cur['img'] = True
        if tag in ('p', 'h2', 'h3'):
            self.cur = {'tag': tag, 'segs': [[]], 'img': False}
        elif tag == 'br' and self.cur is not None:
            self.cur['segs'].append([])
        if tag not in ('br', 'img', 'hr'):
            self.stack.append('white-space:nowrap' in (a.get('style') or ''))
    def handle_endtag(self, tag):
        if tag not in ('br', 'img', 'hr') and self.stack:
            self.stack.pop()
        if tag in ('p', 'h2', 'h3') and self.cur is not None:
            self.blocks.append(self.cur); self.cur = None
    def handle_data(self, data):
        if self.cur is not None and data:
            locked = any(self.stack)
            self.cur['segs'][-1].extend((c, locked) for c in data)

b = Blocks(); b.feed(ART)
fails, notes = [], []
if b.bad_tags:
    fails.append(f'tags that WeChat drops inside the copy area: {sorted(set(b.bad_tags))}')
if b.classes - {'bp'}:
    fails.append(f'classes inside the copy area (styles must be inline): {sorted(b.classes - {"bp"})}')
# Check mandatory left visual alignment with title: #article must not add horizontal padding, and <hr> must have 0 horizontal margin
art_open = re.search(r'<section\s+id="article"[^>]*>', ART)
art_style = re.search(r'style="([^"]*)"', art_open.group(0)).group(1) if art_open and re.search(r'style="([^"]*)"', art_open.group(0)) else ''
if not re.search(r'(?:^|;)\s*padding\s*:\s*0(?:px)?(?:\s+0(?:px)?)?\s*(?:;|$)', art_style):
    fails.append(f'#article must enforce padding:0 for strict left alignment with title (got style="{art_style}")')
for hr_m in re.finditer(r'<hr\s+[^>]*style="([^"]*)"', ART):
    m_mar = re.search(r'margin\s*:\s*([^;"]+)', hr_m.group(1))
    if m_mar:
        toks = m_mar.group(1).strip().split()
        if (len(toks) == 2 and toks[1] not in ('0', '0px')) or (len(toks) == 4 and (toks[1] not in ('0', '0px') or toks[3] not in ('0', '0px'))):
            fails.append(f'<hr> horizontal margin must be 0 for strict left alignment (got margin:{m_mar.group(1)})')

HEADING_ORD_RE = re.compile(
    r'^(?:'
    r'(?:0?\d{1,2})\s*[｜|、.．:：]\s*'
    r'|[一二三四五六七八九十]+[、.．:：｜|]\s*'
    r'|[（(][一二三四五六七八九十\d]+[）)]\s*'
    r'|第[一二三四五六七八九十\d]+[章节点部分条步个项，、：:\s]'
    r')'
)
BODY_LEAD_ORD_RE = re.compile(
    r'^(?:'
    r'第[一二三四五六七八九十\d]+[，、：:\s]'
    r'|[一二三四五六七八九十]+[、.．]\s*'
    r'|\d+[、.．]\s*'
    r'|[（(][一二三四五六七八九十\d]+[）)]\s*'
    r')'
)
BODY_CHAIN_ORD_RE = re.compile(r'第[一二三四五六七八九十]+[，、：:]')
checked = 0
for blk in b.blocks:
    if blk['img']:
        continue
    full_blk_text = ''.join(''.join(c for c, _ in s) for s in blk['segs']).strip()
    if blk['tag'] in ('h2', 'h3') and HEADING_ORD_RE.match(full_blk_text):
        fails.append(f'heading must not start with numeric/ordinal prefix in <{blk["tag"]}>: {full_blk_text[:24]}')
    if blk['tag'] == 'p' and full_blk_text and not full_blk_text.startswith('【配图位置】') and not full_blk_text.startswith('注：'):
        if BODY_LEAD_ORD_RE.match(full_blk_text):
            fails.append(f'body paragraph starts with ordinal prefix (preprocess into natural prose): {full_blk_text[:24]}')
        elif len(BODY_CHAIN_ORD_RE.findall(full_blk_text)) >= 2:
            fails.append(f'body paragraph contains chained ordinals (第一/第二…) — preprocess into natural prose: {full_blk_text[:28]}')
    for seg in blk['segs']:
        text = ''.join(c for c, _ in seg).strip()
        if not text or text.startswith('【配图位置】') or text.startswith('生成后替换'):
            continue
        us = units(seg)
        if sum(w for w, _ in us) <= 2:
            continue                         # too short to break
        checked += 1
        need, ok = 0, True
        for w, lk in reversed(us):           # the last units worth two characters must be locked
            ok = ok and lk; need += w
            if need >= 2:
                break
        tail_punct = [lk for c, lk in reversed(seg) if not c.isspace()][:1]
        if not ok or not all(tail_punct):
            fails.append(f'tail not locked in <{blk["tag"]}>: …{text[-16:]}')
        tail = []
        for c, lk in reversed(seg):
            if not lk:
                break
            tail.append(c)
        tail = ''.join(reversed(tail))
        runs = re.findall(r'[A-Za-z0-9]+', tail)
        added = len(re.sub(r'\s', '', tail)) - max((len(r) for r in runs), default=0)   # a Latin word never breaks anyway
        if added > MAX_TAIL:
            fails.append(f'locked tail adds {added} characters that cannot break; it may run past the edge of a narrow phone: …{text[-16:]}')
placeholders = re.findall(r'【配图位置】([^<]+)', ART)
embedded = sum(1 for s in b.imgs if s.startswith('data:image'))
if any(not s.startswith('data:image') for s in b.imgs):
    fails.append('images that are not embedded (remote or local src)')
if not re.search(r'第 ?\d+ ?版', SRC):
    fails.append('no version label (第 N 版) on the page')
visible = html.unescape(re.sub(r'<[^>]+>', '', ART))
if '——' in visible:
    fails.append('em dash (——) in the article text')
if len(sys.argv) > 2:
    marked = open(sys.argv[2], encoding='utf8').read()
    body, refs = [], []
    for blk in re.split(r'\n\s*\n', marked):
        blk = blk.strip()
        if not blk or blk.startswith('# ') or blk.startswith('@@IMG') or blk in ('@@PREFACE_END', '@@REFS'):
            continue
        if blk.startswith('@@REF ') or blk.startswith('@@NOTE '):
            refs.append(re.sub(r'^@@(?:REF|NOTE) ', '', blk, flags=re.M).replace('**', ''))
            continue
        blk = re.sub(r'^(?:##|###) (?:\d+\|)?[^|]+\|', '', blk)
        if blk.startswith('@@QUOTE '):
            blk = blk[8:].replace('|', '')          # in a quote, "|" is a manual line break
        body.append(blk.replace('**', ''))
    # the page adds 全文完 after the body, and the 参考资料 heading before the references
    want = re.sub(r'\s+', '', ''.join(body) + '全文完' + ('参考资料' + ''.join(refs) if refs else ''))
    got = re.sub(r'\s+', '', visible)
    got = re.sub(r'【配图位置】[^生]*生成后替换，发布前删除这个框', '', got)
    if want != got:
        i = next((k for k, (x, y) in enumerate(zip(want, got)) if x != y), min(len(want), len(got)))
        fails.append(f'article text differs from the marked text near: …{want[max(0, i - 12):i + 12]}… vs …{got[max(0, i - 12):i + 12]}…')
print(f'blocks with a locked tail checked: {checked}; embedded images: {embedded}; placeholders still open: {len(placeholders)}')
for p in placeholders:
    print('   WARNING placeholder still open, replace it with the image before publishing:', p)
for f in fails:
    print('FAIL', f)
print('PASS' if not fails else f'{len(fails)} problem(s)')
sys.exit(1 if fails else 0)
