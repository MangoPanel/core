import pymupdf
import os
from pathlib import Path

class Manga:
    def __init__(self, path: Path):
        self.path = path
        self._normalize_to_png()
        self._pages = sorted(path.iterdir())

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._pages):
            raise StopIteration
        self._index = self._index + 1
        return self.get_page(self._index)

    def __fspath__(self):
        return self.path

    def get_page(self, index):
        file_path = self.path / index
        with open(file_path) as page:
            return page

    def _normalize_to_png(self):
        for i, file in sorted(self.path.iterdir()):
            if not file.is_file():
                raise IsADirectoryError("Not a file. This is probably a directory")
            ext = file.suffix
            match ext:
                case ".pdf":
                    try:
                        doc = pymupdf.open(file)
                    except:
                        raise FileNotFoundError(f"{file} failed to open")
                    for page in doc:
                        pix = page.get_pixmap()
                            pix.save(f"{page.number:03d}.png")
                case ".jpg" | ".jpeg" | ".png":
                        file.rename(f"{i:03d}.png")
                case _:
                    raise pymupdf.FileDataError("Invalid data type")
        
    def save_to_pdf(self, output_path=None):
        if not output_path:
            output_path = self.path / pdf /

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

    def paint_rectangle(self, rect):
        """
        Paint rectangle on given coordinates
        """
        ...


