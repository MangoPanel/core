import re
from re import Pattern
from manga_processor.filesys import OCRPageLoader, OCRPageSaver
from manga_processor.filesys.loaders.ocrresloader import OCRResultLoader
from manga_processor.models import OCRPage
from manga_processor.models.types import OCRResult


class JPTextCleaner:
    # Regex for Japanese characters:
    # Hiragana: \u3040-\u309F
    # Katakana: \u30A0-\u30FF
    # Kanji: \u4E00-\u9FFF
    jp_regex: Pattern[str] = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]")

    def __init__(
        self,
        ocr_page_loader: OCRPageLoader,
        ocr_page_saver: OCRPageSaver,
        ocr_result_loader: OCRResultLoader,
    ) -> None:
        self.ocr_page_loader: OCRPageLoader = ocr_page_loader
        self.ocr_page_saver: OCRPageSaver = ocr_page_saver
        self.ocr_result_loader: OCRResultLoader = ocr_result_loader

    def clean_ocr_res(self, ocr_res: OCRResult) -> OCRResult:

        output_dir = ocr_res.dir_path / "clean_ocr"

        for page_path in ocr_res.ocr_pages:
            page: OCRPage = self.ocr_page_loader.load_json(page_path)

            new_polys, new_texts, new_scores = [], [], []
            for dt_poly, rec_text, rec_score in page:
                clean_text: str | None = self._clean_text(rec_text)
                if clean_text is not None:
                    new_polys.append(dt_poly)
                    new_texts.append(clean_text)
                    new_scores.append(rec_score)

            new_page = OCRPage(page.index, new_polys, new_texts, new_scores)
            self.ocr_page_saver.save_to_json(new_page, output_dir)

        return self.ocr_result_loader.load_directory(output_dir)

    def _clean_text(self, text: str) -> str | None:
        text = text.strip()
        if not text:
            return None

        if self.jp_regex.search(text):
            return text

        return None
