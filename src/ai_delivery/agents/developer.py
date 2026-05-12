"""Developer agent for generating code."""

from typing import Optional
from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.failure_trace import FailureTrace
from ai_delivery.models.failure_analysis import FailureAnalysis
from ai_delivery.models.quality_report import QualityReport
from ai_delivery.prompts.developer_prompts import initial_code_prompt, refine_code_prompt


class DeveloperAgent:
    """Agent responsible for generating code based on task specifications."""

    def __init__(self, model_name: str = "gpt-4", llm: Optional[LLMClient] = None):
        """Initialize the developer agent."""
        self.model_name = model_name
        self.llm = llm

    def generate_code(
        self,
        task_spec: TaskSpec,
        failure_trace: Optional[FailureTrace] = None,
        current_code: str = "",
        test_code: str = "",
        failure_analysis: Optional[FailureAnalysis] = None,
        quality_report: Optional[QualityReport] = None,
    ) -> GeneratedArtifact:
        """Generate code for the task.

        On first call (no failure_trace) produces a stub that intentionally
        omits the target function, triggering the refinement loop.
        On subsequent calls (with failure_trace) produces the correct
        implementation informed by prior test failures, the current code
        version, and the complete pytest output stored in the trace.
        """
        iteration = len(failure_trace.history) + 1 if failure_trace else 1

        if self.llm is not None:
            if failure_trace is None and quality_report is None:
                result = self.llm.invoke(initial_code_prompt(task_spec))
            else:
                ft = failure_trace if failure_trace is not None else FailureTrace(history=[])
                result = self.llm.invoke(
                    refine_code_prompt(
                        task_spec, current_code, ft, test_code,
                        analysis=failure_analysis,
                        quality_report=quality_report,
                    )
                )
            code = result.get("code", "")
            return GeneratedArtifact(
                content=code,
                file_type="py",
                agent_name="developer",
                metadata={"task_description": task_spec.description, "iteration": iteration},
            )

        # ── Stub fallback ─────────────────────────────────────────────────
        label = task_spec.class_name or (
            task_spec.methods[0].split("(")[0] if task_spec.methods else "solution"
        )
        if task_spec.is_class_task:
            code = (
                f'"""Generated stub for: {task_spec.description} (iteration {iteration})"""\n\n\n'
                f'class {label}:\n    pass\n'
            )
        else:
            code = (
                f'"""Generated stub for: {task_spec.description} (iteration {iteration})"""\n\n\n'
                f'def {label}(*args, **kwargs):\n    pass\n'
            )

        return GeneratedArtifact(
            content=code,
            file_type="py",
            agent_name="developer",
            metadata={"task_description": task_spec.description, "iteration": iteration},
        )
