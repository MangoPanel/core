from manga_processor.models import OCRPage
import json
from pathlib import Path
from dataclasses import asdict, fields

class OCRPageSaver:
    def save_from_dirty_dict(self, data_dict: dict, index: int, output_path: Path) -> None:
        wanted_fields = {f.name for f in fields(OCRPage)}
        clean_data = {k: v for k, v in data_dict.items() if k in wanted_fields}
        ocrpage = OCRPage(index=index, **clean_data)
        self.save_to_json(ocr_page=ocrpage, output_path=output_path)

    def save_to_json(self, ocr_page: OCRPage, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(asdict(ocr_page), file)

