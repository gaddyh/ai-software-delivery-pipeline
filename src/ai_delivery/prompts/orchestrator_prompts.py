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
        "  - business_rules: a JSON-encoded string capturing ALL explicit numeric thresholds, "
        "pricing tiers, zone/category surcharges, and validation rules with exact values. "
        "Include every number mentioned in the requirement. "
        'Example value (as a JSON string): \'{"free_shipping_threshold": 150, '
        '"weight_tiers": [{"max_kg": 2, "cost": 5.0}, {"max_kg": 5, "cost": 10.0}, {"min_kg": 5, "cost": 18.0}], '
        '"zone_surcharges": {"local": 0.0, "regional": 4.0, "international": 12.0}, '
        '"invalid_rules": ["negative cart_total raises ValueError"]}\'. '
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
