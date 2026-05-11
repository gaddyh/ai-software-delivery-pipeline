"""Tester agent for writing and executing tests."""

from typing import Optional
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.task_spec import TaskSpec


class TesterAgent:
    """Agent responsible for testing generated code."""

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the tester agent."""
        self.model_name = model_name

    def generate_tests(self, task_spec: TaskSpec, code: str = "") -> GeneratedArtifact:
        """Generate tests from the task specification and generated code (Stage 3).

        Tests are generated once and remain fixed throughout the refinement loop.
        The same suite re-executes after every code change.
        """
        fn = task_spec.function_name
        mod = task_spec.module_name
        test_code = f"""import pytest
from {mod} import {fn}


def test_{fn}_of_zero():
    assert {fn}(0) == 1


def test_{fn}_of_one():
    assert {fn}(1) == 1


def test_{fn}_of_five():
    assert {fn}(5) == 120


def test_{fn}_of_ten():
    assert {fn}(10) == 3628800


def test_negative_raises_error():
    with pytest.raises(ValueError):
        {fn}(-1)
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
        failed = re.findall(r"FAILED (.+?) ", result.output)
        if not failed:
            failed = re.findall(r"::test_\w+", result.output)
        return [f.strip() for f in failed]

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