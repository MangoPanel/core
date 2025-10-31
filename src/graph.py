from pathlib import Path
from typing import TypedDict, Any

from langgraph.graph import StateGraph
from paddleocr import PaddleOCR

from documents import Manga, MangaJSONRepresentation

import paint


class GeneralState(TypedDict):
    original_manga: Manga
    clean_manga: Manga | None
    translated_manga: Manga | None

    ocr_representation: MangaJSONRepresentation | None
    bubble_representation: list[dict[Any, Any]] | None


def ocr(state: GeneralState) -> GeneralState:
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """

    ocr = PaddleOCR(
        use_doc_orientation_classify=False, use_doc_unwarping=False, lang="japan"
    )
    og_manga = state["original_manga"]
    result = ocr.predict_iter(f"{og_manga.path}")

    for res in result:
        res.save_to_json("output")

    representation = MangaJSONRepresentation(Path("output"))

    return {**state, "ocr_representation": representation}


def bubble_selector(state: GeneralState):
    manga = state["original_manga"]
    ocr_rep = state["ocr_representation"]
    if ocr_rep is None or manga is None:
        raise ValueError("Expected non-None value, but got None")
    bubble_rep = []

    for img_page, json_page in zip(manga, ocr_rep):
        text_polygons = json_page["rec_polys"]
        bubble_page = paint.create_bubble_representation(
            img_page, text_polygons, 500, 500000, 0.05, 0.2
        )
        bubble_rep.append(bubble_page)

    return {**state, "bubble_representation": bubble_rep}


def bubble_cleaner(state: GeneralState):
    manga = state["original_manga"]
    bubble_rep = state["bubble_representation"]
    if bubble_rep is None or manga is None:
        raise ValueError("Expectred non-None value, but got None")
    for i, (img_page, bubble_page) in enumerate(zip(manga, bubble_rep)):
        bubbles = [item["contour"] for item in bubble_page if item["is_bubble"]]
        paint.clean_contours(
            img_page,
            bubbles,
            f"output-clean/{i:03d}.png",
        )

    clean_manga = Manga(
        Path("output-clean")
    )
    clean_manga.save_to_pdf()

    return {**state, "clean_manga": clean_manga}

def text_writer(state: GeneralState):
    clean_manga = state["clean_manga"]
    bubble_rep = state["bubble_representation"]
    ocr_rep = state["ocr_representation"]
    if bubble_rep is None or clean_manga is None or ocr_rep is None:
        raise ValueError("Expected to get clean manga, ocr rep and bubble rep. One or more is None")
    
    for i, (img_page, bubble_page, ocr_page) in enumerate(zip(clean_manga, bubble_rep, ocr_rep)):
        bubbles = [item["contour"] for item in bubble_page if item["is_bubble"]]
        text = ocr_page["rec_texts"]
        paint.write_into_contours(bubbles, text)
    


graph = StateGraph(GeneralState)
graph.add_node("ocr", ocr)
graph.add_node("selector", bubble_selector)
graph.add_node("cleaner", bubble_cleaner)
graph.add_node("writer", text_writer)
graph.set_entry_point("ocr")
graph.add_edge("ocr", "selector")
graph.add_edge("selector", "cleaner")
graph.add_edge("cleaner", "writer")
graph.set_finish_point("writer")

app = graph.compile()
app_res = app.invoke(
    {
        "original_manga": Manga(Path("input/opmv30")),
        "clean_manga": None,
        "translated_manga": None,
        "ocr_representation": None,
        "bubble_representation": None,
    }
)
