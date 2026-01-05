from manga_processor.models import OCRPage
import json
from pathlib import Path
from dataclasses import asdict, fields


class OCRPageSaver:
    def save_from_dirty_dict(
        self, data_dict: dict, index: int, output_dir_path: Path
    ) -> None:
        wanted_fields = {f.name for f in fields(OCRPage)}
        clean_data = {k: v for k, v in data_dict.items() if k in wanted_fields}
        ocrpage = OCRPage(index=index, **clean_data)
        self.save_to_json(ocr_page=ocrpage, output_dir_path=output_dir_path)

    def save_to_json(self, ocr_page: OCRPage, output_dir_path: Path) -> None:
        output_dir_path.mkdir(parents=True, exist_ok=True)
        file_path: Path = output_dir_path / f"{ocr_page.index}.json"
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(asdict(ocr_page), file)
