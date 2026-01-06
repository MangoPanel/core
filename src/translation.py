from dotenv import load_dotenv
from pydantic import BaseModel, Field
from manga_processor.models.types import BubblePage
from typing import cast
from langchain_openai import ChatOpenAI


class BubbleOutput(BaseModel):
    index_in_page: int = Field(description="The original index of the bubble")
    translated_text: str = Field(description="The translated text for this bubble")


class PageOutput(BaseModel):
    page_index: int = Field(description="The original index of the page")
    bubbles: list[BubbleOutput]


class TranlationResponse(BaseModel):
    pages: list[PageOutput]


def translate_bubbles(
    pages: list[BubblePage], source_lang: str, target_lang: str, llm: ChatOpenAI
) -> list[BubblePage]:
    structured_llm = llm.with_structured_output(TranlationResponse)

    input_data = []
    for page in pages:
        page_content = {
            "page_index": page.index,
            "bubbles": [{"id": i, "text": b.text} for i, b in enumerate(page.bubbles)],
        }
        input_data.append(page_content)

    prompt: str = (
        f"Translate the following document bubbles from {source_lang} to {target_lang}./n"
        + f"Maintain the context of the story across pages.\n\nData: {input_data}"
    )

    response = cast(TranlationResponse, structured_llm.invoke(prompt))

    for page_update in response.pages:
        og_page: BubblePage = pages[page_update.page_index]
        for b_update in page_update.bubbles:
            og_page.bubbles[b_update.index_in_page].text = b_update.translated_text

    return pages
