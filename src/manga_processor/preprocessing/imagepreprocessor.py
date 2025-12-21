import cv2
from cv2.typing import MatLike, Size
from models import MangaPage
from typing import Protocol

class Filter(Protocol):
    def apply(self, image: MatLike) -> MatLike:
        ...

class GrayScaleFilter:
    def apply(self, image: MatLike) -> MatLike:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

class BinaryFilter:
    def __init__(self, threshold=230):
        self.threshold = threshold

    def apply(self, image: MatLike) -> MatLike:
        _, res = cv2.threshold(image, self.threshold, 255, cv2.THRESH_BINARY)
        return res

class ErodeFilter:
    def __init__(self, ksize: Size):
        self.ksize = ksize

    def apply(self, image: MatLike) -> MatLike:
        kernel = kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, self.ksize)
        image_eroded = cv2.morphologyEx(image, cv2.MORPH_ERODE, kernel)
        return image_eroded

class PagePreprocessor:
    def __init__(self, manga_page: MangaPage[MatLike]):
        self.manga_page = manga_page
        self.pipeline: list[Filter] = []

    def add(self, filter: Filter):
        self.pipeline.append(filter)
        return self

    def run(self):
        for filter in self.pipeline:
            self.manga_page.image = filter.apply(self.manga_page.image)
        return self.manga_page
