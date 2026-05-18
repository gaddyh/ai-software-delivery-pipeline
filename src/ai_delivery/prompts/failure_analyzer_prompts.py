"""Prompt builder for FailureAnalyzerAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec

_FAILURE_TYPE_VALUES = [
    "test_syntax_error",
    "test_indentation_error",
    "test_import_error",
    "test_collection_error",
    "numeric_precision",
    "assertion_mismatch",
    "unexpected_exception",
    "missing_exception",
    "spec_ambiguity",
    "implementation_logic_error",
    "spec_test_conflict",
    "test_expectation_not_grounded",
    "unknown",
]

_BLAMED_ARTIFACT_VALUES = [
    "implementation",
    "test_suite",
    "task_spec",
    "spec_or_test_expectation",
    "unknown",
]

_RECOMMENDED_ACTION_VALUES = [
    "repair_implementation",
    "repair_test_suite",
    "review_spec_and_tests",
    "review_test_grounding",
    "apply_minimal_numeric_repair",
    "stop_and_escalate",
    "unknown",
]

FAILURE_ANALYSIS_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "failed_tests": {
            "type": "array",
            "description": "One object per failing test or collection-level failure.",
            "items": {
                "type": "object",
                "properties": {
                    "test_name": {
                        "type": "string",
                        "description": (
                            "The full test function name as it appears in pytest output. "
                            "For collection failures where no test ran, use 'pytest_collection'."
                        ),
                    },
                    "failure_type": {
                        "type": "string",
                        "enum": _FAILURE_TYPE_VALUES,
                        "description": (
                            "Normalized failure category. Use the provided enum values only. "
                            "Do NOT use raw exception class names here."
                        ),
                    },
                    "blamed_artifact": {
                        "type": "string",
                        "enum": _BLAMED_ARTIFACT_VALUES,
                        "description": "Which artifact is most likely responsible for this failure.",
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
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Your confidence in this classification (0.0–1.0).",
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Short snippets from the pytest output that support your classification.",
                    },
                },
                "required": [
                    "test_name", "failure_type", "blamed_artifact",
                    "expected", "actual", "error_message", "trace_excerpt",
                    "confidence", "evidence",
                ],
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
        "primary_failure_type": {
            "type": "string",
            "enum": _FAILURE_TYPE_VALUES,
            "description": "The dominant failure type across all failing tests.",
        },
        "primary_blamed_artifact": {
            "type": "string",
            "enum": _BLAMED_ARTIFACT_VALUES,
            "description": "The artifact most likely responsible for the dominant failure.",
        },
        "recommended_action": {
            "type": "string",
            "enum": _RECOMMENDED_ACTION_VALUES,
            "description": "The recommended next pipeline action.",
        },
        "should_modify_code": {
            "type": "boolean",
            "description": "Whether the next repair should modify implementation code.",
        },
        "should_modify_tests": {
            "type": "boolean",
            "description": "Whether the next repair should modify the generated test suite.",
        },
        "should_review_spec": {
            "type": "boolean",
            "description": "Whether the spec/test relationship should be reviewed for ambiguity.",
        },
        "routing_reason": {
            "type": "string",
            "description": (
                "Local explanation for this iteration's routing decision. "
                "Example: 'Pytest failed during collection with SyntaxError in test_generated.py, "
                "so implementation code was not executed.'"
            ),
        },
        "lesson": {
            "type": "string",
            "description": "Reusable lesson learned from this failure, for future iterations.",
        },
    },
    "required": [
        "failed_tests", "failure_summary",
        "primary_failure_type", "primary_blamed_artifact", "recommended_action",
        "should_modify_code", "should_modify_tests", "should_review_spec",
        "routing_reason", "lesson",
    ],
    "additionalProperties": False,
}


def analyze_failures_prompt(
    task_spec: "TaskSpec",
    failed_tests: list[str],
    pytest_output: str,
) -> str:
    """Build the prompt that turns raw pytest output into structured per-test facts."""
    failed_list = "\n".join(f"  - {t}" for t in failed_tests) if failed_tests else "  (see output)"
    failure_type_list = ", ".join(_FAILURE_TYPE_VALUES)
    blamed_list = ", ".join(_BLAMED_ARTIFACT_VALUES)
    action_list = ", ".join(_RECOMMENDED_ACTION_VALUES)

    return (
        "You are a senior software engineer classifying pytest failures.\n\n"
        f"Task the code is supposed to implement:\n  {task_spec.description}\n\n"
        f"Known failing tests:\n{failed_list}\n\n"
        "--- PYTEST OUTPUT ---\n"
        f"{pytest_output}\n"
        "--- END PYTEST OUTPUT ---\n\n"
        "CLASSIFICATION RULES — follow these exactly:\n\n"
        "1. failure_type must be one of the provided enum values. "
        "Do NOT use raw exception class names (AssertionError, ValueError, etc.) as failure_type. "
        f"Allowed values: {failure_type_list}\n\n"
        "2. blamed_artifact must be one of the provided enum values. "
        f"Allowed values: {blamed_list}\n\n"
        "3. recommended_action must be one of the provided enum values. "
        f"Allowed values: {action_list}\n\n"
        "4. Do NOT populate failure_stage, raw_exception_type, failure_signature, "
        "or iteration_failure_signature — these are generated by the pipeline in code.\n\n"
        "5. Collection-phase rules (apply when pytest output shows ERROR collecting / "
        "SyntaxError / IndentationError / import failure before any test ran):\n"
        "   - failure_type    → test_syntax_error or test_indentation_error or test_import_error\n"
        "   - blamed_artifact → test_suite\n"
        "   - recommended_action → repair_test_suite\n"
        "   - should_modify_code  → false\n"
        "   - should_modify_tests → true\n"
        "   - test_name → 'pytest_collection'\n\n"
        "6. Numeric precision rule: if expected and actual differ only by floating-point "
        "representation (e.g. 7.5 vs 7.500000000000001), classify as numeric_precision, "
        "NOT implementation_logic_error.\n\n"
        "7. confidence should reflect how certain you are based on the evidence in the output.\n\n"
        "8. Spec/test grounding rule: if a test's expected value appears structurally inconsistent "
        "with the TaskSpec's declared return type or method signature, classify as "
        "spec_test_conflict or test_expectation_not_grounded. "
        "Set recommended_action = review_test_grounding, should_modify_tests = true, "
        "should_review_spec = true, should_modify_code = false.\n"
        "   Example: if the TaskSpec says get_bookings(room: str) -> list[tuple[int, int]], "
        "a test expecting ('room1', 9, 11) is not grounded — the room name should not appear "
        "in the return value. The method takes the room as input, so the output tuples "
        "contain only the time interval, not the room name.\n"
        "   Do NOT classify every assertion mismatch as implementation_logic_error. "
        "First check: is the expected value consistent with what the spec says the method returns?\n\n"
        "For each failing test, extract:\n"
        "  test_name     — full test function name from pytest (e.g. 'test_apply_discount_rounding')\n"
        "  failure_type  — normalized enum value (not the exception class)\n"
        "  blamed_artifact — normalized enum value\n"
        "  expected      — expected value from the assertion line (empty string if not found)\n"
        "  actual        — actual value the code produced (empty string if not found)\n"
        "  error_message — the full assertion or error message text\n"
        "  trace_excerpt — 3-5 most relevant lines of the stack trace\n"
        "  confidence    — float 0.0–1.0\n"
        "  evidence      — array of short snippets from the output supporting your classification\n\n"
        "Then provide top-level fields:\n"
        "  failure_summary        — concise plain-English overview\n"
        "  primary_failure_type   — dominant failure type across all tests\n"
        "  primary_blamed_artifact — artifact most responsible for the dominant failure\n"
        "  recommended_action     — next pipeline action\n"
        "  should_modify_code     — boolean\n"
        "  should_modify_tests    — boolean\n"
        "  should_review_spec     — boolean\n"
        "  routing_reason         — one-sentence explanation of the routing decision\n"
        "  lesson                 — reusable insight for future iterations\n"
    )
