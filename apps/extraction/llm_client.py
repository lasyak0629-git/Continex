# OWNER: Dev B
import os
from pathlib import Path


def _load_env():
    try:
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv(usecwd=True))
    except ImportError:
        pass


class LLMClient:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    def __init__(self):
        _load_env()
        import anthropic
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

    def complete(self, system, user):
        r = self.client.messages.create(
            model=self.model, max_tokens=6000, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in r.content if b.type == "text")


class GeminiClient(LLMClient):
    def __init__(self):
        _load_env()
        from google import genai
        key = (os.getenv("GEMINI_API_KEY") or "").strip()
        # Normal Gemini API mode by default. Vertex mode only if GEMINI_VERTEX=true in .env.
        if os.getenv("GEMINI_VERTEX", "").strip().lower() == "true":
            self.client = genai.Client(vertexai=True, api_key=key)
        else:
            self.client = genai.Client(api_key=key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def complete(self, system, user):
        from google.genai import types
        r = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=8000,
                response_mime_type="application/json",
            ),
        )
        return r.text


class FakeClient(LLMClient):
    """Known-good saved run: used if the API is slow or the Wi-Fi fails."""
    def __init__(self, path="demo_data/known_good_run.json"):
        self.path = path

    def complete(self, system, user):
        return Path(self.path).read_text(encoding="utf-8")


def get_client() -> LLMClient:
    _load_env()
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "fake":
        return FakeClient()
    if provider == "gemini":
        return GeminiClient()
    return AnthropicClient()