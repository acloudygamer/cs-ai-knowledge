"""Check ``## 一、`` sections and ``### 1.`` subsection sequences.

Run from the repository root, for example::

    python -m tools.markdown_checks.check_numbering path/to/article.md
    python -m tools.markdown_checks.check_numbering path/to/chapter/
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Sequence

from tools.markdown_checks._shared.cli import configure_stdio
from tools.markdown_checks._shared.markdown import (
    Diagnostic,
    InputError,
    chapter_files,
    display_path,
    iter_unfenced_lines,
    parse_atx_heading,
    read_utf8,
)


_SECTION_NUMBER = re.compile(r"^([零一二三四五六七八九十百千两]+)、")
_SUBSECTION_NUMBER = re.compile(r"^(\d+)\.(?:[ \t]+|$)")
_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_UNITS = {"十": 10, "百": 100, "千": 1000}


@dataclass(frozen=True)
class NumberingResult:
    diagnostics: tuple[Diagnostic, ...]
    sections: int
    subsections: int


def _format_chinese_number(value: int) -> str:
    """Return the canonical spelling used to validate parsed section numbers."""

    if value == 0:
        return "零"
    if not 0 < value < 10000:
        raise ValueError("节编号仅支持 0～9999")
    digits = "零一二三四五六七八九"
    parts: list[str] = []
    started = False
    zero_pending = False
    for unit, symbol in ((1000, "千"), (100, "百"), (10, "十"), (1, "")):
        digit = (value // unit) % 10
        if digit == 0:
            if started:
                zero_pending = True
            continue
        if zero_pending and started:
            parts.append("零")
        if unit != 10 or digit != 1 or started:
            parts.append(digits[digit])
        if symbol:
            parts.append(symbol)
        started = True
        zero_pending = False
    return "".join(parts)


def parse_chinese_number(text: str) -> int:
    """Parse a canonical Chinese integer used in section titles, up to thousands."""

    total = 0
    pending = 0
    seen = False
    for char in text:
        if char in _DIGITS:
            pending = _DIGITS[char]
            seen = True
        elif char in _UNITS:
            unit = _UNITS[char]
            total += (pending or 1) * unit
            pending = 0
            seen = True
        else:
            raise ValueError(f"无法识别中文编号：{text}")
    if not seen:
        raise ValueError("中文编号不能为空")
    value = total + pending
    if text != _format_chinese_number(value):
        raise ValueError(f"不是规范中文整数：{text}")
    return value


def check_file(path: Path) -> NumberingResult:
    """Check one Markdown file without modifying it."""

    text = read_utf8(path)
    diagnostics: list[Diagnostic] = []
    expected_section = 1
    expected_subsection = 1
    current_section: str | None = None
    section_count = 0
    subsection_count = 0

    for line_number, line in iter_unfenced_lines(text):
        heading = parse_atx_heading(line)
        if heading is None:
            continue
        level, title = heading

        if level == 2:
            expected_subsection = 1
            current_section = None
            match = _SECTION_NUMBER.match(title)
            if match is None:
                continue
            raw_number = match.group(1)
            try:
                actual = parse_chinese_number(raw_number)
            except ValueError as exc:
                diagnostics.append(Diagnostic(path, line_number, "E_SECTION_NUMBER", str(exc)))
                continue
            section_count += 1
            if actual != expected_section:
                diagnostics.append(
                    Diagnostic(
                        path,
                        line_number,
                        "E_SECTION_SEQUENCE",
                        f"节编号为 {actual}，按当前顺序应为 {expected_section}",
                    )
                )
            expected_section = actual + 1
            current_section = title
            continue

        if level != 3:
            continue
        match = _SUBSECTION_NUMBER.match(title)
        if match is None:
            continue
        actual = int(match.group(1))
        if current_section is None:
            diagnostics.append(
                Diagnostic(
                    path,
                    line_number,
                    "E_SUBSECTION_WITHOUT_SECTION",
                    "编号小节必须位于带“## 一、”编号的节内",
                )
            )
            continue
        subsection_count += 1
        if actual != expected_subsection:
            diagnostics.append(
                Diagnostic(
                    path,
                    line_number,
                    "E_SUBSECTION_SEQUENCE",
                    f"《{current_section}》的小节编号为 {actual}，按当前顺序应为 {expected_subsection}",
                )
            )
        expected_subsection = actual + 1

    return NumberingResult(tuple(diagnostics), section_count, subsection_count)


def _expand_inputs(paths: Sequence[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            files.extend(chapter_files(path))
        elif path.is_file():
            files.append(path)
        else:
            raise InputError(f"路径不存在：{display_path(path)}")
    return files


def main(argv: Sequence[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", help="Markdown 篇目，或含 NN-*.md 的章目录")
    parser.add_argument(
        "--require-numbered",
        action="store_true",
        help="没有“## 一、”编号节时也返回 1，供收章闸门使用",
    )
    args = parser.parse_args(argv)

    had_input_error = False
    had_violation = False
    try:
        files = _expand_inputs(args.paths)
    except InputError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    for path in files:
        try:
            result = check_file(path)
        except InputError as exc:
            had_input_error = True
            print(f"ERROR {exc}", file=sys.stderr)
            continue
        for diagnostic in result.diagnostics:
            print(diagnostic.render())
        if result.diagnostics:
            had_violation = True
            print(f"FAIL {display_path(path)}：{len(result.diagnostics)} 个编号问题")
        elif result.sections == 0:
            if args.require_numbered:
                had_violation = True
                print(f"FAIL {display_path(path)}：未找到规范要求的“## 一、”编号节")
            else:
                print(f"SKIP {display_path(path)}：未发现可校验的“## 一、”编号节")
        else:
            print(
                f"PASS {display_path(path)}："
                f"{result.sections} 节，{result.subsections} 个编号小节"
            )

    if had_input_error:
        return 2
    return 1 if had_violation else 0


if __name__ == "__main__":
    raise SystemExit(main())
