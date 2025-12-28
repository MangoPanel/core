import cv2
import numpy as np
from manga_processor.debug.debug_tools import return_debug
from manga_processor.models.types import MangaPage
import skimage

class Watershed:
    @return_debug()
    def fit(self, topology_page: MangaPage, markers_page: MangaPage) -> MangaPage:
        result = markers_page.image.copy()
        cv2.watershed(topology_page.image, result)
        return MangaPage(markers_page.index, result)

class WatershedTreshold:
    def __init__(self, threshold: int = 150):
        self.threshold = threshold

    @return_debug()
    def fit(self, topology_page: MangaPage, markers_page: MangaPage) -> MangaPage:
        mask = topology_page.image < self.threshold
        result = skimage.segmentation.watershed(topology_page.image, markers_page.image, mask=mask)
        return MangaPage(markers_page.index, result)
