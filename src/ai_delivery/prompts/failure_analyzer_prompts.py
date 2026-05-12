"""Prompt builder for FailureAnalyzerAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec


FAILURE_ANALYSIS_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "failed_tests": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Names of the tests that failed.",
        },
        "inferred_rules": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Business rules inferred from the assertion values. "
                "Each entry is a plain-English rule the implementation must satisfy."
            ),
        },
        "likely_bug": {
            "type": "string",
            "description": "One-sentence diagnosis of the most probable defect.",
        },
        "patch_instruction": {
            "type": "string",
            "description": (
                "Concrete, actionable instruction for the Developer Agent: "
                "what to change, in what order, and why."
            ),
        },
    },
    "required": ["failed_tests", "inferred_rules", "likely_bug", "patch_instruction"],
    "additionalProperties": False,
}


def analyze_failures_prompt(
    task_spec: "TaskSpec",
    failed_tests: list[str],
    pytest_output: str,
) -> str:
    """Build the prompt that turns raw pytest output into a structured patch instruction."""
    failed_list = "\n".join(f"  - {t}" for t in failed_tests) if failed_tests else "  (see output)"
    return (
        "You are a senior software engineer analysing failing tests.\n\n"
        f"Task the code is supposed to implement:\n  {task_spec.description}\n\n"
        f"Function signature:\n  {task_spec.function_signature}\n\n"
        f"Failed tests:\n{failed_list}\n\n"
        "--- PYTEST OUTPUT ---\n"
        f"{pytest_output}\n"
        "--- END PYTEST OUTPUT ---\n\n"
        "Study every assertion error above carefully. "
        "For each failing assertion, infer the business rule it encodes "
        "(e.g. 'cart_total > 100 should always return 0.0'). "
        "Then diagnose the most likely defect in the current implementation "
        "and write a concrete patch instruction for the developer.\n\n"
        "Return a JSON object with exactly these four keys:\n"
        "  failed_tests   — list of failing test names\n"
        "  inferred_rules — list of plain-English business rules (one per failing assertion)\n"
        "  likely_bug     — one-sentence diagnosis\n"
        "  patch_instruction — what the developer must change and in what order\n"
    )
