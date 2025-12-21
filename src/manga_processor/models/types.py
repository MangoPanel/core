from dataclasses import dataclass
from pathlib import Path
import numpy as np
from typing import TypeVar, Generic
from PIL.ImageFont import ImageFont as PILImageFont


@dataclass
class Bubble:
    contour: np.ndarray
    poly_ids: list[int]
    is_bubble: bool
    circularity: float
    solidity: float
    area: float
    perimeter: float


@dataclass
class Coords:
    x: float
    y: float


@dataclass
class TextLine:
    coords: Coords
    text: str


@dataclass
class TextShape:
    lines: list[TextLine]
    font: PILImageFont


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
