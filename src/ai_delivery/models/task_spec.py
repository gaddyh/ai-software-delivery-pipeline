from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    raw_requirement: str
    function_name: str
    function_signature: str
    module_name: str = "solution"
    description: str
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    business_rules: dict = Field(
        default_factory=dict,
        description=(
            "Structured business rules extracted from the requirement: "
            "pricing tiers, thresholds, surcharges, and validation rules with exact values."
        ),
    )