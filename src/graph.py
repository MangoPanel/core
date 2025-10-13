from typing import TypedDict, List, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage

class GeneralState(TypedDict):
    pdf_path: str
    oryginal_text: Annotated[list, add_messages]
    translated_text: Annotated[list, add_messages]

def ocr(state: GeneralState):
    """
    OCR node. Responsible for finding and extracting text from given pdf
    """
    return {"oryginal_text": AIMessage("chingchong")}

def 

def translator(state: GeneralState):
    """Translator node. Responsible for translating text."""
    ...
