"""Orchestrator agent for coordinating the pipeline."""

import re
from typing import Optional
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.execution_result import ExecutionResult


class OrchestratorAgent:
    """Orchestrates the software delivery pipeline."""

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the orchestrator agent."""
        self.model_name = model_name

    def assign_task(self, user_message: str) -> TaskSpec:
        """Parse a natural-language user message into a TaskSpec (Stage 1).

        Stub implementation: extracts a function name via heuristic pattern
        matching and fills remaining fields with sensible defaults derived
        from the message text.  Replace the body with an LLM call when ready.
        """
        # Try to extract an explicit function name from the message
        fn_match = (
            re.search(r"function\s+([a-z_][a-z0-9_]*)", user_message, re.IGNORECASE)
            or re.search(r"def\s+([a-z_][a-z0-9_]*)\s*\(", user_message, re.IGNORECASE)
            or re.search(r"\b([a-z_][a-z0-9_]*)\s*\(", user_message, re.IGNORECASE)
        )
        function_name = fn_match.group(1).lower() if fn_match else "solution"

        # Derive a minimal function signature from name
        sig_match = re.search(
            r"(def\s+[a-z_][a-z0-9_]*\s*\([^)]*\)(?:\s*->\s*\S+)?)",
            user_message,
            re.IGNORECASE,
        )
        function_signature = sig_match.group(1) if sig_match else f"def {function_name}(*args)"

        return TaskSpec(
            raw_requirement=user_message,
            function_name=function_name,
            function_signature=function_signature,
            module_name="solution",
            description=user_message.strip(),
            constraints=[],
            success_criteria=[f"{function_name}() returns correct output for valid inputs"],
            edge_cases=[],
        )

    def plan_task(self, task_spec: TaskSpec) -> list[str]:
        """Break down a task into steps."""
        # Placeholder for AI-based task planning
        return ["analyze_requirements", "generate_code", "write_tests", "execute_tests"]

    def coordinate_development(
        self, task_spec: TaskSpec
    ) -> tuple[GeneratedArtifact, Optional[ExecutionResult]]:
        """Coordinate the development process."""
        # Placeholder for coordination logic
        steps = self.plan_task(task_spec)
        artifact = GeneratedArtifact(
            content="# Generated code placeholder",
            file_type="py",
            agent_name="orchestrator",
        )
        return artifact, None

    def validate_result(
        self, artifact: GeneratedArtifact, result: ExecutionResult
    ) -> bool:
        """Validate the execution result."""
        return result.status.value == "success"
