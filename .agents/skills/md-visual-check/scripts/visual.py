#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md-visual-check — 把 Markdown 渲染成可截图的 HTML 页面，顺带给出排版线索。

只用标准库。渲染结果用于「用眼睛看」，不是权威解析器：它按 GFM 常规路径铺开，
对 DSH 侧栏预览的个别脾气（表格跨空行合并等）只在 hints 里单独提示。

用法：
    python visual.py render <file.md> [--section TEXT] [--lines A-B] [--out DIR]
                                     [--width N] [--page-height N] [--max-pages N]
    python visual.py render <file.md> --json        # 只输出机器可读结果
"""

import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import unicodedata

# ---------------------------------------------------------------- 基础工具


def dwidth(s: str) -> int:
    """按显示宽度计数：东亚宽字符算 2，其余算 1。"""

    n = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            n += 2
        else:
            n += 1
    return n


def esc(s: str) -> str:
    return html.escape(s, quote=False)


RE_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)")
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
RE_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?\s*$")
RE_UL = re.compile(r"^(\s*)([-*+])\s+(.*)$")
RE_OL = re.compile(r"^(\s*)(\d{1,9})[.)]\s+(.*)$")
RE_QUOTE = re.compile(r"^\s{0,3}>\s?(.*)$")

# ---------------------------------------------------------------- 行内渲染

_MARK = "\ue000"
_RE_MARK = re.compile(re.escape(_MARK) + r"(\d+)" + re.escape(_MARK))


def fence_html(code: str) -> str:
    """围栏内逐字符对齐：ASCII/制表符按 1 格，全角按 2 格；字符宽度用 em 固定。

    这样图里「一个全角字 = 两个 ASCII 格」的手工对位才算得准，不会因为等宽字体的
    CJK 回退比例（Consolas 里是 1.82 格）把本来对齐的框图显示成错位。
    """

    out = []
    for ch in code:
        if ch == "\n":
            out.append("\n")
            continue
        wide = unicodedata.east_asian_width(ch) in ("W", "F")
        if not wide and ord(ch) < 128:
            out.append(esc(ch))
        else:
            out.append('<span class="g%d">%s</span>' % (2 if wide else 1, esc(ch)))
    return "".join(out)


def inline(text: str) -> str:
    stash = []

    def keep(fragment: str) -> str:
        stash.append(fragment)
        return "%s%d%s" % (_MARK, len(stash) - 1, _MARK)

    def code_span(m):
        return keep("<code>" + esc(m.group(1)) + "</code>")

    def math_span(m):
        return keep('<span class="math">' + esc(m.group(1).strip()) + "</span>")

    text = re.sub(r"`([^`\n]+)`", code_span, text)
    # 行内数学：$...$，不跨行、不吃 $$；\$ 视为转义。
    text = re.sub(r"(?<![\\$])\$(?!\$)([^$\n]+?)\$(?!\$)", math_span, text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!$~|])", r"\1", text)
    text = esc(text)

    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: '<img alt="%s" src="%s">' % (m.group(1), m.group(2)),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)),
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = re.sub(r"<br\s*/?>", "<br>", text, flags=re.I)

    def restore(s: str) -> str:
        while True:
            m = _RE_MARK.search(s)
            if not m:
                return s
            s = s[: m.start()] + stash[int(m.group(1))] + s[m.end() :]

    return restore(text)


# ---------------------------------------------------------------- 块级解析


class Block:
    __slots__ = ("kind", "html", "l0", "l1", "est", "meta")

    def __init__(self, kind, html_text, l0, l1, est, meta=None):
        self.kind = kind
        self.html = html_text
        self.l0 = l0
        self.l1 = l1
        self.est = est
        self.meta = meta or {}


def split_row(line: str):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, buf, i = [], [], 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def parse_blocks(lines, cells_per_line=114):
    """把行列表解析成 Block 列表；每块记住源行号区间（0 基）。"""

    blocks = []
    i, n = 0, len(lines)

    def push(kind, body, l0, l1, est, meta=None):
        blocks.append(Block(kind, body, l0, l1, est, meta))

    while i < n:
        line = lines[i]
        raw = line.rstrip("\n")

        if not raw.strip():
            i += 1
            continue

        m = RE_FENCE.match(raw)
        if m:
            indent, fence, lang = m.group(1), m.group(2), m.group(3)
            body = []
            j = i + 1
            closed = False
            while j < n:
                if lines[j].strip().startswith(fence[0] * len(fence)) and not lines[j].strip()[len(fence) :].strip():
                    closed = True
                    break
                body.append(lines[j].rstrip("\n"))
                j += 1
            code = "\n".join(body)
            label = '<div class="fence-lang">%s</div>' % esc(lang) if lang else ""
            push(
                "fence",
                '<div class="fence">%s<pre><code>%s</code></pre></div>'
                % (label, fence_html(code)),
                i,
                j if closed else n - 1,
                len(body) * 20 + 30,
                {"lang": lang, "closed": closed, "body": body, "fence": fence, "indent": indent},
            )
            i = j + 1
            continue

        m = RE_HEADING.match(raw)
        if m:
            level = len(m.group(1))
            push(
                "heading",
                "<h%d>%s</h%d>" % (level, inline(m.group(2)), level),
                i,
                i,
                34 + level * 10,
                {"level": level, "text": re.sub(r"[`*_]", "", m.group(2))},
            )
            i += 1
            continue

        if i + 1 < n and "|" in raw and RE_TABLE_SEP.match(lines[i + 1]) and raw.strip().startswith("|"):
            head = split_row(raw)
            sep_cells = split_row(lines[i + 1])
            aligns = []
            for cell in sep_cells:
                c = cell.strip()
                aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "left")
            rows, j = [], i + 2
            ragged = [] if len(sep_cells) == len(head) else [(i + 2, len(sep_cells))]
            while j < n:
                r = lines[j].rstrip("\n")
                if not r.strip().startswith("|"):
                    break
                cells = split_row(r)
                if len(cells) != len(head):
                    ragged.append((j + 1, len(cells)))
                rows.append(cells)
                j += 1

            def cell_html(tag, cells, cells_aligns):
                out = []
                for k in range(len(head)):
                    val = cells[k] if k < len(cells) else ""
                    al = cells_aligns[k] if k < len(cells_aligns) else "left"
                    out.append('<%s style="text-align:%s">%s</%s>' % (tag, al, inline(val), tag))
                return "".join(out)

            body = ["<thead><tr>%s</tr></thead><tbody>" % cell_html("th", head, aligns)]
            for cells in rows:
                body.append("<tr>%s</tr>" % cell_html("td", cells, aligns))
            body.append("</tbody>")
            push(
                "table",
                '<table class="tbl">%s</table>' % "".join(body),
                i,
                j - 1,
                (len(rows) + 1) * 36 + 12,
                {"cols": len(head), "rows": len(rows), "ragged": ragged, "header": head},
            )
            i = j
            continue

        m = RE_QUOTE.match(raw)
        if m:
            inner, j = [], i
            while j < n and RE_QUOTE.match(lines[j].rstrip("\n")):
                inner.append(RE_QUOTE.match(lines[j].rstrip("\n")).group(1))
                j += 1
            sub = parse_blocks(inner + [""], cells_per_line)
            body = "".join(b.html for b in sub)
            est = sum(b.est for b in sub) + 16
            push("quote", "<blockquote>%s</blockquote>" % body, i, j - 1, est, {"inner": inner})
            i = j
            continue

        if RE_HR.match(raw):
            push("hr", "<hr>", i, i, 24)
            i += 1
            continue

        if RE_UL.match(raw) or RE_OL.match(raw):
            items, j = [], i
            while j < n:
                r = lines[j].rstrip("\n")
                mu = RE_UL.match(r)
                mo = RE_OL.match(r)
                if mu or mo:
                    mm = mu or mo
                    items.append((len(mm.group(1).replace("\t", "    ")), bool(mo), mm.group(3).strip(), j))
                    j += 1
                    continue
                if r.strip() and not RE_HEADING.match(r) and not RE_FENCE.match(r) and items:
                    indent = len(r) - len(r.lstrip())
                    if indent >= items[-1][0] + 2 and (r.lstrip().startswith(("|", "```")) is False):
                        lvl, ordered, txt, ln = items[-1]
                        items[-1] = (lvl, ordered, txt + " " + r.strip(), ln)
                        j += 1
                        continue
                break
            # 组装嵌套列表
            body, stack = [], []
            for indent, ordered, txt, ln in items:
                depth = indent // 2
                tag = "ol" if ordered else "ul"
                while stack and stack[-1][0] > depth:
                    body.append("</li></%s>" % stack.pop()[1])
                if stack and stack[-1][0] == depth:
                    if stack[-1][1] != tag:
                        body.append("</li></%s>" % stack.pop()[1])
                        body.append("<%s>" % tag)
                        stack.append((depth, tag))
                    else:
                        body.append("</li>")
                else:
                    body.append("<%s>" % tag)
                    stack.append((depth, tag))
                mt = re.match(r"^\[([ xX])\]\s+(.*)$", txt)
                if mt:
                    txt = ("☑ " if mt.group(1).lower() == "x" else "☐ ") + mt.group(2)
                body.append("<li>%s" % inline(txt))
            while stack:
                body.append("</li></%s>" % stack.pop()[1])
            html_text = "".join(body)
            est = sum(
                max(1, (dwidth(t) + indent + cells_per_line - 1) // cells_per_line) * 30 + 8
                for indent, _o, t, _l in items
            )
            push("list", html_text, i, j - 1, est, {"count": len(items)})
            i = j
            continue

        # 段落：直到空行或下一个块起点
        para, j = [], i
        while j < n:
            r = lines[j].rstrip("\n")
            if not r.strip():
                break
            if j > i and (
                RE_HEADING.match(r)
                or RE_FENCE.match(r)
                or RE_HR.match(r)
                or RE_QUOTE.match(r)
                or RE_UL.match(r)
                or RE_OL.match(r)
            ):
                break
            para.append(r)
            j += 1
        text = "\n".join(para)
        # 段内的 $$ 块
        if text.strip().startswith("$$"):
            push(
                "mathblock",
                '<div class="math-block">%s</div>' % esc(text.strip().strip("$").strip()),
                i,
                j - 1,
                60,
            )
            i = j
            continue
        est = max(1, (dwidth(text) + cells_per_line - 1) // cells_per_line) * 30 + 6
        push("para", "<p>%s</p>" % inline(text.replace("\n", " ")), i, j - 1, est, {"text": text})
        i = j

    return blocks


# ---------------------------------------------------------------- 静态线索

BOX_CHARS = "│┃┆┊|║"


def hints(blocks, lines, base_dir):
    out = []

    def add(sev, line, code, msg):
        out.append({"severity": sev, "line": line, "code": code, "message": msg})

    prev_table = None
    prev_level = 0
    for b in blocks:
        if b.kind == "heading":
            lvl = b.meta["level"]
            if prev_level and lvl > prev_level + 1:
                add("warn", b.l0 + 1, "heading-jump", "标题从 %d 级跳到 %d 级" % (prev_level, lvl))
            prev_level = lvl

        if b.kind == "table":
            if b.meta["ragged"]:
                add(
                    "error",
                    b.meta["ragged"][0][0],
                    "table-ragged",
                    "表格列数不一致：表头 %d 列，第 %d 行列数 %d（预览器会把整块降级成纯文字）"
                    % (b.meta["cols"], b.meta["ragged"][0][0], b.meta["ragged"][0][1]),
                )
            if prev_table is not None and b.l0 - prev_table.l1 <= 2:
                add(
                    "warn",
                    b.l0 + 1,
                    "table-glued",
                    "两张表之间只隔空行，DSH 预览会把它们并成一张（第 %d 行起）" % (prev_table.l0 + 1),
                )
            prev_table = b
        else:
            if b.kind not in ("hr",):
                prev_table = None

        if b.kind == "fence":
            body = b.meta["body"]
            if not b.meta["closed"]:
                add("error", b.l0 + 1, "fence-unclosed", "代码围栏没有闭合")
            long_lines = [(b.l0 + 2 + k, dwidth(s)) for k, s in enumerate(body) if dwidth(s) > 100]
            if long_lines and b.meta["lang"] not in ("text", "txt"):
                ln, w = long_lines[0]
                add("info", ln, "code-long", "代码行显示宽度 %d 格，超过 100 格（截图里需要横向滚动）" % w)
            if b.meta["lang"] in ("text", "txt") and body:
                # 找右边界列：优先 │，其次 |；统计众数列，列出偏离行
                edges = "│┌┐└┘├┤┬┴┼║╔╗╚╝┃|"
                cols = {}
                for k, s in enumerate(body):
                    t = s.rstrip()
                    pos = [j for j, ch in enumerate(t) if ch in edges]
                    # 只看「右边框就是行尾」的行：树状图（├── 文本）结尾是文字，右边框列必然不同
                    if len(pos) >= 2 and pos[-1] == len(t) - 1:
                        cols[k] = (dwidth(t[: pos[0]]), dwidth(t[: pos[-1]]))
                if cols:
                    left_mode = max(set(v[0] for v in cols.values()), key=lambda x: sum(1 for v in cols.values() if v[0] == x))
                    same_left = {k: v for k, v in cols.items() if v[0] == left_mode}
                    freq = {}
                    for v in same_left.values():
                        freq[v[1]] = freq.get(v[1], 0) + 1
                    if freq:
                        modal, hits = max(freq.items(), key=lambda kv: kv[1])
                        bad = [(k, v[1]) for k, v in same_left.items() if v[1] != modal]
                        if len(same_left) >= 3 and bad and len(bad) <= len(same_left) // 2 and hits > len(bad):
                            k, v = bad[0]
                            where = "、".join("L%d" % (b.l0 + 2 + kk) for kk, _v in bad[:3])
                            add(
                                "warn",
                                b.l0 + 2 + k,
                                "ascii-misaligned",
                                "text 图右边框错位：该行到第 %d 列，同组 %d 行都在第 %d 列；偏离 %s（共 %d 行）"
                                % (v, hits, modal, where, len(bad)),
                            )

        if b.kind == "para":
            dollars = b.meta["text"].count("$")
            if dollars % 2 == 1:
                add("warn", b.l0 + 1, "math-dollar", "本段有 %d 个 $，奇数个会让半个段落变成公式或被吞掉" % dollars)

    # 图片路径不存在
    for k, line in enumerate(lines):
        for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)", line):
            src = m.group(1)
            if re.match(r"^(https?:|data:)", src):
                continue
            if not os.path.exists(os.path.join(base_dir, src.replace("%20", " "))):
                add("warn", k + 1, "img-missing", "图片路径找不到：%s" % src)

    out.sort(key=lambda d: (d["line"], d["code"]))
    return out


# ---------------------------------------------------------------- 页面装配

CSS = """
:root { --ink:#1a1a1a; --muted:#777; --line:#d0d0d0; }
* { box-sizing: border-box; }
body { margin:0; background:#fff; color:var(--ink);
       font:16px/1.75 "Microsoft YaHei","Segoe UI",system-ui,sans-serif; }
.page { width:%(width)spx; margin:0 auto; padding:14px 26px 40px; }
.runhead { font:12px/1.4 Consolas,monospace; color:var(--muted);
           border-bottom:1px solid var(--line); padding-bottom:6px; margin-bottom:14px; }
h1,h2,h3,h4,h5,h6 { line-height:1.35; margin:1.1em 0 .5em; }
h1 { font-size:1.9em; border-bottom:2px solid #333; padding-bottom:.2em; }
h2 { font-size:1.45em; border-bottom:1px solid var(--line); padding-bottom:.2em; }
h3 { font-size:1.2em; } h4 { font-size:1.05em; } h5,h6 { font-size:1em; color:#333; }
p { margin:.55em 0; }
ul,ol { margin:.5em 0; padding-left:1.9em; }
li { margin:.18em 0; }
blockquote { margin:.7em 0; padding:.1em 0 .1em 1em; border-left:3px solid #bbb; color:#333; }
hr { border:0; border-top:1px solid var(--line); margin:1.2em 0; }
table.tbl { border-collapse:collapse; margin:.7em 0; width:100%%; font-size:14px; line-height:1.55; }
table.tbl th, table.tbl td { border:1px solid #b8b8b8; padding:4px 8px; vertical-align:top;
                             word-break:break-word; }
table.tbl th { background:#f2f2f2; }
code { font-family:Consolas,"Courier New",monospace; font-size:.9em; background:#f4f4f4;
       padding:1px 3px; border-radius:3px; }
.fence { margin:.7em 0; border:1px solid #dcdcdc; border-radius:4px; background:#fbfbfb; }
.fence-lang { font:11px/1.6 Consolas,monospace; color:#999; padding:1px 8px; border-bottom:1px solid #eee; }
.fence pre { margin:0; padding:8px 10px; overflow-x:auto;
             font-family:Consolas,"Courier New",monospace; font-size:14px; line-height:1.45;
             white-space:pre; }
/* 一格 = 0.55em（Consolas 的字符步进）；全角占两格，字形居中不改变步进 */
.g1,.g2 { display:inline-block; text-align:center; vertical-align:baseline; }
.g1 { width:.55em; font-family:Consolas,"Segoe UI Symbol",monospace; }
.g2 { width:1.1em; font-family:SimSun,"NSimSun","Microsoft YaHei",serif; }
.math { font-family:"Cambria Math",Cambria,serif; font-style:italic; color:#2b2b2b;
        background:#f6f4ff; padding:0 2px; border-radius:2px; }
.math-block { font-family:Consolas,monospace; font-size:13px; color:#444;
              background:#f7f7f7; border-left:3px solid #c9c9c9; padding:6px 10px;
              margin:.7em 0; }
img { max-width:100%%; border:1px solid var(--line); }
a { color:#0b57d0; text-decoration:none; border-bottom:1px dotted #0b57d0; }
"""


def page_html(title, runhead, body, width):
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        "<title>%s</title><style>%s</style></head><body><div class=\"page\">"
        '<div class="runhead">%s</div>%s</div></body></html>'
        % (esc(title), CSS % {"width": width}, esc(runhead), body)
    )


def paginate(blocks, page_height):
    pages, cur, h = [], [], 0
    for b in blocks:
        if cur and h + b.est > page_height:
            pages.append(cur)
            cur, h = [], 0
        cur.append(b)
        h += b.est
    if cur:
        pages.append(cur)
    return pages


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown 渲染成可截图页面 + 排版线索")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("render")
    r.add_argument("md")
    r.add_argument("--section", default=None, help="只渲染标题包含该文字的节")
    r.add_argument("--lines", default=None, help="只渲染 A-B 行（1 基，含端点）")
    r.add_argument("--pad", type=int, default=2, help="--lines 时向前后扩展的行数")
    r.add_argument("--out", default=None)
    r.add_argument("--width", type=int, default=960)
    r.add_argument("--page-height", type=int, default=1400)
    r.add_argument("--max-pages", type=int, default=0, help="最多输出多少页，0 为全部")
    r.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd != "render" or not args.md:
        ap.print_help()
        return 2

    path = os.path.abspath(args.md)
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        text = fh.read()
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    base_dir = os.path.dirname(path)

    cells_per_line = max(40, int(args.width / 8.4))
    blocks = parse_blocks(lines, cells_per_line)

    # 选区
    sel_note = ""
    sel_range = None
    if args.lines:
        a, _, b = args.lines.partition("-")
        lo = max(0, int(a) - 1 - args.pad)
        hi = min(len(lines) - 1, int(b or a) - 1 + args.pad)
        blocks = [x for x in blocks if x.l0 <= hi and x.l1 >= lo]
        sel_note = "选中第 %d-%d 行" % (lo + 1, hi + 1)
        sel_range = (lo + 1, hi + 1)
    elif args.section:
        key = args.section.strip()
        start = None
        for b in blocks:
            if b.kind == "heading" and key in b.meta.get("text", ""):
                start = b
                break
        if start is None:
            print("找不到包含该文字的标题：%s" % key, file=sys.stderr)
            return 1
        level = start.meta["level"]
        end_idx = len(blocks)
        for k, b in enumerate(blocks):
            if k and b.kind == "heading" and b.meta["level"] <= level and b.l0 > start.l0:
                end_idx = k
                break
        blocks = blocks[blocks.index(start) : end_idx]
        sel_note = "节：%s" % start.meta["text"]
        sel_range = (start.l0 + 1, blocks[-1].l1 + 1)

    found = hints(parse_blocks(lines, cells_per_line), lines, base_dir)
    if sel_range:
        for h in found:
            if not (sel_range[0] <= h["line"] <= sel_range[1]):
                h["message"] += "（选区外）"

    out_dir = args.out or os.path.join(
        tempfile.gettempdir(), "mdvisual-" + hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
    )
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".html"):
            os.remove(os.path.join(out_dir, old))

    pages = paginate(blocks, args.page_height)
    written = []
    for k, page_blocks in enumerate(pages):
        if args.max_pages and k >= args.max_pages:
            break
        l0, l1 = page_blocks[0].l0, page_blocks[-1].l1
        runhead = "%s ｜ 第 %d/%d 页 ｜ 源 L%d–L%d%s" % (
            os.path.basename(path),
            k + 1,
            len(pages),
            l0 + 1,
            l1 + 1,
            (" ｜ " + sel_note) if sel_note else "",
        )
        body = "".join(b.html for b in page_blocks)
        name = "page-%02d.html" % (k + 1)
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(page_html(os.path.basename(path), runhead, body, args.width))
        written.append({"n": k + 1, "l0": l0 + 1, "l1": l1 + 1, "path": os.path.join(out_dir, name)})

    result = {
        "md": path,
        "lines": len(lines),
        "eol": "CRLF" if eol == "\r\n" else "LF",
        "mixed_eol": ("\r\n" in text) and ("\n" in text.replace("\r\n", "")),
        "out_dir": out_dir,
        "pages": written,
        "hints": found,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    report = []
    report.append("文件：%s（%d 行，%s%s）" % (
        os.path.basename(path),
        len(lines),
        result["eol"],
        "，行尾混用" if result["mixed_eol"] else "",
    ))
    report.append("页面：%d 个 → %s" % (len(written), out_dir))
    for p in written:
        report.append("  page-%02d  L%d–L%d" % (p["n"], p["l0"], p["l1"]))
    if not found:
        report.append("线索：无")
    else:
        report.append("线索：%d 条" % len(found))
        for h in found:
            report.append("  [%s] L%-5d %-16s %s" % (h["severity"], h["line"], h["code"], h["message"]))
    text_out = "\n".join(report) + "\n"
    report_path = os.path.join(out_dir, "report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text_out)
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.stdout.write(text_out)
    sys.stdout.write("报告：%s\n" % report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
