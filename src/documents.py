from abc import abstractmethod
from io import  BytesIO
from typing import Dict, Any, Generic, TypeVar
import pymupdf
from pathlib import Path
import json

T = TypeVar("T")
class IterablePageCollection(Generic[T]):
    def __init__(self, path: Path):
        self.path = path
        self._create_dir_structure()

    def _create_dir_structure(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)

    def __iter__(self):
        self._pages = sorted(self.path.iterdir())
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._pages):
            raise StopIteration
        page = self.get_page(self._index)
        self._index = self._index + 1
        return page

    def __fspath__(self):
        return self.path

    @abstractmethod
    def get_page(self, index) -> T: ...


class Manga(IterablePageCollection[bytes]):
    def __init__(self, path: Path):
        super().__init__(path)
        self._normalize_to_png(path)

    def _normalize_to_png(self, path) -> None:
        for i, file in enumerate(sorted(path.iterdir())):
            if not file.is_file():
                raise IsADirectoryError("Not a file. This is probably a directory")
            ext = file.suffix
            match ext:
                case ".pdf":
                    try:
                        doc = pymupdf.open(file)
                    except Exception:
                        raise FileNotFoundError(f"PDF {file} failed to open")
                    for page in doc:
                        pix = page.get_pixmap()
                        pix.save(self.path / f"{page.number:03d}.png")
                case ".jpg" | ".jpeg" | ".png":
                    file.rename(self.path / f"{i:03d}.png")
                case _:
                    raise pymupdf.FileDataError("Invalid data type")

    def get_page(self, index) -> bytes:
        file_path = self._pages[index]
        with open(file_path, mode="rb") as page:
            return page.read()

    def save_to_pdf(self, output_path=None) -> None:
        if not output_path:
            output_path = self.path / "pdf.pdf"

        doc = pymupdf.open()

        for page in self:
            img = pymupdf.open("png", page)
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, imgPDF, 0)

        doc.save(output_path)


class MangaJSONRepresentation(IterablePageCollection[Dict[str, Any]]):
    def __init__(self, path: Path):
        super().__init__(path)

    def get_page(self, index) -> Dict[str, Any]:
        file_path = self._pages[index]
        with open(file_path, "r") as json_page:
            return json.load(json_page)
