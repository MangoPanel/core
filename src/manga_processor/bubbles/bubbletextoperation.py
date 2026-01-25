from typing import Iterable

import cv2
import numpy as np
from cv2.typing import MatLike, Point
from numpy._typing import NDArray
from PIL.ImageFont import FreeTypeFont
from typing import Sequence
from manga_processor.models.types import BubbleTextShape
from manga_processor.models.types import BubblePage, TextLine


def split_text_into_words(text: str, separator: str = " ") -> list[str]:
    return text.split(sep=separator)


def words_to_size(words: Iterable[str], font: FreeTypeFont) -> list[tuple[int, int]]:
    return [font.getmask(word).size for word in words]


def get_space_width(font: FreeTypeFont) -> int:
    return font.getmask(" ").size[0]


def get_max_line_height(word_sizes: Iterable[tuple[int, int]]) -> int:
    return np.max(np.array(word_sizes), axis=0)[1]


def fit_into_slices(
    slices: list[TextLine],
    words: list[str],
    word_sizes: list[tuple[int, int]],
    space_width: int,
) -> list[TextLine] | None:
    if not slices:
        return None

    slice_idx = 0

    for word, (w_width, _) in zip(words, word_sizes):
        word_placed = False

        while slice_idx < len(slices):
            current_slice = slices[slice_idx]
            prefix = " " if current_slice.text else ""
            needed_width = (space_width if current_slice.text else 0) + w_width

            # Check if it fits in the current slice
            if current_slice.used_width + needed_width <= current_slice.total_width:
                current_slice.text += prefix + word
                current_slice.used_width += int(needed_width)
                word_placed = True
                break  # Move to next word
            else:
                # Word too wide for this slice, try the next vertical slice
                slice_idx += 1

        # If we ran out of slices and the word was never placed
        if not word_placed:
            return None

    return slices


def split_contour_by_line_height(contour: MatLike, line_height: int) -> list[TextLine]:
    x, y, w, h = cv2.boundingRect(contour)
    slices: list[TextLine] = []
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask, [contour - [x, y]], -1, 255, -1)

    # REMOVED the 'if top == 0...' skip logic.
    # We want to use all available space.
    for top in range(0, h, line_height):
        bottom = min(top + line_height, h)
        roi = mask[top:bottom, :]
        column_exists = np.any(roi > 0, axis=0)

        if np.any(column_exists):
            indices = np.where(column_exists)[0]
            slice_width = int(indices[-1] - indices[0] + 1)
            relative_x_offset = int(indices[0])
            # Filter out tiny slivers that can't hold even a letter
            if slice_width > 5:
                slices.append(
                    TextLine((int(x + relative_x_offset), int(top + y)), slice_width)
                )

    return slices


def prepare_text_shapes(
    bubble_page: BubblePage,
    font: FreeTypeFont,
    min_font_size: int = 5,
    max_font_size: int = 50,
) -> list[BubbleTextShape]:
    text_shapes: list[BubbleTextShape] = []
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
            if len(slices) == 0:
                continue
            fitted_slices = fit_into_slices(slices, words, word_sizes, space_width)
            if fitted_slices is not None:
                text_shapes.append(
                    BubbleTextShape(textlines=fitted_slices, font=font_adjusted)
                )
                break
            else:
                if font_size > min_font_size:
                    continue
                else:
                    raise Exception(
                        f"Failed while fitting words into bubbles on page: {bubble_page.index}. Minimum allowed font size reched"
                    )

    return text_shapes
