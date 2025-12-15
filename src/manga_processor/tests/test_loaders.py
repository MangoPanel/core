import unittest
import tempfile
import shutil
import os
from unittest import TestCase
from pathlib import Path

from filesys import MangaLoader, MangaNormalizer, PageLoader, OCRPageLoader, OCRResultLoader
from models import MangaPagePath
from models import Manga


class TestMangaLoader(TestCase):
    def setUp(self):
        self.temp_input_dir = Path(tempfile.mkdtemp())
        self.manga_norm = MangaNormalizer()
        self.manga_loader = MangaLoader(self.manga_norm)

    def tearDown(self):
        shutil.rmtree(self.temp_input_dir)

    def _make_dummy_files(self, filenames: list[str]):
        paths = []
        for name in filenames:
            path = self.temp_input_dir / name
            path.write_bytes(b"dummy image")
            paths.append(path)
        
        return paths

    def test_load_mixed_png_jpg(self):
        """
        Test that it can load and process a directory of mixed file types
        """
        dummy_file_names = ["file1.png", "abc2.jpg", "test3.png"]
        self._make_dummy_files(dummy_file_names)
        
        normalized_dir = self.temp_input_dir.parent / f"{self.temp_input_dir.name}_normalized"
        expected_page_paths = [
            MangaPagePath(index=0, path=normalized_dir / "0.png"),
            MangaPagePath(index=1, path=normalized_dir / "1.png"),
            MangaPagePath(index=2, path=normalized_dir / "2.png")
        ]

        manga = self.manga_loader.load_directory(self.temp_input_dir)
        
        self.assertIsInstance(manga, Manga)

        self.assertEqual(len(manga.pages), 3, "Should have loaded exactly 3 pages.")

        for actual, expected in zip(manga.pages, expected_page_paths):
            self.assertIsInstance(actual, MangaPagePath)
            self.assertEqual(actual.index, expected.index, f"Index mismatch for page {expected.index}.")

            self.assertEqual(os.path.normpath(actual.path), os.path.normpath(expected.path), f"Path mismatch for page {expected.index}.")
            
        for page_path in expected_page_paths:
            self.assertTrue(page_path.path.is_file(), f"file {page_path.index} is missing.")

        normalized_files = list(normalized_dir.glob("*"))
        self.assertEqual(len(normalized_files), 3, "Only 3 files should exist in the normalized directory")

    def test_load_unsupported_type(self):
        """
        Test that loading a directory with an unsupported file type raises an appriopiate exception.
        """

        self._make_dummy_files(["page1.png", "abecadlo.txt"])

        with self.assertRaises(ValueError):
            self.manga_loader.load_directory(self.temp_input_dir)


if __name__ == "__main__":
    unittest.main()
