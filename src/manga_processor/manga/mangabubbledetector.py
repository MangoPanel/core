from cv2.typing import MatLike
from manga_processor.bubbles.bubbledetector import BubbleDetector
from manga_processor.bubbles.watershed import WatershedTreshold
from manga_processor.filesys import OCRPageLoader, PageLoader
from manga_processor.geometry.autopolyclustering import AutoPolyClustering
from manga_processor.models import Manga, MangaPage, OCRPage, OCRResult
from manga_processor.models.types import BubblePage
from manga_processor.preprocessing.imagepreprocessor import (
    Binarize,
    Close,
    DistanceTransfrom,
    Erode,
    PagePreprocessor,
    ToEmptyMask,
    ToGray,
    Invert,
)


class MangaBubbleDetector:
    def __init__(
        self, manga_page_loader: PageLoader, ocr_page_loader: OCRPageLoader
    ) -> None:
        self.manga_page_loader: PageLoader = manga_page_loader
        self.ocr_page_loader: OCRPageLoader = ocr_page_loader

    def fit_predict(self, manga: Manga, ocr_res: OCRResult) -> list[BubblePage]:
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
        mask_procesor: PagePreprocessor = PagePreprocessor([ToEmptyMask()])
        auto_poly_clustering: AutoPolyClustering = AutoPolyClustering()
        watershed: WatershedTreshold = WatershedTreshold(threshold=220)

        bubble_detector: BubbleDetector = BubbleDetector(
            landscape_preprocessor, mask_procesor, auto_poly_clustering, watershed
        )

        bubble_pages: list[BubblePage] = []
        for page_path, ocr_page_path in zip(manga.pages, ocr_res.ocr_pages):
            loaded_page: MangaPage[MatLike] = self.manga_page_loader.load_for_cv2(
                page_path
            )
            loaded_ocr_page: OCRPage = self.ocr_page_loader.load_json(ocr_page_path)
            bubble_pages.append(
                bubble_detector.fit_predict(loaded_ocr_page, loaded_page)
            )

        return bubble_pages
