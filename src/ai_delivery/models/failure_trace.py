"""Failure trace models for the TDG refinement loop."""

from pydantic import BaseModel, Field


class IterationRecord(BaseModel):
    """Record of a single failed iteration in the refinement loop."""

    iteration: int = Field(..., description="Iteration number (1-based)")
    failed_tests: list[str] = Field(default_factory=list, description="Names of failed tests")
    traceback_summary: str = Field(default="", description="First error block from pytest output")
    exit_code: int = Field(..., description="Pytest exit code")


class FailureTrace(BaseModel):
    """Accumulated history of all failed iterations for a single run."""

    history: list[IterationRecord] = Field(default_factory=list)

    def latest(self) -> IterationRecord | None:
        """Return the most recent failure record."""
        return self.history[-1] if self.history else None

    def summary(self) -> str:
        """Human-readable summary of all prior failed attempts."""
        if not self.history:
            return ""
        lines = [f"Prior failed attempts: {len(self.history)}"]
        for record in self.history:
            lines.append(
                f"  Iteration {record.iteration}: "
                f"{len(record.failed_tests)} test(s) failed — "
                f"{', '.join(record.failed_tests[:3])}"
            )
        return "\n".join(lines)
