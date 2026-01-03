from typing import Any, Dict, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json
from documents import Manga, MangaJSONRepresentation
from pathlib import Path

from paddleocr import PaddleOCR
from translation import translator

class GeneralState(TypedDict):
    oryginal_manga: Manga
    inpainted_manga: Manga | None
    translated_manga: Manga | None

    oryginal_json_representation: MangaJSONRepresentation | None
    translated_json_representation: MangaJSONRepresentation | None
    
    work_dir: Path  # Working directory for processing
    output_pdf_path: str | None  # Path to final translated PDF


def ocr(state: GeneralState) -> GeneralState:
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """

    ocr = PaddleOCR(
        use_doc_orientation_classify=False, use_doc_unwarping=False, lang="japan"
    )
    og_manga = state["oryginal_manga"]
    work_dir = state["work_dir"]
    ocr_output_dir = work_dir / "ocr_output"
    ocr_output_dir.mkdir(exist_ok=True)
    
    result = ocr.predict_iter(f"{og_manga.path}")

    for res in result:
        res.save_to_json(str(ocr_output_dir))

    representation = MangaJSONRepresentation(ocr_output_dir)

    for i, page in enumerate(representation):
        print(f"Text from page {i}: {page['rec_texts']}")

    return {**state, "oryginal_json_representation": representation}


def text_selector(state: GeneralState): ...


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
