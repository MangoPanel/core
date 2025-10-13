from typing import Any, Dict, TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage
import json

from paddleocr import PaddleOCR


class GeneralState(TypedDict):
    pdf_path: str
    oryginal_json_path: str
    translated_json_path: str
    
def ocr(state: GeneralState) -> GeneralState:
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """
    
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, lang="japan")
    result = ocr.predict_iter(state["pdf_path"])

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

app_res = app.invoke({"pdf_path": "input/test", "oryginal_json_path": "", "translated_json_path": ""})


