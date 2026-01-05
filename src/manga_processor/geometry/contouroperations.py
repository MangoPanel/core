import numpy as np
import cv2
from manga_processor.models.types import MangaPage


def find_unique_contours(page: MangaPage, skip_background: bool = True):
    uniqe_contours = []

    if skip_background:
        labels = np.unique(page.image)[1:]
    else:
        labels = np.unique(page.image)

    for label in labels:
        target = np.where(page.image == label, 255, 0).astype(np.uint8)

        contours, _ = cv2.findContours(
            target, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        uniqe_contours.append(contours[0])

    return uniqe_contours
