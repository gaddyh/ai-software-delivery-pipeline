"""Shared task context formatter used by all prompt builders."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec


def format_task_context(task_spec: "TaskSpec") -> str:
    """Return a compact multi-line block describing the artifact's public API.

    Output for a class task:
        Class: ShoppingCart
        Methods:
          - add_item(item_name: str, price: float, quantity: int = 1) -> None
          - total() -> float
        Module: solution

    Output for a function task (class_name is empty):
        Methods:
          - calculate_shipping(cart_total: float, ...) -> float
        Module: solution
    """
    lines: list[str] = []
    if task_spec.is_class_task:
        lines.append(f"Class: {task_spec.class_name}")
    if task_spec.methods:
        lines.append("Methods:")
        for m in task_spec.methods:
            lines.append(f"  - {m}")
    else:
        lines.append("Methods: (none specified)")
    lines.append(f"Module: {task_spec.module_name}")
    return "\n".join(lines)
