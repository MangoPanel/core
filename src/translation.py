from dotenv import load_dotenv
from pydantic import BaseModel, Field
from manga_processor.models.types import BubblePage
from typing import cast
from langchain_openai import ChatOpenAI


class BubbleOutput(BaseModel):
    index_in_page: int = Field(description="The original index of the bubble")
    english_translation: str = Field(description="The text converted into English")


class PageOutput(BaseModel):
    page_index: int = Field(description="The original index of the page")
    bubbles: list[BubbleOutput]


class TranlationResponse(BaseModel):
    pages: list[PageOutput]


def translate_bubbles(
    pages: list[BubblePage], source_lang: str, target_lang: str, llm: ChatOpenAI
) -> list[BubblePage]:
    structured_llm = llm.with_structured_output(TranlationResponse)

    story_context = []

    for page in pages:
        if not page.bubbles:
            continue

        context_string = (
            " | ".join(story_context[-8:]) if story_context else "Beginning of story."
        )

        print(f"Translating page {page.index} with story context: {context_string}")

        input_data = [
            {
                "page_index": page.index,
                "bubbles": [
                    {"id": j, "text": b.text} for j, b in enumerate(page.bubbles)
                ],
            }
        ]

        system_message = (
            f"You are a Manga Translator. Context: {context_string}\n"
            "Translate the text naturally. Avoid repeating yourself. \n"
            "If OCR text looks broken, use context to fix it."
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"JSON to translate:\n{input_data}"},
        ]

        try:
            response = cast(TranlationResponse, structured_llm.invoke(messages))

            for page_update in response.pages:
                for b_update in page_update.bubbles:
                    trans = b_update.english_translation
                    page.bubbles[b_update.index_in_page].text = trans
                    story_context.append(trans)

        except Exception as e:
            print(f"Error on page {page.index}: {e}")

    return pages
