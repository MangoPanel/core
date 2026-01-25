import numpy as np
from shapely import Polygon
from sklearn.cluster import AgglomerativeClustering
from manga_processor.models import OCRPage


class AutoPolyClustering:
    def __init__(self, expansion_factor: float = 10.0, separator: str = "\n"):
        self.expansion_factor = expansion_factor
        self.separator = separator

    def fit_predict(self, ocr_page: OCRPage) -> OCRPage:
        if len(ocr_page.dt_polys) < 2:
            return ocr_page

        np_polys = np.array(ocr_page.dt_polys)

        shapely_polys = [Polygon(p) for p in ocr_page.dt_polys]

        # Ts is for cleaning invalid just in case
        shapely_polys = [p.buffer(0) if not p.is_valid else p for p in shapely_polys]

        n = len(shapely_polys)
        dist_matrix = np.zeros((n, n))

        # Distance matrix between every pair of polygons
        # Shapely .distance() should hopefully return 0 if they intersect
        for i in range(n):
            for j in range(i + 1, n):
                dist = shapely_polys[i].distance(shapely_polys[j])
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist

        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="single",
            distance_threshold=self.expansion_factor,
        )
        labels = clustering.fit_predict(dist_matrix)

        texts = ocr_page.rec_texts
        scores = ocr_page.rec_scores
        new_polys, new_texts, new_scores = [], [], []

        unique_labels = np.unique(labels)
        for label in unique_labels:
            group_poly_ids = np.where(labels == label)[0]

            merged_texts = self.separator.join(texts[i] for i in group_poly_ids)
            new_texts.append(merged_texts)

            mean_score = np.mean([scores[i] for i in group_poly_ids])
            new_scores.append(mean_score)

            merged_polys = np.array([np_polys[i] for i in group_poly_ids]).reshape(
                -1, 2
            )
            new_polys.append(merged_polys)

        new_ocr_page = OCRPage(
            index=ocr_page.index,
            dt_polys=new_polys,
            rec_texts=new_texts,
            rec_scores=new_scores,
        )
        return new_ocr_page
