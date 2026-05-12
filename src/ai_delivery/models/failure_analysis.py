"""Structured analysis produced by the FailureAnalyzerAgent."""

from typing import Optional

from pydantic import BaseModel, Field


class StructuredTestFailure(BaseModel):
    """Factual record of a single failing test extracted from pytest output."""

    test_name: str = Field(description="Name of the failing test.")
    failure_type: str = Field(description="Exception or failure type, e.g. 'AssertionError', 'ValueError'.")
    expected: Optional[str] = Field(default=None, description="Expected value from the assertion, if extractable.")
    actual: Optional[str] = Field(default=None, description="Actual value produced by the code, if extractable.")
    error_message: str = Field(description="The assertion or error message text.")
    trace_excerpt: str = Field(description="Relevant snippet of the stack trace for this test.")


class FailureAnalysis(BaseModel):
    """Structured facts extracted from a pytest run by the FailureAnalyzerAgent."""

    failed_tests: list[StructuredTestFailure] = Field(
        description="One entry per failing test, with extracted evidence."
    )
    failure_summary: str = Field(
        description=(
            "Concise plain-English overview of what failed and why, "
            "e.g. '2 tests failed. test_X expected 63.34 but got 63.34001. "
            "test_Y raised ValueError unexpectedly.'"
        )
    )
