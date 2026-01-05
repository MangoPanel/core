from dotenv import load_dotenv

load_dotenv()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph import GeneralState

from langchain_openai import ChatOpenAI
from pathlib import Path
import json


def translate_text(text: list[str], llm: ChatOpenAI) -> list[str]:
    if not text:
        return []
    joined_text = "\n".join(text)
    prompt = (
        "You are a translation system. Translate each Japanese line into natural English. "
        "Return ONLY the translated lines, in the same order, one per line. "
        "Do NOT add commentary, explanations, or formatting. "
        "Input:\n"
        f"{joined_text}\n\nOutput:"
    )
    response = llm.invoke(prompt)
    translated_lines = response.content.split("\n")
    return [line.strip() for line in translated_lines if line.strip()]





def translator(state: "GeneralState") -> "GeneralState":
    og_bubbles = state["original_bubbles"]

    if not og_bubbles:
        raise ValueError("missing data - cant translate")

    llm = ChatOpenAI(model="Qwen3", temperature=0.3, base_url="http://10.10.10.20:8000")

    for bubble_page in og_bubbles:

    return {**state, "translated_json_representation": translated_repr}

