from typing import override
import pymupdf
from pathlib import Path
import json


class IterablePageCollection:
    def __init__(self, path: Path):
        self.path = path
        self._pages = sorted(path.iterdir())

    def __iter__(self):
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
    
    def get_page(self, index):
        file_path = self._pages[index]
        with open(file_path) as page:
            return page

class Manga(IterablePageCollection):
    def __init__(self, path: Path, work_dir: Path = None):
        self.work_dir = work_dir or path
        self._normalize_to_png(path)
        super().__init__(self.work_dir)

    def _normalize_to_png(self, path):
        import os
        os.makedirs(self.work_dir, exist_ok=True)
        
        for i, file in enumerate(sorted(path.iterdir())):
            if not file.is_file():
                raise IsADirectoryError("Not a file. This is probably a directory")
            ext = file.suffix
            match ext:
                case ".pdf":
                    try:
                        doc = pymupdf.open(file)
                    except Exception:
                        raise FileNotFoundError(f"{file} failed to open")
                    for page in doc:
                        pix = page.get_pixmap()
                        pix.save(str(self.work_dir / f"{page.number:03d}.png"))
                case ".jpg" | ".jpeg" | ".png":
                    import shutil
                    shutil.copy2(file, self.work_dir / f"{i:03d}.png")
                case _:
                    raise pymupdf.FileDataError("Invalid data type")

    def save_to_pdf(self, output_path=None):
        if not output_path:
            output_path = "output/test_pdf.pdf"

        doc = pymupdf.open()

        for page in self._pages:
            img = pymupdf.open(page)
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, imgPDF, 0)

        doc.save(output_path)


class MangaJSONRepresentation(IterablePageCollection):
    def __init__(self, path: Path):
        super().__init__(path)
        #only json files
        self._pages = [p for p in self._pages if p.suffix == '.json']

    @override
    def get_page(self, index):
        file_path = self._pages[index]
        with open(file_path) as json_page:
            return json.load(json_page)
