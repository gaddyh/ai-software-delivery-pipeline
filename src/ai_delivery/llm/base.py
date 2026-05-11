from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def invoke(self, prompt: str, schema: dict | None = None) -> dict:
        pass