"""Paste-ready WeChat HTML in the tuned replica style. Every style is inline (the WeChat editor drops style tags and classes).
Usage: build_html.py marked.txt out.html art_dir [version label]
Marked text: blocks separated by blank lines. "# title", "## key|一级标题", "### NN|key|二级标题", "**重点**",
"@@IMG name" (art_dir/name.png; a dashed placeholder if missing, labels from placeholders.txt "name|说明" next to the marked text),
"@@QUOTE 引用文字" for the gray quote box (every "|" marks a manual line break),
"@@REFS" then "@@REF 参考资料条目" lines and one "@@NOTE 注释"."""
import base64, html, os, re, sys

SRC, OUT, ART = sys.argv[1], sys.argv[2], sys.argv[3]
VERSION = sys.argv[4] if len(sys.argv) > 4 else ''
BAR, RED, INK, HEAD, QBG, QLINE, QINK = '#F0382A', '#E0301E', '#222222', '#111111', '#F2F2F2', '#D9D9D9', '#3A3A3A'
BODY_FONT = "Optima-Regular, Optima, PingFangSC-light, PingFangTC-light, 'PingFang SC', Cambria, Cochin, Georgia, Times, 'Times New Roman', serif"
HEAD_FONT = "Optima-Regular, Optima, PingFangSC-Regular, 'PingFang SC', 'Microsoft YaHei', sans-serif"
QFONT = "Georgia, 'Times New Roman', Times, 'Liberation Serif', 'Noto Serif', serif"
QMARK = base64.b64encode(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'quote-mark.png'), 'rb').read()).decode()
QPAD_TOP, QMARK_GAP = 22, 36   # reference: mark 22px below the box top, about 39px above the text
# heading spacing (CSS px margins), tuned against measured ink gaps
H2_ABOVE, H2_BELOW, H3_ABOVE, H3_ABOVE_IMG, H3_BELOW = 42, 37, 38, 44, 27
P = f"margin:0 0 16px 0;padding:0;font-family:{BODY_FONT};font-size:17px;line-height:1.56;letter-spacing:0.5px;color:{INK};text-align:justify;overflow-wrap:break-word;word-wrap:break-word;"

blocks = [b.strip() for b in re.split(r'\n\s*\n', open(SRC, encoding='utf8').read()) if b.strip()]
TITLE = next(b[2:] for b in blocks if b.startswith('# '))

# Line rule, enforced by structure instead of by editing the copy: the last LOCK characters of every block
# (plus the punctuation around them) sit in one white-space:nowrap span, so on ANY screen width the last line
# keeps at least two characters, and a closing mark can never be left alone on a line.
# Counting: punctuation (opening marks included) does not count; a run of Latin letters or digits counts as
# one character when it has 1 or 2 of them ("AI") and as two when it has 3 or more ("GitHub").
LOCK = 2
# keep PUNCT in selfcheck.py and htmlcheck.py identical to TAIL_PUNCT
TAIL_PUNCT = set('，。、；：？！…—）」』》〉】〕］｝”’,.;:?!)]%～·「『《〈【〔［｛“‘（(["\'')
OPENING = set('「『《〈【〔［｛“‘（(["\'')     # kept with the character after them

def latin(c):
    return c.isascii() and c.isalnum()

def render(segments, lock=True):
    """segments: [(text, inline style or None)] -> HTML; with lock, the tail is wrapped in a nowrap span."""
    chars = [(c, st) for t, st in segments for c in t]
    cut = len(chars)
    if lock:
        n = 0
        while cut > 0:
            c = chars[cut - 1][0]
            if c.isspace() or c in TAIL_PUNCT:
                cut -= 1
                continue
            if n >= LOCK:
                break
            if latin(c):                       # a Latin word or number never breaks inside; count it as a unit
                j = cut
                while j > 0 and latin(chars[j - 1][0]):
                    j -= 1
                n += 2 if cut - j >= 3 else 1
                cut = j
            else:
                n += 1
                cut -= 1
        if n < LOCK:           # block too short to need it
            cut = len(chars)
        while cut < len(chars) and (chars[cut][0].isspace() or (chars[cut][0] in TAIL_PUNCT and chars[cut][0] not in OPENING)):
            cut += 1           # a space or closing mark in front of the tail stays outside, so the line may break before it
    def runs(cs):
        out, cur, buf = [], None, ''
        for c, st in cs + [(None, '__end__')]:
            if st != cur and buf:
                out.append(f'<span style="{cur}">{html.escape(buf)}</span>' if cur else html.escape(buf))
                buf = ''
            cur = st
            if c is not None:
                buf += c
        return ''.join(out)
    head, tail = chars[:cut], chars[cut:]
    return runs(head) + (f'<span style="white-space:nowrap;">{runs(tail)}</span>' if tail else '')

def inline(text):
    parts = text.split('**')
    return render([(t, f'color:{RED};' if i % 2 else None) for i, t in enumerate(parts) if t])

def head_runs(title):
    # Latin words bold (as in the reference), Chinese regular; colour set on the text itself; tail locked like body text
    return render([(t, f'font-weight:bold;color:{HEAD};' if re.fullmatch(r'[A-Za-z0-9]+', t) else None)
                   for t in re.split(r'([A-Za-z0-9]+)', title) if t])

def divider(top=30, bottom=30):
    return (f'<hr style="margin:{top}px 8px {bottom}px 8px;border:0;height:1px;'
            'background-image:linear-gradient(to right, rgba(226,112,98,0), rgba(226,112,98,0.9), rgba(226,112,98,0));" />')

parts = []
refs = []
PLACEHOLDER = {}
PH_FILE = os.path.join(os.path.dirname(os.path.abspath(SRC)), 'placeholders.txt')   # next to the marked text,
if not os.path.exists(PH_FILE):                                                        # else the current folder
    PH_FILE = 'placeholders.txt'
if os.path.exists(PH_FILE):
    PLACEHOLDER = dict(l.strip().split('|', 1) for l in open(PH_FILE, encoding='utf8') if '|' in l)
prev_img = False
pending_after_box = False
for b in blocks:
    if b.startswith('# ') or b == '@@PREFACE_END':
        continue
    prev_img, was_img = False, prev_img
    if b == '@@REFS':
        continue
    if b.startswith('@@REF ') or b.startswith('@@NOTE '):
        refs.append(b)
        continue
    m = re.match(r'^@@IMG (\w+)$', b)
    if m and not os.path.exists(f'{ART}/{m.group(1)}.png'):
        # image not generated yet: a clearly marked placeholder that must be replaced before publishing
        parts.append(f'<section style="margin:4px 0 20px 0;padding:56px 16px;border:2px dashed #D9D9D9;background-color:#FAFAFA;text-align:center;">'
                     f'<p style="margin:0;font-family:{HEAD_FONT};font-size:14px;line-height:1.6;color:#999999;">【配图位置】{html.escape(PLACEHOLDER.get(m.group(1), m.group(1)))}<br />生成后替换，发布前删除这个框</p></section>')
        prev_img = True
        continue
    if m:
        data = base64.b64encode(open(f'{ART}/{m.group(1)}.png', 'rb').read()).decode()
        parts.append(f'<p style="margin:4px 0 20px 0;padding:0;text-align:center;line-height:0;">'
                     f'<img src="data:image/png;base64,{data}" alt="" style="display:block;width:100%;max-width:100%;height:auto;margin:0 auto;" /></p>')
        prev_img = True
        continue
    m = re.match(r'^## [^|]+\|(.+)$', b)
    if m:
        parts.append(divider(30, H2_ABOVE))
        parts.append(f'<h2 style="margin:0 0 {H2_BELOW}px 0;padding:0 0 0 12px;border-left:5px solid {BAR};'
                     f'font-family:{HEAD_FONT};font-size:19px;font-weight:normal;line-height:23px;letter-spacing:0.6px;color:{HEAD};">'
                     f'{head_runs(m.group(1))}</h2>')
        continue
    m = re.match(r'^### \d+\|[^|]+\|(.+)$', b)
    if m:
        parts.append(f'<h3 style="margin:{H3_ABOVE_IMG if was_img else H3_ABOVE}px 0 {H3_BELOW}px 0;padding:0;font-family:{HEAD_FONT};font-size:17px;font-weight:normal;'
                     f'line-height:28px;letter-spacing:0.5px;color:{HEAD};">{head_runs(m.group(1))}</h3>')
        continue
    if b.startswith('@@QUOTE '):
        q = b[8:]
        parts.append(f'<section style="margin:10px 0 24px 0;padding:{QPAD_TOP}px 16px 16px 17px;background-color:{QBG};border-left:3px solid {QLINE};">'
                     f'<p style="margin:0 0 {QMARK_GAP}px 0;padding:0;line-height:0;font-size:0;"><img src="data:image/png;base64,{QMARK}" alt="“" width="12" style="display:block;width:11.6px;height:9.6px;margin:0 0 0 1px;padding:0;" /></p>'
                     f'<p style="margin:0;padding:0;font-family:{BODY_FONT};font-size:17px;line-height:1.56;letter-spacing:0.5px;color:{QINK};overflow-wrap:break-word;word-wrap:break-word;">'
                     + '<br />'.join(render([(t, None)]) for t in q.split('|')) + '</p></section>')
        continue
    # a Latin word of 8+ letters stretches justified CJK lines badly, so such paragraphs are left-aligned
    style = P.replace('text-align:justify;', 'text-align:left;') if re.search(r'[A-Za-z][A-Za-z-]{7,}', b) else P
    parts.append(f'<p class="bp" style="{style}">{inline(b)}</p>')
parts.append(divider(16, 22))
parts.append(f'<p style="{P.replace("color:" + INK, "color:" + RED)}font-style:italic;">{render([("全文完", None)])}</p>')
if refs:
    SMALL = f"padding:0;font-family:{BODY_FONT};letter-spacing:0.3px;color:#8C8C8C;text-align:left;overflow-wrap:break-word;word-wrap:break-word;"
    parts.append(f'<p style="margin:30px 0 10px 0;padding:0;font-family:{HEAD_FONT};font-size:15px;line-height:1.6;letter-spacing:0.5px;color:#8C8C8C;">{render([("参考资料", None)])}</p>')
    for r in refs:
        if r.startswith('@@REF '):
            # keep a trailing date (2024年, 2024年3月, 2024年3月5日) together; any other entry gets the normal tail lock
            item = r[6:]
            m = re.search(r'(\d{4}年(?:\d{1,2}月(?:\d{1,2}日)?)?[。.]?)$', item)
            ref = (html.escape(item[:m.start()]) + f'<span style="white-space:nowrap;">{html.escape(m.group(1))}</span>') if m else render([(item, None)])
            parts.append(f'<p class="bp" style="margin:0 0 6px 0;{SMALL}font-size:14px;line-height:1.6;">{ref}</p>')
        else:
            parts.append(f'<p class="bp" style="margin:14px 0 0 0;{SMALL.replace("color:#8C8C8C;", "color:#A0A0A0;")}font-size:13px;line-height:1.6;font-style:italic;">{render([(r[7:], None)])}</p>')

article = '\n'.join(parts)
page = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITLE)}</title>
</head>
<body style="margin:0;background:#EDEDED;font-family:-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;">
<div id="bar" style="position:sticky;top:0;z-index:2;background:#1E2226;color:#EFE8DC;padding:12px 16px;font-size:14px;line-height:1.6;">
  <button id="copy" type="button" style="font-size:15px;padding:8px 18px;border:0;border-radius:6px;background:#F0382A;color:#fff;cursor:pointer;">复制到公众号</button>
  <span style="margin-left:12px;padding:2px 8px;border:1px solid #F0382A;border-radius:4px;color:#F0382A;">{html.escape(VERSION)}</span>
  <span id="msg" style="margin-left:12px;">点按钮复制正文，到公众号编辑器里粘贴。标题请填在公众号的标题栏。</span>
</div>
<div style="max-width:402px;margin:24px auto 60px auto;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,.08);">
  <div style="padding:22px 16px 6px 16px;">
    <div style="font-size:22px;font-weight:bold;line-height:1.5;color:#1A1A1A;">{html.escape(TITLE)}</div>
    <div style="margin-top:8px;font-size:14px;color:#B2B2B2;">以下为正文（复制范围）</div>
  </div>
  <div style="padding:14px 16px 24px 16px;">
<section id="article" style="padding:0 14px;">
{article}
</section>
  </div>
</div>
<script>
document.getElementById('copy').addEventListener('click', async function () {{
  var node = document.getElementById('article');
  var msg = document.getElementById('msg');
  try {{
    var htmlText = node.outerHTML;
    if (navigator.clipboard && window.ClipboardItem) {{
      await navigator.clipboard.write([new ClipboardItem({{
        'text/html': new Blob([htmlText], {{ type: 'text/html' }}),
        'text/plain': new Blob([node.innerText], {{ type: 'text/plain' }})
      }})]);
    }} else {{ throw new Error('no clipboard api'); }}
  }} catch (e) {{
    var range = document.createRange(); range.selectNode(node);
    var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
    try {{ document.execCommand('copy'); }} catch (e2) {{}}
    sel.removeAllRanges();
  }}
  msg.textContent = '已复制，去公众号编辑器粘贴。如果图片没跟过去，在原位置重新插入即可。';
}});
</script>
</body>
</html>
'''
open(OUT, 'w', encoding='utf8').write(page)
print('wrote', OUT, len(page) // 1024, 'KB')
