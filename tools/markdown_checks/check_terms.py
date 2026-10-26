"""Check a chapter's term manifest against actual first occurrences.

The manifest is the ``## 本章术语表`` table in the chapter ``README.md``.
Run from the repository root::

    python -m tools.markdown_checks.check_terms path/to/chapter/
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


@dataclass(frozen=True)
class TermEntry:
    term: str
    full_name: str
    first_file: str
    line: int
    sense: str | None = None

    @property
    def label(self) -> str:
        if self.sense is None:
            return self.term
        return f"{self.term}（{self.sense}）"


@dataclass(frozen=True)
class TermResult:
    diagnostics: tuple[Diagnostic, ...]
    terms: int
    files: int


def clean_table_cell(cell: str) -> str:
    """Normalize the light markup allowed in a manifest table cell."""

    value = cell.strip().replace(r"\|", "|")
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    return value


def parse_declared_term(cell: str) -> tuple[str, str | None]:
    """Split an optional Chinese-parenthesized sense from a declared term."""

    match = re.fullmatch(r"(.+?)（([^（）]+)）", cell)
    if match is None:
        return cell, None
    return match.group(1).strip(), match.group(2).strip()


def split_table_row(line: str) -> list[str] | None:
    """Split a real pipe table row, not an indented code example."""

    leading = re.match(r"^[ \t]*", line).group(0)
    if "\t" in leading or len(leading) > 3:
        return None
    stripped = line.strip()
    if len(stripped) < 2 or not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in stripped[1:-1]:
        if char == "|" and not escaped:
            cells.append(clean_table_cell("".join(current)))
            current = []
        else:
            current.append(char)
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    cells.append(clean_table_cell("".join(current)))
    return cells


def is_separator_row(cells: list[str]) -> bool:
    """Recognize a Markdown table's ``---`` separator row."""

    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def term_pattern(term: str) -> re.Pattern[str]:
    """Match a term without also matching its ASCII word/identifier affixes."""

    prefix = ""
    suffix = ""
    if term[0].isascii() and (term[0].isalnum() or term[0] == "_"):
        prefix = r"(?<![A-Za-z0-9_])"
    if term[-1].isascii() and (term[-1].isalnum() or term[-1] == "_"):
        suffix = r"(?![A-Za-z0-9_])"
    return re.compile(prefix + re.escape(term) + suffix)


def line_at(text: str, offset: int) -> int:
    """Convert a string offset to a 1-based source line."""

    return text.count("\n", 0, offset) + 1


def _header_indices(cells: list[str]) -> tuple[int, int, int] | None:
    term = full_name = first_file = None
    for index, cell in enumerate(cells):
        if cell == "术语" or cell.startswith("术语（"):
            term = index
        elif cell == "全称":
            full_name = index
        elif cell == "首次出现的篇":
            first_file = index
    if term is None or full_name is None or first_file is None:
        return None
    return term, full_name, first_file


def parse_manifest(readme: Path, text: str) -> tuple[list[TermEntry], list[Diagnostic]]:
    """Read the dedicated term table without interpreting prose heuristically."""

    lines = list(iter_unfenced_lines(text))
    headings = [
        (index, line_number, title)
        for index, (line_number, line) in enumerate(lines)
        if (heading := parse_atx_heading(line)) is not None
        for level, title in [heading]
        if level == 2
    ]
    targets = [item for item in headings if item[2] == "本章术语表"]
    diagnostics: list[Diagnostic] = []
    if not targets:
        return [], [Diagnostic(readme, None, "E_TABLE_MISSING", "缺少“## 本章术语表”")]
    if len(targets) > 1:
        for _, line_number, _ in targets[1:]:
            diagnostics.append(
                Diagnostic(readme, line_number, "E_TABLE_DUPLICATE", "本章术语表只能出现一次")
            )

    start = targets[0][0]
    end = len(lines)
    for index, _, _ in headings:
        if index > start:
            end = index
            break
    section_lines = lines[start + 1 : end]
    header_position = None
    indices = None
    header_cells: list[str] = []
    header_line = targets[0][1]
    for position, (line_number, line) in enumerate(section_lines):
        cells = split_table_row(line)
        if cells is None:
            continue
        indices = _header_indices(cells)
        if indices is not None:
            header_position = position
            header_line = line_number
            header_cells = cells
            break
    if header_position is None or indices is None:
        diagnostics.append(
            Diagnostic(
                readme,
                targets[0][1],
                "E_TABLE_HEADER",
                "术语表需要“术语（最简形式）｜全称｜首次出现的篇”三列",
            )
        )
        return [], diagnostics

    separator_position = header_position + 1
    separator_cells = None
    separator_line = header_line
    if separator_position < len(section_lines):
        separator_line, separator_text = section_lines[separator_position]
        separator_cells = split_table_row(separator_text)
    if (
        separator_cells is None
        or not is_separator_row(separator_cells)
        or separator_line != header_line + 1
    ):
        diagnostics.append(
            Diagnostic(
                readme,
                separator_line,
                "E_TABLE_SEPARATOR",
                "表头下一行必须是 Markdown 分隔行，不能跨正文或空行拼表",
            )
        )
        return [], diagnostics
    if len(separator_cells) != len(header_cells):
        diagnostics.append(
            Diagnostic(readme, separator_line, "E_TABLE_SEPARATOR", "分隔行列数与表头不一致")
        )

    data_rows: list[tuple[int, list[str]]] = []
    table_end = separator_position + 1
    previous_line = separator_line
    while table_end < len(section_lines):
        line_number, line = section_lines[table_end]
        cells = split_table_row(line)
        if cells is None or line_number != previous_line + 1:
            break
        data_rows.append((line_number, cells))
        previous_line = line_number
        table_end += 1
    for line_number, line in section_lines[table_end:]:
        if split_table_row(line) is not None:
            diagnostics.append(
                Diagnostic(
                    readme,
                    line_number,
                    "E_TABLE_CONTIGUITY",
                    "术语表数据行必须连续，不能跨正文或空行续接",
                )
            )
            break

    entries: list[TermEntry] = []
    seen_entries: dict[tuple[str, str | None], int] = {}
    seen_terms: set[str] = set()
    unqualified_terms: set[str] = set()
    saw_data_row = False
    for line_number, cells in data_rows:
        if is_separator_row(cells):
            continue
        saw_data_row = True
        if len(cells) != len(header_cells):
            diagnostics.append(
                Diagnostic(readme, line_number, "E_TABLE_ROW", "数据行列数与表头不一致")
            )
            continue
        term, sense = parse_declared_term(cells[indices[0]])
        full_name = cells[indices[1]]
        first_file = cells[indices[2]]
        if not term or not full_name or not first_file or sense == "":
            diagnostics.append(
                Diagnostic(readme, line_number, "E_TABLE_CELL", "术语、全称和首次出现的篇均不能为空")
            )
            continue
        key = (term, sense)
        label = f"{term}（{sense}）" if sense is not None else term
        if key in seen_entries:
            diagnostics.append(
                Diagnostic(
                    readme,
                    line_number,
                    "E_DUPLICATE_TERM",
                    f"术语“{label}”已在第 {seen_entries[key]} 行登记",
                )
            )
            continue
        if term in seen_terms and (sense is None or term in unqualified_terms):
            diagnostics.append(
                Diagnostic(
                    readme,
                    line_number,
                    "E_TERM_SENSE",
                    f"同形术语“{term}”的每个条目都必须用“术语（含义）”区分",
                )
            )
            continue
        seen_entries[key] = line_number
        seen_terms.add(term)
        if sense is None:
            unqualified_terms.add(term)
        entries.append(TermEntry(term, full_name, first_file, line_number, sense))

    if not saw_data_row:
        diagnostics.append(
            Diagnostic(readme, header_line, "E_TABLE_EMPTY", "本章术语表没有术语数据行")
        )
    return entries, diagnostics


def _locations(matches: list[tuple[Path, int]]) -> str:
    return "、".join(f"{display_path(path)}:{line}" for path, line in matches)


def check_chapter(directory: Path) -> TermResult:
    """Check all declared terms in one chapter, in numeric article order."""

    if not directory.is_dir():
        raise InputError(f"不是有效章目录：{display_path(directory)}")
    files = chapter_files(directory)
    readme = directory / "README.md"
    if not readme.is_file():
        return (
            TermResult(
                (Diagnostic(readme, None, "E_README_MISSING", "章目录缺少 README.md"),),
                0,
                len(files),
            )
        )

    entries, diagnostics = parse_manifest(readme, read_utf8(readme))
    documents = [(path, read_utf8(path)) for path in files]
    known_names = {path.name for path, _ in documents}

    for entry in entries:
        declared_exists = entry.first_file in known_names
        if not declared_exists:
            diagnostics.append(
                Diagnostic(
                    readme,
                    entry.line,
                    "E_TERM_FILE",
                    f"首次出现的篇“{entry.first_file}”不是本章的 NN-*.md 文件名",
                )
            )

        pattern = term_pattern(entry.term)
        term_first: tuple[Path, int] | None = None
        for path, text in documents:
            match = pattern.search(text)
            if match:
                term_first = (path, line_at(text, match.start()))
                break
        if term_first is None:
            diagnostics.append(
                Diagnostic(readme, entry.line, "E_TERM_MISSING", f"正文未出现术语“{entry.label}”")
            )

        full_matches: list[tuple[Path, int]] = []
        for path, text in documents:
            for match in re.finditer(re.escape(entry.full_name), text):
                nested = any(
                    len(other.full_name) > len(entry.full_name)
                    and any(
                        outer.start() <= match.start() and match.end() <= outer.end()
                        for outer in re.finditer(re.escape(other.full_name), text)
                    )
                    for other in entries
                )
                if not nested:
                    full_matches.append((path, line_at(text, match.start())))

        if entry.sense is None:
            actual_first = term_first
        else:
            actual_first = full_matches[0] if full_matches else None
            if declared_exists:
                declared_text = next(text for path, text in documents if path.name == entry.first_file)
                if pattern.search(declared_text) is None:
                    diagnostics.append(
                        Diagnostic(
                            readme,
                            entry.line,
                            "E_TERM_MISSING",
                            f"声明篇 {entry.first_file} 未出现术语“{entry.label}”",
                        )
                    )
        if actual_first is not None and declared_exists and actual_first[0].name != entry.first_file:
            diagnostics.append(
                Diagnostic(
                    readme,
                    entry.line,
                    "E_TERM_FIRST",
                    f"“{entry.label}”实际首现于 {actual_first[0].name}:{actual_first[1]}，"
                    f"表中声明为 {entry.first_file}",
                )
            )

        if not full_matches:
            diagnostics.append(
                Diagnostic(
                    readme,
                    entry.line,
                    "E_FULL_MISSING",
                    f"“{entry.label}”的全称未在正文出现：{entry.full_name}",
                )
            )
            continue
        if len(full_matches) != 1:
            diagnostics.append(
                Diagnostic(
                    readme,
                    entry.line,
                    "E_FULL_COUNT",
                    f"“{entry.label}”的全称出现 {len(full_matches)} 次，应为 1 次；"
                    f"位置：{_locations(full_matches)}",
                )
            )
        if declared_exists:
            wrong_locations = [
                (path, line) for path, line in full_matches if path.name != entry.first_file
            ]
            if wrong_locations:
                diagnostics.append(
                    Diagnostic(
                        readme,
                        entry.line,
                        "E_FULL_LOCATION",
                        f"“{entry.label}”的全称应位于 {entry.first_file}；"
                        f"实际另有：{_locations(wrong_locations)}",
                    )
                )

    return TermResult(tuple(diagnostics), len(entries), len(documents))


def main(argv: Sequence[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", help="一个或多个章目录")
    args = parser.parse_args(argv)

    had_input_error = False
    had_violation = False
    for raw_path in args.paths:
        directory = Path(raw_path)
        try:
            result = check_chapter(directory)
        except InputError as exc:
            had_input_error = True
            print(f"ERROR {exc}", file=sys.stderr)
            continue
        for diagnostic in result.diagnostics:
            print(diagnostic.render())
        if result.diagnostics:
            had_violation = True
            print(f"FAIL {display_path(directory)}：{len(result.diagnostics)} 个术语问题")
        else:
            print(
                f"PASS {display_path(directory)}："
                f"{result.terms} 个术语，{result.files} 篇，首现与全称次数一致"
            )

    if had_input_error:
        return 2
    return 1 if had_violation else 0


if __name__ == "__main__":
    raise SystemExit(main())
