from cv2.typing import MatLike
from manga_processor.models.types import MangaPage
import cv2
from abc import ABC

class VisualDebuger(ABC):
    winnames = []

    @classmethod
    def debug_show(cls, page: MangaPage[MatLike]):
        winname = f"Page: {page.index}, transformations: {page.transformation_info}"
        while winname in cls.winnames:
            winname = winname + " +"
        cls.winnames.append(winname)
        try:
            cv2.imshow(winname, page.image)
        except Exception:
            try:
                new_image = cv2.applyColorMap(cv2.normalize(page.image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8UC1), cv2.COLORMAP_JET)
                cv2.imshow(winname, new_image)
            except Exception as e:
                raise Exception(f"Failed to debug show an image with the following exception: {e}")
        
    @classmethod
    def wait(cls):
        while True:
            res = cv2.waitKey()
            print(
                "You pressed %d (0x%x), LSB: %d (%s), try pressing 'esc'"
                % (res, res, res % 256, repr(chr(res % 256)) if res % 256 < 128 else "?")
            )
            if res == 27:
                print("pressed 'esc', closing windows")
                break


