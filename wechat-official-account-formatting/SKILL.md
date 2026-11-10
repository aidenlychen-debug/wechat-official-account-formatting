---
name: wechat-official-account-formatting
description: 把中文文章排成可直接粘贴进微信公众号的版式（A社风格），并生成配图和封面：Claude 连了生图工具就直接生图，没连时在 Claude Code 里写生图指令交给同一项目文件夹里的 ChatGPT Work，在 ChatGPT Work 里直接生图；断行在任何手机宽度下都不出单字；交付前由独立检查方逐项复查。
---

# WeChat Official Account Formatting Skill

> 许可：CC BY-NC 4.0（https://creativecommons.org/licenses/by-nc/4.0/），完整条款见同目录的 LICENSE。非商业用途（包括个人的非商业使用）免费，商业用途需要授权，详见项目 README 的「许可与授权」。

把一篇中文文章排成公众号版式：可直接粘贴的 HTML、标题、引用块、配图位置，以及配图和封面的生图要求。后面的版式参数是逐项调好的默认值。

## 流程

1. **标记原文**：按第 9 节的标记写法把原文写成标记稿（`assets/sample_marked.txt` 是一份完整示例）。只加标记，不改字。文中的人名写进同目录的 `terms.txt`，排版时整体不拆行（第 5 节）。
2. **排版**：`python3 scripts/build_html.py 标记稿.txt 文章_vN.html art "第 N 版"`。只需要 Python 3。
3. **自查**：`python3 scripts/selfcheck.py 文章_vN.html 标记稿.txt` 必须 PASS；有 Playwright 和 Chrome 时，再跑 `python3 scripts/htmlcheck.py 文章_vN.html`，TOTAL issues 必须是 0，然后跑 `python3 scripts/phonecheck.py 文章_vN.html`，看小屏和大屏两种宽度。
4. **内文配图**：按 `references/images.md` 第 9 节的三种方式之一生成（连了生图工具就直接生图；在 Claude Code 里写生图指令交给 ChatGPT Work；在 ChatGPT Work 里直接生图），图片放进 art 文件夹，用 `@@IMG 名字` 引用。
5. **封面**：按 `references/cover.md` 出四张不同风格的封面给用户挑，单独一份封面生图要求，和内文配图分开生成，垫图用同一套。
6. **独立检查**：按 `references/checklist.md`，另开一个没看过制作过程的检查方，最多 3 轮。
7. **交付**：文件带版本号，附检查结果表。

## 0. 总原则

- **不改原文。** 断行规则由排版脚本保证（第 5 节），不需要为断行改字。字距不均时可以微调表述（第 5 节）。用户另外要求改字时，每处改动都要列给用户：从什么改成什么。
- 回复用口语化中文，不用破折号。
- **每次交付都带版本号**：文件名加 `_vN`，页面顶部也标「第 N 版」。同名文件再次下载时，浏览器会自动改名，用户很容易贴错版本。
- 用户发截图反馈时，先量截图再改：用像素算出比例，判断贴的是哪一版、用的是什么字体。Windows 电脑上没有苹方，标题会换成微软雅黑，正文会换成宋体加 Cambria，字在行里的位置和苹果设备不一样。
- 用户说「不好看，不做了」，就撤掉，不再推荐。重点句下面不加荧光笔底色。

## 1. 交付形式

- **默认交付一个 HTML 文件，所有样式都写在元素的 style 属性上。** 公众号编辑器会丢掉 style 标签和 class，只保留内联样式。
- 页面顶部放一个「复制到公众号」按钮：用 ClipboardItem 同时写 text/html 和 text/plain，失败时退回 `execCommand('copy')`。复制范围只包含 id 为 article 的正文 section。按钮旁边标版本号。
- 文章标题显示在复制范围外面，并提示用户填进公众号的标题栏。
- 配图用 base64 嵌进 img 标签，粘贴时公众号会自动上传。如果有图没跟过去，告诉用户在原位置重新插入。
- **不要经过 MarkNice 一类的转换工具。** 它会把 Word 转成 Markdown 再套自己的模板，会改掉竖线和重点的颜色，丢掉边框、缩进和本地图片。
- 用户明确要 Word 时，做一份干净的语义化 Word：只用内置标题 2 和标题 3、加粗、引用样式、斜体和内嵌图片，不放边框、底纹、缩进和直接颜色。同时说明颜色和竖线要靠转换工具的模板，不可控。Word 里没有尾字锁定，断行规则只在 HTML 版里保证，发布以 HTML 版为准。

## 2. 版式参数（默认值）

- **字体栈**
  - 正文：`Optima-Regular, Optima, PingFangSC-light, PingFangTC-light, 'PingFang SC', Cambria, Cochin, Georgia, Times, 'Times New Roman', serif`
  - 标题：`Optima-Regular, Optima, PingFangSC-Regular, 'PingFang SC', 'Microsoft YaHei', sans-serif`
- **正文容器**：id 为 article 的 section，style 是 `padding:0 14px;`。公众号自带两侧各 16px，所以文字区宽度是手机宽度减 60px，比如 375 宽的手机上是 315px，390 宽的是 330px，430 宽的是 370px。成品页面按 402 宽的小屏手机预览（文字区 342px），交付前再确认 440 宽的大屏（文字区 380px）。

| 元素 | 内联样式要点 |
|---|---|
| 正文段落 | margin 0 0 16px；17px；line-height 1.56；letter-spacing 0.5px；color #222222；两端对齐；overflow-wrap break-word（长网址放不下时才折开） |
| 尾字锁定 | 每段、每个标题、引用块的每一行、参考资料的每一条，最后两个字连同后面的标点放进 `<span style="white-space:nowrap;">`，见第 5 节 |
| 专有名词 | 人名、带空格的英文名、《》「」里的短词，整个放进 nowrap span，不拆到两行，见第 5 节 |
| 含长英文的段落 | 段落里有 8 个字符以上的英文词（连字符也算，如 Markdown、Combinator、AI-Native）时改成左对齐，否则两端对齐会把中文拉散 |
| 英文专名里的单个字母 | 和后面的词用不换行空格（U+00A0）连起来，比如 Y Combinator，人名缩写也一样，比如 Michael E. Porter，避免单个字母留在行尾 |
| 重点 | span 加 `color:#E0301E;`，不加粗，不加荧光笔底色 |
| 一级标题（带竖线） | margin 0 0 37px 0；padding-left 12px；border-left 5px solid #F0382A；19px；font-weight normal；line-height 23px（竖线和字差不多高）；letter-spacing 0.6px；color #111111 |
| 一级标题里的英文和数字（如 AI） | 单独用 span，font-weight bold，color #111111，不跟红色 |
| 一级标题前的分隔线 | hr 标签：margin 30px 8px 42px 8px；border 0；height 1px；background-image 是 linear-gradient(to right, rgba(226,112,98,0), rgba(226,112,98,0.9), rgba(226,112,98,0)) |
| 二级标题 | margin 38px 0 27px 0（紧跟在图片后面时上边距用 44px）；17px；font-weight normal；line-height 28px；color #111111 |
| 配图 | 外层 p：margin 4px 0 20px；line-height 0。img：display block；width 100%；height auto |
| 引用块 | section：margin 10px 0 24px；padding 22px 16px 16px 17px；background #F2F2F2；border-left 3px solid #D9D9D9。里面先放引号图片，再放文字：17px，line-height 1.56，color #3A3A3A，需要时用 br 标签手动断句 |
| 引号 | 用代码画成小图片：两个斜着的水滴，下圆上尖，向右上倾斜约 22°，整体 11.6 × 9.6px，颜色 #F0382A。按 4 倍分辨率画成 PNG，base64 嵌入，宽 11.6px，左边距 1px，下面离文字 36px。原版用的 Optima 引号，Windows 上没有这个字体，所以不能直接用字符 |
| 结尾 | 一条分隔线（margin 16px 8px 22px），下面一行「全文完」：正文样式，color #E0301E，斜体 |
| 参考资料 | 放在「全文完」后面：「参考资料」15px 灰色 #8C8C8C；每条 14px、左对齐、灰色；注释 13px 斜体 #A0A0A0。条目末尾的年份或日期整段锁在一起，不让「年。」单独掉到下一行 |
| 配图占位 | 图还没生成时，用虚线占位框标出位置和图名，写明「生成后替换，发布前删除这个框」 |

## 3. 间距规则

第 2 节的默认值是对照电脑版公众号的截图调出来的。不同系统的字体不一样（比如 Windows 上标题是微软雅黑，正文是宋体加 Cambria），量出来的比例会有出入，所以判断时以用户的截图为准；没有截图时，只核对 CSS 数值和第 2 节一致。`scripts/gapmeasure.py` 可以量页面上的实际空白。

**怎么量**：一律量两行字之间实际看到的空白，单位是 px。

- 段落空白：上一段最后一行字的底端，到下一段第一行字的顶端。CSS 是 16px，实际看到约 26px。
- 小标题上方：上一段文字底端到小标题文字顶端；小标题下方：小标题文字底端到下一段文字顶端。
- 分隔线上方：上一段文字底端到横线；分隔线下方：横线到竖线顶端。
- 竖线标题下方：标题文字底端到下一段文字顶端。

**比例**（逐条调定的，允许 ±0.05）：

- 小标题下方比段落空白至少多半个字，约 8 到 9px；上方明显大于下方，和上一段形成区隔。
- 分隔线下方是分隔线上方的 1.2 倍。
- 竖线标题下方是小标题下方的 1.2 倍。

**调整**：用户说「多 1/5」「加 1/4」，就在当前看到的空白上乘以 1.2 或 1.25，只改用户点名的那一处。段落之间的 16px 没有点名不要动。

## 4. 标题

- 一级和二级标题优先用「四字：四字」的对仗格式，越简单越好，但要能看懂，整体视觉对齐。
  - 一级标题例子：传统公司：经验难留 / AI 原生：经验沉淀 / 如何开始：先选流程
  - 二级标题例子：信息感知：看见业务 / 规则判断：划清边界
- **不为了凑对仗硬加词。** 后半句读起来突兀时就去掉。结尾一节直接用「写在最后」，不加后半句。
- 原文有小节就沿用原文的意思，不另起内容。原文自带的标题照原文用，不改成四字对仗。
- 标题最好一行放下。尾字锁定能保证折行时最后一行不止一个字，但两行的标题不好看，太长时去掉「一、」「二、」这类编号；要去就所有标题一起去，保持一致。

## 5. 断行

**规则**：段落最后一行至少两个字加标点，不能只有一个字；任何一行都不能只有标点。

**为什么不能靠改字解决**：读者的手机宽度各不相同。文字区从 315px（375 宽的手机）到 370px（430 宽的手机）都有，安卓手机还会换成宋体一类的衬线字体。为某一种宽度删一个字，换一台手机就又掉出一个单字；只检查一两种宽度，等于没检查。

**怎么保证**：`build_html.py` 自动做**尾字锁定**：每一段、每个标题、引用块的每一行（每个 br 分隔的片段）、参考资料的每一条，把最后两个字连同后面的标点放进一个 `white-space:nowrap` 的 span。这样不管屏幕多宽，最后一行至少有这两个字；收尾的标点也一定跟着前面的字。

- 计数时标点不算。开引号、书名号、括号跟着后面的字一起锁，比如「叫“好”。」整个锁在一起。
- 英文单词和数字整个算：一两个字母（比如 AI）算 1 个字，3 个字母以上（比如 GitHub）算 2 个字。
- 参考资料末尾的日期（2024年、2024年3月、2024年3月5日）整个锁在一起。
- 锁住的部分里，除去一个本来就不能断开的英文单词，再多出 12 个字以上时，selfcheck 会报错：这一段不能换行，窄屏上可能超出边界。
- 很长的英文单词和网址本来就不能断开，正文、引用和参考资料都带 `overflow-wrap:break-word`，放不下时在词中间折行，不会撑出屏幕。

**专有名词不拆行**：「Genie 4」拆成「Genie」和「4」两行、「李飞飞」拆成「李」和「飞飞」，读起来很割裂。`build_html.py` 会把专有名词整个放进 `white-space:nowrap` 的 span，放不下时整个挪到下一行。

- 自动锁定：中间带空格的英文名（Genie 4、World Labs、Google DeepMind），以及《》「」里不超过 8 个字的词（《GTA》、「AI 教母」）。
- 人名写进标记稿同目录的 `terms.txt`，一行一个，# 开头是注释。
- 只锁名字，不讲究到每个词。常用词（机器人、自动驾驶）和概念词（世界模型）不锁，断成「世界」和「模型」也能读。
- 尾字锁定碰到专有名词时，往前多锁一点，把整个名词一起锁进去，不会把名词切成两半。
- 代价：名词整个挪到下一行时，上一行会空出这个名词的宽度，两端对齐把它分摊到字距里，这一行字距会变宽。锁的词越多越长，这样的行越多，所以只锁名字。

**字距统一**：两端对齐会把一行末尾空出来的位置分摊到字距里。一行少排了一个字（名字整个挪下去、句号逗号不能放行首、尾字锁定带走两个字），这一行就比别的行松，看起来很怪。

- `python3 scripts/phonecheck.py 文章_vN.html` 按 402 宽的小屏和 440 宽的大屏渲染，名词拆开、尾行单字和字距不均（uneven）都必须是 none。
- 有 uneven 的行，就微调这一段的表述，让这一行排满或者让下一行接上：删一个可有可无的字、换个等长或差一两个字的说法，比如「原因在于」改成「原因是」、「刚刚发布了」改成「刚发布」、「准确预测」改成「准确地预测」。一处改动要同时照顾小屏和大屏，改完两种宽度都重查。
- 只动措辞，不改意思，不加新内容。每处改动列给用户：从什么改成什么。

公众号编辑器保留内联样式，粘贴后应该同样有效。第一次用、或者公众号编辑器更新以后，粘贴到后台用手机预览看一眼（360 或 414 宽的手机最容易出单字）。浏览器的避头尾规则本来就不会让一行以句号、逗号这类标点开头，所以段落中间也不会出现只有标点的行。

**怎么查**：

- `selfcheck.py`（只要 Python）：确认每个文字块的结尾都锁住了，正文和标记稿一字不差。
- `htmlcheck.py`（要 Playwright 和 Chrome）：把页面放在 340 到 450px 的每一种手机宽度下实际渲染，四组字体（三种英文字宽配无衬线中文，加一组衬线字体模拟安卓），逐字取位置分行，检查每个段落、标题、引用行和参考资料，也检查有没有字超出段落右边。TOTAL issues 必须是 0。
- 交付后用户在手机上看到单字落行时，先问手机型号和是否改过字号，再用 htmlcheck 复查；公众号设置里调大字号会改变每行字数，但尾字锁定照样有效。

## 6. 配图放在哪

- **公众号开头以文字为主。** 只有必须用图才能讲清楚时，才把图放在开头。
- 每张图放在它所解释的那段文字后面，紧跟着讲这个概念的句子。图上的标签和那句话能一一对应最好。比如「个人经验 → 组织能力」这张图，放在「让个人经验逐渐转化为组织能力，让公司在日常运转中不断积累和改进」这句话后面。
- 两张图之间至少隔 3 段正文，不要挤在一起。

## 7. 配图和封面

- **内文配图**：风格、配色、字号、边距、构图、半自动排版（`scripts/diagram.py`）和生成流程，见 `references/images.md`。
- **封面**：每篇出四张不同风格给用户挑。参考图学的是为什么好看，版式可以换。设计原则、四张怎么拉开、人物用白模和生成流程，见 `references/cover.md`。

## 8. 独立检查

做的人不给自己打分。所有交付物交给用户之前，按 `references/checklist.md` 让一个没看过制作过程的检查方逐项检查，有不通过的就改，最多 3 轮，交付时附检查结果表。

## 9. 附带文件

| 路径 | 用途 |
|---|---|
| `references/images.md` | 内文配图的全部规则和流程 |
| `references/cover.md` | 封面的设计原则、四张怎么拉开、共同规则和流程 |
| `references/checklist.md` | 独立检查的检查表和检查环 |
| `assets/sample_marked.txt` | 标记稿示例，用到了所有标记 |
| `assets/approved/approved-*.png` | 4 张定稿配图（留边修正版）：个人经验到组织能力、树状结构、五层圆环、订单流程 |
| `assets/covers/cover-illustration.png` | 封面参考：浅底、墨线插画 |
| `assets/covers/cover-whitebust.png` | 封面参考：陶土橙底、白模半身像 |
| `assets/quote-mark.png` | 引用块的水滴引号小图 |
| `scripts/build_html.py` | 把标记稿排成可粘贴的 HTML，自带尾字锁定和专有名词锁定。只用 Python 标准库 |
| `scripts/selfcheck.py` | 不用浏览器的结构检查：`python3 selfcheck.py 成品.html [标记稿.txt]`。只用 Python 标准库 |
| `scripts/htmlcheck.py` | 断行实测：340 到 450px 每种宽度、四组字体，打印 TOTAL issues |
| `scripts/phonecheck.py` | 小屏和大屏实测：名词有没有拆开、尾行有没有单字、哪几行字距最宽 |
| `scripts/gapmeasure.py` | 量标题上下和段落之间实际看到的空白 |
| `scripts/diagram.py` | 配图半自动排版：圆环、流程、容器三种图，输出坐标表、文字表和草图 |
| `scripts/coversheet.py` | 封面对比图：每张的信息流缩略图和 1:1 裁切并排，给用户挑 |
| `scripts/wireframe.py` | 手工排其他形式配图用的画布工具，里面的四个函数是 `assets/approved/` 四张定稿图的版式例子 |

**标记写法**：`# 标题`、`## 键|一级标题`、`### 编号|键|二级标题`、`**重点**`、`@@PREFACE_END`（导语结束）、`@@IMG 名字`（图片放在 art 文件夹的 名字.png；不存在时显示虚线占位框，说明文字写在标记稿同目录的 placeholders.txt，一行一个「名字|说明」；专有名词写在同目录的 terms.txt，一行一个）、`@@QUOTE 引用文字`（用竖线 \| 手动断行）、`@@REFS` 加 `@@REF 条目` 和 `@@NOTE 注释`。块和块之间空一行。

**运行环境**：排版和 selfcheck 只要 Python 3。htmlcheck、phonecheck、gapmeasure、diagram、wireframe、coversheet 还要 Pillow、NumPy 和 Playwright（`pip install pillow numpy playwright` 再 `playwright install chromium`）。Chrome 的路径可以用环境变量 CHROME_PATH 指定；不指定时先找 /usr/bin/google-chrome，没有就用 Playwright 自带的 Chromium。断行实测要用 Noto Sans CJK SC、Noto Serif CJK SC、Carlito、Liberation Sans、Liberation Serif、DejaVu Sans，缺了会打印警告。配图脚本的字体路径用环境变量 WENKAI_DIR 和 CAVEAT_FILE 指定。

**没有浏览器的环境**（比如 Claude 网页版不能装 Chrome 时）：照常排版，跑 selfcheck；尾字锁定已经保证了断行规则。在检查结果表里写明「没跑浏览器实测」。配图坐标没法用脚本排时，按 `references/images.md` 第 6 节的间距规则手算，并在提示词里留出余量。
