import copy
from PIL import Image, ImageFont
import cv2
from pydantic import SecretStr
from manga_processor.bubbles.bubbletextoperation import prepare_text_shapes
from manga_processor.debug.debug_visual import VisualDebugger
from manga_processor.drawing.drawer import draw_polys
from manga_processor.drawing.writer import draw_translated_text
from manga_processor.filesys import (
    MangaLoader,
    MangaNormalizer,
    MangaSaver,
    OCRPageLoader,
    OCRResultLoader,
    PageLoader,
    PageSaver,
)
from manga_processor.filesys.savers.ocrresaver import OCRPageSaver
from manga_processor.language.clean_ocrres import JPTextCleaner
from manga_processor.manga.mangabubbledetector import MangaBubbleDetector
from typing import Any, Dict, Iterable, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json
from pathlib import Path

from paddleocr import PaddleOCR
from manga_processor.models import MangaPagePath
from manga_processor.models.types import BubblePage, OCRResult, Manga
from translation import translate_bubbles


class GeneralState(TypedDict):
    manga_name: str
    original_manga: Manga
    original_ocr_result: OCRResult | None
    original_bubbles: list[BubblePage] | None
    translated_bubbles: list[BubblePage] | None

    work_dir: Path  # Working directory for processing
    output_pdf_path: str | None  # Path to final translated PDF


def ocr(state: GeneralState) -> GeneralState:
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        lang="japan",
        text_rec_score_thresh=0.3,
    )

    ocr_page_loader = OCRPageLoader()
    ocr_page_saver: OCRPageSaver = OCRPageSaver()
    ocr_res_loader: OCRResultLoader = OCRResultLoader()

    work_dir: Path = state["work_dir"]
    ocr_output_dir: Path = work_dir / "ocr_output"
    ocr_output_dir.mkdir(exist_ok=True)
    input_dir = state["original_manga"].dir_path

    img_dir = ocr_output_dir / "img"

    result: Iterable[type] = ocr.predict_iter(input=f"{input_dir}")
    for num, res in enumerate(result):
        ocr_page_saver.save_from_dirty_dict(
            data_dict=res.json, index=num, output_dir_path=ocr_output_dir
        )
        img_path = img_dir / f"{num}"
        res.save_to_img(f"{img_path}.png")

    ocr_res: OCRResult = ocr_res_loader.load_directory(path=ocr_output_dir)
    jp_text_cleaner = JPTextCleaner(ocr_page_loader, ocr_page_saver, ocr_res_loader)
    clean_ocr_res = jp_text_cleaner.clean_ocr_res(ocr_res)

    return {**state, "original_ocr_result": clean_ocr_res}


def bubble_selector(state: GeneralState) -> GeneralState:
    og_manga: Manga = state["original_manga"]
    og_ocr: OCRResult | None = state["original_ocr_result"]
    if og_ocr is None:
        raise ValueError("OCR failed")
    page_loader: PageLoader = PageLoader()
    ocr_page_loader: OCRPageLoader = OCRPageLoader()
    manga_bubble_detector = MangaBubbleDetector(page_loader, ocr_page_loader)
    bubble_pages: list[BubblePage] = manga_bubble_detector.fit_predict(og_manga, og_ocr)
    return {**state, "original_bubbles": bubble_pages}


def translator(state: GeneralState) -> GeneralState:
    og_bubbles: list[BubblePage] | None = state["original_bubbles"]

    if og_bubbles is None:
        raise ValueError("missing data - cant translate")

    bubbles_to_translate = copy.deepcopy(og_bubbles)

    llm: ChatOpenAI = ChatOpenAI(
        model="LFM",
        base_url="http://10.10.10.20:8000/v1",
        api_key=SecretStr("abc"),
        temperature=0.1,
        top_p=0.1,
        extra_body={"top_k": 50, "repetition_penalty": 1.05},
    )

    translated_bubbles: list[BubblePage] = translate_bubbles(
        bubbles_to_translate, "Japanese", "English", llm
    )

    return {**state, "translated_bubbles": translated_bubbles}


def text_writer(state: GeneralState) -> GeneralState:
    translated_bubbles: list[BubblePage] | None = state["translated_bubbles"]
    og_ocr = state["original_ocr_result"]
    manga = state["original_manga"]

    page_loader = PageLoader()
    page_saver = PageSaver()
    ocr_page_loader = OCRPageLoader()
    manga_saver = MangaSaver()

    if translated_bubbles is None or og_ocr is None:
        raise ValueError("Required data missing in state")

    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    font_path = project_root / "fonts" / "Inktype-MAp2J.ttf"
    font = ImageFont.truetype(str(font_path), size=30)

    img_output_dir = state["work_dir"] / "translated_pages"
    img_output_dir.mkdir(parents=True, exist_ok=True)

    new_page_paths = []

    for bubble_page, ocr_path in zip(translated_bubbles, og_ocr.ocr_pages):
        ocr_page = ocr_page_loader.load_json(ocr_path)
        page = page_loader.load_for_cv2(manga.pages[bubble_page.index])

        page = draw_polys(ocr_page, page, (255, 255, 255))
        color_converted = cv2.cvtColor(page.image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(color_converted)
        page.image = pil_image

        text_shapes = prepare_text_shapes(bubble_page, font)
        drawn_page = draw_translated_text(page, text_shapes)

        page_saver.save_to_img_from_pil(drawn_page, img_output_dir)

        saved_path = img_output_dir / f"{bubble_page.index}.png"
        new_page_paths.append(MangaPagePath(index=bubble_page.index, path=saved_path))

    new_page_paths.sort(key=lambda x: x.index)
    translated_manga = Manga(pages=new_page_paths, dir_path=img_output_dir)

    manga_filename = Path(state["manga_name"]).stem
    pdf_path = state["work_dir"] / f"{manga_filename}.pdf"

    manga_saver.save_to_pdf(translated_manga, pdf_path)

    return {**state, "output_pdf_path": str(pdf_path)}


# def pdf_generator(state: GeneralState) -> GeneralState:
#     """
#     Generate final translated PDF from processed manga pages.
#     """
#     work_dir = state["work_dir"]
#     output_pdf_path = work_dir / "translated_output.pdf"
#
#     # Get the manga with translated pages
#     manga = state["oryginal_manga"]
#     manga.save_to_pdf(str(output_pdf_path))
#
#     print(f"Generated translated PDF at: {output_pdf_path}")
#
#     return {**state, "output_pdf_path": str(output_pdf_path)}


# Build the workflow graph
graph = StateGraph(GeneralState)
graph.add_node("ocr", ocr)
graph.add_node("bubble_selector", bubble_selector)
graph.add_node("translator", translator)
graph.add_node("text_writer", text_writer)
graph.add_edge("ocr", "bubble_selector")
graph.add_edge("bubble_selector", "translator")
graph.add_edge("translator", "text_writer")
graph.add_edge("text_writer", END)
graph.set_entry_point("ocr")

# Compile the workflow
app = graph.compile()

# Only run if this file is executed directly (not imported)
if __name__ == "__main__":
    test_work_dir = Path("output/test_work")
    test_work_dir.mkdir(parents=True, exist_ok=True)

    test_input = Path("input/opmv30")
    manga_norm = MangaNormalizer()
    manga_loader = MangaLoader(manga_norm)
    manga = manga_loader.load_directory(test_input)

    app_res = app.invoke(
        GeneralState(
            {
                "manga_name": "abc",
                "original_manga": manga,
                "work_dir": test_work_dir,
                "original_bubbles": None,
                "original_ocr_result": None,
                "translated_bubbles": None,
                "output_pdf_path": None,
            }
        )
    )
