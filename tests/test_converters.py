"""Converter validation and local text conversion tests."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import media_converter
import office_converter


class ConverterTests(unittest.TestCase):
    def test_media_targets(self):
        self.assertEqual(media_converter.MediaConverter.normalize_format(".MP4"), "mp4")
        self.assertEqual(media_converter.MediaConverter.normalize_format("mp3"), "mp3")
        with self.assertRaises(media_converter.MediaValidationError):
            media_converter.MediaConverter.normalize_format("exe")

    def test_media_default_path(self):
        path = media_converter.MediaConverter.default_output_path("clip.mkv", "mp4")
        self.assertEqual(path.suffix, ".mp4")

    def test_office_targets(self):
        self.assertEqual(office_converter.OfficeConverter.targets_for("deck.pptx"),
                         ["pdf", "png", "jpg", "txt"])
        self.assertIn("csv", office_converter.OfficeConverter.targets_for("book.xlsx"))
        self.assertIn("docx", office_converter.OfficeConverter.targets_for("notes.txt"))

    def test_office_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "notes.txt"
            src.write_text("hello", encoding="utf-8")
            conv = office_converter.OfficeConverter()
            src, target, out = conv.validate(src, "xlsx", Path(tmp) / "notes.xlsx")
            self.assertEqual(target, "xlsx")
            self.assertEqual(out.suffix, ".xlsx")
            with self.assertRaises(office_converter.OfficeConversionError):
                conv.validate(src, "xlsx", Path(tmp) / "wrong.pdf")

    def test_text_to_xlsx(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "notes.txt"
            src.write_text("a\tb\n1\t2\n", encoding="utf-8")
            out = Path(tmp) / "notes.xlsx"
            conv = office_converter.OfficeConverter()
            result = conv.convert(src, "xlsx", out)
            self.assertTrue(result.outputs[0].is_file())

    def test_json_sheets(self):
        conv = office_converter.OfficeConverter()
        sheets = conv._json_sheets([{"name": "A", "score": 10},
                                    {"name": "B", "score": 20}])
        self.assertEqual(sheets[0][1][0], ["name", "score"])
        self.assertEqual(sheets[0][1][1], ["A", 10])


if __name__ == "__main__":
    unittest.main()
