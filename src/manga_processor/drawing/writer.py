import copy
from PIL import Image, ImageDraw
from manga_processor.models import MangaPage
from manga_processor.models.types import BubblePage, BubbleTextShape


def draw_translated_text(
    page: MangaPage,
    text_shapes: list[BubbleTextShape],
    text_color: str = "black",
    halo_color: str = "white",
    halo_width: int = 2,
) -> MangaPage[Image.Image]:
    image = copy.deepcopy(page.image)
    draw = ImageDraw.Draw(image)

    for shape in text_shapes:
        font = shape.font

        for line in shape.textlines:
            if not line.text.strip():
                continue

            x_offset = (line.total_width - line.used_width) // 2
            position = (line.start_point[0] + x_offset, line.start_point[1])

            if halo_width > 0:
                for adj in range(-halo_width, halo_width + 1):
                    for adj_y in range(-halo_width, halo_width + 1):
                        draw.text(
                            (position[0] + adj, position[1] + adj_y),
                            line.text,
                            font=font,
                            fill=halo_color,
                        )

            draw.text(position, line.text, font=font, fill=text_color)

    return MangaPage(index=page.index, image=image)
