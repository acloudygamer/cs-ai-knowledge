#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公式排版 修复+检查脚本（配套《公式排版规范-工作版》）

用法（仓库根目录下）：
    python .agents/skills/gfm-math/math_fix.py <文件.md> [更多文件...] [--check] [--no-api]

三段流程：
  1. 自动修（默认直接改原文件；--check 只列不改）：
     - 开 $ 前是阻断字符（非空格/行首/半角(）→ 补半角空格
     - 闭 $ 后是词字符（字母/数字/_）→ 补半角空格
     - 公式内侧空白（`$ x$` / `$x $`）→ 去成紧贴
     - 公式内单写 \\% \\{ \\} \\_ \\& \\# \\, \\; \\! \\: \\. → 双写
     - $$ 块未独占段落（前后缺空行）→ 补空行（邻居是列表/引用/表格等结构行时只报告）
  2. 静态检查（只报告）：
     - 行内公式含杀手子串 select/begin
     - 行内公式含断行 \\\\（后随非转义标点）
     - 疑似表格行内裸 |
     - $$ 与文字同行（退化风险）/ 未配对 $$
     - 边界合法但找不到闭 $（货币写法会自动跳过，不报）
  3. API 比对（默认开；--no-api 关闭）：
     - 公式计数：源码候选数 vs 返回的 <math-renderer> 数
     - 退化检查：js-inline-math 内含 $$
     - 残留定位：HTML 文本里残留的裸 $…$ 反查源文件行号
     默认模式 API 发送修复后文本；--check 模式发送原文。
"""
import html as html_mod
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ESCAPABLE = '%{}_&#,;!:.'
DOUBLE_RE = re.compile(r'(?<!\\)\\(?=[' + re.escape(ESCAPABLE) + r'])')
LINEBREAK_RE = re.compile(r'\\\\(?![\\' + re.escape(ESCAPABLE) + r'])')
KILLER_RE = re.compile(r'select|begin', re.IGNORECASE)
WORD_RE = re.compile(r'[A-Za-z0-9_]')
STRUCT_LINE = re.compile(r'\s*(>|[-*+]|\d+\.|\||#)')
NORM_RE = re.compile(r'[^0-9A-Za-z一-鿿]+')
OPEN_OK = (' ', '\t', '\n', '(', '\x00')


class Report:
    def __init__(self):
        self.fixes = []    # (line, msg)
        self.issues = []   # (line, msg)


def norm(s):
    return NORM_RE.sub('', s)


def apply_edits(text, edits):
    for pos, delete_len, insert in sorted(edits, reverse=True):
        text = text[:pos - delete_len] + insert + text[pos:]
    return text


def mask_code(text, frags):
    """掩码：$`…`$ 兜底、围栏代码块、行内 code span。返回 (掩码文本, 兜底数)。"""
    def hold(m):
        frags.append(m.group(0))
        return '\x00%d\x00' % (len(frags) - 1)
    text = re.sub(r'```.*?```', hold, text, flags=re.S)  # 围栏块最先（内部可能含 $`…`$ 形态）
    text, n_fallback = re.subn(r'\$`[^`]*`\$', hold, text)
    text = re.sub(r'`[^`\n]*`', hold, text)
    return text, n_fallback


def restore(text, frags):
    def back(m):
        return frags[int(m.group(1))]
    return re.sub('\x00(\\d+)\x00', back, text)


def fix_display(text, frags, rep, nl):
    """处理 $$…$$ 块：转义双写、独占段落补空行、退化检查；然后掩码。返回 (文本, 块数)。"""
    edits = []
    spans = list(re.finditer(r'\$\$.*?\$\$', text, re.S))
    n_marks = text.count('$$')
    if n_marks != 2 * len(spans):
        rep.issues.append((0, '存在未配对的 $$（配对结果可能错位），请人工检查'))

    for m in spans:
        line = text.count('\n', 0, m.start()) + 1
        cs, ce = m.start() + 2, m.end() - 2  # 内容区间
        for dm in DOUBLE_RE.finditer(text[cs:ce]):
            edits.append((cs + dm.start() + 1, 0, '\\'))
            rep.fixes.append((line, '块内转义双写：\\%s' % text[cs + dm.start() + 1]))

        # 同行文字 → 退化风险（只报告）
        ls = text.rfind('\n', 0, m.start()) + 1
        le = text.find('\n', m.end())
        le = len(text) if le == -1 else le
        prefix = text[ls:m.start()].strip()
        suffix = text[m.end():le].strip()
        if prefix or suffix:
            rep.issues.append((line, '$$ 与文字同行，会退化为行内（js-inline-math），请拆开'))
            continue

        # 独占段落：前一行/后一行非空则补空行（结构行只报告）
        if ls >= 2:
            prev_end = ls - 1
            prev_start = text.rfind('\n', 0, prev_end) + 1 if prev_end > 0 else 0
            prev_line = text[prev_start:prev_end].strip()
            if prev_line:
                if STRUCT_LINE.match(prev_line):
                    rep.issues.append((line, '$$ 块紧跟结构行（列表/引用/表格等），请人工处理'))
                else:
                    edits.append((ls, 0, nl))
                    rep.fixes.append((line, '$$ 块前补空行'))
        if le < len(text):
            next_end = text.find('\n', le + 1)
            next_end = len(text) if next_end == -1 else next_end
            next_line = text[le + 1:next_end].strip()
            if next_line:
                if STRUCT_LINE.match(next_line):
                    rep.issues.append((le and text.count('\n', 0, le) + 1, '$$ 块后紧跟结构行（列表/引用/表格等），请人工处理'))
                else:
                    ins = le - 1 if le > 0 and text[le - 1] == '\r' else le  # CRLF 插在 \r 前
                    edits.append((ins, 0, nl))
                    rep.fixes.append((line, '$$ 块后补空行'))

    text = apply_edits(text, edits)

    # 掩码（含 edits 后的新位置，重新扫描）
    def hold(m):
        frags.append(m.group(0))
        return '\x00%d\x00' % (len(frags) - 1)
    text, n_display = re.subn(r'\$\$.*?\$\$', hold, text, flags=re.S)
    return text, n_display


def fix_inline(text, rep, check_mode):
    """扫描行内 $…$：边界补空格、内侧去空白、转义双写、静态检查。返回 (文本, 活公式数)。"""
    edits = []
    n = len(text)
    n_alive = 0
    i = 0
    while i < n:
        if text[i] != '$' or (i > 0 and text[i - 1] == '\\'):
            i += 1
            continue
        if text[i + 1:i + 2] == '$':
            rep.issues.append((text.count('\n', 0, i) + 1, '落单的 $$（未配对残留）'))
            i += 2
            continue
        # 找闭 $（严格）：前非空白非反斜杠、后非数字（货币规则）；内容含 $ 的配对不可信，继续找
        j = i + 1
        closer = -1
        digit_k = -1
        while closer == -1:
            k = text.find('$', j)
            if k == -1:
                break
            if text[k - 1] == '\\':
                j = k + 1
                continue
            if k + 1 < n and text[k + 1].isdigit():
                if digit_k == -1 and not text[k - 1].isspace():
                    digit_k = k
                j = k + 1
                continue
            if text[k - 1].isspace():
                j = k + 1
                continue
            inner = text[i + 1:k]
            if '$' in inner or not inner.strip():
                j = k + 1
                continue
            closer = k
        if closer == -1 and digit_k != -1 and not text[i + 1:i + 2].isdigit() and not text[i + 1:i + 2].isspace():
            # 闭 $ 后贴数字 → 定界符不成立（货币写法在上面按开 $ 后数字排除）
            if '$' not in text[i + 1:digit_k] and text[i + 1:digit_k].strip():
                closer = digit_k  # 落入正常流程，闭侧补空格修复
        if closer == -1:
            # 宽松：接受闭前空白（`$y $` 形态），排除货币/散写误判
            j = i + 1
            while True:
                k = text.find('$', j)
                if k == -1:
                    break
                if text[k - 1] == '\\' or not text[k - 1].isspace():
                    j = k + 1
                    continue
                if k + 1 < n and text[k + 1].isdigit():
                    j = k + 1
                    continue
                inner = text[i + 1:k]
                stripped = inner.strip()
                if '$' in inner or not stripped:
                    break
                if text[i + 1:i + 2].isdigit() and (re.search(r'\s', stripped) or re.search(r'[一-鿿]', stripped)):
                    break  # `$2/GB … $0.08/GB` 式货币，不是公式
                closer = k
                break
        if closer == -1:
            prev_ok = i == 0 or text[i - 1] in OPEN_OK
            if prev_ok and i + 1 < n and not text[i + 1].isspace() and not text[i + 1].isdigit():
                rep.issues.append((text.count('\n', 0, i) + 1, '找不到闭 $（疑似未闭合；货币写法不会报这条）'))
            i += 1
            continue

        content = text[i + 1:closer]
        if '$' in content:  # 内含被规则跳过的 $，多半不是公式（货币/散写）
            i += 1
            continue

        line = text.count('\n', 0, i) + 1
        alive = True

        # 开侧边界
        if i > 0 and text[i - 1] not in OPEN_OK:
            edits.append((i, 0, ' '))
            rep.fixes.append((line, '开 $ 前补空格（前字符「%s」）' % text[i - 1]))
            alive = False
        # 闭侧边界
        if closer + 1 < n and WORD_RE.match(text[closer + 1]):
            edits.append((closer + 1, 0, ' '))
            rep.fixes.append((line, '闭 $ 后补空格（后字符「%s」）' % text[closer + 1]))
            alive = False
        # 内侧空白
        m_lead = re.match(r'\s+', content)
        if m_lead:
            edits.append((i + 1 + m_lead.end(), m_lead.end(), ''))
            rep.fixes.append((line, '开 $ 内侧去空白'))
            alive = False
        m_trail = re.search(r'\s+$', content)
        if m_trail:
            edits.append((closer, m_trail.end() - m_trail.start(), ''))
            rep.fixes.append((line, '闭 $ 内侧去空白'))
            # 闭前空白仅三明治阻断，统一按修复处理，alive 不变严格化

        # 转义双写
        for dm in DOUBLE_RE.finditer(content):
            edits.append((i + 1 + dm.start() + 1, 0, '\\'))
            rep.fixes.append((line, '行内转义双写：\\%s' % content[dm.start() + 1]))

        # 静态检查
        core = content.strip()
        if KILLER_RE.search(core):
            rep.issues.append((line, '行内公式含杀手子串 select/begin → 必死，请改写或进块级'))
        if LINEBREAK_RE.search(core):
            rep.issues.append((line, '行内公式含断行 \\\\（行中塌成 \\）→ 请进块级 aligned'))
        if re.search(r'(?<!\\)\|', core):
            ls = text.rfind('\n', 0, i) + 1
            le = text.find('\n', closer)
            line_text = text[ls:le if le != -1 else n]
            if '|' in line_text[:i - ls] or '|' in line_text[closer - ls + 1:]:
                rep.issues.append((line, '疑似表格行内裸 | → 格会被切开，写 \\|'))

        if alive or not check_mode:
            n_alive += 1
        i = closer + 1

    return apply_edits(text, edits), n_alive


def api_check(text, n_inline, n_display, n_fallback, rep):
    try:
        token = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip()
        req = urllib.request.Request(
            'https://api.github.com/markdown',
            data=json.dumps({'text': text, 'mode': 'gfm'}).encode('utf-8'),
            headers={'Authorization': 'token %s' % token, 'Content-Type': 'application/json'})
        html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8')
    except Exception as e:
        rep.issues.append((0, 'API 调用失败：%s' % e))
        return

    renderers = re.findall(r'<math-renderer class="(js-inline-math|js-display-math)"[^>]*>(.*?)</math-renderer>', html, re.S)
    a_inline = sum(1 for c, _ in renderers if c == 'js-inline-math')
    a_display = sum(1 for c, _ in renderers if c == 'js-display-math')
    e_inline = n_inline + n_fallback

    print('  [API] 预期 行内 %d + 块级 %d = %d ｜ 实际 行内 %d + 块级 %d = %d'
          % (e_inline, n_display, e_inline + n_display, a_inline, a_display, len(renderers)))

    for c, content in renderers:
        if c == 'js-inline-math' and '$$' in content:
            rep.issues.append((0, '退化：块级公式被包成行内（内容含 $$）：%s' % content[:40]))

    if a_display != n_display:
        rep.issues.append((0, '块级数量不符：预期 %d、实际 %d（检查退化或块结构）' % (n_display, a_display)))

    if len(renderers) < e_inline + n_display:
        # 残留定位：去掉渲染器和标签后在纯文本里找 $ / $$
        plain = re.sub(r'<math-renderer\b.*?</math-renderer>', '', html, flags=re.S)
        plain = html_mod.unescape(re.sub(r'<[^>]+>', '', plain))
        src_lines = [norm(l) for l in text.split('\n')]
        seen = set()

        def locate(frag):
            f = norm(frag)
            if len(f) < 2 or f in seen:
                return
            seen.add(f)
            hits = [idx + 1 for idx, l in enumerate(src_lines) if f in l]
            where = '、'.join('L%d' % h for h in hits[:3]) if hits else '（未能定位，内容已被改写）'
            rep.issues.append((0, '死公式残留：「%s」→ %s' % (frag.strip()[:50].replace('\n', '⏎'), where)))

        for m in re.finditer(r'\$\$([\s\S]{0,300}?)\$\$', plain):  # 死块
            locate(m.group(1))
        plain = re.sub(r'\$\$[\s\S]{0,300}?\$\$', '', plain)
        for m in re.finditer(r'\$([^\n$]{0,100})\$?', plain):  # 行内残留
            inner = m.group(1)
            if inner[:1].isdigit():
                continue  # 货币：$ 后贴数字
            if m.group(0).endswith('$') and plain[m.end():m.end() + 1].isdigit():
                continue  # 货币：闭 $ 后贴数字
            locate(inner or m.group(0))


def process(path, check_mode, use_api):
    raw = Path(path).read_text(encoding='utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    rep = Report()
    frags = []

    text, n_fallback = mask_code(raw, frags)
    text, n_display = fix_display(text, frags, rep, nl)
    text, n_inline = fix_inline(text, rep, check_mode)
    fixed = restore(text, frags)

    print('=== %s ===' % path)
    if rep.fixes:
        print('  [修复] %d 处：' % len(rep.fixes))
        for line, msg in rep.fixes:
            print('    L%-5s %s' % (line, msg))
        if not check_mode and fixed != raw:
            Path(path).write_text(fixed, encoding='utf-8', newline='')
            print('  → 已写回文件')
    else:
        print('  [修复] 无需修复')

    if use_api:
        api_check(fixed if not check_mode else raw, n_inline, n_display, n_fallback, rep)

    if rep.issues:
        print('  [检查] %d 项：' % len(rep.issues))
        for line, msg in rep.issues:
            print('    %-6s %s' % ('L%d' % line if line else '-', msg))
    else:
        print('  [检查] 无问题')
    print()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check_mode = '--check' in sys.argv
    use_api = '--no-api' not in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    sys.stdout.reconfigure(encoding='utf-8')
    for p in args:
        process(p, check_mode, use_api)


if __name__ == '__main__':
    main()
