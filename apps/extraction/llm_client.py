# OWNER: Dev B
import os
from pathlib import Path


class LLMClient:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

    def complete(self, system, user):
        r = self.client.messages.create(
            model=self.model, max_tokens=4000, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in r.content if b.type == "text")


class FakeClient(LLMClient):
    """Known-good saved run: used if the API is slow or the Wi-Fi fails."""
    def __init__(self, path="demo_data/known_good_run.json"):
        self.path = path

    def complete(self, system, user):
        return Path(self.path).read_text(encoding="utf-8")


def get_client() -> LLMClient:
    return FakeClient() if os.getenv("LLM_PROVIDER") == "fake" else AnthropicClient()