"""Structured analysis produced by the FailureAnalyzerAgent."""

from typing import Optional

from pydantic import BaseModel, Field

FAILURE_CATEGORIES = (
    "precision_rounding_error",
    "formula_logic_error",
    "validation_error",
    "missing_branch_error",
    "type_error",
    "overfitting_suspected",
    "unknown",
)


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
    expected_value: Optional[str] = Field(
        default=None,
        description="Expected value extracted from the first failing assertion, e.g. '63.34'.",
    )
    actual_value: Optional[str] = Field(
        default=None,
        description="Actual value extracted from the first failing assertion, e.g. '63.34000000001'.",
    )
    difference: Optional[str] = Field(
        default=None,
        description="Human-readable delta between actual and expected, e.g. '~1e-11'.",
    )
    failure_category: str = Field(
        default="unknown",
        description=(
            "Category of the failure. One of: "
            + ", ".join(FAILURE_CATEGORIES)
        ),
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the failure_category classification (0.0–1.0). "
            "Use >= 0.8 only when evidence strongly supports the category."
        ),
    )
