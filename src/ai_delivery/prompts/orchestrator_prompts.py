"""Prompt builders and schemas for OrchestratorAgent."""


def assign_task_prompt(user_message: str) -> str:
    """Build the prompt that asks the LLM to parse a user message into a TaskSpec."""
    return (
        "You are a software project orchestrator. "
        "Parse the following requirement into a structured task specification.\n\n"
        f"Requirement:\n{user_message}\n\n"
        "Return a JSON object with exactly these fields:\n"
        "  - function_name: snake_case name of the primary function to implement\n"
        "  - function_signature: full Python signature e.g. 'def foo(x: int) -> int'\n"
        "  - description: one-sentence description of what the function does\n"
        "  - constraints: list of implementation constraints (may be empty)\n"
        "  - success_criteria: list of measurable acceptance criteria\n"
        "  - edge_cases: list of edge cases that must be handled\n"
        "  - business_rules: a JSON-encoded string containing a LIST of objects, "
        "one per distinct business rule or validation constraint. "
        "Each object has exactly two keys: "
        '\'name\' (short label, e.g. "Free shipping") and '
        '\'rule\' (precise condition string using → to show the outcome and exact numbers, '
        'e.g. "cart_total > 150.0 → return 0.0"). '
        "Use 'base cost' for weight-tier costs and 'add X' for surcharges. "
        "Include every rule mentioned in the requirement. "
        'Example value (as a JSON string): \'['
        '{"name": "Free shipping", "rule": "cart_total > 150.0 → return 0.0"}, '
        '{"name": "Weight tier 1", "rule": "package_weight <= 2.0 → base cost 5.0"}, '
        '{"name": "Regional surcharge", "rule": "destination_zone == \'regional\' → add 4.0"}, '
        '{"name": "Negative inputs", "rule": "cart_total < 0 OR package_weight < 0 → raise ValueError"}'
        "]\'. "
        "Do not invent values not present in the requirement.\n"
    )


TASK_SPEC_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "function_name": {"type": "string"},
        "function_signature": {"type": "string"},
        "description": {"type": "string"},
        "constraints": {
            "type": "array",
            "items": {"type": "string"},
        },
        "success_criteria": {
            "type": "array",
            "items": {"type": "string"},
        },
        "edge_cases": {
            "type": "array",
            "items": {"type": "string"},
        },
        "business_rules": {"type": "string"},
    },
    "required": [
        "function_name",
        "function_signature",
        "description",
        "constraints",
        "success_criteria",
        "edge_cases",
        "business_rules",
    ],
    "additionalProperties": False,
}
