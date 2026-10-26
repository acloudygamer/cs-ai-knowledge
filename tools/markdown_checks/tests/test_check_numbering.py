from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from tools.markdown_checks.check_numbering import check_file, main, parse_chinese_number


class NumberingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def write_markdown(self, text: str) -> Path:
        path = self.root / "article.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_sequences_and_fenced_examples(self) -> None:
        path = self.write_markdown(
            """# 示例

## 一、第一节
### 1. 小节
```text
## 九、图里的假标题
### 9. 图里的假小节
```
## 二、第二节
### 1. 重新编号
### 2. 连续编号
## 附录
无编号内容不参与检查。
"""
        )
        result = check_file(path)
        self.assertEqual(result.diagnostics, ())
        self.assertEqual((result.sections, result.subsections), (2, 3))

    def test_sequence_errors_are_local_and_have_line_numbers(self) -> None:
        path = self.write_markdown(
            """## 一、第一节
### 1. 正常
### 3. 跳号
## 三、第二节跳号
### 2. 未从一开始
"""
        )
        result = check_file(path)
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["E_SUBSECTION_SEQUENCE", "E_SECTION_SEQUENCE", "E_SUBSECTION_SEQUENCE"],
        )
        self.assertEqual([item.line for item in result.diagnostics], [3, 4, 5])

    def test_numbered_subsection_requires_numbered_section(self) -> None:
        path = self.write_markdown("## 附录\n### 1. 没有编号父节\n")
        result = check_file(path)
        self.assertEqual([item.code for item in result.diagnostics], ["E_SUBSECTION_WITHOUT_SECTION"])

    def test_chinese_numbers_cover_two_digits(self) -> None:
        expected = {
            "十": 10,
            "十一": 11,
            "二十": 20,
            "二十一": 21,
            "一百零二": 102,
            "一千零一": 1001,
            "一千零一十": 1010,
        }
        self.assertEqual({key: parse_chinese_number(key) for key in expected}, expected)

    def test_noncanonical_chinese_numbers_are_rejected(self) -> None:
        for text in ("一二", "十十", "一百百", "一十", "一百零二十", "一千零一百", "两"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_chinese_number(text)

        path = self.write_markdown("## 一、正常\n## 一二、非法编号\n")
        result = check_file(path)
        self.assertEqual([item.code for item in result.diagnostics], ["E_SECTION_NUMBER"])

    def test_legacy_decimal_headings_are_skipped_not_passed_as_sections(self) -> None:
        path = self.write_markdown("### 4.1 旧格式\n### 4.2 旧格式\n")
        result = check_file(path)
        self.assertEqual(result.diagnostics, ())
        self.assertEqual((result.sections, result.subsections), (0, 0))

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main([str(path)]), 0)
        self.assertIn("SKIP", stdout.getvalue())

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["--require-numbered", str(path)]), 1)
        self.assertIn("FAIL", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
