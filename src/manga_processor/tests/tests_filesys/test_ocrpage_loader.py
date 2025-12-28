from dataclasses import asdict
import unittest
import json
from unittest import TestCase
from pathlib import Path

from manga_processor.filesys import OCRPageLoader
from manga_processor.models import OCRPagePath


SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "../test_data/json/json_cleaned/"

class TestOCRPageLoader(TestCase):
    def setUp(self):
        self.ocrpageloader = OCRPageLoader()

    def test_load_ocrpage_from_json(self):
        file_path = TEST_DATA_DIR / "000_res.json"

        ocr_page_path = OCRPagePath(index=0, path=file_path)
        ocr_page = self.ocrpageloader.load_json(ocr_page_path=ocr_page_path)

        with file_path.open("r", encoding="utf-8") as file:
            valid_data = json.load(file)

        ocr_page_dict = asdict(ocr_page)

        self.assertEqual(ocr_page_dict, valid_data)


