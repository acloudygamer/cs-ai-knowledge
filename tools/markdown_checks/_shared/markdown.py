"""Small Markdown primitives shared by the checkers.

This module deliberately contains no writing-policy rules. Those live in the
individual ``check_*.py`` entry points so their ownership stays discoverable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterator


_NUMBERED_FILE = re.compile(r"^(\d+)-.+\.md$", re.IGNORECASE)


class InputError(Exception):
    """An input path or file could not be inspected."""


@dataclass(frozen=True)
class Diagnostic:
    """One deterministic rule violation, ready for terminal display."""

    path: Path
    line: int | None
    code: str
    message: str

    def render(self) -> str:
        location = display_path(self.path)
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{location}: {self.code} {self.message}"


def display_path(path: Path) -> str:
    """Prefer a stable, forward-slash path relative to the invocation root."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def read_utf8(path: Path) -> str:
    """Read repository Markdown, accepting a UTF-8 BOM when present."""

    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"无法读取 {display_path(path)}：{exc}") from exc


def chapter_files(directory: Path) -> list[Path]:
    """Return direct ``NN-*.md`` children in numeric chapter order."""

    if not directory.is_dir():
        raise InputError(f"不是有效章目录：{display_path(directory)}")
    try:
        numbered: list[tuple[int, str, Path]] = []
        for child in directory.iterdir():
            if not child.is_file():
                continue
            match = _NUMBERED_FILE.match(child.name)
            if match:
                numbered.append((int(match.group(1)), child.name, child))
    except OSError as exc:
        raise InputError(f"无法枚举 {display_path(directory)}：{exc}") from exc
    if not numbered:
        raise InputError(f"章目录没有 NN-*.md 篇目：{display_path(directory)}")
    return [item[2] for item in sorted(numbered, key=lambda item: (item[0], item[1]))]


def iter_unfenced_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield lines outside backtick/tilde fences, retaining 1-based numbers."""

    fence: tuple[str, int] | None = None
    for line_number, line in enumerate(text.splitlines(), 1):
        if fence is not None:
            char, minimum_length = fence
            closing = rf"^ {{0,3}}{re.escape(char)}{{{minimum_length},}}[ \t]*$"
            if re.match(closing, line):
                fence = None
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if opening:
            marker = opening.group(1)
            fence = (marker[0], len(marker))
            continue
        yield line_number, line


def parse_atx_heading(line: str) -> tuple[int, str] | None:
    """Parse an ATX heading without interpreting headings indented as code."""

    match = re.match(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t]*$", line)
    if not match:
        return None
    title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
    return len(match.group(1)), title
