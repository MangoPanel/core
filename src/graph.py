from typing import Any, Dict, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json
from pdf import Manga

from paddleocr import PaddleOCR


class GeneralState(TypedDict):
    oryginal_manga: Manga
    inpainted_manga: Union[Manga, None]
    translated_manga: Union[Manga, None]

def ocr(state: GeneralState) -> GeneralState:
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """
    
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, lang="japan")
    og_manga = state["oryginal_manga"]
    result = ocr.predict_iter(og_manga)

    for res in result:
        res.save_to_json("output")
        
    return {
        **state,
        "oryginal_json_path": "output"
    }

def text_selector(state: GeneralState):
    ...

def translator(state: GeneralState):
    """
    Translator node. Responsible for translating text.
    """
    ...

graph = StateGraph(GeneralState)
graph.add_node("ocr", ocr)
graph.set_entry_point("ocr")

app = graph.compile()

app_res = app.invoke({"oryginal_manga": Manga("input/test"), 
                      "inpainted_manga": None, 
                      "translated_manga": None})


