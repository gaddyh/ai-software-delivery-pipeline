"""Failure Analyzer agent — converts raw pytest output into structured patch instructions."""

import re
from typing import Optional

from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.failure_analysis import FailureAnalysis
from ai_delivery.prompts.failure_analyzer_prompts import (
    analyze_failures_prompt,
    FAILURE_ANALYSIS_SCHEMA,
)


class FailureAnalyzerAgent:
    """Agent that reads pytest output and produces a structured FailureAnalysis.

    When an LLM is available the analysis is generated via a schema-enforced
    OpenAI call.  Without an LLM the agent falls back to regex-based extraction
    so the pipeline keeps running without an API key.
    """

    def __init__(self, model_name: str = "gpt-4o", llm: Optional[LLMClient] = None):
        """Initialise the agent."""
        self.model_name = model_name
        self.llm = llm

    def analyze(
        self,
        task_spec: TaskSpec,
        execution_result: ExecutionResult,
        failed_tests: list[str],
    ) -> FailureAnalysis:
        """Produce a FailureAnalysis from the latest execution result.

        Args:
            task_spec: The task the code is supposed to implement.
            execution_result: The result of the most recent pytest run.
            failed_tests: Pre-parsed list of failing test names.

        Returns:
            A FailureAnalysis with four structured fields.
        """
        if self.llm is not None:
            prompt = analyze_failures_prompt(
                task_spec, failed_tests, execution_result.output
            )
            raw = self.llm.invoke(prompt, schema=FAILURE_ANALYSIS_SCHEMA)
            return FailureAnalysis(
                failed_tests=raw.get("failed_tests", failed_tests),
                inferred_rules=raw.get("inferred_rules", []),
                likely_bug=raw.get("likely_bug", ""),
                patch_instruction=raw.get("patch_instruction", ""),
            )

        # ── Stub fallback (no LLM) ─────────────────────────────────────────
        return self._regex_analyze(execution_result.output, failed_tests)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _regex_analyze(self, pytest_output: str, failed_tests: list[str]) -> FailureAnalysis:
        """Best-effort deterministic analysis when no LLM is available."""
        # Extract lines starting with "E " (pytest error lines)
        error_lines = re.findall(r"^E\s{1,3}(.+)$", pytest_output, re.MULTILINE)

        # Pull out assert-equality failures: "assert X == Y" or "AssertionError: X != Y"
        inferred_rules: list[str] = []
        for line in error_lines:
            # e.g. "AssertionError: assert 10.0 == 0.0"
            m = re.search(r"assert\s+(.+?)\s*==\s*(.+)", line)
            if m:
                got, expected = m.group(1).strip(), m.group(2).strip()
                inferred_rules.append(f"Expected {expected}, got {got}")

        if not inferred_rules and error_lines:
            inferred_rules = [e.strip() for e in error_lines[:3]]

        likely_bug = (
            f"Implementation produces wrong output for: {', '.join(failed_tests[:2])}"
            if failed_tests
            else "Unknown defect — inspect pytest output."
        )
        patch_instruction = (
            "Fix the logic so that each failing assertion produces its expected value. "
            "Check condition ordering carefully."
        )

        return FailureAnalysis(
            failed_tests=failed_tests,
            inferred_rules=inferred_rules,
            likely_bug=likely_bug,
            patch_instruction=patch_instruction,
        )
