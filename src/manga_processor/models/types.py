from dataclasses import dataclass
from pathlib import Path
import numpy as np

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
class BubbleRepresentation:
    bubbles: list[Bubble]

