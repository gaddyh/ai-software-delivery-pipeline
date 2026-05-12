"""Prompt builder for FailureAnalyzerAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec

from ai_delivery.prompts.task_context import format_task_context


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
        "expected_value": {
            "type": "string",
            "description": (
                "The expected value extracted directly from the first failing assertion line, "
                "e.g. '63.34'. Leave empty string if not extractable."
            ),
        },
        "actual_value": {
            "type": "string",
            "description": (
                "The actual value produced by the code, extracted from the first failing assertion line, "
                "e.g. '63.34000000001'. Leave empty string if not extractable."
            ),
        },
        "difference": {
            "type": "string",
            "description": (
                "Human-readable description of the delta between actual and expected, "
                "e.g. '~1e-11 (float precision)' or '0.006 (formula off by ~0.01)'."
            ),
        },
        "failure_category": {
            "type": "string",
            "enum": [
                "precision_rounding_error",
                "formula_logic_error",
                "validation_error",
                "missing_branch_error",
                "type_error",
                "overfitting_suspected",
                "unknown",
            ],
            "description": "Category of the failure.",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": (
                "Confidence in the failure_category (0.0–1.0). "
                "Use >= 0.8 only when evidence strongly supports the category."
            ),
        },
    },
    "required": [
        "failed_tests",
        "inferred_rules",
        "likely_bug",
        "patch_instruction",
        "expected_value",
        "actual_value",
        "difference",
        "failure_category",
        "confidence",
    ],
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
        f"{format_task_context(task_spec)}\n\n"
        f"Failed tests:\n{failed_list}\n\n"
        "--- PYTEST OUTPUT ---\n"
        f"{pytest_output}\n"
        "--- END PYTEST OUTPUT ---\n\n"
        "Study every assertion error above carefully.\n\n"
        "STEP 1 — Extract evidence from the assertion lines:\n"
        "  - Find the first 'assert X == Y' or 'AssertionError' line in the pytest output.\n"
        "  - Set expected_value to the expected number/string (e.g. '63.34').\n"
        "  - Set actual_value to the value the code produced (e.g. '63.34000000001').\n"
        "  - Set difference to a human-readable description of the delta.\n\n"
        "STEP 2 — Classify failure_category using ALL available evidence:\n"
        "  Choose 'precision_rounding_error' when you see any of:\n"
        "    - The test name contains 'round', 'decimal', 'precision', or 'two_decimal'.\n"
        "    - The expected and actual values are numerically very close (differ by less than 0.01).\n"
        "    - The actual value has excessive decimal digits (e.g. more than 4 significant decimals).\n"
        "    - The actual value is a number that differs from expected only in the decimal portion.\n"
        "    - The implementation uses plain float arithmetic for money/percentage calculations.\n"
        "  Choose 'formula_logic_error' when the values differ significantly and the formula appears wrong.\n"
        "  Choose 'validation_error' when a ValueError is raised unexpectedly or not raised when expected.\n"
        "  Choose 'missing_branch_error' when a specific input combination is not handled.\n"
        "  Choose 'type_error' when the assertion fails due to a type mismatch.\n"
        "  IMPORTANT: Do NOT switch category between iterations. Read the assertion values, not just the test name.\n\n"
        "STEP 3 — Set confidence (0.0–1.0):\n"
        "  Use >= 0.8 when 2 or more signals above clearly support the category.\n"
        "  Use 0.5–0.7 when only 1 signal is present or evidence is ambiguous.\n"
        "  Use < 0.5 when category is uncertain.\n\n"
        "STEP 4 — Infer business rules and write a patch instruction:\n"
        "  For each failing assertion, infer the business rule it encodes.\n"
        "  Then write a concrete patch instruction for the developer.\n"
        "  IMPORTANT: If failure_category is 'precision_rounding_error', the patch instruction\n"
        "  must NOT suggest changing business rules, discount logic, surcharge logic, or condition\n"
        "  thresholds. It must only address how the final numeric value is computed.\n\n"
        "Return a JSON object with exactly these keys:\n"
        "  failed_tests      — list of failing test names\n"
        "  expected_value    — expected value from first assertion (string, empty if not found)\n"
        "  actual_value      — actual value from first assertion (string, empty if not found)\n"
        "  difference        — human-readable delta (string, empty if not found)\n"
        "  failure_category  — one of the categories above\n"
        "  confidence        — float 0.0–1.0\n"
        "  inferred_rules    — list of plain-English business rules (one per failing assertion)\n"
        "  likely_bug        — one-sentence diagnosis\n"
        "  patch_instruction — what the developer must change and in what order\n"
    )
