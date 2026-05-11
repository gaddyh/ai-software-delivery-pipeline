"""Developer agent for generating code."""

from typing import Optional
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.failure_trace import FailureTrace


class DeveloperAgent:
    """Agent responsible for generating code based on task specifications."""

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the developer agent."""
        self.model_name = model_name

    def generate_code(
        self,
        task_spec: TaskSpec,
        failure_trace: Optional[FailureTrace] = None,
        current_code: str = "",
    ) -> GeneratedArtifact:
        """Generate code for the task.

        On first call (no failure_trace) produces a stub that intentionally
        omits the target function, triggering the refinement loop.
        On subsequent calls (with failure_trace) produces the correct
        implementation informed by prior test failures, the current code
        version, and the complete pytest output stored in the trace.
        """
        fn = task_spec.function_name
        iteration = len(failure_trace.history) + 1 if failure_trace else 1

        if failure_trace is None:
            code = (
                f'""";\nGenerated code for: {task_spec.description}\n'
                f'(iteration {iteration} — stub)\n"""\n\n\n'
                f'def main():\n    """Main entry point."""\n'
                f'    print("Hello, World!")\n\n\n'
                f'if __name__ == "__main__":\n    main()\n'
            )
        else:
            code = (
                f'""";\nGenerated code for: {task_spec.description}\n'
                f'(iteration {iteration} — refined after {len(failure_trace.history)} failure(s))\n"""\n\n\n'
                f'def {fn}(n: int) -> int:\n'
                f'    """Calculate {fn} of n.\n\n'
                f'    Args:\n        n: A non-negative integer.\n\n'
                f'    Returns:\n        The {fn} of n.\n\n'
                f'    Raises:\n        ValueError: If n is negative.\n    """\n'
                f'    if n < 0:\n'
                f'        raise ValueError(f"{fn}() not defined for negative values, got {{n}}")\n'
                f'    if n == 0:\n        return 1\n'
                f'    return n * {fn}(n - 1)\n\n\n'
                f'def main():\n    """Main entry point."""\n'
                f'    print({fn}(5))\n\n\n'
                f'if __name__ == "__main__":\n    main()\n'
            )

        return GeneratedArtifact(
            content=code,
            file_type="py",
            agent_name="developer",
            metadata={"task_description": task_spec.description, "iteration": iteration},
        )
