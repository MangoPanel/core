import cv2
import numpy as np
from cv2.typing import MatLike, Size
from manga_processor.debug.debug_tools import return_debug
from manga_processor.models import MangaPage
from typing import Protocol, List, Callable


class ImageTransformation(Protocol):
    def apply(self, image: MatLike) -> MatLike: ...


class ToGray:
    def apply(self, image: MatLike) -> MatLike:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class ToColor:
    def apply(self, image: MatLike) -> MatLike:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


class Invert:
    def apply(self, image: MatLike) -> MatLike:
        return cv2.bitwise_not(image)


class Binarize:
    def __init__(self, threshold=230):
        self.threshold = threshold

    def apply(self, image: MatLike) -> MatLike:
        _, res = cv2.threshold(image, self.threshold, 255, cv2.THRESH_BINARY)
        return res


class Erode:
    def __init__(self, ksize: Size = (3, 3)):
        self.ksize = ksize

    def apply(self, image: MatLike) -> MatLike:
        kernel = kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, self.ksize)
        image_eroded = cv2.morphologyEx(image, cv2.MORPH_ERODE, kernel)
        return image_eroded


class Open:
    def __init__(self, ksize: Size = (3, 3)):
        self.ksize = ksize

    def apply(self, image: MatLike) -> MatLike:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, self.ksize)
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return opened


class Close:
    def __init__(self, ksize: Size = (3, 3)):
        self.ksize = ksize

    def apply(self, image: MatLike) -> MatLike:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, self.ksize)
        opened = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        return opened


class DistanceTransfrom:
    def __init__(self, mask_size: int = 5):
        self.mask_size = mask_size

    def apply(self, image: MatLike) -> MatLike:
        dist = cv2.distanceTransform(image, cv2.DIST_L2, self.mask_size)
        dist_norm = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        return dist_norm


class ToEmptyMask:
    def __init__(self, dtype=np.int32) -> None:
        self.dtype = dtype

    def apply(self, image: MatLike) -> MatLike:
        return np.zeros(image.shape[:2], dtype=self.dtype)


class Dilate:
    def __init__(self, ksize: Size = (3, 3)):
        self.ksize = ksize

    def apply(self, image: MatLike) -> MatLike:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, self.ksize)
        dilated = cv2.morphologyEx(image, cv2.MORPH_DILATE, kernel)
        return dilated


class PagePreprocessor:
    def __init__(self, transformations: List[ImageTransformation]):
        self.transformations = transformations or []
        self._compiled_process = self._compile_pipeline()

    def _compile_pipeline(self) -> Callable[[MatLike], MatLike]:
        def compiled_process(image: MatLike) -> MatLike:
            result = image.copy()
            for transform in self.transformations:
                result = transform.apply(result)
            return result

        return compiled_process

    def add(self, transformation: ImageTransformation | List[ImageTransformation]):
        if isinstance(transformation, list):
            self.transformations.extend(transformation)
        else:
            self.transformations.append(transformation)
        self._compiled_process = self._compile_pipeline()
        return self

    @return_debug()
    def process(self, manga_page: MangaPage) -> MangaPage:
        return MangaPage(
            index=manga_page.index, image=self._compiled_process(manga_page.image)
        )

    def get_debug_info(self):
        return " -> ".join(
            [type(t).__name__ for t in self.transformations]
        )
