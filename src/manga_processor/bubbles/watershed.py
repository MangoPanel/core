import cv2
import numpy as np
from manga_processor.debug.debug_tools import return_debug
from manga_processor.models.types import MangaPage
import skimage

class WatershedTreshold:
    def __init__(self, threshold: int = 150):
        self.threshold = threshold
        self.watershed_img = None
        self.watershed_page = None

    @return_debug()
    def fit_predict(self, topology_page: MangaPage, markers_page: MangaPage):
        mask = topology_page.image < self.threshold
        self.watershed_img = skimage.segmentation.watershed(topology_page.image, markers_page.image, mask=mask)
        self.watershed_page = MangaPage(markers_page.index, self.watershed_img)
        return self.watershed_page


