import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzer import AnalysisResult, analyze_directory, count_characters, generate_report

class AnalyzerTests(unittest.TestCase):
    def test_count_characters_ignores_whitespace(self):
        self.assertEqual(count_characters("你好 world\n\t"), 7)

    def test_analyze_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.md").write_text("你好\n世界", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.markdown").write_text("abc", encoding="utf-8")
            (root / "ignored.txt").write_text("ignored", encoding="utf-8")
            result = analyze_directory(root)
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(len(result.files), 2)
            self.assertEqual(result.total_character_count, 7)
            self.assertIsNotNone(result.largest_file)
            self.assertIsNotNone(result.latest_file)

    def test_empty_directory_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report = generate_report(analyze_directory(Path(directory)))
            self.assertIn("Markdown files: 0", report)
            self.assertIn("No Markdown files found.", report)

    def test_largest_file_is_selected_by_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            small = root / "small.md"
            large = root / "large.md"
            small.write_text("small", encoding="utf-8")
            large.write_text("large content", encoding="utf-8")

            result = analyze_directory(root)

            self.assertEqual(result.largest_file.path, large)

    def test_latest_file_is_selected_by_modified_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            older = root / "older.md"
            latest = root / "latest.md"
            older.write_text("older", encoding="utf-8")
            latest.write_text("latest", encoding="utf-8")
            older.touch()
            latest.touch()
            import os
            os.utime(older, (1000, 1000))
            os.utime(latest, (2000, 2000))

            result = analyze_directory(root)

            self.assertEqual(result.latest_file.path, latest)

    def test_markdown_extensions_are_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lower.md").write_text("one", encoding="utf-8")
            (root / "mixed.MARKDOWN").write_text("two", encoding="utf-8")
            (root / "ignored.txt").write_text("three", encoding="utf-8")

            result = analyze_directory(root)

            self.assertEqual(len(result.files), 2)

    def test_missing_directory_raises_file_not_found(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaises(FileNotFoundError):
                analyze_directory(missing)

    def test_report_contains_core_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "document.md").write_text("report content", encoding="utf-8")

            report = generate_report(analyze_directory(root))

            self.assertIn("Markdown files: 1", report)
            self.assertIn("Total characters:", report)
            self.assertIn("Largest File", report)
            self.assertIn("Most Recently Modified File", report)

    def test_read_errors_are_recorded_as_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "document.md"
            document.write_text("valid", encoding="utf-8")
            unreadable = root / "unreadable.md"
            unreadable.write_bytes(b"\xff\xfe")

            result = analyze_directory(root)
            report = generate_report(result)

            self.assertEqual(len(result.files), 1)
            self.assertEqual(result.files[0].path, document)
            self.assertEqual(len(result.warnings), 1)
            self.assertIn("Warnings", report)
            self.assertIn("unreadable.md", report)

if __name__ == "__main__":
    unittest.main()
