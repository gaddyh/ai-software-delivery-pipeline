from pydantic import BaseModel, Field


class BusinessRule(BaseModel):
    """A single named business rule with a precise, human-readable condition string."""

    name: str
    rule: str


class TaskSpec(BaseModel):
    raw_requirement: str
    class_name: str = ""
    methods: list[str] = Field(
        default_factory=list,
        description=(
            "Public callable signatures without 'def'. "
            "For class tasks: method signatures. "
            "For module-level function tasks: function signatures."
        ),
    )
    module_name: str = "solution"
    description: str
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(
        default_factory=list,
        description=(
            "Structured business rules as a list of {name, rule} pairs, "
            "each encoding one precise condition with exact numeric values."
        ),
    )

    @property
    def is_class_task(self) -> bool:
        """True when the artifact is a class rather than module-level function(s)."""
        return bool(self.class_name.strip())