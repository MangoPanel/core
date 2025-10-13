import pymupdf
import os
from pathlib import Path

class Document:
    def __init__(self, path: Path):
        self.path = path
        self._normalize_to_img()
        self._pages = sorted(path.iterdir())

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._pages):
            raise StopIteration
        self._index = self._index + 1
        return self.get_page(self._index)

    def get_page(self, index):
        file_path = self.path / index
        with open(file_path) as page:
            return page

    def _normalize_to_img(self):
        try:
            for file in self.path.iterdir():
                """TODO"""
                match ext:
                    case ".pdf":
                        pdf_page = pymupdf.open(file_path)
                        doc.insert_pdf(pdf_page)
                        pdf_page.close()
                    case ".jpg" | ".jpeg" | ".png":
                        self._convert_img_to_page(f, filedir, doc)
                    case _:
                        raise pymupdf.FileDataError("Invalid data type")
        

    def save_to_pdf(self, output_path=None):
            
                        
            doc.save(output_path)
        except Exception as e:
            print("Failed saving to pdf:", e)
            raise

    def _convert_img_to_page(self, file, imgdir, doc):

        img_path = os.path.join(imgdir, file)
        try:
            img = pymupdf.open(img_path)
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, imgPDF, 0)
        except Exception as e:
            print(f"Failed while processing {img_path} with:", e)
            raise

    def paint_rectangle(self, rect):
        """
        Paint rectangle on given coordinates
        """
        ...

    
