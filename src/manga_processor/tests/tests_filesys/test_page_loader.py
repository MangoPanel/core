import unittest
from unittest import TestCase

import cv2
from cv2.typing import MatLike
from filesys import PageLoader
from pathlib import Path
from models import MangaPage, MangaPagePath
from PIL.Image import Image as PILImage
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "../test_data/png/"


class TestPageLoader(TestCase):
    def setUp(self):
        self.pageloader = PageLoader()

    def test_loading_opencv(self):
        image_path = TEST_DATA_DIR / "000.png"
        manga_page_path = MangaPagePath(index=0, path=image_path)
        manga_page = self.pageloader.load_for_cv2(manga_page_path=manga_page_path)

        self.assertIsInstance(
            manga_page, MangaPage, "Loaded type is not that of manga page"
        )
        self.assertIsInstance(
            manga_page.image,
            MatLike,
            "The image of the manga page is not the type of opencv",
        )

        cv2_image = cv2.imread(f"{image_path}")

        self.assertEqual(
            manga_page.image.all(),
            cv2_image.all(),
            "Image loading for opencv is not equal to opencv loading",
        )

    def test_loading_pil(self):
        image_path = TEST_DATA_DIR / "000.png"
        manga_page_path = MangaPagePath(index=0, path=image_path)
        manga_page = self.pageloader.load_for_pil(manga_page_path=manga_page_path)

        self.assertIsInstance(
            manga_page, MangaPage, "Loaded type is not that of manga page"
        )
        self.assertIsInstance(
            manga_page.image,
            PILImage,
            "The image of the manga page is not the type of pil's image",
        )

        pil_image = Image.open(f"{image_path}")

        self.assertEqual(
            manga_page.image,
            pil_image,
            "Image loading for opencv is not equal to opencv loading",
        )


if __name__ == "__main__":
    unittest.main()
