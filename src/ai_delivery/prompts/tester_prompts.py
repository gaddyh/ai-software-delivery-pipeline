"""Prompt builders for TesterAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
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


def _format_list(title: str, values: list[str], empty: str = "  (none)") -> str:
    """Format a string list section for prompts."""
    body = "\n".join(f"  - {value}" for value in values) if values else empty
    return f"{title}:\n{body}"