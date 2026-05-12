"""Prompt builders for TesterAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec

from ai_delivery.prompts.task_context import format_task_context


def _format_rules(business_rules: list) -> str:
    """Format a list of BusinessRule instances (or dicts) as 'name: rule' lines."""
    lines = []
    for r in business_rules:
        if hasattr(r, "name") and hasattr(r, "rule"):
            lines.append(f"  {r.name}: {r.rule}")
        elif isinstance(r, dict):
            lines.append(f"  {r.get('name', '?')}: {r.get('rule', '?')}")
    return "\n".join(lines)


def generate_tests_prompt(task_spec: "TaskSpec", code: str = "") -> str:
    """Prompt that asks the LLM to write a pytest suite grounded in the task spec."""
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
        f"{_format_rules(task_spec.business_rules)}\n"
        f"--- END BUSINESS RULES ---\n\n"
        if task_spec.business_rules
        else ""
    )
    import_instruction = (
        f"from {task_spec.module_name} import {task_spec.class_name}\n"
        f"Instantiate {task_spec.class_name}() and test all public behavior through its methods. "
        "Do not test private implementation details."
        if task_spec.is_class_task
        else f"from {task_spec.module_name} import the function and call it directly."
    )
    return (
        "You are an expert Python test engineer. "
        "Write a pytest test suite grounded in the business rules below.\n\n"
        f"Task: {task_spec.description}\n\n"
        f"{format_task_context(task_spec)}\n\n"
        f"Import instructions: {import_instruction}\n\n"
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
