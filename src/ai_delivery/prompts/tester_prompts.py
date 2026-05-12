"""Prompt builders for TesterAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec


def generate_tests_prompt(task_spec: "TaskSpec", code: str = "") -> str:
    """Prompt that asks the LLM to write a pytest suite grounded in the task spec."""
    import json

    edge_cases = (
        "\n".join(f"  - {e}" for e in task_spec.edge_cases)
        if task_spec.edge_cases
        else "  (none specified — infer important ones)"
    )
    success_criteria = (
        "\n".join(f"  - {s}" for s in task_spec.success_criteria)
        if task_spec.success_criteria
        else "  (none specified)"
    )
    business_rules_section = (
        f"--- BUSINESS RULES (ground truth — use these exact numbers) ---\n"
        f"{json.dumps(task_spec.business_rules, indent=2)}\n"
        f"--- END BUSINESS RULES ---\n\n"
        if task_spec.business_rules
        else ""
    )
    return (
        "You are an expert Python test engineer. "
        "Write a pytest test suite grounded in the business rules below.\n\n"
        f"Task: {task_spec.description}\n"
        f"Function signature: {task_spec.function_signature}\n"
        f"Module to import from: {task_spec.module_name}\n\n"
        f"{business_rules_section}"
        f"Success criteria:\n{success_criteria}\n\n"
        f"Edge cases to cover:\n{edge_cases}\n\n"
        "CRITICAL requirements for the test suite:\n"
        "  - Use pytest\n"
        "  - Import the function from the module shown above\n"
        "  - Write EXACTLY ONE test function per business rule or edge case\n"
        "  - NEVER group multiple unrelated assertions in a single test function\n"
        "  - Test function names must describe the rule being tested, e.g. "
        "'test_cart_total_over_150_returns_free_shipping'\n"
        "  - Use ONLY the exact numeric values from the BUSINESS RULES section above\n"
        "  - Do NOT invent thresholds, costs, or surcharges not listed in the business rules\n"
        "  - Tests must be self-contained (no external dependencies)\n\n"
        "Return a JSON object with a single key 'tests' containing the full pytest source."
    )
