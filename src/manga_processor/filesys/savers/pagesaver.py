from pathlib import Path
from cv2.typing import MatLike
from manga_processor.models import MangaPage
import cv2
from PIL.Image import Image as PILImage


class PageSaver:
    def save_to_img_from_cv2(
        self, page: MangaPage[MatLike], output_dir_path: Path
    ) -> None:
        output_dir_path.mkdir(parents=True, exist_ok=True)
        filepath = output_dir_path / f"{page.index}.png"
        cv2.imwrite(filename=f"{filepath}", img=page.image)

    def save_to_img_from_pil(
        self, page: MangaPage[PILImage], output_dir_path: Path
    ) -> None:
        output_dir_path.mkdir(parents=True, exist_ok=True)
        filepath = output_dir_path / f"{page.index}.png"
        page.image.save(fp=f"{filepath}")
