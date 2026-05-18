"""Prompt builders for TesterAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.failure_analysis import FailureAnalysis
    from ai_delivery.models.execution_result import ExecutionResult
    from ai_delivery.models.task_spec import TaskSpec

from ai_delivery.prompts.task_context import format_task_context


def generate_tests_prompt(task_spec: "TaskSpec", code: str = "") -> str:
    """Prompt that asks the LLM to write a pytest suite grounded in the task spec."""
    edge_cases = _format_list(
        "Edge cases to cover",
        task_spec.edge_cases,
        empty="  (none specified — infer only obvious edge cases that do not contradict the TaskSpec)",
    )
    success_criteria = _format_list(
        "Success criteria",
        task_spec.success_criteria,
        empty="  (none specified)",
    )
    business_rules_section = (
        "--- BUSINESS RULES (ground truth — use these exact numbers) ---\n"
        f"{_format_rules(task_spec.business_rules)}\n"
        "--- END BUSINESS RULES ---\n\n"
        if task_spec.business_rules
        else ""
    )

    import_instruction = (
        f"from {task_spec.module_name} import {task_spec.class_name}\n"
        f"Instantiate {task_spec.class_name}() and test all public behavior through its methods. "
        "Do not test private implementation details."
        if task_spec.is_class_task
        else (
            f"from {task_spec.module_name} import the module-level function(s) listed above. "
            "Call the function(s) directly."
        )
    )

    return (
        "You are an expert Python test engineer.\n"
        "Write a pytest test suite grounded strictly in the TaskSpec and business rules below.\n\n"
        f"Task: {task_spec.description}\n\n"
        f"{format_task_context(task_spec)}\n\n"
        f"Import instructions: {import_instruction}\n\n"
        f"{business_rules_section}"
        f"{success_criteria}\n\n"
        f"{edge_cases}\n\n"
        "CRITICAL requirements for the test suite:\n"
        "  - Use pytest.\n"
        "  - Import only from the module shown above.\n"
        "  - Write one focused test function per business rule, success criterion, or edge case.\n"
        "  - NEVER group multiple unrelated assertions in a single test function.\n"
        "  - Test function names must describe the rule being tested, e.g. "
        "'test_cart_total_over_150_returns_free_shipping'.\n"
        "  - Use ONLY the exact numeric values from the TaskSpec, business rules, success criteria, and edge cases.\n"
        "  - Do NOT invent thresholds, costs, coupon codes, percentages, surcharges, statuses, dates, caps, or validation rules.\n"
        "  - Do NOT add pathological edge cases unless the TaskSpec explicitly asks for them.\n"
        "  - Prefer representative boundary cases over obscure numerical precision cases.\n"
        "  - If the TaskSpec says to round to 2 decimal places, expected values must be rounded to 2 decimal places.\n"
        "  - Do NOT create tests that require preserving more precision than the TaskSpec asks for.\n"
        "  - Avoid tiny floating-point stress cases unless high-precision numeric behavior is explicitly required.\n"
        "  - If Python rounding behavior matters, use expected values that are unambiguous under round(value, 2).\n"
        "  - Tests must be self-contained and must not use external dependencies.\n"
        "  - Do not test private implementation details.\n\n"
        "Return a JSON object with a single key 'tests' containing the full pytest source."
    )


def _format_rules(business_rules: list) -> str:
    """Format a list of BusinessRule instances or dicts as 'name: rule' lines."""
    if not business_rules:
        return "  (none)"

    lines: list[str] = []

    for rule in business_rules:
        if hasattr(rule, "name") and hasattr(rule, "rule"):
            lines.append(f"  - {rule.name}: {rule.rule}")
        elif isinstance(rule, dict):
            lines.append(f"  - {rule.get('name', '?')}: {rule.get('rule', '?')}")
        else:
            lines.append(f"  - {rule}")

    return "\n".join(lines)


def repair_tests_prompt(
    task_spec: "TaskSpec",
    current_test_code: str,
    current_code: str,
    failure_analysis: "FailureAnalysis",
    execution_result: "ExecutionResult",
) -> str:
    """Prompt that asks the LLM to fix a test suite that failed pytest collection."""
    collection_failure = failure_analysis.failed_tests[0] if failure_analysis.failed_tests else None
    error_message = collection_failure.error_message if collection_failure else ""
    trace_excerpt = collection_failure.trace_excerpt if collection_failure else ""

    return (
        "You are repairing a pytest file that failed during collection.\n\n"
        f"Task the tests are supposed to cover:\n  {task_spec.description}\n\n"
        "--- COLLECTION ERROR ---\n"
        f"Failure type : {failure_analysis.primary_failure_type.value}\n"
        f"Error message: {error_message}\n"
        f"Trace        :\n{trace_excerpt}\n"
        "--- END COLLECTION ERROR ---\n\n"
        "--- CURRENT TEST FILE ---\n"
        f"{current_test_code}\n"
        "--- END CURRENT TEST FILE ---\n\n"
        "--- CURRENT IMPLEMENTATION (for import reference only) ---\n"
        f"{current_code}\n"
        "--- END CURRENT IMPLEMENTATION ---\n\n"
        "REPAIR RULES — follow these exactly:\n\n"
        "You may ONLY fix:\n"
        "  - indentation errors\n"
        "  - syntax errors\n"
        "  - invalid test function names (must start with 'test_')\n"
        "  - import errors (fix import syntax, NOT the import target)\n"
        "  - pytest collection errors\n\n"
        "You must NOT:\n"
        "  - change the business intent of any test\n"
        "  - weaken or remove assertions\n"
        "  - remove tests (unless the test is syntactically unrecoverable)\n"
        "  - add new test cases\n"
        "  - change what is being tested\n\n"
        "Import rules:\n"
        "  - Preserve the intended import of the generated solution module "
        "unless the import syntax itself is invalid.\n"
        "  - Do not import external dependencies not already required by pytest "
        "or the generated code.\n\n"
        "Return a JSON object with a single key 'tests' containing the full corrected pytest source."
    )


def review_and_repair_test_grounding_prompt(
    task_spec: "TaskSpec",
    current_test_code: str,
    current_code: str,
    failure_analysis: "FailureAnalysis",
    execution_result: "ExecutionResult",
) -> str:
    """Prompt that asks the LLM to review test expectations against the task spec.

    Unlike repair_tests_prompt (which fixes syntax), this prompt checks whether
    the test's *expected values* are supported by the spec's declared contracts.
    """
    failure_summary = failure_analysis.failure_summary
    failed_details = ""
    for sf in failure_analysis.failed_tests:
        line = f"  - {sf.test_name}"
        if sf.expected and sf.actual:
            line += f": expected={sf.expected} actual={sf.actual}"
        if sf.error_message:
            line += f" | {sf.error_message[:200]}"
        failed_details += line + "\n"

    return (
        "You are a senior Python test engineer reviewing a pytest suite against a task spec.\n\n"
        f"Task spec:\n  {task_spec.description}\n\n"
        f"{format_task_context(task_spec)}\n\n"
        "--- FAILURE SUMMARY ---\n"
        f"{failure_summary}\n\n"
        "Failing tests:\n"
        f"{failed_details}"
        "--- END FAILURE SUMMARY ---\n\n"
        "--- CURRENT TEST FILE ---\n"
        f"{current_test_code}\n"
        "--- END CURRENT TEST FILE ---\n\n"
        "--- CURRENT IMPLEMENTATION (for context only — do not repair it) ---\n"
        f"{current_code}\n"
        "--- END CURRENT IMPLEMENTATION ---\n\n"
        "GROUNDING REVIEW POLICY — follow these exactly:\n\n"
        "Your job is to check whether each failing test's expected value is supported\n"
        "by the task spec's declared method signatures and return types.\n\n"
        "You MAY change a test only if its expected behavior is NOT supported by the spec.\n\n"
        "You MUST preserve tests whose expected behavior IS grounded in the spec.\n\n"
        "You MUST NOT weaken tests just to make the current implementation pass.\n\n"
        "For EACH test you change, you must cite the exact sentence or clause in the task\n"
        "spec that supports the change.\n\n"
        "If the current tests are already grounded in the task spec, return the tests\n"
        "unchanged and an empty changes list. Do not feel obligated to change anything.\n\n"
        "Common grounding failure pattern:\n"
        "  A test expects a return value that includes data the method receives as input.\n"
        "  Example: spec says get_bookings(room) -> list[tuple[int, int]].\n"
        "  A test expecting ('room1', 9, 11) is not grounded — the method takes room as\n"
        "  input, so it should not appear in the output tuples.\n\n"
        "Return a JSON object with exactly these two keys:\n"
        "  'tests'   — the full corrected pytest source (unchanged if no grounding errors found)\n"
        "  'changes' — a list of objects, one per changed test, each with:\n"
        "              'test_name'       — the test function name\n"
        "              'old_expectation' — what the test previously expected\n"
        "              'new_expectation' — what the corrected test expects\n"
        "              'spec_evidence'   — the exact spec clause that justifies this change\n"
        "  If no changes were made, 'changes' must be an empty list [].\n"
    )


def _format_list(title: str, values: list[str], empty: str = "  (none)") -> str:
    """Format a string list section for prompts."""
    body = "\n".join(f"  - {value}" for value in values) if values else empty
    return f"{title}:\n{body}"