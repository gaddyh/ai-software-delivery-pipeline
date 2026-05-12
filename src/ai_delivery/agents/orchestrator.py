"""Orchestrator agent for coordinating the pipeline."""

import json
import re
from typing import Optional
from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.prompts.orchestrator_prompts import assign_task_prompt, TASK_SPEC_SCHEMA


class OrchestratorAgent:
    """Orchestrates the software delivery pipeline."""

    def __init__(self, model_name: str = "gpt-4", llm: Optional[LLMClient] = None):
        """Initialize the orchestrator agent."""
        self.model_name = model_name
        self.llm = llm

    def assign_task(self, user_message: str) -> TaskSpec:
        """Parse a natural-language user message into a TaskSpec (Stage 1).

        Uses the LLM when available; falls back to heuristic stub otherwise.
        """
        if self.llm is not None:
            result = self.llm.invoke(assign_task_prompt(user_message), schema=TASK_SPEC_SCHEMA)
            raw_rules = result.get("business_rules", "{}")
            if isinstance(raw_rules, str):
                try:
                    result["business_rules"] = json.loads(raw_rules)
                except (json.JSONDecodeError, ValueError):
                    result["business_rules"] = {}
            result.setdefault("module_name", "solution")
            return TaskSpec(
                raw_requirement=user_message,
                **result,
            )

        # ── Stub fallback ─────────────────────────────────────────────────
        class_match = re.search(r"\bclass\b\s+([A-Z][a-zA-Z0-9_]*)", user_message)
        class_name = class_match.group(1) if class_match else ""

        sig_matches = re.findall(
            r"([a-z_][a-z0-9_]*\s*\([^)]*\)(?:\s*->\s*\S+)?)",
            user_message,
            re.IGNORECASE,
        )
        if sig_matches:
            methods = sig_matches[:6]
        else:
            fn_match = re.search(
                r"(?:function\s+called\s+|called\s+|named\s+)([a-z_][a-z0-9_]*)",
                user_message,
                re.IGNORECASE,
            )
            fn_name = fn_match.group(1).lower() if fn_match else "solution_function"
            methods = [f"{fn_name}(*args) -> None"]

        return TaskSpec(
            raw_requirement=user_message,
            class_name=class_name,
            methods=methods,
            module_name="solution",
            description=user_message.strip()[:200],
            constraints=[],
            success_criteria=[],
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
