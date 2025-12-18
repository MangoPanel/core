import unittest
import json
import tempfile
import shutil
from unittest import TestCase
from pathlib import Path

from filesys import OCRPageSaver
from models import OCRPagePath


SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "../test_data/json/"

class TestOCRPageSaver(TestCase):
    def setUp(self):
        self.temp_output_dir = Path(tempfile.mkdtemp())
        self.ocrpagesaver = OCRPageSaver()

    def tearDown(self):
        shutil.rmtree(self.temp_output_dir)

    def test_save_ocrpage_from_json(self):
        ocr_page_path = OCRPagePath(index=0, path=TEST_DATA_DIR / "000_res.json")

        with ocr_page_path.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        
        output_file_path = self.temp_output_dir / "000_res.json"
        self.ocrpagesaver.save_from_dirty_dict(data_dict=data, output_path=output_file_path, index=0)

        with output_file_path.open("r", encoding="utf-8") as file:
            saved_data = json.load(file)

        valid_file_path = TEST_DATA_DIR / "json_cleaned" / "000_res.json"
        with valid_file_path.open("r", encoding="utf-8") as file:
            valid_data = json.load(file)

        self.assertEqual(saved_data, valid_data)
