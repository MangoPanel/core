import cv2
from cv2.typing import MatLike, Scalar
import numpy as np
from manga_processor.debug.debug_tools import return_debug
from manga_processor.models.types import MangaPage, OCRPage


class Drawer:
    @return_debug()
    def draw_polys(self, ocr_page: OCRPage, manga_page: MangaPage[MatLike], color: Scalar):
        polys = ocr_page.dt_polys
        result = manga_page.image.copy()
        for poly in polys:
            formatted_poly = np.array(poly, dtype=np.int32)
            cv2.fillPoly(result, [formatted_poly], color)
        
        return MangaPage[MatLike](index=manga_page.index, image=result)
    
    @return_debug()
    def populate_with_circles(
        self, ocr_page: OCRPage, manga_page: MangaPage[MatLike], radius: int = 3
    ):
        result = manga_page.image.copy()
        for i, bubble_points in enumerate(ocr_page.dt_polys):
            for point in bubble_points:
                x, y = int(point[0]), int(point[1])
                cv2.circle(result, (x, y), radius, i + 1, -1)

        return MangaPage[MatLike](index=manga_page.index, image=result)


    @return_debug()
    def populate_with_markers(self, ocr_page: OCRPage, manga_page: MangaPage[MatLike], padding: int = 400):
        result = manga_page.image.copy()
        
        bg_id = len(ocr_page.dt_polys) + 1
        result.fill(bg_id)

        temp_bubble_mask = np.zeros(result.shape, dtype=np.uint8)
        
        for poly in ocr_page.dt_polys:
            pts = np.array(poly, dtype=np.int32).reshape((-1, 2))
            hull = cv2.convexHull(pts)
            cv2.fillPoly(temp_bubble_mask, [hull], 255)

        kernel = np.ones((padding, padding), np.uint8)
        dilated = cv2.dilate(temp_bubble_mask, kernel, iterations=1)
        
        result[dilated == 255] = 0

        for i, poly in enumerate(ocr_page.dt_polys):
            pts = np.array(poly, dtype=np.int32).reshape((-1, 2))
            hull = cv2.convexHull(pts)
            cv2.fillPoly(result, [hull], i + 1)

        return MangaPage[MatLike](index=manga_page.index, image=result)

    @return_debug()
    def populate_with_polys(self, ocr_page: OCRPage, manga_page: MangaPage[MatLike]):
        result = manga_page.image.copy()

        for i, bubble_poly in enumerate(ocr_page.dt_polys):
            formatted_poly = np.array(bubble_poly, dtype=np.int32)
            hull = cv2.convexHull(formatted_poly)
            cv2.fillPoly(result, [hull], i + 1)

        return MangaPage[MatLike](index=manga_page.index, image=result) 
