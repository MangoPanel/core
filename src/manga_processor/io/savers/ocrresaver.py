from models import OCRPage
import json
from pathlib import Path

class OCRPageSaver:
    def save_to_json(self, ocr_page: OCRPage, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(ocr_page, file)

