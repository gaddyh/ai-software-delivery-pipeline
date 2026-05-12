"""Quality report produced by the CodeQualityCriticAgent."""

from pydantic import BaseModel, Field


class QualityReport(BaseModel):
    """Result of a code quality review looking for overfitting and hardcoded hacks."""

    passed: bool = Field(
        description="True if no quality issues were found; False if any flags were raised."
    )
    flags: list[str] = Field(
        description=(
            "Human-readable descriptions of each quality issue found. "
            "Empty when passed is True."
        )
    )
    summary: str = Field(
        description=(
            "One-sentence overall verdict, e.g. "
            "'Code passes quality review.' or "
            "'Found 2 overfitting patterns that must be corrected.'"
        )
    )
