import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from manga_processor.models.types import BubblePage
from typing import cast
from langchain_openai import ChatOpenAI
import re


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

        input_payload = {
            "page_index": page.index,
            "items": [{"id": j, "text": b.text} for j, b in enumerate(page.bubbles)],
        }

        combined_prompt = (
            f"You are a translator. Translate the following manga content to English.\n"
            f"Context: {context_string}\n\n"
            f"Return ONLY a JSON object following this exact schema:\n"
            f'{{"pages": [{{"page_index": {page.index}, "bubbles": [{{"index_in_page": 0, "english_translation": "..."}}]}}]}}\n\n'
            f"DATA: {json.dumps(input_payload, ensure_ascii=False)}"
        )

        messages = [{"role": "user", "content": combined_prompt}]

        try:
            raw_response = llm.invoke(messages).content
            clean_json = re.sub(
                r"^```json\s*|```$", "", raw_response.strip(), flags=re.MULTILINE
            )
            response = TranlationResponse.model_validate_json(clean_json)

            page_text_accumulator = []

            for page_update in response.pages:
                for b_update in page_update.bubbles:
                    idx = b_update.index_in_page

                    if 0 <= idx < len(page.bubbles):
                        trans = b_update.english_translation
                        page.bubbles[idx].text = trans
                        page_text_accumulator.append(trans)
                    else:
                        print(f"⚠️ Model hallucinated index {idx} on page {page.index}")

            full_page_text = " ".join(page_text_accumulator)
            story_context.append(f"Page {page.index}: {full_page_text}")

            story_context = story_context[-2:]

        except Exception as e:
            print(f"Error on page {page.index}: {e}")

    return pages
