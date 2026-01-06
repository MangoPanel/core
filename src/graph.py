from pydantic import SecretStr
from manga_processor.debug.debug_visual import VisualDebuger
from manga_processor.filesys import (
    MangaLoader,
    MangaNormalizer,
    OCRPageLoader,
    OCRResultLoader,
    PageLoader,
)
from manga_processor.filesys.savers.ocrresaver import OCRPageSaver
from manga_processor.manga.mangabubbledetector import MangaBubbleDetector
from typing import Any, Dict, Iterable, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json
from pathlib import Path

from paddleocr import PaddleOCR
from manga_processor.models.types import BubblePage, OCRResult, Manga
from translation import translate_bubbles


class GeneralState(TypedDict):
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

    # ocr = PaddleOCR(
    #     use_doc_orientation_classify=False,
    #     use_doc_unwarping=False,
    #     lang="japan",
    # )
    work_dir: Path = state["work_dir"]
    ocr_output_dir: Path = work_dir / "ocr_output"
    ocr_output_dir.mkdir(exist_ok=True)
    input_dir = state["original_manga"].dir_path
    # result: Iterable[type] = ocr.predict_iter(input=f"{input_dir}")
    # img_dir = ocr_output_dir / "img"
    # ocr_page_saver: OCRPageSaver = OCRPageSaver()
    # for num, res in enumerate(result):
    #     ocr_page_saver.save_from_dirty_dict(
    #         data_dict=res.json, index=num, output_dir_path=ocr_output_dir
    #     )
    #     img_path = img_dir / f"{num}"
    #     res.save_to_img(f"{img_path}.png")

    ocr_res_loader: OCRResultLoader = OCRResultLoader()
    ocr_res: OCRResult = ocr_res_loader.load_directory(path=ocr_output_dir)
    return {**state, "original_ocr_result": ocr_res}


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

    llm: ChatOpenAI = ChatOpenAI(
        model="Qwen3",
        temperature=0.3,
        base_url="http://10.10.10.20:8000/v1",
        api_key=SecretStr("abc"),
    )

    translated_bubbles: list[BubblePage] = translate_bubbles(
        og_bubbles, "Japanese", "English", llm
    )

    return {**state, "translated_bubbles": translated_bubbles}


def text_writer(state: GeneralState) -> GeneralState:
    translated_bubbles: list[BubblePage] | None = state["translated_bubbles"]
    if translated_bubbles is None:
        raise ValueError("Translated bubbles are missing cannot write text")

    for bubble_page in translated_bubbles:
        print(f"Page {bubble_page.index}")
        for bubble in bubble_page.bubbles:
            print(f"bubble text: {bubble.text}")


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
# graph.add_edge("bubble_selector", "translator")
# graph.add_edge("translator", "text_writer")
graph.add_edge("bubble_selector", END)
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
                "original_manga": manga,
                "work_dir": test_work_dir,
                "original_bubbles": None,
                "original_ocr_result": None,
                "translated_bubbles": None,
                "output_pdf_path": None,
            }
        )
    )
