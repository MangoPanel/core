import numpy as np
import cv2

from manga_processor.models.types import OCRPage

def scale_polys(polys, scale):
    M = cv2.moments(polys)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])

    poly_norm = polys - [cx, cy]
    polys_scaled = poly_norm * scale
    polys_scaled = polys_scaled + [cx, cy]
    polys_scaled = polys_scaled.astype(np.int32)

    return polys_scaled

def scale_polys_on_page(ocr_page: OCRPage, scale) -> OCRPage:
    new_polys = [scale_polys(poly, scale) for poly in ocr_page.dt_polys]
    return OCRPage(ocr_page.index, new_polys, ocr_page.rec_texts, ocr_page.rec_scores)

