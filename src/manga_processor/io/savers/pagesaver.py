from pathlib import Path
from cv2.typing import MatLike
from models import MangaPage
import cv2
from PIL.Image import Image as PILImage

class PageSaver():
    def save_from_cv2(self, page: MangaPage[MatLike], path: Path) -> None:
        filepath = path / f"{page.index}.png"
        cv2.imwrite(filename=f"{filepath}", img=page.image)
    
    def save_from_pil(self, page: MangaPage[PILImage], path: Path) -> None:
        filepath = path / f"{page.index}.png"
        page.image.save(fp=f"{filepath}")
