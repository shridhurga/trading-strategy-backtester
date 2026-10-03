import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL


def get_model():
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not found. Add it to your .env file or enable Demo Mode."
        )
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)


def clean_llm_output(text: str) -> str:
    return text.strip().replace("```python", "").replace("```json", "").replace("```", "").strip()
