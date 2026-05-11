"""Prompt builders for TesterAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec


def generate_tests_prompt(task_spec: "TaskSpec", code: str) -> str:
    """Prompt that asks the LLM to write a pytest suite for the given code."""
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
    return (
        "You are an expert Python test engineer. "
        "Write a comprehensive pytest test suite for the following implementation.\n\n"
        f"Task: {task_spec.description}\n"
        f"Function signature: {task_spec.function_signature}\n"
        f"Module to import from: {task_spec.module_name}\n\n"
        f"Success criteria:\n{success_criteria}\n\n"
        f"Edge cases to cover:\n{edge_cases}\n\n"
        f"--- IMPLEMENTATION ---\n"
        f"{code}\n\n"
        "Requirements for the test suite:\n"
        "  - Use pytest\n"
        "  - Import the function from the module shown above\n"
        "  - Cover all success criteria and edge cases\n"
        "  - Include at least one test per edge case\n"
        "  - Tests must be self-contained (no external dependencies)\n\n"
        "Return a JSON object with a single key 'tests' containing the full pytest source."
    )
