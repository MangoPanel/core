import numpy as np
from numpy._typing import NDArray
from sklearn.cluster import AgglomerativeClustering


from models import OCRPage

class AutoPolyClustering:
    def __init__(self, expansion_factor: float = 1.2):
        self.expansion_factor = expansion_factor

    def get_poly_centers(self, polys: NDArray):
        return [np.mean(poly, axis=0) for poly in polys]

    def get_poly_heights(self, polys: NDArray):
        heights = []
        for poly in polys:
            y_coords = poly[:, 1]
            height = np.max(y_coords) - np.min(y_coords)
            heights.append(height)
        return heights

    def fit(self, ocr_page: OCRPage):
        if len(ocr_page.dt_polys) < 2:
            return ocr_page
        
        np_polys = np.array(ocr_page.dt_polys)
        
        poly_centers = self.get_poly_centers(np_polys)
        poly_heights = self.get_poly_heights(np_polys)

        global_threshold = np.mean(poly_heights) * self.expansion_factor

        clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=global_threshold, linkage="single").fit(poly_centers)

        labels = clustering.labels_
        num_groups = clustering.n_clusters

        new_polys, new_texts, new_scores = [], [], []

        for i in range(num_groups):
            indices = np.where(labels == i)[0]
            indices = indices[np.argsort(poly_centers[indices, 1])]
            # TODO FINISH
