from pathlib import Path
import cv2
import numpy as np
from cv2.typing import MatLike
from typing import List
from manga_processor.bubbles.watershed import Watershed, WatershedTreshold
from manga_processor.debug.debug_visual import VisualDebuger
from manga_processor.drawing.drawer import Drawer
from manga_processor.filesys.loaders.ocrresloader import OCRPageLoader
from manga_processor.filesys.loaders.pageloader import PageLoader
from manga_processor.filesys.savers.ocrresaver import OCRPageSaver
from manga_processor.geometry.autopolyclustering import AutoPolyClustering
from manga_processor.geometry.polyoperations import scale_polys, scale_polys_on_page
from manga_processor.models import OCRPage, MangaPage, Bubble
from manga_processor.models.types import MangaPagePath, OCRPagePath
from manga_processor.preprocessing.imagepreprocessor import (
    Dilate,
    DistanceTransfrom,
    Erode,
    Invert,
    Open,
    Close,
    PagePreprocessor,
    Binarize,
    ToColor,
    ToEmptyMask,
    ToGray,
)

drawer = Drawer()
landscape_preprocessor = PagePreprocessor(
    [
        ToGray(),
        Binarize(),
        Close(ksize=(3, 3)),
        Erode(ksize=(5, 5)),
        DistanceTransfrom(),
        Invert()
    ]
)
mask_procesor = PagePreprocessor([ToEmptyMask()])
auto_poly_clustering = AutoPolyClustering()
watershed = WatershedTreshold(threshold=220)

class BubbleDetector:
    def detect(self, ocr_page: OCRPage, manga_page: MangaPage):
        VisualDebuger.debug_show(drawer.draw_polys(ocr_page, manga_page, (255, 0, 0)))
        clean_page = drawer.draw_polys(ocr_page, manga_page, (255, 255, 255))
        landscape_page = landscape_preprocessor.process(clean_page)
        
        grouped_ocr_page = auto_poly_clustering.fit(ocr_page)
        resized_ocr_page = scale_polys_on_page(grouped_ocr_page, 0.8)
        markers_mask_page = mask_procesor.process(clean_page)

        markers_page = drawer.populate_with_polys(resized_ocr_page, markers_mask_page)
        watershed_page = watershed.fit(landscape_page, markers_page)

        VisualDebuger.debug_show(clean_page)
        VisualDebuger.debug_show(landscape_page)
        VisualDebuger.debug_show(markers_page)
        VisualDebuger.debug_show(watershed_page)




# DEMO
SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "../tests/test_data/png/"
image_path = TEST_DATA_DIR / "008.png"

manga_page_path = MangaPagePath(index=0, path=image_path)
pageloader = PageLoader()
manga_page = pageloader.load_for_cv2(manga_page_path=manga_page_path)

TEST_JSON_DIR = SCRIPT_DIR / "../tests/test_data/json/json_cleaned/"
file_path = TEST_JSON_DIR / "008_res.json"
ocr_pageloader = OCRPageLoader()
ocr_page_path = OCRPagePath(index=0, path=file_path)

# import json with ocr_page_path.path.open("r", encoding="utf-8") as file:
#     data = json.load(file)
#
# ocrpagesaver = OCRPageSaver()
# ocrpagesaver.save_from_dirty_dict(data_dict=data, output_path=TEST_JSON_DIR / "008_res.json", index=0)


ocr_page = ocr_pageloader.load_json(ocr_page_path=ocr_page_path)

bubble_detector = BubbleDetector()
bubble_detector.detect(ocr_page, manga_page)

VisualDebuger.wait()
