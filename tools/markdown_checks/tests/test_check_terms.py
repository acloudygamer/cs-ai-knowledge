from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from tools.markdown_checks.check_terms import check_chapter, main, term_pattern


class TermTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def write_chapter(self, rows: list[str], documents: dict[str, str]) -> None:
        table = "\n".join(rows)
        (self.root / "README.md").write_text(
            "# 示例章\n\n## 本章术语表\n\n"
            "| 术语（最简形式） | 全称 | 首次出现的篇 |\n"
            "| --- | --- | --- |\n"
            f"{table}\n",
            encoding="utf-8",
        )
        for name, text in documents.items():
            (self.root / name).write_text(text, encoding="utf-8")

    def test_valid_manifest(self) -> None:
        self.write_chapter(
            [
                "| CF | Carry Flag | 01-a.md |",
                "| NaN | Not a Number | 02-b.md |",
            ],
            {
                "01-a.md": "进位标志（Carry Flag，CF）。\n",
                "02-b.md": "继续使用 CF。非数（Not a Number，NaN）。\n",
            },
        )
        result = check_chapter(self.root)
        self.assertEqual(result.diagnostics, ())
        self.assertEqual((result.terms, result.files), (2, 2))

    def test_nested_full_names_are_counted_independently(self) -> None:
        self.write_chapter(
            [
                "| VA | Virtual Address | 01-a.md |",
                "| UVA | Unified Virtual Address Space | 02-b.md |",
                "| UMA | Uniform Memory Access | 01-a.md |",
                "| NUMA | Non-Uniform Memory Access | 01-a.md |",
            ],
            {
                "01-a.md": "虚拟地址（Virtual Address，VA）。均匀访存（Uniform Memory Access，UMA）与非均匀访存（Non-Uniform Memory Access，NUMA）。\n",
                "02-b.md": "统一虚拟地址空间（Unified Virtual Address Space，UVA）。\n",
            },
        )
        result = check_chapter(self.root)
        self.assertEqual(result.diagnostics, ())

    def test_actual_first_file_and_full_name_location_are_checked(self) -> None:
        self.write_chapter(
            ["| CF | Carry Flag | 02-b.md |"],
            {
                "01-a.md": "进位标志（Carry Flag，CF）。\n",
                "02-b.md": "只使用 CF。\n",
            },
        )
        codes = {item.code for item in check_chapter(self.root).diagnostics}
        self.assertIn("E_TERM_FIRST", codes)
        self.assertIn("E_FULL_LOCATION", codes)

    def test_missing_and_repeated_full_name(self) -> None:
        self.write_chapter(
            ["| CF | Carry Flag | 01-a.md |"],
            {"01-a.md": "只写 CF。\n"},
        )
        self.assertIn("E_FULL_MISSING", {item.code for item in check_chapter(self.root).diagnostics})

        self.write_chapter(
            ["| CF | Carry Flag | 01-a.md |"],
            {
                "01-a.md": "进位标志（Carry Flag，CF）。\n",
                "02-b.md": "重复写 Carry Flag。\n",
            },
        )
        codes = {item.code for item in check_chapter(self.root).diagnostics}
        self.assertIn("E_FULL_COUNT", codes)
        self.assertIn("E_FULL_LOCATION", codes)

    def test_ascii_figure_counts_as_first_occurrence(self) -> None:
        self.write_chapter(
            ["| CF | Carry Flag | 02-b.md |"],
            {
                "01-a.md": "```text\nCF=1\n```\n",
                "02-b.md": "进位标志（Carry Flag，CF）。\n",
            },
        )
        result = check_chapter(self.root)
        self.assertEqual([item.code for item in result.diagnostics], ["E_TERM_FIRST"])

    def test_duplicate_term_and_missing_declared_file(self) -> None:
        self.write_chapter(
            ["| CF | Carry Flag | 01-a.md |", "| CF | Carry Flag | 01-a.md |"],
            {"01-a.md": "进位标志（Carry Flag，CF）。\n"},
        )
        self.assertIn("E_DUPLICATE_TERM", {item.code for item in check_chapter(self.root).diagnostics})

        self.write_chapter(
            ["| CF | Carry Flag | 03-missing.md |"],
            {"01-a.md": "进位标志（Carry Flag，CF）。\n"},
        )
        self.assertIn("E_TERM_FILE", {item.code for item in check_chapter(self.root).diagnostics})

    def test_missing_table_and_empty_cells(self) -> None:
        (self.root / "README.md").write_text("# 没有术语表\n", encoding="utf-8")
        (self.root / "01-a.md").write_text("正文\n", encoding="utf-8")
        self.assertIn("E_TABLE_MISSING", {item.code for item in check_chapter(self.root).diagnostics})

        self.write_chapter(["| CF |  | 01-a.md |"], {"01-a.md": "CF\n"})
        self.assertIn("E_TABLE_CELL", {item.code for item in check_chapter(self.root).diagnostics})

    def test_table_cannot_rejoin_across_prose_or_blank_lines(self) -> None:
        (self.root / "README.md").write_text(
            "# 示例章\n\n## 本章术语表\n\n"
            "| 术语（最简形式） | 全称 | 首次出现的篇 |\n"
            "这不是表格的一部分。\n"
            "| --- | --- | --- |\n"
            "| CF | Carry Flag | 01-a.md |\n",
            encoding="utf-8",
        )
        (self.root / "01-a.md").write_text("进位标志（Carry Flag，CF）。\n", encoding="utf-8")
        result = check_chapter(self.root)
        self.assertEqual([item.code for item in result.diagnostics], ["E_TABLE_SEPARATOR"])

        (self.root / "README.md").write_text(
            "# 示例章\n\n## 本章术语表\n\n"
            "| 术语（最简形式） | 全称 | 首次出现的篇 |\n"
            "| --- | --- | --- |\n"
            "| CF | Carry Flag | 01-a.md |\n\n"
            "| NaN | Not a Number | 02-b.md |\n",
            encoding="utf-8",
        )
        (self.root / "02-b.md").write_text("非数（Not a Number，NaN）。\n", encoding="utf-8")
        codes = {item.code for item in check_chapter(self.root).diagnostics}
        self.assertIn("E_TABLE_CONTIGUITY", codes)

    def test_fenced_blocks_cannot_join_table_rows(self) -> None:
        (self.root / "README.md").write_text(
            "# 示例章\n\n## 本章术语表\n\n"
            "| 术语（最简形式） | 全称 | 首次出现的篇 |\n"
            "~~~text\n被围栏隔断\n~~~\n"
            "| --- | --- | --- |\n"
            "| CF | Carry Flag | 01-a.md |\n",
            encoding="utf-8",
        )
        (self.root / "01-a.md").write_text("进位标志（Carry Flag，CF）。\n", encoding="utf-8")
        result = check_chapter(self.root)
        self.assertEqual([item.code for item in result.diagnostics], ["E_TABLE_SEPARATOR"])

        (self.root / "README.md").write_text(
            "# 示例章\n\n## 本章术语表\n\n"
            "| 术语（最简形式） | 全称 | 首次出现的篇 |\n"
            "| --- | --- | --- |\n"
            "| CF | Carry Flag | 01-a.md |\n"
            "~~~text\n被围栏隔断\n~~~\n"
            "| NaN | Not a Number | 02-b.md |\n",
            encoding="utf-8",
        )
        (self.root / "02-b.md").write_text("非数（Not a Number，NaN）。\n", encoding="utf-8")
        codes = {item.code for item in check_chapter(self.root).diagnostics}
        self.assertIn("E_TABLE_CONTIGUITY", codes)

    def test_indented_code_example_is_not_a_manifest(self) -> None:
        (self.root / "README.md").write_text(
            "# 示例章\n\n## 本章术语表\n\n"
            "    | 术语（最简形式） | 全称 | 首次出现的篇 |\n"
            "    | --- | --- | --- |\n"
            "    | CF | Carry Flag | 01-a.md |\n",
            encoding="utf-8",
        )
        (self.root / "01-a.md").write_text("进位标志（Carry Flag，CF）。\n", encoding="utf-8")
        result = check_chapter(self.root)
        self.assertEqual(result.terms, 0)
        self.assertEqual([item.code for item in result.diagnostics], ["E_TABLE_HEADER"])

    def test_same_term_with_distinct_senses(self) -> None:
        self.write_chapter(
            [
                "| CAS（内存列访问） | Column Access Strobe | 01-a.md |",
                "| CAS（比较并交换） | Compare-And-Swap | 02-b.md |",
            ],
            {
                "01-a.md": "列访问（Column Access Strobe，CAS）。\n",
                "02-b.md": "比较并交换（Compare-And-Swap，CAS）。\n",
            },
        )
        result = check_chapter(self.root)
        self.assertEqual(result.diagnostics, ())
        self.assertEqual(result.terms, 2)

    def test_each_sense_checks_its_own_first_file_and_full_name(self) -> None:
        self.write_chapter(
            [
                "| CAS（内存列访问） | Column Access Strobe | 02-b.md |",
                "| CAS（比较并交换） | Compare-And-Swap | 01-a.md |",
            ],
            {
                "01-a.md": "列访问（Column Access Strobe，CAS）。\n",
                "02-b.md": "比较并交换（Compare-And-Swap，CAS）。\n",
            },
        )
        diagnostics = check_chapter(self.root).diagnostics
        self.assertEqual(
            {item.code for item in diagnostics},
            {"E_TERM_FIRST", "E_FULL_LOCATION"},
        )
        first_messages = [item.message for item in diagnostics if item.code == "E_TERM_FIRST"]
        full_messages = [item.message for item in diagnostics if item.code == "E_FULL_LOCATION"]
        self.assertTrue(any("CAS（内存列访问）" in message for message in first_messages))
        self.assertTrue(any("CAS（比较并交换）" in message for message in full_messages))

    def test_senses_must_be_qualified_and_unique(self) -> None:
        self.write_chapter(
            [
                "| CAS | Column Access Strobe | 01-a.md |",
                "| CAS（比较并交换） | Compare-And-Swap | 02-b.md |",
            ],
            {
                "01-a.md": "列访问（Column Access Strobe，CAS）。\n",
                "02-b.md": "比较并交换（Compare-And-Swap，CAS）。\n",
            },
        )
        self.assertIn("E_TERM_SENSE", {item.code for item in check_chapter(self.root).diagnostics})

        self.write_chapter(
            [
                "| CAS（比较并交换） | Compare-And-Swap | 02-b.md |",
                "| CAS（比较并交换） | Compare-And-Swap | 02-b.md |",
            ],
            {"02-b.md": "比较并交换（Compare-And-Swap，CAS）。\n"},
        )
        self.assertIn("E_DUPLICATE_TERM", {item.code for item in check_chapter(self.root).diagnostics})

    def test_ascii_boundaries_and_exit_codes(self) -> None:
        self.assertIsNone(term_pattern("Inf").search("Infinity"))
        self.assertIsNotNone(term_pattern("Inf").search("（Infinity，Inf）"))

        self.write_chapter(
            ["| CF | Carry Flag | 01-a.md |"],
            {"01-a.md": "进位标志（Carry Flag，CF）。\n"},
        )
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main([str(self.root)]), 0)
        self.assertIn("PASS", stdout.getvalue())

        self.write_chapter(
            ["| CF | Carry Flag | 01-a.md |"],
            {"01-a.md": "只写 CF，没有全称。\n"},
        )
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main([str(self.root)]), 1)
        self.assertIn("E_FULL_MISSING", stdout.getvalue())
        self.assertIn("FAIL", stdout.getvalue())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main([str(self.root / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()
