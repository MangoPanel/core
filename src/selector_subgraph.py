from langgraph.graph.state import StateGraph, START
from typing_extensions import TypedDict, Any

from documents import MangaJSONRepresentation


class SelectorState(TypedDict):
    ocr_representation: MangaJSONRepresentation
    bubble_representation: list[dict[Any, Any]]
