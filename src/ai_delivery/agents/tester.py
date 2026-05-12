"""Tester agent for writing and executing tests."""

from typing import Optional
from ai_delivery.llm.base import LLMClient
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.prompts.tester_prompts import generate_tests_prompt


class TesterAgent:
    """Agent responsible for testing generated code."""

    def __init__(self, model_name: str = "gpt-4", llm: Optional[LLMClient] = None):
        """Initialize the tester agent."""
        self.model_name = model_name
        self.llm = llm

    def generate_tests(self, task_spec: TaskSpec, code: str = "") -> GeneratedArtifact:
        """Generate tests from the task specification and generated code (Stage 3).

        Tests are generated once and remain fixed throughout the refinement loop.
        The same suite re-executes after every code change.
        """
        if self.llm is not None:
            result = self.llm.invoke(generate_tests_prompt(task_spec, code))
            test_code = result.get("tests", "")
            # Handle case where LLM returns a list of lines instead of a string
            if isinstance(test_code, list):
                test_code = "\n".join(test_code)
            return GeneratedArtifact(
                content=test_code,
                file_type="py",
                agent_name="tester",
            )

        # ── Stub fallback ─────────────────────────────────────────────────
        mod = task_spec.module_name
        if task_spec.is_class_task:
            cls = task_spec.class_name
            test_code = f"""import pytest
from {mod} import {cls}


def test_{cls.lower()}_instantiates():
    obj = {cls}()
    assert obj is not None
"""
        else:
            fn = task_spec.methods[0].split("(")[0] if task_spec.methods else "solution_function"
            test_code = f"""import pytest
from {mod} import {fn}


def test_{fn}_returns_value():
    result = {fn}()
    assert result is not None
"""
        return GeneratedArtifact(
            content=test_code,
            file_type="py",
            agent_name="tester",
        )

    def execute_tests(
        self, test_artifact: GeneratedArtifact, code_path: str
    ) -> ExecutionResult:
        """Execute the generated tests."""
        from ai_delivery.execution.pytest_runner import PytestRunner

        runner = PytestRunner()
        return runner.run(test_artifact.content, code_path)

    def parse_failures(self, result: ExecutionResult) -> list[str]:
        """Extract failed test names from pytest stdout."""
        import re
        # Match the short-summary section: "FAILED path/test_file.py::test_name"
        failed = re.findall(r"FAILED\s+[^\n]*::(\w+)", result.output)
        return list(dict.fromkeys(failed))  # deduplicate, preserve order

    def review_results(self, result: ExecutionResult) -> str:
        """Review test execution results and provide feedback."""
        if result.status.value == "success":
            return "All tests passed"
        failed = self.parse_failures(result)
        first_error = ""
        if result.output:
            lines = result.output.splitlines()
            for i, line in enumerate(lines):
                if "FAILED" in line or "AssertionError" in line or "ImportError" in line:
                    first_error = "\n".join(lines[i:i + 8])
                    break
        return f"Tests failed ({len(failed)} test(s)):\n{first_error}\n\nFull output:\n{result.output}"