# src/ai_enricher.py
import json
import re
import requests
from abc import ABC, abstractmethod
from config import Config

class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 100) -> str:
        pass

class OllamaProvider(AIProvider):
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://localhost:11434/v1"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/chat/completions"

    def generate(self, prompt: str, max_tokens: int = 100) -> str:
        response = requests.post(
            self.endpoint,
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a cyber security expert. Answer concisely."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

class OpenAIProvider(AIProvider):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = None):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key or Config.AI_API_KEY)
            self.model = model
        except ImportError:
            raise ImportError("openai library not installed. Install it with 'pip install openai'")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

    def generate(self, prompt: str, max_tokens: int = 100) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a cyber security expert. Answer concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

class AIEnricher:
    def __init__(self, provider: str = None, model: str = None, api_key: str = None, base_url: str = None):
        self.provider_name = provider or Config.AI_PROVIDER
        self.model = model or Config.AI_MODEL
        self.provider = self._create_provider(api_key, base_url)

    def _create_provider(self, api_key=None, base_url=None):
        if self.provider_name == "ollama":
            return OllamaProvider(model=self.model, base_url=base_url or Config.AI_BASE_URL)
        elif self.provider_name == "openai":
            return OpenAIProvider(model=self.model, api_key=api_key or Config.AI_API_KEY)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider_name}")

    def generate(self, prompt: str, max_tokens: int = 100) -> str:
        return self.provider.generate(prompt, max_tokens)