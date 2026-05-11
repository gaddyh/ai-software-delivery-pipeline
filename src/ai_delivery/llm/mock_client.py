from ai_delivery.llm.base import LLMClient


class MockLLMClient(LLMClient):
    def invoke(self, prompt: str, schema: dict | None = None) -> dict:
        if "Generate pytest tests" in prompt:
            return {"content": """
import pytest
from solution import calculate_shipping

def test_free_shipping_for_large_order():
    assert calculate_shipping(cart_total=120, weight=2) == 0

def test_standard_shipping_under_threshold():
    assert calculate_shipping(cart_total=50, weight=2) == 5

def test_heavy_shipping_under_threshold():
    assert calculate_shipping(cart_total=50, weight=10) == 15
"""}

        if "Refactor the code" in prompt:
            return {"content": """
def calculate_shipping(cart_total: float, weight: float) -> float:
    if cart_total >= 100:
        return 0

    if weight > 5:
        return 15

    return 5
"""}

        if "Fix the code" in prompt:
            return {"content": """
def calculate_shipping(cart_total: float, weight: float) -> float:
    if cart_total >= 100:
        return 0

    if weight > 5:
        return 15

    return 5
"""}

        if "Generate Python code" in prompt:
            # Intentionally wrong first version.
            # This lets us see the refactor loop working.
            return {"content": """
def calculate_shipping(cart_total: float, weight: float) -> float:
    if cart_total >= 100:
        return 0

    return 5
"""}

        if "Refactor passing code" in prompt:
            return {"content": """
FREE_SHIPPING_THRESHOLD = 100
HEAVY_PACKAGE_THRESHOLD = 5
STANDARD_SHIPPING_COST = 5
HEAVY_SHIPPING_COST = 15


def calculate_shipping(cart_total: float, weight: float) -> float:
    if cart_total >= FREE_SHIPPING_THRESHOLD:
        return 0

    if weight > HEAVY_PACKAGE_THRESHOLD:
        return HEAVY_SHIPPING_COST

    return STANDARD_SHIPPING_COST
"""}

        raise ValueError(f"MockLLMClient received an unknown prompt:\n{prompt}")