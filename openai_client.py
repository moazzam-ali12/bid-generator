from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import os
import httpx


@dataclass
class OpenAIConfig:
    api_key: str
    base_url: str  # e.g. https://api.openai.com/v1
    model: str
    temperature: float = 0.1
    max_tokens: int = 6000
    timeout_s: float = 120.0


class OpenAIClient:
    """
    OpenAI-compatible chat client.
    Works with OpenAI API and any OpenAI-compatible endpoints.
    """
    def __init__(self, cfg: OpenAIConfig):
        self.cfg = cfg

    def chat_json(self, system: str, user: str) -> str:
        """
        Make a chat completion request and return the response content.
        """
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        
        payload: Dict[str, Any] = {
            "model": self.cfg.model,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        with httpx.Client(timeout=self.cfg.timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        # OpenAI response format
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response shape: {data}") from e