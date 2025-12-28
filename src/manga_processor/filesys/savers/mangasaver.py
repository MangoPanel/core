import pymupdf
import shutil
from pathlib import Path
from manga_processor.filesys import PageLoader
from manga_processor.models import Manga


class MangaSaver:
    def __init__(self):
        self.page_loader = PageLoader()

    def save_to_pdf(self, manga: Manga, output_path: Path) -> None:
        doc = pymupdf.open()

        for page_path in manga.pages:
            manga_page = self.page_loader.load_for_pymupdf(manga_page_path=page_path)
            img = manga_page.image
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, imgPDF, 0)
        

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)

    def save_to_png_dir(self, manga: Manga, output_path: Path) -> None:
        if output_path.is_file():
            raise NotADirectoryError(
                f"Failed saving manga to png directory. {output_path} is a file"
            )

        output_path.mkdir(parents=True, exist_ok=True)

        for page_path in manga.pages:
            shutil.copy(page_path.path, output_path, follow_symlinks=True)
