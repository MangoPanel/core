from manga_processor.filesys import OCRPageLoader, OCRResultLoader, PageLoader
from manga_processor.filesys.savers.ocrresaver import OCRPageSaver
from manga_processor.manga.mangabubbledetector import MangaBubbleDetector
from manga_processor.models import Manga
from typing import Any, Dict, Iterable, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json
from pathlib import Path

from paddleocr import PaddleOCR
from manga_processor.models.types import BubblePage, OCRResult
from translation import translator


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

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        lang="japan",
    )
    work_dir: Path = state["work_dir"]
    ocr_output_dir: Path = work_dir / "ocr_output"
    ocr_output_dir.mkdir(exist_ok=True)

    ocr_input_dir: Path = work_dir / "input"
    ocr_input_dir.mkdir(exist_ok=True)
    result: Iterable[type] = ocr.predict_iter(input=ocr_input_dir)

    ocr_page_saver: OCRPageSaver = OCRPageSaver()
    for num, res in enumerate(result):
        ocr_page_saver.save_from_dirty_dict(
            data_dict=res.json, index=num, output_dir_path=ocr_output_dir
        )

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


def pdf_generator(state: GeneralState) -> GeneralState:
    """
    Generate final translated PDF from processed manga pages.
    """
    work_dir = state["work_dir"]
    output_pdf_path = work_dir / "translated_output.pdf"

    # Get the manga with translated pages
    manga = state["oryginal_manga"]
    manga.save_to_pdf(str(output_pdf_path))

    print(f"Generated translated PDF at: {output_pdf_path}")

    return {**state, "output_pdf_path": str(output_pdf_path)}


# Build the workflow graph
graph = StateGraph(GeneralState)
graph.add_node("ocr", ocr)
graph.add_node("translator", translator)
graph.add_node("pdf_generator", pdf_generator)
graph.add_edge("ocr", "translator")
graph.add_edge("translator", "pdf_generator")
graph.add_edge("pdf_generator", END)
graph.set_entry_point("ocr")

# Compile the workflow
app = graph.compile()

# Only run if this file is executed directly (not imported)
if __name__ == "__main__":
    test_work_dir = Path("output/test_work")
    test_work_dir.mkdir(parents=True, exist_ok=True)

    app_res = app.invoke(
        {
            "oryginal_manga": Manga(Path("input/test")),
            "inpainted_manga": None,
            "translated_manga": None,
            "oryginal_json_representation": None,
            "translated_json_representation": None,
            "work_dir": test_work_dir,
            "output_pdf_path": None,
        }
    )
