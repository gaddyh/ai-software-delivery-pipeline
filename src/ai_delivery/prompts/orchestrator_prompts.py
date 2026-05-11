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
    },
    "required": [
        "function_name",
        "function_signature",
        "description",
        "constraints",
        "success_criteria",
        "edge_cases",
    ],
    "additionalProperties": False,
}
