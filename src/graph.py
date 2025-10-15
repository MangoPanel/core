from typing import Any, Dict, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json
from documents import Manga, MangaJSONRepresentation
from pathlib import Path

from paddleocr import PaddleOCR


class GeneralState(TypedDict):
    oryginal_manga: Manga
    inpainted_manga: Manga | None
    translated_manga: Manga | None

    oryginal_json_representation: MangaJSONRepresentation | None
    translated_json_representation: MangaJSONRepresentation | None


def ocr(state: GeneralState) -> GeneralState:
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """

    ocr = PaddleOCR(
        use_doc_orientation_classify=False, use_doc_unwarping=False, lang="japan"
    )
    og_manga = state["oryginal_manga"]
    result = ocr.predict_iter(f"{og_manga.path}")

    for res in result:
        res.save_to_json("output")

    representation = MangaJSONRepresentation(Path("output"))

    for i, page in enumerate(representation):
        print(f"{i}page: {page['rec_texts']}")

    state["oryginal_manga"].save_to_pdf()

    return {**state, "oryginal_json_representation": representation}


def text_selector(state: GeneralState): ...


def translator(state: GeneralState):
    """
    Translator node. Responsible for translating text.
    """
    ...


graph = StateGraph(GeneralState)
graph.add_node("ocr", ocr)
graph.set_entry_point("ocr")

app = graph.compile()

app_res = app.invoke(
    {
        "oryginal_manga": Manga(Path("input/test")),
        "inpainted_manga": None,
        "translated_manga": None,
        "oryginal_json_representation": None,
        "translated_json_representation": None,
    }
)
