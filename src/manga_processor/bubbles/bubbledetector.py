from pathlib import Path
from manga_processor.bubbles.watershed import WatershedTreshold
from manga_processor.debug.debug_visual import VisualDebuger
from manga_processor.drawing.drawer import (
    draw_contours,
    draw_polys,
    populate_with_polys,
)
from manga_processor.filesys.loaders.ocrresloader import OCRPageLoader
from manga_processor.filesys.loaders.pageloader import PageLoader
from manga_processor.geometry.autopolyclustering import AutoPolyClustering
from manga_processor.geometry.contouroperations import find_unique_contours
from manga_processor.geometry.polyoperations import scale_polys_on_page
from manga_processor.models import Bubble, MangaPage, OCRPage
from manga_processor.models.types import BubblePage, MangaPagePath, OCRPagePath
from manga_processor.preprocessing.imagepreprocessor import (
    Binarize,
    Close,
    DistanceTransfrom,
    Erode,
    Invert,
    PagePreprocessor,
    ToEmptyMask,
    ToGray,
)


class BubbleDetector:
    def __init__(
        self,
        landscape_preprocessor: PagePreprocessor,
        mask_preprocessor: PagePreprocessor,
        polygon_grouping: AutoPolyClustering,
        watershed: WatershedTreshold,
    ):
        self.landscape_preprocessor = landscape_preprocessor
        self.mask_preprocessor = mask_preprocessor
        self.polygon_grouping = polygon_grouping
        self.watershed = watershed

        self.watershed_page = None
        self.bubble_page = None

    def fit(self, ocr_page: OCRPage, manga_page: MangaPage):
        clean_page = draw_polys(ocr_page, manga_page, (255, 255, 255))
        landscape_page = self.landscape_preprocessor.process(clean_page)

        grouped_ocr_page = self.polygon_grouping.fit_predict(ocr_page)
        resized_ocr_page = scale_polys_on_page(grouped_ocr_page, 0.8)

        markers_mask_page = self.mask_preprocessor.process(clean_page)
        markers_page = populate_with_polys(resized_ocr_page, markers_mask_page)

        self.watershed_page = self.watershed.fit_predict(landscape_page, markers_page)

        self.bubble_page = BubblePage(manga_page.index, [])
        contours = find_unique_contours(self.watershed_page)

        for contour, text in zip(contours, grouped_ocr_page.rec_texts):
            self.bubble_page.bubbles.append(Bubble(contour, text))

        return self

    def fit_predict(self, ocr_page: OCRPage, manga_page: MangaPage):
        self.fit(ocr_page, manga_page)
        return self.bubble_page


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


landscape_preprocessor = PagePreprocessor(
    [
        ToGray(),
        Binarize(),
        Close(ksize=(3, 3)),
        Erode(ksize=(5, 5)),
        DistanceTransfrom(),
        Invert(),
    ]
)
mask_procesor = PagePreprocessor([ToEmptyMask()])
auto_poly_clustering = AutoPolyClustering()
watershed = WatershedTreshold(threshold=220)


bubble_detector = BubbleDetector(
    landscape_preprocessor, mask_procesor, auto_poly_clustering, watershed
)
res = bubble_detector.fit(ocr_page, manga_page)
bubble_page = res.bubble_page

clean_page = draw_polys(ocr_page, manga_page, color=(255, 255, 255))
drawn_contours = draw_contours(bubble_page, clean_page)
VisualDebuger.debug_show(res.watershed_page)
VisualDebuger.debug_show(drawn_contours)


VisualDebuger.debug_show(MangaPage(0, base_img))
VisualDebuger.wait()
