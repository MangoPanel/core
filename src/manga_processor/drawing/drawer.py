import cv2
from cv2.typing import MatLike, Scalar
import numpy as np
from manga_processor.debug.debug_tools import return_debug
from manga_processor.models.types import BubblePage, MangaPage, OCRPage


@return_debug(info_provider=lambda _: "Draw polys")
def draw_polys(ocr_page: OCRPage, manga_page: MangaPage[MatLike], color: Scalar):
    polys = ocr_page.dt_polys
    result = manga_page.image.copy()
    for poly in polys:
        formatted_poly = np.array(poly, dtype=np.int32)
        cv2.fillPoly(result, [formatted_poly], color)

    return MangaPage[MatLike](index=manga_page.index, image=result)


@return_debug(info_provider=lambda _: "Populate with circles")
def populate_with_circles(
    ocr_page: OCRPage, manga_page: MangaPage[MatLike], radius: int = 3
):
    result = manga_page.image.copy()
    for i, bubble_points in enumerate(ocr_page.dt_polys):
        for point in bubble_points:
            x, y = int(point[0]), int(point[1])
            cv2.circle(result, (x, y), radius, i + 1, -1)

    return MangaPage[MatLike](index=manga_page.index, image=result)


@return_debug(info_provider=lambda _: "Populate with polys")
def populate_with_polys(ocr_page: OCRPage, manga_page: MangaPage[MatLike]):
    result = manga_page.image.copy()

    for i, bubble_poly in enumerate(ocr_page.dt_polys):
        formatted_poly = np.array(bubble_poly, dtype=np.int32)
        hull = cv2.convexHull(formatted_poly)
        cv2.fillPoly(result, [hull], i + 1)

    return MangaPage[MatLike](index=manga_page.index, image=result)


@return_debug(info_provider=lambda _: "Draw contours")
def draw_contours(bubble_page: BubblePage, manga_page: MangaPage[MatLike]):
    result = manga_page.image.copy()

    cv2.drawContours(
        result, [bubble.contour for bubble in bubble_page.bubbles], -1, (0, 0, 255), 2
    )

    return MangaPage[MatLike](manga_page.index, result)
