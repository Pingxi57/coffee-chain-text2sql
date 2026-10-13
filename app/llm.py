"""Thin wrapper around the LLM API so the provider can be swapped later."""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
_client = genai.Client(api_key=os.getenv("LLM_API_KEY"))


def ask_llm(prompt: str) -> str:
    response = _client.models.generate_content(
        model=os.getenv("LLM_MODEL"),
        contents=prompt,
    )
    return response.text
