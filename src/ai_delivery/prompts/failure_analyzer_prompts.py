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
            "description": "One object per failing test.",
            "items": {
                "type": "object",
                "properties": {
                    "test_name": {
                        "type": "string",
                        "description": "The full test function name as it appears in pytest output.",
                    },
                    "failure_type": {
                        "type": "string",
                        "description": "The exception class, e.g. 'AssertionError', 'ValueError', 'TypeError'.",
                    },
                    "expected": {
                        "type": "string",
                        "description": "Expected value from the assertion line, empty string if not extractable.",
                    },
                    "actual": {
                        "type": "string",
                        "description": "Actual value produced by the code, empty string if not extractable.",
                    },
                    "error_message": {
                        "type": "string",
                        "description": "The full assertion or error message text.",
                    },
                    "trace_excerpt": {
                        "type": "string",
                        "description": "The most relevant 3-5 lines of the stack trace for this test.",
                    },
                },
                "required": ["test_name", "failure_type", "expected", "actual", "error_message", "trace_excerpt"],
                "additionalProperties": False,
            },
        },
        "failure_summary": {
            "type": "string",
            "description": (
                "Concise plain-English overview of what failed, "
                "e.g. '2 tests failed. test_X expected 63.34 but got 63.34001. "
                "test_Y raised ValueError unexpectedly.'"
            ),
        },
    },
    "required": ["failed_tests", "failure_summary"],
    "additionalProperties": False,
}


def analyze_failures_prompt(
    task_spec: "TaskSpec",
    failed_tests: list[str],
    pytest_output: str,
) -> str:
    """Build the prompt that turns raw pytest output into structured per-test facts."""
    failed_list = "\n".join(f"  - {t}" for t in failed_tests) if failed_tests else "  (see output)"
    return (
        "You are a senior software engineer extracting structured failure data from pytest output.\n\n"
        f"Task the code is supposed to implement:\n  {task_spec.description}\n\n"
        f"Known failing tests:\n{failed_list}\n\n"
        "--- PYTEST OUTPUT ---\n"
        f"{pytest_output}\n"
        "--- END PYTEST OUTPUT ---\n\n"
        "For each failing test, extract the following facts directly from the pytest output.\n"
        "Do not infer, diagnose, or suggest fixes. Only report what the output shows.\n\n"
        "For each failing test, extract:\n"
        "  test_name     — the full test function name as shown in pytest (e.g. 'test_apply_discount_rounding')\n"
        "  failure_type  — the exception class (e.g. 'AssertionError', 'ValueError', 'TypeError')\n"
        "  expected      — the expected value from the assertion line, if present (empty string if not found)\n"
        "  actual        — the actual value the code produced, if present (empty string if not found)\n"
        "  error_message — the full assertion or error message text\n"
        "  trace_excerpt — the 3-5 most relevant lines of the stack trace for this test\n\n"
        "Then write a failure_summary: a concise plain-English overview of what failed.\n"
        "Example: '2 tests failed. test_rounding expected 63.34 but got 63.34001. "
        "test_vip_price raised ValueError when VIP surcharge was applied.'\n\n"
        "Return a JSON object with exactly these keys:\n"
        "  failed_tests    — array of per-test objects as described above\n"
        "  failure_summary — concise plain-English overview\n"
    )
