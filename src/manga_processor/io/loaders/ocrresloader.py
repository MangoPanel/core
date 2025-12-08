from pathlib import Path
from models import OCRPagePath, OCRPage, OCRResult
import json

class OCRPageLoader():
    def load_json(self, ocr_page_path: OCRPagePath) -> OCRPage:
        with ocr_page_path.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        page = OCRPage(**data)
        return page

class OCRResultLoader():
    def load_directory(self, path: Path) -> OCRResult:
        ocr_pages: list[OCRPagePath] = []
        for i, file in enumerate(sorted(path.iterdir())):
            if file.suffix.lower() == ".json":
                ocr_pages.append(OCRPagePath(index=i, path=file))
            else:
                raise ValueError(f"Incorrect file extension for file {file}. Expected json")
        ocr_res = OCRResult(ocr_pages=ocr_pages)
        return ocr_res
