"""OpenAI-backed LLM client."""

import json
import os
import time

from openai import OpenAI

from ai_delivery.llm.base import LLMClient

from dotenv import load_dotenv

load_dotenv()

_SYSTEM_DEFAULT = "You are a helpful assistant. Always respond with valid JSON."


class OpenAIClient(LLMClient):
    """LLM client backed by the OpenAI Chat Completions API.

    Every call returns a parsed ``dict``; the model is always instructed to
    produce JSON.  Pass a JSON Schema via ``schema`` to enable strict
    structured output; omit it to use open-ended ``json_object`` mode.
    """

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None) -> None:
        """Initialise the client.

        Args:
            model: OpenAI model name.
            api_key: API key.  Defaults to the ``OPENAI_API_KEY`` env var.
        """
        self.model = model
        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    def invoke(self, prompt: str, schema: dict | None = None) -> dict:
        """Send *prompt* to the model and return the parsed JSON response.

        Args:
            prompt: User-facing prompt text.
            schema: Optional JSON Schema dict.  When provided the request uses
                OpenAI's strict ``json_schema`` structured-output mode.
                When omitted the request uses ``json_object`` mode and the
                caller is responsible for instructing JSON in the prompt.

        Returns:
            Parsed response as a plain ``dict``.
        """
        if schema is not None:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": schema,
                    "strict": True,
                },
            }
        else:
            response_format = {"type": "json_object"}

        last_refusal: str | None = None
        for attempt in range(1, 4):
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_DEFAULT},
                    {"role": "user", "content": prompt},
                ],
                response_format=response_format,
            )
            content = response.choices[0].message.content
            if content is not None:
                return json.loads(content)
            last_refusal = getattr(response.choices[0].message, "refusal", None)
            if attempt < 3:
                time.sleep(1)
        raise ValueError(
            f"OpenAI returned no content after 3 attempts (possible refusal). "
            f"Last refusal message: {last_refusal!r}"
        )
