import pymupdf
from pymupdf import Document
from manga_processor.models import MangaPagePath, MangaPage
import cv2
from cv2.typing import MatLike
from PIL import Image
from PIL.Image import Image as PILImage


class PageLoader:
    def load_for_cv2(self, manga_page_path: MangaPagePath) -> MangaPage[MatLike]:
        image = cv2.imread(f"{manga_page_path.path}")
        if image is None:
            raise ValueError(f"Failed to load image for opencv: {manga_page_path.path}")

        manga_page = MangaPage[MatLike](index=manga_page_path.index, image=image)
        return manga_page

    def load_for_pil(self, manga_page_path: MangaPagePath) -> MangaPage[PILImage]:
        image = Image.open(f"{manga_page_path.path}")
        manga_page = MangaPage[PILImage](index=manga_page_path.index, image=image)
        return manga_page

    def load_for_pymupdf(self, manga_page_path: MangaPagePath) -> MangaPage[Document]:
        image = pymupdf.open(manga_page_path.path)
        if image is None:
            raise ValueError(
                f"Failed to load image for pymupdf: {manga_page_path.path}"
            )
        manga_page = MangaPage[Document](index=manga_page_path.index, image=image)
        return manga_page
