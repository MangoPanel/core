from manga_processor.models import TextShape
from cv2.typing import Point
from modelscope.pipelines.multi_modal.diffusers_wrapped.devices import dtype
import cv2
import numpy as np
from PIL.ImageFont import FreeTypeFont
from typing import Iterable, Any
from PIL import ImageFont

from manga_processor.models.types import TextLine, BubblePage, BubbleTextShape


def split_text_into_words(text: str, separator: str = " ") -> list[str]:
    return text.split(sep=separator)


def words_to_size(words: Iterable[str], font: FreeTypeFont) -> list[tuple[int, int]]:
    return [font.getmask(word).size for word in words]


def get_space_width(font: FreeTypeFont) -> int:
    return font.getmask(" ").size[0]


def get_max_line_height(word_sizes: Iterable[tuple[int, int]]) -> int:
    return np.max(np.array(word_sizes), axis=0)[1]


def split_contour_by_line_height(contour, line_height: int) -> list[TextLine]:
    x, y, w, h = cv2.boundingRect(contour)

    slices: list[TextLine] = []

    mask = np.zeros((h, w), dtype=np.uint8)

    cv2.drawContours(mask, [contour - [x, y]], -1, 255, -1)

    for top in range(0, h, line_height):
        bottom = min(top + line_height, h)
        roi = mask[top:bottom, :]
        column_exists = np.any(roi > 0, axis=0)
        if np.any(column_exists):
            indices = np.where(column_exists)[0]
            slice_width: int = indices[-1] - indices[0] + 1
        else:
            slice_width = 0

        relative_x_offset = indices[0] if slice_width > 0 else 0
        true_x: int = x + relative_x_offset
        slice = TextLine(Point(true_x, top + y), slice_width)
        slices.append(slice)

    return slices


def fit_into_slices(
    slices: list[TextLine], words, word_sizes, space_width
) -> list[TextLine] | bool:
    slice_idx = 0
    current_slice = slices[slice_idx]
    for word, (w_width, _) in zip(words, word_sizes):
        prefix = " " if current_slice.text else ""
        needed_width = (space_width if current_slice.text else 0) + w_width

        if current_slice.used_width + needed_width <= current_slice.total_width:
            current_slice.text += prefix + word
            current_slice.used_width += needed_width
        else:
            slice_idx += 1

            if slice_idx >= len(slices):
                return False

            current_slice = slices[slice_idx]

    return slices


def prepare_text_shapes(
    bubble_page: BubblePage,
    font: FreeTypeFont,
    min_font_size: int = 5,
    max_font_size: int = 50,
):
    text_shapes: list[TextShape] = []
    for bubble in bubble_page.bubbles:
        text = bubble.text
        contour = bubble.contour
        for font_size in range(max_font_size, min_font_size, -1):
            font_adjusted: FreeTypeFont = font.font_variant(size=font_size)
            words = split_text_into_words(text)
            word_sizes = words_to_size(words, font_adjusted)
            max_line_height = get_max_line_height(word_sizes)
            space_width = get_space_width(font_adjusted)
            slices = split_contour_by_line_height(contour, max_line_height)
            fitted_slices = fit_into_slices(slices, words, word_sizes, space_width)
            if fitted_slices:
                text_shapes.append(TextShape(fitted_slices, font_adjusted))

        raise Exception(
            f"Failed while fitting words into bubbles on page: {bubble_page.index}. Minimum allowed font size reched"
        )
    return text_shapes
