import cv2
import os
from cv2.typing import MatLike
from manga_processor.models.types import MangaPage
from abc import ABC


class VisualDebugger(ABC):
    winnames = []

    @classmethod
    def debug_show(cls, page: MangaPage[MatLike]):
        if not __debug__:
            return

        winname = f"Page: {page.index}, transformations: {page.transformation_info}"
        while winname in cls.winnames:
            winname = winname + " +"
        cls.winnames.append(winname)

        image_to_show = cls._prepare_image(page.image)
        cv2.imshow(winname, image_to_show)

    @classmethod
    def debug_save(
        cls,
        page: MangaPage[MatLike],
        output_dir: str = "debug_output",
        force: bool = False,
    ):
        if not __debug__:
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = f"page_{page.index}_{len(page.transformation_info)}.png"
        path = os.path.join(output_dir, filename)

        image_to_save = cls._prepare_image(page.image)
        if force:
            image_to_save = cls._force_norm_colormap(image_to_save)
        cv2.imwrite(path, image_to_save)

    @classmethod
    def wait(cls):
        if not __debug__:
            return

        while True:
            res = cv2.waitKey()
            if res == -1:
                continue

            print(
                "You pressed %d (0x%x), LSB: %d (%s), try pressing 'esc'"
                % (
                    res,
                    res,
                    res % 256,
                    repr(chr(res % 256)) if res % 256 < 128 else "?",
                )
            )
            if res == 27:  # ESC key
                print("pressed 'esc', closing windows")
                cv2.destroyAllWindows()
                cls.winnames.clear()
                break

    @classmethod
    def _prepare_image(cls, image: MatLike) -> MatLike:
        try:
            cv2.mean(image)
            return image
        except Exception:
            try:
                return cls._force_norm_colormap(image)
            except Exception as e:
                raise Exception(f"Failed to process image for debugging: {e}")

    @classmethod
    def _force_norm_colormap(cls, image: MatLike):
        norm_img = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8UC1)
        return cv2.applyColorMap(norm_img, cv2.COLORMAP_JET)
