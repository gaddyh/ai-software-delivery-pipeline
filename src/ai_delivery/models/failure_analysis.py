"""Structured analysis produced by the FailureAnalyzerAgent."""

from pydantic import BaseModel, Field


class FailureAnalysis(BaseModel):
    """Distilled patch instruction derived from a set of failing pytest tests."""

    failed_tests: list[str] = Field(
        description="Names of the tests that failed in this iteration."
    )
    inferred_rules: list[str] = Field(
        description=(
            "Business rules inferred from the assertion values in the failure output. "
            "Each entry is a plain-English statement of one rule the implementation must satisfy."
        )
    )
    likely_bug: str = Field(
        description="One-sentence diagnosis of the most probable defect in the current code."
    )
    patch_instruction: str = Field(
        description=(
            "Concrete, actionable instruction for the Developer Agent: what to change, "
            "in what order, and why."
        )
    )
