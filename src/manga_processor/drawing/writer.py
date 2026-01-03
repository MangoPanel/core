from PIL.Image import Image
from PIL import ImageDraw

from manga_processor.models.types import MangaPage, BubbleTextShape


def write_text_shapes(page: MangaPage[Image], shapes: list[BubbleTextShape]):
    result = page.image.copy()
    for shape in shapes:
        draw = ImageDraw.Draw(result)
        for line in shape.textlines:
            draw.text(
                (line.start_point[0], line.start_point[1]),
                line.text,
                (0, 0, 0),
                shape.font,
            )
    return MangaPage[Image](page.index, result)
