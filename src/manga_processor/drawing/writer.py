from PIL import ImageDraw

from models import MangaPage, TextShape


class Writer:
    def __init__(self, manga_page: MangaPage):
        self.manga_page = manga_page

    def write_text_shape(self, text_shape: TextShape, fill):
        draw = ImageDraw.Draw(self.manga_page.image)
        fnt = text_shape.font

        for line in text_shape.lines:
            draw.text(
                (line.coords.x, line.coords.y),
                line.text,
                font=fnt,
                fill=fill,
            )
