from cv2.typing import MatLike, Point
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from typing import Any, TypeVar, Generic
from PIL.ImageFont import FreeTypeFont

from manga_processor.debug.debug_tools import add_debug_field


@dataclass
class Bubble:
    contour: MatLike
    text: str
    should_draw: bool = True


@dataclass
class BubblePage:
    index: int
    bubbles: list[Bubble]


@dataclass
class TextLine:
    start_point: Point
    total_width: int
    used_width: int = 0
    text: str = ""


@dataclass
class BubbleTextShape:
    textlines: list[TextLine]
    font: FreeTypeFont


@dataclass
class OCRPage:
    index: int
    dt_polys: list[list[list[float]]]
    rec_texts: list[str]
    rec_scores: list[float]


@dataclass
class OCRPagePath:
    index: int
    path: Path


@dataclass
class OCRResult:
    ocr_pages: list[OCRPagePath]


T = TypeVar("T")


@dataclass
class MangaPage(Generic[T]):
    index: int
    image: T


@dataclass
class MangaPagePath:
    index: int
    path: Path


@dataclass
class Manga:
    pages: list[MangaPagePath]
    title: str | None = None
