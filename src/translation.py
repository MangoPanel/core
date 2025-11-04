from dotenv import load_dotenv
load_dotenv()

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from graph import GeneralState

from langchain_openai import ChatOpenAI
from documents import MangaJSONRepresentation
from pathlib import Path
import json
import os


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
    original_json = state.get("oryginal_json_representation")
    if not original_json:
        raise ValueError("missing data from OCR - cant translate")

    output_dir = Path("output/translated_jsons")
    os.makedirs(output_dir, exist_ok=True)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    for i, page in enumerate(original_json):
        page_text = page.get("rec_texts", [])
        translations = translate_text(page_text, llm)

        translated_page = {
            "page_index": i,
            "original_text": page_text,
            "translated_text": translations,
        }

        output_path = output_dir / f"page_{i:03d}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(translated_page, f, ensure_ascii=False, indent=2)

        print(f"Translared page {i}: {len(translations)} segments")

    translated_repr = MangaJSONRepresentation(output_dir)
    return {**state, "translated_json_representation": translated_repr}