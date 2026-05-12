"""Prompt builder and schema for CodeQualityCriticAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec


QUALITY_REPORT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "passed": {
            "type": "boolean",
            "description": "True if no quality issues were found.",
        },
        "flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Human-readable description of each quality issue.",
        },
        "summary": {
            "type": "string",
            "description": "One-sentence overall verdict.",
        },
    },
    "required": ["passed", "flags", "summary"],
    "additionalProperties": False,
}


def _format_rules(business_rules: list) -> str:
    """Format a list of BusinessRule instances (or dicts) as 'name: rule' lines."""
    lines = []
    for r in business_rules:
        if hasattr(r, "name") and hasattr(r, "rule"):
            lines.append(f"  {r.name}: {r.rule}")
        elif isinstance(r, dict):
            lines.append(f"  {r.get('name', '?')}: {r.get('rule', '?')}")
    return "\n".join(lines)


def review_code_prompt(task_spec: "TaskSpec", code: str) -> str:
    """Build the prompt that asks the LLM to review generated code for overfitting."""
    business_rules_section = (
        f"--- BUSINESS RULES (the real spec) ---\n"
        f"{_format_rules(task_spec.business_rules)}\n"
        f"--- END BUSINESS RULES ---\n\n"
        if task_spec.business_rules
        else ""
    )
    return (
        "You are a senior code quality reviewer. "
        "Your job is to detect overfitting: code that passes tests by patching "
        "specific test values instead of implementing the real business logic.\n\n"
        f"Task: {task_spec.description}\n"
        f"Function signature: {task_spec.function_signature}\n\n"
        f"{business_rules_section}"
        "--- CODE TO REVIEW ---\n"
        f"{code}\n"
        "--- END CODE ---\n\n"
        "Flag the code if ANY of the following are true:\n"
        "  1. A comment mentions 'adjust', 'workaround', 'to meet expected', 'hack', "
        "or 'to satisfy'\n"
        "  2. An exact input value is hardcoded as a special case "
        "(e.g. `weight == 10`, `cart_total == 150`) unless that boundary is "
        "explicitly required by the spec\n"
        "  3. A surcharge or cost is negative (subtracted) unless the spec explicitly "
        "allows a discount or reduction\n"
        "  4. A branch or adjustment exists that can only be explained by one specific "
        "test case rather than a general business rule\n"
        "  5. A numeric constant in the code does not appear in the business rules above\n\n"
        "If the code correctly implements the business rules with clean general logic, "
        "set passed=true and flags=[].\n\n"
        "Return a JSON object with keys: passed (bool), flags (list of strings), "
        "summary (one sentence)."
    )
