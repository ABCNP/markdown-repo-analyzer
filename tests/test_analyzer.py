import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzer import analyze_directory, count_characters, generate_report

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
            self.assertEqual(len(result["files"]), 2)
            self.assertEqual(result["total_character_count"], 7)
            self.assertIsNotNone(result["largest_file"])
            self.assertIsNotNone(result["latest_file"])

    def test_empty_directory_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report = generate_report(analyze_directory(Path(directory)))
            self.assertIn("Markdown 文件数：0", report)
            self.assertIn("暂无 Markdown 文件。", report)

if __name__ == "__main__":
    unittest.main()
