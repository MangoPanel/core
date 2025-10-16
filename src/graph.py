from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph
from paddleocr import PaddleOCR

from documents import Manga, MangaJSONRepresentation


class GeneralState(TypedDict):
    original_manga: Manga
    inpainted_manga: Manga | None
    translated_manga: Manga | None

    original_json_representation: MangaJSONRepresentation | None
    translated_json_representation: MangaJSONRepresentation | None


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
    
    # Thid is a demo / debug print
    # for i, page in enumerate(representation):
    #     print(f"Text from page {i}: {page['rec_texts']}")

    # state["oryginal_manga"].save_to_pdf()

    return {**state, "original_json_representation": representation}


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
        "original_manga": Manga(Path("input/test")),
        "inpainted_manga": None,
        "translated_manga": None,
        "original_json_representation": None,
        "translated_json_representation": None,
    }
)
