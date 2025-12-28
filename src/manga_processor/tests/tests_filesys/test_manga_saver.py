import unittest
import tempfile
import shutil
from unittest import TestCase
from pathlib import Path
import pymupdf
import random

from manga_processor.filesys import MangaSaver
from manga_processor.models import MangaPagePath
from manga_processor.models import Manga

SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "../test_data/png/"


class TestMangaLoader(TestCase):
    def setUp(self):
        self.temp_input_dir = Path(tempfile.mkdtemp())
        self.manga_saver = MangaSaver()

    def tearDown(self):
        shutil.rmtree(self.temp_input_dir)

    def _make_dummy_files(self, filenames: list[str]):
        paths = []
        if not TEST_DATA_DIR.exists():
            raise FileNotFoundError(f"Test data directory not found: {TEST_DATA_DIR}")

        png_files = list(TEST_DATA_DIR.glob("*.png"))
        if len(png_files) < 3:
            raise FileNotFoundError(
                f"Not enough PNG files in test data directory. Found {len(png_files)}, need at least 3."
            )

        selected_files = random.sample(png_files, 3)

        for i, name in enumerate(filenames):
            source_path = selected_files[i]
            dest_path = self.temp_input_dir / name
            dest_path.write_bytes(source_path.read_bytes())
            paths.append(dest_path)

        return paths

    def _make_dummy_manga(self, paths: list[MangaPagePath]):
        manga = Manga(pages=paths, title="The Great Test Manga")
        return manga

    def test_save_manga_pdf(self):
        """
        Test that it can save manga to pdf
        """
        dummy_file_names = ["0.png", "1.png", "2.png"]
        paths = self._make_dummy_files(dummy_file_names)
        page_paths = [
            MangaPagePath(index=i, path=Path(path)) for i, path in enumerate(paths)
        ]
        dummy_manga = self._make_dummy_manga(paths=page_paths)

        save_path = (
            self.temp_input_dir.parent
            / f"{self.temp_input_dir.name}_saved"
            / "manga.pdf"
        )

        self.manga_saver.save_to_pdf(manga=dummy_manga, output_path=save_path)

        self.assertTrue(
            save_path.is_file(), "the pdf file is missing or did not get saved"
        )
        self.assertEqual(
            save_path.suffix, ".pdf", "the saved file should be in pdf format"
        )
        saved_files = list(save_path.parent.glob("*"))
        self.assertEqual(
            len(saved_files), 1, "Only 1 file should exist in the save directory"
        )

        doc = pymupdf.open(save_path)
        page_count = doc.page_count
        self.assertEqual(
            page_count, 3, f"Document should have 3 pages while it has {page_count}"
        )


if __name__ == "__main__":
    unittest.main()
